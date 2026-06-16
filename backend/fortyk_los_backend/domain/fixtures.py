from pathlib import Path

from fortyk_los_backend.domain.extraction import (
    extract_event_companion_layout,
    list_event_companion_layout_pages,
)
from fortyk_los_backend.domain.manifest import CacheStatus, SourceKind, SourceManifest
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
                    "source": "fixture",
                }
            )
        layouts.extend(self.list_extracted_layouts())
        return layouts

    def get_layout(self, layout_id: str) -> CanonicalLayout | None:
        for layout_path in sorted(self._layout_dir.glob("*.layout.json")):
            layout = self.load_layout_by_path(layout_path)
            if layout.layout_id == layout_id:
                return layout
        return self.get_extracted_layout(layout_id)

    def list_extracted_layouts(self) -> list[dict[str, str]]:
        event_document_path = self._hash_matched_event_companion_path()
        if event_document_path is None:
            return []

        layouts: list[dict[str, str]] = []
        for page in list_event_companion_layout_pages(event_document_path):
            layout = extract_event_companion_layout(
                event_document_path,
                page_number=page.page_number,
            )
            layouts.append(
                {
                    "layout_id": layout.layout_id,
                    "name": layout.name,
                    "layout_hash": stable_layout_hash(layout),
                    "source": "extracted",
                    "source_document_id": layout.provenance.source_document_id,
                    "source_page": str(layout.provenance.source_page),
                    "validation_status": layout.validation_status.value,
                }
            )
        return layouts

    def get_extracted_layout(self, layout_id: str) -> CanonicalLayout | None:
        event_document_path = self._hash_matched_event_companion_path()
        if event_document_path is None:
            return None
        for page in list_event_companion_layout_pages(event_document_path):
            if page.layout_id == layout_id:
                return extract_event_companion_layout(
                    event_document_path,
                    page_number=page.page_number,
                )
        return None

    def load_layout_by_path(self, layout_path: Path) -> CanonicalLayout:
        return CanonicalLayout.model_validate_json(layout_path.read_text(encoding="utf-8"))

    def source_manifest(self) -> SourceManifest:
        return SourceManifest.model_validate_json(
            self._source_manifest_path.read_text(encoding="utf-8")
        )

    def _hash_matched_event_companion_path(self) -> Path | None:
        manifest = self.source_manifest()
        statuses = {
            status.document_id: status
            for status in manifest.cache_statuses(repo_root=self._repo_root)
        }
        for document in manifest.documents:
            if document.kind != SourceKind.EVENT_COMPANION:
                continue
            status = statuses[document.document_id]
            if status.status != CacheStatus.HASH_MATCH:
                return None
            return (self._repo_root / document.cache_path).resolve()
        return None
