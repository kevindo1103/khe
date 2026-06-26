"""Consent service + endpoint tests (NĐ 13/2023, DEC-010)."""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, init_master_db, init_tenant_db, get_tenant_session
from app.models.master import Tenant, TenantUser
from app.services.consent import (
    check_consent,
    check_extraction_consent,
    record_consent,
    revoke_consent,
    VALID_PURPOSES,
)
from main import app


client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Seed a test tenant + user before running consent tests."""
    init_master_db()
    init_tenant_db("consent-tenant")

    db = MasterSessionLocal()
    tenant = db.query(Tenant).filter(Tenant.id == "consent-tenant").first()
    if not tenant:
        db.add(Tenant(id="consent-tenant", name="Consent Tenant", db_path="tenants/consent-tenant.db"))
        db.commit()

    user = (
        db.query(TenantUser)
        .filter(TenantUser.tenant_id == "consent-tenant", TenantUser.username == "consentuser")
        .first()
    )
    if not user:
        db.add(
            TenantUser(
                tenant_id="consent-tenant",
                username="consentuser",
                hashed_password=get_password_hash("consentpass"),
                role="staff",
            )
        )
        db.commit()
    db.close()


@pytest.fixture
def tenant_db():
    """Yield a tenant-scoped session, auto-close."""
    session = get_tenant_session("consent-tenant")
    try:
        yield session
    finally:
        session.close()


# ── Service tests ──

class TestConsentService:
    def test_check_consent_absent(self, tenant_db):
        assert check_consent(tenant_db, "consent-tenant", "vision_extraction") is False

    def test_record_and_check_consent(self, tenant_db):
        event = record_consent(
            tenant_db,
            "consent-tenant",
            "vision_extraction",
            actor="consentuser",
            entity_id=1,
        )
        assert event.consent_reference is not None
        assert event.consent_text_version == "nd13-v1"
        assert check_consent(tenant_db, "consent-tenant", "vision_extraction") is True

    def test_revoke_consent(self, tenant_db):
        revoke_consent(tenant_db, "consent-tenant", "vision_extraction", actor="consentuser", entity_id=1)
        assert check_consent(tenant_db, "consent-tenant", "vision_extraction") is False

    def test_re_grant_consent(self, tenant_db):
        record_consent(tenant_db, "consent-tenant", "vision_extraction", actor="consentuser", entity_id=1)
        assert check_consent(tenant_db, "consent-tenant", "vision_extraction") is True

    def test_check_extraction_consent(self, tenant_db):
        # "vision_extraction" is the only purpose for this wrapper
        assert check_extraction_consent(tenant_db, "consent-tenant") is True

    def test_invalid_purpose_raises(self, tenant_db):
        with pytest.raises(ValueError, match="Invalid purpose"):
            record_consent(tenant_db, "consent-tenant", "bad_purpose", actor="x", entity_id=1)

    def test_purposes_are_isolated(self, tenant_db):
        """Consent for reminder_send is independent of vision_extraction."""
        # vision_extraction is granted (from above tests)
        assert check_consent(tenant_db, "consent-tenant", "vision_extraction") is True
        # reminder_send is not
        assert check_consent(tenant_db, "consent-tenant", "reminder_send") is False


# ── Endpoint tests ──

class TestConsentEndpoints:
    @pytest.fixture
    def auth_client(self):
        """Login and yield a client with the khe_session cookie set."""
        c = TestClient(app)
        r = c.post(
            "/auth/login",
            json={"tenant_id": "consent-tenant", "username": "consentuser", "password": "consentpass"},
        )
        assert r.status_code == 200
        return c

    def test_post_consent(self, auth_client):
        r = auth_client.post("/consent", json={"purpose": "vision_extraction"})
        assert r.status_code == 201
        data = r.json()
        assert data["purpose"] == "vision_extraction"
        assert data["status"] == "granted"
        assert data["consent_reference"]

    def test_post_consent_invalid_purpose(self, auth_client):
        r = auth_client.post("/consent", json={"purpose": "bad_purpose"})
        assert r.status_code == 422

    def test_get_consents(self, auth_client):
        r = auth_client.get("/consent")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        purposes = {item["purpose"] for item in data}
        assert purposes == VALID_PURPOSES
        vision = next(item for item in data if item["purpose"] == "vision_extraction")
        assert vision["status"] == "granted"

    def test_post_revoke(self, auth_client):
        r = auth_client.post("/consent/revoke", json={"purpose": "vision_extraction"})
        assert r.status_code == 200
        data = r.json()
        assert data["purpose"] == "vision_extraction"
        assert data["status"] == "revoked"

        # After revoke, GET shows none for vision_extraction
        r2 = auth_client.get("/consent")
        vision = next(item for item in r2.json() if item["purpose"] == "vision_extraction")
        assert vision["status"] == "none"

    def test_no_cookie_401(self):
        anon = TestClient(app)
        r = anon.post("/consent", json={"purpose": "vision_extraction"})
        assert r.status_code == 401

    def test_get_me_after_login(self, auth_client):
        r = auth_client.get("/auth/me")
        assert r.status_code == 200
        assert r.json()["username"] == "consentuser"
