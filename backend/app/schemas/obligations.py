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
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class ObligationListOut(BaseModel):
    items: list[ObligationOut]
    page: int
    page_size: int
    total: int


class ObligationPatchIn(BaseModel):
    status: str


class ObligationPatchOut(BaseModel):
    ok: bool
    obligation: ObligationOut
