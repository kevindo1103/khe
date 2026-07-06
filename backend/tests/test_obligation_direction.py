"""DEC-030 obligation direction — self-party match + direction derivation.

Tests that:
1. _derive_direction correctly identifies self vs counterparty.
2. Payment obligations get direction stored after extraction.
3. Chat query search_obligations filters by direction.
4. No legal_name / no obligor / no party match → None (D-08).

Uses tenant_with_legal_name fixture for self-party matching.
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

from app.models.tenant import Document, Obligation, Term
from app.services import chat_query
from app.services.extraction_runner import _derive_direction
from main import app
from modules.extraction import (
    DocType,
    ExtractedField,
    ExtractionResult,
    ObligationScheduleItem,
    PartyItem,
    TokenUsage,
)
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
        assert r.status_code == 201, f"Upload failed: {r.status_code} {r.text}"
        return r.json()["doc_id"]


# ── _derive_direction unit tests ─────────────────────────────────────────

class TestDeriveDirection:
    def test_self_match_returns_nghia_vu(self):
        """obligor matches self-party role_label → nghĩa_vụ."""
        class FakeResult:
            parties = [PartyItem(name="Công ty TNHH Test ABC", role_label="Bên A")]

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value="Công ty TNHH Test ABC",
        ):
            result = _derive_direction("test-tenant", "Bên A", FakeResult())
        assert result == "nghĩa_vụ"

    def test_counterparty_returns_quyen_loi(self):
        """obligor is the counterparty → quyền_lợi."""
        class FakeResult:
            parties = [
                PartyItem(name="Công ty TNHH Test ABC", role_label="Bên A"),
                PartyItem(name="Công ty XYZ", role_label="Bên B"),
            ]

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value="Công ty TNHH Test ABC",
        ):
            result = _derive_direction("test-tenant", "Bên B", FakeResult())
        assert result == "quyền_lợi"

    def test_no_legal_name_returns_none(self):
        """Tenant has no legal_name → None (D-08)."""
        class FakeResult:
            parties = []

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value=None,
        ):
            result = _derive_direction("test-tenant", "Bên A", FakeResult())
        assert result is None

    def test_no_obligor_returns_none(self):
        """No obligor → None (D-08)."""
        result = _derive_direction("test-tenant", None, None)
        assert result is None

    def test_no_party_match_returns_none(self):
        """No party matches legal_name → None (needs_review)."""
        class FakeResult:
            parties = [PartyItem(name="Công ty XYZ", role_label="Bên B")]

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value="Công ty TNHH Test ABC",
        ):
            result = _derive_direction("test-tenant", "Bên B", FakeResult())
        assert result is None

    def test_fuzzy_match_case_insensitive(self):
        """Legal name match is case-insensitive + substring."""
        class FakeResult:
            parties = [PartyItem(name="CÔNG TY TNHH TEST ABC", role_label="NSDLĐ")]

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value="công ty tnhh test abc",
        ):
            result = _derive_direction("test-tenant", "NSDLĐ", FakeResult())
        assert result == "nghĩa_vụ"

    def test_fuzzy_match_partial_name(self):
        """Legal name substring match works (legal_name contains party name)."""
        class FakeResult:
            parties = [PartyItem(name="Test ABC", role_label="Bên thuê")]

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value="Công ty TNHH Test ABC",
        ):
            result = _derive_direction("test-tenant", "Bên thuê", FakeResult())
        assert result == "nghĩa_vụ"

    def test_diacritics_normalization_legal_name(self):
        """legal_name without diacritics matches extracted party name with diacritics (B1 #282)."""
        class FakeResult:
            parties = [PartyItem(name="Công ty TNHH Test ABC", role_label="Bên A")]

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value="Cong ty TNHH Test ABC",  # no diacritics — common user input
        ):
            result = _derive_direction("test-tenant", "Bên A", FakeResult())
        assert result == "nghĩa_vụ"

    def test_obligor_matches_party_name_not_only_role_label(self):
        """Obligor = full company name (not role_label) → still resolves direction (B1 #282)."""
        class FakeResult:
            parties = [
                PartyItem(name="Công ty TNHH Test ABC", role_label="Bên A"),
                PartyItem(name="Công ty XYZ", role_label="Bên B"),
            ]

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value="Công ty TNHH Test ABC",
        ):
            # LLM emitted full company name as obligor instead of role_label
            result = _derive_direction("test-tenant", "Công ty TNHH Test ABC", FakeResult())
        assert result == "nghĩa_vụ"

    def test_counterparty_by_name_returns_quyen_loi(self):
        """Obligor = counterparty's full name → quyền_lợi."""
        class FakeResult:
            parties = [
                PartyItem(name="Công ty TNHH Test ABC", role_label="Bên A"),
                PartyItem(name="Công ty XYZ", role_label="Bên B"),
            ]

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value="Công ty TNHH Test ABC",
        ):
            result = _derive_direction("test-tenant", "Công ty XYZ", FakeResult())
        assert result == "quyền_lợi"

    def test_diacritics_normalization_obligor(self):
        """Obligor without diacritics matches normalized role_label with diacritics."""
        class FakeResult:
            parties = [PartyItem(name="Công ty TNHH Test ABC", role_label="Bên mua")]

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value="Công ty TNHH Test ABC",
        ):
            # obligor without diacritics on "Bên mua" → "Ben mua" matches "ben mua"
            result = _derive_direction("test-tenant", "Ben mua", FakeResult())
        assert result == "nghĩa_vụ"

    def test_d_stroke_normalization_legal_name(self):
        """đ/Đ (U+0111) has no NFD decomp — legal_name with đ must still self-match.

        Before fix: _norm('Đầu tư ABC') → 'u abc' (đ silently dropped) → no match.
        After fix: pre-replace đ→d → _norm('Đầu tư ABC') → 'dau tu abc' → matches.
        """
        class FakeResult:
            parties = [PartyItem(name="Công ty Đầu tư ABC", role_label="Bên A")]

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value="Công ty Đầu tư ABC",
        ):
            result = _derive_direction("test-tenant", "Bên A", FakeResult())
        assert result == "nghĩa_vụ", "Legal name with đ failed D-13 self-match (đ→d pre-replace missing)"

    def test_d_stroke_in_obligor(self):
        """Obligor containing đ must match normalized legal_name."""
        class FakeResult:
            parties = [PartyItem(name="Điện lực Miền Nam", role_label="Bên bán")]

        with patch(
            "app.services.extraction_runner._get_tenant_legal_name",
            return_value="Điện lực Miền Nam",
        ):
            result = _derive_direction("test-tenant", "Điện lực Miền Nam", FakeResult())
        assert result == "nghĩa_vụ"


