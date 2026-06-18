from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote, urlencode

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from warhammer_companion.domain.repository import FileBackedMapRepository
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.packet_builder import IngestionReport, run_official_ingestion
from warhammer_companion.ingestion.pipeline import current_pipeline_status
from warhammer_companion.ingestion.sources import OFFICIAL_SOURCES
from warhammer_companion.integrations.codex_backend import CodexBackend, sanitize_status_message
from warhammer_companion.los.geometry import (
    clamp_base_center,
    heatmap_exclusion_zone,
    heatmap_visibility_polygons_from_deployment_edge,
    heatmap_visibility_polygons_from_deployment_zone,
    safe_heatmap_regions,
    visibility_polygon_from_base,
    visibility_rays_from_base,
)
from warhammer_companion.rendering.svg import render_map_svg
from warhammer_companion.sample_data import SAMPLE_PACKETS

PACKAGE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Warhammer Tournament Companion")
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
ingestion_paths = IngestionPaths()
repository = FileBackedMapRepository(ingestion_paths.map_packets_dir, fallback=SAMPLE_PACKETS)
codex_backend = CodexBackend()


@lru_cache(maxsize=32)
def _cached_heatmap_svg(
    packet_id: str,
    zone_id: str,
    source: str,
    offset_inches: int,
) -> str:
    packet = repository.get_packet(packet_id)
    if source == "interior":
        polygons = heatmap_visibility_polygons_from_deployment_zone(packet, zone_id)
    else:
        polygons = heatmap_visibility_polygons_from_deployment_edge(
            packet,
            zone_id,
            offset_inches=offset_inches,
        )
    exclusion = heatmap_exclusion_zone(
        packet,
        zone_id,
        source=source,
        offset_inches=offset_inches,
    )
    safe_regions = safe_heatmap_regions(packet, polygons, excluded_area=exclusion)
    return render_map_svg(
        packet,
        heatmap_polygons=polygons,
        heatmap_exclusion=exclusion,
        safe_regions=safe_regions,
    )


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse("/viewer", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request) -> HTMLResponse:
    codex_status = codex_backend.current_status()
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "active_page": "settings",
            "app_backend_status": "python ingestion backend ready",
            "app_backend_detail": (
                "Official PDF extraction, LOS geometry, and visual categorizer artifacts "
                "run through Python service boundaries."
            ),
            "codex_status": codex_status,
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
            login = codex_backend.start_chatgpt_device_code_login()
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
        login = codex_backend.start_chatgpt_login()
    except Exception as exc:
        return _settings_codex_error_redirect(exc)
    if not login.auth_url:
        return RedirectResponse("/settings?codex_action=login-started", status_code=303)
    return RedirectResponse(login.auth_url, status_code=303)


@app.post("/settings/codex/logout", response_class=HTMLResponse)
def logout_codex() -> RedirectResponse:
    try:
        codex_backend.logout()
    except Exception as exc:
        return _settings_codex_error_redirect(exc)
    return RedirectResponse("/settings?codex_action=logout-complete", status_code=303)


@app.get("/map-data", response_class=HTMLResponse)
def map_data(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "map_data.html",
        {
            "active_page": "map-data",
            "packets": repository.list_packets(),
            "deletable_packet_ids": _deletable_packet_ids(),
            "sources": OFFICIAL_SOURCES,
            "pipeline": current_pipeline_status(),
            "report": _latest_ingestion_report(),
            "ingestion_status": request.query_params.get("ingestion"),
            "ingestion_message": request.query_params.get("message"),
            "deleted": request.query_params.get("deleted"),
        },
    )


@app.post("/map-data/ingest", response_class=HTMLResponse)
def trigger_ingestion() -> RedirectResponse:
    try:
        run_official_ingestion(paths=ingestion_paths, classify_features=True)
    except Exception as exc:
        return RedirectResponse(
            f"/map-data?ingestion=failed&message={quote(str(exc))}",
            status_code=303,
        )
    repository.reload()
    _cached_heatmap_svg.cache_clear()
    return RedirectResponse("/map-data?ingestion=complete", status_code=303)


