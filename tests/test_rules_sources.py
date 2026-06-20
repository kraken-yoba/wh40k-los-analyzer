from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import TracebackType

import pytest

from warhammer_companion.ingestion.rules_sources import (
    SourceRef,
    build_current_rules_foundation,
    verify_remote_http_source,
)


@dataclass(frozen=True)
class _FakeResponse:
    status_code: int = 200
    url: str = "https://assets.warhammer-community.com/example-core-rules.pdf"
    headers: Mapping[str, str] = field(default_factory=lambda: {"content-type": "application/pdf"})
    chunks: tuple[bytes, ...] = (b"abc", b"", b"def")

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int) -> Iterable[bytes]:
        assert chunk_size > 0
        return (chunk for chunk in self.chunks)


def _fake_get_factory(response: _FakeResponse) -> object:
    def _fake_get(url: str, *, stream: bool, timeout: int | float) -> _FakeResponse:
        assert url == "https://assets.warhammer-community.com/example-core-rules.pdf"
        assert stream is True
        assert timeout == 120
        return response

    return _fake_get


def _fake_get(url: str, *, stream: bool, timeout: int | float) -> _FakeResponse:
    assert url == "https://assets.warhammer-community.com/example-core-rules.pdf"
    assert stream is True
    assert timeout == 120
    return _FakeResponse()


def test_current_foundation_records_mfm_version_and_update_date() -> None:
    foundation = build_current_rules_foundation(
        retrieved_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
    )

    mfm_entry = foundation.registry.get_entry("official-mfm-online")
    mfm_source = foundation.registry.get_source("mfm-online")

    assert mfm_entry.readiness == "source_pending"
    assert mfm_entry.freshness == "current"
    assert mfm_entry.mutable is True
    assert mfm_source.upstream_version == "v1.0"
    assert mfm_source.upstream_updated == date(2026, 6, 17)
    assert mfm_source.sha256 is None
    assert not mfm_source.has_integrity_marker()


def test_current_foundation_keeps_unhashed_mutable_sources_untrusted() -> None:
    foundation = build_current_rules_foundation(
        retrieved_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
    )

    untrusted_mutable = [
        entry
        for entry in foundation.registry.entries
        if entry.mutable and entry.readiness != "trusted_ref"
    ]

    assert {entry.pack_id for entry in untrusted_mutable} >= {
        "official-core-rules-pdf",
        "official-mfm-online",
    }
    assert foundation.rules_pack.readiness == "source_pending"


def test_current_foundation_requires_refresh_timestamp_for_current_freshness() -> None:
    foundation = build_current_rules_foundation()

    assert foundation.registry.get_entry("official-mfm-online").freshness == "unknown"


def test_rules_pack_exposes_source_pending_concepts_and_blocks_legacy_assumptions() -> None:
    foundation = build_current_rules_foundation()
    concepts = foundation.rules_pack.concept_map()

    assert concepts["terrain_area"].status == "source_pending"
    assert concepts["engagement"].status == "source_pending"
    assert concepts["charge"].source_ref_ids == ("core-rules-pdf",)
    assert all(concept.status != "trusted_ref" for concept in foundation.rules_pack.concepts)
    assert foundation.rules_pack.blocks_assumption("engagement_range_one_inch_only")
    assert foundation.rules_pack.blocks_assumption("reserves_are_deep_strike")
    assert foundation.rules_pack.blocks_assumption("visibility_boolean_only")
    assert not foundation.rules_pack.blocks_assumption("source_backed_current_rule")


def test_current_foundation_does_not_embed_rules_text() -> None:
    foundation = build_current_rules_foundation()

    concept_labels = [concept.label for concept in foundation.rules_pack.concepts]
    warning_text = " ".join(foundation.rules_pack.warnings)

    assert all(len(label.split()) <= 4 for label in concept_labels)
    assert all("." not in label for label in concept_labels)
    assert "Copyright" not in warning_text
    assert "Games Workshop Limited" not in warning_text


def test_verify_remote_http_source_streams_and_hashes_bytes() -> None:
    source = SourceRef(
        source_id="core-rules-pdf",
        kind="remote_http",
        label="Core Rules PDF",
        publisher="Games Workshop",
        url="https://assets.warhammer-community.com/example-core-rules.pdf",
    )

    result = verify_remote_http_source(source, get=_fake_get)

    assert result.source_id == "core-rules-pdf"
    assert result.status_code == 200
    assert result.final_url == "https://assets.warhammer-community.com/example-core-rules.pdf"
    assert result.content_type == "application/pdf"
    assert result.byte_size == 6
    assert result.sha256 == hashlib.sha256(b"abcdef").hexdigest()
    assert result.readiness == "trusted_ref"


def test_verify_remote_http_source_blocks_failed_status() -> None:
    source = SourceRef(
        source_id="core-rules-pdf",
        kind="remote_http",
        label="Core Rules PDF",
        publisher="Games Workshop",
        url="https://assets.warhammer-community.com/example-core-rules.pdf",
    )

    result = verify_remote_http_source(
        source,
        get=_fake_get_factory(_FakeResponse(status_code=404)),
    )

    assert result.status_code == 404
    assert result.readiness == "blocked"
    assert result.byte_size == 0
    assert result.warnings


def test_verify_remote_http_source_blocks_incomplete_metadata() -> None:
    source = SourceRef(
        source_id="core-rules-pdf",
        kind="remote_http",
        label="Core Rules PDF",
        publisher="Games Workshop",
        url="https://assets.warhammer-community.com/example-core-rules.pdf",
    )

    result = verify_remote_http_source(
        source,
        get=_fake_get_factory(_FakeResponse(headers={}, chunks=())),
    )

    assert result.readiness == "blocked"
    assert result.byte_size == 0
    assert result.content_type is None
    assert result.warnings


def test_verify_remote_http_source_rejects_unapproved_hosts_before_fetch() -> None:
    source = SourceRef(
        source_id="unexpected-host",
        kind="remote_http",
        label="Unexpected Host",
        publisher="Example",
        url="https://example.com/source.pdf",
    )

    with pytest.raises(ValueError, match="approved"):
        verify_remote_http_source(source, get=_fake_get)


def test_verify_remote_http_source_blocks_unapproved_redirect() -> None:
    source = SourceRef(
        source_id="core-rules-pdf",
        kind="remote_http",
        label="Core Rules PDF",
        publisher="Games Workshop",
        url="https://assets.warhammer-community.com/example-core-rules.pdf",
    )

    result = verify_remote_http_source(
        source,
        get=_fake_get_factory(_FakeResponse(url="https://example.com/final.pdf")),
    )

    assert result.readiness == "blocked"
    assert result.warnings


def test_verify_remote_http_source_rejects_non_remote_sources() -> None:
    source = SourceRef(
        source_id="community-pack",
        kind="community_pack",
        label="Community Pack",
        publisher="Community",
        url="https://example.com/community.zip",
    )

    with pytest.raises(ValueError, match="remote_http"):
        verify_remote_http_source(source, get=_fake_get)