# ── Full extraction flow with direction ──────────────────────────────────

class TestDirectionStoredOnObligation:
    def test_payment_obligation_gets_direction(
        self, auth_client, tenant_with_legal_name, db
    ):
        """Obligation schedule with obligor → Obligation.direction set."""
        result = make_extraction_result(
            doc_type_group="thuong_mai",
            parties=[
                PartyItem(name="Công ty TNHH Test ABC", role_label="Bên A"),
                PartyItem(name="Công ty XYZ", role_label="Bên B"),
            ],
            obligation_schedule=[
                ObligationScheduleItem(
                    obligation_type="payment",
                    description="Thanh toán đợt 1",
                    amount_raw="50000000",
                    due_date="2026-03-01",
                    obligor="Bên A",
                ),
                ObligationScheduleItem(
                    obligation_type="payment",
                    description="Thanh toán đợt 2",
                    amount_raw="30000000",
                    due_date="2026-06-01",
                    obligor="Bên B",
                ),
            ],
        )
        doc_id = _upload_and_extract(auth_client, result, "direction_test.pdf")

        obs = db.query(Obligation).filter(
            Obligation.document_id == doc_id,
            Obligation.obligation_type == "payment",
        ).all()
        assert len(obs) == 2

        by_milestone = {ob.description: ob for ob in obs}
        # Bên A = self → nghĩa_vụ
        ob1 = by_milestone.get("Thanh toán đợt 1")
        assert ob1 is not None
        assert ob1.direction == "nghĩa_vụ"
        assert ob1.obligor == "Bên A"

        # Bên B = counterparty → quyền_lợi
        ob2 = by_milestone.get("Thanh toán đợt 2")
        assert ob2 is not None
        assert ob2.direction == "quyền_lợi"
        assert ob2.obligor == "Bên B"

    def test_no_payer_no_direction(self, auth_client, test_tenant, db):
        """Obligation schedule without obligor → direction=None."""
        result = make_extraction_result(
            doc_type_group="thuong_mai",
            obligation_schedule=[
                ObligationScheduleItem(
                    obligation_type="payment",
                    description="Thanh toán đợt 1",
                    amount_raw="50000000",
                    due_date="2026-03-01",
                    obligor=None,
                ),
            ],
        )
        doc_id = _upload_and_extract(auth_client, result, "no_payer.pdf")

        obs = db.query(Obligation).filter(
            Obligation.document_id == doc_id,
            Obligation.obligation_type == "payment",
        ).all()
        assert len(obs) == 1
        assert obs[0].direction is None
        assert obs[0].obligor is None

    def test_no_legal_name_no_direction(
        self, auth_client, test_tenant, db
    ):
        """Tenant without legal_name → direction=None even with obligor."""
        result = make_extraction_result(
            doc_type_group="thuong_mai",
            parties=[
                PartyItem(name="Công ty A", role_label="Bên A"),
            ],
            obligation_schedule=[
                ObligationScheduleItem(
                    obligation_type="payment",
                    description="Thanh toán",
                    amount_raw="50000000",
                    due_date="2026-03-01",
                    obligor="Bên A",
                ),
            ],
        )
        doc_id = _upload_and_extract(auth_client, result, "no_legal_name.pdf")

        obs = db.query(Obligation).filter(
            Obligation.document_id == doc_id,
            Obligation.obligation_type == "payment",
        ).all()
        assert len(obs) == 1
        assert obs[0].direction is None


