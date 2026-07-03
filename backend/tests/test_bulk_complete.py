"""Tests for #471: bulk complete endpoint, penalty obligation_type, self-party alias fix."""
import json
import os
import sys
from datetime import datetime

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document, Obligation, Party
from app.services.directions import _self_party_strings
from main import app

TENANT_ID = "bulk-tenant"
OTHER_TENANT_ID = "bulk-other-tenant"
FULFILLED_AT = "2026-07-03T10:00:00"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT_ID)
    init_tenant_db(OTHER_TENANT_ID)

    db = MasterSessionLocal()
    for tid, name in [(TENANT_ID, "Bulk Tenant"), (OTHER_TENANT_ID, "Bulk Other Tenant")]:
        if not db.query(Tenant).filter(Tenant.id == tid).first():
            db.add(Tenant(id=tid, name=name, db_path=f"tenants/{tid}.db"))
    db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT_ID, TenantUser.username == "bulkuser").first():
        db.add(TenantUser(
            tenant_id=TENANT_ID, username="bulkuser",
            hashed_password=get_password_hash("bulkpass"), role="staff",
        ))
    if not db.query(TenantUser).filter(TenantUser.tenant_id == OTHER_TENANT_ID, TenantUser.username == "otheruser").first():
        db.add(TenantUser(
            tenant_id=OTHER_TENANT_ID, username="otheruser",
            hashed_password=get_password_hash("otherpass"), role="staff",
        ))
    db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT_ID, "username": "bulkuser", "password": "bulkpass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def other_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": OTHER_TENANT_ID, "username": "otheruser", "password": "otherpass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def tenant_db():
    db = get_tenant_session(TENANT_ID)
    yield db
    db.close()


