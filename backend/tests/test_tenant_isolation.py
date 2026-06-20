"""Bidirectional 2-tenant HTTP isolation test (#77 verification + lock).

Proves `get_db` binds the per-tenant engine from the authenticated cookie
(request.state.tenant_id set by get_current_user), NOT a shared default tenant.
If get_db pooled to DEFAULT_TENANT_ID, tenant A would see tenant B's rows (or
neither would see their own) and these assertions would fail.

Seeds each tenant's data DIRECTLY via get_tenant_session(<tid>) (writes to that
tenant's .db file), then reads back over HTTP (which routes through get_db). The
only way the HTTP reads succeed for own-data AND 404/empty for cross-data is if
get_db bound to the correct per-tenant DB.
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
from app.services import chat_query
from main import app


_TENANTS = {
    "iso-a": {"user": "user-a", "pw": "pass-a", "file": "contract_A.pdf", "due": "2026-03-01"},
    "iso-b": {"user": "user-b", "pw": "pass-b", "file": "contract_B.pdf", "due": "2027-09-15"},
}


def _reset_tenant_db(tid: str):
    """Drop this module's tenant DB so the fixture is hermetic regardless of
    state accumulated by earlier test modules in the same pytest session."""
    from app.db.database import TENANTS_DIR, _engine_cache, _cache_lock

    with _cache_lock:
        eng = _engine_cache.pop(tid, None)
    if eng is not None:
        eng.dispose()
    for suffix in ("", "-wal", "-shm"):
        f = TENANTS_DIR / f"{tid}.db{suffix}"
        try:
            f.unlink()
        except FileNotFoundError:
            pass


@pytest.fixture(scope="module", autouse=True)
def setup_two_tenants():
    init_master_db()
    for tid in _TENANTS:
        _reset_tenant_db(tid)
    db = MasterSessionLocal()
    for tid, cfg in _TENANTS.items():
        init_tenant_db(tid)
        if not db.query(Tenant).filter(Tenant.id == tid).first():
            db.add(Tenant(id=tid, name=tid, db_path=f"tenants/{tid}.db"))
            db.commit()
        if not db.query(TenantUser).filter(
            TenantUser.tenant_id == tid, TenantUser.username == cfg["user"]
        ).first():
            db.add(TenantUser(
                tenant_id=tid, username=cfg["user"],
                hashed_password=get_password_hash(cfg["pw"]), role="admin",
            ))
            db.commit()
    db.close()

    # Seed one document + term + obligation per tenant, written DIRECTLY to each
    # tenant's own .db via get_tenant_session. Explicit, distinct doc ids so the
    # cross-tenant by-id lookup is a genuine 404 (autoincrement alone gives both
    # tenants id=1 in their separate .db files — which would itself prove
    # isolation, but makes a by-id 404 assertion ambiguous).
    explicit_id = {"iso-a": 5001, "iso-b": 5002}
    ids = {}
    for tid, cfg in _TENANTS.items():
        s = get_tenant_session(tid)
        did = explicit_id[tid]
        doc = Document(id=did, tenant_id=tid, file_name=cfg["file"], file_path=f"{tid}/x.pdf", status="extracted")
        s.add(doc)
        s.commit()
        s.add(Term(tenant_id=tid, document_id=did, field_name="ngay_het_han", field_value=cfg["due"], confidence=0.9))
        s.add(Obligation(
            tenant_id=tid, document_id=did, description=f"Hết hạn {cfg['file']}",
            recurrence="once", due_date=cfg["due"], status="pending",
        ))
        s.commit()
        ids[tid] = did
        s.close()
    return ids


def _login(tid):
    c = TestClient(app)
    cfg = _TENANTS[tid]
    r = c.post("/auth/login", json={"tenant_id": tid, "username": cfg["user"], "password": cfg["pw"]})
    assert r.status_code == 200
    return c


def test_each_tenant_sees_only_own_documents(setup_two_tenants):
    ids = setup_two_tenants
    for tid in _TENANTS:
        c = _login(tid)
        files = {d["file_name"] for d in c.get("/documents").json()["items"]}
        assert files == {_TENANTS[tid]["file"]}, f"{tid} sees {files}"


def test_cross_tenant_document_detail_404(setup_two_tenants):
    ids = setup_two_tenants
    a = _login("iso-a")
    # iso-a must NOT be able to read iso-b's document by id (and vice versa).
    assert a.get(f"/documents/{ids['iso-b']}").status_code == 404
    assert a.get(f"/documents/{ids['iso-b']}/file").status_code == 404
    b = _login("iso-b")
    assert b.get(f"/documents/{ids['iso-a']}").status_code == 404


def test_each_tenant_sees_only_own_obligations(setup_two_tenants):
    for tid in _TENANTS:
        c = _login(tid)
        descs = {o["description"] for o in c.get("/obligations").json()["items"]}
        assert descs == {f"Hết hạn {_TENANTS[tid]['file']}"}, f"{tid} sees {descs}"


def _mock_select_tools(question: str, tenant_id: str, db):
    """For each tenant, only resolve the tool call if the document belongs to that tenant."""
    for tid, cfg in _TENANTS.items():
        if cfg["file"] in question:
            if tenant_id == tid:
                return [{"name": "search_terms", "args": {"field_name": "ngay_het_han", "doc_hint": cfg["file"]}}]
            return []
    return []


async def _select_tools_mock(db, tenant_id, question):
    return _mock_select_tools(question, tenant_id, db)


async def _format_answer_mock(question, results):
    return results[0]["value"] if results else ""


def test_chat_does_not_cross_tenant(setup_two_tenants, monkeypatch):
    monkeypatch.setattr(chat_query, "_select_tools", _select_tools_mock)
    monkeypatch.setattr(chat_query, "_format_answer", _format_answer_mock)

    # iso-a asks about iso-b's document by name → must be not-found (D-08), never B's data.
    a = _login("iso-a")
    r = a.post("/chat/query", json={"question": f"hợp đồng {_TENANTS['iso-b']['file']} hết hạn khi nào?"})
    data = r.json()
    assert data["found"] is False
    assert "Không tìm thấy" in data["answer"]
    # iso-a asking about its OWN document resolves.
    r2 = a.post("/chat/query", json={"question": f"hợp đồng {_TENANTS['iso-a']['file']} hết hạn khi nào?"})
    assert r2.json()["found"] is True
    assert _TENANTS["iso-a"]["due"] in r2.json()["answer"]
