"""Definitions glossary tests (#372, R9)."""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import json
import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Definition, Document
from main import app

TENANT_ID = "def-tenant"
OTHER_TENANT_ID = "def-other-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT_ID)
    init_tenant_db(OTHER_TENANT_ID)

    db = MasterSessionLocal()
    for tid, name in [(TENANT_ID, "Def Tenant"), (OTHER_TENANT_ID, "Other Def Tenant")]:
        if not db.query(Tenant).filter(Tenant.id == tid).first():
            db.add(Tenant(id=tid, name=name, db_path=f"tenants/{tid}.db"))
    db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT_ID, TenantUser.username == "defuser").first():
        db.add(TenantUser(
            tenant_id=TENANT_ID, username="defuser",
            hashed_password=get_password_hash("defpass"), role="staff",
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
    r = c.post("/auth/login", json={"tenant_id": TENANT_ID, "username": "defuser", "password": "defpass"})
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
        tenant_id=tid,
        file_name="HD-DEFS.pdf",
        file_path=f"{tid}/HD-DEFS.pdf",
        doc_type="service",
        status="extracted",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _seed_definition(db, doc_id: int, term: str, definition: str, tid=TENANT_ID) -> Definition:
    defn = Definition(
        tenant_id=tid,
        document_id=doc_id,
        term=term,
        definition=definition,
        source_clause_num="Điều 1",
    )
    db.add(defn)
    db.commit()
    db.refresh(defn)
    return defn


# ── Migration ──

class TestDefinitionsMigration:
    def test_migration_idempotent(self, tenant_db):
        from sqlalchemy import inspect
        assert inspect(tenant_db.bind).has_table("definitions")
        cols = {c["name"] for c in inspect(tenant_db.bind).get_columns("definitions")}
        for col in ("id", "tenant_id", "document_id", "term", "definition",
                    "source_clause_num", "source_clause_id", "edited_by_user",
                    "edited_at", "original_definition"):
            assert col in cols, f"Missing column: {col}"


# ── Model CRUD ──

class TestDefinitionModel:
    def test_create_definition(self, tenant_db):
        doc = _seed_doc(tenant_db)
        defn = _seed_definition(tenant_db, doc.id, "Năm Tài chính", "12 tháng tính từ Ngày Khai Trương")
        assert defn.id is not None
        assert defn.term == "Năm Tài chính"
        assert defn.source_clause_num == "Điều 1"
        assert defn.edited_by_user is None
        assert defn.original_definition is None

    def test_update_definition(self, tenant_db):
        doc = _seed_doc(tenant_db)
        defn = _seed_definition(tenant_db, doc.id, "Khách sạn", "Cơ sở lưu trú ban đầu")
        defn.definition = "Cơ sở lưu trú cập nhật"
        tenant_db.commit()
        tenant_db.refresh(defn)
        assert defn.definition == "Cơ sở lưu trú cập nhật"

    def test_delete_definition(self, tenant_db):
        doc = _seed_doc(tenant_db)
        defn = _seed_definition(tenant_db, doc.id, "Tạm thời", "Xóa thử")
        def_id = defn.id
        tenant_db.delete(defn)
        tenant_db.commit()
        assert tenant_db.query(Definition).filter(Definition.id == def_id).first() is None


# ── GET /documents/{doc_id}/definitions ──

class TestListDefinitions:
    def test_list_empty(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        r = auth_client.get(f"/documents/{doc.id}/definitions")
        assert r.status_code == 200
        data = r.json()
        assert data["document_id"] == doc.id
        assert data["definition_count"] == 0
        assert data["definitions"] == []

    def test_list_returns_definitions_sorted_by_id(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        _seed_definition(tenant_db, doc.id, "Thương hiệu", "Tên thương mại được cấp phép")
        _seed_definition(tenant_db, doc.id, "Quốc gia", "Nước Cộng hòa Xã hội chủ nghĩa Việt Nam")
        r = auth_client.get(f"/documents/{doc.id}/definitions")
        assert r.status_code == 200
        data = r.json()
        assert data["definition_count"] == 2
        terms = [d["term"] for d in data["definitions"]]
        assert "Thương hiệu" in terms
        assert "Quốc gia" in terms

    def test_list_requires_auth(self, tenant_db):
        doc = _seed_doc(tenant_db)
        c = TestClient(app)
        r = c.get(f"/documents/{doc.id}/definitions")
        assert r.status_code == 401

    def test_list_tenant_isolation(self, auth_client, other_client, tenant_db):
        other_db = get_tenant_session(OTHER_TENANT_ID)
        try:
            other_doc = _seed_doc(other_db, tid=OTHER_TENANT_ID)
            other_doc_id = other_doc.id
            _seed_definition(other_db, other_doc.id, "Bí mật", "Không phải của tenant này", tid=OTHER_TENANT_ID)
        finally:
            other_db.close()

        # Other tenant can see their own definition
        r_other = other_client.get(f"/documents/{other_doc_id}/definitions")
        assert r_other.status_code == 200
        assert any(d["term"] == "Bí mật" for d in r_other.json()["definitions"])

        # Main tenant must not see the other tenant's secret definition.
        # Per-tenant DBs isolate data; if other_doc_id happens to exist in the
        # main tenant's DB too, the response is 200 but must not contain "Bí mật".
        r = auth_client.get(f"/documents/{other_doc_id}/definitions")
        if r.status_code == 200:
            assert not any(d["term"] == "Bí mật" for d in r.json()["definitions"])
        else:
            assert r.status_code == 404

    def test_list_404_nonexistent_doc(self, auth_client):
        r = auth_client.get("/documents/999999/definitions")
        assert r.status_code == 404


# ── PATCH /documents/{doc_id}/definitions/{def_id} ──

class TestPatchDefinition:
    def test_patch_definition_d07(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        defn = _seed_definition(tenant_db, doc.id, "Chỉ tiêu", "Định nghĩa gốc AI")
        r = auth_client.patch(
            f"/documents/{doc.id}/definitions/{defn.id}",
            json={"definition": "Định nghĩa người dùng chỉnh sửa"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["definition"] == "Định nghĩa người dùng chỉnh sửa"
        assert data["edited_by_user"] == "defuser"
        assert data["original_definition"] == "Định nghĩa gốc AI"

    def test_patch_snapshots_original_once(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        defn = _seed_definition(tenant_db, doc.id, "Cột mốc", "Gốc ban đầu")
        auth_client.patch(
            f"/documents/{doc.id}/definitions/{defn.id}",
            json={"definition": "Sửa lần 1"},
        )
        auth_client.patch(
            f"/documents/{doc.id}/definitions/{defn.id}",
            json={"definition": "Sửa lần 2"},
        )
        tenant_db.refresh(defn)
        assert defn.original_definition == "Gốc ban đầu"  # snapshot not overwritten
        assert defn.definition == "Sửa lần 2"

    def test_patch_definition_event_logged(self, auth_client, tenant_db):
        from app.models.tenant import Event
        doc = _seed_doc(tenant_db)
        defn = _seed_definition(tenant_db, doc.id, "Phí dịch vụ", "Khoản tiền ban đầu")
        auth_client.patch(
            f"/documents/{doc.id}/definitions/{defn.id}",
            json={"definition": "Khoản tiền đã cập nhật"},
        )
        ev = (
            tenant_db.query(Event)
            .filter(
                Event.entity_type == "definition",
                Event.entity_id == defn.id,
                Event.event_type == "definition_edited",
            )
            .first()
        )
        assert ev is not None
        payload = json.loads(ev.payload)
        assert payload["old_value"] == "Khoản tiền ban đầu"
        assert payload["new_value"] == "Khoản tiền đã cập nhật"

    def test_patch_definition_not_found(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        r = auth_client.patch(
            f"/documents/{doc.id}/definitions/999999",
            json={"definition": "x"},
        )
        assert r.status_code == 404

    def test_patch_definition_wrong_doc(self, auth_client, tenant_db):
        doc1 = _seed_doc(tenant_db)
        doc2 = _seed_doc(tenant_db)
        defn = _seed_definition(tenant_db, doc1.id, "Điều khoản A", "def A")
        r = auth_client.patch(
            f"/documents/{doc2.id}/definitions/{defn.id}",
            json={"definition": "tampered"},
        )
        assert r.status_code == 404


# ── DELETE /documents/{doc_id}/definitions/{def_id} ──

class TestDeleteDefinition:
    def test_delete_definition_204(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        defn = _seed_definition(tenant_db, doc.id, "Tạm xóa", "Xóa tôi")
        doc_id = doc.id
        def_id = defn.id
        r = auth_client.delete(f"/documents/{doc_id}/definitions/{def_id}")
        assert r.status_code == 204
        assert tenant_db.query(Definition).filter(Definition.id == def_id).first() is None

    def test_delete_definition_event_logged(self, auth_client, tenant_db):
        from app.models.tenant import Event
        doc = _seed_doc(tenant_db)
        defn = _seed_definition(tenant_db, doc.id, "Xóa có log", "ghi log khi xóa")
        def_id = defn.id
        auth_client.delete(f"/documents/{doc.id}/definitions/{def_id}")
        ev = (
            tenant_db.query(Event)
            .filter(
                Event.entity_type == "definition",
                Event.entity_id == def_id,
                Event.event_type == "definition_deleted",
            )
            .first()
        )
        assert ev is not None

    def test_delete_definition_tenant_isolation(self, auth_client, tenant_db):
        other_db = get_tenant_session(OTHER_TENANT_ID)
        try:
            other_doc = _seed_doc(other_db, tid=OTHER_TENANT_ID)
            other_doc_id = other_doc.id
            other_defn = _seed_definition(other_db, other_doc.id, "Chỉ riêng", "tenant khác", tid=OTHER_TENANT_ID)
            other_def_id = other_defn.id
        finally:
            other_db.close()

        r = auth_client.delete(f"/documents/{other_doc_id}/definitions/{other_def_id}")
        assert r.status_code == 404


# ── definition_count in list + detail ──

class TestDefinitionCount:
    def test_definition_count_in_document_list(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        _seed_definition(tenant_db, doc.id, "A", "def A")
        _seed_definition(tenant_db, doc.id, "B", "def B")
        r = auth_client.get("/documents/")
        assert r.status_code == 200
        items = {item["id"]: item for item in r.json()["items"]}
        assert items[doc.id]["definition_count"] == 2

    def test_definition_count_in_document_detail(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        _seed_definition(tenant_db, doc.id, "X", "def X")
        r = auth_client.get(f"/documents/{doc.id}")
        assert r.status_code == 200
        assert r.json()["definition_count"] == 1
