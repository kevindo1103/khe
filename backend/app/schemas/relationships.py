"""Schemas for document relationships and chain resolution (#50)."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class RelationshipOut(BaseModel):
    id: int
    from_doc_id: int
    to_doc_id: int | None = None
    unresolved_ref: str | None = None
    relationship_type: Literal["amends", "references_framework"]
    status: Literal["pending", "confirmed"]
    confirmed_by_sme: bool
    confidence: float | None = None
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class RelationshipListOut(BaseModel):
    items: list[RelationshipOut]


class RelationshipConfirmIn(BaseModel):
    confirmed_by_sme: bool


class RelationshipConfirmOut(BaseModel):
    ok: bool
    relationship: RelationshipOut
    chain: dict
