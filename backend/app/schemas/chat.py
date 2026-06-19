"""Pydantic schemas for chat query endpoint (#27)."""
from pydantic import BaseModel


class ChatQueryIn(BaseModel):
    question: str


class ChatQueryOut(BaseModel):
    answer: str
    sources: list[dict]
    found: bool
