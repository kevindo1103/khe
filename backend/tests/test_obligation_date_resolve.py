"""B3 (#282) — date-anchored obligation resolution tests.

Tests resolve_date_anchored_obligations():
1. Known anchor in Terms → obligation resolved to pending, due_date set.
2. Anchor date in the past → status set to overdue.
3. No trigger_delay_days → skipped (D-08: can't compute without guessing).
4. Unknown anchor keyword → stays waiting_trigger.
5. No anchor term in DB → stays waiting_trigger.
6. Event-trigger obligations untouched.
7. Already-pending obligations untouched.
8. Multiple obligations resolved in one call.
9. End-to-end: extraction persists date-anchored item and resolver fills it.
"""
import io
import os
import sys

from datetime import date, timedelta
from unittest.mock import patch

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest

from app.models.tenant import Document, Obligation, Term
from app.services.obligation_engine import resolve_date_anchored_obligations
from tests.conftest import FakeVisionProvider, make_extraction_result
from modules.extraction import ExtractedField, ObligationScheduleItem


def _make_doc(db, tenant_id, file_name="test.pdf"):
    doc = Document(
        tenant_id=tenant_id,
        file_name=file_name,
        file_path=f"{tenant_id}/{file_name}",
        status="extracted",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _make_term(db, tenant_id, doc_id, field_name, value):
    t = Term(
        tenant_id=tenant_id,
        document_id=doc_id,
        field_name=field_name,
        field_value=value,
        confidence=0.9,
    )
    db.add(t)
    db.commit()
    return t


def _make_waiting_obligation(db, tenant_id, doc_id, trigger_condition, delay_days, description="Test ob"):
    ob = Obligation(
        tenant_id=tenant_id,
        document_id=doc_id,
        description=description,
        obligation_type="payment",
        recurrence="once",
        status="waiting_trigger",
        milestone_trigger="date",
        trigger_condition=trigger_condition,
        trigger_delay_days=delay_days,
        due_date=None,
    )
    db.add(ob)
    db.commit()
    db.refresh(ob)
    return ob


class TestResolveDateAnchoredObligations:
    def test_known_anchor_resolves_to_pending(self, test_tenant, db):
        """Anchor term found → due_date set, status=pending."""
        doc = _make_doc(db, test_tenant)
        anchor_date = (date.today() + timedelta(days=60)).isoformat()
        _make_term(db, test_tenant, doc.id, "ngay_hieu_luc", anchor_date)
        ob = _make_waiting_obligation(
            db, test_tenant, doc.id,
            trigger_condition="Sau 30 ngày kể từ ngày hiệu lực",
            delay_days=30,
        )

        resolved = resolve_date_anchored_obligations(db, test_tenant, doc.id)

        db.refresh(ob)
        assert resolved == 1
        expected_due = (date.fromisoformat(anchor_date) + timedelta(days=30)).isoformat()
        assert ob.due_date == expected_due
        assert ob.status == "pending"

    def test_past_anchor_resolves_to_overdue(self, test_tenant, db):
        """Anchor + delay yields a past date → status=overdue."""
        doc = _make_doc(db, test_tenant)
        anchor_date = "2020-01-01"
        _make_term(db, test_tenant, doc.id, "ngay_ky", anchor_date)
        ob = _make_waiting_obligation(
            db, test_tenant, doc.id,
            trigger_condition="10 ngày kể từ ngày ký hợp đồng",
            delay_days=10,
        )

        resolved = resolve_date_anchored_obligations(db, test_tenant, doc.id)

        db.refresh(ob)
        assert resolved == 1
        assert ob.status == "overdue"
        assert ob.due_date == "2020-01-11"

    def test_no_trigger_delay_days_skipped(self, test_tenant, db):
        """trigger_delay_days=None → D-08: can't compute, skip."""
        doc = _make_doc(db, test_tenant)
        _make_term(db, test_tenant, doc.id, "ngay_hieu_luc", "2026-01-01")
        ob = _make_waiting_obligation(
            db, test_tenant, doc.id,
            trigger_condition="kể từ ngày hiệu lực",
            delay_days=None,
        )

        resolved = resolve_date_anchored_obligations(db, test_tenant, doc.id)

        db.refresh(ob)
        assert resolved == 0
        assert ob.status == "waiting_trigger"
        assert ob.due_date is None

    def test_unknown_anchor_keyword_skipped(self, test_tenant, db):
        """trigger_condition with no recognized anchor → stays waiting_trigger."""
        doc = _make_doc(db, test_tenant)
        _make_term(db, test_tenant, doc.id, "ngay_hieu_luc", "2026-01-01")
        ob = _make_waiting_obligation(
            db, test_tenant, doc.id,
            trigger_condition="Sau khi nghiệm thu bàn giao",  # unknown anchor
            delay_days=30,
        )

        resolved = resolve_date_anchored_obligations(db, test_tenant, doc.id)

        db.refresh(ob)
        assert resolved == 0
        assert ob.status == "waiting_trigger"
        assert ob.due_date is None

    def test_anchor_term_not_in_db_skipped(self, test_tenant, db):
        """Anchor term recognized but no Term row with that field_name → skip."""
        doc = _make_doc(db, test_tenant)
        # ngay_ky not in DB; only unrelated term present
        _make_term(db, test_tenant, doc.id, "doi_tac", "Cty XYZ")
        ob = _make_waiting_obligation(
            db, test_tenant, doc.id,
            trigger_condition="30 ngày từ ngày ký hợp đồng",
            delay_days=30,
        )

        resolved = resolve_date_anchored_obligations(db, test_tenant, doc.id)

        db.refresh(ob)
        assert resolved == 0
        assert ob.status == "waiting_trigger"

    def test_event_trigger_obligations_untouched(self, test_tenant, db):
        """milestone_trigger='event' obligations are not touched."""
        doc = _make_doc(db, test_tenant)
        _make_term(db, test_tenant, doc.id, "ngay_hieu_luc", "2026-01-01")
        ob = Obligation(
            tenant_id=test_tenant,
            document_id=doc.id,
            description="Event trigger ob",
            obligation_type="payment",
            recurrence="once",
            status="waiting_trigger",
            milestone_trigger="event",
            trigger_condition="Khi nghiệm thu",
            due_date=None,
        )
        db.add(ob)
        db.commit()
        db.refresh(ob)

        resolved = resolve_date_anchored_obligations(db, test_tenant, doc.id)

        db.refresh(ob)
        assert resolved == 0
        assert ob.status == "waiting_trigger"

    def test_already_pending_obligations_untouched(self, test_tenant, db):
        """Obligations already in pending status are not re-processed."""
        doc = _make_doc(db, test_tenant)
        _make_term(db, test_tenant, doc.id, "ngay_hieu_luc", "2026-01-01")
        ob = Obligation(
            tenant_id=test_tenant,
            document_id=doc.id,
            description="Already pending",
            obligation_type="payment",
            recurrence="once",
            status="pending",
            milestone_trigger="date",
            trigger_condition="30 ngày từ ngày hiệu lực",
            due_date="2026-01-31",
        )
        db.add(ob)
        db.commit()
        db.refresh(ob)

        resolved = resolve_date_anchored_obligations(db, test_tenant, doc.id)

        db.refresh(ob)
        assert resolved == 0
        assert ob.status == "pending"

    def test_multiple_obligations_resolved(self, test_tenant, db):
        """Multiple waiting_trigger obligations resolved in one pass."""
        doc = _make_doc(db, test_tenant)
        anchor = (date.today() + timedelta(days=90)).isoformat()
        _make_term(db, test_tenant, doc.id, "ngay_hieu_luc", anchor)
        _make_term(db, test_tenant, doc.id, "ngay_ky", anchor)

        ob1 = _make_waiting_obligation(
            db, test_tenant, doc.id,
            trigger_condition="30 ngày từ ngày hiệu lực",
            delay_days=30,
            description="Ob1",
        )
        ob2 = _make_waiting_obligation(
            db, test_tenant, doc.id,
            trigger_condition="60 ngày từ ngày ký kết",
            delay_days=60,
            description="Ob2",
        )

        resolved = resolve_date_anchored_obligations(db, test_tenant, doc.id)

        db.refresh(ob1)
        db.refresh(ob2)
        assert resolved == 2
        assert ob1.status == "pending"
        assert ob2.status == "pending"

    def test_no_terms_returns_zero(self, test_tenant, db):
        """No Terms in DB → returns 0 without error."""
        doc = _make_doc(db, test_tenant)
        ob = _make_waiting_obligation(
            db, test_tenant, doc.id,
            trigger_condition="30 ngày từ ngày hiệu lực",
            delay_days=30,
        )

        resolved = resolve_date_anchored_obligations(db, test_tenant, doc.id)

        assert resolved == 0

    def test_tenant_isolation(self, test_tenant, db):
        """Resolver only touches obligations belonging to the given tenant."""
        doc = _make_doc(db, test_tenant)
        anchor = (date.today() + timedelta(days=30)).isoformat()
        _make_term(db, test_tenant, doc.id, "ngay_hieu_luc", anchor)

        # Obligation belongs to a different tenant_id
        other_ob = Obligation(
            tenant_id="other-tenant-xyz",
            document_id=doc.id,
            description="Other tenant ob",
            obligation_type="payment",
            recurrence="once",
            status="waiting_trigger",
            milestone_trigger="date",
            trigger_condition="10 ngày từ ngày hiệu lực",
            trigger_delay_days=10,
            due_date=None,
        )
        db.add(other_ob)
        db.commit()
        db.refresh(other_ob)

        resolved = resolve_date_anchored_obligations(db, test_tenant, doc.id)

        db.refresh(other_ob)
        assert other_ob.status == "waiting_trigger"


class TestExtractionRunnerB3Integration:
    """End-to-end: extraction persists date-anchored item → resolver fills due_date."""

    def test_date_anchored_item_resolved_after_extraction(
        self, auth_client, test_tenant, db
    ):
        """ObligationScheduleItem with trigger='date' and no due_date is persisted
        as waiting_trigger, then resolver fills in due_date from ngay_hieu_luc."""
        future_date = (date.today() + timedelta(days=90)).isoformat()

        result = make_extraction_result(
            doc_type_group="thuong_mai",
            fields={
                "ngay_hieu_luc": ExtractedField(
                    value=future_date, confidence=0.9, needs_review=False
                ),
            },
            obligation_schedule=[
                ObligationScheduleItem(
                    obligation_type="payment",
                    description="Thanh toán sau 30 ngày hiệu lực",
                    amount_raw="50000000",
                    due_date=None,
                    obligor="Bên A",
                    trigger="date",
                    trigger_condition="30 ngày kể từ ngày hiệu lực",
                    trigger_delay_days=30,
                ),
            ],
        )

        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=FakeVisionProvider(result)):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("b3_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            )
            assert r.status_code == 201, f"Upload failed: {r.status_code} {r.text}"
            doc_id = r.json()["doc_id"]

        obs = db.query(Obligation).filter(
            Obligation.document_id == doc_id,
            Obligation.description == "Thanh toán sau 30 ngày hiệu lực",
        ).all()
        assert len(obs) == 1
        ob = obs[0]

        expected_due = (date.fromisoformat(future_date) + timedelta(days=30)).isoformat()
        assert ob.due_date == expected_due, f"Expected {expected_due}, got {ob.due_date}"
        assert ob.status == "pending"
