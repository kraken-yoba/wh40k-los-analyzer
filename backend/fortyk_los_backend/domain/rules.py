from enum import StrEnum
from pathlib import Path

import fitz
from pydantic import Field

from fortyk_los_backend.domain.models import CanonicalBaseModel

RULES_TERRAIN_SEMANTICS_METHOD = "core-rules-terrain-semantics-v1"


class RulesBackingStatus(StrEnum):
    BACKED = "backed"
    MISSING_ANCHOR = "missing_anchor"


class RuleAnchor(CanonicalBaseModel):
    section: str
    page_number: int = Field(ge=1)
    terms: tuple[str, ...]


class RuleTerrainSemantic(CanonicalBaseModel):
    code: str
    summary: str
    source_sections: tuple[str, ...]
    source_pages: tuple[int, ...]
    engine_implication: str
    anchors: tuple[RuleAnchor, ...]


class RuleTerrainSemanticsExtraction(CanonicalBaseModel):
    extraction_method: str = RULES_TERRAIN_SEMANTICS_METHOD
    backing_status: RulesBackingStatus
    rules: tuple[RuleTerrainSemantic, ...]
    missing_anchor_codes: tuple[str, ...] = ()


class _SectionAnchorSpec(CanonicalBaseModel):
    section: str
    heading: str
    terms_after_heading: tuple[str, ...]


class _RuleSpec(CanonicalBaseModel):
    code: str
    summary: str
    source_sections: tuple[str, ...]
    required_anchors: tuple[_SectionAnchorSpec, ...]
    engine_implication: str


RULE_SPECS = (
    _RuleSpec(
        code="visibility_line_of_sight",
        summary=(
            "Visibility starts from line of sight between models; the app models this as "
            "base-aware 2D visibility between selected board positions."
        ),
        source_sections=("Visibility 06.01",),
        required_anchors=(
            _SectionAnchorSpec(
                section="Visibility 06.01",
                heading="VISIBILITY 06.01",
                terms_after_heading=("Line of sight", "observing model"),
            ),
        ),
        engine_implication=(
            "LOS clicks and heatmaps evaluate sampled 2D source-to-target lines against "
            "canonical blocker segments."
        ),
    ),
    _RuleSpec(
        code="terrain_categories",
        summary=(
            "The rules classify terrain into Exposed, Light, and Dense categories; the "
            "Event Companion extraction keeps those categories distinct."
        ),
        source_sections=("Terrain Categories 13.02",),
        required_anchors=(
            _SectionAnchorSpec(
                section="Terrain Categories 13.02",
                heading="TERRAIN CATEGORIES 13.02",
                terms_after_heading=(
                    "EXPOSED 13.03",
                    "LIGHT 13.04",
                    "DENSE 13.05",
                    "movement and visibility",
                ),
            ),
        ),
        engine_implication=(
            "Terrain fills and counts are category-aware so Dense, Light, Exposed, and "
            "Unknown features are not visually conflated."
        ),
    ),
    _RuleSpec(
        code="dense_solid_blocks_2d_los",
        summary=(
            "Dense terrain is the category with Solid wall relevance for this 2D LOS "
            "implementation."
        ),
        source_sections=("Terrain and Visibility 13.07", "Solid 13.11"),
        required_anchors=(
            _SectionAnchorSpec(
                section="Terrain and Visibility 13.07",
                heading="TERRAIN AND VISIBILITY 13.07",
                terms_after_heading=("Terrain can affect visibility", "depending on whether"),
            ),
            _SectionAnchorSpec(
                section="Solid 13.11",
                heading="SOLID 13.11",
                terms_after_heading=("Dense terrain features", "ground level"),
            ),
        ),
        engine_implication=(
            "Matched Dense footprint fragments are the only official-layout wall candidates "
            "used by the current 2D LOS engine."
        ),
    ),
    _RuleSpec(
        code="light_exposed_not_opaque_blockers",
        summary=(
            "Light and Exposed terrain can matter for terrain context, movement, or cover, "
            "but this first 2D LOS pass does not treat them as opaque wall segments."
        ),
        source_sections=("Terrain Categories 13.02", "Terrain and Movement 13.06"),
        required_anchors=(
            _SectionAnchorSpec(
                section="Terrain Categories 13.02",
                heading="TERRAIN CATEGORIES 13.02",
                terms_after_heading=("EXPOSED 13.03", "LIGHT 13.04", "movement and visibility"),
            ),
            _SectionAnchorSpec(
                section="Terrain and Movement 13.06",
                heading="TERRAIN AND MOVEMENT 13.06",
                terms_after_heading=("Exposed/Light", "vertically"),
            ),
        ),
        engine_implication=(
            "Light and Exposed features remain visible terrain context and are not emitted as "
            "opaque LOS blocker segments."
        ),
    ),
    _RuleSpec(
        code="future_3d_rules_scope",
        summary=(
            "The current engine intentionally stays base-aware and 2D; vertical levels, "
            "height-sensitive visibility, cover, Hidden, and Obscuring are future scope."
        ),
        source_sections=("Terrain and Visibility 13.07", "Solid 13.11"),
        required_anchors=(
            _SectionAnchorSpec(
                section="Terrain and Visibility 13.07",
                heading="TERRAIN AND VISIBILITY 13.07",
                terms_after_heading=("depending on whether", "OBSCURING 13.10"),
            ),
            _SectionAnchorSpec(
                section="Solid 13.11",
                heading="SOLID 13.11",
                terms_after_heading=("ground level",),
            ),
        ),
        engine_implication=(
            "Future builds can add full 3D-aware LOS after the deterministic 2D geometry and "
            "review workflow are accepted."
        ),
    ),
)


