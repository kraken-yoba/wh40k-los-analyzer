from __future__ import annotations

import hashlib
import ipaddress
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from types import TracebackType
from typing import Literal, Protocol, cast
from urllib.parse import urlparse

SourceKind = Literal[
    "remote_http",
    "local_file",
    "manual_entry",
    "derived_artifact",
    "community_pack",
]
SourceReadiness = Literal[
    "trusted_ref",
    "source_pending",
    "stale",
    "blocked",
    "incompatible",
]
FreshnessState = Literal["current", "unknown", "stale"]
CompatibilityState = Literal["compatible", "candidate", "incompatible", "unknown"]

CORE_RULES_PDF_URL = (
    "https://assets.warhammer-community.com/"
    "eng_01-06_warhammer40k_new40k_core_rules-was6fbu1ix-hfewhmxyiy.pdf"
)
WARHAMMER_DOWNLOADS_URL = "https://www.warhammer-community.com/en-gb/downloads/warhammer-40000/"
MFM_URL = "https://mfm.warhammer-community.com/"
NEW_RECRUIT_URL = "https://www.newrecruit.eu/"
BSDATA_URL = "https://www.bsdata.net/"
EVENT_COMPANION_ARTICLE_URL = (
    "https://www.warhammer-community.com/en-gb/articles/lszdpzmc/"
    "new40k-download-the-new-event-companions-today/"
)
APPROVED_REMOTE_HOSTS = frozenset(
    {
        "assets.warhammer-community.com",
        "www.warhammer-community.com",
        "mfm.warhammer-community.com",
        "www.newrecruit.eu",
        "www.bsdata.net",
    }
)

INITIAL_RULE_CONCEPTS = (
    ("terrain_area", "Terrain Area"),
    ("terrain_feature", "Terrain Feature"),
    ("terrain_category", "Terrain Category"),
    ("visibility_trait", "Visibility Trait"),
    ("benefit_of_cover", "Benefit Of Cover"),
    ("hidden", "Hidden"),
    ("obscuring", "Obscuring"),
    ("solid", "Solid"),
    ("model_base", "Model Base"),
    ("measuring", "Measuring"),
    ("engagement", "Engagement"),
    ("coherency", "Coherency"),
    ("normal_move", "Normal Move"),
    ("advance", "Advance"),
    ("charge", "Charge"),
    ("attack_sequence", "Attack Sequence"),
    ("objective_control", "Objective Control"),
    ("actions", "Actions"),
    ("reserves", "Reserves"),
    ("transports", "Transports"),
    ("disembark", "Disembark"),
)

LEGACY_ASSUMPTION_BLACKLIST = (
    "cover_as_default_plus_one_save",
    "engagement_range_one_inch_only",
    "reserves_are_deep_strike",
    "objectives_are_markers_only",
    "visibility_boolean_only",
)


class RemoteResponse(Protocol):
    @property
    def status_code(self) -> int: ...

    @property
    def url(self) -> str: ...

    @property
    def headers(self) -> Mapping[str, str]: ...

    def __enter__(self) -> RemoteResponse: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...

    def raise_for_status(self) -> None: ...

    def iter_content(self, chunk_size: int) -> Iterable[bytes]: ...


class RemoteGet(Protocol):
    def __call__(self, url: str, *, stream: bool, timeout: int | float) -> RemoteResponse: ...


@dataclass(frozen=True, slots=True)
class SourceRef:
    source_id: str
    kind: SourceKind
    label: str
    publisher: str
    url: str | None = None
    retrieved_at: datetime | None = None
    upstream_version: str | None = None
    upstream_updated: date | None = None
    sha256: str | None = None
    content_type: str | None = None
    byte_size: int | None = None
    anchors: tuple[str, ...] = ()

    def has_integrity_marker(self) -> bool:
        return self.sha256 is not None and self.byte_size is not None


@dataclass(frozen=True, slots=True)
class SourcePackEntry:
    pack_id: str
    label: str
    role: str
    source_ref_ids: tuple[str, ...]
    readiness: SourceReadiness
    freshness: FreshnessState
    compatibility: CompatibilityState
    mutable: bool
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SourcePackRegistry:
    sources: tuple[SourceRef, ...]
    entries: tuple[SourcePackEntry, ...]

    def get_source(self, source_id: str) -> SourceRef:
        for source in self.sources:
            if source.source_id == source_id:
                return source
        raise KeyError(f"Unknown source ref: {source_id}")

    def get_entry(self, pack_id: str) -> SourcePackEntry:
        for entry in self.entries:
            if entry.pack_id == pack_id:
                return entry
        raise KeyError(f"Unknown source pack: {pack_id}")

    def entries_by_role(self, role: str) -> tuple[SourcePackEntry, ...]:
        return tuple(entry for entry in self.entries if entry.role == role)

    def entries_requiring_refresh(self) -> tuple[SourcePackEntry, ...]:
        return tuple(
            entry for entry in self.entries if entry.mutable and entry.readiness != "trusted_ref"
        )


