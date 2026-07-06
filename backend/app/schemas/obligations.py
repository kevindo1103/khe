"""Pydantic schemas for Obligation endpoints (#26 PR-A)."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator
import json


class ObligationOut(BaseModel):
    id: int
    document_id: int
    description: str
    obligation_type: str          # category: payment/expiration/renewal/...
    recurrence: str               # cadence: once/open_ended_review
    direction: str | None = None  # nghĩa_vụ/quyền_lợi/null
    obligor: str | None = None
    due_date: str | None = None
    status: str
    remind_before_days: int
    source_doc_chain: str | None = None
    resolution_method: str | None = None
    # ── DEC-030 Phase 2: series + event-chain ──
    milestone_series_id: str | None = None
    milestone_index: int | None = None
    milestone_total: int | None = None
    milestone_trigger: str | None = None
    trigger_condition: str | None = None
    trigger_delay_days: int | None = None
    trigger_obligation_id: int | None = None
    amount_raw: str | None = None
    snoozed_until: datetime | None = None   # #214 — reminder suppressed until this time
    # Fulfillment capture (#302, DEC-048 G2/P3)
    fulfilled_at: datetime | None = None
    fulfilled_by: str | None = None
    evidence_doc_ids: list[int] | None = None   # deserialized from JSON Text column
    # Clause provenance (#303, DEC-048 §13)
    source_clause_num: str | None = None
    derived_from: str | None = None
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("evidence_doc_ids", mode="before")
    @classmethod
    def _parse_evidence_doc_ids(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return None
        return v


class ObligationListOut(BaseModel):
    items: list[ObligationOut]
    page: int
    page_size: int
    total: int


class ObligationPatchIn(BaseModel):
    status: str
    fulfilled_at: datetime | None = None        # required when status="done"
    fulfilled_by: str | None = None             # actor attribution (P3)
    evidence_doc_ids: list[int] | None = None   # optional evidence doc refs


class SnoozeOut(BaseModel):
    ok: bool = True
    snoozed_until: datetime


class ObligationSummaryOut(BaseModel):
    """Server-side obligation aggregate for the Dashboard (#199 follow-up) —
    canonical group labels so the FE stops deriving direction counts client-side."""
    total: int
    group_by: str
    groups: list[dict]              # [{key, label, count, nearest?}]
    status_breakdown: dict          # {waiting_trigger, overdue, due_soon}
    source: dict                    # {obligation_count, doc_count, label}


class ObligationPatchOut(BaseModel):
    ok: bool
    obligation: ObligationOut
    activated_count: int = 0


# ── Bulk complete (#471) ──

class BulkCompleteIn(BaseModel):
    ids: list[int]
    status: str                          # must be "done" or "cancelled"
    fulfilled_at: datetime | None = None # required when status="done"
    fulfilled_by: str | None = None


class BulkCompleteItemOut(BaseModel):
    id: int
    ok: bool
    error: str | None = None             # reason if not ok (not found, wrong tenant, etc.)


class BulkCompleteOut(BaseModel):
    updated: int
    skipped: int
    items: list[BulkCompleteItemOut]
