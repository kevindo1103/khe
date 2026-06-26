"""DEC-029 extraction coverage — doc_type_group classification + type-specific fields.

Tests that:
1. doc_type_group is classified and stored as a Term row.
2. Type-specific fields are extracted only for the matching group.
3. The 12 CANONICAL_FIELDS are always attempted.
4. Null type-specific fields are not persisted (spec) — see xfail note.
5. Chat query doc_type_filter narrows search_terms + search_obligations.

All extraction uses FakeVisionProvider (no real API calls).
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

from app.services import chat_query
from main import app
from modules.extraction import (
    DocType,
    ExtractedField,
    ExtractionResult,
    TokenUsage,
)
from tests.conftest import FakeVisionProvider, make_extraction_result


def _pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"


def _upload_and_extract(auth_client, result, file_name="test.pdf"):
    """Upload with a mock provider and return the doc_id."""
    fake = FakeVisionProvider(result)
    with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
        r = auth_client.post(
            "/ingest/upload",
            files={"file": (file_name, io.BytesIO(_pdf_bytes()), "application/pdf")},
        )
        assert r.status_code == 201, f"Upload failed: {r.status_code} {r.text}"
        return r.json()["doc_id"]


# ── DocTypeGroup classification ──────────────────────────────────────────

class TestDocTypeGroupClassification:
    def test_thuong_mai_classified(self, auth_client, test_tenant):
        """doc_type_group='thuong_mai' → Term saved with correct value."""
        result = make_extraction_result(doc_type_group="thuong_mai")
        doc_id = _upload_and_extract(auth_client, result, "thuong_mai.pdf")

        data = auth_client.get(f"/documents/{doc_id}").json()
        terms = {t["field_name"]: t for t in data["terms"]}
        assert "doc_type_group" in terms
        assert terms["doc_type_group"]["field_value"] == "thuong_mai"

    def test_lao_dong_classified(self, auth_client, test_tenant):
        """doc_type_group='lao_dong' → type-specific fields: luong_co_ban, thoi_gian_thu_viec."""
        result = make_extraction_result(
            doc_type=DocType.LABOR,
            doc_type_group="lao_dong",
            type_specific={
                "luong_co_ban": ExtractedField(value="15000000", confidence=0.85, needs_review=False),
                "thoi_gian_thu_viec": ExtractedField(value="60 ngày", confidence=0.8, needs_review=True),
                "chu_ky_dong_bao_hiem": ExtractedField(value="12 tháng", confidence=0.8, needs_review=False),
            },
        )
        doc_id = _upload_and_extract(auth_client, result, "lao_dong.pdf")

        data = auth_client.get(f"/documents/{doc_id}").json()
        terms = {t["field_name"]: t for t in data["terms"]}
        assert terms["doc_type_group"]["field_value"] == "lao_dong"
        assert terms["luong_co_ban"]["field_value"] == "15000000"
        assert terms["thoi_gian_thu_viec"]["field_value"] == "60 ngày"
        assert terms["chu_ky_dong_bao_hiem"]["field_value"] == "12 tháng"

    def test_bat_dong_san_classified(self, auth_client, test_tenant):
        """doc_type_group='bat_dong_san' → type-specific: dia_chi_tai_san, dien_tich."""
        result = make_extraction_result(
            doc_type_group="bat_dong_san",
            type_specific={
                "dia_chi_tai_san": ExtractedField(value="123 Lê Lợi, Q1", confidence=0.9, needs_review=False),
                "dien_tich": ExtractedField(value="50m2", confidence=0.85, needs_review=False),
            },
        )
        doc_id = _upload_and_extract(auth_client, result, "bat_dong_san.pdf")

        data = auth_client.get(f"/documents/{doc_id}").json()
        terms = {t["field_name"]: t for t in data["terms"]}
        assert terms["doc_type_group"]["field_value"] == "bat_dong_san"
        assert terms["dia_chi_tai_san"]["field_value"] == "123 Lê Lợi, Q1"
        assert terms["dien_tich"]["field_value"] == "50m2"

    def test_unknown_group_falls_back_to_other(self, auth_client, test_tenant):
        """doc_type_group not in enum → stored as provided (provider decides)."""
        result = make_extraction_result(doc_type_group="other")
        doc_id = _upload_and_extract(auth_client, result, "unknown.pdf")

        data = auth_client.get(f"/documents/{doc_id}").json()
        terms = {t["field_name"]: t for t in data["terms"]}
        assert terms["doc_type_group"]["field_value"] == "other"


# ── Type-specific field storage ──────────────────────────────────────────

class TestTypeSpecificFieldStorage:
    def test_canonical_fields_always_saved(self, auth_client, test_tenant):
        """All 12 CANONICAL_FIELDS present in result.fields → all saved as Term rows."""
        from modules.extraction import CANONICAL_FIELDS

        result = make_extraction_result(doc_type_group="thuong_mai")
        doc_id = _upload_and_extract(auth_client, result, "canonical.pdf")

        data = auth_client.get(f"/documents/{doc_id}").json()
        term_names = {t["field_name"] for t in data["terms"]}
        for field_name in CANONICAL_FIELDS:
            assert field_name in term_names, f"Canonical field '{field_name}' not saved"

    def test_type_specific_only_for_matching_group(self, auth_client, test_tenant):
        """lao_dong doc only extracts lao_dong fields, not bat_dong_san fields."""
        result = make_extraction_result(
            doc_type=DocType.LABOR,
            doc_type_group="lao_dong",
            type_specific={
                "luong_co_ban": ExtractedField(value="15000000", confidence=0.85, needs_review=False),
            },
        )
        doc_id = _upload_and_extract(auth_client, result, "labor_only.pdf")

        data = auth_client.get(f"/documents/{doc_id}").json()
        terms = {t["field_name"]: t for t in data["terms"]}
        assert "luong_co_ban" in terms
        # bat_dong_san fields should NOT be present
        assert "dia_chi_tai_san" not in terms
        assert "dien_tich" not in terms

    @pytest.mark.xfail(
        reason=(
            "SPEC CONFLICT: extraction_runner.py L146-148 intentionally saves "
            "null-value Term rows for D-07/FR-EX-05 (admin review UI needs a row "
            "to edit). Spec says null type-specific fields should NOT be saved. "
            "Code does not distinguish universal vs type-specific for null handling. "
            "Report to KHE_QC lead — bug in application code, not test code."
        ),
        strict=True,
    )
    def test_null_type_specific_not_saved(self, auth_client, test_tenant):
        """Field with value=None → should NOT insert Term row (per spec)."""
        result = make_extraction_result(
            doc_type_group="lao_dong",
            type_specific={
                "luong_co_ban": ExtractedField(value=None, confidence=0.0, needs_review=True),
                "thoi_gian_thu_viec": ExtractedField(value="60 ngày", confidence=0.8, needs_review=False),
            },
        )
        doc_id = _upload_and_extract(auth_client, result, "null_field.pdf")

        data = auth_client.get(f"/documents/{doc_id}").json()
        terms = {t["field_name"]: t for t in data["terms"]}
        # Spec: null type-specific field should NOT be saved
        assert "luong_co_ban" not in terms, (
            "Null type-specific field was saved as Term row — spec says it should not be"
        )
        # Non-null field should still be saved
        assert "thoi_gian_thu_viec" in terms


# ── doc_type_filter in chat search ───────────────────────────────────────

def _mock_select_tools(calls):
    async def _select(*args, **kwargs):
        return calls, {"in": 100, "out": 20}
    return _select


def _mock_format_answer(answer):
    async def _format(*args, **kwargs):
        return answer, {"in": 200, "out": 50}
    return _format


class TestDocTypeFilter:
    def test_search_terms_doc_type_filter(
        self, auth_client, test_tenant, db, sample_doc_thuong_mai, monkeypatch
    ):
        """search_terms with doc_type_filter='thuong_mai' → only thuong_mai docs."""
        from app.models.tenant import Document, Term as TermModel

        # Create a second doc with a different doc_type_group
        doc2 = Document(
            tenant_id=test_tenant,
            file_name="labor_doc.pdf",
            file_path=f"{test_tenant}/labor.pdf",
            doc_type="hd_lao_dong",
            status="extracted",
        )
        db.add(doc2)
        db.commit()
        db.refresh(doc2)
        db.add(TermModel(
            tenant_id=test_tenant, document_id=doc2.id,
            field_name="ngay_het_han", field_value="2028-01-01", confidence=0.9,
        ))
        db.add(TermModel(
            tenant_id=test_tenant, document_id=doc2.id,
            field_name="doc_type_group", field_value="lao_dong", confidence=0.95,
        ))
        db.commit()

        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools([{
                "name": "search_terms",
                "args": {"field_name": "ngay_het_han", "doc_hint": None, "doc_type_filter": "thuong_mai"},
            }]),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Hết hạn 2027-01-01."))

        r = auth_client.post("/chat/query", json={"question": "HĐ thương mại hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        # Only thuong_mai doc's expiry should be in sources
        values = [s["value"] for s in data["sources"] if s["type"] == "term"]
        assert "2027-01-01" in values
        assert "2028-01-01" not in values

    def test_search_obligations_doc_type_filter(
        self, auth_client, test_tenant, db, monkeypatch
    ):
        """search_obligations with doc_type_filter='lao_dong' → only lao_dong obligations."""
        from app.models.tenant import Document, Obligation, Term as TermModel

        # Create two docs with different doc_type_groups + obligations
        doc_tm = Document(
            tenant_id=test_tenant, file_name="tm.pdf",
            file_path=f"{test_tenant}/tm.pdf", status="extracted",
        )
        doc_ld = Document(
            tenant_id=test_tenant, file_name="ld.pdf",
            file_path=f"{test_tenant}/ld.pdf", status="extracted",
        )
        db.add_all([doc_tm, doc_ld])
        db.commit()
        db.refresh(doc_tm)
        db.refresh(doc_ld)

        for doc, group in [(doc_tm, "thuong_mai"), (doc_ld, "lao_dong")]:
            db.add(TermModel(
                tenant_id=test_tenant, document_id=doc.id,
                field_name="doc_type_group", field_value=group, confidence=0.95,
            ))
            db.add(Obligation(
                tenant_id=test_tenant, document_id=doc.id,
                description=f"Hết hạn {doc.file_name}",
                recurrence="once", due_date="2027-06-01", status="pending",
            ))
        db.commit()

        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools([{
                "name": "search_obligations",
                "args": {
                    "due_within_days": 365,
                    "status": "pending",
                    "doc_hint": None,
                    "doc_type_filter": "lao_dong",
                },
            }]),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Hết hạn 2027-06-01."))

        r = auth_client.post("/chat/query", json={"question": "HĐ lao động hết hạn khi nào?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        file_names = [s["file_name"] for s in data["sources"]]
        assert "ld.pdf" in file_names
        assert "tm.pdf" not in file_names
