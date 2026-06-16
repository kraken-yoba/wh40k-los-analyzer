from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class SourceKind(StrEnum):
    TERRAIN_LAYOUTS = "terrain_layouts"
    RULES = "rules"


class CacheStatus(StrEnum):
    MISSING = "missing"
    HASH_MATCH = "hash_match"
    HASH_MISMATCH = "hash_mismatch"


class SourceCacheStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    status: CacheStatus
    cache_path: Path
    expected_sha256: str
    actual_sha256: str | None = None


class SourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    kind: SourceKind
    url: str
    expected_sha256: str
    cache_path: Path
    redistribution: str


class SourceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documents: list[SourceDocument]

    def cache_statuses(self) -> list[SourceCacheStatus]:
        return [self._cache_status(document) for document in self.documents]

    def _cache_status(self, document: SourceDocument) -> SourceCacheStatus:
        if not document.cache_path.exists():
            return SourceCacheStatus(
                document_id=document.document_id,
                status=CacheStatus.MISSING,
                cache_path=document.cache_path,
                expected_sha256=document.expected_sha256,
            )

        actual_sha256 = sha256(document.cache_path.read_bytes()).hexdigest()
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
