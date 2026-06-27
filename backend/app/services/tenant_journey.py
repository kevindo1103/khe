"""tenant_journey_stage state machine (#213).

Monotonic forward-only onboarding spine:

    NEW → EXTRACTING → NEEDS_REVIEW → CONFIRMED → ACTIVATED → STEADY

Rules:
- No backward transition (strictly increasing stage index).
- ``is_first_session`` is cleared atomically the first time a tenant reaches
  CONFIRMED (or beyond) — DEC-040 nav-unlock (#259). Self-heals on any later
  advance call if a tenant was left inconsistent. It powers the FE nav-lock.
- Branch from EXTRACTING: low-confidence → NEEDS_REVIEW, else CONFIRMED (skip).
- ACTIVATED = ≥1 reminder channel (Telegram OR email) — not both.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.master import Tenant

logger = logging.getLogger(__name__)

JOURNEY_STAGES: list[str] = [
    "NEW", "EXTRACTING", "NEEDS_REVIEW", "CONFIRMED", "ACTIVATED", "STEADY",
]
_ORDER = {stage: i for i, stage in enumerate(JOURNEY_STAGES)}
_ACTIVATED_IDX = _ORDER["ACTIVATED"]
_CONFIRMED_IDX = _ORDER["CONFIRMED"]


def is_valid_stage(stage: str | None) -> bool:
    return stage in _ORDER


def is_forward(current: str, target: str) -> bool:
    """True if ``target`` is a strictly later stage than ``current``."""
    return _ORDER.get(target, -1) > _ORDER.get(current, -1)


def advance_stage(
    db: Session,
    tenant_id: str,
    target: str,
    *,
    require_current_at_least: str | None = None,
) -> str | None:
    """Advance a tenant to ``target`` iff it is strictly forward; else no-op.

    Returns the resulting stage, or None if the tenant or target is unknown.

    ``require_current_at_least`` guards spine-skipping auto-transitions: e.g. a
    reminder channel activated while the tenant is still NEW must NOT jump straight
    to ACTIVATED (require CONFIRMED first). FE-driven PATCH passes no floor —
    monotonic forward is the only constraint there.
    """
    if not is_valid_stage(target):
        return None
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant is None:
        return None

    current = tenant.journey_stage or "NEW"

    # DEC-040 self-heal (#259): is_first_session MUST be False once a tenant is
    # at/past CONFIRMED. Clear it even on a no-op advance — this fixes tenants left
    # in {>=CONFIRMED, is_first_session=True} by the old ACTIVATED threshold (e.g.
    # a PATCH/confirm that advanced to CONFIRMED before this fix). Idempotency-safe.
    healed = False
    if _ORDER.get(current, -1) >= _CONFIRMED_IDX and tenant.is_first_session:
        tenant.is_first_session = False
        healed = True

    if require_current_at_least is not None and _ORDER.get(current, -1) < _ORDER.get(require_current_at_least, 0):
        if healed:
            db.commit()
        return current  # precondition not met — leave stage untouched
    if not is_forward(current, target):
        if healed:
            db.commit()
        return current  # already at/past target, or backward → no-op

    tenant.journey_stage = target
    if _ORDER[target] >= _CONFIRMED_IDX:
        tenant.is_first_session = False  # DEC-040: clear at CONFIRMED+ (nav unlock)
    db.commit()
    logger.info("journey advance tenant=%s %s→%s", tenant_id, current, target)
    return target


def advance_stage_standalone(
    tenant_id: str,
    target: str,
    *,
    require_current_at_least: str | None = None,
) -> str | None:
    """``advance_stage`` for contexts without a master session (background tasks).

    Opens + closes its own master session and never raises — a journey-tracking
    failure must never break upload / extraction.
    """
    from app.db.database import MasterSessionLocal

    db = MasterSessionLocal()
    try:
        return advance_stage(db, tenant_id, target, require_current_at_least=require_current_at_least)
    except Exception:  # noqa: BLE001 - journey tracking must not break the caller
        db.rollback()
        logger.warning("journey advance failed tenant=%s target=%s", tenant_id, target, exc_info=True)
        return None
    finally:
        db.close()
