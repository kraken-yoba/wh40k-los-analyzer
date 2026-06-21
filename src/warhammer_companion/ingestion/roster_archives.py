from __future__ import annotations

import hashlib
import io
import posixpath
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath

from warhammer_companion.domain.rosters import RosterArchiveMember, RosterImportBlockReason

NESTED_ARCHIVE_EXTENSIONS = frozenset({".zip", ".rosz", ".catz", ".gstz", ".bsr", ".bsi"})
ALLOWED_ROSZ_MEMBER_EXTENSIONS = frozenset({".ros"})
SUPPORTED_ZIP_COMPRESSION = frozenset({zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED})


@dataclass(frozen=True, slots=True)
class RosterArchiveLimits:
    max_members: int = 3
    max_archive_bytes: int = 1024 * 1024
    max_xml_bytes: int = 1024 * 512
    max_decompression_ratio: float = 100.0


DEFAULT_ARCHIVE_LIMITS = RosterArchiveLimits()


@dataclass(frozen=True, slots=True)
class RosterArchiveInspection:
    xml_bytes: bytes | None
    selected_member_path: str | None
    selected_xml_sha256: str | None
    members: tuple[RosterArchiveMember, ...]
    block_reasons: tuple[RosterImportBlockReason, ...] = ()

    @property
    def is_blocked(self) -> bool:
        return bool(self.block_reasons)


@dataclass(frozen=True, slots=True)
class _BoundedMemberRead:
    xml_bytes: bytes | None
    compressed_size: int | None = None
    uncompressed_size: int | None = None
    block_reason: RosterImportBlockReason | None = None


@dataclass(frozen=True, slots=True)
class _LocalMemberHeader:
    filename: str
    flag_bits: int
    compress_type: int
    crc: int
    compressed_size: int
    uncompressed_size: int
    extra_length: int
    data_start: int


