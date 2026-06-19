"""Extraction runner (PR-B of #25) tests with a fake Protocol-conforming provider."""
import io
import os
import sys
from unittest.mock import patch

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.services.consent import record_consent
from main import app


def _pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"


class FakeProvider:
    """Protocol-conforming provider that returns deterministic fields."""

    name = "fake_provider"

    def __init__(self, result=None):
        self._result = result
        self.calls = []

    async def extract(self, image_bytes: bytes, doc_type: str = "auto"):
        self.calls.append((image_bytes, doc_type))
        return self._result


def _make_success_result():
    from modules.extraction import DocType, ExtractedField, ExtractionResult, TokenUsage

    return ExtractionResult(
        doc_type=DocType.LEASE,
        doc_type_confidence=0.95,
        fields={
            "doi_tac": ExtractedField(value="Công ty A", confidence=0.9, needs_review=False),
            "ngay_hieu_luc": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
            "ngay_het_han": ExtractedField(value="2027-01-01", confidence=0.85, needs_review=False),
            "gia_tri_hd": ExtractedField(value="100000000", confidence=0.8, needs_review=True),
            "thoi_han_hd": ExtractedField(value="12 tháng", confidence=0.9, needs_review=False),
            "dieu_khoan_gia_han": ExtractedField(value="Tự động gia hạn", confidence=0.7, needs_review=True),
            "dieu_khoan_thanh_toan": ExtractedField(value="Chuyển khoản", confidence=0.9, needs_review=False),
        },
        provider="fake_provider",
        model="fake-model",
        latency_ms=123.0,
        usage=TokenUsage(input_tokens=1000, output_tokens=200),
        cost_vnd=500.0,
    )


def _make_error_result():
    from modules.extraction import DocType, ExtractionResult, TokenUsage

    return ExtractionResult(
        doc_type=DocType.OTHER,
        doc_type_confidence=0.0,
        fields={},
        provider="fake_provider",
        model="fake-model",
        latency_ms=0.0,
        usage=TokenUsage(input_tokens=0, output_tokens=0),
        cost_vnd=0.0,
        warnings=["No structured output received"],
    )


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db("extract-tenant")

    db = MasterSessionLocal()
    tenant = db.query(Tenant).filter(Tenant.id == "extract-tenant").first()
    if not tenant:
        db.add(Tenant(id="extract-tenant", name="Extract Tenant", db_path="tenants/extract-tenant.db"))
        db.commit()

    user = db.query(TenantUser).filter(TenantUser.tenant_id == "extract-tenant", TenantUser.username == "extractuser").first()
    if not user:
        db.add(
            TenantUser(
                tenant_id="extract-tenant",
                username="extractuser",
                hashed_password=get_password_hash("extractpass"),
                role="staff",
            )
        )
        db.commit()
    db.close()

    tenant_db = get_tenant_session("extract-tenant")
    record_consent(tenant_db, "extract-tenant", "vision_extraction", actor="extractuser", entity_id=1)
    tenant_db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post(
        "/auth/login",
        json={"tenant_id": "extract-tenant", "username": "extractuser", "password": "extractpass"},
    )
    assert r.status_code == 200
    return c


# ── Happy path ──

class TestExtractionSuccess:
    def test_upload_triggers_extraction(self, auth_client):
        fake = FakeProvider(_make_success_result())
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("extract_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        # BackgroundTasks runs after the response in TestClient.
        r2 = auth_client.get(f"/documents/{doc_id}")
        assert r2.status_code == 200
        data = r2.json()
        assert data["status"] == "extracted"
        assert data["doc_type"] == "hd_thue_mat_bang"
        terms = {t["field_name"]: t for t in data["terms"]}
        assert "doi_tac" in terms
        assert "gia_tri_hd" in terms
        assert terms["gia_tri_hd"]["needs_review"] is True
        assert fake.calls


# ── Failure paths ──

class TestExtractionFailure:
    def test_is_error_marks_failed(self, auth_client):
        fake = FakeProvider(_make_error_result())
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("error_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        r2 = auth_client.get(f"/documents/{doc_id}")
        assert r2.status_code == 200
        data = r2.json()
        assert data["status"] == "failed"
        assert data["terms"] == []

    def test_unavailable_provider_marks_failed(self, auth_client):
        from modules.extraction import ExtractionUnavailable

        with patch("app.services.extraction_runner.get_extraction_provider", side_effect=ExtractionUnavailable("no key")):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("no_provider_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        r2 = auth_client.get(f"/documents/{doc_id}")
        assert r2.status_code == 200
        data = r2.json()
        assert data["status"] == "failed"

    def test_revoked_consent_marks_failed(self, auth_client):
        from app.services.consent import revoke_consent
        from app.services.extraction_runner import run_extraction

        # Upload with consent granted; use a provider that never returns so the
        # background task stays pending until we manually trigger run_extraction.
        blocking = FakeProvider(_make_success_result())
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=blocking):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("revoked_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        # Revoke consent before the worker runs.
        tenant_db = get_tenant_session("extract-tenant")
        revoke_consent(tenant_db, "extract-tenant", "vision_extraction", actor="extractuser")
        tenant_db.close()

        try:
            # Direct-call the worker to test the defensive consent re-check.
            fake = FakeProvider(_make_success_result())
            with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
                import asyncio

                asyncio.run(run_extraction(doc_id, "extract-tenant", None))

            assert fake.calls == []  # LLM was never called

            r2 = auth_client.get(f"/documents/{doc_id}")
            assert r2.status_code == 200
            data = r2.json()
            assert data["status"] == "failed"
        finally:
            # Re-grant consent for other tests
            tenant_db2 = get_tenant_session("extract-tenant")
            record_consent(tenant_db2, "extract-tenant", "vision_extraction", actor="extractuser", entity_id=1)
            tenant_db2.close()


# ── Idempotency ──

class TestExtractionIdempotency:
    def test_re_run_replaces_terms(self, auth_client):
        fake = FakeProvider(_make_success_result())
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("idempotent_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        r2 = auth_client.get(f"/documents/{doc_id}")
        assert r2.status_code == 200
        data = r2.json()
        assert len(data["terms"]) == 7

        # Re-run with a different result set; should replace, not duplicate.
        from modules.extraction import ExtractedField

        result2 = _make_success_result()
        result2.fields["doi_tac"] = ExtractedField(value="Công ty B", confidence=0.9, needs_review=False)
        fake2 = FakeProvider(result2)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake2):
            from app.services.extraction_runner import run_extraction
            import asyncio

            asyncio.run(run_extraction(doc_id, "extract-tenant", None))

        r3 = auth_client.get(f"/documents/{doc_id}")
        terms = {t["field_name"]: t for t in r3.json()["terms"]}
        assert len(terms) == 7
        assert terms["doi_tac"]["field_value"] == "Công ty B"
