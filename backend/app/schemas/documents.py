"""Schemas for Document, Term, and ingest endpoints (#25)."""
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


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
    # Obligation-centric redesign (#279, mockup #278/#283)
    primary_party: str | None = None
    next_due_date: str | None = None          # ISO date string; due_date is stored as String
    nghia_vu_count: int = 0
    quyen_loi_count: int = 0
    direction_null_count: int = 0
    may_have_unextracted_obligations: bool | None = None   # #276 column — NULL until that migration lands
    model_config = ConfigDict(from_attributes=True)


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
    parties: list[dict] = []
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
    clause_num: str | None = None
    title: str | None = None
    content: str
    page_num: int | None = None
    model_config = ConfigDict(from_attributes=True)


class ClauseListOut(BaseModel):
    document_id: int
    clause_count: int
    page_min: int | None = None
    page_max: int | None = None
    clauses: list[ClauseOut]


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


# ── Self-party confirmation (DEC-030, #155) ──


class SelfPartyIn(BaseModel):
    role_label: str


class SelfPartyOut(BaseModel):
    ok: bool
    updated: int
