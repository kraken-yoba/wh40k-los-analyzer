from collections.abc import Callable
from hashlib import sha256
from pathlib import Path

import pytest
from fortyk_los_backend.domain.manifest import SourceDocument, SourceKind, SourceManifest
from fortyk_los_backend.domain.source_cache import SourceDownloadAction, download_manifest_sources


def _document(*, expected_bytes: bytes, cache_path: Path | None = None) -> SourceDocument:
    return SourceDocument(
        document_id="core-rules-2026-06-01",
        kind=SourceKind.RULES,
        url="https://assets.warhammer-community.com/example-rules.pdf",
        expected_sha256=sha256(expected_bytes).hexdigest(),
        cache_path=cache_path or Path("data/pdfs/core_rules.pdf"),
        redistribution="do-not-commit",
    )


def _fetcher_that_writes(payload: bytes) -> Callable[[str, Path], None]:
    def fetcher(_url: str, destination: Path) -> None:
        destination.write_bytes(payload)

    return fetcher


def test_source_downloader_skips_existing_hash_matched_cache(tmp_path: Path) -> None:
    expected_bytes = b"cached official bytes"
    document = _document(expected_bytes=expected_bytes)
    manifest = SourceManifest(documents=(document,))
    cached_path = tmp_path / document.cache_path
    cached_path.parent.mkdir(parents=True)
    cached_path.write_bytes(expected_bytes)

    def fetcher(url: str, destination: Path) -> None:
        del destination
        raise AssertionError(f"hash-matched cache should not be fetched: {url}")

    [result] = download_manifest_sources(
        manifest,
        repo_root=tmp_path,
        fetch_to_path=fetcher,
    )

    assert result.action == SourceDownloadAction.SKIPPED_HASH_MATCH
    assert cached_path.read_bytes() == expected_bytes


def test_source_downloader_downloads_missing_file_after_hash_check(tmp_path: Path) -> None:
    expected_bytes = b"official source bytes"
    document = _document(expected_bytes=expected_bytes)
    manifest = SourceManifest(documents=(document,))

    def fetcher(url: str, destination: Path) -> None:
        assert url == document.url
        destination.write_bytes(expected_bytes)

    [result] = download_manifest_sources(
        manifest,
        repo_root=tmp_path,
        fetch_to_path=fetcher,
    )

    cached_path = tmp_path / document.cache_path
    assert result.action == SourceDownloadAction.DOWNLOADED
    assert result.actual_sha256 == document.expected_sha256
    assert cached_path.read_bytes() == expected_bytes
    assert not cached_path.with_suffix(".pdf.part").exists()


def test_source_downloader_replaces_hash_mismatched_cache_with_verified_download(
    tmp_path: Path,
) -> None:
    expected_bytes = b"fresh official source bytes"
    document = _document(expected_bytes=expected_bytes)
    manifest = SourceManifest(documents=(document,))
    cached_path = tmp_path / document.cache_path
    cached_path.parent.mkdir(parents=True)
    cached_path.write_bytes(b"old invalid bytes")

    [result] = download_manifest_sources(
        manifest,
        repo_root=tmp_path,
        fetch_to_path=_fetcher_that_writes(expected_bytes),
    )

    assert result.action == SourceDownloadAction.DOWNLOADED
    assert cached_path.read_bytes() == expected_bytes


def test_source_downloader_rejects_hash_mismatched_download_without_cache_file(
    tmp_path: Path,
) -> None:
    expected_bytes = b"expected official source bytes"
    corrupt_bytes = b"not the official document"
    document = _document(expected_bytes=expected_bytes)
    manifest = SourceManifest(documents=(document,))

    [result] = download_manifest_sources(
        manifest,
        repo_root=tmp_path,
        fetch_to_path=_fetcher_that_writes(corrupt_bytes),
    )

    cached_path = tmp_path / document.cache_path
    assert result.action == SourceDownloadAction.DOWNLOAD_HASH_MISMATCH
    assert result.actual_sha256 == sha256(corrupt_bytes).hexdigest()
    assert not cached_path.exists()
    assert not cached_path.with_suffix(".pdf.part").exists()


def test_source_downloader_preserves_existing_cache_on_hash_mismatched_download(
    tmp_path: Path,
) -> None:
    expected_bytes = b"expected official source bytes"
    existing_bytes = b"manually cached but stale"
    corrupt_bytes = b"wrong network response"
    document = _document(expected_bytes=expected_bytes)
    manifest = SourceManifest(documents=(document,))
    cached_path = tmp_path / document.cache_path
    cached_path.parent.mkdir(parents=True)
    cached_path.write_bytes(existing_bytes)

    [result] = download_manifest_sources(
        manifest,
        repo_root=tmp_path,
        fetch_to_path=_fetcher_that_writes(corrupt_bytes),
    )

    assert result.action == SourceDownloadAction.DOWNLOAD_HASH_MISMATCH
    assert cached_path.read_bytes() == existing_bytes
    assert not cached_path.with_suffix(".pdf.part").exists()


def test_source_downloader_rejects_unknown_document_filter(tmp_path: Path) -> None:
    manifest = SourceManifest(documents=(_document(expected_bytes=b"official"),))

    with pytest.raises(ValueError, match="unknown source document id"):
        download_manifest_sources(
            manifest,
            repo_root=tmp_path,
            document_ids={"missing-document"},
            fetch_to_path=_fetcher_that_writes(b"official"),
        )


def test_source_downloader_removes_partial_file_when_fetcher_fails(tmp_path: Path) -> None:
    document = _document(expected_bytes=b"official")
    manifest = SourceManifest(documents=(document,))

    def failing_fetcher(_url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"partial bytes")
        raise RuntimeError("network failed")

    with pytest.raises(RuntimeError, match="network failed"):
        download_manifest_sources(
            manifest,
            repo_root=tmp_path,
            fetch_to_path=failing_fetcher,
        )

    cached_path = tmp_path / document.cache_path
    assert not cached_path.exists()
    assert not cached_path.with_suffix(".pdf.part").exists()
