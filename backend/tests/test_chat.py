"""Chat query tests (DEC-026 / #27).

- D-06: retrieve-only
- D-08: not-found fallback
- Tenant isolation
- LLM function-calling paths are mocked so CI stays green without API key.
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
from app.models.tenant import Clause, Document, Obligation, Term
from app.services import chat_query
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

    clause = Clause(
        tenant_id="chat-tenant",
        document_id=doc.id,
        clause_num="Điều 8",
        title="Chấm dứt hợp đồng",
        content="Bên thuê phải thông báo chấm dứt hợp đồng trước 30 ngày.",
        page_num=5,
    )
    db.add(clause)
    db.commit()
    return doc


def _mock_select_tools(calls):
    """Return an async function that yields the given tool_calls."""
    async def _select(*args, **kwargs):
        return calls

    return _select


def _mock_format_answer(answer):
    """Return an async function that yields the canned answer."""
    async def _format(*args, **kwargs):
        return answer

    return _format


class TestChatQuery:
    def _assert_source_shape(self, source):
        assert "type" in source
        assert "document_id" in source
        assert "file_name" in source
        assert "field_name" in source
        assert "value" in source

    def test_d_08_no_tools(self, auth_client, db, monkeypatch):
        """When the LLM selects no tools, D-08 not-found must fire."""
        _seed(db)
        monkeypatch.setattr(chat_query, "_select_tools", _mock_select_tools([]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer(""))

        r = auth_client.post("/chat/query", json={"question": "hợp đồng lease_2026 hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert data["answer"] == "Không tìm thấy thông tin này trong hồ sơ của bạn."
        assert data["sources"] == []

    def test_search_terms_tool(self, auth_client, db, monkeypatch):
        """search_terms returns extracted term values with provenance."""
        doc = _seed(db)
        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools([{"name": "search_terms", "args": {"field_name": "ngay_het_han", "doc_hint": "lease_2026"}}]),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Hợp đồng lease_2026.pdf hết hạn ngày 2026-12-31."))

        r = auth_client.post("/chat/query", json={"question": "hợp đồng lease_2026 hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert "2026-12-31" in data["answer"]
        assert any(s["type"] == "term" and s["field_name"] == "ngay_het_han" for s in data["sources"])
        for s in data["sources"]:
            self._assert_source_shape(s)
            assert s["file_name"] == "lease_2026.pdf"

    def test_search_obligations_tool(self, auth_client, db, monkeypatch):
        """search_obligations returns pending/overdue obligations."""
        doc = _seed(db)
        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools([{"name": "search_obligations", "args": {"due_within_days": 365, "status": "pending", "doc_hint": None}}]),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Có 1 hợp đồng sắp hết hạn."))

        r = auth_client.post("/chat/query", json={"question": "HĐ nào hết hạn trong 365 ngày?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert any(s["type"] == "obligation" and s["field_name"] == "due_date" for s in data["sources"])
        for s in data["sources"]:
            self._assert_source_shape(s)

    def test_search_clauses_tool(self, auth_client, db, monkeypatch):
        """search_clauses returns clause content with clause_num + clause_title."""
        doc = _seed(db)
        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools([{"name": "search_clauses", "args": {"query": "chấm dứt", "doc_hint": "lease_2026"}}]),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Thông báo trước 30 ngày."))

        r = auth_client.post("/chat/query", json={"question": "hợp đồng lease_2026 điều khoản chấm dứt nói gì?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        clause_sources = [s for s in data["sources"] if s["type"] == "clause"]
        assert clause_sources
        assert clause_sources[0]["clause_num"] == "Điều 8"
        assert clause_sources[0]["clause_title"] == "Chấm dứt hợp đồng"
        assert "30 ngày" in clause_sources[0]["value"]
        for s in data["sources"]:
            self._assert_source_shape(s)

    def test_d_08_tools_return_empty(self, auth_client, db, monkeypatch):
        """Tools selected but empty results → D-08."""
        _seed(db)
        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools([{"name": "search_terms", "args": {"field_name": "gia_tri_hd", "doc_hint": "lease_2026"}}]),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer(""))

        r = auth_client.post("/chat/query", json={"question": "hợp đồng lease_2026 giá trị bao nhiêu?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert "Không tìm thấy" in data["answer"]

    def test_cross_tenant_isolation(self, auth_client, db, monkeypatch):
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

        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools([{"name": "search_terms", "args": {"field_name": "ngay_het_han", "doc_hint": "lease_2026"}}]),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer(""))

        r = other.post("/chat/query", json={"question": "hợp đồng lease_2026 hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert "Không tìm thấy" in data["answer"]

    def test_llm_unavailable_select_tools_returns_empty(self, auth_client, db, monkeypatch):
        """When the LLM client cannot be created, tool selection returns [] → D-08."""
        _seed(db)
        monkeypatch.setattr(chat_query, "_get_llm_client", lambda: None)

        r = auth_client.post("/chat/query", json={"question": "hợp đồng lease_2026 hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert data["answer"] == "Không tìm thấy thông tin này trong hồ sơ của bạn."

    def test_llm_format_failure_uses_deterministic_fallback(self, auth_client, db, monkeypatch):
        """When the LLM formatter fails, the endpoint still returns data from tool results."""
        _seed(db)
        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools([{"name": "search_terms", "args": {"field_name": "ngay_het_han", "doc_hint": "lease_2026"}}]),
        )
        monkeypatch.setattr(chat_query, "_get_llm_client", lambda: None)

        r = auth_client.post("/chat/query", json={"question": "hợp đồng lease_2026 hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert "2026-12-31" in data["answer"]
        assert any(s["type"] == "term" for s in data["sources"])


class TestDocumentClauseCount:
    def test_clause_count_in_detail(self, auth_client, db):
        doc = _seed(db)

        r = auth_client.get(f"/documents/{doc.id}")
        assert r.status_code == 200
        data = r.json()
        assert data["clause_count"] == 1
