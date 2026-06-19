from __future__ import annotations

from warhammer_companion.rules.models import (
    CanonicalRulesPack,
    ConceptMapping,
    GlossaryTerm,
    ReadinessState,
    RuleSection,
    RuleSourceDocument,
)
from warhammer_companion.rules.sources import SourceAuthority, SourceKind, SourceRef, SourceTrustState

CORE_RULES_DOCUMENT_ID = "core-rules-2026-06-01"
CORE_RULES_PACK_ID = "wh40k-11e-core-2026-06-01"
CORE_RULES_URL = (
    "https://assets.warhammer-community.com/"
    "eng_01-06_warhammer40k_new40k_core_rules-was6fbu1ix-hfewhmxyiy.pdf"
)
CORE_RULES_SHA256 = "f6a2443a44627ac5f0ef08407d29aa5ec7e97339998f05bc35f3ae37bf276833"


def build_core_rules_pack() -> CanonicalRulesPack:
    return CanonicalRulesPack(
        rules_pack_id=CORE_RULES_PACK_ID,
        edition_id="wh40k-11e",
        source_documents=(_core_rules_document(),),
        source_sections=_core_rules_sections(),
        glossary_terms=_core_glossary_terms(),
        concept_mappings=_core_concept_mappings(),
        readiness=ReadinessState.TRUSTED,
    )


def _core_rules_document() -> RuleSourceDocument:
    return RuleSourceDocument(
        source_ref=SourceRef(
            source_kind=SourceKind.OFFICIAL_PDF,
            authority=SourceAuthority.AUTHORITATIVE,
            trust_state=SourceTrustState.TRUSTED,
            source_document_id=CORE_RULES_DOCUMENT_ID,
            source_label="Warhammer 40,000 Core Rules",
            url=CORE_RULES_URL,
            local_filename="core-rules.pdf",
            sha256=CORE_RULES_SHA256,
            edition_id="wh40k-11e",
        ),
        page_count=88,
    )


def _core_rules_sections() -> tuple[RuleSection, ...]:
    return (
        _section("01.01", "Armies", 8, ("Armies",)),
        _section("02.02", "Profiles", 10, ("M", "T", "Sv", "W", "Ld", "OC")),
        _section("02.04", "Weapons", 11, ("R", "A", "BS", "WS", "S", "AP", "D")),
        _section("03.01", "Moving Units", 12, ("movement",)),
        _section("03.04", "Engagement", 14, ("Engagement Range",)),
        _section("05.01", "Hit Rolls", 18, ("Hit Rolls",)),
        _section("05.02", "Wound Rolls", 19, ("Wound Rolls",)),
        _section("05.03", "Save Rolls", 20, ("Save Rolls",)),
        _section("05.04", "Inflict Damage", 21, ("Inflict Damage",)),
        _section("06.01", "Visibility", 24, ("visible", "fully visible")),
        _section("09.05", "Normal Move", 32, ("Normal Move",)),
        _section("09.06", "Advance Move", 32, ("Advance Move",)),
        _section("09.07", "Fall-back Move", 32, ("Fall-back Move",)),
        _section("11.04", "Charge Move", 36, ("Charge Move",)),
        _section("13.02", "Terrain Categories", 48, ("Exposed", "Light", "Dense")),
        _section("13.07", "Terrain and Visibility", 50, ("Benefit of Cover", "Hidden")),
        _section("13.08", "Benefit of Cover", 50, ("Benefit of Cover",)),
        _section("13.09", "Hidden", 50, ("Hidden", "detection range")),
        _section("13.10", "Obscuring", 50, ("Obscuring",)),
        _section("13.11", "Solid", 51, ("Solid",)),
        _section("14.01", "Terrain Objectives", 52, ("Terrain Objective",)),
        _section("14.02", "Level of Control", 52, ("OC", "control")),
        _section("16.01", "Performing Actions", 58, ("Actions",)),
        _section("18.04", "Disembark Move", 62, ("Disembark Move",)),
        _section("20.04", "Ingress Move", 72, ("Ingress Move",)),
        _section("24.09", "Deep Strike", 80, ("Deep Strike",)),
    )


def _section(
    section_id: str,
    section_label: str,
    page_number: int,
    terms: tuple[str, ...],
) -> RuleSection:
    return RuleSection(
        source_document_id=CORE_RULES_DOCUMENT_ID,
        section_id=section_id,
        section_label=section_label,
        page_number=page_number,
        terms=terms,
    )


def _core_glossary_terms() -> tuple[GlossaryTerm, ...]:
    return (
        GlossaryTerm(
            term_id="benefit_of_cover",
            display_label="Benefit of Cover",
            source_section_ids=("13.08",),
        ),
        GlossaryTerm(
            term_id="hidden",
            display_label="Hidden",
            source_section_ids=("13.09",),
        ),
        GlossaryTerm(
            term_id="obscuring",
            display_label="Obscuring",
            source_section_ids=("13.10",),
        ),
        GlossaryTerm(
            term_id="solid",
            display_label="Solid",
            source_section_ids=("13.11",),
        ),
    )


def _core_concept_mappings() -> tuple[ConceptMapping, ...]:
    return (
        ConceptMapping(
            concept_id="benefit_of_cover",
            internal_name="visibility_trait_cover",
            display_label="Benefit of Cover",
            source_section_ids=("13.08",),
            related_terms=("ranged attack", "attacking BS"),
            mechanic_tags=("bs_worsening", "terrain_visibility_trait"),
        ),
        ConceptMapping(
            concept_id="engagement_range",
            internal_name="engagement_region",
            display_label="Engagement Range",
            source_section_ids=("03.04",),
            related_terms=("engaged", "unengaged"),
            mechanic_tags=("2in_horizontal_5in_vertical", "model_region"),
        ),
        ConceptMapping(
            concept_id="reserve_arrival_method",
            internal_name="reserve_arrival_method",
            display_label="Ingress Move",
            source_section_ids=("20.04", "24.09"),
            related_terms=("Strategic Reserves", "Deep Strike-modified Ingress Move"),
            mechanic_tags=("reserve_arrival", "ability_modified_ingress"),
        ),
        ConceptMapping(
            concept_id="objective_region",
            internal_name="objective_region",
            display_label="Terrain Objective",
            source_section_ids=("14.01", "14.02"),
            related_terms=("Objective Marker", "Level of Control", "OC"),
            mechanic_tags=("terrain_area_range", "control_level"),
        ),
        ConceptMapping(
            concept_id="visibility_state",
            internal_name="visibility_state",
            display_label="Visibility State",
            source_section_ids=("06.01", "13.07", "13.09", "13.10", "13.11"),
            related_terms=("visible", "fully visible", "Hidden", "Obscuring", "Solid"),
            mechanic_tags=("non_binary_visibility", "terrain_visibility_trait"),
        ),
        ConceptMapping(
            concept_id="action_capability",
            internal_name="action_capability",
            display_label="Performing Actions",
            source_section_ids=("16.01",),
            related_terms=("eligible to start an action", "performing action", "completes action"),
            mechanic_tags=("eligibility_restrictions", "completion_interruptions"),
        ),
    )