def inspect_roster_archive(
    data: bytes,
    *,
    limits: RosterArchiveLimits = DEFAULT_ARCHIVE_LIMITS,
) -> RosterArchiveInspection:
    block_reasons: list[RosterImportBlockReason] = []
    members: list[RosterArchiveMember] = []

    if len(data) > limits.max_archive_bytes:
        block_reasons.append(
            RosterImportBlockReason(
                reason_id="archive-too-large",
                detail="Roster archive exceeds the maximum admitted byte size.",
            )
        )
        return RosterArchiveInspection(None, None, None, (), tuple(block_reasons))

    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return RosterArchiveInspection(
            None,
            None,
            None,
            (),
            (
                RosterImportBlockReason(
                    reason_id="malformed-roster-archive",
                    detail="Roster archive is not a valid zip file.",
                ),
            ),
        )

    with archive:
        if archive.comment:
            block_reasons.append(
                RosterImportBlockReason(
                    reason_id="unexpected-archive-member",
                    detail="Roster archive comments are not admitted in Phase 4A.",
                )
            )
        all_infos = tuple(archive.infolist())
        layout_reason = _archive_layout_block_reason(data, all_infos)
        if layout_reason is not None:
            block_reasons.append(layout_reason)
        if len(all_infos) > limits.max_members:
            block_reasons.append(
                RosterImportBlockReason(
                    reason_id="archive-member-count",
                    detail="Roster archive contains too many entries.",
                )
            )
        for info in all_infos:
            normalized_path = _normalize_member_path(info.filename)
            if normalized_path is None:
                block_reasons.append(
                    RosterImportBlockReason(
                        reason_id="unsafe-archive-path",
                        detail=f"Roster archive member has an unsafe path: {info.filename}",
                    )
                )
                continue
            if info.extra:
                block_reasons.append(
                    RosterImportBlockReason(
                        reason_id="unexpected-archive-member",
                        detail=(
                            f"Roster archive member extra fields are not admitted: {info.filename}"
                        ),
                    )
                )
                continue
            if info.comment:
                block_reasons.append(
                    RosterImportBlockReason(
                        reason_id="unexpected-archive-member",
                        detail=(
                            f"Roster archive member comments are not admitted: {info.filename}"
                        ),
                    )
                )
                continue
            if info.is_dir():
                directory_reason = _directory_entry_block_reason(
                    archive_data=data,
                    all_infos=all_infos,
                    info=info,
                    normalized_path=normalized_path,
                )
                if directory_reason is not None:
                    block_reasons.append(directory_reason)
        infos = tuple(info for info in all_infos if not info.is_dir())
        for info in infos:
            normalized_path = _normalize_member_path(info.filename)
            compressed_size = int(info.compress_size)
            uncompressed_size = int(info.file_size)
            ratio = _decompression_ratio(
                compressed_size=compressed_size,
                uncompressed_size=uncompressed_size,
            )
            members.append(
                RosterArchiveMember(
                    path=info.filename,
                    compressed_size=compressed_size,
                    uncompressed_size=uncompressed_size,
                    decompression_ratio=ratio,
                )
            )
            if normalized_path is None:
                continue
            suffix = PurePosixPath(normalized_path).suffix.lower()
            if suffix in NESTED_ARCHIVE_EXTENSIONS:
                block_reasons.append(
                    RosterImportBlockReason(
                        reason_id="nested-archive-member",
                        detail=f"Nested archive members are not allowed: {info.filename}",
                    )
                )
            elif suffix not in ALLOWED_ROSZ_MEMBER_EXTENSIONS:
                block_reasons.append(
                    RosterImportBlockReason(
                        reason_id="unexpected-archive-member",
                        detail=f"Unexpected roster archive member type: {info.filename}",
                    )
                )
            if info.flag_bits & 0x1:
                block_reasons.append(
                    RosterImportBlockReason(
                        reason_id="encrypted-archive-member",
                        detail=f"Encrypted roster archive members are not allowed: {info.filename}",
                    )
                )
            if info.compress_type not in SUPPORTED_ZIP_COMPRESSION:
                block_reasons.append(
                    RosterImportBlockReason(
                        reason_id="unsupported-archive-compression",
                        detail=(
                            f"Roster archive member uses unsupported compression: {info.filename}"
                        ),
                    )
                )
            if uncompressed_size > limits.max_xml_bytes:
                block_reasons.append(
                    RosterImportBlockReason(
                        reason_id="archive-member-too-large",
                        detail=f"Roster archive member is too large: {info.filename}",
                    )
                )
            if ratio > limits.max_decompression_ratio:
                block_reasons.append(
                    RosterImportBlockReason(
                        reason_id="archive-decompression-ratio",
                        detail=(
                            "Roster archive member has excessive compression ratio: "
                            f"{info.filename}"
                        ),
                    )
                )

        ros_members = tuple(
            info
            for info in infos
            if _normalize_member_path(info.filename) is not None
            and PurePosixPath(_normalize_member_path(info.filename) or "").suffix.lower() == ".ros"
        )
        if not block_reasons and len(ros_members) != 1:
            block_reasons.append(
                RosterImportBlockReason(
                    reason_id="archive-selected-roster-count",
                    detail="Roster archive must contain exactly one .ros member for Phase 4A.",
                )
            )
        if block_reasons:
            return RosterArchiveInspection(None, None, None, tuple(members), tuple(block_reasons))

        selected_info = ros_members[0]
        read_result = _read_member_bytes_bounded(
            archive_data=data,
            all_infos=all_infos,
            selected_info=selected_info,
            limits=limits,
        )
        if read_result.block_reason is not None or read_result.xml_bytes is None:
            return RosterArchiveInspection(
                None,
                selected_info.filename,
                None,
                tuple(members),
                (read_result.block_reason or _member_read_failed(selected_info.filename),),
            )
        xml_bytes = read_result.xml_bytes
        members = _record_actual_selected_member_sizes(
            members=members,
            selected_path=selected_info.filename,
            compressed_size=read_result.compressed_size,
            uncompressed_size=read_result.uncompressed_size,
        )
        return RosterArchiveInspection(
            xml_bytes=xml_bytes,
            selected_member_path=selected_info.filename,
            selected_xml_sha256=hashlib.sha256(xml_bytes).hexdigest(),
            members=tuple(members),
        )


def _normalize_member_path(path: str) -> str | None:
    normalized = path.replace("\\", "/")
    raw_parts = tuple(part for part in normalized.split("/") if part)
    if any(part == ".." for part in raw_parts):
        return None
    if normalized.startswith(("/", "\\")):
        return None
    if ":" in normalized:
        return None
    if PureWindowsPath(normalized).is_absolute() or PurePosixPath(normalized).is_absolute():
        return None
    normalized = posixpath.normpath(normalized)
    if normalized == ".":
        return None
    if normalized.startswith("../") or normalized == ".." or "/../" in normalized:
        return None
    return normalized