# ── Chat query direction filter ──────────────────────────────────────────

def _mock_select_tools(calls):
    async def _select(*args, **kwargs):
        return calls, {"in": 100, "out": 20}
    return _select


def _mock_format_answer(answer):
    async def _format(*args, **kwargs):
        return answer, {"in": 200, "out": 50}
    return _format


class TestChatDirectionFilter:
    def test_search_obligations_direction_nghia_vu(
        self, auth_client, tenant_with_legal_name, db, monkeypatch
    ):
        """search_obligations(direction='nghĩa_vụ') → only self-obligations."""
        doc = Document(
            tenant_id=tenant_with_legal_name,
            file_name="direction_chat.pdf",
            file_path=f"{tenant_with_legal_name}/dir.pdf",
            status="extracted",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        db.add(Obligation(
            tenant_id=tenant_with_legal_name, document_id=doc.id,
            description="Tôi phải trả", recurrence="once",
            obligation_type="payment", direction="nghĩa_vụ",
            due_date="2027-01-01", status="pending",
        ))
        db.add(Obligation(
            tenant_id=tenant_with_legal_name, document_id=doc.id,
            description="Đối tác phải trả", recurrence="once",
            obligation_type="payment", direction="quyền_lợi",
            due_date="2027-02-01", status="pending",
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
                    "direction": "nghĩa_vụ",
                },
            }]),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Tôi phải trả 2027-01-01."))

        r = auth_client.post("/chat/query", json={"question": "Nghĩa vụ của tôi là gì?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        descriptions = [s["file_name"] for s in data["sources"]]
        # Only the nghĩa_vụ obligation should be returned
        assert len(data["sources"]) == 1
        assert data["sources"][0]["value"] == "2027-01-01"

    def test_search_obligations_direction_quyen_loi(
        self, auth_client, tenant_with_legal_name, db, monkeypatch
    ):
        """search_obligations(direction='quyền_lợi') → only counterparty obligations."""
        doc = Document(
            tenant_id=tenant_with_legal_name,
            file_name="quyen_loi.pdf",
            file_path=f"{tenant_with_legal_name}/ql.pdf",
            status="extracted",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        db.add(Obligation(
            tenant_id=tenant_with_legal_name, document_id=doc.id,
            description="Tôi phải trả", recurrence="once",
            obligation_type="payment", direction="nghĩa_vụ",
            due_date="2027-01-01", status="pending",
        ))
        db.add(Obligation(
            tenant_id=tenant_with_legal_name, document_id=doc.id,
            description="Đối tác phải trả", recurrence="once",
            obligation_type="payment", direction="quyền_lợi",
            due_date="2027-02-01", status="pending",
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
                    "direction": "quyền_lợi",
                },
            }]),
        )
        monkeypatch.setattr(chat_query, "_format_answer", _mock_format_answer("Đối tác phải trả 2027-02-01."))

        r = auth_client.post("/chat/query", json={"question": "Quyền lợi của tôi là gì?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert len(data["sources"]) == 1
        assert data["sources"][0]["value"] == "2027-02-01"
