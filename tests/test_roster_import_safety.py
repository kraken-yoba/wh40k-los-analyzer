from __future__ import annotations

import binascii
import io
import zipfile

from warhammer_companion.application.roster_import import build_roster_import_result_from_bytes


def _safe_roster_xml(roster_name: str = "Synthetic Army") -> bytes:
    return (
        f"""<?xml version="1.0" encoding="UTF-8"?>
<roster id="roster-1" name="{roster_name}" gameSystemId="game-system-1"
  gameSystemName="Synthetic System">
  <forces>
    <force id="force-1" name="Main Force" catalogueId="catalogue-1"
      catalogueName="Synthetic Catalogue">
      <selections>
        <selection id="unit-1" name="Example Unit" type="unit">
          <costs>
            <cost id="cost-1" name="pts" typeId="points" value="125"/>
          </costs>
          <selections>
            <selection id="model-1" name="Example Model" type="model">
              <costs>
                <cost id="cost-2" name="pts" typeId="points" value="25"/>
              </costs>
            </selection>
          </selections>
        </selection>
        <selection id="upgrade-1" name="Example Upgrade" type="upgrade"/>
      </selections>
    </force>
  </forces>
</roster>
"""
    ).encode()


def _zip_bytes(
    members: dict[str, bytes],
    *,
    encrypted: bool = False,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, content in members.items():
            info = zipfile.ZipInfo(path)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
    data = buffer.getvalue()
    if encrypted:
        data = _mark_first_zip_member_encrypted(data)
    return data


def _zip_bytes_with_directory(directory: str, members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(zipfile.ZipInfo(directory), b"")
        for path, content in members.items():
            info = zipfile.ZipInfo(path)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
    return buffer.getvalue()


def _zip_bytes_with_directory_payload(
    directory: str,
    payload: bytes,
    members: dict[str, bytes],
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        directory_info = zipfile.ZipInfo(directory)
        directory_info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(directory_info, payload)
        for path, content in members.items():
            info = zipfile.ZipInfo(path)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
    return buffer.getvalue()


def _insert_bytes_after_first_local_header(data: bytes, payload: bytes) -> bytes:
    local_header = data.find(b"PK\x03\x04")
    if local_header < 0:
        return data
    filename_length = int.from_bytes(data[local_header + 26 : local_header + 28], "little")
    extra_length = int.from_bytes(data[local_header + 28 : local_header + 30], "little")
    insert_at = local_header + 30 + filename_length + extra_length
    patched = bytearray(data[:insert_at] + payload + data[insert_at:])
    second_local = data.find(b"PK\x03\x04", local_header + 4)
    if second_local >= 0:
        central_header = bytes(patched).find(b"PK\x01\x02")
        while central_header >= 0:
            header_offset = int.from_bytes(
                patched[central_header + 42 : central_header + 46], "little"
            )
            if header_offset == second_local:
                patched[central_header + 42 : central_header + 46] = (
                    second_local + len(payload)
                ).to_bytes(4, "little")
                break
            central_header = bytes(patched).find(b"PK\x01\x02", central_header + 4)
    eocd = bytes(patched).rfind(b"PK\x05\x06")
    if eocd >= 0:
        central_directory_offset = int.from_bytes(patched[eocd + 16 : eocd + 20], "little")
        patched[eocd + 16 : eocd + 20] = (central_directory_offset + len(payload)).to_bytes(
            4, "little"
        )
    return bytes(patched)


def _zip_bytes_with_archive_comment(members: dict[str, bytes], comment: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.comment = comment
        for path, content in members.items():
            info = zipfile.ZipInfo(path)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
    return buffer.getvalue()


def _zip_bytes_with_member_extra(members: dict[str, bytes], extra: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, content in members.items():
            info = zipfile.ZipInfo(path)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.extra = extra
            archive.writestr(info, content)
    return buffer.getvalue()


def _zip_bytes_with_member_comment(members: dict[str, bytes], comment: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, content in members.items():
            info = zipfile.ZipInfo(path)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.comment = comment
            archive.writestr(info, content)
    return buffer.getvalue()


def _patch_first_zip_member_local_extra(data: bytes, extra: bytes) -> bytes:
    patched = bytearray(data)
    local_header = patched.find(b"PK\x03\x04")
    if local_header < 0:
        return data
    filename_length = int.from_bytes(patched[local_header + 26 : local_header + 28], "little")
    insert_at = local_header + 30 + filename_length
    patched[local_header + 28 : local_header + 30] = len(extra).to_bytes(2, "little")
    patched[insert_at:insert_at] = extra
    central_header = bytes(patched).find(b"PK\x01\x02")
    while central_header >= 0:
        header_offset = int.from_bytes(patched[central_header + 42 : central_header + 46], "little")
        if header_offset > local_header:
            patched[central_header + 42 : central_header + 46] = (
                header_offset + len(extra)
            ).to_bytes(4, "little")
        central_header = bytes(patched).find(b"PK\x01\x02", central_header + 4)
    eocd = bytes(patched).rfind(b"PK\x05\x06")
    if eocd >= 0:
        central_directory_offset = int.from_bytes(patched[eocd + 16 : eocd + 20], "little")
        patched[eocd + 16 : eocd + 20] = (central_directory_offset + len(extra)).to_bytes(
            4, "little"
        )
    return bytes(patched)


def _prepend_unreferenced_local_entry(data: bytes) -> bytes:
    hidden = _zip_bytes({"hidden.ros": b'<roster id="hidden"/>'})
    hidden_payload_end = hidden.find(b"PK\x01\x02")
    hidden_local = hidden[:hidden_payload_end]
    patched = bytearray(hidden_local + data)
    central_header = bytes(patched).find(b"PK\x01\x02")
    while central_header >= 0:
        header_offset = int.from_bytes(patched[central_header + 42 : central_header + 46], "little")
        patched[central_header + 42 : central_header + 46] = (
            header_offset + len(hidden_local)
        ).to_bytes(4, "little")
        central_header = bytes(patched).find(b"PK\x01\x02", central_header + 4)
    eocd = bytes(patched).rfind(b"PK\x05\x06")
    if eocd >= 0:
        central_directory_offset = int.from_bytes(patched[eocd + 16 : eocd + 20], "little")
        patched[eocd + 16 : eocd + 20] = (central_directory_offset + len(hidden_local)).to_bytes(
            4, "little"
        )
    return bytes(patched)


def _mark_first_zip_member_encrypted(data: bytes) -> bytes:
    patched = bytearray(data)
    local_header = patched.find(b"PK\x03\x04")
    central_header = patched.find(b"PK\x01\x02")
    if local_header >= 0:
        patched[local_header + 6 : local_header + 8] = (
            int.from_bytes(patched[local_header + 6 : local_header + 8], "little") | 0x1
        ).to_bytes(2, "little")
    if central_header >= 0:
        patched[central_header + 8 : central_header + 10] = (
            int.from_bytes(patched[central_header + 8 : central_header + 10], "little") | 0x1
        ).to_bytes(2, "little")
    return bytes(patched)


def _patch_first_zip_member_compression_method(data: bytes, method: int) -> bytes:
    patched = bytearray(data)
    local_header = patched.find(b"PK\x03\x04")
    central_header = patched.find(b"PK\x01\x02")
    if local_header >= 0:
        patched[local_header + 8 : local_header + 10] = method.to_bytes(2, "little")
    if central_header >= 0:
        patched[central_header + 10 : central_header + 12] = method.to_bytes(2, "little")
    return bytes(patched)


def _patch_first_zip_member_local_filename(data: bytes, filename: bytes) -> bytes:
    patched = bytearray(data)
    local_header = patched.find(b"PK\x03\x04")
    if local_header < 0:
        return data
    filename_length = int.from_bytes(patched[local_header + 26 : local_header + 28], "little")
    if len(filename) != filename_length:
        raise ValueError("Replacement filename must have the same encoded length")
    filename_offset = local_header + 30
    patched[filename_offset : filename_offset + filename_length] = filename
    return bytes(patched)


def _patch_first_zip_member_local_flag_bits(data: bytes, flag_bits: int) -> bytes:
    patched = bytearray(data)
    local_header = patched.find(b"PK\x03\x04")
    if local_header >= 0:
        patched[local_header + 6 : local_header + 8] = flag_bits.to_bytes(2, "little")
    return bytes(patched)


def _patch_first_zip_member_local_compression_method(data: bytes, method: int) -> bytes:
    patched = bytearray(data)
    local_header = patched.find(b"PK\x03\x04")
    if local_header >= 0:
        patched[local_header + 8 : local_header + 10] = method.to_bytes(2, "little")
    return bytes(patched)


def _insert_bytes_before_central_directory(data: bytes, payload: bytes) -> bytes:
    eocd = data.rfind(b"PK\x05\x06")
    if eocd < 0:
        return data
    central_directory_offset = int.from_bytes(data[eocd + 16 : eocd + 20], "little")
    patched = bytearray(data[:central_directory_offset] + payload + data[central_directory_offset:])
    new_eocd = eocd + len(payload)
    patched[new_eocd + 16 : new_eocd + 20] = (central_directory_offset + len(payload)).to_bytes(
        4, "little"
    )
    return bytes(patched)


def _corrupt_first_zip_member_payload(data: bytes) -> bytes:
    patched = bytearray(data)
    local_header = patched.find(b"PK\x03\x04")
    if local_header < 0:
        return data
    filename_length = int.from_bytes(patched[local_header + 26 : local_header + 28], "little")
    extra_length = int.from_bytes(patched[local_header + 28 : local_header + 30], "little")
    payload_offset = local_header + 30 + filename_length + extra_length
    if payload_offset < len(patched):
        patched[payload_offset] ^= 0xFF
    return bytes(patched)


def _forge_first_zip_member_uncompressed_size(data: bytes, *, uncompressed_size: int) -> bytes:
    patched = bytearray(data)
    local_header = patched.find(b"PK\x03\x04")
    central_header = patched.find(b"PK\x01\x02")
    if local_header < 0 or central_header < 0:
        return data
    local_crc = binascii.crc32(b'<roster id="roster-1" name="Synthetic Army"/>') & 0xFFFFFFFF
    for offset in (local_header + 14, central_header + 16):
        patched[offset : offset + 4] = local_crc.to_bytes(4, "little")
    for offset in (local_header + 22, central_header + 24):
        patched[offset : offset + 4] = uncompressed_size.to_bytes(4, "little")
    return bytes(patched)


def _deep_roster_xml(depth: int) -> bytes:
    opening = [
        '<roster id="roster-1" name="Synthetic Army">',
        '<forces><force id="force-1"><selections>',
    ]
    closing = ["</selections></force></forces></roster>"]
    for index in range(depth):
        opening.append(f'<selection id="selection-{index}" name="Nested {index}" type="unit">')
        opening.append("<selections>")
        closing.append("</selections></selection>")
    return "".join((*opening, *reversed(closing))).encode()


def test_ros_bytes_produce_estimated_source_record_and_canonical_army() -> None:
    result = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_safe_roster_xml(),
        source_kind="ros_xml",
        source_ref_ids=("local-file:synthetic",),
    )

    assert result.readiness == "estimated"
    assert result.tool_id == "roster_import"
    assert not result.overlays
    assert not result.allows_recommendation_language()
    assert result.source_ref_ids == ("local-file:synthetic",)

    source = result.payload.source
    assert source.filename == "synthetic.ros"
    assert source.source_kind == "ros_xml"
    assert source.byte_size > 0
    assert source.sha256
    assert source.selected_xml_member_path is None
    assert source.selected_xml_sha256 == source.sha256
    assert source.parser_version == "roster-import/v0"
    assert source.schema_version == "roster-import-source/v0"
    assert source.quarantine_status == "accepted"

    army = result.payload.army
    assert army is not None
    assert army.roster_id == "roster-1"
    assert army.name == "Synthetic Army"
    assert army.game_system_id == "game-system-1"
    assert army.catalogue_name == "Synthetic Catalogue"
    assert army.source_format == "battlescribe_ros_v0"
    assert army.source_ref_ids == ("local-file:synthetic",)
    assert [selection.raw_id for selection in army.selections] == ["unit-1", "upgrade-1"]
    assert army.selections[0].source_path == "roster/force-1/unit-1"
    assert army.selections[0].children[0].raw_id == "model-1"
    assert army.selections[0].costs[0].name == "pts"
    assert army.selections[0].costs[0].value == "125"


def test_rosz_bytes_record_archive_member_and_selected_xml_hash() -> None:
    archive_bytes = _zip_bytes({"folder/synthetic.ros": _safe_roster_xml()})

    result = build_roster_import_result_from_bytes(
        filename="synthetic.rosz",
        data=archive_bytes,
        source_kind="rosz_archive",
        source_ref_ids=("local-file:synthetic-archive",),
    )

    assert result.readiness == "estimated"
    source = result.payload.source
    assert source.source_kind == "rosz_archive"
    assert source.selected_xml_member_path == "folder/synthetic.ros"
    assert source.selected_xml_sha256
    assert source.archive_members[0].path == "folder/synthetic.ros"
    assert source.archive_members[0].compressed_size > 0
    assert source.archive_members[0].uncompressed_size == len(_safe_roster_xml())
    assert source.archive_members[0].decompression_ratio >= 1.0
    assert result.payload.army is not None


def test_import_hash_changes_with_filename_source_kind_or_bytes() -> None:
    base = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_safe_roster_xml("Synthetic Army"),
        source_kind="ros_xml",
    )
    changed_filename = build_roster_import_result_from_bytes(
        filename="renamed.ros",
        data=_safe_roster_xml("Synthetic Army"),
        source_kind="ros_xml",
    )
    changed_bytes = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_safe_roster_xml("Renamed Army"),
        source_kind="ros_xml",
    )
    changed_kind = build_roster_import_result_from_bytes(
        filename="synthetic.rosz",
        data=_zip_bytes({"synthetic.ros": _safe_roster_xml("Synthetic Army")}),
        source_kind="rosz_archive",
    )

    assert (
        len(
            {
                base.input_hash,
                changed_filename.input_hash,
                changed_bytes.input_hash,
                changed_kind.input_hash,
            }
        )
        == 4
    )


def test_nested_selections_and_costs_are_not_silently_discarded() -> None:
    result = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_safe_roster_xml(),
        source_kind="ros_xml",
    )

    army = result.payload.army
    assert army is not None
    flattened = army.flattened_selections()

    assert [selection.raw_id for selection in flattened] == [
        "unit-1",
        "model-1",
        "upgrade-1",
    ]
    assert [cost.value for selection in flattened for cost in selection.costs] == ["125", "25"]


def test_malicious_archive_path_traversal_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({"../evil.ros": _safe_roster_xml()}),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert result.payload.army is None
    assert not result.overlays
    assert not result.allows_recommendation_language()
    assert any(reason.reason_id == "unsafe-archive-path" for reason in result.block_reasons)


def test_malicious_archive_embedded_path_traversal_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({"safe/../evil.ros": _safe_roster_xml()}),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-archive-path" for reason in result.block_reasons)


def test_malicious_archive_absolute_path_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({"C:/evil.ros": _safe_roster_xml()}),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-archive-path" for reason in result.block_reasons)


def test_malicious_archive_windows_drive_relative_path_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({"C:../evil.ros": _safe_roster_xml()}),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-archive-path" for reason in result.block_reasons)


def test_malicious_archive_windows_drive_member_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({"C:evil.ros": _safe_roster_xml()}),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-archive-path" for reason in result.block_reasons)


def test_malicious_archive_unsafe_directory_entry_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes_with_directory("../evil/", {"synthetic.ros": _safe_roster_xml()}),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-archive-path" for reason in result.block_reasons)


def test_malicious_archive_directory_payload_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes_with_directory_payload(
            "safe/",
            payload=b"hidden",
            members={"synthetic.ros": _safe_roster_xml()},
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(
        reason.reason_id in {"archive-member-read-failed", "unexpected-archive-member"}
        for reason in result.block_reasons
    )


def test_malicious_archive_directory_local_payload_span_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_insert_bytes_after_first_local_header(
            _zip_bytes_with_directory("safe/", {"synthetic.ros": _safe_roster_xml()}),
            payload=b"hidden",
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "archive-member-read-failed" for reason in result.block_reasons)


def test_malicious_archive_comment_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes_with_archive_comment(
            {"synthetic.ros": _safe_roster_xml()},
            comment=b"hidden",
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unexpected-archive-member" for reason in result.block_reasons)


def test_malicious_archive_member_extra_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes_with_member_extra(
            {"synthetic.ros": _safe_roster_xml()},
            extra=b"\x01\x00\x00\x00",
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unexpected-archive-member" for reason in result.block_reasons)


def test_malicious_archive_member_comment_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes_with_member_comment(
            {"synthetic.ros": _safe_roster_xml()},
            comment=b"hidden",
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unexpected-archive-member" for reason in result.block_reasons)


def test_malicious_archive_selected_local_extra_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_patch_first_zip_member_local_extra(
            _zip_bytes({"synthetic.ros": _safe_roster_xml()}),
            extra=b"\x01\x00\x00\x00",
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unexpected-archive-member" for reason in result.block_reasons)


def test_malicious_archive_directory_local_extra_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_patch_first_zip_member_local_extra(
            _zip_bytes_with_directory("safe/", {"synthetic.ros": _safe_roster_xml()}),
            extra=b"\x01\x00\x00\x00",
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unexpected-archive-member" for reason in result.block_reasons)


def test_malicious_archive_unreferenced_leading_local_entry_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_prepend_unreferenced_local_entry(_zip_bytes({"synthetic.ros": _safe_roster_xml()})),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "archive-member-read-failed" for reason in result.block_reasons)


def test_malicious_archive_trailing_bytes_after_eocd_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({"synthetic.ros": _safe_roster_xml()}) + b"hidden",
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "archive-member-read-failed" for reason in result.block_reasons)


def test_malicious_archive_nested_archive_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({"nested.zip": b"not really a zip"}),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "nested-archive-member" for reason in result.block_reasons)


def test_malicious_archive_encrypted_member_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({"synthetic.ros": _safe_roster_xml()}, encrypted=True),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "encrypted-archive-member" for reason in result.block_reasons)


def test_malicious_archive_unsupported_compression_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_patch_first_zip_member_compression_method(
            _zip_bytes({"synthetic.ros": _safe_roster_xml()}),
            method=99,
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(
        reason.reason_id == "unsupported-archive-compression" for reason in result.block_reasons
    )


def test_malicious_archive_local_header_path_mismatch_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_patch_first_zip_member_local_filename(
            _zip_bytes({"safe123.ros": _safe_roster_xml()}),
            filename=b"../evil.ros",
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-archive-path" for reason in result.block_reasons)


def test_malicious_archive_local_header_encrypted_flag_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_patch_first_zip_member_local_flag_bits(
            _zip_bytes({"synthetic.ros": _safe_roster_xml()}),
            flag_bits=0x1,
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "encrypted-archive-member" for reason in result.block_reasons)


def test_malicious_archive_local_header_compression_mismatch_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_patch_first_zip_member_local_compression_method(
            _zip_bytes({"synthetic.ros": _safe_roster_xml()}),
            method=99,
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(
        reason.reason_id == "unsupported-archive-compression" for reason in result.block_reasons
    )


def test_malicious_archive_trailing_selected_member_bytes_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_insert_bytes_before_central_directory(
            _zip_bytes({"synthetic.ros": _safe_roster_xml()}),
            payload=b"PK\x03\x04hidden trailing member bytes",
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "archive-member-read-failed" for reason in result.block_reasons)


def test_malicious_archive_local_data_descriptor_flag_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_patch_first_zip_member_local_flag_bits(
            _zip_bytes({"synthetic.ros": _safe_roster_xml()}),
            flag_bits=0x8,
        ),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "archive-member-read-failed" for reason in result.block_reasons)


def test_malicious_archive_corrupt_member_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_corrupt_first_zip_member_payload(_zip_bytes({"synthetic.ros": _safe_roster_xml()})),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "archive-member-read-failed" for reason in result.block_reasons)


def test_malicious_archive_unexpected_extension_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({"synthetic.txt": b"hello"}),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unexpected-archive-member" for reason in result.block_reasons)


def test_malicious_archive_excessive_member_count_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({f"synthetic-{index}.ros": _safe_roster_xml() for index in range(4)}),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "archive-member-count" for reason in result.block_reasons)


def test_malicious_archive_excessive_directory_count_blocks_result() -> None:
    members = {f"dir-{index}/": b"" for index in range(1000)}
    archive_bytes = _zip_bytes_with_directory("safe/", {"synthetic.ros": _safe_roster_xml()})
    buffer = io.BytesIO(archive_bytes)
    with zipfile.ZipFile(buffer, "a", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in members:
            archive.writestr(zipfile.ZipInfo(path), b"")

    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=buffer.getvalue(),
        source_kind="rosz_archive",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "archive-member-count" for reason in result.block_reasons)


def test_malicious_archive_oversized_uncompressed_member_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({"synthetic.ros": b"<roster>" + (b" " * 2048) + b"</roster>"}),
        source_kind="rosz_archive",
        max_xml_bytes=1024,
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "archive-member-too-large" for reason in result.block_reasons)


def test_malicious_archive_excessive_decompression_ratio_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=_zip_bytes({"synthetic.ros": b"A" * 4096}),
        source_kind="rosz_archive",
        max_decompression_ratio=2.0,
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "archive-decompression-ratio" for reason in result.block_reasons)


def test_malicious_archive_forged_uncompressed_size_blocks_actual_inflation() -> None:
    truncated_xml = b'<roster id="roster-1" name="Synthetic Army"/>'
    forged_archive = _forge_first_zip_member_uncompressed_size(
        _zip_bytes({"synthetic.ros": truncated_xml + (b" " * 65536)}),
        uncompressed_size=len(truncated_xml),
    )

    result = build_roster_import_result_from_bytes(
        filename="evil.rosz",
        data=forged_archive,
        source_kind="rosz_archive",
        max_xml_bytes=128,
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "archive-member-too-large" for reason in result.block_reasons)


def test_malformed_xml_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=b"<roster>",
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert result.payload.army is None
    assert any(reason.reason_id == "malformed-roster-xml" for reason in result.block_reasons)


def test_xml_doctype_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=b'<!DOCTYPE roster [<!ENTITY x "boom">]><roster id="r" name="n"/>',
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-roster-xml" for reason in result.block_reasons)


def test_utf16_xml_doctype_blocks_result() -> None:
    xml = (
        '<?xml version="1.0" encoding="UTF-16"?>'
        '<!DOCTYPE roster [<!ENTITY x "boom">]><roster id="r" name="&x;"/>'
    )
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=xml.encode("utf-16"),
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(
        reason.reason_id == "unsupported-roster-xml-encoding" for reason in result.block_reasons
    )


def test_utf16le_without_bom_xml_doctype_blocks_result() -> None:
    xml = '<?xml version="1.0"?><!DOCTYPE roster [<!ENTITY x "boom">]<roster id="r" name="&x;"/>'
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=xml.encode("utf-16le"),
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(
        reason.reason_id == "unsupported-roster-xml-encoding" for reason in result.block_reasons
    )


def test_utf16be_without_bom_xml_doctype_blocks_result() -> None:
    xml = '<?xml version="1.0"?><!DOCTYPE roster [<!ENTITY x "boom">]<roster id="r" name="&x;"/>'
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=xml.encode("utf-16be"),
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(
        reason.reason_id == "unsupported-roster-xml-encoding" for reason in result.block_reasons
    )


def test_xml_entity_reference_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=b'<roster id="r" name="&xxe;"/>',
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-roster-xml" for reason in result.block_reasons)


def test_xml_xinclude_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=b'<roster xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="x"/></roster>',
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-roster-xml" for reason in result.block_reasons)


def test_xml_url_reference_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=b'<roster id="r" name="http://example.com/evil"/>',
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-roster-xml" for reason in result.block_reasons)


def test_xml_encoded_url_reference_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=b'<roster id="r" name="http&#58;//example.com/evil"/>',
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-roster-xml" for reason in result.block_reasons)


def test_xml_encoded_namespace_url_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=b'<roster xmlns="http&#58;//example.com/ns" id="r" name="n"/>',
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-roster-xml" for reason in result.block_reasons)


def test_xml_unused_encoded_namespace_url_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=b'<roster xmlns:evil="http&#58;//example.com/ns" id="r" name="n"/>',
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-roster-xml" for reason in result.block_reasons)


def test_xml_unused_encoded_https_namespace_url_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=b'<roster xmlns:evil="https&#58;//example.com/ns" id="r" name="n"/>',
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-roster-xml" for reason in result.block_reasons)


def test_xml_processing_instruction_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=(b'<?xml-stylesheet href="http&#58;//example.com/x.css"?><roster id="r" name="n"/>'),
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-roster-xml" for reason in result.block_reasons)


def test_xml_comment_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=b'<!-- http&#58;//example.com --><roster id="r" name="n"/>',
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert any(reason.reason_id == "unsafe-roster-xml" for reason in result.block_reasons)


def test_xml_excessive_selection_depth_blocks_result() -> None:
    result = build_roster_import_result_from_bytes(
        filename="deep.ros",
        data=_deep_roster_xml(depth=64),
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert result.payload.army is None
    assert any(reason.reason_id == "roster-xml-too-deep" for reason in result.block_reasons)
