"""Pydantic schemas for Obligation endpoints (#26 PR-A)."""
from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
import json


OBLIGATION_SOURCE_VALUES = {"ai_extracted", "ai_re_derived", "user_manual", "rule_pack"}


class ObligationOut(BaseModel):
    id: int
    document_id: int | None = None  # NULL for manual/rule-pack obligations without a contract (#494)
    description: str
    obligation_type: str          # category: payment/expiration/renewal/.../standing/reporting
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
    # Provenance (#494)
    source: str | None = None
    source_rule_id: str | None = None
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


class ObligationCreateIn(BaseModel):
    """Request body for POST /obligations and embedded POST /documents/ obligations (#494)."""

    description: str
    obligation_type: str = "other"
    direction: str | None = None
    due_date: str | None = None
    recurrence: str | None = "once"
    obligor: str | None = None
    remind_before_days: int = 7
    document_id: int | None = None
    source: str = "user_manual"
    source_rule_id: str | None = None
    milestone_trigger: str = "date"
    trigger_condition: str | None = None
    trigger_delay_days: int | None = None
    # index into the obligations list of the same manual-document request (0-based).
    trigger_obligation_ref: int | None = None

    @field_validator("source")
    @classmethod
    def _check_source(cls, v: str) -> str:
        if v not in OBLIGATION_SOURCE_VALUES:
            raise ValueError(f"source must be one of {sorted(OBLIGATION_SOURCE_VALUES)}")
        return v

    @field_validator("milestone_trigger")
    @classmethod
    def _check_milestone_trigger(cls, v: str) -> str:
        if v not in ("date", "event"):
            raise ValueError("milestone_trigger must be 'date' or 'event'")
        return v

    @field_validator("direction")
    @classmethod
    def _check_direction(cls, v: str | None) -> str | None:
        if v is not None and v not in ("nghĩa_vụ", "quyền_lợi"):
            raise ValueError("direction must be 'nghĩa_vụ' or 'quyền_lợi'")
        return v

    @model_validator(mode="after")
    def _check_date_when_date_trigger(self):
        if self.milestone_trigger == "date" and self.due_date is None:
            raise ValueError("due_date bắt buộc khi milestone_trigger là 'date'")
        return self


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


class TriggerConfirmIn(BaseModel):
    event_date: date | None = None   # defaults to today if omitted


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
