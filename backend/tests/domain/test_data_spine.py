import json
from pathlib import Path

import pytest
from fortyk_los_backend.domain.manifest import (
    CacheStatus,
    SourceDocument,
    SourceKind,
    SourceManifest,
)
from fortyk_los_backend.domain.models import (
    Blocker,
    BlockerKind,
    Board,
    CanonicalLayout,
    DeploymentZone,
    LayoutProvenance,
    Point,
    PolygonGeometry,
    ReviewStatus,
    TerrainFeature,
    ValidationRecord,
    ValidationSeverity,
    ValidationStatus,
)
from fortyk_los_backend.domain.serialization import (
    canonical_json_bytes,
    stable_layout_hash,
)
from pydantic import ValidationError


def _rectangle(
    *,
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
) -> PolygonGeometry:
    return PolygonGeometry(
        points=[
            Point(x=x_min, y=y_min),
            Point(x=x_max, y=y_min),
            Point(x=x_max, y=y_max),
            Point(x=x_min, y=y_max),
        ]
    )


def _layout() -> CanonicalLayout:
    return CanonicalLayout(
        layout_id="synthetic-alpha",
        name="Synthetic Alpha",
        board=Board(width=44.0, height=60.0, unit="inch"),
        terrain_features=[
            TerrainFeature(
                feature_id="ruin-b",
                label="Ruin B",
                footprint=_rectangle(x_min=30.0, y_min=10.0, x_max=38.0, y_max=18.0),
            ),
            TerrainFeature(
                feature_id="ruin-a",
                label="Ruin A",
                footprint=_rectangle(x_min=4.0, y_min=4.0, x_max=12.0, y_max=14.0),
            ),
        ],
        blockers=[
            Blocker(
                blocker_id="wall-b",
                feature_id="ruin-b",
                kind=BlockerKind.WALL,
                start=Point(x=30.0, y=10.0),
                end=Point(x=38.0, y=10.0),
            ),
            Blocker(
                blocker_id="wall-a",
                feature_id="ruin-a",
                kind=BlockerKind.WALL,
                start=Point(x=4.0, y=4.0),
                end=Point(x=12.0, y=4.0),
            ),
        ],
        deployments=[
            DeploymentZone(
                zone_id="attacker",
                label="Attacker",
                area=_rectangle(x_min=0.0, y_min=0.0, x_max=44.0, y_max=10.0),
            )
        ],
        provenance=LayoutProvenance(
            source_document_id="terrain-layouts-2026-06-12",
            source_page=2,
            extraction_method="synthetic-fixture",
        ),
        validation_records=[
            ValidationRecord(
                code="synthetic_fixture",
                severity=ValidationSeverity.INFO,
                message="Fixture has deterministic ground truth.",
            )
        ],
        validation_status=ValidationStatus.PASSED,
    )


def test_canonical_layout_captures_required_domain_fields() -> None:
    layout = _layout()

    assert layout.schema_version == "1.0"
    assert layout.board.unit == "inch"
    assert {feature.feature_id for feature in layout.terrain_features} == {"ruin-a", "ruin-b"}
    assert {blocker.kind for blocker in layout.blockers} == {BlockerKind.WALL}
    assert layout.provenance.source_document_id == "terrain-layouts-2026-06-12"
    assert layout.validation_status == ValidationStatus.PASSED


def test_canonical_layout_rejects_geometry_outside_board_bounds() -> None:
    payload = _layout().model_dump()
    payload["terrain_features"][0]["footprint"]["points"][0]["x"] = 45.0

    with pytest.raises(ValidationError, match="outside board bounds"):
        CanonicalLayout.model_validate(payload)


def test_canonical_layout_rejects_duplicate_domain_ids() -> None:
    payload = _layout().model_dump()
    payload["terrain_features"][1]["feature_id"] = "ruin-b"

    with pytest.raises(ValidationError, match="duplicate terrain feature id"):
        CanonicalLayout.model_validate(payload)


