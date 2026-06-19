from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self, assert_never

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


@dataclass(frozen=True, slots=True)
class SourceTrustPolicyViolation(ValueError):
    source_kind: SourceKind
    message: str

    def __str__(self) -> str:
        return f"{self.source_kind}: {self.message}"


class SourceRef(BaseModel):
    model_config = ConfigDict(frozen=True)

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

    @model_validator(mode="after")
    def enforce_source_trust_policy(self) -> Self:
        match self.source_kind:
            case SourceKind.OFFICIAL_PDF:
                if self.authority != SourceAuthority.AUTHORITATIVE or self.trust_state not in (
                    SourceTrustState.TRUSTED,
                    SourceTrustState.REVIEWED,
                ):
                    raise SourceTrustPolicyViolation(
                        source_kind=self.source_kind,
                        message="official PDFs must be authoritative and trusted or reviewed",
                    )
            case SourceKind.PUBLIC_SHEET:
                if (
                    self.authority != SourceAuthority.SUPPORTING
                    or self.trust_state != SourceTrustState.UNTRUSTED
                ):
                    raise SourceTrustPolicyViolation(
                        source_kind=self.source_kind,
                        message="public sheets must remain untrusted supporting material",
                    )
            case SourceKind.WAHAPEDIA_10E:
                if (
                    self.authority != SourceAuthority.PROVISIONAL_PROFILE_BOOTSTRAP
                    or self.trust_state != SourceTrustState.PROVISIONAL
                    or self.edition_id != "wh40k-10e"
                ):
                    raise SourceTrustPolicyViolation(
                        source_kind=self.source_kind,
                        message=(
                            "Wahapedia data must remain a provisional wh40k-10e "
                            "profile bootstrap source"
                        ),
                    )
            case SourceKind.LOCAL_FIXTURE:
                if self.authority != SourceAuthority.LOCAL_TEST_FIXTURE:
                    raise SourceTrustPolicyViolation(
                        source_kind=self.source_kind,
                        message="local fixtures must use local test fixture authority",
                    )
            case unreachable:
                assert_never(unreachable)
        return self

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
