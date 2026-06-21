from __future__ import annotations

import hashlib
import json
from dataclasses import replace

from warhammer_companion.domain.rosters import (
    CanonicalArmy,
    CanonicalRosterIndex,
    RosterProfileCandidate,
    RosterSelection,
    RosterSelectionIndexEntry,
    RosterSelectionTypeCount,
    RosterSnapshotProfile,
    RosterSnapshotProfileCandidatePack,
    RosterSnapshotRule,
)

ROSTER_IMPORT_TOOLKIT_SCHEMA_VERSION = "roster-import-toolkit/v0"


def canonical_army_with_source_refs(
    *,
    army: CanonicalArmy,
    source_ref_ids: tuple[str, ...],
) -> CanonicalArmy:
    return replace(
        army,
        selections=tuple(
            _selection_with_source_refs(selection, source_ref_ids) for selection in army.selections
        ),
        source_ref_ids=source_ref_ids,
    )


def build_canonical_roster_index(
    *,
    army: CanonicalArmy,
    source_ref_ids: tuple[str, ...],
) -> CanonicalRosterIndex:
    entries: list[RosterSelectionIndexEntry] = []
    candidates: list[RosterProfileCandidate] = []
    type_counts: dict[str, int] = {}

    def visit(
        selection: RosterSelection,
        *,
        parent_key: str | None,
        depth: int,
        sibling_ordinal: int,
        ordinal_path: tuple[int, ...],
    ) -> None:
        selection_key = _selection_key(
            roster_id=army.roster_id,
            source_path=selection.source_path,
            ordinal_path=ordinal_path,
        )
        type_counts[selection.selection_type] = type_counts.get(selection.selection_type, 0) + 1
        entries.append(
            RosterSelectionIndexEntry(
                selection_key=selection_key,
                parent_selection_key=parent_key,
                selection_id=selection.raw_id,
                selection_name=selection.name,
                selection_type=selection.selection_type,
                source_path=selection.source_path,
                depth=depth,
                sibling_ordinal=sibling_ordinal,
                child_count=len(selection.children),
                cost_count=len(selection.costs),
                profile_count=len(selection.profiles),
                rule_count=len(selection.rules),
            )
        )
        candidates.append(
            RosterProfileCandidate(
                selection_key=selection_key,
                selection_id=selection.raw_id,
                selection_name=selection.name,
                selection_type=selection.selection_type,
                source_path=selection.source_path,
                resolution_status="unresolved",
                profile_ids=tuple(profile.raw_id for profile in selection.profiles),
                rule_ids=tuple(rule.raw_id for rule in selection.rules),
                cost_ids=tuple(cost.raw_id for cost in selection.costs),
                source_ref_ids=source_ref_ids,
            )
        )
        for child_ordinal, child in enumerate(selection.children):
            visit(
                child,
                parent_key=selection_key,
                depth=depth + 1,
                sibling_ordinal=child_ordinal,
                ordinal_path=(*ordinal_path, child_ordinal),
            )

    for top_level_ordinal, selection in enumerate(army.selections):
        visit(
            selection,
            parent_key=None,
            depth=0,
            sibling_ordinal=top_level_ordinal,
            ordinal_path=(top_level_ordinal,),
        )

    selection_type_counts = tuple(
        RosterSelectionTypeCount(selection_type=selection_type, count=count)
        for selection_type, count in sorted(type_counts.items())
    )
    return CanonicalRosterIndex(
        roster_id=army.roster_id,
        roster_name=army.name,
        selection_count=len(entries),
        top_level_selection_count=len(army.selections),
        selection_type_counts=selection_type_counts,
        entries=tuple(entries),
        profile_candidates=tuple(candidates),
        source_ref_ids=source_ref_ids,
    )


