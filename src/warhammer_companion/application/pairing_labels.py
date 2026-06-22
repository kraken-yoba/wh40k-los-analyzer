from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from warhammer_companion.application.toolkit import BlockReason
from warhammer_companion.domain.matchups import PairingListEntry

LabelInput = str | Sequence[str]

MAX_PAIRING_LABELS_PER_SIDE = 8
MAX_PAIRING_LABEL_LENGTH = 80


@dataclass(frozen=True, slots=True)
class PairingLabelNormalizationResult:
    entries: tuple[PairingListEntry, ...]
    block_reasons: tuple[BlockReason, ...]


def normalize_pairing_list_entries(
    side: str,
    labels: LabelInput,
) -> PairingLabelNormalizationResult:
    normalized = _normalized_labels(labels)
    reasons: list[BlockReason] = []
    if not normalized:
        reasons.append(
            BlockReason(
                reason_id=f"missing-{side}-lists",
                detail=f"Enter at least one {side} list label.",
            )
        )
    if len(normalized) > MAX_PAIRING_LABELS_PER_SIDE:
        reasons.append(
            BlockReason(
                reason_id=f"too-many-{side}-lists",
                detail=f"Enter no more than {MAX_PAIRING_LABELS_PER_SIDE} {side} list labels.",
            )
        )
    if any(len(label) > MAX_PAIRING_LABEL_LENGTH for label in normalized):
        reasons.append(
            BlockReason(
                reason_id=f"{side}-list-label-too-long",
                detail=(
                    f"{side.title()} list labels must be "
                    f"{MAX_PAIRING_LABEL_LENGTH} characters or less."
                ),
            )
        )
    seen: set[str] = set()
    duplicate_found = False
    for label in normalized:
        key = label.casefold()
        if key in seen:
            duplicate_found = True
            break
        seen.add(key)
    if duplicate_found:
        reasons.append(
            BlockReason(
                reason_id=f"duplicate-{side}-list-label",
                detail=f"{side.title()} list labels must be unique after normalization.",
            )
        )
    entries = tuple(
        PairingListEntry(list_id=f"{side}-{index}", label=label)
        for index, label in enumerate(normalized, start=1)
    )
    return PairingLabelNormalizationResult(entries=entries, block_reasons=tuple(reasons))


def _normalized_labels(labels: LabelInput) -> tuple[str, ...]:
    fragments: list[str] = []
    for raw_label in _raw_label_items(labels):
        normalized_text = _normalize_raw_label_text(raw_label)
        fragments.extend(re.split(r"[,\n]+", normalized_text))
    return tuple(
        label for fragment in fragments if (label := re.sub(r"\s+", " ", fragment).strip())
    )


def _raw_label_items(labels: LabelInput) -> tuple[str, ...]:
    if isinstance(labels, str):
        return (labels,)
    return tuple(str(label) for label in labels)


def _normalize_raw_label_text(raw_label: str) -> str:
    normalized = raw_label.replace("\r\n", "\n").replace("\r", "\n")
    chars: list[str] = []
    for char in normalized:
        if char in {",", "\n"}:
            chars.append(char)
        elif char.isspace():
            chars.append(" ")
        elif char.isprintable():
            chars.append(char)
    return "".join(chars)
