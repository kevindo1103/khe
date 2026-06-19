"""Document relationship endpoints (DEC-019/020/021, #50 PR-B).

Nested under /documents as required by frozen contract #1.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import get_current_user
from app.models.master import TenantUser
from app.models.tenant import Document, Event
from app.schemas.relationships import (
    RelationshipConfirmIn,
    RelationshipConfirmOut,
    RelationshipListOut,
    RelationshipOut,
)
from app.services.relationships import (
    confirm_relationship,
    get_relationships_for_document,
    suggest_relationships,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def _log_event(
    db: Session,
    tenant_id: str,
    event_type: str,
    entity_type: str,
    entity_id: int,
    actor: str,
    payload: dict | None = None,
) -> None:
    event = Event(
        tenant_id=tenant_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        payload=json.dumps(payload) if payload else None,
    )
    db.add(event)
    db.commit()


@router.get("/{doc_id}/relationships", response_model=RelationshipListOut)
def list_relationships(
    doc_id: int,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List relationships for a document (as source or target)."""
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.tenant_id == user.tenant_id)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    rels = get_relationships_for_document(db, user.tenant_id, doc_id)
    return RelationshipListOut(items=[RelationshipOut.model_validate(r) for r in rels])


@router.patch("/{doc_id}/relationships/{rel_id}", response_model=RelationshipConfirmOut)
def patch_relationship(
    doc_id: int,
    rel_id: int,
    payload: RelationshipConfirmIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SME confirms a relationship. Only confirmation acts on data (D-02)."""
    if not payload.confirmed_by_sme:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only confirmed_by_sme=true is supported.",
        )

    rel = confirm_relationship(db, user.tenant_id, doc_id, rel_id, actor=user.username)
    if rel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found")

    _log_event(
        db,
        user.tenant_id,
        event_type="updated",
        entity_type="document_relationship",
        entity_id=rel.id,
        actor=user.username,
        payload={"status": rel.status, "confirmed_by_sme": rel.confirmed_by_sme},
    )

    # Re-run suggestion engine to catch any newly linkable matches (optional but useful).
    suggest_relationships(db, user.tenant_id, rel.from_doc_id)

    return RelationshipConfirmOut(
        ok=True,
        relationship=RelationshipOut.model_validate(rel),
        chain={
            "doc_ids": [rel.from_doc_id, rel.to_doc_id] if rel.to_doc_id else [rel.from_doc_id],
        },
    )
