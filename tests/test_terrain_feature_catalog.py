from __future__ import annotations

from pathlib import Path

from warhammer_companion.ingestion.terrain_feature_catalog import (
    FEATURE_CATALOG_VERSION,
    TERRAIN_FEATURE_TYPES,
    terrain_feature_type_by_id,
)


def test_catalog_entries_require_database_fields_and_assets() -> None:
    assert FEATURE_CATALOG_VERSION >= 1
    assert len(TERRAIN_FEATURE_TYPES) >= 5

    type_ids = {entry.type_id for entry in TERRAIN_FEATURE_TYPES}
    assert {"ruined-wall-l", "ruined-wall-u", "armoured-container"}.issubset(type_ids)

    for entry in TERRAIN_FEATURE_TYPES:
        assert entry.type_id
        assert entry.display_name
        assert entry.description
        assert entry.representative_image_path.endswith(".svg")
        assert entry.blocker_template
        assert entry.typical_positions
        assert entry.feature_profile
        assert Path(entry.resolved_representative_image_path()).exists()


def test_catalog_lookup_rejects_unknown_type_ids() -> None:
    assert terrain_feature_type_by_id("ruined-wall-u").feature_profile == "ruined_wall_u"

    try:
        terrain_feature_type_by_id("missing-type")
    except KeyError as exc:
        assert "missing-type" in str(exc)
    else:
        raise AssertionError("unknown type id should raise KeyError")
