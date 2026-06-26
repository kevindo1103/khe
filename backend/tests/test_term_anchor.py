"""Term source anchor for Stage 3 review ref-link trust gate (#217, FR-EX-05).

- TermOut exposes ref / page_num / bbox; bbox deserializes from JSON TEXT.
- Graceful degrade: a term with no anchor → all three None (FE renders plain text).
- Document detail endpoint surfaces the anchor per term.
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
from app.models.tenant import Document, Term
from app.schemas.documents import TermOut
from main import app

TENANT = "anchor-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Anchor Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "auser").first():
        db.add(TenantUser(tenant_id=TENANT, username="auser",
                          hashed_password=get_password_hash("apass"), role="staff"))
        db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "auser", "password": "apass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session(TENANT)
    try:
        yield d
    finally:
        d.close()


def _doc_with_terms(db):
    doc = Document(tenant_id=TENANT, file_name="lease.pdf", file_path="x/y.pdf", status="extracted")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    # Anchored term (bbox stored as JSON TEXT)
    db.add(Term(tenant_id=TENANT, document_id=doc.id, field_name="ngay_het_han",
                field_value="2026-12-31", confidence=0.9, ref="Điều 8", page_num=1,
                bbox="[0.1, 0.2, 0.3, 0.4]"))
    # Un-anchored term (graceful degrade)
    db.add(Term(tenant_id=TENANT, document_id=doc.id, field_name="doi_tac",
                field_value="Công ty A", confidence=0.8))
    db.commit()
    return doc


def test_termout_deserializes_bbox():
    t = Term(id=1, tenant_id=TENANT, document_id=1, field_name="x", field_value="v", needs_review=False,
             confidence=0.9, ref="Điều 8", page_num=2, bbox="[0.1, 0.2, 0.3, 0.4]")
    out = TermOut.model_validate(t)
    assert out.ref == "Điều 8"
    assert out.page_num == 2
    assert out.bbox == [0.1, 0.2, 0.3, 0.4]   # JSON TEXT → list[float]


def test_termout_graceful_none():
    t = Term(id=2, tenant_id=TENANT, document_id=1, field_name="x", field_value="v", confidence=0.5, needs_review=False)
    out = TermOut.model_validate(t)
    assert out.ref is None
    assert out.page_num is None
    assert out.bbox is None


def test_termout_bad_bbox_is_none():
    t = Term(id=3, tenant_id=TENANT, document_id=1, field_name="x", field_value="v", needs_review=False,
             confidence=0.5, bbox="not-json")
    out = TermOut.model_validate(t)
    assert out.bbox is None


def test_detail_endpoint_surfaces_anchor(auth_client, db):
    doc = _doc_with_terms(db)
    r = auth_client.get(f"/documents/{doc.id}")
    assert r.status_code == 200
    terms = {t["field_name"]: t for t in r.json()["terms"]}
    anchored = terms["ngay_het_han"]
    assert anchored["ref"] == "Điều 8"
    assert anchored["page_num"] == 1
    assert anchored["bbox"] == [0.1, 0.2, 0.3, 0.4]
    plain = terms["doi_tac"]
    assert plain["ref"] is None
    assert plain["page_num"] is None
    assert plain["bbox"] is None
