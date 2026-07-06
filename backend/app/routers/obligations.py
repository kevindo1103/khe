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
from app.models.tenant import Document, Event, Obligation, OBLIGATION_STATUSES
from app.services.obligation_chain import propagate_obligation_done
from app.schemas.obligations import (
    BulkCompleteIn,
    BulkCompleteItemOut,
    BulkCompleteOut,
    ObligationListOut,
    ObligationOut,
    ObligationPatchIn,
    ObligationPatchOut,
    ObligationSummaryOut,
    SnoozeOut,
    TriggerConfirmIn,
)
from app.services import chat_query

router = APIRouter(prefix="/obligations", tags=["obligations"])

# Snooze duration (#214) — v1 is always 3 days, no custom duration.
SNOOZE_DAYS = 3


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


@router.get("/summary", response_model=ObligationSummaryOut)
def obligations_summary(
    group_by: str = Query("direction"),
    status: str | None = Query(None),
    direction: str | None = Query(None),
    obligation_type: str | None = Query(None),
    due_within_days: int | None = Query(None, ge=0),
    active_only: bool = Query(True),
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Server-side obligation aggregate for the Dashboard (#199 follow-up).

    Reuses the canonical aggregate (count + grouped labels + status_breakdown)
    the chat path already uses, so the FE renders server `groups[].label`
    (e.g. "Bạn cần" / "Đối tác cần làm cho bạn") instead of deriving direction
    counts client-side. Tenant-scoped; count-only (D-06, no money sum). total=0 is
    a valid response, never an error.

    ``active_only`` defaults True (#253) — the dashboard overview excludes terminal
    done/cancelled so total + direction cards match the active-only list. Pass
    ``active_only=false`` for the full historical count.
    """
    agg = chat_query.aggregate_obligations(
        db, user.tenant_id, group_by,
        status=status, direction=direction, obligation_type=obligation_type,
        due_within_days=due_within_days, active_only=active_only,
    )
    s = agg["summary"]
    return ObligationSummaryOut(
        total=s["total"],
        group_by=s["group_by"],
        groups=s["groups"],
        status_breakdown=s["status_breakdown"],
        source=agg["source"],
    )


# ── Bulk complete (#471) — MUST be before /{obligation_id} to avoid path shadowing ──

_BULK_ALLOWED_STATUSES = {"done", "cancelled"}


@router.patch("/bulk", response_model=BulkCompleteOut)
def bulk_complete_obligations(
    payload: BulkCompleteIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk-update obligations to 'done' or 'cancelled'. Logs one Event per item (D-07/FR-OB-04).

    - Tenant-isolated: only obligations belonging to the authenticated tenant are touched.
    - IDs not found or belonging to another tenant are silently skipped (reported in items[].error).
    - fulfilled_at is required when status='done' (same rule as single PATCH).
    """
    if payload.status not in _BULK_ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"bulk status must be one of: {sorted(_BULK_ALLOWED_STATUSES)}",
        )
    if payload.status == "done" and payload.fulfilled_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fulfilled_at is required when status='done'",
        )
    if not payload.ids:
        return BulkCompleteOut(updated=0, skipped=0, items=[])

    owned = {
        ob.id: ob
        for ob in db.query(Obligation).filter(
            Obligation.id.in_(payload.ids),
            Obligation.tenant_id == user.tenant_id,
        ).all()
    }

    items: list[BulkCompleteItemOut] = []
    updated = 0

    for ob_id in payload.ids:
        if ob_id not in owned:
            items.append(BulkCompleteItemOut(id=ob_id, ok=False, error="not found"))
            continue

        ob = owned[ob_id]
        old_status = ob.status
        ob.status = payload.status

        if payload.status == "done":
            ob.fulfilled_at = payload.fulfilled_at
            ob.fulfilled_by = payload.fulfilled_by or user.username
            propagate_obligation_done(ob.id, db, fulfilled_at=payload.fulfilled_at)
        elif old_status == "done":
            ob.fulfilled_at = None
            ob.fulfilled_by = None
            ob.evidence_doc_ids = None

        _log_event(
            db,
            user.tenant_id,
            event_type="updated",
            entity_type="obligation",
            entity_id=ob.id,
            actor=user.username,
            payload={
                "old_status": old_status,
                "new_status": payload.status,
                "bulk": True,
                "fulfilled_at": payload.fulfilled_at.isoformat() if payload.fulfilled_at else None,
                "fulfilled_by": ob.fulfilled_by if payload.status == "done" else None,
            },
        )
        updated += 1
        items.append(BulkCompleteItemOut(id=ob_id, ok=True))

    db.commit()
    return BulkCompleteOut(
        updated=updated,
        skipped=len(payload.ids) - updated,
        items=items,
    )


@router.patch("/{obligation_id}", response_model=ObligationPatchOut)
def patch_obligation(
    obligation_id: int,
    payload: ObligationPatchIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an obligation's status. SME/status-machine edits only (D-02)."""
    allowed = set(OBLIGATION_STATUSES)
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

    activated_count = 0
    if payload.status == "done":
        # G2 (#302): require fulfilled_at; persist date + actor + evidence.
        if payload.fulfilled_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fulfilled_at is required when marking an obligation done.",
            )
        # F2: validate evidence_doc_ids belong to this tenant.
        if payload.evidence_doc_ids:
            existing = {
                d.id for d in db.query(Document.id)
                .filter(Document.id.in_(payload.evidence_doc_ids),
                        Document.tenant_id == user.tenant_id)
                .all()
            }
            invalid = set(payload.evidence_doc_ids) - existing
            if invalid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Evidence doc IDs not found in this tenant: {sorted(invalid)}",
                )

        ob.status = payload.status
        ob.fulfilled_at = payload.fulfilled_at
        ob.fulfilled_by = payload.fulfilled_by or user.username
        ob.evidence_doc_ids = (
            json.dumps(payload.evidence_doc_ids) if payload.evidence_doc_ids else None
        )
        # G1 (#302): anchor chain propagation on fulfilled_at, not today.
        activated_count = propagate_obligation_done(ob.id, db, fulfilled_at=payload.fulfilled_at)

        # P4 compliance: log evidence_attached Event for each evidence doc (NĐ 13 audit).
        if payload.evidence_doc_ids:
            for ev_doc_id in payload.evidence_doc_ids:
                db.add(Event(
                    tenant_id=user.tenant_id,
                    event_type="evidence_attached",
                    entity_type="obligation",
                    entity_id=ob.id,
                    actor=ob.fulfilled_by,
                    purpose="obligation_fulfillment",
                    payload=json.dumps({
                        "evidence_doc_id": ev_doc_id,
                        "obligation_id": ob.id,
                    }),
                ))
    else:
        ob.status = payload.status
        # F1: clear stale fulfillment data when reverting away from "done".
        if old_status == "done":
            ob.fulfilled_at = None
            ob.fulfilled_by = None
            ob.evidence_doc_ids = None

    _log_event(
        db,
        user.tenant_id,
        event_type="updated",
        entity_type="obligation",
        entity_id=ob.id,
        actor=user.username,
        payload={
            "old_status": old_status,
            "new_status": payload.status,
            "fulfilled_at": payload.fulfilled_at.isoformat() if payload.fulfilled_at else None,
            "fulfilled_by": ob.fulfilled_by if payload.status == "done" else None,
            "evidence_doc_ids": payload.evidence_doc_ids,
        },
    )

    db.commit()
    db.refresh(ob)

    return ObligationPatchOut(ok=True, obligation=ObligationOut.model_validate(ob), activated_count=activated_count)