def _seed_doc(db, tid=TENANT_ID) -> Document:
    doc = Document(
        tenant_id=tid, file_name="HD.pdf", file_path=f"{tid}/HD.pdf",
        doc_type="service", status="extracted",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _seed_obligation(db, doc_id, tid=TENANT_ID, ob_type="payment") -> Obligation:
    ob = Obligation(
        tenant_id=tid, document_id=doc_id, description="Thanh toán",
        obligation_type=ob_type, status="pending",
    )
    db.add(ob)
    db.commit()
    db.refresh(ob)
    return ob


# ── Bulk complete endpoint ──

def test_bulk_complete_done(auth_client, tenant_db):
    doc = _seed_doc(tenant_db)
    doc_id = doc.id
    ob1 = _seed_obligation(tenant_db, doc_id)
    ob2 = _seed_obligation(tenant_db, doc_id)
    ob1_id, ob2_id = ob1.id, ob2.id

    r = auth_client.patch("/obligations/bulk", json={
        "ids": [ob1_id, ob2_id],
        "status": "done",
        "fulfilled_at": FULFILLED_AT,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["updated"] == 2
    assert data["skipped"] == 0
    assert all(i["ok"] for i in data["items"])

    tenant_db.expire_all()
    for ob_id in [ob1_id, ob2_id]:
        ob = tenant_db.query(Obligation).filter(Obligation.id == ob_id).first()
        assert ob.status == "done"
        assert ob.fulfilled_at is not None


def test_bulk_complete_cancelled(auth_client, tenant_db):
    doc = _seed_doc(tenant_db)
    ob = _seed_obligation(tenant_db, doc.id)
    ob_id = ob.id

    r = auth_client.patch("/obligations/bulk", json={"ids": [ob_id], "status": "cancelled"})
    assert r.status_code == 200
    data = r.json()
    assert data["updated"] == 1
    tenant_db.expire_all()
    assert tenant_db.query(Obligation).filter(Obligation.id == ob_id).first().status == "cancelled"


def test_bulk_complete_done_requires_fulfilled_at(auth_client, tenant_db):
    doc = _seed_doc(tenant_db)
    ob = _seed_obligation(tenant_db, doc.id)
    ob_id = ob.id

    r = auth_client.patch("/obligations/bulk", json={"ids": [ob_id], "status": "done"})
    assert r.status_code == 400
    assert "fulfilled_at" in r.json()["detail"]


def test_bulk_complete_invalid_status(auth_client, tenant_db):
    doc = _seed_doc(tenant_db)
    ob = _seed_obligation(tenant_db, doc.id)
    ob_id = ob.id

    r = auth_client.patch("/obligations/bulk", json={
        "ids": [ob_id], "status": "pending",
    })
    assert r.status_code == 400


def test_bulk_complete_empty_ids(auth_client):
    r = auth_client.patch("/obligations/bulk", json={"ids": [], "status": "cancelled"})
    assert r.status_code == 200
    data = r.json()
    assert data["updated"] == 0
    assert data["skipped"] == 0


def test_bulk_complete_tenant_isolation(auth_client, other_client, tenant_db):
    """Bulk endpoint must not mutate obligations in other tenants.

    Per-tenant DB architecture means IDs can collide across separate SQLite files,
    so we assert non-leakage of the other tenant's 'secret' data rather than
    asserting updated==0 (which would fail when IDs happen to match).
    """
    other_db = get_tenant_session(OTHER_TENANT_ID)
    try:
        other_doc = _seed_doc(other_db, OTHER_TENANT_ID)
        other_ob = Obligation(
            tenant_id=OTHER_TENANT_ID,
            document_id=other_doc.id,
            description="BÍ MẬT TENANT KHÁC",
            obligation_type="payment",
            status="pending",
        )
        other_db.add(other_ob)
        other_db.commit()
        other_ob_id = other_ob.id
    finally:
        other_db.close()

    # auth_client (bulk-tenant) attempts to cancel by that ID
    r = auth_client.patch("/obligations/bulk", json={
        "ids": [other_ob_id], "status": "cancelled",
    })
    assert r.status_code == 200

    # The other tenant's obligation must remain "pending" — never cancelled by bulk-tenant
    other_db2 = get_tenant_session(OTHER_TENANT_ID)
    try:
        ob = other_db2.query(Obligation).filter(
            Obligation.id == other_ob_id,
            Obligation.tenant_id == OTHER_TENANT_ID,
        ).first()
        assert ob is not None
        assert ob.status == "pending", "other tenant obligation must not be mutated"
    finally:
        other_db2.close()


def test_bulk_complete_mixed_found_not_found(auth_client, tenant_db):
    doc = _seed_doc(tenant_db)
    ob = _seed_obligation(tenant_db, doc.id)
    ob_id = ob.id
    nonexistent_id = 999999

    r = auth_client.patch("/obligations/bulk", json={
        "ids": [ob_id, nonexistent_id], "status": "cancelled",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["updated"] == 1
    assert data["skipped"] == 1
    ok_items = [i for i in data["items"] if i["ok"]]
    skip_items = [i for i in data["items"] if not i["ok"]]
    assert len(ok_items) == 1
    assert len(skip_items) == 1
    assert skip_items[0]["id"] == nonexistent_id


def test_bulk_complete_logs_event_per_item(auth_client, tenant_db):
    """Each updated obligation gets its own Event (D-07/FR-OB-04 audit granularity)."""
    from app.models.tenant import Event
    doc = _seed_doc(tenant_db)
    ob1 = _seed_obligation(tenant_db, doc.id)
    ob2 = _seed_obligation(tenant_db, doc.id)
    ob1_id, ob2_id = ob1.id, ob2.id

    r = auth_client.patch("/obligations/bulk", json={
        "ids": [ob1_id, ob2_id],
        "status": "done",
        "fulfilled_at": FULFILLED_AT,
    })
    assert r.status_code == 200

    for ob_id in [ob1_id, ob2_id]:
        events = tenant_db.query(Event).filter(
            Event.entity_type == "obligation",
            Event.entity_id == ob_id,
            Event.event_type == "updated",
        ).all()
        assert len(events) >= 1, f"obligation {ob_id} must have an Event"
        payloads = [json.loads(e.payload) for e in events if e.payload]
        assert any(p.get("bulk") is True for p in payloads)


# ── penalty obligation_type ──

def test_penalty_obligation_type_stored_and_retrieved(tenant_db):
    doc = _seed_doc(tenant_db)
    ob = _seed_obligation(tenant_db, doc.id, ob_type="penalty")
    ob_id = ob.id
    tenant_db.expunge(ob)

    loaded = tenant_db.query(Obligation).filter(Obligation.id == ob_id).first()
    assert loaded.obligation_type == "penalty"


def test_penalty_obligation_type_via_api(auth_client, tenant_db):
    doc = _seed_doc(tenant_db)
    ob = Obligation(
        tenant_id=TENANT_ID, document_id=doc.id, description="Phạt vi phạm",
        obligation_type="penalty", status="pending",
    )
    tenant_db.add(ob)
    tenant_db.commit()
    ob_id = ob.id

    r = auth_client.get(f"/obligations/?page=1&page_size=100")
    assert r.status_code == 200
    items = r.json()["items"]
    match = [i for i in items if i["id"] == ob_id]
    assert match
    assert match[0]["obligation_type"] == "penalty"


# ── Self-party alias fix (directions.py) ──

def test_self_party_strings_includes_aliases(tenant_db):
    """_self_party_strings must match when legal_name equals a Party alias (not canonical name)."""
    doc = _seed_doc(tenant_db)
    doc_id = doc.id

    party = Party(
        tenant_id=TENANT_ID,
        document_id=doc_id,
        name="Công ty TNHH Phát Triển Phần Mềm ABC",
        role_label="Bên A",
        aliases=json.dumps(["ABC Tech", "ABC Software"]),
    )
    tenant_db.add(party)
    tenant_db.commit()

    # legal_name matches alias "ABC Tech", not the canonical name
    result = _self_party_strings(tenant_db, TENANT_ID, doc_id, "ABC Tech")
    assert result, "should find self-party via alias match"
    assert "ben a" in result or "abc tech" in result


def test_self_party_strings_alias_no_false_positive(tenant_db):
    """Alias match on one party does not pollute non-matching parties."""
    doc = _seed_doc(tenant_db)
    doc_id = doc.id

    party = Party(
        tenant_id=TENANT_ID,
        document_id=doc_id,
        name="Đối Tác XYZ",
        role_label="Bên B",
        aliases=json.dumps(["XYZ Ltd"]),
    )
    tenant_db.add(party)
    tenant_db.commit()

    result = _self_party_strings(tenant_db, TENANT_ID, doc_id, "ABC Tech")
    assert "ben b" not in result


def test_self_party_strings_null_aliases_still_works(tenant_db):
    """Parties without aliases still match by canonical name."""
    doc = _seed_doc(tenant_db)
    doc_id = doc.id

    party = Party(
        tenant_id=TENANT_ID,
        document_id=doc_id,
        name="Công ty Mẫu",
        role_label="Bên A",
        aliases=None,
    )
    tenant_db.add(party)
    tenant_db.commit()

    result = _self_party_strings(tenant_db, TENANT_ID, doc_id, "Công ty Mẫu")
    assert result
    assert "ben a" in result


def test_self_party_strings_corrupt_aliases_graceful(tenant_db):
    """Corrupt JSON in aliases column is silently skipped — no crash."""
    doc = _seed_doc(tenant_db)
    doc_id = doc.id

    party = Party(
        tenant_id=TENANT_ID,
        document_id=doc_id,
        name="Công ty Lỗi",
        role_label="Bên A",
        aliases="not-valid-json{{",
    )
    tenant_db.add(party)
    tenant_db.commit()

    # Should not raise; falls back to canonical name match only
    result = _self_party_strings(tenant_db, TENANT_ID, doc_id, "Công ty Lỗi")
    assert "ben a" in result
