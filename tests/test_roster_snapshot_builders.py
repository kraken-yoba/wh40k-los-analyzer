from __future__ import annotations

import hashlib

from warhammer_companion.application.roster_snapshots import (
    build_canonical_roster_index,
    build_roster_snapshot_profile_candidate_pack,
    canonical_army_with_source_refs,
)
from warhammer_companion.domain.rosters import (
    CanonicalArmy,
    RosterCost,
    RosterSelection,
    RosterSnapshotCharacteristic,
    RosterSnapshotProfile,
    RosterSnapshotRule,
)


def _snapshot_profile(
    *,
    raw_id: str,
    name: str,
    source_path: str,
    characteristic_id: str,
    characteristic_value: str,
) -> RosterSnapshotProfile:
    return RosterSnapshotProfile(
        raw_id=raw_id,
        name=name,
        type_id="synthetic-profile-type",
        type_name="Synthetic",
        source_path=source_path,
        characteristics=(
            RosterSnapshotCharacteristic(
                raw_id=characteristic_id,
                name="Synthetic",
                type_id="synthetic-characteristic",
                source_path=f"{source_path}/{characteristic_id}",
                value=characteristic_value,
                value_sha256=hashlib.sha256(characteristic_value.encode("utf-8")).hexdigest(),
                value_length=len(characteristic_value),
            ),
        ),
    )


def _snapshot_rule(*, raw_id: str, name: str, source_path: str) -> RosterSnapshotRule:
    description = "Synthetic local note."
    return RosterSnapshotRule(
        raw_id=raw_id,
        name=name,
        source_path=source_path,
        description_sha256=hashlib.sha256(description.encode("utf-8")).hexdigest(),
        description_length=len(description),
    )


def _canonical_army() -> CanonicalArmy:
    first_child = RosterSelection(
        raw_id="duplicate-selection",
        name="Nested Copy",
        selection_type="model",
        source_path="roster/force-1/duplicate-selection/duplicate-selection",
        costs=(RosterCost(raw_id="cost-child", name="pts", type_id="points", value="10"),),
        profiles=(
            _snapshot_profile(
                raw_id="profile-child",
                name="Nested Profile",
                source_path="roster/force-1/duplicate-selection/duplicate-selection/profile-child",
                characteristic_id="characteristic-child",
                characteristic_value="4",
            ),
        ),
        rules=(
            _snapshot_rule(
                raw_id="rule-child",
                name="Nested Rule",
                source_path="roster/force-1/duplicate-selection/duplicate-selection/rule-child",
            ),
        ),
    )
    return CanonicalArmy(
        roster_id="roster-1",
        name="Synthetic Army",
        game_system_id="game-system-1",
        game_system_name="Synthetic System",
        catalogue_id="catalogue-1",
        catalogue_name="Synthetic Catalogue",
        source_format="battlescribe_ros_v0",
        selections=(
            RosterSelection(
                raw_id="duplicate-selection",
                name="First Copy",
                selection_type="unit",
                source_path="roster/force-1/duplicate-selection",
                costs=(RosterCost(raw_id="cost-1", name="pts", type_id="points", value="125"),),
                profiles=(
                    _snapshot_profile(
                        raw_id="profile-1",
                        name="First Profile",
                        source_path="roster/force-1/duplicate-selection/profile-1",
                        characteristic_id="characteristic-1",
                        characteristic_value="6",
                    ),
                ),
                rules=(
                    _snapshot_rule(
                        raw_id="rule-1",
                        name="First Rule",
                        source_path="roster/force-1/duplicate-selection/rule-1",
                    ),
                ),
                children=(first_child,),
            ),
            RosterSelection(
                raw_id="duplicate-selection",
                name="Second Copy",
                selection_type="unit",
                source_path="roster/force-1/duplicate-selection",
            ),
        ),
    )


def test_canonical_army_with_source_refs_propagates_through_nested_evidence() -> None:
    army = canonical_army_with_source_refs(
        army=_canonical_army(),
        source_ref_ids=("local-file:synthetic",),
    )

    assert army.source_ref_ids == ("local-file:synthetic",)
    first = army.selections[0]
    nested = first.children[0]

    assert first.profiles[0].source_ref_ids == ("local-file:synthetic",)
    assert first.profiles[0].characteristics[0].source_ref_ids == ("local-file:synthetic",)
    assert first.rules[0].source_ref_ids == ("local-file:synthetic",)
    assert nested.profiles[0].source_ref_ids == ("local-file:synthetic",)
    assert nested.profiles[0].characteristics[0].source_ref_ids == ("local-file:synthetic",)
    assert nested.rules[0].source_ref_ids == ("local-file:synthetic",)


