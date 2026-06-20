"""
main.py – FastAPI application entry point.

Start: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import init_master_db, init_tenant_db
from app.routers import auth, chat, consent, documents, health, obligations, relationships, reminders, tenants
from app.services.scheduler import create_scheduler


def _seed_default_tenant():
    """Ensure the default tenant and its admin user exist in master.db."""
    from app.core.security import get_password_hash
    from app.db.database import MasterSessionLocal
    from app.models.master import Tenant, TenantUser

    db = MasterSessionLocal()
    try:
        tenant_id = settings.DEFAULT_TENANT_ID
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            db.add(
                Tenant(
                    id=tenant_id,
                    name="Local Dev Tenant",
                    db_path=f"tenants/{tenant_id}.db",
                )
            )
            db.commit()
            print(f"[Main] Seeded default tenant: {tenant_id}")

        has_users = db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id).first()
        if not has_users:
            admin_pw = os.getenv("ADMIN_PASSWORD", "admin123")
            db.add(
                TenantUser(
                    tenant_id=tenant_id,
                    username="admin",
                    hashed_password=get_password_hash(admin_pw),
                    role="admin",
                )
            )
            db.commit()
            print(f"[Main] Seeded admin user for {tenant_id}")
    except Exception as e:
        print(f"[Main] Seed warning: {e}")
    finally:
        db.close()


def _seed_uat_tenant():
    """Seed a UAT demo tenant (non-production only). Idempotent.

    Creates tenant `uat-demo` + user `demo`, initialises its tenant DB, and grants
    `vision_extraction` consent so the upload→extract→obligation flow works in UAT
    without the SME having to POST consent first (Admin web has no consent screen).
    Credentials: tenant=`uat-demo`, user=`demo`, password=env UAT_DEMO_PASSWORD
    (default `Khe@UAT2026`).
    """
    if settings.ENVIRONMENT == "production":
        return

    from app.core.security import get_password_hash
    from app.db.database import MasterSessionLocal, get_tenant_session
    from app.models.master import Tenant, TenantUser
    from app.services.consent import check_consent, record_consent

    tenant_id = "uat-demo"
    password = os.getenv("UAT_DEMO_PASSWORD", "Khe@UAT2026")

    db = MasterSessionLocal()
    try:
        if not db.query(Tenant).filter(Tenant.id == tenant_id).first():
            db.add(Tenant(id=tenant_id, name="UAT Demo SME", db_path=f"tenants/{tenant_id}.db"))
            db.commit()
            print(f"[Main] Seeded UAT tenant: {tenant_id}")
        if not db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id, TenantUser.username == "demo"
        ).first():
            db.add(
                TenantUser(
                    tenant_id=tenant_id,
                    username="demo",
                    hashed_password=get_password_hash(password),
                    role="admin",
                )
            )
            db.commit()
            print(f"[Main] Seeded UAT user: demo@{tenant_id}")
    except Exception as e:
        print(f"[Main] UAT seed warning: {e}")
    finally:
        db.close()

    try:
        init_tenant_db(tenant_id)
        tdb = get_tenant_session(tenant_id)
        try:
            if not check_consent(tdb, tenant_id, "vision_extraction"):
                record_consent(
                    tdb, tenant_id, "vision_extraction",
                    actor="uat-seed", consent_text_version="nd13-v1",
                )
                print(f"[Main] Granted vision_extraction consent for {tenant_id}")
        finally:
            tdb.close()
    except Exception as e:
        print(f"[Main] UAT consent seed warning: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------- Startup ----------
    if settings.ENVIRONMENT == "production" and settings.JWT_SECRET == "change-me-in-production":
        raise RuntimeError("JWT_SECRET must be set in production")

    # Ensure runtime data dirs exist (DATA_DIR may be a fresh /opt/khe/data-* path
    # on first deploy after the #87 fix). database.py creates TENANTS_DIR on import.
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[Main] DATA_DIR={settings.DATA_DIR}")
    print("[Main] Initialising databases...")
    init_master_db()
    _seed_default_tenant()
    init_tenant_db(settings.DEFAULT_TENANT_ID)
    _seed_uat_tenant()

    # Boot-time visibility for extraction provider env (NĐ 13: no key VALUES logged).
    # Hits journald so Infra/QC can spot a missing-key deploy without first-upload UX.
    _gem = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    _cla = bool(os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))
    print(
        f"[Main] Extraction providers configured: "
        f"gemini_flash={'yes' if _gem else 'NO'}, "
        f"claude_haiku/sonnet={'yes' if _cla else 'NO'}. "
        + ("" if (_gem or _cla) else
           "WARNING: every upload will status=failed until systemd EnvironmentFile= "
           "loads the .env into the process env (see GET /health/extraction).")
    )

    # Start daily reminder scheduler (#62). Disabled in test environment to avoid
    # AsyncIOScheduler side-effects during test runs.
    if settings.ENVIRONMENT != "test":
        scheduler = create_scheduler()
        scheduler.start()
        app.state.scheduler = scheduler

    yield  # Application runs here

    # ---------- Shutdown ----------
    if hasattr(app.state, "scheduler") and getattr(app.state.scheduler, "running", False):
        app.state.scheduler.shutdown()
    print("[Main] Goodbye.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(consent.router)
app.include_router(documents.ingest_router)
app.include_router(documents.docs_router)
app.include_router(relationships.router)
app.include_router(obligations.router)
app.include_router(reminders.router)
app.include_router(chat.router)
app.include_router(tenants.router)
app.include_router(health.router)


@app.get("/")
def root():
    return {"status": "ok", "message": f"{settings.PROJECT_NAME} is running"}
