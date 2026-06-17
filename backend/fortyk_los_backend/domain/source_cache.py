from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from fortyk_los_backend.domain.manifest import CacheStatus, SourceManifest


class SourceDownloadAction(StrEnum):
    SKIPPED_HASH_MATCH = "skipped_hash_match"
    DOWNLOADED = "downloaded"
    DOWNLOAD_HASH_MISMATCH = "download_hash_mismatch"


@dataclass(frozen=True)
class SourceDownloadResult:
    document_id: str
    action: SourceDownloadAction
    cache_path: Path
    expected_sha256: str
    actual_sha256: str | None


FetchToPath = Callable[[str, Path], None]


def download_manifest_sources(
    manifest: SourceManifest,
    *,
    repo_root: Path,
    fetch_to_path: FetchToPath,
    document_ids: set[str] | None = None,
) -> tuple[SourceDownloadResult, ...]:
    requested_document_ids = set(document_ids) if document_ids is not None else None
    documents = manifest.documents
    if requested_document_ids is not None:
        known_document_ids = {document.document_id for document in documents}
        unknown_document_ids = requested_document_ids - known_document_ids
        if unknown_document_ids:
            unknown = ", ".join(sorted(unknown_document_ids))
            raise ValueError(f"unknown source document id: {unknown}")
        documents = tuple(
            document for document in documents if document.document_id in requested_document_ids
        )

    statuses_by_id = {
        status.document_id: status for status in manifest.cache_statuses(repo_root=repo_root)
    }
    results: list[SourceDownloadResult] = []
    for document in documents:
        status = statuses_by_id[document.document_id]
        if status.status == CacheStatus.HASH_MATCH:
            results.append(
                SourceDownloadResult(
                    document_id=document.document_id,
                    action=SourceDownloadAction.SKIPPED_HASH_MATCH,
                    cache_path=document.cache_path,
                    expected_sha256=document.expected_sha256,
                    actual_sha256=status.actual_sha256,
                )
            )
            continue

        resolved_cache_path = _resolve_cache_path(repo_root, document.cache_path)
        resolved_cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = _temporary_cache_path(repo_root, document.cache_path)
        temporary_path.unlink(missing_ok=True)
        try:
            fetch_to_path(document.url, temporary_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        actual_sha256 = _hash_file(temporary_path)
        if actual_sha256 != document.expected_sha256:
            temporary_path.unlink(missing_ok=True)
            results.append(
                SourceDownloadResult(
                    document_id=document.document_id,
                    action=SourceDownloadAction.DOWNLOAD_HASH_MISMATCH,
                    cache_path=document.cache_path,
                    expected_sha256=document.expected_sha256,
                    actual_sha256=actual_sha256,
                )
            )
            continue

        temporary_path.replace(resolved_cache_path)
        results.append(
            SourceDownloadResult(
                document_id=document.document_id,
                action=SourceDownloadAction.DOWNLOADED,
                cache_path=document.cache_path,
                expected_sha256=document.expected_sha256,
                actual_sha256=actual_sha256,
            )
        )
    return tuple(results)


def _resolve_cache_path(repo_root: Path, cache_path: Path) -> Path:
    repo_root = repo_root.resolve()
    approved_root = (repo_root / "data" / "pdfs").resolve()
    resolved_cache_path = (repo_root / cache_path).resolve()
    resolved_cache_path.relative_to(approved_root)
    return resolved_cache_path


def _temporary_cache_path(repo_root: Path, cache_path: Path) -> Path:
    resolved_cache_path = _resolve_cache_path(repo_root, cache_path)
    return resolved_cache_path.with_suffix(f"{resolved_cache_path.suffix}.part")


def _hash_file(path: Path) -> str:
    hasher = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
