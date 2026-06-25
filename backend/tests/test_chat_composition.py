"""Chat fallback chain — clause-text fallback before D-08 on entity router miss (#263).

Only `_select_tools` (router) and `_format_answer` are mocked; the fallback
`_tool_search_clauses` runs for real against seeded clauses.
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
from app.models.tenant import Clause, Document
from app.services import chat_query
from main import app

TENANT = "compose-tenant"
_NOT_FOUND = "Không tìm thấy thông tin này trong hồ sơ của bạn."


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Compose Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "cmuser").first():
        db.add(TenantUser(tenant_id=TENANT, username="cmuser",
                          hashed_password=get_password_hash("cmpass"), role="staff"))
        db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "cmuser", "password": "cmpass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session(TENANT)
    try:
        yield d
    finally:
        d.close()


def _wipe(db):
    db.query(Clause).filter(Clause.tenant_id == TENANT).delete()
    db.query(Document).filter(Document.tenant_id == TENANT).delete()
    db.commit()


def _doc_with_clause(db, content):
    doc = Document(tenant_id=TENANT, file_name="d.pdf", file_path="x/y.pdf", status="extracted")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.add(Clause(tenant_id=TENANT, document_id=doc.id, clause_num="Điều 1",
                  title="Đối tượng", content=content))
    db.commit()
    return doc


def _miss_router(monkeypatch):
    """Router 'miss' — selects a structured tool that returns 0 rows."""
    async def _select(*a, **k):
        return [{"name": "search_terms",
                 "args": {"field_name": "ngay_het_han", "doc_hint": "khong_ton_tai",
                          "value_contains": None, "party_filter": None, "doc_type_filter": None}}], {"in": 10, "out": 5}
    monkeypatch.setattr(chat_query, "_select_tools", _select)


def test_fallback_finds_party_when_router_misses(auth_client, db, monkeypatch):
    _wipe(db)
    _doc_with_clause(db, "Bên A cho Penfield Corp thuê văn phòng tại Quận 1.")
    _miss_router(monkeypatch)

    async def _fmt(*a, **k):
        return "Hợp đồng nhắc tới Penfield Corp.", {"in": 0, "out": 0}
    monkeypatch.setattr(chat_query, "_format_answer", _fmt)

    r = auth_client.post("/chat/query", json={"question": "Hợp đồng với Penfield?"})
    data = r.json()
    assert data["found"] is True
    assert data["answer"].startswith("Tìm gần đúng: ")     # disclosed approximate (#263)
    assert any(s["type"] == "clause" for s in data["sources"])


def test_fallback_disabled_when_no_entity_in_query(auth_client, db, monkeypatch):
    _wipe(db)
    _doc_with_clause(db, "Bên A cho Penfield Corp thuê văn phòng.")
    _miss_router(monkeypatch)
    # No proper noun → no fallback → D-08 (don't clause-spam every miss).
    r = auth_client.post("/chat/query", json={"question": "có cái gì sắp hết hạn?"})
    data = r.json()
    assert data["found"] is False
    assert data["answer"] == _NOT_FOUND


def test_fallback_still_emits_d08_if_clauses_empty(auth_client, db, monkeypatch):
    _wipe(db)
    _doc_with_clause(db, "Bên A cho Bên B thuê văn phòng. Không có công ty nào khác.")
    _miss_router(monkeypatch)
    # Entity present in the query but absent from clauses → fallback runs, finds 0 → D-08.
    r = auth_client.post("/chat/query", json={"question": "Hợp đồng với Penfield?"})
    data = r.json()
    assert data["found"] is False
    assert data["answer"] == _NOT_FOUND      # byte-exact D-08 preserved


def test_entity_terms_heuristic():
    f = chat_query._entity_terms
    assert "Penfield" in f("Hợp đồng với Penfield?")
    assert f("có cái gì sắp hết hạn?") == []
    assert f("Có cái gì sắp hết hạn?") == []      # sentence-initial cap ignored
    assert "ALASKA" in f("HĐ với ALASKA năm 2021")
    assert "Danh Việt" in f('HĐ với "Danh Việt"')
