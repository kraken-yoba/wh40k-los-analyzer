from __future__ import annotations

from warhammer_companion.rules.sources import (
    SourceAuthority,
    SourceKind,
    SourceRef,
    SourceTrustState,
)


def test_official_pdf_source_ref_serializes_source_anchor() -> None:
    ref = SourceRef(
        source_kind=SourceKind.OFFICIAL_PDF,
        authority=SourceAuthority.AUTHORITATIVE,
        trust_state=SourceTrustState.TRUSTED,
        source_document_id="core-rules-2026-06-01",
        source_label="Warhammer 40,000 Core Rules",
        url="https://assets.warhammer-community.com/core.pdf",
        local_filename="core-rules.pdf",
        sha256="abc123",
        page_number=50,
        section_id="13.08",
        section_label="Benefit of Cover",
    )

    payload = ref.model_dump(mode="json")

    assert payload["source_kind"] == "official_pdf"
    assert payload["authority"] == "authoritative"
    assert payload["trust_state"] == "trusted"
    assert payload["section_id"] == "13.08"
    assert payload["page_number"] == 50


def test_public_sheet_source_ref_is_untrusted_by_default() -> None:
    ref = SourceRef.public_sheet(
        source_document_id="mission-sheet-public",
        source_label="Public mission sheet",
        url="https://docs.google.com/spreadsheets/d/example",
        sheet_gid="1565185881",
    )

    assert ref.source_kind == SourceKind.PUBLIC_SHEET
    assert ref.authority == SourceAuthority.SUPPORTING
    assert ref.trust_state == SourceTrustState.UNTRUSTED
    assert ref.sheet_gid == "1565185881"


def test_wahapedia_source_ref_is_provisional_profile_bootstrap() -> None:
    ref = SourceRef.wahapedia_10e(
        source_document_id="wahapedia-10e-datasheets",
        source_label="Wahapedia 10e data export",
        url="https://wahapedia.ru/wh40k10ed/the-rules/data-export/",
    )

    assert ref.source_kind == SourceKind.WAHAPEDIA_10E
    assert ref.authority == SourceAuthority.PROVISIONAL_PROFILE_BOOTSTRAP
    assert ref.trust_state == SourceTrustState.PROVISIONAL
    assert ref.edition_id == "wh40k-10e"
