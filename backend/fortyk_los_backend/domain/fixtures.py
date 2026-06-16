from pathlib import Path

from fortyk_los_backend.domain.extraction import (
    TerrainFootprintMatch,
    TerrainFootprintTemplate,
    extract_event_companion_layout,
    extract_terrain_footprint_outlines,
    extract_terrain_footprint_templates,
    list_event_companion_layout_pages,
    match_terrain_features_to_footprints,
)
from fortyk_los_backend.domain.manifest import (
    CacheStatus,
    SourceCacheStatus,
    SourceDocument,
    SourceKind,
    SourceManifest,
)
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

        footprint_templates = self._terrain_footprint_templates()
        layouts: list[dict[str, str]] = []
        for page in list_event_companion_layout_pages(event_document_path):
            layout = extract_event_companion_layout(
                event_document_path,
                page_number=page.page_number,
                footprint_templates=footprint_templates,
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
        footprint_templates = self._terrain_footprint_templates()
        for page in list_event_companion_layout_pages(event_document_path):
            if page.layout_id == layout_id:
                return extract_event_companion_layout(
                    event_document_path,
                    page_number=page.page_number,
                    footprint_templates=footprint_templates,
                )
        return None

    def footprint_match_evidence(self, layout_id: str) -> dict[str, object] | None:
        layout = self.get_layout(layout_id)
        if layout is None:
            return None

        document_status = self._source_document_status(SourceKind.TERRAIN_LAYOUTS)
        if document_status is None:
            return {
                "layout_id": layout.layout_id,
                "source_document_id": None,
                "cache_status": None,
                "extraction_method": "terrain-footprint-match-v1",
                "matches": [],
            }

        document, status = document_status
        templates = self._terrain_footprint_templates()
        matches: list[TerrainFootprintMatch] = []
        if (
            templates
            and layout.provenance.extraction_method == "event-companion-vector-v1"
        ):
            matches = list(match_terrain_features_to_footprints(layout, templates))
        return {
            "layout_id": layout.layout_id,
            "source_document_id": document.document_id,
            "cache_status": status,
            "extraction_method": "terrain-footprint-match-v1",
            "matches": matches,
        }

    def terrain_footprint_evidence(self) -> dict[str, object]:
        document_status = self._source_document_status(SourceKind.TERRAIN_LAYOUTS)
        if document_status is not None:
            document, status = document_status
            outlines = []
            if status.status == CacheStatus.HASH_MATCH:
                outlines = list(
                    extract_terrain_footprint_outlines(
                        (self._repo_root / document.cache_path).resolve()
                    )
                )
            return {
                "source_document_id": document.document_id,
                "cache_status": status,
                "extraction_method": "terrain-footprint-vector-v1",
                "outlines": outlines,
            }
        return {
            "source_document_id": None,
            "cache_status": None,
            "extraction_method": "terrain-footprint-vector-v1",
            "outlines": [],
        }

    def load_layout_by_path(self, layout_path: Path) -> CanonicalLayout:
        return CanonicalLayout.model_validate_json(layout_path.read_text(encoding="utf-8"))

    def source_manifest(self) -> SourceManifest:
        return SourceManifest.model_validate_json(
            self._source_manifest_path.read_text(encoding="utf-8")
        )

    def _hash_matched_event_companion_path(self) -> Path | None:
        document_status = self._source_document_status(SourceKind.EVENT_COMPANION)
        if document_status is None:
            return None
        document, status = document_status
        if status.status != CacheStatus.HASH_MATCH:
            return None
        return (self._repo_root / document.cache_path).resolve()

    def _terrain_footprint_templates(self) -> tuple[TerrainFootprintTemplate, ...]:
        document_status = self._source_document_status(SourceKind.TERRAIN_LAYOUTS)
        if document_status is None:
            return ()
        document, status = document_status
        if status.status != CacheStatus.HASH_MATCH:
            return ()
        return extract_terrain_footprint_templates(
            (self._repo_root / document.cache_path).resolve()
        )

    def _source_document_status(
        self,
        kind: SourceKind,
    ) -> tuple[SourceDocument, SourceCacheStatus] | None:
        manifest = self.source_manifest()
        statuses = {
            status.document_id: status
            for status in manifest.cache_statuses(repo_root=self._repo_root)
        }
        for document in manifest.documents:
            if document.kind == kind:
                return document, statuses[document.document_id]
        return None
