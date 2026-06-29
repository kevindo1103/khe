"""Signature persistence tests (#368, R5b)."""
import json
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document
from main import app

TENANT_ID = "sig-tenant"
OTHER_TENANT_ID = "sig-other-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT_ID)
    init_tenant_db(OTHER_TENANT_ID)

    db = MasterSessionLocal()
    for tid, name in [(TENANT_ID, "Sig Tenant"), (OTHER_TENANT_ID, "Sig Other Tenant")]:
        if not db.query(Tenant).filter(Tenant.id == tid).first():
            db.add(Tenant(id=tid, name=name, db_path=f"tenants/{tid}.db"))
    db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT_ID, TenantUser.username == "siguser").first():
        db.add(TenantUser(
            tenant_id=TENANT_ID, username="siguser",
            hashed_password=get_password_hash("sigpass"), role="staff",
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
    r = c.post("/auth/login", json={"tenant_id": TENANT_ID, "username": "siguser", "password": "sigpass"})
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


def _seed_doc(db, tid=TENANT_ID, has_sig=None, sig_pages=None) -> Document:
    doc = Document(
        tenant_id=tid,
        file_name="HD-SIG.pdf",
        file_path=f"{tid}/HD-SIG.pdf",
        doc_type="service",
        status="extracted",
        has_signature=has_sig,
        signature_pages=json.dumps(sig_pages) if sig_pages is not None else None,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ── Model round-trip ──

def test_model_has_signature_column(tenant_db):
    doc = _seed_doc(tenant_db, has_sig=True, sig_pages=[1, 3])
    doc_id = doc.id
    tenant_db.expunge(doc)

    loaded = tenant_db.query(Document).filter(Document.id == doc_id).first()
    assert loaded.has_signature is True
    assert loaded.signature_pages == json.dumps([1, 3])


def test_model_has_signature_false(tenant_db):
    doc = _seed_doc(tenant_db, has_sig=False, sig_pages=[])
    doc_id = doc.id
    tenant_db.expunge(doc)

    loaded = tenant_db.query(Document).filter(Document.id == doc_id).first()
    assert loaded.has_signature is False
    assert loaded.signature_pages == json.dumps([])


def test_model_has_signature_null_for_pre_migration_docs(tenant_db):
    """Docs created before tenant_028 have NULL for both columns."""
    doc = _seed_doc(tenant_db, has_sig=None, sig_pages=None)
    doc_id = doc.id
    tenant_db.expunge(doc)

    loaded = tenant_db.query(Document).filter(Document.id == doc_id).first()
    assert loaded.has_signature is None
    assert loaded.signature_pages is None


# ── API: GET /documents/{id} ──

def test_detail_endpoint_exposes_has_signature(auth_client, tenant_db):
    doc = _seed_doc(tenant_db, has_sig=True, sig_pages=[2, 4])
    doc_id = doc.id

    r = auth_client.get(f"/documents/{doc_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["has_signature"] is True
    assert data["signature_pages"] == [2, 4]


def test_detail_endpoint_has_signature_false(auth_client, tenant_db):
    doc = _seed_doc(tenant_db, has_sig=False, sig_pages=[])
    doc_id = doc.id

    r = auth_client.get(f"/documents/{doc_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["has_signature"] is False
    assert data["signature_pages"] == []


def test_detail_endpoint_null_for_pre_migration(auth_client, tenant_db):
    doc = _seed_doc(tenant_db, has_sig=None, sig_pages=None)
    doc_id = doc.id

    r = auth_client.get(f"/documents/{doc_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["has_signature"] is None
    assert data["signature_pages"] is None


# ── API: GET /documents (list) ──

def test_list_endpoint_exposes_has_signature(auth_client, tenant_db):
    doc = _seed_doc(tenant_db, has_sig=True, sig_pages=[1])
    doc_id = doc.id

    r = auth_client.get("/documents")
    assert r.status_code == 200
    items = r.json()["items"]
    matching = [i for i in items if i["id"] == doc_id]
    assert matching, "seeded doc must appear in list"
    item = matching[0]
    assert item["has_signature"] is True
    assert item["signature_pages"] == [1]


def test_list_endpoint_null_pre_migration(auth_client, tenant_db):
    doc = _seed_doc(tenant_db, has_sig=None, sig_pages=None)
    doc_id = doc.id

    r = auth_client.get("/documents")
    assert r.status_code == 200
    items = r.json()["items"]
    matching = [i for i in items if i["id"] == doc_id]
    assert matching
    item = matching[0]
    assert item["has_signature"] is None
    assert item["signature_pages"] is None


# ── Schema: JSON deserialization ──

def test_schema_deserializes_signature_pages_json_string(auth_client, tenant_db):
    """signature_pages stored as TEXT JSON string is parsed back to list[int]."""
    doc = _seed_doc(tenant_db, has_sig=True, sig_pages=[5, 10])
    doc_id = doc.id

    r = auth_client.get(f"/documents/{doc_id}")
    assert r.status_code == 200
    pages = r.json()["signature_pages"]
    assert isinstance(pages, list)
    assert pages == [5, 10]


def test_schema_null_signature_pages_on_corrupt_json(tenant_db):
    """Corrupt JSON in signature_pages column → None (graceful degrade)."""
    from app.schemas.documents import DocumentDetailOut
    from datetime import datetime

    data = {
        "id": 99,
        "file_name": "corrupt.pdf",
        "doc_type": None,
        "status": "extracted",
        "created_at": datetime.now(),
        "file_url": None,
        "terms": [],
        "obligations": [],
        "clause_count": 0,
        "parties": [],
        "failure_reason": None,
        "provider": None,
        "model": None,
        "confirmed_by_user_at": None,
        "processing_stage": None,
        "processing_progress": None,
        "title": None,
        "contract_number": None,
        "signing_date": None,
        "commencement_date": None,
        "contract_term": None,
        "lifecycle_status": None,
        "definition_count": 0,
        "has_signature": True,
        "signature_pages": "not-valid-json{{",
    }
    out = DocumentDetailOut(**data)
    assert out.signature_pages is None