def extract_rules_terrain_semantics(pdf_path: Path) -> RuleTerrainSemanticsExtraction:
    page_texts = _page_texts(pdf_path)
    rules: list[RuleTerrainSemantic] = []
    missing_anchor_codes: list[str] = []
    for spec in RULE_SPECS:
        anchors = _anchors_for_spec(page_texts, spec)
        if len(anchors) != len(spec.required_anchors):
            missing_anchor_codes.append(spec.code)
            continue
        source_pages = tuple(
            sorted({anchor.page_number for anchor in anchors})
        )
        rules.append(
            RuleTerrainSemantic(
                code=spec.code,
                summary=spec.summary,
                source_sections=spec.source_sections,
                source_pages=source_pages,
                engine_implication=spec.engine_implication,
                anchors=tuple(anchors),
            )
        )

    return RuleTerrainSemanticsExtraction(
        backing_status=(
            RulesBackingStatus.BACKED
            if not missing_anchor_codes
            else RulesBackingStatus.MISSING_ANCHOR
        ),
        rules=tuple(rules) if not missing_anchor_codes else (),
        missing_anchor_codes=tuple(missing_anchor_codes),
    )


def _page_texts(pdf_path: Path) -> tuple[str, ...]:
    with fitz.open(pdf_path) as document:
        return tuple(page.get_text("text") for page in document)


def _anchors_for_spec(
    page_texts: tuple[str, ...],
    spec: _RuleSpec,
) -> list[RuleAnchor]:
    anchors: list[RuleAnchor] = []
    for anchor_spec in spec.required_anchors:
        page_number = _first_page_with_anchor(page_texts, anchor_spec)
        if page_number is None:
            continue
        anchors.append(
            RuleAnchor(
                section=anchor_spec.section,
                page_number=page_number,
                terms=(anchor_spec.heading, *anchor_spec.terms_after_heading),
            )
        )
    return anchors


def _first_page_with_anchor(
    page_texts: tuple[str, ...],
    anchor_spec: _SectionAnchorSpec,
) -> int | None:
    folded_heading = anchor_spec.heading.casefold()
    folded_terms = tuple(term.casefold() for term in anchor_spec.terms_after_heading)
    for index, text in enumerate(page_texts, start=1):
        folded_text = text.casefold()
        heading_index = folded_text.find(folded_heading)
        if heading_index < 0:
            continue
        body_text = folded_text[heading_index + len(folded_heading) :]
        if all(term in body_text for term in folded_terms):
            return index
    return None
