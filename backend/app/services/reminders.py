"""Reminder engine (#26 PR-B / #62).

- Computes the due window for pending obligations using `remind_before_days`.
- Idempotent delivery via `Event(event_type="reminder_sent")` ledger lookup.
- Consent gate via `purpose="reminder_send"` (Compliance §A.5).
- Overdue status flip for obligations whose due_date is past today.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tenant import Document, Event, Obligation
from app.services.consent import check_consent, get_active_consent_channel
from app.services.telegram import send_admin_alert, send_obligation_reminder

logger = logging.getLogger(__name__)

# Retry-tick policy (#183 / #180a). Backoff per attempt already made:
# 1st retry waits 1m after the 1st failure, then 5m, 30m, 2h, 4h.
_RETRY_BACKOFF_MINUTES = [1, 5, 30, 120, 240]
_MAX_RETRY_ATTEMPTS = 5
# Backfill: re-attempt reminders whose first failure was at most this many days
# ago. Older than this → drop (D-08 spirit: a reminder 3 days late is noise).
_BACKFILL_MAX_AGE_DAYS = 1


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


def _log_reminder_dead(
    db: Session,
    tenant_id: str,
    obligation_id: int,
    channel: str,
    channel_target_ref: str,
    reason: str,
) -> None:
    """Append a terminal reminder_dead Event — retry tick gave up on this one."""
    event = Event(
        tenant_id=tenant_id,
        entity_type="obligation",
        entity_id=obligation_id,
        event_type="reminder_dead",
        actor="system",
        purpose="reminder_send",
        channel=channel,
        channel_target_ref=channel_target_ref,
        payload=json.dumps({"reason": reason}),
    )
    db.add(event)
    db.commit()


def _has_event(db: Session, obligation_id: int, event_type: str) -> bool:
    """True if any Event of the given type exists for this obligation."""
    return (
        db.query(Event)
        .filter(
            Event.entity_type == "obligation",
            Event.entity_id == obligation_id,
            Event.event_type == event_type,
        )
        .first()
        is not None
    )


def _failure_events(db: Session, tenant_id: str, obligation_id: int) -> list[Event]:
    """All reminder_failed events for an obligation, oldest first."""
    return (
        db.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.entity_type == "obligation",
            Event.entity_id == obligation_id,
            Event.event_type == "reminder_failed",
        )
        .order_by(Event.created_at.asc())
        .all()
    )


async def retry_failed_reminders_for_tenant(
    db: Session,
    tenant_id: str,
    reference_time: datetime | None = None,
) -> dict:
    """Re-attempt reminders that previously failed and never succeeded (#183).

    Reuses the Event ledger (no outbox table — that is #180b). For every
    obligation with a reminder_failed event but no reminder_sent / reminder_dead:

    - **Idempotency:** skip if a reminder_sent already exists (same-day no-dup).
    - **Backfill window:** if the first failure is older than
      ``_BACKFILL_MAX_AGE_DAYS`` → mark reminder_dead(stale_backfill) and drop.
    - **Max attempts:** at ``_MAX_RETRY_ATTEMPTS`` failures → reminder_dead +
      admin Telegram alert.
    - **Exponential backoff:** wait ``_RETRY_BACKOFF_MINUTES[attempts-1]`` after
      the most recent failure before re-sending.

    ``reference_time`` defaults to ``datetime.utcnow()`` to match the UTC
    ``Event.created_at`` server default; tests pass it explicitly.
    """
    now = reference_time or datetime.utcnow()
    result = {
        "candidates": 0, "retried": 0, "sent": 0,
        "still_failing": 0, "dead": 0, "skipped_backoff": 0, "consent": True,
    }

    # Consent gate (same as the daily job) — no consent ⇒ nothing to retry.
    if not check_consent(db, tenant_id, "reminder_send"):
        result["consent"] = False
        return result

    failed_ids = [
        row.entity_id
        for row in db.query(Event.entity_id)
        .filter(
            Event.tenant_id == tenant_id,
            Event.entity_type == "obligation",
            Event.event_type == "reminder_failed",
        )
        .distinct()
        .all()
    ]
    if not failed_ids:
        return result

    consent_event = get_active_consent_channel(db, tenant_id, "reminder_send")
    channel = (consent_event.channel if consent_event else "telegram") or "telegram"
    chat_id = (
        consent_event.channel_target_ref
        if consent_event and consent_event.channel_target_ref
        else (settings.TELEGRAM_CHAT_ID if settings.ENVIRONMENT == "development" else None)
    )

    for obl_id in failed_ids:
        # Terminal states win — already delivered or already given up.
        if _has_event(db, obl_id, "reminder_sent") or _has_event(db, obl_id, "reminder_dead"):
            continue

        failures = _failure_events(db, tenant_id, obl_id)
        if not failures:
            continue
        result["candidates"] += 1
        attempts = len(failures)
        first_at = failures[0].created_at or now
        last_at = failures[-1].created_at or now

        ob = (
            db.query(Obligation)
            .filter(Obligation.tenant_id == tenant_id, Obligation.id == obl_id)
            .first()
        )
        if ob is None:
            continue

        # Backfill staleness: drop reminders whose first failure is too old.
        if (now.date() - first_at.date()).days > _BACKFILL_MAX_AGE_DAYS:
            _log_reminder_dead(db, tenant_id, obl_id, channel, chat_id or "", "stale_backfill")
            result["dead"] += 1
            continue

        # Exhausted attempts → dead-letter + admin alert.
        if attempts >= _MAX_RETRY_ATTEMPTS:
            _log_reminder_dead(db, tenant_id, obl_id, channel, chat_id or "", "max_attempts")
            result["dead"] += 1
            await send_admin_alert(
                f"Tenant `{tenant_id}` — nghĩa vụ #{obl_id} không gửi được reminder "
                f"sau {attempts} lần thử: {ob.description}"
            )
            continue

        # Exponential backoff since the most recent failure.
        backoff_min = _RETRY_BACKOFF_MINUTES[attempts - 1]
        if now < last_at + timedelta(minutes=backoff_min):
            result["skipped_backoff"] += 1
            continue

        if not chat_id:
            continue

        result["retried"] += 1
        success = False
        try:
            success = await send_obligation_reminder(
                tenant_id, obl_id, ob.description, ob.due_date, chat_id
            )
        except Exception as exc:  # noqa: BLE001 — never let one send crash the tick
            logger.exception("Retry send crashed for obligation %s: %s", obl_id, exc)

        if success:
            _log_reminder_sent(db, tenant_id, obl_id, channel, chat_id)
            result["sent"] += 1
        else:
            _log_reminder_failed(db, tenant_id, obl_id, channel, chat_id, "retry_failed")
            result["still_failing"] += 1

    return result


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
        .join(Document, Document.id == Obligation.document_id)
        .filter(
            Obligation.tenant_id == tenant_id,
            Obligation.status == "pending",
            # #250: only act on obligations from user-CONFIRMED docs (D-02 — never
            # touch unreviewed data). With the first-confirm journey gate a tenant
            # can be CONFIRMED with docs still unconfirmed; their obligations must
            # stay untouched until the user confirms them.
            Document.confirmed_by_user_at.isnot(None),
            # P5 (#302): obligations with fulfilled_at set are completed (pending
            # confirmation). Never flip these to overdue — they need SME confirm,
            # not a false alarm. See "cần xác nhận đã hoàn thành?" UX spec.
            Obligation.fulfilled_at.is_(None),
            # #313 (DEC-048 Option B): cascade-past children get status=awaiting_confirmation
            # (not "pending") — already excluded by the status=="pending" filter above.
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
        .join(Document, Document.id == Obligation.document_id)
        .filter(
            Obligation.tenant_id == tenant_id,
            Obligation.status == "pending",
            # #250 (D-02): reminders only for user-CONFIRMED docs — never nhắc on a
            # deadline the user hasn't reviewed. See _flip_overdue_status note.
            Document.confirmed_by_user_at.isnot(None),
            # P5 (#302): suppress reminders for already-fulfilled obligations pending
            # formal confirmation. fulfilled_at IS NOT NULL = awaiting SME confirm.
            Obligation.fulfilled_at.is_(None),
            # #313 (DEC-048 Option B): cascade-past children get status=awaiting_confirmation
            # (not "pending") — already excluded by the status=="pending" filter above.
        )
        .all()
    )

    now = datetime.utcnow()
    result: list[Obligation] = []
    for ob in pending:
        if ob.due_date is None:
            # open_ended_review obligations are never due-window reminders;
            # they remain pending until SME action.
            continue
        # Snooze (#214): suppress while snoozed_until is in the future. Auto-resumes
        # once it passes (no cleanup) — snooze never changes status/due_date (D-07).
        if ob.snoozed_until is not None and ob.snoozed_until > now:
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
