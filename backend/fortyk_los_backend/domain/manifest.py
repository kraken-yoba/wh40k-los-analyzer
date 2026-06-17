import re
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator, model_validator

APPROVED_SOURCE_HOST = "assets.warhammer-community.com"
APPROVED_CACHE_PARTS = ("data", "pdfs")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


class SourceKind(StrEnum):
    TERRAIN_LAYOUTS = "terrain_layouts"
    EVENT_COMPANION = "event_companion"
    RULES = "rules"


class CacheStatus(StrEnum):
    MISSING = "missing"
    HASH_MATCH = "hash_match"
    HASH_MISMATCH = "hash_mismatch"


class SourceCacheStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    status: CacheStatus
    cache_path: Path
    expected_sha256: str
    actual_sha256: str | None = None

    @field_serializer("cache_path")
    def serialize_cache_path(self, cache_path: Path) -> str:
        return cache_path.as_posix()


class SourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    kind: SourceKind
    url: str
    expected_sha256: str
    cache_path: Path
    redistribution: Literal["do-not-commit"]

    @field_validator("url")
    @classmethod
    def validate_official_source_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.netloc != APPROVED_SOURCE_HOST or not parsed.path:
            raise ValueError("url must be an official Warhammer Community asset URL")
        return value

    @field_validator("expected_sha256")
    @classmethod
    def validate_expected_sha256(cls, value: str) -> str:
        if not SHA256_RE.fullmatch(value):
            raise ValueError("expected_sha256 must be 64 lowercase hex characters")
        return value

    @field_validator("cache_path")
    @classmethod
    def validate_cache_path(cls, value: Path) -> Path:
        parts = value.parts
        unsafe_path = (
            value.is_absolute()
            or ".." in parts
            or len(parts) < 3
            or parts[:2] != APPROVED_CACHE_PARTS
        )
        if unsafe_path:
            raise ValueError("cache_path must be a relative path under data/pdfs")
        return value

    @field_serializer("cache_path")
    def serialize_cache_path(self, cache_path: Path) -> str:
        return cache_path.as_posix()


class SourceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    documents: tuple[SourceDocument, ...]

    @model_validator(mode="after")
    def validate_unique_document_ids(self) -> Self:
        seen: set[str] = set()
        for document in self.documents:
            if document.document_id in seen:
                raise ValueError(f"duplicate source document id: {document.document_id}")
            seen.add(document.document_id)
        return self

    def cache_statuses(self, *, repo_root: Path) -> list[SourceCacheStatus]:
        return [self._cache_status(document, repo_root) for document in self.documents]

    def _cache_status(self, document: SourceDocument, repo_root: Path) -> SourceCacheStatus:
        resolved_cache_path = self._resolve_cache_path(document, repo_root)
        if not resolved_cache_path.exists():
            return SourceCacheStatus(
                document_id=document.document_id,
                status=CacheStatus.MISSING,
                cache_path=document.cache_path,
                expected_sha256=document.expected_sha256,
            )

        actual_sha256 = sha256(resolved_cache_path.read_bytes()).hexdigest()
        status = (
            CacheStatus.HASH_MATCH
            if actual_sha256 == document.expected_sha256
            else CacheStatus.HASH_MISMATCH
        )
        return SourceCacheStatus(
            document_id=document.document_id,
            status=status,
            cache_path=document.cache_path,
            expected_sha256=document.expected_sha256,
            actual_sha256=actual_sha256,
        )

    def _resolve_cache_path(self, document: SourceDocument, repo_root: Path) -> Path:
        repo_root = repo_root.resolve()
        approved_root = (repo_root / "data" / "pdfs").resolve()
        resolved_cache_path = (repo_root / document.cache_path).resolve()
        resolved_cache_path.relative_to(approved_root)
        return resolved_cache_path
