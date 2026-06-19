"""Obligation endpoints (#26 PR-A).

Frozen contract #1 paths:
  /obligations              (list)
  /obligations/{id}         (update status)
"""
import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import get_current_user
from app.models.master import TenantUser
from app.models.tenant import Document, Event, Obligation
from app.schemas.obligations import (
    ObligationListOut,
    ObligationOut,
    ObligationPatchIn,
    ObligationPatchOut,
)

router = APIRouter(prefix="/obligations", tags=["obligations"])


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


@router.get("/", response_model=ObligationListOut)
def list_obligations(
    due_within: int | None = Query(None, ge=0),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List obligations for the tenant.

    - due_within=N filters to obligations whose due_date is within the next N days.
    - status filters by exact status string.
    """
    query = db.query(Obligation).filter(Obligation.tenant_id == user.tenant_id)

    if status:
        query = query.filter(Obligation.status == status)

    if due_within is not None:
        today = date.today()
        window_end = today + timedelta(days=due_within)
        query = query.filter(
            Obligation.due_date.isnot(None),
            Obligation.due_date >= today.isoformat(),
            Obligation.due_date <= window_end.isoformat(),
        )

    total = query.count()
    rows = (
        query.order_by(Obligation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ObligationListOut(
        items=[ObligationOut.model_validate(ob) for ob in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.patch("/{obligation_id}", response_model=ObligationPatchOut)
def patch_obligation(
    obligation_id: int,
    payload: ObligationPatchIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an obligation's status. SME/status-machine edits only (D-02)."""
    allowed = {"pending", "done", "cancelled"}
    if payload.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed: {sorted(allowed)}",
        )

    ob = (
        db.query(Obligation)
        .filter(Obligation.id == obligation_id, Obligation.tenant_id == user.tenant_id)
        .first()
    )
    if ob is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obligation not found")

    old_status = ob.status
    ob.status = payload.status
    db.commit()
    db.refresh(ob)

    _log_event(
        db,
        user.tenant_id,
        event_type="updated",
        entity_type="obligation",
        entity_id=ob.id,
        actor=user.username,
        payload={"old_status": old_status, "new_status": payload.status},
    )

    return ObligationPatchOut(ok=True, obligation=ObligationOut.model_validate(ob))
