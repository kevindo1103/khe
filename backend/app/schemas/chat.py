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


class ChatStatsOut(BaseModel):
    total_queries: int
    total_cost_vnd: float
    total_input_tokens: int
    total_output_tokens: int
    total_llm_calls: int
    avg_tokens_per_query: float
