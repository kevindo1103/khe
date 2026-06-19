#!/usr/bin/env python3
"""
Idempotent per-tenant Alembic migration runner.

Usage (from backend/ directory):
    python scripts/migrate_all_tenants.py

Loops over every tenant in master.db and applies the alembic_tenant
migration chain up to head.  Running twice is a no-op.
"""
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.db.database import MasterSessionLocal
from app.models.master import Tenant


def _run_upgrade_for_tenant(tenant_id: str, db_path: str) -> None:
    """Programmatically run alembic upgrade for a single tenant DB.

    Baseline-stamps DBs that were bootstrapped via create_all() (tables present
    but no alembic_version) before upgrading — mirrors init_tenant_db so a
    create_all'd tenant DB on the VPS doesn't fail with "table already exists".
    """
    from sqlalchemy import create_engine, inspect

    cfg = Config(str(backend_dir / "alembic_tenant.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "alembic_tenant"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    if os.path.exists(db_path):
        eng = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        names = inspect(eng).get_table_names()
        eng.dispose()
        if names and "alembic_version" not in names:
            command.stamp(cfg, "tenant_001")
            print(f"  [alembic] {tenant_id} baseline-stamped tenant_001")

    command.upgrade(cfg, "head")
    print(f"  [alembic] {tenant_id} -> head")


def main() -> None:
    db = MasterSessionLocal()
    try:
        tenants = db.query(Tenant).all()
        if not tenants:
            print("[migrate_all_tenants] No tenants found in master.db.")
            return

        print(f"[migrate_all_tenants] Found {len(tenants)} tenant(s).")
        for tenant in tenants:
            db_path = os.path.join(str(settings.BASE_DIR), tenant.db_path)
            _run_upgrade_for_tenant(tenant.id, db_path)

        print("[migrate_all_tenants] Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
