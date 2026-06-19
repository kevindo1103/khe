"""Schemas for Document, Term, and ingest endpoints (#25)."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


# ── Terms ──

class TermOut(BaseModel):
    id: int
    field_name: str
    field_value: str | None = None
    confidence: float | None = None
    needs_review: bool = False
    model_config = ConfigDict(from_attributes=True)


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
    created_at: datetime | None = None
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
    # When status == "failed", populated from the most recent extraction_failed
    # Event's payload.reason — surfaces the exact failure path (#79 follow-up)
    # so UAT can self-diagnose without VPS access. Null for non-failed docs.
    failure_reason: str | None = None
    model_config = ConfigDict(from_attributes=True)


# ── Ingest ──

class UploadOut(BaseModel):
    doc_id: int
    file_name: str
    status: str


class BulkUploadOut(BaseModel):
    count: int
    documents: list[UploadOut]
