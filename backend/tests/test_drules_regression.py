"""D-rules regression suite — D-06, D-07, D-08, D-10.

D-06: Extraction is READ-ONLY — stored values match provider output verbatim.
D-07: Admin review UI can edit terms (PATCH endpoint clears needs_review).
D-08: Never fabricate — chat returns "not found" when no data.
D-10: Tenant isolation — cross-tenant queries return empty/404.
"""
import io
import os
import sys
from unittest.mock import patch

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import (
    MasterSessionLocal,
    get_tenant_session,
    init_master_db,
    init_tenant_db,
)
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document, Term
from app.services import chat_query
from main import app
from modules.extraction import DocType, ExtractedField, TokenUsage
from tests.conftest import FakeVisionProvider, make_extraction_result


def _pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"


def _upload_and_extract(auth_client, result, file_name="test.pdf"):
    fake = FakeVisionProvider(result)
    with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
        r = auth_client.post(
            "/ingest/upload",
            files={"file": (file_name, io.BytesIO(_pdf_bytes()), "application/pdf")},
        )
        assert r.status_code == 201
        return r.json()["doc_id"]


def _mock_select_tools(calls):
    async def _select(*args, **kwargs):
        return calls
    return _select


def _mock_format_answer(answer):
    async def _format(*args, **kwargs):
        return answer
    return _format


# ── D-06: READ-ONLY extraction ───────────────────────────────────────────

