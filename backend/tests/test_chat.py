"""Chat query MVP tests (#27).

- D-06: retrieve-only
- D-08: not-found fallback
- Tenant isolation
"""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document, Obligation, Term
from main import app


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db("chat-tenant")

    db = MasterSessionLocal()
    tenant = db.query(Tenant).filter(Tenant.id == "chat-tenant").first()
    if not tenant:
        db.add(Tenant(id="chat-tenant", name="Chat Tenant", db_path="tenants/chat-tenant.db"))
        db.commit()

    user = db.query(TenantUser).filter(TenantUser.tenant_id == "chat-tenant", TenantUser.username == "chatuser").first()
    if not user:
        db.add(
            TenantUser(
                tenant_id="chat-tenant",
                username="chatuser",
                hashed_password=get_password_hash("chatpass"),
                role="staff",
            )
        )
        db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post(
        "/auth/login",
        json={"tenant_id": "chat-tenant", "username": "chatuser", "password": "chatpass"},
    )
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session("chat-tenant")
    try:
        yield d
    finally:
        d.close()


def _seed(db):
    doc = Document(tenant_id="chat-tenant", file_name="lease_2026.pdf", file_path="x/y.pdf", status="extracted")
    db.add(doc)
    db.commit()
    db.refresh(doc)

    term_due = Term(
        tenant_id="chat-tenant",
        document_id=doc.id,
        field_name="ngay_het_han",
        field_value="2026-12-31",
        confidence=0.9,
    )
    term_start = Term(
        tenant_id="chat-tenant",
        document_id=doc.id,
        field_name="ngay_hieu_luc",
        field_value="2026-01-01",
        confidence=0.9,
    )
    term_duration = Term(
        tenant_id="chat-tenant",
        document_id=doc.id,
        field_name="thoi_han_hd",
        field_value="12 tháng",
        confidence=0.9,
    )
    term_party = Term(
        tenant_id="chat-tenant",
        document_id=doc.id,
        field_name="doi_tac",
        field_value="Công ty A",
        confidence=0.9,
    )
    db.add_all([term_due, term_start, term_duration, term_party])

    ob = Obligation(
        tenant_id="chat-tenant",
        document_id=doc.id,
        description="Hợp đồng lease_2026.pdf hết hạn ngày 2026-12-31",
        obligation_type="once",
        due_date="2026-12-31",
        status="pending",
    )
    db.add(ob)
    db.commit()
    return doc


class TestChatQuery:
    def _assert_source_shape(self, source):
        assert "type" in source
        assert "document_id" in source
        assert "file_name" in source
        assert "field_name" in source
        assert "value" in source

    def test_expiry_from_obligation(self, auth_client, db):
        doc = _seed(db)

        r = auth_client.post("/chat/query", json={"question": "hợp đồng lease_2026 hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert "2026-12-31" in data["answer"]
        assert any(s["type"] == "obligation" for s in data["sources"])
        for s in data["sources"]:
            self._assert_source_shape(s)
            assert s["file_name"] == "lease_2026.pdf"

    def test_expiry_fallback_to_term(self, auth_client, db):
        doc = Document(tenant_id="chat-tenant", file_name="fallback.pdf", file_path="x/y.pdf", status="extracted")
        db.add(doc)
        db.commit()
        db.refresh(doc)
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=doc.id,
                field_name="ngay_het_han",
                field_value="2027-06-30",
                confidence=0.9,
            )
        )
        db.commit()

        r = auth_client.post("/chat/query", json={"question": "hợp đồng fallback hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert "2027-06-30" in data["answer"]
        for s in data["sources"]:
            self._assert_source_shape(s)
            assert s["file_name"] == "fallback.pdf"

    def test_d_08_not_found(self, auth_client, db):
        _seed(db)

        r = auth_client.post("/chat/query", json={"question": "hợp đồng không_tồn_tại hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert "Không tìm thấy" in data["answer"]

    def test_d_08_no_guess(self, auth_client, db):
        doc = Document(tenant_id="chat-tenant", file_name="noinfo.pdf", file_path="x/y.pdf", status="extracted")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        r = auth_client.post("/chat/query", json={"question": "hợp đồng noinfo hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert "Không tìm thấy" in data["answer"]

    def test_d_08_no_hint_multiple_docs(self, auth_client, db):
        """Without a document hint and >1 extracted docs, the engine must not guess."""
        _seed(db)
        doc2 = Document(tenant_id="chat-tenant", file_name="second.pdf", file_path="x/y.pdf", status="extracted")
        db.add(doc2)
        db.commit()

        r = auth_client.post("/chat/query", json={"question": "hợp đồng hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert "Không tìm thấy" in data["answer"]

    def test_cross_tenant_isolation(self, auth_client, db):
        _seed(db)
        init_tenant_db("other-chat-tenant")

        mdb = MasterSessionLocal()
        if not mdb.query(Tenant).filter(Tenant.id == "other-chat-tenant").first():
            mdb.add(Tenant(id="other-chat-tenant", name="Other", db_path="tenants/other-chat-tenant.db"))
            mdb.commit()
        if not mdb.query(TenantUser).filter(TenantUser.tenant_id == "other-chat-tenant", TenantUser.username == "otherchatuser").first():
            mdb.add(
                TenantUser(
                    tenant_id="other-chat-tenant",
                    username="otherchatuser",
                    hashed_password=get_password_hash("otherchatpass"),
                    role="staff",
                )
            )
            mdb.commit()
        mdb.close()

        other = TestClient(app)
        other.post(
            "/auth/login",
            json={"tenant_id": "other-chat-tenant", "username": "otherchatuser", "password": "otherchatpass"},
        )

        r = other.post("/chat/query", json={"question": "hợp đồng lease_2026 hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert "Không tìm thấy" in data["answer"]

    def test_start_date_intent(self, auth_client, db):
        _seed(db)

        r = auth_client.post("/chat/query", json={"question": "hợp đồng lease_2026 có hiệu lực từ khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert "2026-01-01" in data["answer"]
        for s in data["sources"]:
            self._assert_source_shape(s)

    def test_duration_intent(self, auth_client, db):
        _seed(db)

        r = auth_client.post("/chat/query", json={"question": "hợp đồng lease_2026 thời hạn bao lâu?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert "12 tháng" in data["answer"]
        for s in data["sources"]:
            self._assert_source_shape(s)

    def test_parties_intent(self, auth_client, db):
        _seed(db)

        r = auth_client.post("/chat/query", json={"question": "hợp đồng lease_2026 đối tác là ai?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert "Công ty A" in data["answer"]
        for s in data["sources"]:
            self._assert_source_shape(s)

    def test_status_intent(self, auth_client, db):
        _seed(db)

        r = auth_client.post("/chat/query", json={"question": "hợp đồng lease_2026 trạng thái gì?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert "extracted" in data["answer"]
        for s in data["sources"]:
            self._assert_source_shape(s)