def _directory_entry_block_reason(
    *,
    archive_data: bytes,
    all_infos: tuple[zipfile.ZipInfo, ...],
    info: zipfile.ZipInfo,
    normalized_path: str,
) -> RosterImportBlockReason | None:
    try:
        local_header = _local_member_header(archive_data, info)
        header_reason = _validate_local_member_header(
            central_info=info,
            local_header=local_header,
        )
        if header_reason is not None:
            return header_reason
        data_end = _member_data_end(archive_data, all_infos, info)
    except (IndexError, ValueError) as exc:
        return _member_read_failed(info.filename, detail=str(exc))
    if local_header.data_start != data_end:
        return _member_read_failed(
            info.filename,
            detail="Roster archive directory local entry has a non-empty payload span.",
        )
    suffix = PurePosixPath(normalized_path).suffix.lower()
    if suffix in NESTED_ARCHIVE_EXTENSIONS:
        return RosterImportBlockReason(
            reason_id="nested-archive-member",
            detail=f"Nested archive directory members are not allowed: {info.filename}",
        )
    if info.flag_bits & 0x1:
        return RosterImportBlockReason(
            reason_id="encrypted-archive-member",
            detail=f"Encrypted roster archive directories are not allowed: {info.filename}",
        )
    if info.flag_bits & 0x8:
        return _member_read_failed(
            info.filename,
            detail="Roster archive directory data descriptors are not supported in Phase 4A.",
        )
    if info.compress_type not in SUPPORTED_ZIP_COMPRESSION:
        return RosterImportBlockReason(
            reason_id="unsupported-archive-compression",
            detail=f"Roster archive directory uses unsupported compression: {info.filename}",
        )
    if info.compress_size != 0 or info.file_size != 0:
        return RosterImportBlockReason(
            reason_id="unexpected-archive-member",
            detail=f"Roster archive directory entries must not carry payloads: {info.filename}",
        )
    return None


def _read_member_bytes_bounded(
    *,
    archive_data: bytes,
    all_infos: tuple[zipfile.ZipInfo, ...],
    selected_info: zipfile.ZipInfo,
    limits: RosterArchiveLimits,
) -> _BoundedMemberRead:
    try:
        local_header = _local_member_header(archive_data, selected_info)
        header_block_reason = _validate_local_member_header(
            central_info=selected_info,
            local_header=local_header,
        )
        if header_block_reason is not None:
            return _BoundedMemberRead(None, block_reason=header_block_reason)
        data_start = local_header.data_start
        data_end = _member_data_end(archive_data, all_infos, selected_info)
    except (IndexError, ValueError) as exc:
        return _BoundedMemberRead(
            None,
            block_reason=_member_read_failed(selected_info.filename, detail=str(exc)),
        )
    if data_start < 0 or data_end < data_start or data_end > len(archive_data):
        return _BoundedMemberRead(
            None,
            block_reason=_member_read_failed(
                selected_info.filename,
                detail="Roster archive member has invalid local data boundaries.",
            ),
        )
    compressed_payload = memoryview(archive_data)[data_start:data_end]
    if local_header.compress_type == zipfile.ZIP_STORED:
        return _read_stored_member_bounded(
            compressed_payload=compressed_payload,
            selected_info=selected_info,
            limits=limits,
        )
    if local_header.compress_type == zipfile.ZIP_DEFLATED:
        return _read_deflated_member_bounded(
            compressed_payload=compressed_payload,
            selected_info=selected_info,
            limits=limits,
        )
    return _BoundedMemberRead(
        None,
        block_reason=RosterImportBlockReason(
            reason_id="unsupported-archive-compression",
            detail=f"Roster archive member uses unsupported compression: {selected_info.filename}",
        ),
    )


