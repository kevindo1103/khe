"""Ingest router tests — upload, storage, CRUD, consent gate, patch term (#25 PR-A)."""
import io
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, init_master_db, init_tenant_db, get_tenant_session
from app.models.master import Tenant, TenantUser
from app.services.consent import record_consent
from main import app


def _pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"


def _non_pdf_bytes() -> bytes:
    return b"NOT_A_PDF_FILE_CONTENT"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Seed a test tenant + user + consent before ingest tests."""
    init_master_db()
    init_tenant_db("ingest-tenant")

    db = MasterSessionLocal()
    tenant = db.query(Tenant).filter(Tenant.id == "ingest-tenant").first()
    if not tenant:
        db.add(Tenant(id="ingest-tenant", name="Ingest Tenant", db_path="tenants/ingest-tenant.db"))
        db.commit()

    user = (
        db.query(TenantUser)
        .filter(TenantUser.tenant_id == "ingest-tenant", TenantUser.username == "ingestuser")
        .first()
    )
    if not user:
        db.add(
            TenantUser(
                tenant_id="ingest-tenant",
                username="ingestuser",
                hashed_password=get_password_hash("ingestpass"),
                role="staff",
            )
        )
        db.commit()
    db.close()

    # Grant vision_extraction consent
    tenant_db = get_tenant_session("ingest-tenant")
    record_consent(tenant_db, "ingest-tenant", "vision_extraction", actor="ingestuser", entity_id=1)
    tenant_db.close()


@pytest.fixture
def auth_client():
    """Login and yield a client with the khe_session cookie set."""
    c = TestClient(app)
    r = c.post(
        "/auth/login",
        json={"tenant_id": "ingest-tenant", "username": "ingestuser", "password": "ingestpass"},
    )
    assert r.status_code == 200
    return c


# ── Consent gate ──

class TestConsentGate:
    def test_upload_403_without_consent(self):
        """A tenant without consent gets 403 before any file processing."""
        # Create a fresh tenant with user but NO consent
        init_tenant_db("no-consent-tenant")
        db = MasterSessionLocal()
        tenant = db.query(Tenant).filter(Tenant.id == "no-consent-tenant").first()
        if not tenant:
            db.add(Tenant(id="no-consent-tenant", name="No Consent", db_path="tenants/no-consent-tenant.db"))
            db.commit()
        user = (
            db.query(TenantUser)
            .filter(TenantUser.tenant_id == "no-consent-tenant", TenantUser.username == "noconsent")
            .first()
        )
        if not user:
            db.add(
                TenantUser(
                    tenant_id="no-consent-tenant",
                    username="noconsent",
                    hashed_password=get_password_hash("pass"),
                    role="staff",
                )
            )
            db.commit()
        db.close()

        c = TestClient(app)
        r = c.post(
            "/auth/login",
            json={"tenant_id": "no-consent-tenant", "username": "noconsent", "password": "pass"},
        )
        assert r.status_code == 200

        r2 = c.post(
            "/ingest/upload",
            files={"file": ("test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
        )
        assert r2.status_code == 403
        assert "consent" in r2.json()["detail"].lower()


# ── Upload ──

class TestUpload:
    def test_upload_single_pdf(self, auth_client):
        r = auth_client.post(
            "/ingest/upload",
            files={"file": ("contract.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["doc_id"] > 0
        assert data["file_name"] == "contract.pdf"
        assert data["status"] == "processing"

    def test_upload_non_pdf_rejected(self, auth_client):
        r = auth_client.post(
            "/ingest/upload",
            files={"file": ("fake.txt", io.BytesIO(_non_pdf_bytes()), "text/plain")},
        )
        assert r.status_code == 422

    def test_upload_with_doc_type(self, auth_client):
        r = auth_client.post(
            "/ingest/upload?doc_type=lease",
            files={"file": ("lease.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
        )
        assert r.status_code == 201
        assert r.json()["status"] == "processing"


# ── Bulk upload ──

class TestBulkUpload:
    def test_bulk_upload_ok(self, auth_client):
        files = [
            ("files", (f"doc{i}.pdf", io.BytesIO(_pdf_bytes()), "application/pdf"))
            for i in range(3)
        ]
        r = auth_client.post("/ingest/bulk", files=files)
        assert r.status_code == 201
        data = r.json()
        assert data["count"] == 3
        assert len(data["documents"]) == 3
        for d in data["documents"]:
            assert d["status"] == "processing"

    def test_bulk_over_20_rejected(self, auth_client):
        files = [
            ("files", (f"doc{i}.pdf", io.BytesIO(_pdf_bytes()), "application/pdf"))
            for i in range(21)
        ]
        r = auth_client.post("/ingest/bulk", files=files)
        assert r.status_code == 422


# ── List / Detail ──

class TestListDetail:
    def test_list_documents(self, auth_client):
        # Upload a doc first
        r = auth_client.post(
            "/ingest/upload",
            files={"file": ("list_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
        )
        assert r.status_code == 201

        r2 = auth_client.get("/documents")
        assert r2.status_code == 200
        data = r2.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1

    def test_list_documents_needs_review_filter(self, auth_client):
        # Upload a doc and create a term with needs_review=True
        r = auth_client.post(
            "/ingest/upload",
            files={"file": ("review_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
        )
        assert r.status_code == 201
        doc_id = r.json()["doc_id"]

        from app.models.tenant import Term
        db = get_tenant_session("ingest-tenant")
        term = Term(
            tenant_id="ingest-tenant",
            document_id=doc_id,
            field_name="review_field",
            field_value="review_me",
            confidence=0.5,
            needs_review=True,
        )
        db.add(term)
        db.commit()
        db.close()

        r2 = auth_client.get("/documents?needs_review=true")
        assert r2.status_code == 200
        data = r2.json()
        assert any(d["id"] == doc_id and d["needs_review"] is True for d in data["items"])

        r3 = auth_client.get("/documents?needs_review=false")
        assert r3.status_code == 200
        data3 = r3.json()
        assert not any(d["id"] == doc_id for d in data3["items"])

    def test_detail_document(self, auth_client):
        r = auth_client.post(
            "/ingest/upload",
            files={"file": ("detail_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
        )
        assert r.status_code == 201
        doc_id = r.json()["doc_id"]

        r2 = auth_client.get(f"/documents/{doc_id}")
        assert r2.status_code == 200
        data = r2.json()
        assert data["id"] == doc_id
        assert data["file_name"] == "detail_test.pdf"
        assert data["file_url"] == f"/documents/{doc_id}/file"
        assert "terms" in data
        assert "obligations" in data

    def test_detail_cross_tenant_404(self, auth_client):
        # Try to access doc_id 99999 which shouldn't exist for this tenant
        r = auth_client.get("/documents/99999")
        assert r.status_code == 404

    def test_detail_real_cross_tenant_404(self, auth_client):
        """Create a doc in another tenant and try to access it with ingest-tenant auth.

        Uses a high explicit ID (999999) to avoid collision with ingest-tenant's
        auto-incremented IDs.
        """
        from sqlalchemy import text
        from app.models.tenant import Document

        # Setup other tenant with consent
        init_tenant_db("other-tenant")
        db = MasterSessionLocal()
        tenant = db.query(Tenant).filter(Tenant.id == "other-tenant").first()
        if not tenant:
            db.add(Tenant(id="other-tenant", name="Other Tenant", db_path="tenants/other-tenant.db"))
            db.commit()
        user = db.query(TenantUser).filter(TenantUser.tenant_id == "other-tenant", TenantUser.username == "otheruser").first()
        if not user:
            db.add(
                TenantUser(
                    tenant_id="other-tenant",
                    username="otheruser",
                    hashed_password=get_password_hash("pass"),
                    role="staff",
                )
            )
            db.commit()
        db.close()

        other_db = get_tenant_session("other-tenant")
        record_consent(other_db, "other-tenant", "vision_extraction", actor="otheruser", entity_id=1)
        other_doc_id = 999999
        # Clean up stale fixture doc from prior runs before insert
        other_db.execute(text("DELETE FROM documents WHERE id = :id"), {"id": other_doc_id})
        other_db.commit()
        # Insert with explicit ID to avoid collision with ingest-tenant
        other_db.execute(
            text(
                "INSERT INTO documents (id, tenant_id, file_name, file_path, doc_type, status) "
                "VALUES (:id, :tenant_id, :file_name, :file_path, :doc_type, :status)"
            ),
            {
                "id": other_doc_id,
                "tenant_id": "other-tenant",
                "file_name": "other_doc.pdf",
                "file_path": "other-tenant/other_doc.pdf",
                "doc_type": "lease",
                "status": "processing",
            },
        )
        other_db.commit()
        other_db.close()

        # Ensure ingest-tenant has no doc with this ID
        r0 = auth_client.get(f"/documents/{other_doc_id}")
        assert r0.status_code == 404

        r2 = auth_client.get(f"/documents/{other_doc_id}/file")
        assert r2.status_code == 404

        # Sanity: other-tenant can see its own doc
        oc = TestClient(app)
        lr = oc.post(
            "/auth/login",
            json={"tenant_id": "other-tenant", "username": "otheruser", "password": "pass"},
        )
        assert lr.status_code == 200
        r3 = oc.get(f"/documents/{other_doc_id}")
        assert r3.status_code == 200


# ── File download ──

class TestFileDownload:
    def test_download_file(self, auth_client):
        r = auth_client.post(
            "/ingest/upload",
            files={"file": ("download_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
        )
        assert r.status_code == 201
        doc_id = r.json()["doc_id"]

        r2 = auth_client.get(f"/documents/{doc_id}/file")
        assert r2.status_code == 200
        assert r2.headers["content-type"] == "application/pdf"

    def test_download_404_cross_tenant(self, auth_client):
        r = auth_client.get("/documents/99999/file")
        assert r.status_code == 404


# ── Patch term (D-07) ──

class TestPatchTerm:
    def test_patch_term(self, auth_client):
        # Upload doc (terms will be empty until extraction in PR-B)
        r = auth_client.post(
            "/ingest/upload",
            files={"file": ("patch_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
        )
        assert r.status_code == 201
        doc_id = r.json()["doc_id"]

        # Manually create a term for testing D-07
        from app.db.database import get_tenant_session
        db = get_tenant_session("ingest-tenant")
        from app.models.tenant import Term
        term = Term(
            tenant_id="ingest-tenant",
            document_id=doc_id,
            field_name="test_field",
            field_value="old_value",
            confidence=0.8,
            needs_review=True,
        )
        db.add(term)
        db.commit()
        db.refresh(term)
        term_id = term.id
        db.close()

        # Patch the term
        r2 = auth_client.patch(
            f"/documents/{doc_id}/terms/{term_id}",
            json={"field_value": "new_value"},
        )
        assert r2.status_code == 200
        data = r2.json()
        assert data["ok"] is True
        assert data["field_value"] == "new_value"

        # Verify term was updated
        db2 = get_tenant_session("ingest-tenant")
        updated = db2.query(Term).filter(Term.id == term_id).first()
        assert updated.field_value == "new_value"
        assert updated.needs_review is False
        db2.close()

    def test_patch_term_404_wrong_doc(self, auth_client):
        r = auth_client.patch(
            "/documents/99999/terms/1",
            json={"field_value": "x"},
        )
        assert r.status_code == 404