class TestD06ReadOnly:
    def test_stored_values_match_provider_verbatim(self, auth_client, test_tenant, db):
        """Term.field_value matches ExtractedField.value exactly — no modification."""
        result = make_extraction_result(
            doc_type_group="thuong_mai",
            fields={
                "doi_tac": ExtractedField(value="Công ty XYZ — chi nhánh Hà Nội", confidence=0.92, needs_review=False),
                "ngay_het_han": ExtractedField(value="2027-06-30", confidence=0.88, needs_review=False),
            },
        )
        doc_id = _upload_and_extract(auth_client, result, "d06_verbatim.pdf")

        terms = db.query(Term).filter(Term.document_id == doc_id).all()
        term_map = {t.field_name: t for t in terms}

        assert term_map["doi_tac"].field_value == "Công ty XYZ — chi nhánh Hà Nội"
        assert term_map["doi_tac"].confidence == 0.92
        assert term_map["ngay_het_han"].field_value == "2027-06-30"
        assert term_map["ngay_het_han"].confidence == 0.88

    def test_provider_called_with_image_bytes(self, auth_client, test_tenant):
        """Provider.extract receives the raw file bytes — not modified."""
        result = make_extraction_result(doc_type_group="thuong_mai")
        fake = FakeVisionProvider(result)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            auth_client.post(
                "/ingest/upload",
                files={"file": ("d06_bytes.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
        assert len(fake.calls) == 1
        received_bytes, received_doc_type = fake.calls[0]
        assert received_bytes == _pdf_bytes()


# ── D-07: Admin review (PATCH term) ──────────────────────────────────────

class TestD07AdminReview:
    def test_patch_term_updates_value(self, auth_client, test_tenant, db):
        """PATCH /documents/{id}/terms/{term_id} updates field_value."""
        result = make_extraction_result(doc_type_group="thuong_mai")
        doc_id = _upload_and_extract(auth_client, result, "d07_patch.pdf")

        terms = auth_client.get(f"/documents/{doc_id}").json()["terms"]
        term = next(t for t in terms if t["field_name"] == "doi_tac")
        assert term["needs_review"] is False

        r = auth_client.patch(
            f"/documents/{doc_id}/terms/{term['id']}",
            json={"field_value": "Công ty ABC (đã sửa)"},
        )
        assert r.status_code == 200
        assert r.json()["field_value"] == "Công ty ABC (đã sửa)"

    def test_patch_term_clears_needs_review(self, auth_client, test_tenant, db):
        """PATCH clears needs_review flag (admin has reviewed)."""
        result = make_extraction_result(
            doc_type_group="thuong_mai",
            fields={
                "gia_tri_hd": ExtractedField(value="100000000", confidence=0.6, needs_review=True),
            },
        )
        doc_id = _upload_and_extract(auth_client, result, "d07_review.pdf")

        terms = auth_client.get(f"/documents/{doc_id}").json()["terms"]
        term = next(t for t in terms if t["field_name"] == "gia_tri_hd")
        assert term["needs_review"] is True

        r = auth_client.patch(
            f"/documents/{doc_id}/terms/{term['id']}",
            json={"field_value": "120000000"},
        )
        assert r.status_code == 200

        # Verify needs_review is cleared in DB
        db_term = db.query(Term).filter(Term.id == term["id"]).first()
        assert db_term.needs_review is False
        assert db_term.field_value == "120000000"

    def test_patch_nonexistent_term_404(self, auth_client, test_tenant, db):
        """PATCH with invalid term_id → 404."""
        result = make_extraction_result(doc_type_group="thuong_mai")
        doc_id = _upload_and_extract(auth_client, result, "d07_404.pdf")

        r = auth_client.patch(
            f"/documents/{doc_id}/terms/99999",
            json={"field_value": "test"},
        )
        assert r.status_code == 404


# ── D-08: Never fabricate ────────────────────────────────────────────────

class TestD08NeverFabricate:
    def test_chat_no_tools_returns_not_found(self, auth_client, test_tenant, db, monkeypatch):
        """When LLM selects no tools → D-08 not-found message."""
        monkeypatch.setattr(chat_query, "_select_tools", _mock_select_tools([]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer(""))

        r = auth_client.post("/chat/query", json={"question": "random question?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert data["answer"] == "Không tìm thấy thông tin này trong hồ sơ của bạn."
        assert data["sources"] == []

    def test_chat_empty_results_returns_not_found(
        self, auth_client, test_tenant, db, monkeypatch
    ):
        """When tools return empty results → D-08 not-found."""
        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools([{
                "name": "search_terms",
                "args": {"field_name": "ngay_het_han", "doc_hint": "nonexistent"},
            }]),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer(""))

        r = auth_client.post("/chat/query", json={"question": "hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert "Không tìm thấy" in data["answer"]

    def test_extraction_error_marks_failed(self, auth_client, test_tenant, db):
        """Provider error → doc.status='failed', no terms fabricated."""
        from modules.extraction import ExtractionResult

        # is_error is a computed property: bool(warnings) and usage.input_tokens == 0
        error_result = ExtractionResult(
            doc_type=DocType.OTHER,
            doc_type_confidence=0.0,
            fields={},
            provider="fake",
            model="fake",
            warnings=["Simulated error"],
            usage=TokenUsage(input_tokens=0, output_tokens=0),
        )
        assert error_result.is_error is True

        fake = FakeVisionProvider(error_result)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("d08_error.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        # Wait for background task to complete (TestClient runs sync)
        doc_data = auth_client.get(f"/documents/{doc_id}").json()
        assert doc_data["status"] == "failed"
        assert len(doc_data["terms"]) == 0


# ── D-10: Tenant isolation ───────────────────────────────────────────────

class TestD10TenantIsolation:
    def test_cross_tenant_document_404(self, auth_client, test_tenant, db):
        """Tenant A cannot access tenant B's document by ID."""
        # Create a second tenant
        other_id = f"qc-other-{os.urandom(4).hex()}"
        init_tenant_db(other_id)
        master_db = MasterSessionLocal()
        try:
            master_db.add(Tenant(id=other_id, name="Other", db_path=f"tenants/{other_id}.db"))
            master_db.add(TenantUser(
                tenant_id=other_id, username="otheruser",
                hashed_password=get_password_hash("otherpass"), role="admin",
            ))
            master_db.commit()
        finally:
            master_db.close()

        # Create a doc in other tenant's DB
        other_db = get_tenant_session(other_id)
        try:
            doc = Document(
                tenant_id=other_id, file_name="secret.pdf",
                file_path=f"{other_id}/secret.pdf", status="extracted",
            )
            other_db.add(doc)
            other_db.commit()
            other_db.refresh(doc)
            other_doc_id = doc.id
        finally:
            other_db.close()

        # Tenant A (auth_client) tries to access other tenant's doc
        r = auth_client.get(f"/documents/{other_doc_id}")
        assert r.status_code == 404

        # Cleanup
        from tests.conftest import _reset_tenant_db, _cleanup_master
        _reset_tenant_db(other_id)
        _cleanup_master(other_id)

    def test_cross_tenant_obligation_404(self, auth_client, test_tenant, db):
        """Tenant A cannot patch tenant B's obligation."""
        from app.models.tenant import Obligation

        other_id = f"qc-other-{os.urandom(4).hex()}"
        init_tenant_db(other_id)
        master_db = MasterSessionLocal()
        try:
            master_db.add(Tenant(id=other_id, name="Other", db_path=f"tenants/{other_id}.db"))
            master_db.add(TenantUser(
                tenant_id=other_id, username="otheruser",
                hashed_password=get_password_hash("otherpass"), role="admin",
            ))
            master_db.commit()
        finally:
            master_db.close()

        other_db = get_tenant_session(other_id)
        try:
            doc = Document(
                tenant_id=other_id, file_name="obl.pdf",
                file_path=f"{other_id}/obl.pdf", status="extracted",
            )
            other_db.add(doc)
            other_db.commit()
            other_db.refresh(doc)
            ob = Obligation(
                tenant_id=other_id, document_id=doc.id,
                description="Other tenant obligation",
                recurrence="once", due_date="2027-01-01", status="pending",
            )
            other_db.add(ob)
            other_db.commit()
            other_db.refresh(ob)
            other_ob_id = ob.id
        finally:
            other_db.close()

        # Tenant A tries to patch other tenant's obligation
        r = auth_client.patch(
            f"/obligations/{other_ob_id}",
            json={"status": "done"},
        )
        assert r.status_code == 404

        # Cleanup
        from tests.conftest import _reset_tenant_db, _cleanup_master
        _reset_tenant_db(other_id)
        _cleanup_master(other_id)

    def test_cross_tenant_chat_isolation(self, auth_client, test_tenant, db, monkeypatch):
        """Chat query for tenant A does not return tenant B's data."""
        other_id = f"qc-other-{os.urandom(4).hex()}"
        init_tenant_db(other_id)
        master_db = MasterSessionLocal()
        try:
            master_db.add(Tenant(id=other_id, name="Other", db_path=f"tenants/{other_id}.db"))
            master_db.add(TenantUser(
                tenant_id=other_id, username="otheruser",
                hashed_password=get_password_hash("otherpass"), role="admin",
            ))
            master_db.commit()
        finally:
            master_db.close()

        other_db = get_tenant_session(other_id)
        try:
            doc = Document(
                tenant_id=other_id, file_name="secret_contract.pdf",
                file_path=f"{other_id}/secret.pdf", status="extracted",
            )
            other_db.add(doc)
            other_db.commit()
            other_db.refresh(doc)
            other_db.add(Term(
                tenant_id=other_id, document_id=doc.id,
                field_name="ngay_het_han", field_value="2029-12-31", confidence=0.9,
            ))
            other_db.commit()
        finally:
            other_db.close()

        # Tenant A asks about the other tenant's document
        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools([{
                "name": "search_terms",
                "args": {"field_name": "ngay_het_han", "doc_hint": "secret_contract"},
            }]),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer(""))

        r = auth_client.post(
            "/chat/query",
            json={"question": "hợp đồng secret_contract.pdf hết hạn khi nào?"},
        )
        assert r.status_code == 200
        data = r.json()
        # Tenant A should not find tenant B's data
        assert data["found"] is False
        assert "Không tìm thấy" in data["answer"]

        # Cleanup
        from tests.conftest import _reset_tenant_db, _cleanup_master
        _reset_tenant_db(other_id)
        _cleanup_master(other_id)
