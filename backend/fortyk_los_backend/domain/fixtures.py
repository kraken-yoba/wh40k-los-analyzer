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
from fortyk_los_backend.domain.models import CanonicalLayout, ReviewStatus, ValidationSeverity
from fortyk_los_backend.domain.rules import (
    RULES_TERRAIN_SEMANTICS_METHOD,
    extract_rules_terrain_semantics,
)
from fortyk_los_backend.domain.serialization import stable_layout_hash
from fortyk_los_backend.domain.source_underlay import render_event_companion_board_underlay
from fortyk_los_backend.domain.visual_sanity import (
    EventCompanionVisualSanityReport,
    VisualSanityStatus,
    run_event_companion_visual_sanity,
)


class FixtureRepository:
    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root
        self._layout_dir = repo_root / "fixtures" / "layouts"
        self._source_manifest_path = repo_root / "fixtures" / "source_manifest.official.json"
        self._terrain_footprint_template_cache: tuple[TerrainFootprintTemplate, ...] | None = None
        self._accepted_validation_records: dict[tuple[str, str], set[str]] = {}

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
                return self._apply_accepted_validation_records(layout)
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
                layout = extract_event_companion_layout(
                    event_document_path,
                    page_number=page.page_number,
                    footprint_templates=footprint_templates,
                )
                return self._apply_accepted_validation_records(layout)
        return None

    def accept_validation_record(
        self,
        layout_id: str,
        record_code: str,
        *,
        layout_hash: str,
    ) -> CanonicalLayout | None:
        layout = self.get_layout(layout_id)
        if layout is None:
            return None
        if stable_layout_hash(layout) != layout_hash:
            raise StaleLayoutAcceptanceError(layout_id)

        record = next(
            (candidate for candidate in layout.validation_records if candidate.code == record_code),
            None,
        )
        if record is None:
            raise ValueError(f"Validation record not found: {record_code}")
        if record.severity != ValidationSeverity.WARNING:
            raise ValueError(f"Only warning validation records can be accepted: {record_code}")

        review_scope_hash = _review_scope_hash(layout)
        self._accepted_validation_records.setdefault((layout_id, review_scope_hash), set()).add(
            record_code
        )
        accepted_layout = self.get_layout(layout_id)
        if accepted_layout is None:
            raise RuntimeError(f"Accepted layout disappeared: {layout_id}")
        return accepted_layout

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

    def visual_sanity_evidence(
        self,
        layout_id: str,
    ) -> EventCompanionVisualSanityReport | dict[str, object] | None:
        layout = self.get_layout(layout_id)
        if layout is None:
            return None
        if layout.provenance.extraction_method != "event-companion-vector-v1":
            return _unavailable_visual_sanity(layout)

        event_document_path = self._hash_matched_event_companion_path()
        if event_document_path is None:
            return _unavailable_visual_sanity(layout)

        return run_event_companion_visual_sanity(
            event_document_path,
            page_number=layout.provenance.source_page,
            layout=layout,
        )

    def source_underlay_png(self, layout: CanonicalLayout) -> bytes | None:
        if layout.provenance.extraction_method != "event-companion-vector-v1":
            return None

        event_document_path = self._hash_matched_event_companion_path()
        if event_document_path is None:
            return None

        return render_event_companion_board_underlay(
            event_document_path,
            page_number=layout.provenance.source_page,
        )

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

    def rules_terrain_semantics_evidence(self) -> dict[str, object]:
        document_statuses = self._source_document_statuses(SourceKind.RULES)
        if not document_statuses:
            return _unavailable_rules_terrain_semantics(
                source_document_id=None,
                cache_status=None,
            )
        if len(document_statuses) > 1:
            return _unavailable_rules_terrain_semantics(
                source_document_id=None,
                cache_status=None,
                backing_status="source_ambiguous",
            )

        document, status = document_statuses[0]
        if status.status != CacheStatus.HASH_MATCH:
            return _unavailable_rules_terrain_semantics(
                source_document_id=document.document_id,
                cache_status=status,
            )

        extraction = extract_rules_terrain_semantics(
            (self._repo_root / document.cache_path).resolve()
        )
        return {
            "source_document_id": document.document_id,
            "cache_status": status,
            "extraction_method": extraction.extraction_method,
            "backing_status": extraction.backing_status,
            "rules": extraction.rules,
            "missing_anchor_codes": extraction.missing_anchor_codes,
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
        if self._terrain_footprint_template_cache is not None:
            return self._terrain_footprint_template_cache
        document_status = self._source_document_status(SourceKind.TERRAIN_LAYOUTS)
        if document_status is None:
            self._terrain_footprint_template_cache = ()
            return ()
        document, status = document_status
        if status.status != CacheStatus.HASH_MATCH:
            self._terrain_footprint_template_cache = ()
            return ()
        self._terrain_footprint_template_cache = extract_terrain_footprint_templates(
            (self._repo_root / document.cache_path).resolve()
        )
        return self._terrain_footprint_template_cache

    def _source_document_status(
        self,
        kind: SourceKind,
    ) -> tuple[SourceDocument, SourceCacheStatus] | None:
        document_statuses = self._source_document_statuses(kind)
        if not document_statuses:
            return None
        return document_statuses[0]

    def _source_document_statuses(
        self,
        kind: SourceKind,
    ) -> tuple[tuple[SourceDocument, SourceCacheStatus], ...]:
        manifest = self.source_manifest()
        statuses = {
            status.document_id: status
            for status in manifest.cache_statuses(repo_root=self._repo_root)
        }
        return tuple(
            (document, statuses[document.document_id])
            for document in manifest.documents
            if document.kind == kind
        )

    def _apply_accepted_validation_records(self, layout: CanonicalLayout) -> CanonicalLayout:
        accepted_codes = self._accepted_validation_records.get(
            (layout.layout_id, _review_scope_hash(layout)),
            set(),
        )
        if not accepted_codes:
            return layout

        records = tuple(
            record.model_copy(update={"review_status": ReviewStatus.ACCEPTED})
            if record.code in accepted_codes and record.severity == ValidationSeverity.WARNING
            else record
            for record in layout.validation_records
        )
        return layout.model_copy(update={"validation_records": records})


class StaleLayoutAcceptanceError(ValueError):
    def __init__(self, layout_id: str) -> None:
        super().__init__(f"Layout hash does not match current layout: {layout_id}")


def _review_scope_hash(layout: CanonicalLayout) -> str:
    review_scope_records = tuple(
        record.model_copy(update={"review_status": ReviewStatus.UNREVIEWED})
        if record.severity == ValidationSeverity.WARNING
        else record
        for record in layout.validation_records
    )
    return stable_layout_hash(
        layout.model_copy(update={"validation_records": review_scope_records})
    )


def _unavailable_visual_sanity(layout: CanonicalLayout) -> dict[str, object]:
    return {
        "layout_id": layout.layout_id,
        "source_page": layout.provenance.source_page,
        "extraction_method": "event-companion-cv-sanity-v1",
        "status": VisualSanityStatus.UNAVAILABLE,
        "checks": [],
        "vision_advisory": {
            "status": "not_run",
            "reason": "Visual sanity checks require a hash-matched Event Companion PDF layout.",
            "input": "none",
        },
    }


def _unavailable_rules_terrain_semantics(
    *,
    source_document_id: str | None,
    cache_status: SourceCacheStatus | None,
    backing_status: str = "source_unavailable",
) -> dict[str, object]:
    return {
        "source_document_id": source_document_id,
        "cache_status": cache_status,
        "extraction_method": RULES_TERRAIN_SEMANTICS_METHOD,
        "backing_status": backing_status,
        "rules": [],
        "missing_anchor_codes": [],
    }
