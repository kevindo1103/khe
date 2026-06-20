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


def _make_success_result_with_clauses(clauses=None):
    from modules.extraction import ClauseItem

    result = _make_success_result()
    items = clauses if clauses is not None else [
        ClauseItem(num="Điều 1", title="Phạm vi", content="Bên A cho Bên B thuê mặt bằng."),
        ClauseItem(num="Điều 8", title="Chấm dứt", content="Thông báo trước 30 ngày."),
        ClauseItem(num=None, title=None, content="Phụ lục không đánh số."),
    ]
    result.clauses = items
    return result


def _make_success_result_with_type_specific():
    """Result with type-specific fields (labor) + payment schedule (DEC-027)."""
    from modules.extraction import (
        DocType, ExtractedField, ExtractionResult, PaymentScheduleItem, TokenUsage,
    )

    return ExtractionResult(
        doc_type=DocType.LABOR,
        doc_type_confidence=0.95,
        fields={
            "doi_tac": ExtractedField(value="Công ty A", confidence=0.9, needs_review=False),
            "ngay_hieu_luc": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
            "ngay_het_han": ExtractedField(value="2027-01-01", confidence=0.85, needs_review=False),
            "gia_tri_hd": ExtractedField(value="50000000", confidence=0.8, needs_review=True),
            "thoi_han_hd": ExtractedField(value="12 tháng", confidence=0.9, needs_review=False),
            "dieu_khoan_gia_han": ExtractedField(value="Tự động gia hạn", confidence=0.7, needs_review=True),
            "dieu_khoan_thanh_toan": ExtractedField(value="Chuyển khoản", confidence=0.9, needs_review=False),
            "luong_co_ban": ExtractedField(value="15000000", confidence=0.85, needs_review=False),
            "thoi_gian_thu_viec": ExtractedField(value="60 ngày", confidence=0.8, needs_review=True),
        },
        payment_schedule=[
            PaymentScheduleItem(amount="15000000", due_date="2026-02-01", milestone="Tạm ứng tháng 1", recurrence=None),
            PaymentScheduleItem(amount="15000000", due_date="2026-03-01", milestone="Tạm ứng tháng 2", recurrence=None),
            PaymentScheduleItem(amount=None, due_date=None, milestone="Theo thông báo", recurrence=None),
        ],
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
                run_extraction(doc_id, "extract-tenant", None)

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

            run_extraction(doc_id, "extract-tenant", None)

        r3 = auth_client.get(f"/documents/{doc_id}")
        terms = {t["field_name"]: t for t in r3.json()["terms"]}
        assert len(terms) == 7
        assert terms["doi_tac"]["field_value"] == "Công ty B"


# ── Clauses (DEC-026 / #99) ──

class TestExtractionClauses:
    def test_clauses_persisted_and_counted(self, auth_client):
        """Provider clauses are inserted; clause_count surfaces on detail + list."""
        fake = FakeProvider(_make_success_result_with_clauses())
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("clauses_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        # Detail endpoint (#104).
        detail = auth_client.get(f"/documents/{doc_id}").json()
        assert detail["clause_count"] == 3

        # List endpoint (this PR) — find our doc in the rollup.
        listing = auth_client.get("/documents/").json()
        item = next(i for i in listing["items"] if i["id"] == doc_id)
        assert item["clause_count"] == 3

    def test_re_run_replaces_clauses(self, auth_client):
        """Re-extraction replaces clauses (idempotent) — no duplication."""
        from modules.extraction import ClauseItem

        fake = FakeProvider(_make_success_result_with_clauses())
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("clauses_idem_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        assert auth_client.get(f"/documents/{doc_id}").json()["clause_count"] == 3

        # Re-run with a single clause; must replace the original 3, not add.
        result2 = _make_success_result_with_clauses(
            clauses=[ClauseItem(num="Điều 2", title="Giá", content="Giá thuê cố định.")]
        )
        fake2 = FakeProvider(result2)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake2):
            from app.services.extraction_runner import run_extraction

            run_extraction(doc_id, "extract-tenant", None)

        assert auth_client.get(f"/documents/{doc_id}").json()["clause_count"] == 1

    def test_no_clauses_yields_zero_count(self, auth_client):
        """Claude-fallback path (clauses=[]) → clause_count 0, no error."""
        fake = FakeProvider(_make_success_result())  # base result has no clauses
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("no_clauses_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        assert auth_client.get(f"/documents/{doc_id}").json()["clause_count"] == 0


# ── Type-specific fields + payment schedule (#137) ──

class TestTypeSpecificFields:
    def test_type_specific_fields_persisted(self, auth_client):
        """Type-specific fields (luong_co_ban, thoi_gian_thu_viec) stored as Term rows."""
        fake = FakeProvider(_make_success_result_with_type_specific())
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("labor_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        data = auth_client.get(f"/documents/{doc_id}").json()
        terms = {t["field_name"]: t for t in data["terms"]}
        assert "luong_co_ban" in terms
        assert terms["luong_co_ban"]["field_value"] == "15000000"
        assert "thoi_gian_thu_viec" in terms
        assert terms["thoi_gian_thu_viec"]["field_value"] == "60 ngày"
        # Base fields still present
        assert "doi_tac" in terms
        assert "ngay_hieu_luc" in terms

    def test_claude_fallback_base_fields_only(self, auth_client):
        """Claude fallback (7 base fields only) still works — no type-specific fields."""
        fake = FakeProvider(_make_success_result())
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("claude_fallback_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        data = auth_client.get(f"/documents/{doc_id}").json()
        terms = {t["field_name"]: t for t in data["terms"]}
        assert len(terms) == 7
        assert "luong_co_ban" not in terms


class TestPaymentScheduleObligations:
    def test_payment_schedule_creates_obligations(self, auth_client):
        """Payment schedule items with due_date create pending Obligation rows."""
        fake = FakeProvider(_make_success_result_with_type_specific())
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("payment_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        # Check obligations via the document detail endpoint
        data = auth_client.get(f"/documents/{doc_id}").json()
        obligations = data.get("obligations", [])
        # 2 payment obligations (items with due_date) + 1 expiry obligation from derive_obligations
        payment_obs = [o for o in obligations if "Tạm ứng" in o.get("description", "")]
        assert len(payment_obs) == 2
        due_dates = {o["due_date"] for o in payment_obs}
        assert "2026-02-01" in due_dates
        assert "2026-03-01" in due_dates
        # Payment obligations must have obligation_type="payment" + recurrence="once"
        for po in payment_obs:
            assert po["obligation_type"] == "payment"
            assert po["recurrence"] == "once"
        # The item without due_date should NOT create an obligation
        assert not any("Theo thông báo" in o.get("description", "") for o in obligations)

    def test_payment_schedule_no_due_date_skipped(self, auth_client):
        """Payment schedule items without due_date are skipped (no obligation created)."""
        from modules.extraction import (
            DocType, ExtractedField, ExtractionResult, PaymentScheduleItem, TokenUsage,
        )

        result = ExtractionResult(
            doc_type=DocType.LEASE,
            doc_type_confidence=0.9,
            fields={
                "doi_tac": ExtractedField(value="Công ty A", confidence=0.9, needs_review=False),
                "ngay_hieu_luc": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
                "ngay_het_han": ExtractedField(value="2027-01-01", confidence=0.85, needs_review=False),
                "gia_tri_hd": ExtractedField(value="100000000", confidence=0.8, needs_review=True),
                "thoi_han_hd": ExtractedField(value="12 tháng", confidence=0.9, needs_review=False),
                "dieu_khoan_gia_han": ExtractedField(value="Tự động gia hạn", confidence=0.7, needs_review=True),
                "dieu_khoan_thanh_toan": ExtractedField(value="Chuyển khoản", confidence=0.9, needs_review=False),
            },
            payment_schedule=[
                PaymentScheduleItem(amount="50000000", due_date=None, milestone="Theo thông báo", recurrence=None),
            ],
            provider="fake_provider",
            model="fake-model",
            latency_ms=123.0,
            usage=TokenUsage(input_tokens=1000, output_tokens=200),
            cost_vnd=500.0,
        )

        fake = FakeProvider(result)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("no_due_date_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        data = auth_client.get(f"/documents/{doc_id}").json()
        obligations = data.get("obligations", [])
        # Only the expiry obligation from derive_obligations, no payment obligation
        assert not any("Theo thông báo" in o.get("description", "") for o in obligations)

    def test_payment_obligations_idempotent_on_re_extraction_skip_path(self, auth_client):
        """Re-extraction on a doc where derive_obligations skips (no derivable expiry)
        must not duplicate payment obligations — regression for #141 blocker 2."""
        from modules.extraction import (
            DocType, ExtractedField, ExtractionResult, PaymentScheduleItem, TokenUsage,
        )

        # No ngay_het_han, no ngay_hieu_luc + numeric thoi_han_hd → derive_obligations skips.
        # Payment schedule has 2 items with due_date → 2 payment obligations expected.
        result = ExtractionResult(
            doc_type=DocType.OTHER,
            doc_type_confidence=0.5,
            fields={
                "doi_tac": ExtractedField(value="Công ty A", confidence=0.9, needs_review=False),
                "ngay_hieu_luc": ExtractedField(value=None, confidence=0.0, needs_review=True),
                "ngay_het_han": ExtractedField(value=None, confidence=0.0, needs_review=True),
                "gia_tri_hd": ExtractedField(value="50000000", confidence=0.8, needs_review=True),
                "thoi_han_hd": ExtractedField(value="theo thông báo", confidence=0.5, needs_review=True),
                "dieu_khoan_gia_han": ExtractedField(value=None, confidence=0.0, needs_review=True),
                "dieu_khoan_thanh_toan": ExtractedField(value="Theo đợt", confidence=0.7, needs_review=True),
            },
            payment_schedule=[
                PaymentScheduleItem(amount="25000000", due_date="2026-06-01", milestone="Đợt 1", recurrence=None),
                PaymentScheduleItem(amount="25000000", due_date="2026-09-01", milestone="Đợt 2", recurrence=None),
            ],
            provider="fake_provider",
            model="fake-model",
            latency_ms=123.0,
            usage=TokenUsage(input_tokens=1000, output_tokens=200),
            cost_vnd=500.0,
        )

        fake = FakeProvider(result)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("idem_payment_test.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        data = auth_client.get(f"/documents/{doc_id}").json()
        payment_obs = [o for o in data.get("obligations", []) if "Đợt" in o.get("description", "")]
        assert len(payment_obs) == 2, f"Expected 2 payment obligations after first extraction, got {len(payment_obs)}"

        # Re-extract — must NOT duplicate payment obligations.
        fake2 = FakeProvider(result)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake2):
            from app.services.extraction_runner import run_extraction
            run_extraction(doc_id, "extract-tenant", None)

        data2 = auth_client.get(f"/documents/{doc_id}").json()
        payment_obs2 = [o for o in data2.get("obligations", []) if "Đợt" in o.get("description", "")]
        assert len(payment_obs2) == 2, (
            f"Expected 2 payment obligations after re-extraction (idempotent), got {len(payment_obs2)} — duplication bug"
        )
