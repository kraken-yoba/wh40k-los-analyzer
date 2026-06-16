import json
from hashlib import sha256
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
        points=(
            Point(x=x_min, y=y_min),
            Point(x=x_max, y=y_min),
            Point(x=x_max, y=y_max),
            Point(x=x_min, y=y_max),
        )
    )


def _layout() -> CanonicalLayout:
    return CanonicalLayout(
        layout_id="synthetic-alpha",
        name="Synthetic Alpha",
        board=Board(width=44.0, height=60.0, unit="inch"),
        terrain_features=(
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
        ),
        blockers=(
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
        ),
        deployments=(
            DeploymentZone(
                zone_id="attacker",
                label="Attacker",
                area=_rectangle(x_min=0.0, y_min=0.0, x_max=44.0, y_max=10.0),
            ),
        ),
        provenance=LayoutProvenance(
            source_document_id="terrain-layouts-2026-06-12",
            source_page=2,
            extraction_method="synthetic-fixture",
        ),
        validation_records=(
            ValidationRecord(
                code="synthetic_fixture",
                severity=ValidationSeverity.INFO,
                message="Fixture has deterministic ground truth.",
            ),
        ),
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
    payload = _layout().model_dump(mode="json")
    payload["deployments"][0]["area"]["points"][2]["x"] = 45.0

    with pytest.raises(ValidationError, match="outside board bounds"):
        CanonicalLayout.model_validate(payload)


@pytest.mark.parametrize("bad_number", [float("nan"), float("inf"), float("-inf")])
def test_geometry_rejects_non_finite_numbers(bad_number: float) -> None:
    with pytest.raises(ValidationError):
        Point(x=bad_number, y=0.0)

    with pytest.raises(ValidationError):
        Board(width=bad_number, height=60.0)


def test_canonical_layout_rejects_unknown_schema_version() -> None:
    payload = _layout().model_dump()
    payload["schema_version"] = "2.0"

    with pytest.raises(ValidationError):
        CanonicalLayout.model_validate(payload)


@pytest.mark.parametrize(
    ("points", "case_name"),
    [
        (
            (Point(x=0.0, y=0.0), Point(x=1.0, y=1.0), Point(x=2.0, y=2.0)),
            "collinear",
        ),
        (
            (Point(x=0.0, y=0.0), Point(x=2.0, y=0.0), Point(x=2.0, y=0.0)),
            "duplicate",
        ),
        (
            (
                Point(x=0.0, y=0.0),
                Point(x=2.0, y=2.0),
                Point(x=0.0, y=2.0),
                Point(x=2.0, y=0.0),
            ),
            "bow-tie",
        ),
        (
            (
                Point(x=0.0, y=0.0),
                Point(x=4.0, y=0.0),
                Point(x=4.0, y=4.0),
                Point(x=0.0, y=4.0),
                Point(x=0.0, y=2.0),
                Point(x=2.0, y=2.0),
                Point(x=2.0, y=0.0),
            ),
            "edge-touching",
        ),
    ],
)
def test_polygon_geometry_rejects_invalid_shapes(
    points: tuple[Point, ...],
    case_name: str,
) -> None:
    with pytest.raises(ValidationError, match="valid simple polygon"):
        PolygonGeometry(points=points)


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


def test_canonical_layout_rejects_zero_length_blocker() -> None:
    payload = _layout().model_dump()
    payload["blockers"][0]["end"] = payload["blockers"][0]["start"]

    with pytest.raises(ValidationError, match="zero length"):
        CanonicalLayout.model_validate(payload)


def test_canonical_layout_rejects_blocker_outside_referenced_footprint() -> None:
    payload = _layout().model_dump()
    payload["blockers"][1]["start"] = {"x": 20.0, "y": 20.0}
    payload["blockers"][1]["end"] = {"x": 25.0, "y": 20.0}

    with pytest.raises(ValidationError, match="outside terrain footprint"):
        CanonicalLayout.model_validate(payload)


def test_canonical_layout_rejects_endpoint_only_blocker_footprint_overlap() -> None:
    payload = _layout().model_dump()
    payload["blockers"][1]["start"] = {"x": 12.0, "y": 4.0}
    payload["blockers"][1]["end"] = {"x": 20.0, "y": 4.0}

    with pytest.raises(ValidationError, match="outside terrain footprint"):
        CanonicalLayout.model_validate(payload)


def test_canonical_layout_rejects_duplicate_validation_record_codes() -> None:
    payload = _layout().model_dump(mode="json")
    payload["validation_records"].append(payload["validation_records"][0])

    with pytest.raises(ValidationError, match="duplicate validation record code"):
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


def test_canonical_json_and_hash_are_stable_across_validation_record_order() -> None:
    first_payload = _layout().model_dump()
    first_payload["validation_records"] = [
        {
            "code": "zeta",
            "severity": "info",
            "message": "Later code.",
        },
        {
            "code": "alpha",
            "severity": "warning",
            "message": "Earlier code.",
        },
    ]
    second_payload = _layout().model_dump()
    second_payload["validation_records"] = list(reversed(first_payload["validation_records"]))

    first = CanonicalLayout.model_validate(first_payload)
    second = CanonicalLayout.model_validate(second_payload)

    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert stable_layout_hash(first) == stable_layout_hash(second)


def test_canonical_json_uses_fixed_float_precision() -> None:
    payload = _layout().model_dump(mode="json")
    payload["deployments"][0]["area"]["points"][2] = {"x": 43.23456789, "y": 10.34567891}
    layout = CanonicalLayout.model_validate(payload)

    canonical_json = canonical_json_bytes(layout).decode("utf-8")

    assert "43.2346" in canonical_json
    assert "10.3457" in canonical_json
    assert "43.23456789" not in canonical_json


def test_canonical_json_normalizes_negative_zero() -> None:
    payload = _layout().model_dump(mode="json")
    payload["deployments"][0]["area"]["points"][0] = {"x": -0.0, "y": -0.0}
    layout = CanonicalLayout.model_validate(payload)

    canonical_json = canonical_json_bytes(layout).decode("utf-8")

    assert "-0.0" not in canonical_json


def test_canonical_json_rejects_non_standard_float_payloads() -> None:
    with pytest.raises(ValueError):
        canonical_json_bytes({"value": float("nan")})


def test_canonical_models_are_immutable_after_validation() -> None:
    layout = _layout()

    with pytest.raises(ValidationError):
        layout.name = "Mutated"

    with pytest.raises(ValidationError):
        layout.terrain_features[0].label = "Mutated"

    assert isinstance(layout.terrain_features, tuple)


def test_source_manifest_reports_cache_status_without_committing_pdfs(tmp_path: Path) -> None:
    relative_cache_path = Path("data/pdfs/terrain-layouts.pdf")
    cached_pdf = tmp_path / relative_cache_path
    cached_pdf.parent.mkdir(parents=True)
    cached_pdf.write_bytes(b"official bytes stay local")

    manifest = SourceManifest(
        documents=(
            SourceDocument(
                document_id="terrain-layouts-2026-06-12",
                kind=SourceKind.TERRAIN_LAYOUTS,
                url="https://assets.warhammer-community.com/example-terrain.pdf",
                expected_sha256="1cfc9e4bbcd4a4ad1fe2c6d096b30c6b28ebf057bb8b789f4d3c761b49ac11db",
                cache_path=relative_cache_path,
                redistribution="do-not-commit",
            ),
        )
    )

    [status] = manifest.cache_statuses(repo_root=tmp_path)

    assert status.document_id == "terrain-layouts-2026-06-12"
    assert status.status == CacheStatus.HASH_MISMATCH
    assert status.cache_path == relative_cache_path


def test_source_manifest_resolves_cache_relative_to_repo_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    relative_cache_path = Path("data/pdfs/rules.pdf")
    cached_pdf = tmp_path / relative_cache_path
    cached_pdf.parent.mkdir(parents=True)
    cached_pdf.write_bytes(b"stable bytes")
    outside_cwd = tmp_path / "outside-cwd"
    outside_cwd.mkdir()
    monkeypatch.chdir(outside_cwd)

    manifest = SourceManifest(
        documents=(
            SourceDocument(
                document_id="core-rules-2026-06-01",
                kind=SourceKind.RULES,
                url="https://assets.warhammer-community.com/example-rules.pdf",
                expected_sha256=sha256(b"stable bytes").hexdigest(),
                cache_path=relative_cache_path,
                redistribution="do-not-commit",
            ),
        )
    )

    [status] = manifest.cache_statuses(repo_root=tmp_path)

    assert status.status == CacheStatus.HASH_MATCH


@pytest.mark.parametrize(
    "cache_path",
    [
        Path.cwd() / "data" / "pdfs" / "absolute.pdf",
        Path("../escape.pdf"),
        Path("other/cache.pdf"),
    ],
)
def test_source_manifest_rejects_unsafe_cache_paths(cache_path: Path) -> None:
    with pytest.raises(ValidationError, match="relative path under data/pdfs"):
        SourceDocument(
            document_id="unsafe-cache",
            kind=SourceKind.RULES,
            url="https://assets.warhammer-community.com/example.pdf",
            expected_sha256="1cfc9e4bbcd4a4ad1fe2c6d096b30c6b28ebf057bb8b789f4d3c761b49ac11db",
            cache_path=cache_path,
            redistribution="do-not-commit",
        )


@pytest.mark.parametrize(
    "url",
    [
        "not-a-url",
        "http://assets.warhammer-community.com/example.pdf",
        "https://example.com/example.pdf",
    ],
)
def test_source_manifest_rejects_untrusted_urls(url: str) -> None:
    with pytest.raises(ValidationError, match="official Warhammer Community asset URL"):
        SourceDocument(
            document_id="bad-url",
            kind=SourceKind.RULES,
            url=url,
            expected_sha256="1cfc9e4bbcd4a4ad1fe2c6d096b30c6b28ebf057bb8b789f4d3c761b49ac11db",
            cache_path=Path("data/pdfs/example.pdf"),
            redistribution="do-not-commit",
        )


def test_source_manifest_rejects_malformed_sha256() -> None:
    with pytest.raises(ValidationError, match="64 lowercase hex"):
        SourceDocument(
            document_id="bad-hash",
            kind=SourceKind.RULES,
            url="https://assets.warhammer-community.com/example.pdf",
            expected_sha256="not-a-hash",
            cache_path=Path("data/pdfs/example.pdf"),
            redistribution="do-not-commit",
        )


def test_source_manifest_rejects_duplicate_document_ids() -> None:
    document = SourceDocument(
        document_id="duplicate",
        kind=SourceKind.RULES,
        url="https://assets.warhammer-community.com/example.pdf",
        expected_sha256="1cfc9e4bbcd4a4ad1fe2c6d096b30c6b28ebf057bb8b789f4d3c761b49ac11db",
        cache_path=Path("data/pdfs/example.pdf"),
        redistribution="do-not-commit",
    )

    with pytest.raises(ValidationError, match="duplicate source document id"):
        SourceManifest(documents=(document, document))


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
