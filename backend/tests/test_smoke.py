import os
import sys

# Ensure backend/ is on path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Seed a test tenant + user before running smoke tests."""
    init_master_db()
    init_tenant_db("test-tenant")

    db = MasterSessionLocal()
    tenant = db.query(Tenant).filter(Tenant.id == "test-tenant").first()
    if not tenant:
        db.add(Tenant(id="test-tenant", name="Test Tenant", db_path="tenants/test-tenant.db"))
        db.commit()

    user = (
        db.query(TenantUser)
        .filter(TenantUser.tenant_id == "test-tenant", TenantUser.username == "testuser")
        .first()
    )
    if not user:
        db.add(
            TenantUser(
                tenant_id="test-tenant",
                username="testuser",
                hashed_password=get_password_hash("testpass"),
                role="staff",
            )
        )
        db.commit()
    db.close()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success():
    response = client.post(
        "/auth/login",
        json={"tenant_id": "test-tenant", "username": "testuser", "password": "testpass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure():
    response = client.post(
        "/auth/login",
        json={"tenant_id": "test-tenant", "username": "testuser", "password": "wrongpass"},
    )
    assert response.status_code == 401


def test_get_tenant_session():
    """get_tenant_session(tid) must return an open Session and create tables."""
    session = get_tenant_session("test-tenant")
    assert session is not None
    # Quick sanity: query something that will fail if tables are missing
    from app.models.tenant import Document
    result = session.query(Document).first()
    session.close()
