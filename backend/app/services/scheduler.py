"""APScheduler daily reminder job (#26 PR-B / #62).

Started in FastAPI lifespan. Single daily job at 08:00 ICT runs a multi-tenant
loop over the master Tenant table and dispatches reminders per tenant.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.db.database import MasterSessionLocal, get_tenant_session
from app.models.master import Tenant
from app.services.reminders import send_reminders_for_tenant
from app.services.obligation_expander import expand_recurring_obligations

logger = logging.getLogger(__name__)


async def run_daily_reminder_job() -> None:
    """Daily job: for each tenant, send reminders and flip overdue status."""
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


async def run_expand_all_tenants() -> None:
    """Weekly job: for each tenant, expand T2 recurring obligations."""
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


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler."""
    scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")
    scheduler.add_job(
        run_daily_reminder_job,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_reminder_job",
        replace_existing=True,
    )
    scheduler.add_job(
        run_expand_all_tenants,
        trigger=CronTrigger(day_of_week="mon", hour=2, minute=0),
        id="obligation_expander",
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
