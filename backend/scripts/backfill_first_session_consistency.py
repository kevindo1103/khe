#!/usr/bin/env python3
"""One-shot backfill: fix tenants left in {>=CONFIRMED, is_first_session=True} (#259).

The old journey threshold cleared is_first_session at ACTIVATED, not CONFIRMED
(DEC-040). Tenants that advanced to CONFIRMED before the fix are stuck with the
sidebar locked. The fix in tenant_journey.advance_stage also self-heals on the
next advance call, but this script clears the state immediately for tenants that
won't trigger another advance soon (e.g. uat-demo).

Usage (from backend/):  python scripts/backfill_first_session_consistency.py
Idempotent — safe to run repeatedly.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.db.database import MasterSessionLocal
from app.models.master import Tenant
from app.services.tenant_journey import JOURNEY_STAGES

_ORDER = {stage: i for i, stage in enumerate(JOURNEY_STAGES)}
_CONFIRMED_IDX = _ORDER["CONFIRMED"]


def backfill() -> int:
    db = MasterSessionLocal()
    fixed = 0
    try:
        for t in db.query(Tenant).all():
            if _ORDER.get(t.journey_stage, -1) >= _CONFIRMED_IDX and t.is_first_session:
                t.is_first_session = False
                fixed += 1
                print(f"  [backfill] {t.id}: {t.journey_stage} → is_first_session=False")
        db.commit()
    finally:
        db.close()
    print(f"[backfill_first_session_consistency] Fixed {fixed} tenant(s).")
    return fixed


if __name__ == "__main__":
    backfill()
