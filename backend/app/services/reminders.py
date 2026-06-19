"""Reminder engine (#26 PR-B / #62).

- Computes the due window for pending obligations using `remind_before_days`.
- Idempotent delivery via `Event(event_type="reminder_sent")` ledger lookup.
- Consent gate via `purpose="reminder_send"` (Compliance §A.5).
- Overdue status flip for obligations whose due_date is past today.
"""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.tenant import Event, Obligation
from app.services.consent import check_consent
from app.services.telegram import send_obligation_reminder

logger = logging.getLogger(__name__)


def _today() -> date:
    """Centralize today for testability."""
    return date.today()


def _reminder_already_sent(db: Session, obligation_id: int) -> bool:
    """Check the Event ledger for a reminder_sent row for this obligation."""
    return (
        db.query(Event)
        .filter(
            Event.entity_type == "obligation",
            Event.entity_id == obligation_id,
            Event.event_type == "reminder_sent",
        )
        .first()
        is not None
    )


def _log_reminder_sent(
    db: Session,
    tenant_id: str,
    obligation_id: int,
    channel: str,
    channel_target_ref: str,
    success: bool,
) -> None:
    event = Event(
        tenant_id=tenant_id,
        entity_type="obligation",
        entity_id=obligation_id,
        event_type="reminder_sent",
        actor="system",
        purpose="reminder_send",
        channel=channel,
        channel_target_ref=channel_target_ref,
        payload=json.dumps({"success": success}),
    )
    db.add(event)
    db.commit()


def _log_reminder_batch(
    db: Session,
    tenant_id: str,
    attempted: int,
    sent: int,
    overdue_flipped: int,
) -> None:
    event = Event(
        tenant_id=tenant_id,
        entity_type="tenant",
        entity_id=0,
        event_type="reminder_batch",
        actor="system",
        purpose="reminder_send",
        payload=json.dumps(
            {
                "attempted": attempted,
                "sent": sent,
                "overdue_flipped": overdue_flipped,
            }
        ),
    )
    db.add(event)
    db.commit()


def compute_due_window(
    db: Session,
    tenant_id: str,
    reference_date: date | None = None,
) -> list[Obligation]:
    """Return pending obligations whose due_date falls within remind_before_days.

    Also flips status="overdue" for any pending obligation with due_date < today.
    """
    today = reference_date or _today()
    pending = (
        db.query(Obligation)
        .filter(
            Obligation.tenant_id == tenant_id,
            Obligation.status == "pending",
        )
        .all()
    )

    result: list[Obligation] = []
    modified = False
    for ob in pending:
        if ob.due_date is None:
            # open_ended_review obligations are never due-window reminders;
            # they remain pending until SME action.
            continue
        try:
            ob_date = date.fromisoformat(ob.due_date)
        except ValueError:
            continue

        if ob_date < today:
            ob.status = "overdue"
            modified = True
            continue

        window_start = today
        window_end = today + timedelta(days=ob.remind_before_days)
        if window_start <= ob_date <= window_end:
            result.append(ob)

    if modified:
        db.commit()

    return result


async def send_reminders_for_tenant(
    db: Session,
    tenant_id: str,
    chat_id: str | None,
    reference_date: date | None = None,
) -> dict:
    """Send reminders for one tenant.

    - Consent gate: skips entirely if no active reminder_send consent.
    - Idempotent: skips obligations already logged as reminder_sent.
    - Returns counts: attempted, sent, skipped.
    """
    if not check_consent(db, tenant_id, "reminder_send"):
        logger.info("No reminder_send consent for tenant %s; skipping batch", tenant_id)
        return {"attempted": 0, "sent": 0, "skipped": 0, "consent": False}

    due_obs = compute_due_window(db, tenant_id, reference_date)
    attempted = 0
    sent = 0
    skipped = 0

    for ob in due_obs:
        if _reminder_already_sent(db, ob.id):
            skipped += 1
            continue

        attempted += 1
        success = False
        try:
            success = await send_obligation_reminder(
                tenant_id,
                ob.id,
                ob.description,
                ob.due_date,
                chat_id,
            )
        except Exception as exc:
            logger.exception("Unexpected error sending reminder for obligation %s: %s", ob.id, exc)

        _log_reminder_sent(db, tenant_id, ob.id, "telegram", chat_id or "", success)
        if success:
            sent += 1

    return {"attempted": attempted, "sent": sent, "skipped": skipped, "consent": True}
