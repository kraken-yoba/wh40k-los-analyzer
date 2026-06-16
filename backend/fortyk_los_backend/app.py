from collections.abc import Sequence
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import Field, FiniteFloat, ValidationError

from fortyk_los_backend.domain.analysis import (
    GridSpec,
    MovementExposureRequest,
    Region,
    TerrainCoverageRequest,
    generate_firing_lane_heatmap,
    measure_deployment_exposure,
    measure_terrain_coverage,
)
from fortyk_los_backend.domain.fixtures import FixtureRepository
from fortyk_los_backend.domain.los import (
    BaseProfile,
    LineOfSightRequest,
    LineOfSightResult,
    compute_base_aware_los,
    compute_point_los,
)
from fortyk_los_backend.domain.models import CanonicalBaseModel, CanonicalLayout, Point
from fortyk_los_backend.domain.serialization import stable_layout_hash

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]

app = FastAPI(title="Warhammer 40k LOS Analyzer")
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
fixtures = FixtureRepository(REPO_ROOT)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": _sanitize_validation_errors(exc.errors())},
    )


class LineOfSightApiRequest(CanonicalBaseModel):
    source: Point
    target: Point
    source_base_diameter: FiniteFloat | None = Field(default=None, gt=0)
    target_base_diameter: FiniteFloat | None = Field(default=None, gt=0)
    boundary_sample_count: int = Field(default=16, ge=8, le=128)


class HeatmapApiRequest(CanonicalBaseModel):
    source_region: Region
    target_grid: GridSpec
    source_step: FiniteFloat | None = Field(default=None, gt=0)


class TerrainCoverageApiRequest(CanonicalBaseModel):
    source_region: Region
    target_grid: GridSpec


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
        try:
            result: LineOfSightResult = compute_base_aware_los(
                layout,
                los_request,
                source_base=BaseProfile(
                    diameter=source_diameter,
                    boundary_sample_count=request.boundary_sample_count,
                ),
                target_base=BaseProfile(
                    diameter=target_diameter,
                    boundary_sample_count=request.boundary_sample_count,
                ),
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=422,
                detail=_sanitize_validation_errors(exc.errors()),
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    else:
        result = compute_point_los(layout, los_request)

    return dict(jsonable_encoder(result))


@app.post("/api/layouts/{layout_id}/heatmap")
def firing_lane_heatmap(layout_id: str, request: HeatmapApiRequest) -> dict[str, object]:
    layout = _get_layout_or_404(layout_id)
    result = generate_firing_lane_heatmap(
        layout,
        source_region=request.source_region,
        target_grid=request.target_grid,
        source_step=request.source_step,
    )
    return dict(jsonable_encoder(result))


@app.post("/api/layouts/{layout_id}/exposure")
def deployment_exposure(layout_id: str, request: MovementExposureRequest) -> dict[str, object]:
    layout = _get_layout_or_404(layout_id)
    try:
        result = measure_deployment_exposure(layout, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return dict(jsonable_encoder(result))


@app.post("/api/layouts/{layout_id}/terrain/{feature_id}/coverage")
def terrain_coverage(
    layout_id: str,
    feature_id: str,
    request: TerrainCoverageApiRequest,
) -> dict[str, object]:
    layout = _get_layout_or_404(layout_id)
    try:
        result = measure_terrain_coverage(
            layout,
            TerrainCoverageRequest(
                feature_id=feature_id,
                source_region=request.source_region,
                target_grid=request.target_grid,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
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


def _get_layout_or_404(layout_id: str) -> CanonicalLayout:
    layout = fixtures.get_layout(layout_id)
    if layout is None:
        raise HTTPException(status_code=404, detail=f"Layout not found: {layout_id}")
    return layout


def _sanitize_validation_errors(errors: Sequence[object]) -> list[dict[str, object]]:
    return [_sanitize_validation_error(error) for error in errors]


def _sanitize_validation_error(error: object) -> dict[str, object]:
    if not isinstance(error, dict):
        return {"msg": str(error)}
    sanitized = dict(error)
    sanitized.pop("input", None)
    ctx = sanitized.get("ctx")
    if isinstance(ctx, dict):
        sanitized["ctx"] = {key: str(value) for key, value in ctx.items()}
    return sanitized