@router.post("/{obligation_id}/snooze", response_model=SnoozeOut)
def snooze_obligation(
    obligation_id: int,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Snooze this obligation's reminder for 3 days ("Nhắc lại sau 3 ngày", #214).

    Suppresses only the reminder — the obligation itself (status, due_date) is
    untouched and still visible (D-07). Auto-resumes once snoozed_until passes.
    """
    ob = (
        db.query(Obligation)
        .filter(Obligation.id == obligation_id, Obligation.tenant_id == user.tenant_id)
        .first()
    )
    if ob is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obligation not found")

    snoozed_until = datetime.utcnow() + timedelta(days=SNOOZE_DAYS)
    ob.snoozed_until = snoozed_until

    _log_event(
        db,
        user.tenant_id,
        event_type="reminder_snoozed",
        entity_type="obligation",
        entity_id=ob.id,
        actor=user.username,
        payload={"obligation_id": ob.id, "snoozed_until": snoozed_until.isoformat()},
    )

    db.commit()
    return SnoozeOut(ok=True, snoozed_until=snoozed_until)


@router.post("/{obligation_id}/confirm-trigger", response_model=ObligationOut)
def confirm_trigger(
    obligation_id: int,
    body: TriggerConfirmIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm that a trigger event has occurred for a waiting_trigger obligation (#501).

    Only for event-triggered obligations (milestone_trigger != "date"). Date-anchored
    obligations (milestone_trigger == "date") resolve automatically via contract date
    extraction — D-08 prevents manual override.

    Computes due_date = event_date + trigger_delay_days and transitions:
      - pending          when due_date >= today
      - awaiting_confirmation when due_date < today  (D-15 backfill guard — D-02 SME confirm)

    Prerequisite guard (defense-in-depth): if trigger_obligation_id is set, the
    referenced obligation must already be done.

    D-07 trigger_confirmed Event logged in the same transaction as the status change.
    """
    ob = (
        db.query(Obligation)
        .filter(Obligation.id == obligation_id, Obligation.tenant_id == user.tenant_id)
        .first()
    )
    if ob is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obligation not found")

    # D-08: date-anchored obligations resolve via AI contract date extraction, not manual confirm.
    if ob.milestone_trigger == "date":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Date-anchored obligations are resolved via contract date extraction, not manual trigger confirmation",
        )

    if ob.status != "waiting_trigger":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Obligation is not in waiting_trigger state (current: {ob.status})",
        )

    # Prerequisite guard (defense-in-depth for edge cases where cascade didn't fire).
    if ob.trigger_obligation_id:
        prereq = (
            db.query(Obligation)
            .filter(
                Obligation.id == ob.trigger_obligation_id,
                Obligation.tenant_id == user.tenant_id,
            )
            .first()
        )
        if prereq is None or prereq.status != "done":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Prerequisite obligation is not done — cannot confirm trigger event",
            )

    event_date = body.event_date or date.today()
    delay = ob.trigger_delay_days or 0
    due = event_date + timedelta(days=delay)
    ob.due_date = due.isoformat()
    # D-15: backfilled past due_date → awaiting_confirmation (D-02 SME confirm required).
    ob.status = "awaiting_confirmation" if due < date.today() else "pending"

    # Log Event in the same transaction as the status change (atomicity — D-07).
    _log_event(
        db,
        user.tenant_id,
        event_type="trigger_confirmed",
        entity_type="obligation",
        entity_id=ob.id,
        actor=user.username,
        payload={
            "event_date": str(event_date),
            "due_date": ob.due_date,
            "confirmed_by": user.username,
        },
    )
    db.commit()
    db.refresh(ob)

    return ObligationOut.model_validate(ob)
