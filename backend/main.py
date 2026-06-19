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
from app.routers import auth, consent, documents, health, obligations, relationships


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------- Startup ----------
    if settings.ENVIRONMENT == "production" and settings.JWT_SECRET == "change-me-in-production":
        raise RuntimeError("JWT_SECRET must be set in production")

    print("[Main] Initialising databases...")
    init_master_db()
    _seed_default_tenant()
    init_tenant_db(settings.DEFAULT_TENANT_ID)

    yield  # Application runs here

    # ---------- Shutdown ----------
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
app.include_router(health.router)


@app.get("/")
def root():
    return {"status": "ok", "message": f"{settings.PROJECT_NAME} is running"}
