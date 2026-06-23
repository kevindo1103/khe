"""Pydantic schemas for Obligation endpoints (#26 PR-A)."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


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
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class ObligationListOut(BaseModel):
    items: list[ObligationOut]
    page: int
    page_size: int
    total: int


class ObligationPatchIn(BaseModel):
    status: str


class SnoozeOut(BaseModel):
    ok: bool = True
    snoozed_until: datetime


class ObligationPatchOut(BaseModel):
    ok: bool
    obligation: ObligationOut
    activated_count: int = 0
