from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from warhammer_companion.domain.repository import InMemoryMapRepository
from warhammer_companion.ingestion.pipeline import current_pipeline_status
from warhammer_companion.ingestion.sources import OFFICIAL_SOURCES
from warhammer_companion.los.geometry import heatmap_from_deployment_zone, visibility_rays_from_base
from warhammer_companion.rendering.svg import render_map_svg

PACKAGE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Warhammer Tournament Companion")
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
repository = InMemoryMapRepository()


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse("/viewer", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "active_page": "settings",
            "codex_status": "not wired",
            "chatgpt_status": "not connected",
        },
    )


@app.get("/map-data", response_class=HTMLResponse)
def map_data(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "map_data.html",
        {
            "active_page": "map-data",
            "packets": repository.list_packets(),
            "sources": OFFICIAL_SOURCES,
            "pipeline": current_pipeline_status(),
        },
    )


@app.post("/map-data/ingest", response_class=HTMLResponse)
def trigger_ingestion() -> RedirectResponse:
    return RedirectResponse("/map-data?ingestion=queued", status_code=303)


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
    request: Request, packet_id: str | None = None, zone_id: str = "attacker"
) -> HTMLResponse:
    packet = repository.get_packet(packet_id) if packet_id else repository.default_packet()
    heatmap_cells = heatmap_from_deployment_zone(packet, zone_id)
    return templates.TemplateResponse(
        request,
        "heatmap.html",
        {
            "active_page": "heatmap",
            "packet": packet,
            "packets": repository.list_packets(),
            "selected_zone_id": zone_id,
            "map_svg": render_map_svg(packet, heatmap=heatmap_cells),
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
    rays = visibility_rays_from_base(packet, center=(x, y), base_diameter=base)
    return templates.TemplateResponse(
        request,
        "los_checker.html",
        {
            "active_page": "los-checker",
            "packet": packet,
            "packets": repository.list_packets(),
            "x": x,
            "y": y,
            "base": base,
            "map_svg": render_map_svg(packet, rays=rays, base_center=(x, y), base_diameter=base),
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
