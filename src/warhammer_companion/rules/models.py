from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from warhammer_companion.rules.sources import SourceRef


class ReadinessState(StrEnum):
    TRUSTED = "trusted"
    ESTIMATED = "estimated"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


class ValidationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationRecord(BaseModel):
    code: str
    severity: ValidationSeverity
    message: str
    source_ref: SourceRef | None = None


class RuleSourceDocument(BaseModel):
    source_ref: SourceRef
    page_count: int | None = Field(default=None, ge=1)


class RuleSection(BaseModel):
    source_document_id: str
    section_id: str
    section_label: str
    page_number: int = Field(ge=1)
    terms: tuple[str, ...] = Field(default_factory=tuple)


class GlossaryTerm(BaseModel):
    term_id: str
    display_label: str
    source_section_ids: tuple[str, ...] = Field(default_factory=tuple)
    aliases: tuple[str, ...] = Field(default_factory=tuple)


class ConceptMapping(BaseModel):
    concept_id: str
    internal_name: str
    display_label: str
    source_section_ids: tuple[str, ...] = Field(default_factory=tuple)
    related_terms: tuple[str, ...] = Field(default_factory=tuple)
    mechanic_tags: tuple[str, ...] = Field(default_factory=tuple)


class CanonicalRulesPack(BaseModel):
    rules_pack_id: str
    edition_id: str
    source_documents: tuple[RuleSourceDocument, ...]
    source_sections: tuple[RuleSection, ...]
    glossary_terms: tuple[GlossaryTerm, ...] = Field(default_factory=tuple)
    concept_mappings: tuple[ConceptMapping, ...]
    readiness: ReadinessState
    validation_records: tuple[ValidationRecord, ...] = Field(default_factory=tuple)
