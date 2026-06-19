"""KHE_QC — M0+M1 smoke fixtures (#76).

Per CLAUDE.md §Multi-Tenant DB: every test that touches tenant data MUST go
through `get_tenant_session(tid)` — never `SessionLocal()` directly.

Strategy:
- Session-scoped: tmp dir for master.db + tenants/ + storage/.
- 2 isolated tenants seeded for D-10 cross-tenant assertions:
  - `tenant-a` / user `alice` / `alice-pass` — has `vision_extraction` consent.
  - `tenant-b` / user `bob`   / `bob-pass`   — has `vision_extraction` consent.
- `tenant-noconsent` / user `noc` / `noc-pass` — NO consent (for H-block tests).
- Per-test teardown wipes documents/terms/obligations/events but keeps tenants
  + users (faster than re-init each test).

NOTE — scaffolded by QC lead per PM directive (2026-06-19). Test bodies are
Windsurf_QC scope; this file provides only the wiring + Tier-1 fixtures.
"""
import os
import shutil
import sys
from pathlib import Path

import pytest

# Force ENVIRONMENT=test BEFORE importing app modules so scheduler stays off
# (main.py:lifespan gates AsyncIOScheduler on ENVIRONMENT != "test").
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod")

# Add backend/ to sys.path (mirrors existing test_smoke.py pattern).
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)


# ── Settings override (session-scoped, applied before app import) ──────────
@pytest.fixture(scope="session", autouse=True)
def _redirect_settings_paths(tmp_path_factory):
    """Redirect master.db / tenants/ / storage/ to a tmp dir so tests never
    pollute the repo working tree.

    Direct attribute mutation on the `settings` singleton (pydantic-settings
    BaseSettings instance is mutable). No MonkeyPatch wrapper — mixing
    session-scope MonkeyPatch with function-scope fixtures triggers a pytest
    finalizer ordering bug.
    """
    from app.core.config import settings
    from app.db import database as db_module

    test_root: Path = tmp_path_factory.mktemp("khe-test")
    tenants_dir = test_root / "tenants"
    storage_dir = test_root / "storage"
    tenants_dir.mkdir(parents=True, exist_ok=True)
    storage_dir.mkdir(parents=True, exist_ok=True)

    original = {
        "TENANTS_DIR": settings.TENANTS_DIR,
        "MASTER_DB_URL": settings.MASTER_DB_URL,
        "STORAGE_DIR": getattr(settings, "STORAGE_DIR", None),
        "db_module_TENANTS_DIR": db_module.TENANTS_DIR,
    }
    settings.TENANTS_DIR = tenants_dir
    settings.MASTER_DB_URL = f"sqlite:///{test_root / 'master.db'}"
    if hasattr(settings, "STORAGE_DIR"):
        # STORAGE_DIR introduced by #54 (ingest). Defensive — not on main yet.
        settings.STORAGE_DIR = storage_dir
    db_module.TENANTS_DIR = tenants_dir
    db_module._engine_cache.clear()

    yield test_root

    settings.TENANTS_DIR = original["TENANTS_DIR"]
    settings.MASTER_DB_URL = original["MASTER_DB_URL"]
    if original["STORAGE_DIR"] is not None:
        settings.STORAGE_DIR = original["STORAGE_DIR"]
    db_module.TENANTS_DIR = original["db_module_TENANTS_DIR"]
    db_module._engine_cache.clear()
    shutil.rmtree(test_root, ignore_errors=True)


# ── Master DB + tenant seed (session-scoped) ───────────────────────────────
@pytest.fixture(scope="session")
def seeded_tenants(_redirect_settings_paths):
    """Initialise master.db + 3 isolated tenant DBs with users + consent state.

    Returns: dict[str, dict] keyed by tenant_id with {user, password, role}.
    """
    from app.core.security import get_password_hash
    from app.db.database import MasterSessionLocal, init_master_db, init_tenant_db
    from app.models.master import Tenant, TenantUser

    init_master_db()

    seeds = {
        "tenant-a": {"user": "alice", "password": "alice-pass", "role": "admin"},
        "tenant-b": {"user": "bob",   "password": "bob-pass",   "role": "admin"},
        "tenant-noconsent": {"user": "noc", "password": "noc-pass", "role": "admin"},
    }
    db = MasterSessionLocal()
    try:
        for tid, info in seeds.items():
            if not db.query(Tenant).filter(Tenant.id == tid).first():
                db.add(Tenant(id=tid, name=tid, db_path=f"tenants/{tid}.db"))
            if not db.query(TenantUser).filter(
                TenantUser.tenant_id == tid, TenantUser.username == info["user"]
            ).first():
                db.add(TenantUser(
                    tenant_id=tid,
                    username=info["user"],
                    hashed_password=get_password_hash(info["password"]),
                    role=info["role"],
                ))
        db.commit()
    finally:
        db.close()

    for tid in seeds:
        init_tenant_db(tid)

    # TODO(Windsurf_QC): seed consent rows for tenant-a + tenant-b
    # (vision_extraction granted), leave tenant-noconsent without consent.
    # Reference: app.services.consent.grant_consent() once #22 lands.

    return seeds


# ── HTTP client (function-scoped — fresh state per test) ───────────────────
@pytest.fixture
def client(seeded_tenants):
    """FastAPI TestClient with lifespan executed.

    `with TestClient(app)` triggers startup (init_master_db, UAT seed) — that's
    fine, our session-scoped redirect already isolated paths.
    """
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_cookie(client, seeded_tenants):
    """Return a callable that logs in and yields the session cookie.

    Usage:
        cookie = auth_cookie("tenant-a", "alice", "alice-pass")
        client.get("/auth/me", cookies={"khe_session": cookie})
    """
    def _login(tenant_id: str, username: str, password: str) -> str:
        r = client.post(
            "/auth/login",
            json={"tenant_id": tenant_id, "username": username, "password": password},
        )
        assert r.status_code == 200, f"Seed login failed: {r.status_code} {r.text}"
        return r.cookies["khe_session"]

    return _login


# ── Per-test teardown — wipe tenant data tables ────────────────────────────
@pytest.fixture(autouse=True)
def _wipe_tenant_data(seeded_tenants):
    """After each test, clear documents/terms/obligations/events from every
    tenant DB so tests don't bleed into each other. Keeps Tenants + Users.
    """
    yield
    from app.db.database import get_tenant_session
    from app.models.tenant import Document, Event, Term

    for tid in seeded_tenants:
        s = get_tenant_session(tid)
        try:
            s.query(Term).delete()
            s.query(Event).delete()
            s.query(Document).delete()
            # TODO(Windsurf_QC): add Obligation, Relationship, Consent once models confirmed.
            s.commit()
        finally:
            s.close()
