"""Event-chaining service for obligation series (DEC-030 Phase 2 Part 3).

When an obligation is marked "done", any obligations waiting on it
(status=waiting_trigger, trigger_obligation_id=that obligation) are activated:
- due_date set to today + trigger_delay_days (or today if no delay)
- status flipped to "pending"
- milestone_trigger set to "date" (now has a concrete date)
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.tenant import Obligation

logger = logging.getLogger(__name__)


def propagate_obligation_done(obligation_id: int, tenant_db: Session) -> int:
    """Activate obligations waiting on the given obligation.

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

    today = date.today()
    for dep in dependents:
        if dep.trigger_delay_days:
            dep.due_date = (today + timedelta(days=dep.trigger_delay_days)).isoformat()
        else:
            dep.due_date = today.isoformat()
        dep.status = "pending"
        dep.milestone_trigger = "date"

    tenant_db.commit()
    count = len(dependents)
    if count:
        logger.info(
            "propagate_obligation_done: obligation=%s activated %d dependents",
            obligation_id,
            count,
        )
    return count
