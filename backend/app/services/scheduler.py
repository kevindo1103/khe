"""APScheduler daily reminder job (#26 PR-B / #62).

Started in FastAPI lifespan. Single daily job at 08:00 ICT runs a multi-tenant
loop over the master Tenant table and dispatches reminders per tenant.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.db.database import MasterSessionLocal, get_tenant_session
from app.models.master import Tenant
from app.models.tenant import Event
from app.services.reminders import (
    retry_failed_reminders_for_tenant,
    send_reminders_for_tenant,
)
from app.services.chat_session import cleanup_expired_sessions
from app.services.obligation_expander import expand_recurring_obligations

logger = logging.getLogger(__name__)

_ICT = ZoneInfo("Asia/Ho_Chi_Minh")
_DAILY_REMINDER_HOUR = 8  # 08:00 ICT daily reminder fire time

# One-time scheduler benchmark (#185). /health/scheduler reports how long a
# multi-tenant tick takes and how many tenants it loops — to measure distance
# to the #181 scaling thresholds. Process-local; resets on restart.
_scheduler_metrics: dict[str, object] = {
    "active_tenants": None,
    "last_reminder_tick_ms": None,
    "last_expand_tick_ms": None,
    "last_run_at": None,
}


def get_scheduler_metrics() -> dict:
    """Return a snapshot of the latest scheduler tick metrics (#185)."""
    return dict(_scheduler_metrics)


async def run_daily_reminder_job() -> None:
    """Daily job: for each tenant, send reminders and flip overdue status."""
    start = time.monotonic()
    db: Session = MasterSessionLocal()
    try:
        tenants = db.query(Tenant).all()
    finally:
        db.close()

    for tenant in tenants:
        tenant_db = get_tenant_session(tenant.id)
        try:
            await send_reminders_for_tenant(
                tenant_db,
                tenant.id,
            )
        except Exception as exc:
            logger.exception("Daily reminder job failed for tenant %s: %s", tenant.id, exc)
        finally:
            tenant_db.close()

    elapsed_ms = round((time.monotonic() - start) * 1000, 1)
    _scheduler_metrics["active_tenants"] = len(tenants)
    _scheduler_metrics["last_reminder_tick_ms"] = elapsed_ms
    _scheduler_metrics["last_run_at"] = datetime.now(_ICT).isoformat()
    logger.info("daily_reminder_job tick: tenants=%d duration_ms=%s", len(tenants), elapsed_ms)


async def run_expand_all_tenants() -> None:
    """Weekly job: for each tenant, expand T2 recurring obligations."""
    start = time.monotonic()
    db: Session = MasterSessionLocal()
    try:
        tenants = db.query(Tenant).all()
    finally:
        db.close()

    for tenant in tenants:
        tenant_db = get_tenant_session(tenant.id)
        try:
            expand_recurring_obligations(tenant.id, tenant_db)
        except Exception as exc:
            logger.exception("Obligation expander job failed for tenant %s: %s", tenant.id, exc)
        finally:
            tenant_db.close()

    elapsed_ms = round((time.monotonic() - start) * 1000, 1)
    _scheduler_metrics["active_tenants"] = len(tenants)
    _scheduler_metrics["last_expand_tick_ms"] = elapsed_ms
    _scheduler_metrics["last_run_at"] = datetime.now(_ICT).isoformat()
    logger.info("obligation_expander tick: tenants=%d duration_ms=%s", len(tenants), elapsed_ms)


async def run_chat_session_cleanup() -> None:
    """Daily job (#201/#203): purge expired chat_sessions per tenant."""
    db: Session = MasterSessionLocal()
    try:
        tenants = db.query(Tenant).all()
    finally:
        db.close()

    total = 0
    for tenant in tenants:
        tenant_db = get_tenant_session(tenant.id)
        try:
            total += cleanup_expired_sessions(tenant_db)
        except Exception as exc:
            logger.exception("Chat session cleanup failed for tenant %s: %s", tenant.id, exc)
        finally:
            tenant_db.close()
    if total:
        logger.info("chat_session cleanup removed %d expired rows", total)


async def run_retry_tick_all_tenants() -> None:
    """Every-30-min retry tick (#183): re-attempt failed reminders per tenant."""
    db: Session = MasterSessionLocal()
    try:
        tenants = db.query(Tenant).all()
    finally:
        db.close()

    for tenant in tenants:
        tenant_db = get_tenant_session(tenant.id)
        try:
            res = await retry_failed_reminders_for_tenant(tenant_db, tenant.id)
            if res.get("retried") or res.get("dead"):
                logger.info("retry tick tenant=%s %s", tenant.id, res)
        except Exception as exc:
            logger.exception("Retry tick failed for tenant %s: %s", tenant.id, exc)
        finally:
            tenant_db.close()


async def catch_up_missed_daily_run(reference_time: datetime | None = None) -> bool:
    """On startup, fire the daily reminder job if it was missed today (#183).

    APScheduler's in-memory job store does not persist missed runs across a
    process restart, so a crash during the 08:00 fire window would silently skip
    a day. If it's already past the daily run hour and no tenant has a
    reminder_batch Event dated today, run the job once now.

    Returns True if a catch-up run was triggered.
    """
    now = reference_time or datetime.now(_ICT)
    if now.hour < _DAILY_REMINDER_HOUR:
        return False  # today's window hasn't opened yet — normal cron will fire.

    today = now.date()
    db: Session = MasterSessionLocal()
    try:
        tenants = db.query(Tenant).all()
    finally:
        db.close()

    ran_today = False
    for tenant in tenants:
        tenant_db = get_tenant_session(tenant.id)
        try:
            batch = (
                tenant_db.query(Event)
                .filter(
                    Event.entity_type == "tenant",
                    Event.event_type == "reminder_batch",
                )
                .order_by(Event.created_at.desc())
                .first()
            )
            if batch and batch.created_at and batch.created_at.date() == today:
                ran_today = True
                break
        finally:
            tenant_db.close()

    if ran_today:
        return False

    logger.info("Daily reminder run missed for %s — firing catch-up now", today)
    await run_daily_reminder_job()
    return True


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler."""
    scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")
    scheduler.add_job(
        run_daily_reminder_job,
        trigger=CronTrigger(hour=_DAILY_REMINDER_HOUR, minute=0),
        id="daily_reminder_job",
        replace_existing=True,
        # Tolerate event-loop lag / short pauses so a slightly-late fire still
        # runs instead of being skipped (#183). Cross-restart catch-up is handled
        # by catch_up_missed_daily_run() since the memory job store doesn't persist.
        misfire_grace_time=4 * 3600,
        coalesce=True,
    )
    scheduler.add_job(
        run_expand_all_tenants,
        trigger=CronTrigger(day_of_week="mon", hour=2, minute=0),
        id="obligation_expander",
        replace_existing=True,
    )
    scheduler.add_job(
        run_retry_tick_all_tenants,
        trigger=IntervalTrigger(minutes=30),
        id="reminder_retry_tick",
        replace_existing=True,
        misfire_grace_time=600,
        coalesce=True,
    )
    scheduler.add_job(
        run_chat_session_cleanup,
        # Daily (not weekly): with a 24h TTL a weekly sweep could leave up to
        # 7 days of stale rows accumulating (#203 M2).
        trigger=CronTrigger(hour=3, minute=0),
        id="chat_session_cleanup",
        replace_existing=True,
    )
    return scheduler


def start_scheduler(scheduler: AsyncIOScheduler | None = None) -> AsyncIOScheduler:
    """Start the scheduler. Returns the scheduler instance."""
    sched = scheduler or create_scheduler()
    if not sched.running:
        sched.start()
        logger.info("APScheduler daily reminder job started")
    return sched


def shutdown_scheduler(scheduler: AsyncIOScheduler | None = None) -> None:
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler shut down")
