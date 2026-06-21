from __future__ import annotations

import hashlib
import json
from dataclasses import replace

from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.overlays import ToolkitWarning
from warhammer_companion.domain.rosters import (
    ROSTER_IMPORT_PARSER_VERSION,
    ROSTER_IMPORT_SOURCE_SCHEMA_VERSION,
    CanonicalArmy,
    CanonicalRosterIndex,
    RosterArchiveMember,
    RosterImportBlockReason,
    RosterImportPayload,
    RosterImportSource,
    RosterProfileCandidate,
    RosterQuarantineStatus,
    RosterSelection,
    RosterSelectionIndexEntry,
    RosterSelectionTypeCount,
    RosterSnapshotProfile,
    RosterSnapshotProfileCandidatePack,
    RosterSnapshotRule,
    RosterSourceKind,
)
from warhammer_companion.ingestion.roster_archives import (
    RosterArchiveLimits,
    inspect_roster_archive,
)
from warhammer_companion.ingestion.roster_xml import RosterXmlLimits, parse_roster_xml

ROSTER_IMPORT_TOOLKIT_SCHEMA_VERSION = "roster-import-toolkit/v0"


def build_roster_import_result_from_bytes(
    *,
    filename: str,
    data: bytes,
    source_kind: RosterSourceKind,
    source_ref_ids: tuple[str, ...] = (),
    max_xml_bytes: int = 1024 * 512,
    max_decompression_ratio: float = 100.0,
) -> ToolkitResult[RosterImportPayload]:
    source_sha = hashlib.sha256(data).hexdigest()
    input_hash = _input_hash(
        filename=filename,
        source_kind=source_kind,
        data_sha256=source_sha,
        source_ref_ids=source_ref_ids,
    )
    suffix = input_hash.removeprefix("sha256:")[:12]

    if source_kind == "ros_xml":
        selected_xml: bytes | None = data
        selected_xml_member_path: str | None = None
        selected_xml_sha: str | None = source_sha
        archive_members: tuple[RosterArchiveMember, ...] = ()
        archive_block_reasons: tuple[RosterImportBlockReason, ...] = ()
    elif source_kind == "rosz_archive":
        archive = inspect_roster_archive(
            data,
            limits=RosterArchiveLimits(
                max_xml_bytes=max_xml_bytes,
                max_decompression_ratio=max_decompression_ratio,
            ),
        )
        selected_xml = archive.xml_bytes
        selected_xml_member_path = archive.selected_member_path
        selected_xml_sha = archive.selected_xml_sha256
        archive_members = archive.members
        archive_block_reasons = archive.block_reasons
    else:
        archive_block_reasons = (
            RosterImportBlockReason(
                reason_id="unsupported-roster-source-kind",
                detail=f"Unsupported roster source kind: {source_kind}",
            ),
        )
        selected_xml = None
        selected_xml_member_path = None
        selected_xml_sha = None
        archive_members = ()

    if archive_block_reasons or selected_xml is None:
        source = _source_record(
            filename=filename,
            source_kind=source_kind,
            data=data,
            source_sha=source_sha,
            selected_xml_member_path=selected_xml_member_path,
            selected_xml_sha=selected_xml_sha,
            archive_members=archive_members,
            quarantine_status="blocked",
            block_reasons=archive_block_reasons,
        )
        return _blocked_result(
            result_id=f"{filename}:roster-import:{suffix}",
            input_hash=input_hash,
            source=source,
            block_reasons=archive_block_reasons,
            source_ref_ids=source_ref_ids,
        )

    parsed = parse_roster_xml(selected_xml, limits=RosterXmlLimits(max_xml_bytes=max_xml_bytes))
    if parsed.block_reasons:
        source = _source_record(
            filename=filename,
            source_kind=source_kind,
            data=data,
            source_sha=source_sha,
            selected_xml_member_path=selected_xml_member_path,
            selected_xml_sha=selected_xml_sha,
            archive_members=archive_members,
            quarantine_status="blocked",
            block_reasons=parsed.block_reasons,
        )
        return _blocked_result(
            result_id=f"{filename}:roster-import:{suffix}",
            input_hash=input_hash,
            source=source,
            block_reasons=parsed.block_reasons,
            source_ref_ids=source_ref_ids,
        )

    source = _source_record(
        filename=filename,
        source_kind=source_kind,
        data=data,
        source_sha=source_sha,
        selected_xml_member_path=selected_xml_member_path,
        selected_xml_sha=selected_xml_sha,
        archive_members=archive_members,
        quarantine_status="accepted",
        block_reasons=(),
    )
    army = (
        _army_with_source_refs(army=parsed.army, source_ref_ids=source_ref_ids)
        if parsed.army is not None
        else None
    )
    roster_index = (
        _canonical_roster_index(army=army, source_ref_ids=source_ref_ids)
        if army is not None
        else None
    )
    snapshot_profile_pack = (
        _snapshot_profile_candidate_pack(
            army=army,
            selected_xml_sha256=selected_xml_sha,
            source_ref_ids=source_ref_ids,
        )
        if army is not None
        else None
    )
    return ToolkitResult(
        result_id=f"{filename}:roster-import:{suffix}",
        tool_id="roster_import",
        input_hash=input_hash,
        readiness="estimated",
        payload=RosterImportPayload(
            source=source,
            army=army,
            roster_index=roster_index,
            snapshot_profile_pack=snapshot_profile_pack,
        ),
        warnings=(
            ToolkitWarning(
                warning_id="roster-snapshot-local-evidence",
                detail="Imported roster data is local evidence, not rules or points authority.",
                source_ref_ids=source_ref_ids,
            ),
            ToolkitWarning(
                warning_id="roster-profile-candidates-unresolved",
                detail=(
                    "Roster snapshot profiles, rules, characteristics, and costs are unresolved "
                    "local evidence, not source authority."
                ),
                source_ref_ids=source_ref_ids,
            ),
        ),
        source_ref_ids=source_ref_ids,
    )


