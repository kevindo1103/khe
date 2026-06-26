"""POST /documents/{id}/remap-type — clause-remap of doc_type_group (#258).

KHE_AI's remap_type() is mocked (LLM call, no key in CI). Verifies the backend
orchestration: whitelist delete + insert (source="remap"), doc_type_group update,
obligations re-derive, confirm-reset, Event, cost tracking, 409 on empty clauses.
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
from app.models.tenant import Clause, Document, Event, Obligation, Term
from app.routers import documents
from main import app
from modules.extraction import RemapFieldResult, RemapResult, TYPE_SPECIFIC_FIELDS

TENANT = "remap-tenant"
OLD_FIELD = TYPE_SPECIFIC_FIELDS["lao_dong"][0]                 # seeded, must be deleted
NEW_FIELDS = list(TYPE_SPECIFIC_FIELDS["bat_dong_san"][:2])     # remapped in


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Remap Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "ruser").first():
        db.add(TenantUser(tenant_id=TENANT, username="ruser",
                          hashed_password=get_password_hash("rpass"), role="staff"))
        db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "ruser", "password": "rpass"})
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
    for m in (Term, Clause, Obligation, Document, Event):
        db.query(m).filter(m.tenant_id == TENANT).delete()
    db.commit()


def _doc(db, with_clauses=True):
    d = Document(tenant_id=TENANT, file_name="c.pdf", file_path="x/y.pdf", status="extracted")
    db.add(d)
    db.commit()
    db.refresh(d)
    if with_clauses:
        db.add(Clause(tenant_id=TENANT, document_id=d.id, clause_num="Điều 1",
                      title="Đối tượng", content="Bên A cho thuê văn phòng tại 12 Lý Tự Trọng."))
        db.commit()
    return d


def _seed_old_type(db, doc):
    db.add(Term(tenant_id=TENANT, document_id=doc.id, field_name="doc_type_group",
                field_value="lao_dong", source="extracted"))
    db.add(Term(tenant_id=TENANT, document_id=doc.id, field_name=OLD_FIELD,
                field_value="cũ", source="extracted"))
    db.commit()


def _fake_remap(monkeypatch, fields):
    async def _r(clauses, target_type):
        return RemapResult(fields=fields, provider="gemini_flash_text", cost_vnd=2.5, warnings=[])
    monkeypatch.setattr(documents, "remap_type", _r)


def test_remap_clears_old_inserts_new(auth_client, db, monkeypatch):
    _wipe(db)
    doc = _doc(db)
    _seed_old_type(db, doc)
    _fake_remap(monkeypatch, {
        NEW_FIELDS[0]: RemapFieldResult(value="12 Lý Tự Trọng", ref="Điều 1", confidence=0.9, needs_review=False),
        NEW_FIELDS[1]: RemapFieldResult(value=None, ref=None, confidence=0.0, needs_review=True),  # D-08 null row
    })
    r = auth_client.post(f"/documents/{doc.id}/remap-type", json={"doc_type_group": "bat_dong_san"})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["fields_remapped"] == 1   # one value, one null
    assert data["fields_null"] == 1
    assert data["cost_vnd"] == 2.5

    db.expire_all()
    names = {t.field_name: t for t in db.query(Term).filter(Term.document_id == doc.id)}
    assert OLD_FIELD not in names                       # old type-specific cleared
    assert names[NEW_FIELDS[0]].field_value == "12 Lý Tự Trọng"
    assert names[NEW_FIELDS[0]].source == "remap"
    assert names[NEW_FIELDS[0]].ref == "Điều 1"
    assert NEW_FIELDS[1] in names and names[NEW_FIELDS[1]].field_value is None   # null row kept (D-07)
    assert names["doc_type_group"].field_value == "bat_dong_san"   # updated, not duplicated


def test_remap_resets_confirm_and_writes_event(auth_client, db, monkeypatch):
    _wipe(db)
    doc = _doc(db)
    from datetime import datetime
    doc.confirmed_by_user_at = datetime.utcnow()
    db.commit()
    _seed_old_type(db, doc)
    _fake_remap(monkeypatch, {NEW_FIELDS[0]: RemapFieldResult(value="x", confidence=0.8, needs_review=False)})

    auth_client.post(f"/documents/{doc.id}/remap-type", json={"doc_type_group": "bat_dong_san"})
    db.expire_all()
    assert db.query(Document).filter(Document.id == doc.id).one().confirmed_by_user_at is None
    ev = db.query(Event).filter(Event.event_type == "doc_type_corrected", Event.entity_id == doc.id).first()
    assert ev is not None
    assert '"from": "lao_dong"' in ev.payload and '"to": "bat_dong_san"' in ev.payload


def test_remap_tracks_cost(auth_client, db, monkeypatch):
    _wipe(db)
    doc = _doc(db)
    _seed_old_type(db, doc)
    _fake_remap(monkeypatch, {NEW_FIELDS[0]: RemapFieldResult(value="x", confidence=0.8, needs_review=False)})
    auth_client.post(f"/documents/{doc.id}/remap-type", json={"doc_type_group": "bat_dong_san"})
    db.expire_all()
    assert db.query(Document).filter(Document.id == doc.id).one().extraction_cost_vnd == 2.5


def test_remap_409_no_clauses(auth_client, db, monkeypatch):
    _wipe(db)
    doc = _doc(db, with_clauses=False)
    _seed_old_type(db, doc)
    r = auth_client.post(f"/documents/{doc.id}/remap-type", json={"doc_type_group": "bat_dong_san"})
    assert r.status_code == 409
    assert r.json()["detail"]["error"] == "no_clauses"


def test_remap_422_invalid_type(auth_client, db):
    _wipe(db)
    doc = _doc(db)
    r = auth_client.post(f"/documents/{doc.id}/remap-type", json={"doc_type_group": "khong_co_thatj"})
    assert r.status_code == 422


def test_remap_404_other_tenant(auth_client, db):
    _wipe(db)
    r = auth_client.post("/documents/99999/remap-type", json={"doc_type_group": "bat_dong_san"})
    assert r.status_code == 404


def test_remap_requires_auth():
    anon = TestClient(app)
    assert anon.post("/documents/1/remap-type", json={"doc_type_group": "bat_dong_san"}).status_code in (401, 403)
