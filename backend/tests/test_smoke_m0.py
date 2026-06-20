"""M0 smoke test — full vertical slice.

Upload → Extract → Derive → Chat → Reminder in one test flow.
Uses mock provider (no real API calls) and mock Telegram sender.
"""
import asyncio
import io
import os
import sys
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.models.tenant import Document, Obligation, Term
from app.services import chat_query
from app.services.consent import record_consent
from app.services.reminders import compute_due_window, _flip_overdue_status, send_reminders_for_tenant
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


def _mock_select_tools(calls):
    async def _select(*args, **kwargs):
        return calls
    return _select


def _mock_format_answer(answer):
    async def _format(*args, **kwargs):
        return answer
    return _format


class TestM0VerticalSlice:
    """Full M0 flow: upload → extract → derive → chat → reminder."""

    def test_full_flow(self, auth_client, tenant_with_legal_name, db, monkeypatch):
        """End-to-end M0 smoke test with mocked provider + Telegram."""
        # ── 1. Upload + Extract ───────────────────────────────────────────
        due_date_str = (date.today() + timedelta(days=15)).isoformat()
        result = make_extraction_result(
            doc_type=DocType.LEASE,
            doc_type_group="bat_dong_san",
            fields={
                "doi_tac": ExtractedField(value="Công ty TNHH Test ABC", confidence=0.9, needs_review=False),
                "ngay_hieu_luc": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
                "ngay_het_han": ExtractedField(value=due_date_str, confidence=0.9, needs_review=False),
                "gia_tri_hd": ExtractedField(value="500000000", confidence=0.85, needs_review=True),
            },
            parties=[
                PartyItem(name="Công ty TNHH Test ABC", role_label="Bên thuê"),
                PartyItem(name="Công ty Landlord", role_label="Bên cho thuê"),
            ],
            obligation_schedule=[
                ObligationScheduleItem(
                    obligation_type="payment",
                    description="Thanh toán đợt 1",
                    amount_raw="250000000",
                    due_date=due_date_str,
                    obligor="Bên thuê",
                ),
            ],
        )
        fake = FakeVisionProvider(result)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("m0_smoke.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            doc_id = r.json()["doc_id"]

        # ── 2. Verify extraction ──────────────────────────────────────────
        doc_data = auth_client.get(f"/documents/{doc_id}").json()
        assert doc_data["status"] == "extracted"
        term_map = {t["field_name"]: t for t in doc_data["terms"]}
        assert term_map["doc_type_group"]["field_value"] == "bat_dong_san"
        assert term_map["ngay_het_han"]["field_value"] == due_date_str
        assert term_map["doi_tac"]["field_value"] == "Công ty TNHH Test ABC"

        # ── 3. Verify obligation derivation ───────────────────────────────
        obligations = doc_data["obligations"]
        assert len(obligations) >= 1

        # Expiration obligation from derive_obligations
        exp_obs = [o for o in obligations if o["obligation_type"] == "expiration"]
        assert len(exp_obs) == 1
        assert exp_obs[0]["due_date"] == due_date_str
        assert exp_obs[0]["recurrence"] == "once"

        # Payment obligation from obligation_schedule
        pay_obs = [o for o in obligations if o["obligation_type"] == "payment"]
        assert len(pay_obs) == 1
        assert pay_obs[0]["due_date"] == due_date_str
        # Bên thuê = self (legal_name match) → nghĩa_vụ
        assert pay_obs[0]["direction"] == "nghĩa_vụ"
        assert pay_obs[0]["obligor"] == "Bên thuê"

        # ── 4. Chat query ─────────────────────────────────────────────────
        monkeypatch.setattr(
            chat_query,
            "_select_tools",
            _mock_select_tools([{
                "name": "search_terms",
                "args": {"field_name": "ngay_het_han", "doc_hint": "m0_smoke"},
            }]),
        )
        monkeypatch.setattr(
            chat_query,
            "_format_answer",
            _mock_format_answer(f"Hợp đồng hết hạn ngày {due_date_str}."),
        )

        r_chat = auth_client.post(
            "/chat/query",
            json={"question": "hợp đồng m0_smoke hết hạn khi nào?"},
        )
        assert r_chat.status_code == 200
        chat_data = r_chat.json()
        assert chat_data["found"] is True
        assert due_date_str in chat_data["answer"]
        assert any(s["file_name"] == "m0_smoke.pdf" for s in chat_data["sources"])

        # ── 5. Reminder flow ──────────────────────────────────────────────
        # Record consent for reminder_send
        record_consent(
            db, tenant_with_legal_name, "reminder_send",
            actor="qcuser", entity_id=1,
            channel="telegram", channel_target_ref="123456789",
        )

        # Compute due window — obligation due in 15 days, remind_before=30
        due_obs = compute_due_window(db, tenant_with_legal_name)
        assert len(due_obs) >= 1
        assert any(o.due_date == due_date_str for o in due_obs)

        # Mock Telegram send and run reminder batch
        with patch(
            "app.services.reminders.send_obligation_reminder",
            new_callable=AsyncMock,
            return_value=True,
        ):
            stats = asyncio.run(
                send_reminders_for_tenant(db, tenant_with_legal_name)
            )
        assert stats["sent"] >= 1
        assert stats["consent"] is True

        # ── 6. Verify idempotency — second run skips already-sent ─────────
        with patch(
            "app.services.reminders.send_obligation_reminder",
            new_callable=AsyncMock,
            return_value=True,
        ):
            stats2 = asyncio.run(
                send_reminders_for_tenant(db, tenant_with_legal_name)
            )
        assert stats2["skipped"] >= 1
        assert stats2["sent"] == 0

    def test_overdue_flow(self, auth_client, test_tenant, db):
        """Obligation past due → overdue status + still in due window check."""
        from app.services.obligation_engine import derive_obligations

        doc = Document(
            tenant_id=test_tenant,
            file_name="overdue_smoke.pdf",
            file_path=f"{test_tenant}/overdue.pdf",
            status="extracted",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        past_date = (date.today() - timedelta(days=30)).isoformat()
        db.add(Term(
            tenant_id=test_tenant, document_id=doc.id,
            field_name="ngay_het_han", field_value=past_date, confidence=0.9,
        ))
        db.commit()

        result = derive_obligations(db, test_tenant, doc.id)
        assert result["created"] == 1

        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        assert ob.status == "pending"

        flipped = _flip_overdue_status(db, test_tenant)
        assert flipped >= 1
        db.refresh(ob)
        assert ob.status == "overdue"

        # Overdue obligations should NOT be in the due window (only pending)
        due_obs = compute_due_window(db, test_tenant)
        assert not any(o.id == ob.id for o in due_obs)
