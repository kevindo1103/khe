"""Pydantic schemas for chat query endpoint (#27)."""
from pydantic import BaseModel


class ChatQueryIn(BaseModel):
    question: str


class ChatQueryOut(BaseModel):
    answer: str
    sources: list[dict]
    found: bool


class ChatStatsOut(BaseModel):
    total_queries: int
    total_cost_vnd: float
    total_input_tokens: int
    total_output_tokens: int
    total_llm_calls: int
    avg_tokens_per_query: float