def _local_member_header(
    archive_data: bytes,
    selected_info: zipfile.ZipInfo,
) -> _LocalMemberHeader:
    header_offset = int(selected_info.header_offset)
    if header_offset < 0 or header_offset + 30 > len(archive_data):
        raise ValueError("Roster archive member local header is outside the archive.")
    if archive_data[header_offset : header_offset + 4] != b"PK\x03\x04":
        raise ValueError("Roster archive member local header is missing.")
    filename_length = int.from_bytes(
        archive_data[header_offset + 26 : header_offset + 28], "little"
    )
    extra_length = int.from_bytes(archive_data[header_offset + 28 : header_offset + 30], "little")
    filename_start = header_offset + 30
    filename_end = filename_start + filename_length
    data_start = header_offset + 30 + filename_length + extra_length
    if data_start > len(archive_data):
        raise ValueError("Roster archive member local header lengths exceed archive size.")
    try:
        filename = archive_data[filename_start:filename_end].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Roster archive member local filename is not UTF-8.") from exc
    return _LocalMemberHeader(
        filename=filename,
        flag_bits=int.from_bytes(archive_data[header_offset + 6 : header_offset + 8], "little"),
        compress_type=int.from_bytes(
            archive_data[header_offset + 8 : header_offset + 10], "little"
        ),
        crc=int.from_bytes(archive_data[header_offset + 14 : header_offset + 18], "little"),
        compressed_size=int.from_bytes(
            archive_data[header_offset + 18 : header_offset + 22], "little"
        ),
        uncompressed_size=int.from_bytes(
            archive_data[header_offset + 22 : header_offset + 26],
            "little",
        ),
        extra_length=extra_length,
        data_start=data_start,
    )


def _validate_local_member_header(
    *,
    central_info: zipfile.ZipInfo,
    local_header: _LocalMemberHeader,
) -> RosterImportBlockReason | None:
    normalized_central = _normalize_member_path(central_info.filename)
    normalized_local = _normalize_member_path(local_header.filename)
    if normalized_local is None:
        return RosterImportBlockReason(
            reason_id="unsafe-archive-path",
            detail=f"Roster archive member has an unsafe local path: {local_header.filename}",
        )
    if normalized_central != normalized_local:
        return RosterImportBlockReason(
            reason_id="unsafe-archive-path",
            detail=(
                "Roster archive member local path does not match central directory path: "
                f"{local_header.filename}"
            ),
        )
    if (central_info.flag_bits | local_header.flag_bits) & 0x1:
        return RosterImportBlockReason(
            reason_id="encrypted-archive-member",
            detail=f"Encrypted roster archive members are not allowed: {central_info.filename}",
        )
    if central_info.compress_type != local_header.compress_type:
        return RosterImportBlockReason(
            reason_id="unsupported-archive-compression",
            detail=(
                "Roster archive member local compression does not match central directory: "
                f"{central_info.filename}"
            ),
        )
    if local_header.compress_type not in SUPPORTED_ZIP_COMPRESSION:
        return RosterImportBlockReason(
            reason_id="unsupported-archive-compression",
            detail=f"Roster archive member uses unsupported compression: {central_info.filename}",
        )
    if local_header.extra_length != 0:
        return RosterImportBlockReason(
            reason_id="unexpected-archive-member",
            detail=f"Roster archive local extra fields are not admitted: {central_info.filename}",
        )
    central_uses_data_descriptor = bool(central_info.flag_bits & 0x8)
    local_uses_data_descriptor = bool(local_header.flag_bits & 0x8)
    if central_uses_data_descriptor != local_uses_data_descriptor:
        return _member_read_failed(
            central_info.filename,
            detail="Roster archive data-descriptor flag differs between local and central headers.",
        )
    if central_uses_data_descriptor:
        return _member_read_failed(
            central_info.filename,
            detail="Roster archive data descriptors are not supported in Phase 4A.",
        )
    if (
        central_info.CRC != local_header.crc
        or central_info.compress_size != local_header.compressed_size
        or central_info.file_size != local_header.uncompressed_size
    ):
        return _member_read_failed(
            central_info.filename,
            detail="Roster archive local header does not match central directory metadata.",
        )
    return None


def _member_data_end(
    archive_data: bytes,
    all_infos: tuple[zipfile.ZipInfo, ...],
    selected_info: zipfile.ZipInfo,
) -> int:
    selected_offset = int(selected_info.header_offset)
    next_offsets = sorted(
        int(info.header_offset) for info in all_infos if int(info.header_offset) > selected_offset
    )
    if next_offsets:
        return next_offsets[0]
    return _central_directory_start(archive_data)


