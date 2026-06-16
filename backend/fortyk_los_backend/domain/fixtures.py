from pathlib import Path

from fortyk_los_backend.domain.manifest import SourceManifest
from fortyk_los_backend.domain.models import CanonicalLayout
from fortyk_los_backend.domain.serialization import stable_layout_hash


class FixtureRepository:
    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root
        self._layout_dir = repo_root / "fixtures" / "layouts"
        self._source_manifest_path = repo_root / "fixtures" / "source_manifest.official.json"

    def list_layouts(self) -> list[dict[str, str]]:
        layouts: list[dict[str, str]] = []
        for layout_path in sorted(self._layout_dir.glob("*.layout.json")):
            layout = self.load_layout_by_path(layout_path)
            layouts.append(
                {
                    "layout_id": layout.layout_id,
                    "name": layout.name,
                    "layout_hash": stable_layout_hash(layout),
                }
            )
        return layouts

    def get_layout(self, layout_id: str) -> CanonicalLayout | None:
        for layout_path in sorted(self._layout_dir.glob("*.layout.json")):
            layout = self.load_layout_by_path(layout_path)
            if layout.layout_id == layout_id:
                return layout
        return None

    def load_layout_by_path(self, layout_path: Path) -> CanonicalLayout:
        return CanonicalLayout.model_validate_json(layout_path.read_text(encoding="utf-8"))

    def source_manifest(self) -> SourceManifest:
        return SourceManifest.model_validate_json(
            self._source_manifest_path.read_text(encoding="utf-8")
        )
