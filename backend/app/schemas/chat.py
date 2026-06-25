"""Pydantic schemas for chat query endpoint (#27)."""
from pydantic import BaseModel


class ChatQueryIn(BaseModel):
    question: str
    # DEC-031 v2 (#201): per-device/tab UUID from FE localStorage. Optional —
    # absent → stateless (cold) chat, fully backward compatible.
    session_id: str | None = None


class ChatQueryOut(BaseModel):
    answer: str
    sources: list[dict]
    found: bool
    # DEC-031 v2 (#201): working-set chip label (null when cold/over-cap) + the
    # echoed session_id so the FE can persist it.
    context_label: str | None = None
    session_id: str | None = None
    # #199 aggregate vs retrieval (FR-CQ, Stage 6). Defaults keep every existing
    # retrieval response byte-compatible.
    #   intent="aggregate" → summary/source populated; found ALWAYS true (even
    #   total=0 → "Bạn không có nghĩa vụ X", never D-08).
    #   tenant_empty=true → tenant has 0 documents (FE cold-start nudge, distinct
    #   from aggregate-zero).
    intent: str = "retrieval"
    summary: dict | None = None
    source: dict | None = None
    tenant_empty: bool = False


class ChatSessionResetIn(BaseModel):
    # POST body (not a query param) so the session_id UUID never lands in nginx
    # access logs as a device fingerprint (#203 M1, NĐ 13).
    session_id: str


class ChatStatsOut(BaseModel):
    total_queries: int
    total_cost_vnd: float
    total_input_tokens: int
    total_output_tokens: int
    total_llm_calls: int
    avg_tokens_per_query: float