@dataclass(frozen=True, slots=True)
class RulesConcept:
    concept_id: str
    label: str
    status: SourceReadiness
    source_ref_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RulesPack:
    ruleset_id: str
    edition_id: str
    season_id: str
    source_version: str
    effective_date: date | None
    readiness: SourceReadiness
    source_ref_ids: tuple[str, ...]
    concepts: tuple[RulesConcept, ...]
    terminology_blacklist: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def concept_map(self) -> dict[str, RulesConcept]:
        return {concept.concept_id: concept for concept in self.concepts}

    def blocks_assumption(self, assumption_key: str) -> bool:
        return assumption_key in self.terminology_blacklist


@dataclass(frozen=True, slots=True)
class SourceRulesFoundation:
    registry: SourcePackRegistry
    rules_pack: RulesPack


@dataclass(frozen=True, slots=True)
class RemoteSourceVerification:
    source_id: str
    status_code: int
    final_url: str
    content_type: str | None
    byte_size: int
    sha256: str
    readiness: SourceReadiness
    warnings: tuple[str, ...] = ()


def build_current_rules_foundation(
    retrieved_at: datetime | None = None,
) -> SourceRulesFoundation:
    mfm_freshness: FreshnessState = "current" if retrieved_at is not None else "unknown"
    mfm_warnings: tuple[str, ...] = (
        "Version and update metadata are recorded; row data is not imported.",
    )
    if retrieved_at is None:
        mfm_warnings = (
            "Version and update metadata are recorded without a refresh timestamp.",
            "Row data is not imported.",
        )
    sources = (
        SourceRef(
            source_id="warhammer-downloads-page",
            kind="remote_http",
            label="Warhammer 40,000 Downloads Page",
            publisher="Games Workshop",
            url=WARHAMMER_DOWNLOADS_URL,
            retrieved_at=retrieved_at,
        ),
        SourceRef(
            source_id="core-rules-pdf",
            kind="remote_http",
            label="Core Rules PDF Candidate",
            publisher="Games Workshop",
            url=CORE_RULES_PDF_URL,
            retrieved_at=retrieved_at,
        ),
        SourceRef(
            source_id="mfm-online",
            kind="remote_http",
            label="Munitorum Field Manual Online",
            publisher="Games Workshop",
            url=MFM_URL,
            retrieved_at=retrieved_at,
            upstream_version="v1.0",
            upstream_updated=date(2026, 6, 17),
        ),
        SourceRef(
            source_id="event-companion-article",
            kind="remote_http",
            label="Event Companion Article",
            publisher="Games Workshop",
            url=EVENT_COMPANION_ARTICLE_URL,
            retrieved_at=retrieved_at,
        ),
        SourceRef(
            source_id="new-recruit",
            kind="remote_http",
            label="New Recruit",
            publisher="New Recruit",
            url=NEW_RECRUIT_URL,
            retrieved_at=retrieved_at,
        ),
        SourceRef(
            source_id="bsdata",
            kind="community_pack",
            label="BSData Community Data",
            publisher="BSData Community",
            url=BSDATA_URL,
            retrieved_at=retrieved_at,
        ),
    )
    entries = (
        SourcePackEntry(
            pack_id="official-core-rules-pdf",
            label="Core Rules PDF Candidate",
            role="rules",
            source_ref_ids=("core-rules-pdf",),
            readiness="source_pending",
            freshness="unknown",
            compatibility="candidate",
            mutable=True,
            warnings=("Remote source must be fetched and hashed before trusted use.",),
        ),
        SourcePackEntry(
            pack_id="official-mfm-online",
            label="Munitorum Field Manual Online",
            role="points",
            source_ref_ids=("warhammer-downloads-page", "mfm-online"),
            readiness="source_pending",
            freshness=mfm_freshness,
            compatibility="candidate",
            mutable=True,
            warnings=mfm_warnings,
        ),
        SourcePackEntry(
            pack_id="official-event-companion-family",
            label="Event Companion Source Family",
            role="mission_and_event",
            source_ref_ids=("event-companion-article",),
            readiness="source_pending",
            freshness="unknown",
            compatibility="candidate",
            mutable=True,
            warnings=("Event source family is referenced without mechanics extraction.",),
        ),
        SourcePackEntry(
            pack_id="new-recruit-roster-ecosystem",
            label="New Recruit Roster Ecosystem",
            role="roster_candidate",
            source_ref_ids=("new-recruit", "bsdata"),
            readiness="source_pending",
            freshness="unknown",
            compatibility="unknown",
            mutable=True,
            warnings=("Roster ecosystem is not mechanics authority.",),
        ),
        SourcePackEntry(
            pack_id="bsdata-community-catalogs",
            label="BSData Community Catalogs",
            role="community_profile_candidate",
            source_ref_ids=("bsdata",),
            readiness="incompatible",
            freshness="unknown",
            compatibility="incompatible",
            mutable=True,
            warnings=("Community catalog compatibility must be proven before profile use.",),
        ),
    )
    rules_pack = RulesPack(
        ruleset_id="warhammer-40000",
        edition_id="current-source-candidate",
        season_id="source-pending",
        source_version="mfm-v1.0-metadata",
        effective_date=None,
        readiness="source_pending",
        source_ref_ids=("core-rules-pdf", "mfm-online", "event-companion-article"),
        concepts=tuple(
            RulesConcept(
                concept_id=concept_id,
                label=label,
                status="source_pending",
                source_ref_ids=("core-rules-pdf",),
            )
            for concept_id, label in INITIAL_RULE_CONCEPTS
        ),
        terminology_blacklist=LEGACY_ASSUMPTION_BLACKLIST,
        warnings=(
            "Mechanics are source-pending until field anchors and reviewed rules models exist.",
        ),
    )
    return SourceRulesFoundation(
        registry=SourcePackRegistry(sources=sources, entries=entries),
        rules_pack=rules_pack,
    )


