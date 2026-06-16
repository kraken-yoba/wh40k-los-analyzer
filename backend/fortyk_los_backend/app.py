from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import Field

from fortyk_los_backend.domain.fixtures import FixtureRepository
from fortyk_los_backend.domain.los import (
    BaseProfile,
    LineOfSightRequest,
    LineOfSightResult,
    compute_base_aware_los,
    compute_point_los,
)
from fortyk_los_backend.domain.models import CanonicalBaseModel, Point
from fortyk_los_backend.domain.serialization import stable_layout_hash

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]

app = FastAPI(title="Warhammer 40k LOS Analyzer")
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
fixtures = FixtureRepository(REPO_ROOT)


class LineOfSightApiRequest(CanonicalBaseModel):
    source: Point
    target: Point
    source_base_diameter: float | None = Field(default=None, gt=0)
    target_base_diameter: float | None = Field(default=None, gt=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/layouts")
def list_layouts() -> dict[str, list[dict[str, str]]]:
    return {"layouts": fixtures.list_layouts()}


@app.get("/api/layouts/{layout_id}")
def get_layout(layout_id: str) -> dict[str, object]:
    layout = fixtures.get_layout(layout_id)
    if layout is None:
        raise HTTPException(status_code=404, detail=f"Layout not found: {layout_id}")
    return {
        "layout": jsonable_encoder(layout),
        "layout_hash": stable_layout_hash(layout),
    }


@app.post("/api/layouts/{layout_id}/los")
def line_of_sight(layout_id: str, request: LineOfSightApiRequest) -> dict[str, object]:
    layout = fixtures.get_layout(layout_id)
    if layout is None:
        raise HTTPException(status_code=404, detail=f"Layout not found: {layout_id}")

    los_request = LineOfSightRequest(source=request.source, target=request.target)
    if request.source_base_diameter is not None or request.target_base_diameter is not None:
        source_diameter = request.source_base_diameter or request.target_base_diameter
        target_diameter = request.target_base_diameter or request.source_base_diameter
        if source_diameter is None or target_diameter is None:
            raise HTTPException(status_code=422, detail="Base diameter is required")
        result: LineOfSightResult = compute_base_aware_los(
            layout,
            los_request,
            source_base=BaseProfile(diameter=source_diameter),
            target_base=BaseProfile(diameter=target_diameter),
        )
    else:
        result = compute_point_los(layout, los_request)

    return dict(jsonable_encoder(result))


@app.get("/api/sources")
def source_status() -> dict[str, list[dict[str, object]]]:
    manifest = fixtures.source_manifest()
    statuses = {
        status.document_id: status for status in manifest.cache_statuses(repo_root=REPO_ROOT)
    }
    documents: list[dict[str, object]] = []
    for document in manifest.documents:
        document_payload = jsonable_encoder(document)
        document_payload["cache_status"] = jsonable_encoder(statuses[document.document_id])
        documents.append(document_payload)
    return {"documents": documents}
