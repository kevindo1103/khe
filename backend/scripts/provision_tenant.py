#!/usr/bin/env python3
"""
Provision a new tenant on production/staging.

Usage (from backend/ directory on VPS):
    python scripts/provision_tenant.py \
        --slug tran-thai-cam-ranh \
        --name "Công ty Cổ phần Trần Thái Cam Ranh" \
        --username admin \
        --role admin \
        --plan pilot

Password is prompted interactively — never passed as CLI arg or logged.
"""
import argparse
import getpass
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, init_tenant_db
from app.models.master import Tenant, TenantUser


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision a new Khế tenant")
    parser.add_argument("--slug", required=True, help="Tenant ID slug (e.g. tran-thai-cam-ranh)")
    parser.add_argument("--name", required=True, help="Display name")
    parser.add_argument("--username", default="admin", help="Initial user username")
    parser.add_argument("--role", default="admin", choices=["admin", "manager", "staff"])
    parser.add_argument("--plan", default="pilot", help="Plan tier")
    args = parser.parse_args()

    db = MasterSessionLocal()
    try:
        existing = db.query(Tenant).filter(Tenant.id == args.slug).first()
        if existing:
            print(f"[ERROR] Tenant '{args.slug}' already exists. Aborting.")
            sys.exit(1)

        password = getpass.getpass(f"Password for {args.username}@{args.slug}: ")
        if not password or len(password) < 6:
            print("[ERROR] Password must be at least 6 characters.")
            sys.exit(1)
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("[ERROR] Passwords do not match.")
            sys.exit(1)

        tenant = Tenant(
            id=args.slug,
            name=args.name,
            db_path=f"tenants/{args.slug}.db",
            plan=args.plan,
            is_active=True,
            journey_stage="NEW",
        )
        db.add(tenant)

        user = TenantUser(
            tenant_id=args.slug,
            username=args.username,
            hashed_password=get_password_hash(password),
            role=args.role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"[OK] Tenant '{args.slug}' created in master.db")
        print(f"[OK] User '{args.username}' (role={args.role}) created")

        settings.TENANTS_DIR.mkdir(parents=True, exist_ok=True)
        init_tenant_db(args.slug)
        print(f"[OK] Per-tenant DB created: tenants/{args.slug}.db")

        print(f"\n✓ Tenant provisioned. Verify with:")
        print(f"  curl -X POST https://<host>/auth/login \\")
        print(f'    -H "Content-Type: application/json" \\')
        print(f'    -d \'{{"tenant_id": "{args.slug}", "username": "{args.username}", "password": "***"}}\'')
    finally:
        db.close()


if __name__ == "__main__":
    main()
