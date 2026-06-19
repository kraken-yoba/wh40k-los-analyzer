from __future__ import annotations

from warhammer_companion.rules.core_rules import build_core_rules_pack
from warhammer_companion.rules.models import ReadinessState


def test_core_rules_pack_identifies_official_source_metadata() -> None:
    pack = build_core_rules_pack()

    assert pack.rules_pack_id == "wh40k-11e-core-2026-06-01"
    assert pack.edition_id == "wh40k-11e"
    assert pack.readiness == ReadinessState.TRUSTED
    assert pack.source_documents[0].source_ref.source_document_id == "core-rules-2026-06-01"
    assert pack.source_documents[0].source_ref.local_filename == "core-rules.pdf"
    assert pack.source_documents[0].source_ref.sha256 == (
        "f6a2443a44627ac5f0ef08407d29aa5ec7e97339998f05bc35f3ae37bf276833"
    )


def test_core_rules_pack_contains_required_source_anchors() -> None:
    pack = build_core_rules_pack()
    anchors = {section.section_id: section for section in pack.source_sections}

    required_section_ids = [
        "03.04",
        "05.01",
        "13.08",
        "13.09",
        "13.10",
        "13.11",
        "14.01",
        "16.01",
        "20.04",
    ]
    for section_id in required_section_ids:
        assert section_id in anchors
        assert anchors[section_id].page_number > 0
        assert anchors[section_id].source_document_id == "core-rules-2026-06-01"


def test_core_rules_pack_maps_current_rules_concepts() -> None:
    pack = build_core_rules_pack()
    concepts = {concept.concept_id: concept for concept in pack.concept_mappings}

    assert concepts["benefit_of_cover"].display_label == "Benefit of Cover"
    assert "bs_worsening" in concepts["benefit_of_cover"].mechanic_tags
    assert "save_modifier" not in concepts["benefit_of_cover"].mechanic_tags

    assert "2in_horizontal_5in_vertical" in concepts["engagement_range"].mechanic_tags
    assert "1in_horizontal_only" not in concepts["engagement_range"].mechanic_tags

    assert concepts["reserve_arrival_method"].display_label == "Ingress Move"
    assert "Deep Strike-modified Ingress Move" in concepts[
        "reserve_arrival_method"
    ].related_terms

    assert concepts["objective_region"].display_label == "Terrain Objective"
    assert "terrain_area_range" in concepts["objective_region"].mechanic_tags

    assert set(concepts["visibility_state"].related_terms) >= {
        "visible",
        "fully visible",
        "Hidden",
        "Obscuring",
        "Solid",
    }
