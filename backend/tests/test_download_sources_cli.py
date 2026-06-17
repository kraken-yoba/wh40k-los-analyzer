from hashlib import sha256
from pathlib import Path
from types import TracebackType
from typing import Self

import pytest
from fortyk_los_backend import download_sources


def _manifest_json(*, payload: bytes, cache_name: str = "core_rules.pdf") -> str:
    return f"""
{{
  "documents": [
    {{
      "cache_path": "data/pdfs/{cache_name}",
      "document_id": "core-rules-2026-06-01",
      "expected_sha256": "{sha256(payload).hexdigest()}",
      "kind": "rules",
      "redistribution": "do-not-commit",
      "url": "https://assets.warhammer-community.com/example-rules.pdf"
    }}
  ]
}}
"""


def test_download_sources_cli_downloads_manifest_document(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = b"official rules pdf bytes"
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text(_manifest_json(payload=payload), encoding="utf-8")

    def fetcher(_url: str, destination: Path) -> None:
        destination.write_bytes(payload)

    monkeypatch.setattr(download_sources, "fetch_url_to_path", fetcher)

    exit_code = download_sources.main(
        [
            "--repo-root",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "data" / "pdfs" / "core_rules.pdf").read_bytes() == payload
    assert "downloaded core-rules-2026-06-01" in capsys.readouterr().out


def test_download_sources_cli_returns_failure_for_hash_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text(_manifest_json(payload=b"expected bytes"), encoding="utf-8")

    def fetcher(_url: str, destination: Path) -> None:
        destination.write_bytes(b"corrupt bytes")

    monkeypatch.setattr(download_sources, "fetch_url_to_path", fetcher)

    exit_code = download_sources.main(
        [
            "--repo-root",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
        ]
    )

    assert exit_code == 1
    assert not (tmp_path / "data" / "pdfs" / "core_rules.pdf").exists()
    assert "download_hash_mismatch core-rules-2026-06-01" in capsys.readouterr().out


def test_download_sources_cli_filters_document_ids(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b"official rules pdf bytes"
    other_payload = b"official event pdf bytes"
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text(
        f"""
{{
  "documents": [
    {{
      "cache_path": "data/pdfs/core_rules.pdf",
      "document_id": "core-rules-2026-06-01",
      "expected_sha256": "{sha256(payload).hexdigest()}",
      "kind": "rules",
      "redistribution": "do-not-commit",
      "url": "https://assets.warhammer-community.com/example-rules.pdf"
    }},
    {{
      "cache_path": "data/pdfs/event_companion.pdf",
      "document_id": "event-companion-2026-06-12",
      "expected_sha256": "{sha256(other_payload).hexdigest()}",
      "kind": "event_companion",
      "redistribution": "do-not-commit",
      "url": "https://assets.warhammer-community.com/example-event.pdf"
    }}
  ]
}}
""",
        encoding="utf-8",
    )
    fetched_urls: list[str] = []

    def fetcher(url: str, destination: Path) -> None:
        fetched_urls.append(url)
        destination.write_bytes(other_payload)

    monkeypatch.setattr(download_sources, "fetch_url_to_path", fetcher)

    exit_code = download_sources.main(
        [
            "--repo-root",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
            "--document-id",
            "event-companion-2026-06-12",
        ]
    )

    assert exit_code == 0
    assert fetched_urls == ["https://assets.warhammer-community.com/example-event.pdf"]
    assert not (tmp_path / "data" / "pdfs" / "core_rules.pdf").exists()
    assert (tmp_path / "data" / "pdfs" / "event_companion.pdf").read_bytes() == other_payload


def test_download_sources_cli_reports_unknown_document_without_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text(_manifest_json(payload=b"expected bytes"), encoding="utf-8")

    exit_code = download_sources.main(
        [
            "--repo-root",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
            "--document-id",
            "missing-document",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "unknown source document id: missing-document" in captured.err
    assert "Traceback" not in captured.err


def test_download_sources_cli_reports_missing_manifest_without_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_manifest = tmp_path / "missing_manifest.json"

    exit_code = download_sources.main(
        [
            "--repo-root",
            str(tmp_path),
            "--manifest",
            str(missing_manifest),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_download_sources_cli_reports_invalid_manifest_without_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")

    exit_code = download_sources.main(
        [
            "--repo-root",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_fetch_url_to_path_rejects_untrusted_redirect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _FakeResponse(
        final_url="https://example.com/redirected.pdf",
        chunks=(b"redirected bytes",),
    )
    monkeypatch.setattr(download_sources, "urlopen", lambda _request, timeout: response)
    destination = tmp_path / "download.part"

    with pytest.raises(download_sources.SourceDownloadError, match="untrusted redirect"):
        download_sources.fetch_url_to_path(
            "https://assets.warhammer-community.com/example-rules.pdf",
            destination,
            max_bytes=100,
        )

    assert not destination.exists()


def test_fetch_url_to_path_enforces_max_source_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _FakeResponse(
        final_url="https://assets.warhammer-community.com/example-rules.pdf",
        chunks=(b"1234", b"56"),
    )
    monkeypatch.setattr(download_sources, "urlopen", lambda _request, timeout: response)
    destination = tmp_path / "download.part"

    with pytest.raises(download_sources.SourceDownloadError, match="exceeds maximum"):
        download_sources.fetch_url_to_path(
            "https://assets.warhammer-community.com/example-rules.pdf",
            destination,
            max_bytes=5,
        )

    assert not destination.exists()


def test_fetch_url_to_path_streams_to_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _FakeResponse(
        final_url="https://assets.warhammer-community.com/example-rules.pdf",
        chunks=(b"abc", b"def"),
    )
    monkeypatch.setattr(download_sources, "urlopen", lambda _request, timeout: response)
    destination = tmp_path / "download.part"

    download_sources.fetch_url_to_path(
        "https://assets.warhammer-community.com/example-rules.pdf",
        destination,
        max_bytes=10,
    )

    assert destination.read_bytes() == b"abcdef"


class _FakeResponse:
    def __init__(self, *, final_url: str, chunks: tuple[bytes, ...]) -> None:
        self._final_url = final_url
        self._chunks = list(chunks)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc, traceback

    def geturl(self) -> str:
        return self._final_url

    def read(self, _size: int = -1) -> bytes:
        if not self._chunks:
            return b""
        return self._chunks.pop(0)