def build_roster_snapshot_profile_candidate_pack(
    *,
    army: CanonicalArmy,
    selected_xml_sha256: str | None,
    source_ref_ids: tuple[str, ...],
) -> RosterSnapshotProfileCandidatePack:
    profiles: list[RosterSnapshotProfile] = []
    rules: list[RosterSnapshotRule] = []
    for selection in army.flattened_selections():
        profiles.extend(
            _profile_with_source_refs(profile, source_ref_ids) for profile in selection.profiles
        )
        rules.extend(replace(rule, source_ref_ids=source_ref_ids) for rule in selection.rules)
    profiles_tuple = tuple(profiles)
    rules_tuple = tuple(rules)
    pack_hash = _snapshot_pack_hash(
        army=army,
        selected_xml_sha256=selected_xml_sha256,
        profiles=profiles_tuple,
        rules=rules_tuple,
        source_ref_ids=source_ref_ids,
    )
    return RosterSnapshotProfileCandidatePack(
        roster_id=army.roster_id,
        source_format=army.source_format,
        selected_xml_sha256=selected_xml_sha256,
        pack_hash=pack_hash,
        profiles=profiles_tuple,
        rules=rules_tuple,
        source_ref_ids=source_ref_ids,
    )


def _selection_with_source_refs(
    selection: RosterSelection,
    source_ref_ids: tuple[str, ...],
) -> RosterSelection:
    return replace(
        selection,
        profiles=tuple(
            _profile_with_source_refs(profile, source_ref_ids) for profile in selection.profiles
        ),
        rules=tuple(replace(rule, source_ref_ids=source_ref_ids) for rule in selection.rules),
        children=tuple(
            _selection_with_source_refs(child, source_ref_ids) for child in selection.children
        ),
    )


def _profile_with_source_refs(
    profile: RosterSnapshotProfile,
    source_ref_ids: tuple[str, ...],
) -> RosterSnapshotProfile:
    return replace(
        profile,
        characteristics=tuple(
            replace(characteristic, source_ref_ids=source_ref_ids)
            for characteristic in profile.characteristics
        ),
        source_ref_ids=source_ref_ids,
    )


def _selection_key(
    *,
    roster_id: str,
    source_path: str,
    ordinal_path: tuple[int, ...],
) -> str:
    payload = {
        "ordinal_path": ordinal_path,
        "roster_id": roster_id,
        "schema_version": ROSTER_IMPORT_TOOLKIT_SCHEMA_VERSION,
        "source_path": source_path,
    }
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return f"selection:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _snapshot_pack_hash(
    *,
    army: CanonicalArmy,
    selected_xml_sha256: str | None,
    profiles: tuple[RosterSnapshotProfile, ...],
    rules: tuple[RosterSnapshotRule, ...],
    source_ref_ids: tuple[str, ...],
) -> str:
    payload = {
        "profiles": [
            {
                "characteristics": [
                    {
                        "name": characteristic.name,
                        "raw_id": characteristic.raw_id,
                        "source_path": characteristic.source_path,
                        "type_id": characteristic.type_id,
                        "value": characteristic.value,
                        "value_length": characteristic.value_length,
                        "value_sha256": characteristic.value_sha256,
                    }
                    for characteristic in profile.characteristics
                ],
                "name": profile.name,
                "raw_id": profile.raw_id,
                "source_path": profile.source_path,
                "type_id": profile.type_id,
                "type_name": profile.type_name,
            }
            for profile in profiles
        ],
        "roster_id": army.roster_id,
        "rules": [
            {
                "description_length": rule.description_length,
                "description_sha256": rule.description_sha256,
                "name": rule.name,
                "raw_id": rule.raw_id,
                "source_path": rule.source_path,
            }
            for rule in rules
        ],
        "schema_version": ROSTER_IMPORT_TOOLKIT_SCHEMA_VERSION,
        "selected_xml_sha256": selected_xml_sha256,
        "source_format": army.source_format,
        "source_ref_ids": sorted(set(source_ref_ids)),
    }
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
