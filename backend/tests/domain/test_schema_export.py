from pathlib import Path

from fortyk_los_backend.domain.schema_export import export_json_schemas


def test_schema_export_is_stable_and_matches_committed_files(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]

    exported_paths = export_json_schemas(tmp_path)

    assert {path.name for path in exported_paths} == {
        "canonical_layout.schema.json",
        "source_manifest.schema.json",
    }
    for exported_path in exported_paths:
        committed_path = repo_root / "schemas" / exported_path.name
        assert committed_path.read_text(encoding="utf-8") == exported_path.read_text(
            encoding="utf-8"
        )
