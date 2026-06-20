"""Chat query tests (DEC-026 / #27).

- D-06: retrieve-only
- D-08: not-found fallback
- Tenant isolation
- LLM function-calling paths are mocked so CI stays green without API key.
"""
import os
import sys
from datetime import date

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

    def test_search_obligations_due_range(self, auth_client, db, monkeypatch):
        """search_obligations filters by inclusive due_from/due_to range."""
        doc = _seed(db)
        # Add obligations outside the target range.
        db.add_all(
            [
                Obligation(
                    tenant_id="chat-tenant",
                    document_id=doc.id,
                    description="Hợp đồng hết hạn tháng 6",
                    obligation_type="once",
                    due_date="2026-06-15",
                    status="pending",
                ),
                Obligation(
                    tenant_id="chat-tenant",
                    document_id=doc.id,
                    description="Hợp đồng hết hạn tháng 7",
                    obligation_type="once",
                    due_date="2026-07-20",
                    status="pending",
                ),
                Obligation(
                    tenant_id="chat-tenant",
                    document_id=doc.id,
                    description="Hợp đồng hết hạn tháng 8",
                    obligation_type="once",
                    due_date="2026-08-10",
                    status="pending",
                ),
            ]
        )
        db.commit()

        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools(
                [{"name": "search_obligations", "args": {"due_within_days": None, "status": None, "doc_hint": None, "due_from": "2026-07-01", "due_to": "2026-07-31"}}]
            ),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Có 1 hợp đồng hết hạn tháng 7."))

        r = auth_client.post("/chat/query", json={"question": "HĐ nào hết hạn tháng 7?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        values = [s["value"] for s in data["sources"] if s["type"] == "obligation"]
        assert "2026-07-20" in values
        assert "2026-06-15" not in values
        assert "2026-08-10" not in values

    def test_search_obligations_due_range_inclusive(self, auth_client, db, monkeypatch):
        """Boundary due_from and due_to dates are inclusive."""
        doc = _seed(db)
        db.add(
            Obligation(
                tenant_id="chat-tenant",
                document_id=doc.id,
                description="Boundary",
                obligation_type="once",
                due_date="2026-06-01",
                status="pending",
            )
        )
        db.commit()

        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools(
                [{"name": "search_obligations", "args": {"due_within_days": None, "status": None, "doc_hint": None, "due_from": "2026-06-01", "due_to": "2026-06-01"}}]
            ),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Có 1 hợp đồng."))

        r = auth_client.post("/chat/query", json={"question": "HĐ hết hạn ngày 2026-06-01?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert any(s["type"] == "obligation" and s["value"] == "2026-06-01" for s in data["sources"])

    def test_search_obligations_due_range_and_status_and_doc_hint(self, auth_client, db, monkeypatch):
        """due_from + due_to + status + doc_hint are AND-composed."""
        doc = _seed(db)
        db.add(
            Obligation(
                tenant_id="chat-tenant",
                document_id=doc.id,
                description="Matching",
                obligation_type="once",
                due_date="2026-06-15",
                status="pending",
            )
        )
        db.add(
            Obligation(
                tenant_id="chat-tenant",
                document_id=doc.id,
                description="Wrong status",
                obligation_type="once",
                due_date="2026-06-15",
                status="done",
            )
        )
        db.commit()

        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools(
                [{"name": "search_obligations", "args": {"due_within_days": None, "status": "pending", "doc_hint": "lease_2026", "due_from": "2026-06-01", "due_to": "2026-06-30"}}]
            ),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Có 1 pending."))

        r = auth_client.post("/chat/query", json={"question": "HĐ lease_2026 pending hết hạn tháng 6?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        sources = [s for s in data["sources"] if s["type"] == "obligation"]
        assert len(sources) == 1
        assert sources[0]["value"] == "2026-06-15"
        assert sources[0]["status"] == "pending"

    def test_select_tools_prompt_includes_today_date(self):
        """Router system prompt must include today's date and calendar-range rules."""
        prompt = chat_query._build_router_system_prompt(date(2026, 6, 20))
        assert "Hôm nay là 2026-06-20" in prompt
        assert "due_from" in prompt
        assert "due_to" in prompt
        assert "tháng này" in prompt
        assert "quý sau" in prompt

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

    def test_search_terms_value_contains(self, auth_client, db, monkeypatch):
        """search_terms value_contains finds party data across documents by value substring."""
        doc = _seed(db)
        # Add a second doc with a different party to prove cross-document search.
        doc2 = Document(tenant_id="chat-tenant", file_name="second.pdf", file_path="x/y.pdf", status="extracted")
        db.add(doc2)
        db.commit()
        db.refresh(doc2)
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=doc2.id,
                field_name="doi_tac",
                field_value="CÔNG TY CỔ PHẦN ĐẦU TƯ ĐỊA ỐC ALASKA",
                confidence=0.9,
            )
        )
        db.commit()

        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools(
                [{"name": "search_terms", "args": {"field_name": "doi_tac", "doc_hint": None, "value_contains": "ALASKA"}}]
            ),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Có hợp đồng với ALASKA."))

        r = auth_client.post("/chat/query", json={"question": "Hợp đồng nào có đối tác là CÔNG TY CỔ PHẦN ĐẦU TƯ ĐỊA ỐC ALASKA?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        sources = [s for s in data["sources"] if s["type"] == "term" and "ALASKA" in s["value"]]
        assert sources
        assert any(s["file_name"] == "second.pdf" for s in sources)

    def test_search_terms_value_contains_cross_tenant_isolation(self, auth_client, db, monkeypatch):
        """value_contains must not match terms in another tenant."""
        # chat-tenant has ALASKA; other-tenant has a different party. Querying as other-tenant must return D-08.
        _seed(db)
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=db.query(Document).filter(Document.tenant_id == "chat-tenant", Document.file_name == "lease_2026.pdf").first().id,
                field_name="doi_tac",
                field_value="CÔNG TY CỔ PHẦN ĐẦU TƯ ĐỊA ỐC ALASKA",
                confidence=0.9,
            )
        )
        db.commit()

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

        # Seed a different party in the other tenant.
        other_db = get_tenant_session("other-chat-tenant")
        try:
            other_doc = Document(tenant_id="other-chat-tenant", file_name="other.pdf", file_path="x/y.pdf", status="extracted")
            other_db.add(other_doc)
            other_db.commit()
            other_db.refresh(other_doc)
            other_db.add(
                Term(
                    tenant_id="other-chat-tenant",
                    document_id=other_doc.id,
                    field_name="doi_tac",
                    field_value="CÔNG TY B",
                    confidence=0.9,
                )
            )
            other_db.commit()
        finally:
            other_db.close()

        other = TestClient(app)
        other.post(
            "/auth/login",
            json={"tenant_id": "other-chat-tenant", "username": "otherchatuser", "password": "otherchatpass"},
        )

        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools(
                [{"name": "search_terms", "args": {"field_name": "doi_tac", "doc_hint": None, "value_contains": "ALASKA"}}]
            ),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer(""))

        r = other.post("/chat/query", json={"question": "Hợp đồng nào có đối tác ALASKA?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert "Không tìm thấy" in data["answer"]

    def test_party_filter_returns_field_for_docs_matching_party(self, auth_client, db, monkeypatch):
        """party_filter pre-filters docs by doi_tac, then returns requested field with provenance."""
        _seed(db)
        # chat-tenant lease_2026.pdf has doi_tac "Công ty A" by default from _seed.
        # Add a second doc with ALASKA party and an ngay_hieu_luc term.
        doc2 = Document(tenant_id="chat-tenant", file_name="alaska_lease.pdf", file_path="x/y.pdf", status="extracted")
        db.add(doc2)
        db.commit()
        db.refresh(doc2)
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=doc2.id,
                field_name="doi_tac",
                field_value="CÔNG TY CỔ PHẦN ĐẦU TƯ ĐỊA ỐC ALASKA",
                confidence=0.9,
            )
        )
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=doc2.id,
                field_name="ngay_hieu_luc",
                field_value="2024-01-15",
                confidence=0.9,
            )
        )
        db.commit()

        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools(
                [{"name": "search_terms", "args": {"field_name": "ngay_hieu_luc", "doc_hint": None, "value_contains": None, "party_filter": "ALASKA"}}]
            ),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Hợp đồng với ALASKA có hiệu lực từ 2024-01-15."))

        r = auth_client.post("/chat/query", json={"question": "Ngày hiệu lực của hợp đồng với ALASKA?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert any(s["type"] == "term" and s["field_name"] == "ngay_hieu_luc" and s["value"] == "2024-01-15" and s["file_name"] == "alaska_lease.pdf" for s in data["sources"])

    def test_party_filter_no_match_returns_d08(self, auth_client, db, monkeypatch):
        """party_filter with no matching party returns D-08."""
        _seed(db)
        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools(
                [{"name": "search_terms", "args": {"field_name": "ngay_hieu_luc", "doc_hint": None, "value_contains": None, "party_filter": "NONEXISTENT"}}]
            ),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer(""))

        r = auth_client.post("/chat/query", json={"question": "Ngày hiệu lực của hợp đồng với NONEXISTENT?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert data["answer"] == "Không tìm thấy thông tin này trong hồ sơ của bạn."

    def test_party_filter_escapes_like_wildcards(self, auth_client, db, monkeypatch):
        """A literal % or _ in party_filter must not broaden the match."""
        _seed(db)
        # Add a doc whose party value actually contains a literal percent.
        doc2 = Document(tenant_id="chat-tenant", file_name="pct_lease.pdf", file_path="x/y.pdf", status="extracted")
        db.add(doc2)
        db.commit()
        db.refresh(doc2)
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=doc2.id,
                field_name="doi_tac",
                field_value="50% ALASKA",
                confidence=0.9,
            )
        )
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=doc2.id,
                field_name="ngay_hieu_luc",
                field_value="2024-02-01",
                confidence=0.9,
            )
        )
        db.commit()

        # Search for the literal "%" — should NOT match rows that simply have any characters.
        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools(
                [{"name": "search_terms", "args": {"field_name": "ngay_hieu_luc", "doc_hint": None, "value_contains": None, "party_filter": "%"}}]
            ),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer(""))

        r = auth_client.post("/chat/query", json={"question": "Ngày hiệu lực HĐ với đối tác chứa %?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert any(s["file_name"] == "pct_lease.pdf" for s in data["sources"])

        # Search for "_" literal — should NOT match every single-char party.
        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools(
                [{"name": "search_terms", "args": {"field_name": "ngay_hieu_luc", "doc_hint": None, "value_contains": None, "party_filter": "_"}}]
            ),
        )
        r = auth_client.post("/chat/query", json={"question": "Ngày hiệu lực HĐ với đối tác chứa _?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False

    def test_party_filter_cross_tenant_isolation(self, auth_client, db, monkeypatch):
        """party_filter must not match party data in another tenant."""
        _seed(db)
        doc2 = Document(tenant_id="chat-tenant", file_name="alaska_lease.pdf", file_path="x/y.pdf", status="extracted")
        db.add(doc2)
        db.commit()
        db.refresh(doc2)
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=doc2.id,
                field_name="doi_tac",
                field_value="CÔNG TY CỔ PHẦN ĐẦU TƯ ĐỊA ỐC ALASKA",
                confidence=0.9,
            )
        )
        db.commit()

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
            _mock_select_tools(
                [{"name": "search_terms", "args": {"field_name": "ngay_hieu_luc", "doc_hint": None, "value_contains": None, "party_filter": "ALASKA"}}]
            ),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer(""))

        r = other.post("/chat/query", json={"question": "Ngày hiệu lực HĐ với ALASKA?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert "Không tìm thấy" in data["answer"]

    def test_party_filter_and_value_contains_compose(self, auth_client, db, monkeypatch):
        """value_contains AND party_filter compose together (both filter the same result)."""
        _seed(db)
        doc2 = Document(tenant_id="chat-tenant", file_name="alaska_lease.pdf", file_path="x/y.pdf", status="extracted")
        db.add(doc2)
        db.commit()
        db.refresh(doc2)
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=doc2.id,
                field_name="doi_tac",
                field_value="CÔNG TY CỔ PHẦN ĐẦU TƯ ĐỊA ỐC ALASKA",
                confidence=0.9,
            )
        )
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=doc2.id,
                field_name="ngay_hieu_luc",
                field_value="2024-01-15",
                confidence=0.9,
            )
        )
        # Another ALASKA doc with a different ngay_hieu_luc that should be excluded by value_contains.
        doc3 = Document(tenant_id="chat-tenant", file_name="alaska_lease_2025.pdf", file_path="x/y.pdf", status="extracted")
        db.add(doc3)
        db.commit()
        db.refresh(doc3)
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=doc3.id,
                field_name="doi_tac",
                field_value="CÔNG TY CỔ PHẦN ĐẦU TƯ ĐỊA ỐC ALASKA",
                confidence=0.9,
            )
        )
        db.add(
            Term(
                tenant_id="chat-tenant",
                document_id=doc3.id,
                field_name="ngay_hieu_luc",
                field_value="2025-01-15",
                confidence=0.9,
            )
        )
        db.commit()

        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools(
                [{"name": "search_terms", "args": {"field_name": "ngay_hieu_luc", "doc_hint": None, "value_contains": "2024", "party_filter": "ALASKA"}}]
            ),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer(""))

        r = auth_client.post("/chat/query", json={"question": "Ngày hiệu lực năm 2024 của hợp đồng với ALASKA?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert any(s["file_name"] == "alaska_lease.pdf" for s in data["sources"])
        assert not any(s["file_name"] == "alaska_lease_2025.pdf" for s in data["sources"])


class TestDocumentClauseCount:
    def test_clause_count_in_detail(self, auth_client, db):
        doc = _seed(db)

        r = auth_client.get(f"/documents/{doc.id}")
        assert r.status_code == 200
        data = r.json()
        assert data["clause_count"] == 1
