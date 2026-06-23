"""Tests for self-party endpoints (#155, DEC-030).

- PATCH /tenants/me/legal_name — JWT-scoped upsert TenantProfile
- POST /documents/{doc_id}/confirm_self_party — re-derive direction
- parties[] persist in extraction_runner (idempotent)
- parties[] in GET /documents/{doc_id} response
- Tenant isolation (D-10)
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.db.database import MasterSessionLocal, get_tenant_session
from app.models.master import TenantProfile
from app.models.tenant import Document, Obligation, Party
from tests.conftest import (
    FakeVisionProvider,
    make_extraction_result,
)
from modules.extraction import DocType, PartyItem


class TestLegalNameEndpoint:
    """PATCH /tenants/me/legal_name — JWT-scoped upsert."""

    def test_legal_name_upsert_create(self, auth_client, test_tenant):
        """First call creates TenantProfile row."""
        r = auth_client.patch("/tenants/me/legal_name", json={"legal_name": "Công ty ABC"})
        assert r.status_code == 200
        assert r.json() == {"ok": True, "legal_name": "Công ty ABC"}

        db = MasterSessionLocal()
        profile = db.query(TenantProfile).filter(TenantProfile.tenant_id == test_tenant).first()
        assert profile is not None
        assert profile.legal_name == "Công ty ABC"
        db.close()

    def test_legal_name_upsert_update(self, auth_client, test_tenant):
        """Second call updates existing TenantProfile row."""
        # First call
        auth_client.patch("/tenants/me/legal_name", json={"legal_name": "Công ty ABC"})
        # Second call — update
        r = auth_client.patch("/tenants/me/legal_name", json={"legal_name": "Công ty XYZ"})
        assert r.status_code == 200
        assert r.json()["legal_name"] == "Công ty XYZ"

        db = MasterSessionLocal()
        profile = db.query(TenantProfile).filter(TenantProfile.tenant_id == test_tenant).first()
        assert profile.legal_name == "Công ty XYZ"
        db.close()

    def test_legal_name_requires_auth(self):
        """Unauthenticated request → 401."""
        c = TestClient(__import__("main").app)
        r = c.patch("/tenants/me/legal_name", json={"legal_name": "Test"})
        assert r.status_code == 401

    def test_get_legal_name_null_when_unset(self, auth_client, test_tenant):
        """GET returns legal_name=null when TenantProfile row not yet created (#176)."""
        r = auth_client.get("/tenants/me/legal_name")
        assert r.status_code == 200
        assert r.json() == {"ok": True, "legal_name": None}

    def test_get_legal_name_after_patch(self, auth_client, test_tenant):
        """GET returns current legal_name after PATCH upsert (#176)."""
        auth_client.patch("/tenants/me/legal_name", json={"legal_name": "Công ty ABC"})
        r = auth_client.get("/tenants/me/legal_name")
        assert r.status_code == 200
        assert r.json() == {"ok": True, "legal_name": "Công ty ABC"}

    def test_get_legal_name_requires_auth(self):
        """Unauthenticated GET → 401."""
        c = TestClient(__import__("main").app)
        r = c.get("/tenants/me/legal_name")
        assert r.status_code == 401


class TestConfirmSelfParty:
    """POST /documents/{doc_id}/confirm_self_party — re-derive direction."""

    def test_confirm_rederive_direction(self, auth_client, test_tenant, db):
        """User selects role_label → obligations get direction re-derived."""
        doc = Document(
            tenant_id=test_tenant,
            file_name="test_confirm.pdf",
            file_path=f"{test_tenant}/test_confirm.pdf",
            doc_type="hd_thue",
            status="extracted",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Seed obligations with obligor but no direction
        ob1 = Obligation(
            tenant_id=test_tenant, document_id=doc.id,
            description="Trả tiền thuê", obligor="Bên A",
            direction=None, status="pending",
        )
        ob2 = Obligation(
            tenant_id=test_tenant, document_id=doc.id,
            description="Giao nhà", obligor="Bên B",
            direction=None, status="pending",
        )
        ob3 = Obligation(
            tenant_id=test_tenant, document_id=doc.id,
            description="Không rõ", obligor=None,
            direction=None, status="pending",
        )
        db.add_all([ob1, ob2, ob3])
        db.commit()

        # User says "I am Bên A"
        r = auth_client.post(
            f"/documents/{doc.id}/confirm_self_party",
            json={"role_label": "Bên A"},
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True
        assert r.json()["updated"] == 2  # ob1 + ob2 changed, ob3 stays null

        db.refresh(ob1)
        db.refresh(ob2)
        db.refresh(ob3)
        assert ob1.direction == "nghĩa_vụ"   # obligor == selected role
        assert ob2.direction == "quyền_lợi"   # obligor != selected role
        assert ob3.direction is None           # obligor is None → D-08

    def test_confirm_self_party_404(self, auth_client, db):
        """Non-existent doc → 404."""
        r = auth_client.post("/documents/99999/confirm_self_party", json={"role_label": "Bên A"})
        assert r.status_code == 404

    def test_confirm_self_party_requires_auth(self):
        """Unauthenticated → 401."""
        c = TestClient(__import__("main").app)
        r = c.post("/documents/1/confirm_self_party", json={"role_label": "Bên A"})
        assert r.status_code == 401


class TestPartiesPersist:
    """parties[] persistence in extraction_runner (idempotent)."""

    def test_parties_persisted_on_extraction(self, auth_client, test_tenant, db, monkeypatch):
        """After extraction, parties[] rows exist in DB."""
        from app.services import extraction_runner

        doc = Document(
            tenant_id=test_tenant,
            file_name="parties_test.pdf",
            file_path=f"{test_tenant}/parties_test.pdf",
            doc_type="hd_thue",
            status="pending",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Create a fake file
        from app.core.config import settings
        file_path = settings.STORAGE_DIR / doc.file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(b"%PDF-1.4 fake")

        result = make_extraction_result(
            parties=[
                PartyItem(name="Công ty A", role_label="Bên A"),
                PartyItem(name="Công ty B", role_label="Bên B"),
            ]
        )
        monkeypatch.setattr(
            extraction_runner, "get_extraction_provider",
            lambda: FakeVisionProvider(result),
        )

        extraction_runner.run_extraction(doc.id, test_tenant)

        parties = db.query(Party).filter(
            Party.document_id == doc.id,
            Party.tenant_id == test_tenant,
        ).all()
        assert len(parties) == 2
        names = {p.name for p in parties}
        assert names == {"Công ty A", "Công ty B"}
        roles = {p.role_label for p in parties}
        assert roles == {"Bên A", "Bên B"}

    def test_parties_idempotent_on_re_extraction(self, auth_client, test_tenant, db, monkeypatch):
        """Re-extraction replaces parties, not duplicates."""
        from app.services import extraction_runner

        doc = Document(
            tenant_id=test_tenant,
            file_name="reextract_test.pdf",
            file_path=f"{test_tenant}/reextract_test.pdf",
            doc_type="hd_thue",
            status="pending",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        from app.core.config import settings
        file_path = settings.STORAGE_DIR / doc.file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(b"%PDF-1.4 fake")

        result1 = make_extraction_result(
            parties=[PartyItem(name="Công ty A", role_label="Bên A")]
        )
        monkeypatch.setattr(
            extraction_runner, "get_extraction_provider",
            lambda: FakeVisionProvider(result1),
        )
        extraction_runner.run_extraction(doc.id, test_tenant)

        # Verify 1 party
        parties = db.query(Party).filter(Party.document_id == doc.id).all()
        assert len(parties) == 1

        # Re-extract with different parties
        result2 = make_extraction_result(
            parties=[
                PartyItem(name="Công ty C", role_label="Lessor"),
                PartyItem(name="Công ty D", role_label="Lessee"),
            ]
        )
        monkeypatch.setattr(
            extraction_runner, "get_extraction_provider",
            lambda: FakeVisionProvider(result2),
        )
        extraction_runner.run_extraction(doc.id, test_tenant)

        db.expire_all()
        parties = db.query(Party).filter(Party.document_id == doc.id).all()
        assert len(parties) == 2  # replaced, not 3
        names = {p.name for p in parties}
        assert names == {"Công ty C", "Công ty D"}


class TestPartiesInGetDocument:
    """parties[] in GET /documents/{doc_id} response."""

    def test_parties_in_detail_response(self, auth_client, test_tenant, db):
        """GET /documents/{id} returns parties[] array."""
        doc = Document(
            tenant_id=test_tenant,
            file_name="detail_parties.pdf",
            file_path=f"{test_tenant}/detail_parties.pdf",
            doc_type="hd_thue",
            status="extracted",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        db.add(Party(tenant_id=test_tenant, document_id=doc.id, name="Công ty A", role_label="Bên A"))
        db.add(Party(tenant_id=test_tenant, document_id=doc.id, name="Công ty B", role_label="Bên B"))
        db.commit()

        r = auth_client.get(f"/documents/{doc.id}")
        assert r.status_code == 200
        data = r.json()
        assert "parties" in data
        assert len(data["parties"]) == 2
        party_names = {p["name"] for p in data["parties"]}
        assert party_names == {"Công ty A", "Công ty B"}

    def test_parties_empty_when_none(self, auth_client, test_tenant, db):
        """GET /documents/{id} returns empty parties[] when no parties."""
        doc = Document(
            tenant_id=test_tenant,
            file_name="no_parties.pdf",
            file_path=f"{test_tenant}/no_parties.pdf",
            doc_type="hd_thue",
            status="extracted",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        r = auth_client.get(f"/documents/{doc.id}")
        assert r.status_code == 200
        assert r.json()["parties"] == []


class TestTenantIsolation:
    """D-10: cross-tenant isolation for self-party endpoints."""

    def test_legal_name_tenant_isolated(self, test_tenant):
        """Tenant A's legal_name not visible to Tenant B."""
        import uuid
        from app.db.database import init_tenant_db
        from app.core.security import get_password_hash
        from app.models.master import Tenant, TenantUser

        other_id = f"iso-party-{uuid.uuid4().hex[:8]}"
        init_master_db = __import__("app.db.database", fromlist=["init_master_db"]).init_master_db
        init_master_db()
        init_tenant_db(other_id)

        mdb = MasterSessionLocal()
        mdb.add(Tenant(id=other_id, name="Other", db_path=f"tenants/{other_id}.db"))
        mdb.add(TenantUser(
            tenant_id=other_id, username="otheruser",
            hashed_password=get_password_hash("otherpass"), role="admin",
        ))
        mdb.commit()
        mdb.close()

        # Tenant A sets legal_name
        c_a = TestClient(__import__("main").app)
        r = c_a.post("/auth/login", json={"tenant_id": test_tenant, "username": "qcuser", "password": "qcpass"})
        assert r.status_code == 200
        c_a.patch("/tenants/me/legal_name", json={"legal_name": "Tenant A Name"})

        # Tenant B sets legal_name
        c_b = TestClient(__import__("main").app)
        r = c_b.post("/auth/login", json={"tenant_id": other_id, "username": "otheruser", "password": "otherpass"})
        assert r.status_code == 200
        c_b.patch("/tenants/me/legal_name", json={"legal_name": "Tenant B Name"})

        # Verify A's profile is not B's
        mdb = MasterSessionLocal()
        a_profile = mdb.query(TenantProfile).filter(TenantProfile.tenant_id == test_tenant).first()
        b_profile = mdb.query(TenantProfile).filter(TenantProfile.tenant_id == other_id).first()
        assert a_profile.legal_name == "Tenant A Name"
        assert b_profile.legal_name == "Tenant B Name"
        assert a_profile.legal_name != b_profile.legal_name
        mdb.close()

        # Cleanup
        from tests.conftest import _reset_tenant_db
        _reset_tenant_db(other_id)
        mdb = MasterSessionLocal()
        mdb.query(TenantUser).filter(TenantUser.tenant_id == other_id).delete()
        mdb.query(TenantProfile).filter(TenantProfile.tenant_id == other_id).delete()
        mdb.query(Tenant).filter(Tenant.id == other_id).delete()
        mdb.commit()
        mdb.close()

    def test_confirm_self_party_cross_tenant_404(self, auth_client, test_tenant, db):
        """Tenant A cannot confirm self-party on Tenant B's document."""
        import uuid
        from app.db.database import init_tenant_db
        from tests.conftest import _reset_tenant_db
        from app.core.security import get_password_hash
        from app.models.master import Tenant, TenantUser

        other_id = f"iso-doc-{uuid.uuid4().hex[:8]}"
        init_master_db = __import__("app.db.database", fromlist=["init_master_db"]).init_master_db
        init_master_db()
        init_tenant_db(other_id)

        mdb = MasterSessionLocal()
        mdb.add(Tenant(id=other_id, name="Other", db_path=f"tenants/{other_id}.db"))
        mdb.add(TenantUser(
            tenant_id=other_id, username="otheruser",
            hashed_password=get_password_hash("otherpass"), role="admin",
        ))
        mdb.commit()
        mdb.close()

        # Create doc in other tenant
        odb = get_tenant_session(other_id)
        other_doc = Document(
            tenant_id=other_id, file_name="other.pdf",
            file_path=f"{other_id}/other.pdf", doc_type="hd_thue", status="extracted",
        )
        odb.add(other_doc)
        odb.commit()
        odb.refresh(other_doc)
        other_doc_id = other_doc.id
        odb.close()

        # Tenant A tries to confirm self-party on Tenant B's doc
        r = auth_client.post(
            f"/documents/{other_doc_id}/confirm_self_party",
            json={"role_label": "Bên A"},
        )
        assert r.status_code == 404  # Not found in A's tenant

        # Cleanup
        from tests.conftest import _reset_tenant_db
        _reset_tenant_db(other_id)
        mdb = MasterSessionLocal()
        mdb.query(TenantUser).filter(TenantUser.tenant_id == other_id).delete()
        mdb.query(Tenant).filter(Tenant.id == other_id).delete()
        mdb.commit()
        mdb.close()