def _archive_layout_block_reason(
    archive_data: bytes,
    all_infos: tuple[zipfile.ZipInfo, ...],
) -> RosterImportBlockReason | None:
    try:
        eocd_offset, comment_length = _end_of_central_directory(archive_data)
        if eocd_offset + 22 + comment_length != len(archive_data):
            return _member_read_failed(
                "<archive>",
                detail="Roster archive has trailing bytes after the end-of-central-directory.",
            )
        if not all_infos:
            return None
        central_directory_start = _central_directory_start(archive_data)
        sorted_infos = tuple(sorted(all_infos, key=lambda info: int(info.header_offset)))
        expected_offset = 0
        for info in sorted_infos:
            header_offset = int(info.header_offset)
            if header_offset != expected_offset:
                return _member_read_failed(
                    info.filename,
                    detail="Roster archive local entries do not cover the archive from byte zero.",
                )
            _local_member_header(archive_data, info)
            expected_offset = _member_data_end(archive_data, sorted_infos, info)
        if expected_offset != central_directory_start:
            return _member_read_failed(
                "<archive>",
                detail="Roster archive has unreferenced bytes before the central directory.",
            )
    except (IndexError, ValueError) as exc:
        return _member_read_failed("<archive>", detail=str(exc))
    return None


def _central_directory_start(archive_data: bytes) -> int:
    eocd_offset, _comment_length = _end_of_central_directory(archive_data)
    central_directory_offset = int.from_bytes(
        archive_data[eocd_offset + 16 : eocd_offset + 20],
        "little",
    )
    if central_directory_offset == 0xFFFFFFFF:
        raise ValueError("ZIP64 roster archives are not supported in Phase 4A.")
    if central_directory_offset < 0 or central_directory_offset > len(archive_data):
        raise ValueError("Roster archive central directory offset is outside the archive.")
    return central_directory_offset


def _end_of_central_directory(archive_data: bytes) -> tuple[int, int]:
    search_start = max(0, len(archive_data) - (65535 + 22))
    eocd_offset = archive_data.rfind(b"PK\x05\x06", search_start)
    if eocd_offset < 0 or eocd_offset + 22 > len(archive_data):
        raise ValueError("Roster archive end-of-central-directory record is missing.")
    comment_length = int.from_bytes(archive_data[eocd_offset + 20 : eocd_offset + 22], "little")
    return eocd_offset, comment_length


def _read_stored_member_bounded(
    *,
    compressed_payload: memoryview,
    selected_info: zipfile.ZipInfo,
    limits: RosterArchiveLimits,
) -> _BoundedMemberRead:
    compressed_size = len(compressed_payload)
    if compressed_size != selected_info.compress_size:
        return _BoundedMemberRead(
            None,
            compressed_size=compressed_size,
            uncompressed_size=compressed_size,
            block_reason=_member_read_failed(
                selected_info.filename,
                detail="Roster archive stored member size does not match its local entry span.",
            ),
        )
    if compressed_size > limits.max_xml_bytes:
        return _BoundedMemberRead(
            None,
            compressed_size=compressed_size,
            uncompressed_size=compressed_size,
            block_reason=_member_too_large(selected_info.filename),
        )
    xml_bytes = bytes(compressed_payload)
    crc_reason = _crc_block_reason(selected_info=selected_info, xml_bytes=xml_bytes)
    if crc_reason is not None:
        return _BoundedMemberRead(
            None,
            compressed_size=compressed_size,
            uncompressed_size=len(xml_bytes),
            block_reason=crc_reason,
        )
    return _BoundedMemberRead(
        xml_bytes,
        compressed_size=compressed_size,
        uncompressed_size=len(xml_bytes),
    )


