from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, urlencode

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.domain.repository import FileBackedMapRepository
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.integrations.codex_backend import CodexBackend, sanitize_status_message
from warhammer_companion.sample_data import SAMPLE_PACKETS

PACKAGE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Warhammer Tournament Companion")
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
ingestion_paths = IngestionPaths()
repository = FileBackedMapRepository(ingestion_paths.map_packets_dir, fallback=SAMPLE_PACKETS)
codex_backend = CodexBackend()
service = WarhammerCompanionService(
    paths=ingestion_paths,
    repository=repository,
    codex_backend=codex_backend,
)


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse("/viewer", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request) -> HTMLResponse:
    state = service.settings_state()
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "active_page": "settings",
            "app_backend_status": state.app_backend_status,
            "app_backend_detail": state.app_backend_detail,
            "codex_status": state.codex_status,
            "codex_action": request.query_params.get("codex_action"),
            "codex_message": request.query_params.get("codex_message"),
            "codex_login_url": request.query_params.get("codex_login_url"),
            "codex_user_code": request.query_params.get("codex_user_code"),
        },
    )


@app.post("/settings/codex/login", response_class=HTMLResponse)
def start_codex_login(method: str = Form("browser")) -> RedirectResponse:
    try:
        if method == "device-code":
            login = service.start_codex_device_code_login()
            return RedirectResponse(
                "/settings?"
                + urlencode(
                    {
                        "codex_action": "device-code-started",
                        "codex_login_url": login.verification_url or "",
                        "codex_user_code": login.user_code or "",
                    }
                ),
                status_code=303,
            )
        login = service.start_codex_login()
    except Exception as exc:
        return _settings_codex_error_redirect(exc)
    if not login.auth_url:
        return RedirectResponse("/settings?codex_action=login-started", status_code=303)
    return RedirectResponse(login.auth_url, status_code=303)


@app.post("/settings/codex/logout", response_class=HTMLResponse)
def logout_codex() -> RedirectResponse:
    try:
        service.logout_codex()
    except Exception as exc:
        return _settings_codex_error_redirect(exc)
    return RedirectResponse("/settings?codex_action=logout-complete", status_code=303)


@app.get("/map-data", response_class=HTMLResponse)
def map_data(request: Request) -> HTMLResponse:
    state = service.map_data_state()
    return templates.TemplateResponse(
        request,
        "map_data.html",
        {
            "active_page": "map-data",
            "packets": state.packets,
            "deletable_packet_ids": state.deletable_packet_ids,
            "sources": state.sources,
            "pipeline": state.pipeline,
            "report": state.report,
            "ingestion_status": request.query_params.get("ingestion"),
            "ingestion_message": request.query_params.get("message"),
            "deleted": request.query_params.get("deleted"),
        },
    )


@app.post("/map-data/ingest", response_class=HTMLResponse)
def trigger_ingestion() -> RedirectResponse:
    try:
        service.run_ingestion()
    except Exception as exc:
        return RedirectResponse(
            f"/map-data?ingestion=failed&message={quote(str(exc))}",
            status_code=303,
        )
    return RedirectResponse("/map-data?ingestion=complete", status_code=303)


@app.post("/map-data/delete", response_class=HTMLResponse)
def delete_packet(packet_id: str = Form(...)) -> RedirectResponse:
    deleted = service.delete_packet(packet_id)
    return RedirectResponse(f"/map-data?deleted={int(deleted)}", status_code=303)


@app.get("/viewer", response_class=HTMLResponse)
def viewer(
    request: Request,
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
) -> HTMLResponse:
    state = service.viewer_state(
        packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
    )
    return templates.TemplateResponse(
        request,
        "viewer.html",
        {
            "active_page": "viewer",
            "packet": state.packet,
            "packet_groups": state.packet_groups,
            "packet_selector": state.packet_selector,
            "map_svg": state.map_svg,
        },
    )


@app.get("/heatmap", response_class=HTMLResponse)
def heatmap(
    request: Request,
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
    zone_id: str = "attacker",
    source: str = "edge",
    offset_inches: int = 0,
) -> HTMLResponse:
    state = service.heatmap_state(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
        zone_id=zone_id,
        source=source,
        offset_inches=offset_inches,
    )
    return templates.TemplateResponse(
        request,
        "heatmap.html",
        {
            "active_page": "heatmap",
            "packet": state.packet,
            "packet_groups": state.packet_groups,
            "packet_selector": state.packet_selector,
            "selected_zone_id": state.selected_zone_id,
            "selected_source": state.selected_source,
            "selected_offset_inches": state.selected_offset_inches,
            "offset_options": state.offset_options,
            "map_svg": state.map_svg,
        },
    )


@app.get("/los-checker", response_class=HTMLResponse)
def los_checker(
    request: Request,
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
    x: float = 22.0,
    y: float = 10.0,
    base: float = 1.57,
) -> HTMLResponse:
    state = service.los_checker_state(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
        x=x,
        y=y,
        base=base,
    )
    return templates.TemplateResponse(
        request,
        "los_checker.html",
        {
            "active_page": "los-checker",
            "packet": state.packet,
            "packet_groups": state.packet_groups,
            "packet_selector": state.packet_selector,
            "x": state.x,
            "y": state.y,
            "base": state.base,
            "map_svg": state.map_svg,
        },
    )


@app.post("/los-checker", response_class=HTMLResponse)
def update_los_checker(
    packet_id: str | None = Form(None),
    player_a: str | None = Form(None),
    player_b: str | None = Form(None),
    layout_variant: str | None = Form(None),
    x: float = Form(...),
    y: float = Form(...),
    base: float = Form(...),
) -> RedirectResponse:
    resolved_packet_id = service.resolve_packet_id(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
    )
    return RedirectResponse(
        f"/los-checker?packet_id={resolved_packet_id}&x={x}&y={y}&base={base}",
        status_code=303,
    )


def _settings_codex_error_redirect(exc: Exception) -> RedirectResponse:
    return RedirectResponse(
        "/settings?"
        + urlencode(
            {
                "codex_action": "error",
                "codex_message": sanitize_status_message(str(exc)),
            }
        ),
        status_code=303,
    )
