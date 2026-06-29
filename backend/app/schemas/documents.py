"""Schemas for Document, Term, and ingest endpoints (#25)."""
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


# ── Parties ──


class _PartyAliasesMixin(BaseModel):
    aliases: list[str] | None = None

    @field_validator("aliases", mode="before")
    @classmethod
    def _parse_aliases(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return None
        return v


class PartyOut(_PartyAliasesMixin):
    id: int
    name: str
    role_label: str | None = None
    address: str | None = None
    contact: str | None = None
    representative: str | None = None
    tax_code: str | None = None
    is_self: bool = False
    model_config = ConfigDict(from_attributes=True)


class PartyPatchIn(BaseModel):
    name: str | None = None
    role_label: str | None = None
    address: str | None = None
    contact: str | None = None
    representative: str | None = None
    tax_code: str | None = None
    is_self: bool | None = None
    aliases: list[str] | None = None


class PartyPatchOut(_PartyAliasesMixin):
    id: int
    name: str
    role_label: str | None = None
    address: str | None = None
    contact: str | None = None
    representative: str | None = None
    tax_code: str | None = None
    is_self: bool = False
    model_config = ConfigDict(from_attributes=True)


# ── Terms ──

class TermOut(BaseModel):
    id: int
    field_name: str
    field_value: str | None = None
    confidence: float | None = None
    needs_review: bool = False
    # Stage 3 review ref-link trust gate (#217, FR-EX-05). All optional → FE
    # graceful-degrades to plain text when absent (no dead link).
    ref: str | None = None             # display label, e.g. "Điều 8" / "tr.1 §A"
    page_num: int | None = None        # 1-based page for scroll-to
    bbox: list[float] | None = None    # [x0,y0,x1,y1] normalized 0..1 for highlight
    model_config = ConfigDict(from_attributes=True)

    @field_validator("bbox", mode="before")
    @classmethod
    def _parse_bbox(cls, v: Any) -> Any:
        """bbox is stored as a JSON TEXT column — deserialize on read."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return None
        return v


class TermPatchIn(BaseModel):
    field_value: str | None = None


# ── Documents ──

class DocumentListItem(BaseModel):
    id: int
    file_name: str
    doc_type: str | None = None
    status: str
    needs_review: bool = False
    term_count: int = 0
    obligation_count: int = 0
    clause_count: int = 0
    confirmed_by_user_at: datetime | None = None   # #238 — null = "Cần xác nhận"
    created_at: datetime | None = None
    # Extraction progress (#360) — None for pre-migration / not-yet-started docs.
    processing_stage: str | None = None
    processing_progress: int | None = None
    # Obligation-centric redesign (#279, mockup #278/#283)
    primary_party: str | None = None
    next_due_date: str | None = None          # ISO date string; due_date is stored as String
    nghia_vu_count: int = 0
    quyen_loi_count: int = 0
    direction_null_count: int = 0
    may_have_unextracted_obligations: bool | None = None   # #276 column — NULL until that migration lands
    # R1 (#363): contract title/number — null for pre-migration docs (FE falls back to file_name)
    title: str | None = None
    contract_number: str | None = None
    # R6 (#369): date taxonomy — null for pre-migration docs
    signing_date: str | None = None
    commencement_date: str | None = None
    # R8 (#371): contract term + lifecycle status
    contract_term: str | None = None
    lifecycle_status: str | None = None
    # R9 (#372): definitions count
    definition_count: int = 0
    # R5 (#368): signature detection — null for pre-migration docs
    has_signature: bool | None = None
    signature_pages: list[int] | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("signature_pages", mode="before")
    @classmethod
    def _parse_signature_pages(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return None
        return v


class DocumentListOut(BaseModel):
    items: list[DocumentListItem]
    page: int
    page_size: int
    total: int


class DocumentDetailOut(BaseModel):
    id: int
    file_name: str
    doc_type: str | None = None
    status: str
    created_at: datetime | None = None
    file_url: str | None = None
    terms: list[TermOut] = []
    obligations: list[Any] = []
    clause_count: int = 0
    parties: list[PartyOut] = []
    # When status == "failed", populated from the most recent extraction_failed
    # Event's payload.reason — surfaces the exact failure path (#79 follow-up)
    # so UAT can self-diagnose without VPS access. Null for non-failed docs.
    failure_reason: str | None = None
    # Last extraction provider/model from the extraction_performed Event (#233).
    # Lets the staging smoke gate discriminate gemini_flash (anchors required, #230)
    # vs claude fallback (null anchors OK). Also feeds NĐ 13 PII-processing audit.
    # Null pre-extraction / for legacy docs.
    provider: str | None = None     # e.g. "gemini_flash" | "claude_haiku"
    model: str | None = None        # e.g. "gemini-2.5-flash"
    confirmed_by_user_at: datetime | None = None   # #238 — null = not yet user-confirmed
    # Extraction progress (#360) — None for pre-migration / not-yet-started docs.
    processing_stage: str | None = None
    processing_progress: int | None = None
    # R1 (#363): contract title/number — null for pre-migration docs
    title: str | None = None
    contract_number: str | None = None
    # R6 (#369): date taxonomy — null for pre-migration docs
    signing_date: str | None = None
    commencement_date: str | None = None
    # R8 (#371): contract term + lifecycle status
    contract_term: str | None = None
    lifecycle_status: str | None = None
    # R9 (#372): definitions count
    definition_count: int = 0
    # R5 (#368): signature detection — null for pre-migration docs
    has_signature: bool | None = None
    signature_pages: list[int] | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("signature_pages", mode="before")
    @classmethod
    def _parse_signature_pages(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return None
        return v


# ── Document-level PATCH (#363 D-07 + #371 R8) ──


class DocumentPatchIn(BaseModel):
    title: str | None = None
    contract_number: str | None = None
    lifecycle_status: str | None = None  # only "settled" | "suspended" | None (manual override)


class DocumentPatchOut(BaseModel):
    id: int
    title: str | None = None
    contract_number: str | None = None
    lifecycle_status: str | None = None
    model_config = ConfigDict(from_attributes=True)


class ConfirmDocumentOut(BaseModel):
    doc_id: int
    confirmed_at: datetime
    directions_recomputed: int
    journey_advanced: bool
    new_journey_stage: str | None = None


class RemapTypeIn(BaseModel):
    doc_type_group: str


class RemapTypeOut(BaseModel):
    success: bool = True
    fields_remapped: int
    fields_null: int
    cost_vnd: float


# ── Ingest ──

class UploadOut(BaseModel):
    doc_id: int | None = None      # None when status="quota_exceeded" (#63 bulk)
    file_name: str
    status: str


class BulkUploadOut(BaseModel):
    count: int
    documents: list[UploadOut]


# ── Clause list (#284) ──


class ClauseOut(BaseModel):
    id: int
    clause_num: str | None = None
    title: str | None = None
    content: str
    page_num: int | None = None
    # R3 (#365): hierarchy fields — null for pre-migration / flat clauses
    parent_id: int | None = None
    level: int | None = None
    clause_path: str | None = None
    model_config = ConfigDict(from_attributes=True)


class ClauseListOut(BaseModel):
    document_id: int
    clause_count: int
    page_min: int | None = None
    page_max: int | None = None
    clauses: list[ClauseOut]


class ClausePatchIn(BaseModel):
    content: str


class ClausePatchOut(BaseModel):
    id: int
    clause_num: str | None = None
    title: str | None = None
    page_num: int | None = None
    content: str
    edited_by_user: str | None = None
    edited_at: datetime | None = None
    original_content: str | None = None
    model_config = ConfigDict(from_attributes=True)


# ── Clause-scoped re-derive (#303, DEC-048 §13) ──


class ReDeriveClauseIn(BaseModel):
    clause_num: str


class ReDeriveClauseOut(BaseModel):
    ok: bool = True
    created: int
    skipped: bool
    protected_manual: int
    deleted: int
    cost_vnd: float = 0.0


# ── Re-read trigger (#324 Task 2, DEC-048 §13) ──


class ReReadIn(BaseModel):
    clause_ids: list[int] | None = None   # scope to specific clauses; None = all


class ReReadDiff(BaseModel):
    action: str                           # "add" | "update" | "remove"
    obligation_id: int | None = None      # existing obligation (for update/remove)
    field: str | None = None             # which field changed (for update)
    old_value: str | None = None
    new_value: str | None = None
    description: str | None = None
    obligation_type: str | None = None
    due_date: str | None = None
    source_clause_num: str | None = None
    protected: bool = False              # True if source='user_manual' → FE default Giữ


class ReReadOut(BaseModel):
    document_id: int
    clauses_checked: int
    diffs: list[ReReadDiff]


# ── Self-party confirmation (DEC-030, #155) ──


class SelfPartyIn(BaseModel):
    role_label: str


class SelfPartyOut(BaseModel):
    ok: bool
    updated: int


# ── Document event history (#281) ──


class EventOut(BaseModel):
    id: int
    event_type: str
    entity_type: str
    entity_id: int
    actor: str | None = None
    created_at: datetime | None = None
    payload: dict | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("payload", mode="before")
    @classmethod
    def _parse_payload(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return None
        return v


class EventListOut(BaseModel):
    document_id: int
    total: int
    limit: int
    offset: int
    items: list[EventOut]


# ── Definitions glossary (#372, R9) ──


class DefinitionOut(BaseModel):
    id: int
    term: str
    definition: str
    source_clause_num: str | None = None
    source_clause_id: int | None = None
    edited_by_user: str | None = None
    edited_at: datetime | None = None
    original_definition: str | None = None
    original_term: str | None = None
    model_config = ConfigDict(from_attributes=True)


class DefinitionListOut(BaseModel):
    document_id: int
    definition_count: int
    definitions: list[DefinitionOut]


class DefinitionPatchIn(BaseModel):
    term: str | None = None
    definition: str | None = None


class DefinitionPatchOut(BaseModel):
    id: int
    term: str
    definition: str
    edited_by_user: str | None = None
    edited_at: datetime | None = None
    original_definition: str | None = None
    original_term: str | None = None
    model_config = ConfigDict(from_attributes=True)


# ── Cross-reference resolution (#373, R10) ──


class CrossRefOut(BaseModel):
    id: int
    source_clause_id: int
    ref_text: str
    ref_type: str               # "clause" | "sub_clause" | "appendix" | "document"
    target_clause_id: int | None = None
    target_clause_path: str | None = None
    target_doc_id: int | None = None
    is_orphan: bool = False
    model_config = ConfigDict(from_attributes=True)


class CrossRefListOut(BaseModel):
    document_id: int
    total_refs: int
    resolved: int
    orphans: int
    refs: list[CrossRefOut]


class CrossRefResolveOut(BaseModel):
    document_id: int
    total_refs: int
    resolved: int
    orphans: int
