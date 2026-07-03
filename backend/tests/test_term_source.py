"""TermOut.source field exposed via API (#484)."""
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

TENANT = "termsrc-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="TermSrc Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "tsuser").first():
        db.add(TenantUser(tenant_id=TENANT, username="tsuser",
                          hashed_password=get_password_hash("tspass"), role="staff"))
        db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "tsuser", "password": "tspass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session(TENANT)
    try:
        yield d
    finally:
        d.close()


def test_termout_source_extracted():
    t = Term(id=1, tenant_id=TENANT, document_id=1, field_name="ngay_ky",
             field_value="2025-01-01", confidence=0.95, needs_review=False,
             source="extracted")
    out = TermOut.model_validate(t)
    assert out.source == "extracted"


def test_termout_source_remap():
    t = Term(id=2, tenant_id=TENANT, document_id=1, field_name="tien_thue",
             field_value="10000000", confidence=0.8, needs_review=False,
             source="remap")
    out = TermOut.model_validate(t)
    assert out.source == "remap"


def test_termout_source_manual():
    t = Term(id=3, tenant_id=TENANT, document_id=1, field_name="dia_chi",
             field_value="123 Đường ABC", confidence=None, needs_review=False,
             source="manual")
    out = TermOut.model_validate(t)
    assert out.source == "manual"


def test_termout_source_null_legacy():
    t = Term(id=4, tenant_id=TENANT, document_id=1, field_name="doi_tac",
             field_value="Công ty X", confidence=0.7, needs_review=False,
             source=None)
    out = TermOut.model_validate(t)
    assert out.source is None


def test_detail_endpoint_includes_source(auth_client, db):
    doc = Document(tenant_id=TENANT, file_name="contract.pdf",
                   file_path="x/contract.pdf", status="extracted")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.add(Term(tenant_id=TENANT, document_id=doc.id, field_name="ten_hop_dong",
                field_value="Hợp đồng thuê", confidence=0.9, needs_review=False,
                source="extracted"))
    db.add(Term(tenant_id=TENANT, document_id=doc.id, field_name="gia_tri",
                field_value="50000000", confidence=0.85, needs_review=False,
                source="remap"))
    db.add(Term(tenant_id=TENANT, document_id=doc.id, field_name="ghi_chu",
                field_value="chú thích tay", confidence=None, needs_review=False,
                source=None))
    db.commit()

    r = auth_client.get(f"/documents/{doc.id}")
    assert r.status_code == 200
    terms = {t["field_name"]: t for t in r.json()["terms"]}

    assert terms["ten_hop_dong"]["source"] == "extracted"
    assert terms["gia_tri"]["source"] == "remap"
    assert terms["ghi_chu"]["source"] is None