def _read_deflated_member_bounded(
    *,
    compressed_payload: memoryview,
    selected_info: zipfile.ZipInfo,
    limits: RosterArchiveLimits,
) -> _BoundedMemberRead:
    decompressor = zlib.decompressobj(-15)
    output = bytearray()
    compressed_size = 0
    offset = 0
    pending = b""
    try:
        while offset < len(compressed_payload) or pending:
            if pending:
                chunk = pending
                pending = b""
            else:
                view = compressed_payload[offset : offset + 8192]
                chunk = bytes(view)
                offset += len(view)
                compressed_size += len(chunk)
            remaining = limits.max_xml_bytes + 1 - len(output)
            produced = decompressor.decompress(chunk, max(0, remaining))
            output.extend(produced)
            if len(output) > limits.max_xml_bytes:
                return _BoundedMemberRead(
                    None,
                    compressed_size=compressed_size,
                    uncompressed_size=len(output),
                    block_reason=_member_too_large(selected_info.filename),
                )
            if decompressor.unconsumed_tail:
                pending = decompressor.unconsumed_tail
            if decompressor.eof:
                break
        if not decompressor.eof:
            return _BoundedMemberRead(
                None,
                compressed_size=compressed_size,
                uncompressed_size=len(output),
                block_reason=_member_read_failed(
                    selected_info.filename,
                    detail="Roster archive member deflate stream is incomplete.",
                ),
            )
        compressed_size = len(compressed_payload) - len(decompressor.unused_data)
        if compressed_size != len(compressed_payload):
            return _BoundedMemberRead(
                None,
                compressed_size=compressed_size,
                uncompressed_size=len(output),
                block_reason=_member_read_failed(
                    selected_info.filename,
                    detail="Roster archive member has trailing bytes after its deflate stream.",
                ),
            )
        if compressed_size != selected_info.compress_size:
            return _BoundedMemberRead(
                None,
                compressed_size=compressed_size,
                uncompressed_size=len(output),
                block_reason=_member_read_failed(
                    selected_info.filename,
                    detail=(
                        "Roster archive deflated member size does not match its local entry span."
                    ),
                ),
            )
        if len(output) != selected_info.file_size:
            return _BoundedMemberRead(
                None,
                compressed_size=compressed_size,
                uncompressed_size=len(output),
                block_reason=_member_read_failed(
                    selected_info.filename,
                    detail="Roster archive inflated member size does not match metadata.",
                ),
            )
        ratio = _decompression_ratio(
            compressed_size=compressed_size,
            uncompressed_size=len(output),
        )
        if ratio > limits.max_decompression_ratio:
            return _BoundedMemberRead(
                None,
                compressed_size=compressed_size,
                uncompressed_size=len(output),
                block_reason=RosterImportBlockReason(
                    reason_id="archive-decompression-ratio",
                    detail=(
                        "Roster archive member has excessive compression ratio: "
                        f"{selected_info.filename}"
                    ),
                ),
            )
        xml_bytes = bytes(output)
        crc_reason = _crc_block_reason(selected_info=selected_info, xml_bytes=xml_bytes)
        if crc_reason is not None:
            return _BoundedMemberRead(
                None,
                compressed_size=compressed_size,
                uncompressed_size=len(xml_bytes),
                block_reason=crc_reason,
            )
    except (OverflowError, zlib.error) as exc:
        return _BoundedMemberRead(
            None,
            compressed_size=compressed_size,
            uncompressed_size=len(output),
            block_reason=_member_read_failed(selected_info.filename, detail=str(exc)),
        )
    return _BoundedMemberRead(
        xml_bytes,
        compressed_size=compressed_size,
        uncompressed_size=len(xml_bytes),
    )


def _crc_block_reason(
    *,
    selected_info: zipfile.ZipInfo,
    xml_bytes: bytes,
) -> RosterImportBlockReason | None:
    if selected_info.CRC == (zlib.crc32(xml_bytes) & 0xFFFFFFFF):
        return None
    return _member_read_failed(
        selected_info.filename,
        detail="Roster archive member CRC does not match its actual inflated content.",
    )


def _member_too_large(path: str) -> RosterImportBlockReason:
    return RosterImportBlockReason(
        reason_id="archive-member-too-large",
        detail=f"Roster archive member is too large: {path}",
    )


def _member_read_failed(path: str, *, detail: str | None = None) -> RosterImportBlockReason:
    message = f"Roster archive member could not be read safely: {path}"
    if detail:
        message = f"{message} ({detail})"
    return RosterImportBlockReason(
        reason_id="archive-member-read-failed",
        detail=message,
    )


def _record_actual_selected_member_sizes(
    *,
    members: list[RosterArchiveMember],
    selected_path: str,
    compressed_size: int | None,
    uncompressed_size: int | None,
) -> list[RosterArchiveMember]:
    if compressed_size is None or uncompressed_size is None:
        return members
    return [
        RosterArchiveMember(
            path=member.path,
            compressed_size=compressed_size
            if member.path == selected_path
            else member.compressed_size,
            uncompressed_size=(
                uncompressed_size if member.path == selected_path else member.uncompressed_size
            ),
            decompression_ratio=(
                _decompression_ratio(
                    compressed_size=compressed_size,
                    uncompressed_size=uncompressed_size,
                )
                if member.path == selected_path
                else member.decompression_ratio
            ),
        )
        for member in members
    ]


def _decompression_ratio(*, compressed_size: int, uncompressed_size: int) -> float:
    if compressed_size <= 0:
        return float(uncompressed_size) if uncompressed_size > 0 else 1.0
    ratio = uncompressed_size / compressed_size
    return max(1.0, ratio)
