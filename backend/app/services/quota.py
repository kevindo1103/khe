"""Ingest quota guard (FR-TN-01 / D-11, #63).

Prevents vision-extraction cost runaway. One quota slot = one accepted ingest
(PM 2026-06-19: slot consumed at accept, NOT refunded on extraction failure).

TOCTOU-safe: the consume is a single atomic conditional UPDATE
(`docs_used_month = docs_used_month + 1 WHERE docs_used_month < doc_quota`); the
WHERE clause IS the gate, so concurrent uploads can never over-consume.
"""
from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.master import Tenant

logger = logging.getLogger(__name__)

DEFAULT_DOC_QUOTA = 500  # PM-ratified default; firm-configurable per tenant later.


def _next_month_first(today: date) -> date:
    """First day of next calendar month."""
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    return date(today.year, today.month + 1, 1)


def try_consume_quota(master_db: Session, tenant_id: str) -> bool:
    """Atomically consume one ingest slot. Returns True if consumed, False if at limit.

    The conditional UPDATE is both the check and the increment — no read-then-write
    race (D-11 TOCTOU). rowcount == 1 → consumed; 0 → at/over limit (or unknown tenant).
    """
    result = master_db.execute(
        update(Tenant)
        .where(Tenant.id == tenant_id, Tenant.docs_used_month < Tenant.doc_quota)
        .values(docs_used_month=Tenant.docs_used_month + 1)
    )
    master_db.commit()
    return result.rowcount == 1


def get_quota_status(master_db: Session, tenant_id: str) -> dict | None:
    """Read-only quota snapshot for a tenant (firm portal Phase 2 / diagnostics)."""
    t = master_db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if t is None:
        return None
    return {
        "doc_quota": t.doc_quota,
        "docs_used_month": t.docs_used_month,
        "quota_reset_at": t.quota_reset_at.isoformat() if t.quota_reset_at else None,
    }


def reset_all_quotas(master_db: Session, today: date | None = None) -> int:
    """Reset docs_used_month → 0 for every tenant + set next reset date. Returns row count.

    Run by the calendar-1st APScheduler job. Idempotent within a day.
    """
    today = today or date.today()
    result = master_db.execute(
        update(Tenant).values(
            docs_used_month=0,
            cost_vnd_month=0,  # #255: reset monthly cost with the doc counter
            quota_reset_at=_next_month_first(today),
        )
    )
    master_db.commit()
    logger.info("monthly quota reset: %d tenants → next reset %s", result.rowcount, _next_month_first(today))
    return result.rowcount


def add_extraction_cost(master_db: Session, tenant_id: str, cost_vnd: float) -> bool:
    """Atomically add one extraction's cost to a tenant's month + lifetime aggregate (#255).

    Called at extraction-complete (cost is known) — NOT in the upload-time quota
    guard, which runs before the provider call. Only successful extractions are
    billed. Returns True if a row was updated.
    """
    if not cost_vnd:
        return False
    result = master_db.execute(
        update(Tenant)
        .where(Tenant.id == tenant_id)
        .values(
            cost_vnd_month=Tenant.cost_vnd_month + cost_vnd,
            cost_vnd_total=Tenant.cost_vnd_total + cost_vnd,
        )
    )
    master_db.commit()
    return result.rowcount == 1


def add_extraction_cost_standalone(tenant_id: str, cost_vnd: float) -> bool:
    """``add_extraction_cost`` from a background task (own master session, never raises)."""
    from app.db.database import MasterSessionLocal

    db = MasterSessionLocal()
    try:
        return add_extraction_cost(db, tenant_id, cost_vnd)
    except Exception:  # noqa: BLE001 - cost tracking must never break extraction
        db.rollback()
        logger.warning("extraction cost aggregate failed tenant=%s", tenant_id, exc_info=True)
        return False
    finally:
        db.close()