def verify_remote_http_source(
    source: SourceRef,
    *,
    get: RemoteGet | None = None,
    timeout: int | float = 120,
    chunk_size: int = 1024 * 256,
) -> RemoteSourceVerification:
    if source.kind != "remote_http":
        raise ValueError("verify_remote_http_source requires a remote_http source")
    if source.url is None:
        raise ValueError("remote_http source requires a URL")
    if not _is_approved_remote_url(source.url):
        raise ValueError("remote_http source URL must use HTTPS and an approved host")

    if get is None:
        import requests

        get = cast(RemoteGet, requests.get)

    digest = hashlib.sha256()
    byte_size = 0
    with get(source.url, stream=True, timeout=timeout) as response:
        if response.status_code != 200:
            return RemoteSourceVerification(
                source_id=source.source_id,
                status_code=response.status_code,
                final_url=response.url,
                content_type=response.headers.get("content-type"),
                byte_size=0,
                sha256="",
                readiness="blocked",
                warnings=(f"Remote source returned HTTP {response.status_code}.",),
            )
        response.raise_for_status()
        if not _is_approved_remote_url(response.url):
            return RemoteSourceVerification(
                source_id=source.source_id,
                status_code=response.status_code,
                final_url=response.url,
                content_type=response.headers.get("content-type"),
                byte_size=0,
                sha256="",
                readiness="blocked",
                warnings=("Remote source redirected to an unapproved host.",),
            )
        for chunk in response.iter_content(chunk_size=chunk_size):
            if not chunk:
                continue
            digest.update(chunk)
            byte_size += len(chunk)
        content_type = response.headers.get("content-type")
        warnings: tuple[str, ...] = ()
        readiness: SourceReadiness = "trusted_ref"
        if byte_size <= 0 or content_type is None:
            warnings = ("Remote source verification did not produce complete metadata.",)
            readiness = "blocked"
        return RemoteSourceVerification(
            source_id=source.source_id,
            status_code=response.status_code,
            final_url=response.url,
            content_type=content_type,
            byte_size=byte_size,
            sha256=digest.hexdigest(),
            readiness=readiness,
            warnings=warnings,
        )


def _is_approved_remote_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    if parsed.hostname is None:
        return False
    hostname = parsed.hostname.lower()
    if _is_private_or_loopback_host(hostname):
        return False
    return hostname in APPROVED_REMOTE_HOSTS


def _is_private_or_loopback_host(hostname: str) -> bool:
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return hostname in {"localhost", "localhost.localdomain"}
    return address.is_private or address.is_loopback or address.is_link_local
