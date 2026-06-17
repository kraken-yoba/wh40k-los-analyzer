import argparse
import sys
from pathlib import Path
from typing import cast
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pydantic import ValidationError

from fortyk_los_backend.domain.manifest import APPROVED_SOURCE_HOST, SourceManifest
from fortyk_los_backend.domain.source_cache import (
    SourceDownloadAction,
    SourceDownloadResult,
    download_manifest_sources,
)

MAX_SOURCE_BYTES = 100 * 1024 * 1024
STREAM_CHUNK_BYTES = 1024 * 1024


class SourceDownloadError(RuntimeError):
    pass


def fetch_url_to_path(
    url: str,
    destination: Path,
    *,
    max_bytes: int = MAX_SOURCE_BYTES,
) -> None:
    request = Request(
        url,
        headers={"User-Agent": "fortyk-los-analyzer/0.1 (+local source cache)"},
    )
    try:
        with urlopen(request, timeout=120) as response:
            final_url = cast(str, response.geturl())
            if not _is_approved_source_url(final_url):
                raise SourceDownloadError(f"untrusted redirect target: {final_url}")

            bytes_written = 0
            with destination.open("wb") as output:
                while True:
                    chunk = cast(bytes, response.read(STREAM_CHUNK_BYTES))
                    if not chunk:
                        break
                    bytes_written += len(chunk)
                    if bytes_written > max_bytes:
                        raise SourceDownloadError(
                            f"download exceeds maximum size of {max_bytes} bytes: {url}"
                        )
                    output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download official Warhammer source PDFs into the local hash-pinned cache.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing fixtures/source_manifest.official.json.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Source manifest path. Defaults to fixtures/source_manifest.official.json.",
    )
    parser.add_argument(
        "--document-id",
        action="append",
        default=[],
        help="Optional source document id to download. Repeat to download multiple documents.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest or repo_root / "fixtures" / "source_manifest.official.json"
    document_ids = set(args.document_id) if args.document_id else None
    try:
        manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        results = download_manifest_sources(
            manifest,
            repo_root=repo_root,
            fetch_to_path=fetch_url_to_path,
            document_ids=document_ids,
        )
    except (OSError, SourceDownloadError, ValidationError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for result in results:
        print(_format_result(result))
    return (
        1
        if any(result.action == SourceDownloadAction.DOWNLOAD_HASH_MISMATCH for result in results)
        else 0
    )


def _format_result(result: SourceDownloadResult) -> str:
    actual = f" actual={result.actual_sha256}" if result.actual_sha256 is not None else ""
    return (
        f"{result.action.value} {result.document_id} "
        f"path={result.cache_path.as_posix()} expected={result.expected_sha256}{actual}"
    )


def _is_approved_source_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.netloc == APPROVED_SOURCE_HOST and bool(parsed.path)


if __name__ == "__main__":
    raise SystemExit(main())
