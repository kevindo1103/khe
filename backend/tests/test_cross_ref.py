"""Cross-reference resolution tests (#373, R10)."""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Clause, ClauseCrossRef, Document, DocumentRelationship
from app.services.cross_ref import _detect_refs, resolve_cross_refs
from main import app

TENANT_ID = "xref-tenant"
OTHER_TENANT_ID = "xref-other-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT_ID)
    init_tenant_db(OTHER_TENANT_ID)

    db = MasterSessionLocal()
    for tid, name in [(TENANT_ID, "XRef Tenant"), (OTHER_TENANT_ID, "Other XRef Tenant")]:
        if not db.query(Tenant).filter(Tenant.id == tid).first():
            db.add(Tenant(id=tid, name=name, db_path=f"tenants/{tid}.db"))
    db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT_ID, TenantUser.username == "xrefuser").first():
        db.add(TenantUser(
            tenant_id=TENANT_ID, username="xrefuser",
            hashed_password=get_password_hash("xrefpass"), role="staff",
        ))
    if not db.query(TenantUser).filter(TenantUser.tenant_id == OTHER_TENANT_ID, TenantUser.username == "otherxref").first():
        db.add(TenantUser(
            tenant_id=OTHER_TENANT_ID, username="otherxref",
            hashed_password=get_password_hash("otherpass"), role="staff",
        ))
    db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT_ID, "username": "xrefuser", "password": "xrefpass"})
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
        file_name="CONTRACT.pdf",
        file_path=f"{tid}/CONTRACT.pdf",
        doc_type="service",
        status="extracted",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _seed_clause(db, doc_id: int, content: str, clause_path: str | None = None,
                 clause_num: str | None = None, tid=TENANT_ID) -> Clause:
    c = Clause(
        tenant_id=tid,
        document_id=doc_id,
        content=content,
        clause_path=clause_path,
        clause_num=clause_num,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ── _detect_refs unit tests ──

class TestDetectRefs:
    def test_detect_dieu_ref(self):
        refs = _detect_refs("theo Điều 5 quy định về thanh toán")
        assert any(rt == "clause" and tk == "5" for _, rt, tk in refs)

    def test_detect_khoan_ref(self):
        refs = _detect_refs("tại Khoản 2.1 của hợp đồng")
        assert any(rt == "sub_clause" and tk == "2.1" for _, rt, tk in refs)

    def test_detect_muc_ref(self):
        refs = _detect_refs("theo Mục 3 của phụ lục này")
        assert any(rt == "sub_clause" and tk == "3" for _, rt, tk in refs)

    def test_detect_phu_luc_ref(self):
        refs = _detect_refs("quy định tại Phụ lục A")
        assert any(rt == "appendix" and tk.upper() == "A" for _, rt, tk in refs)

    def test_detect_multiple_refs(self):
        content = "Theo Điều 3 và Điều 7 và Phụ lục B"
        refs = _detect_refs(content)
        assert len(refs) == 3

    def test_no_refs_in_plain_text(self):
        refs = _detect_refs("Bên thuê sẽ thanh toán đúng hạn hàng tháng.")
        assert refs == []

    def test_dedup_same_ref(self):
        content = "Điều 5 được áp dụng. Xem Điều 5 để biết thêm."
        refs = _detect_refs(content)
        clause_5 = [(rt, tk) for _, rt, tk in refs if rt == "clause" and tk == "5"]
        assert len(clause_5) == 1

    def test_compound_khoan_dieu(self):
        refs = _detect_refs("theo Khoản 2 Điều 5 về thanh toán")
        assert any(rt == "clause" and tk == "5.2" for _, rt, tk in refs)
        assert not any(rt == "sub_clause" and tk == "2" for _, rt, tk in refs)
        assert not any(rt == "clause" and tk == "5" for _, rt, tk in refs)

    def test_compound_muc_dieu(self):
        refs = _detect_refs("tại Mục 3 Điều 7")
        assert any(rt == "clause" and tk == "7.3" for _, rt, tk in refs)
        assert not any(rt == "sub_clause" and tk == "3" for _, rt, tk in refs)

    def test_compound_with_comma(self):
        refs = _detect_refs("Khoản 1, Điều 4 quy định")
        assert any(rt == "clause" and tk == "4.1" for _, rt, tk in refs)

    def test_compound_plus_standalone(self):
        content = "Khoản 2 Điều 5 và Điều 8"
        refs = _detect_refs(content)
        assert any(rt == "clause" and tk == "5.2" for _, rt, tk in refs)
        assert any(rt == "clause" and tk == "8" for _, rt, tk in refs)
        assert len(refs) == 2

    def test_standalone_khoan_is_sub_clause(self):
        refs = _detect_refs("tại Khoản 3 của hợp đồng")
        assert any(rt == "sub_clause" and tk == "3" for _, rt, tk in refs)
        assert not any(rt == "clause" and tk == "3" for _, rt, tk in refs)


# ── resolve_cross_refs integration tests ──

class TestResolveCrossRefs:
    def test_resolve_intra_doc(self, tenant_db):
        doc = _seed_doc(tenant_db)
        doc_id = doc.id
        c5 = _seed_clause(tenant_db, doc_id, "Nội dung điều 5", clause_path="5", clause_num="5")
        c5_id = c5.id
        _seed_clause(
            tenant_db, doc_id,
            "Theo quy định tại Điều 5, bên A phải thực hiện nghĩa vụ.",
            clause_path="3",
        )
        stats = resolve_cross_refs(tenant_db, TENANT_ID, doc_id)
        tenant_db.commit()
        assert stats["total_refs"] >= 1
        assert stats["resolved"] >= 1
        xref = (
            tenant_db.query(ClauseCrossRef)
            .filter(
                ClauseCrossRef.document_id == doc_id,
                ClauseCrossRef.target_clause_path == "5",
            )
            .first()
        )
        assert xref is not None
        assert xref.target_clause_id == c5_id
        assert not xref.is_orphan

    def test_orphan_unresolved(self, tenant_db):
        doc = _seed_doc(tenant_db)
        doc_id = doc.id
        _seed_clause(tenant_db, doc_id, "Xem Điều 99 để biết thêm chi tiết.", clause_path="1")
        stats = resolve_cross_refs(tenant_db, TENANT_ID, doc_id)
        tenant_db.commit()
        assert stats["orphans"] >= 1
        xref = (
            tenant_db.query(ClauseCrossRef)
            .filter(
                ClauseCrossRef.document_id == doc_id,
                ClauseCrossRef.is_orphan == True,
            )
            .first()
        )
        assert xref is not None
        assert xref.target_clause_id is None

    def test_no_self_reference(self, tenant_db):
        doc = _seed_doc(tenant_db)
        doc_id = doc.id
        # Clause 5 whose content references "Điều 5" (itself)
        _seed_clause(tenant_db, doc_id, "Điều 5 này quy định về thanh toán.", clause_path="5")
        resolve_cross_refs(tenant_db, TENANT_ID, doc_id)
        tenant_db.commit()
        # Self-ref should not create a resolved cross-ref pointing to itself
        self_ref = (
            tenant_db.query(ClauseCrossRef)
            .filter(
                ClauseCrossRef.document_id == doc_id,
                ClauseCrossRef.target_clause_path == "5",
            )
            .first()
        )
        assert self_ref is None or self_ref.is_orphan

    def test_idempotent_rerun(self, tenant_db):
        doc = _seed_doc(tenant_db)
        doc_id = doc.id
        _seed_clause(tenant_db, doc_id, "Theo Điều 2 về nghĩa vụ.", clause_path="1")
        _seed_clause(tenant_db, doc_id, "Điều 2 quy định.", clause_path="2")
        resolve_cross_refs(tenant_db, TENANT_ID, doc_id)
        tenant_db.commit()
        count_after_first = tenant_db.query(ClauseCrossRef).filter(
            ClauseCrossRef.document_id == doc_id).count()
        resolve_cross_refs(tenant_db, TENANT_ID, doc_id)
        tenant_db.commit()
        count_after_second = tenant_db.query(ClauseCrossRef).filter(
            ClauseCrossRef.document_id == doc_id).count()
        assert count_after_first == count_after_second

    def test_empty_doc_no_refs(self, tenant_db):
        doc = _seed_doc(tenant_db)
        doc_id = doc.id
        stats = resolve_cross_refs(tenant_db, TENANT_ID, doc_id)
        tenant_db.commit()
        assert stats["total_refs"] == 0
        assert stats["resolved"] == 0
        assert stats["orphans"] == 0

    def test_resolve_compound_khoan_dieu(self, tenant_db):
        doc = _seed_doc(tenant_db)
        doc_id = doc.id
        c52 = _seed_clause(tenant_db, doc_id, "Nội dung khoản 2 điều 5", clause_path="5.2")
        c52_id = c52.id
        _seed_clause(tenant_db, doc_id, "Nội dung điều 5", clause_path="5")
        _seed_clause(
            tenant_db, doc_id,
            "Theo Khoản 2 Điều 5, bên A phải thực hiện.",
            clause_path="3",
        )
        stats = resolve_cross_refs(tenant_db, TENANT_ID, doc_id)
        tenant_db.commit()
        xref = (
            tenant_db.query(ClauseCrossRef)
            .filter(
                ClauseCrossRef.document_id == doc_id,
                ClauseCrossRef.target_clause_path == "5.2",
            )
            .first()
        )
        assert xref is not None
        assert xref.target_clause_id == c52_id
        assert not xref.is_orphan
        assert stats["resolved"] >= 1

    def test_resolve_appendix_via_annex_rel(self, tenant_db):
        main_doc = _seed_doc(tenant_db)
        annex_doc = _seed_doc(tenant_db)
        main_doc_id = main_doc.id
        annex_doc_id = annex_doc.id
        # Create annex relationship: annex_doc → main_doc with identifier "A"
        rel = DocumentRelationship(
            tenant_id=TENANT_ID,
            from_doc_id=annex_doc_id,
            to_doc_id=main_doc_id,
            relationship_type="annex",
            unresolved_ref="A",
        )
        tenant_db.add(rel)
        tenant_db.commit()
        _seed_clause(tenant_db, main_doc_id, "Xem Phụ lục A để biết thêm.", clause_path="1")
        stats = resolve_cross_refs(tenant_db, TENANT_ID, main_doc_id)
        tenant_db.commit()
        xref = (
            tenant_db.query(ClauseCrossRef)
            .filter(
                ClauseCrossRef.document_id == main_doc_id,
                ClauseCrossRef.ref_type == "appendix",
            )
            .first()
        )
        assert xref is not None
        assert xref.target_doc_id == annex_doc_id
        assert not xref.is_orphan
        assert stats["resolved"] >= 1


# ── GET /documents/{doc_id}/cross-refs ──

class TestCrossRefEndpoint:
    def test_list_returns_refs(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        doc_id = doc.id
        c2 = _seed_clause(tenant_db, doc_id, "Điều 2 về phí.", clause_path="2")
        _seed_clause(tenant_db, doc_id, "Theo Điều 2, bên thuê trả phí.", clause_path="1")
        resolve_cross_refs(tenant_db, TENANT_ID, doc_id)
        tenant_db.commit()
        r = auth_client.get(f"/documents/{doc_id}/cross-refs")
        assert r.status_code == 200
        data = r.json()
        assert data["document_id"] == doc_id
        assert data["total_refs"] >= 1
        assert isinstance(data["refs"], list)

    def test_list_requires_auth(self, tenant_db):
        doc = _seed_doc(tenant_db)
        doc_id = doc.id
        c = TestClient(app)
        r = c.get(f"/documents/{doc_id}/cross-refs")
        assert r.status_code == 401

    def test_list_404_nonexistent_doc(self, auth_client):
        r = auth_client.get("/documents/999999/cross-refs")
        assert r.status_code == 404

    def test_orphan_count_correct(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        doc_id = doc.id
        _seed_clause(tenant_db, doc_id, "Xem Điều 88 và Điều 99.", clause_path="1")
        resolve_cross_refs(tenant_db, TENANT_ID, doc_id)
        tenant_db.commit()
        r = auth_client.get(f"/documents/{doc_id}/cross-refs")
        assert r.status_code == 200
        data = r.json()
        assert data["orphans"] == data["total_refs"]  # both orphans (no clause 88 or 99)
        assert data["resolved"] == 0

    def test_list_tenant_isolation(self, auth_client, tenant_db):
        other_db = get_tenant_session(OTHER_TENANT_ID)
        try:
            other_doc = _seed_doc(other_db, tid=OTHER_TENANT_ID)
            other_doc_id = other_doc.id
            _seed_clause(other_db, other_doc_id, "Theo Điều 1.", clause_path="2", tid=OTHER_TENANT_ID)
            resolve_cross_refs(other_db, OTHER_TENANT_ID, other_doc_id)
            other_db.commit()
        finally:
            other_db.close()

        # Other tenant's cross-refs not visible from main tenant
        r = auth_client.get(f"/documents/{other_doc_id}/cross-refs")
        if r.status_code == 200:
            # If doc_id happens to exist in main tenant's DB too, refs must not include
            # cross-refs that belong to the other tenant
            for ref in r.json()["refs"]:
                assert ref["ref_text"] != "Theo Điều 1."
        else:
            assert r.status_code == 404

    def test_post_resolve_endpoint(self, auth_client, tenant_db):
        doc = _seed_doc(tenant_db)
        doc_id = doc.id
        _seed_clause(tenant_db, doc_id, "Theo Điều 3.", clause_path="1")
        _seed_clause(tenant_db, doc_id, "Điều 3.", clause_path="3")
        r = auth_client.post(f"/documents/{doc_id}/cross-refs/resolve")
        assert r.status_code == 200
        data = r.json()
        assert data["document_id"] == doc_id
        assert "total_refs" in data
        assert "resolved" in data
        assert "orphans" in data