@app.post("/map-data/delete", response_class=HTMLResponse)
def delete_packet(packet_id: str = Form(...)) -> RedirectResponse:
    deleted = False
    try:
        packet_path = _packet_path(packet_id)
    except ValueError:
        packet_path = None
    if packet_path is not None and packet_path.exists():
        packet_path.unlink()
        deleted = True
    repository.reload()
    _cached_heatmap_svg.cache_clear()
    return RedirectResponse(f"/map-data?deleted={int(deleted)}", status_code=303)


@app.get("/viewer", response_class=HTMLResponse)
def viewer(request: Request, packet_id: str | None = None) -> HTMLResponse:
    packet = repository.get_packet(packet_id) if packet_id else repository.default_packet()
    return templates.TemplateResponse(
        request,
        "viewer.html",
        {
            "active_page": "viewer",
            "packet": packet,
            "packets": repository.list_packets(),
            "map_svg": render_map_svg(packet),
        },
    )


@app.get("/heatmap", response_class=HTMLResponse)
def heatmap(
    request: Request,
    packet_id: str | None = None,
    zone_id: str = "attacker",
    source: str = "edge",
    offset_inches: int = 0,
) -> HTMLResponse:
    packet = repository.get_packet(packet_id) if packet_id else repository.default_packet()
    heatmap_source = source if source in {"edge", "interior"} else "edge"
    clamped_offset = min(max(offset_inches, 0), 12)
    return templates.TemplateResponse(
        request,
        "heatmap.html",
        {
            "active_page": "heatmap",
            "packet": packet,
            "packets": repository.list_packets(),
            "selected_zone_id": zone_id,
            "selected_source": heatmap_source,
            "selected_offset_inches": clamped_offset,
            "offset_options": list(range(0, 13)),
            "map_svg": _cached_heatmap_svg(
                packet.id,
                zone_id,
                heatmap_source,
                clamped_offset,
            ),
        },
    )


@app.get("/los-checker", response_class=HTMLResponse)
def los_checker(
    request: Request,
    packet_id: str | None = None,
    x: float = 22.0,
    y: float = 10.0,
    base: float = 1.57,
) -> HTMLResponse:
    packet = repository.get_packet(packet_id) if packet_id else repository.default_packet()
    center = clamp_base_center(packet, (x, y), base)
    coverage_polygon = visibility_polygon_from_base(packet, center=center, base_diameter=base)
    rays = visibility_rays_from_base(packet, center=center, base_diameter=base)
    return templates.TemplateResponse(
        request,
        "los_checker.html",
        {
            "active_page": "los-checker",
            "packet": packet,
            "packets": repository.list_packets(),
            "x": center[0],
            "y": center[1],
            "base": base,
            "map_svg": render_map_svg(
                packet,
                coverage_polygon=coverage_polygon,
                rays=rays,
                base_center=center,
                base_diameter=base,
            ),
        },
    )


@app.post("/los-checker", response_class=HTMLResponse)
def update_los_checker(
    packet_id: str = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    base: float = Form(...),
) -> RedirectResponse:
    return RedirectResponse(
        f"/los-checker?packet_id={packet_id}&x={x}&y={y}&base={base}", status_code=303
    )


def _latest_ingestion_report() -> IngestionReport | None:
    path = ingestion_paths.ingestion_report_path
    if not path.exists():
        return None
    try:
        return IngestionReport.model_validate_json(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


def _deletable_packet_ids() -> set[str]:
    directory = ingestion_paths.map_packets_dir
    if not directory.exists() or not directory.is_dir():
        return set()
    return {path.stem for path in directory.glob("*.json") if path.is_file()}


def _packet_path(packet_id: str) -> Path:
    candidate = ingestion_paths.map_packets_dir / f"{packet_id}.json"
    if not packet_id or candidate.name != f"{packet_id}.json":
        raise ValueError(f"Invalid packet id: {packet_id}")
    return candidate


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
