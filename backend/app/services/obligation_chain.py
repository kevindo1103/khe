"""Event-chaining service for obligation series (DEC-030 Phase 2 Part 3).

When an obligation is marked "done", any obligations waiting on it
(status=waiting_trigger, trigger_obligation_id=that obligation) are activated:
- due_date set to today + trigger_delay_days (or today if no delay)
- status flipped to "pending"
- milestone_trigger set to "date" (now has a concrete date)
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.tenant import Obligation

logger = logging.getLogger(__name__)


def propagate_obligation_done(
    obligation_id: int,
    tenant_db: Session,
    fulfilled_at: datetime | None = None,
) -> int:
    """Activate obligations waiting on the given obligation.

    ``fulfilled_at`` anchors the child due-date calculation (G1 fix #302):
    use the parent's actual completion date, not today, so backfilled
    historical milestones propagate the correct future date.

    Returns the count of activated dependents (for Frontend toast).
    """
    dependents = (
        tenant_db.query(Obligation)
        .filter(
            Obligation.trigger_obligation_id == obligation_id,
            Obligation.status == "waiting_trigger",
        )
        .all()
    )

    anchor = fulfilled_at.date() if fulfilled_at else date.today()
    for dep in dependents:
        if dep.trigger_delay_days:
            dep.due_date = (anchor + timedelta(days=dep.trigger_delay_days)).isoformat()
        else:
            dep.due_date = anchor.isoformat()
        dep.status = "pending"
        dep.milestone_trigger = "date"

    count = len(dependents)
    if count:
        logger.info(
            "propagate_obligation_done: obligation=%s activated %d dependents",
            obligation_id,
            count,
        )
    return count
