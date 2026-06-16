import json
from pathlib import Path

from pydantic import BaseModel

from fortyk_los_backend.domain.manifest import SourceManifest
from fortyk_los_backend.domain.models import CanonicalLayout

SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "canonical_layout.schema.json": CanonicalLayout,
    "source_manifest.schema.json": SourceManifest,
}


def export_json_schemas(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    exported_paths: list[Path] = []
    for filename, model in sorted(SCHEMA_MODELS.items()):
        schema = model.model_json_schema()
        path = output_dir / filename
        path.write_text(
            json.dumps(schema, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        exported_paths.append(path)

    return exported_paths
