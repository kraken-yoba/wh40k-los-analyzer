from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class SourceKind(StrEnum):
    OFFICIAL_PDF = "official_pdf"
    PUBLIC_SHEET = "public_sheet"
    WAHAPEDIA_10E = "wahapedia_10e"
    LOCAL_FIXTURE = "local_fixture"


class SourceAuthority(StrEnum):
    AUTHORITATIVE = "authoritative"
    SUPPORTING = "supporting"
    PROVISIONAL_PROFILE_BOOTSTRAP = "provisional_profile_bootstrap"
    LOCAL_TEST_FIXTURE = "local_test_fixture"


class SourceTrustState(StrEnum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    PROVISIONAL = "provisional"
    REVIEWED = "reviewed"


class SourceRef(BaseModel):
    source_kind: SourceKind
    authority: SourceAuthority
    trust_state: SourceTrustState
    source_document_id: str
    source_label: str
    url: str | None = None
    local_filename: str | None = None
    sha256: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    section_id: str | None = None
    section_label: str | None = None
    sheet_gid: str | None = None
    edition_id: str | None = None

    @classmethod
    def public_sheet(
        cls,
        *,
        source_document_id: str,
        source_label: str,
        url: str,
        sheet_gid: str,
    ) -> SourceRef:
        return cls(
            source_kind=SourceKind.PUBLIC_SHEET,
            authority=SourceAuthority.SUPPORTING,
            trust_state=SourceTrustState.UNTRUSTED,
            source_document_id=source_document_id,
            source_label=source_label,
            url=url,
            sheet_gid=sheet_gid,
        )

    @classmethod
    def wahapedia_10e(
        cls,
        *,
        source_document_id: str,
        source_label: str,
        url: str,
    ) -> SourceRef:
        return cls(
            source_kind=SourceKind.WAHAPEDIA_10E,
            authority=SourceAuthority.PROVISIONAL_PROFILE_BOOTSTRAP,
            trust_state=SourceTrustState.PROVISIONAL,
            source_document_id=source_document_id,
            source_label=source_label,
            url=url,
            edition_id="wh40k-10e",
        )