def test_canonical_layout_rejects_blocker_referencing_unknown_feature() -> None:
    payload = _layout().model_dump()
    payload["blockers"][0]["feature_id"] = "missing-feature"

    with pytest.raises(ValidationError, match="unknown terrain feature"):
        CanonicalLayout.model_validate(payload)


def test_warning_validation_records_default_to_unreviewed() -> None:
    record = ValidationRecord(
        code="low_confidence_dimension",
        severity=ValidationSeverity.WARNING,
        message="Dimension text had low OCR confidence.",
    )

    assert record.review_status == ReviewStatus.UNREVIEWED


def test_canonical_json_and_hash_are_stable_across_domain_list_order() -> None:
    first = _layout()
    second_payload = first.model_dump()
    second_payload["terrain_features"] = list(reversed(second_payload["terrain_features"]))
    second_payload["blockers"] = list(reversed(second_payload["blockers"]))
    second = CanonicalLayout.model_validate(second_payload)

    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert stable_layout_hash(first) == stable_layout_hash(second)


def test_canonical_json_uses_fixed_float_precision() -> None:
    layout = _layout()
    layout.terrain_features[0].footprint.points[0] = Point(x=1.23456789, y=2.34567891)

    canonical_json = canonical_json_bytes(layout).decode("utf-8")

    assert "1.2346" in canonical_json
    assert "2.3457" in canonical_json
    assert "1.23456789" not in canonical_json


def test_source_manifest_reports_cache_status_without_committing_pdfs(tmp_path: Path) -> None:
    cached_pdf = tmp_path / "terrain-layouts.pdf"
    cached_pdf.write_bytes(b"official bytes stay local")

    manifest = SourceManifest(
        documents=[
            SourceDocument(
                document_id="terrain-layouts-2026-06-12",
                kind=SourceKind.TERRAIN_LAYOUTS,
                url="https://assets.warhammer-community.com/example-terrain.pdf",
                expected_sha256="1cfc9e4bbcd4a4ad1fe2c6d096b30c6b28ebf057bb8b789f4d3c761b49ac11db",
                cache_path=cached_pdf,
                redistribution="do-not-commit",
            )
        ]
    )

    [status] = manifest.cache_statuses()

    assert status.document_id == "terrain-layouts-2026-06-12"
    assert status.status == CacheStatus.HASH_MISMATCH
    assert status.cache_path == cached_pdf


def test_public_source_manifest_contains_official_documents() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    manifest_path = repo_root / "fixtures" / "source_manifest.official.json"

    manifest = SourceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))

    documents_by_id = {document.document_id: document for document in manifest.documents}
    assert set(documents_by_id) == {
        "terrain-layouts-2026-06-12",
        "core-rules-2026-06-01",
    }
    assert documents_by_id["terrain-layouts-2026-06-12"].expected_sha256 == (
        "abda484efe1e3031a92079053594a8b933a6ac429b899151f39ce8d51cbb9189"
    )
    assert documents_by_id["core-rules-2026-06-01"].expected_sha256 == (
        "f6a2443a44627ac5f0ef08407d29aa5ec7e97339998f05bc35f3ae37bf276833"
    )
    assert all(document.redistribution == "do-not-commit" for document in manifest.documents)


def test_synthetic_layout_fixture_is_canonical_and_hash_tracked() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    layout_path = repo_root / "fixtures" / "layouts" / "synthetic_alpha.layout.json"
    hash_path = repo_root / "fixtures" / "layouts" / "synthetic_alpha.layout.sha256"

    layout = CanonicalLayout.model_validate_json(layout_path.read_text(encoding="utf-8"))

    assert layout_path.read_text(encoding="utf-8").strip().encode("utf-8") == canonical_json_bytes(
        layout
    )
    assert hash_path.read_text(encoding="utf-8").strip() == stable_layout_hash(layout)