def test_canonical_roster_index_preserves_identity_counts_and_candidate_markers() -> None:
    army = canonical_army_with_source_refs(
        army=_canonical_army(),
        source_ref_ids=("local-file:synthetic",),
    )
    index = build_canonical_roster_index(
        army=army,
        source_ref_ids=("local-file:synthetic",),
    )

    assert index.roster_id == "roster-1"
    assert index.selection_count == 3
    assert index.top_level_selection_count == 2
    assert [(entry.selection_type, entry.count) for entry in index.selection_type_counts] == [
        ("model", 1),
        ("unit", 2),
    ]

    first, nested, second = index.entries
    assert first.selection_id == "duplicate-selection"
    assert first.parent_selection_key is None
    assert first.depth == 0
    assert first.sibling_ordinal == 0
    assert first.child_count == 1
    assert first.cost_count == 1
    assert first.profile_count == 1
    assert first.rule_count == 1
    assert nested.parent_selection_key == first.selection_key
    assert nested.depth == 1
    assert nested.sibling_ordinal == 0
    assert second.selection_id == "duplicate-selection"
    assert second.depth == 0
    assert second.sibling_ordinal == 1
    assert first.source_path == second.source_path
    assert first.selection_key != second.selection_key

    assert len(index.profile_candidates) == 3
    for candidate in index.profile_candidates:
        assert candidate.resolution_status == "unresolved"
        assert candidate.source_policy == "local_evidence"
        assert candidate.points_authority == "not_official_points"
        assert candidate.mechanics_authority == "not_profile_resolution"
        assert candidate.source_ref_ids == ("local-file:synthetic",)


def test_snapshot_profile_candidate_pack_hash_is_deterministic_and_source_sensitive() -> None:
    army = canonical_army_with_source_refs(
        army=_canonical_army(),
        source_ref_ids=("local-file:synthetic",),
    )

    first = build_roster_snapshot_profile_candidate_pack(
        army=army,
        selected_xml_sha256="xml-sha",
        source_ref_ids=("local-file:synthetic",),
    )
    second = build_roster_snapshot_profile_candidate_pack(
        army=army,
        selected_xml_sha256="xml-sha",
        source_ref_ids=("local-file:synthetic",),
    )
    changed_source = build_roster_snapshot_profile_candidate_pack(
        army=army,
        selected_xml_sha256="xml-sha",
        source_ref_ids=("local-file:synthetic", "manual-review:1"),
    )

    assert first.pack_hash == second.pack_hash
    assert first.pack_hash != changed_source.pack_hash
    assert first.readiness == "estimated"
    assert first.source_policy == "local_evidence"
    assert first.authority == "not_source_authority"
    assert first.source_ref_ids == ("local-file:synthetic",)
    assert [profile.raw_id for profile in first.profiles] == ["profile-1", "profile-child"]
    assert [rule.raw_id for rule in first.rules] == ["rule-1", "rule-child"]
    assert all(profile.source_ref_ids == ("local-file:synthetic",) for profile in first.profiles)
    assert all(rule.source_ref_ids == ("local-file:synthetic",) for rule in first.rules)


def test_snapshot_pack_hash_normalizes_source_refs_but_exposes_original_tuple() -> None:
    army = _canonical_army()

    first = build_roster_snapshot_profile_candidate_pack(
        army=army,
        selected_xml_sha256="xml-sha",
        source_ref_ids=("source:b", "source:a", "source:a"),
    )
    second = build_roster_snapshot_profile_candidate_pack(
        army=army,
        selected_xml_sha256="xml-sha",
        source_ref_ids=("source:a", "source:b"),
    )

    assert first.pack_hash == second.pack_hash
    assert first.source_ref_ids == ("source:b", "source:a", "source:a")
    assert first.profiles[0].source_ref_ids == ("source:b", "source:a", "source:a")
    assert second.source_ref_ids == ("source:a", "source:b")
    assert second.profiles[0].source_ref_ids == ("source:a", "source:b")


def test_snapshot_rules_expose_only_hash_and_length_not_description_text() -> None:
    army = canonical_army_with_source_refs(
        army=_canonical_army(),
        source_ref_ids=("local-file:synthetic",),
    )
    pack = build_roster_snapshot_profile_candidate_pack(
        army=army,
        selected_xml_sha256="xml-sha",
        source_ref_ids=("local-file:synthetic",),
    )

    assert pack.rules
    for rule in pack.rules:
        assert rule.description_sha256
        assert rule.description_length > 0
        assert not hasattr(rule, "description")
