import json
from hashlib import sha256
from typing import Any

from fortyk_los_backend.domain.models import CanonicalLayout

SORTABLE_ID_KEYS = ("feature_id", "blocker_id", "zone_id", "document_id", "code")


def canonical_json_bytes(layout: CanonicalLayout) -> bytes:
    payload = _normalize_for_canonical_json(layout.model_dump(mode="json"))
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )


def stable_layout_hash(layout: CanonicalLayout) -> str:
    return sha256(canonical_json_bytes(layout)).hexdigest()


def _normalize_for_canonical_json(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {key: _normalize_for_canonical_json(item) for key, item in value.items()}
    if isinstance(value, list):
        normalized_items = [_normalize_for_canonical_json(item) for item in value]
        sort_key = _sortable_id_key(normalized_items)
        if sort_key is not None:
            return sorted(normalized_items, key=lambda item: str(item[sort_key]))
        return normalized_items
    return value


def _sortable_id_key(items: list[Any]) -> str | None:
    if not items or not all(isinstance(item, dict) for item in items):
        return None
    for key in SORTABLE_ID_KEYS:
        if all(key in item for item in items):
            return key
    return None
