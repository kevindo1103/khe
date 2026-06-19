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

from app.core.config import settings
from app.models.tenant import Event, Obligation
from app.services.consent import check_consent, get_active_consent_channel
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
        payload=json.dumps({"success": True}),
    )
    db.add(event)
    db.commit()


def _log_reminder_failed(
    db: Session,
    tenant_id: str,
    obligation_id: int,
    channel: str,
    channel_target_ref: str,
    reason: str,
) -> None:
    event = Event(
        tenant_id=tenant_id,
        entity_type="obligation",
        entity_id=obligation_id,
        event_type="reminder_failed",
        actor="system",
        purpose="reminder_send",
        channel=channel,
        channel_target_ref=channel_target_ref,
        payload=json.dumps({"success": False, "reason": reason}),
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


def _flip_overdue_status(
    db: Session,
    tenant_id: str,
    reference_date: date | None = None,
) -> int:
    """Flip status='overdue' for pending obligations whose due_date < today.

    Returns the number of rows flipped.
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

    flipped = 0
    for ob in pending:
        if ob.due_date is None:
            continue
        try:
            ob_date = date.fromisoformat(ob.due_date)
        except ValueError:
            continue
        if ob_date < today:
            ob.status = "overdue"
            flipped += 1

    if flipped:
        db.commit()
    return flipped


def compute_due_window(
    db: Session,
    tenant_id: str,
    reference_date: date | None = None,
) -> list[Obligation]:
    """Return pending obligations whose due_date falls within remind_before_days.

    Does NOT mutate status. Call _flip_overdue_status separately.
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
    for ob in pending:
        if ob.due_date is None:
            # open_ended_review obligations are never due-window reminders;
            # they remain pending until SME action.
            continue
        try:
            ob_date = date.fromisoformat(ob.due_date)
        except ValueError:
            continue

        window_start = today
        window_end = today + timedelta(days=ob.remind_before_days)
        if window_start <= ob_date <= window_end:
            result.append(ob)

    return result


async def send_reminders_for_tenant(
    db: Session,
    tenant_id: str,
    reference_date: date | None = None,
) -> dict:
    """Send reminders for one tenant.

    - Consent gate: skips entirely if no active reminder_send consent.
    - Idempotent: skips obligations already logged as reminder_sent.
    - Per-tenant routing: chat_id from consent.channel_target_ref (dev fallback to
      settings.TELEGRAM_CHAT_ID).
    - Returns counts: attempted, sent, skipped, failed, skipped_no_destination.
    """
    if not check_consent(db, tenant_id, "reminder_send"):
        logger.info("No reminder_send consent for tenant %s; skipping batch", tenant_id)
        return {"attempted": 0, "sent": 0, "skipped": 0, "failed": 0, "skipped_no_destination": 0, "consent": False}

    # Resolve destination from consent. Production must route via consent record;
    # global env var is dev-only fallback.
    consent_event = get_active_consent_channel(db, tenant_id, "reminder_send")
    channel = consent_event.channel if consent_event else "telegram"
    chat_id = (
        consent_event.channel_target_ref
        if consent_event and consent_event.channel_target_ref
        else (settings.TELEGRAM_CHAT_ID if settings.ENVIRONMENT == "development" else None)
    )

    overdue_flipped = _flip_overdue_status(db, tenant_id, reference_date)
    due_obs = compute_due_window(db, tenant_id, reference_date)
    attempted = 0
    sent = 0
    skipped = 0
    failed = 0
    skipped_no_destination = 0

    for ob in due_obs:
        if _reminder_already_sent(db, ob.id):
            skipped += 1
            continue

        if not chat_id:
            skipped_no_destination += 1
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

        if success:
            _log_reminder_sent(db, tenant_id, ob.id, channel or "telegram", chat_id)
            sent += 1
        else:
            _log_reminder_failed(db, tenant_id, ob.id, channel or "telegram", chat_id, "delivery_failed")
            failed += 1

    _log_reminder_batch(
        db,
        tenant_id,
        attempted=attempted,
        sent=sent,
        overdue_flipped=overdue_flipped,
    )

    return {
        "attempted": attempted,
        "sent": sent,
        "skipped": skipped,
        "failed": failed,
        "skipped_no_destination": skipped_no_destination,
        "consent": True,
    }
