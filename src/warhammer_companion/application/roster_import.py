from __future__ import annotations

import hashlib
import json
from dataclasses import replace

from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.overlays import ToolkitWarning
from warhammer_companion.domain.rosters import (
    ROSTER_IMPORT_PARSER_VERSION,
    ROSTER_IMPORT_SOURCE_SCHEMA_VERSION,
    RosterArchiveMember,
    RosterImportBlockReason,
    RosterImportPayload,
    RosterImportSource,
    RosterQuarantineStatus,
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
    army = replace(parsed.army, source_ref_ids=source_ref_ids) if parsed.army is not None else None
    return ToolkitResult(
        result_id=f"{filename}:roster-import:{suffix}",
        tool_id="roster_import",
        input_hash=input_hash,
        readiness="estimated",
        payload=RosterImportPayload(source=source, army=army),
        warnings=(
            ToolkitWarning(
                warning_id="roster-snapshot-local-evidence",
                detail="Imported roster data is local evidence, not rules or points authority.",
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