def _source_record(
    *,
    filename: str,
    source_kind: RosterSourceKind,
    data: bytes,
    source_sha: str,
    selected_xml_member_path: str | None,
    selected_xml_sha: str | None,
    archive_members: tuple[RosterArchiveMember, ...],
    quarantine_status: RosterQuarantineStatus,
    block_reasons: tuple[RosterImportBlockReason, ...],
) -> RosterImportSource:
    return RosterImportSource(
        filename=filename,
        source_kind=source_kind,
        byte_size=len(data),
        sha256=source_sha,
        parser_version=ROSTER_IMPORT_PARSER_VERSION,
        schema_version=ROSTER_IMPORT_SOURCE_SCHEMA_VERSION,
        quarantine_status=quarantine_status,
        selected_xml_member_path=selected_xml_member_path,
        selected_xml_sha256=selected_xml_sha,
        archive_members=archive_members,
        block_reasons=block_reasons,
    )


def _blocked_result(
    *,
    result_id: str,
    input_hash: str,
    source: RosterImportSource,
    block_reasons: tuple[RosterImportBlockReason, ...],
    source_ref_ids: tuple[str, ...],
) -> ToolkitResult[RosterImportPayload]:
    return ToolkitResult(
        result_id=result_id,
        tool_id="roster_import",
        input_hash=input_hash,
        readiness="blocked",
        payload=RosterImportPayload(source=source, army=None),
        warnings=(
            ToolkitWarning(
                warning_id="roster-import-blocked",
                detail="Roster import was blocked by the quarantine gate.",
                source_ref_ids=source_ref_ids,
            ),
        ),
        block_reasons=_toolkit_block_reasons(block_reasons),
        source_ref_ids=source_ref_ids,
    )


def _toolkit_block_reasons(
    block_reasons: tuple[RosterImportBlockReason, ...],
) -> tuple[BlockReason, ...]:
    return tuple(
        BlockReason(
            reason_id=reason.reason_id,
            detail=reason.detail,
            remediation=reason.remediation,
            source_ref_ids=reason.source_ref_ids,
        )
        for reason in block_reasons
    )


def _input_hash(
    *,
    filename: str,
    source_kind: RosterSourceKind,
    data_sha256: str,
    source_ref_ids: tuple[str, ...],
) -> str:
    payload = {
        "data_sha256": data_sha256,
        "filename": filename,
        "schema_version": ROSTER_IMPORT_TOOLKIT_SCHEMA_VERSION,
        "source_kind": source_kind,
        "source_ref_ids": sorted(set(source_ref_ids)),
        "tool_id": "roster_import",
    }
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _canonical_roster_index(
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


def _army_with_source_refs(
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


def _snapshot_profile_candidate_pack(
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
