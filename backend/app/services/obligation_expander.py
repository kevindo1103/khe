"""T2 auto-expand scheduler for recurring obligations (DEC-030 Phase 2 Part 4).

Weekly job: for each tenant, find recurring obligations (monthly/quarterly/yearly)
that are NOT part of a milestone series (T2, not T3), and lazily create the next
installment row if one doesn't already exist and the next date is within the
document's expiry date.
"""
from __future__ import annotations

import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.models.tenant import Obligation, Term

logger = logging.getLogger(__name__)

CADENCE_DELTA = {
    "monthly": relativedelta(months=1),
    "quarterly": relativedelta(months=3),
    "yearly": relativedelta(years=1),
}


def _get_doc_expiry(document_id: int, tenant_db: Session) -> date | None:
    """Read the document's ngay_het_han Term, parse ISO; return None if absent/unparseable."""
    row = (
        tenant_db.query(Term.field_value)
        .filter(
            Term.document_id == document_id,
            Term.field_name == "ngay_het_han",
            Term.field_value.isnot(None),
            Term.field_value != "",
        )
        .order_by(Term.created_at.desc())
        .first()
    )
    if not row or not row[0]:
        return None
    try:
        return date.fromisoformat(row[0])
    except (ValueError, TypeError):
        return None


def expand_recurring_obligations(tenant_id: str, tenant_db: Session) -> int:
    """Lazy expand: create the next row for T2 recurring obligations.

    Returns the number of new rows created.
    """
    recurring = (
        tenant_db.query(Obligation)
        .filter(
            Obligation.tenant_id == tenant_id,
            Obligation.recurrence.in_(["monthly", "quarterly", "yearly"]),
            Obligation.status != "done",
            Obligation.milestone_series_id.is_(None),
        )
        .all()
    )

    created = 0
    for obl in recurring:
        if obl.recurrence not in CADENCE_DELTA:
            continue

        last = (
            tenant_db.query(Obligation)
            .filter(
                Obligation.document_id == obl.document_id,
                Obligation.obligation_type == obl.obligation_type,
                Obligation.recurrence == obl.recurrence,
                Obligation.tenant_id == tenant_id,
            )
            .order_by(Obligation.due_date.desc())
            .first()
        )
        if not last or not last.due_date:
            continue

        try:
            last_date = date.fromisoformat(last.due_date)
        except (ValueError, TypeError):
            continue

        next_date = last_date + CADENCE_DELTA[obl.recurrence]

        doc_expiry = _get_doc_expiry(obl.document_id, tenant_db)
        if doc_expiry and next_date > doc_expiry:
            continue

        exists = (
            tenant_db.query(Obligation)
            .filter(
                Obligation.document_id == obl.document_id,
                Obligation.obligation_type == obl.obligation_type,
                Obligation.due_date == next_date.isoformat(),
                Obligation.tenant_id == tenant_id,
            )
            .first()
        )
        if exists:
            continue

        tenant_db.add(Obligation(
            tenant_id=tenant_id,
            document_id=obl.document_id,
            description=obl.description,
            obligation_type=obl.obligation_type,
            recurrence=obl.recurrence,
            due_date=next_date.isoformat(),
            status="pending",
            direction=obl.direction,
            obligor=obl.obligor,
        ))
        tenant_db.flush()
        created += 1

    tenant_db.commit()
    if created:
        logger.info(
            "expand_recurring_obligations: tenant=%s created %d new rows",
            tenant_id,
            created,
        )
    return created
