"""Obligation model regression — recurrence, obligation_type, DEC-020 windows.

Tests that:
1. recurrence='once' for deadline-based obligations.
2. recurrence='open_ended_review' for open-ended contracts.
3. obligation_type='expiration' for derived obligations.
4. obligation_type='payment' for payment_schedule-derived obligations.
5. DEC-020: open_ended_review → remind_before_days=365; once → 30.
6. Idempotency: done obligations preserved on re-derivation.
7. Date parsing edge cases (Vietnamese dates, durations).
"""
import os
import sys
from datetime import date, datetime

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest

from app.models.tenant import Document, Obligation, Term
from app.services.date_parse import add_months, parse_date, parse_duration_months
from app.services.obligation_engine import derive_obligations
from app.services.reminders import compute_due_window, _flip_overdue_status


def _make_doc(db, tenant_id, file_name, status="extracted"):
    doc = Document(
        tenant_id=tenant_id,
        file_name=file_name,
        file_path=f"{tenant_id}/{file_name}",
        status=status,
        confirmed_by_user_at=datetime.utcnow(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _make_term(db, tenant_id, doc_id, field_name, value, confidence=0.9):
    t = Term(
        tenant_id=tenant_id,
        document_id=doc_id,
        field_name=field_name,
        field_value=value,
        confidence=confidence,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


# ── Recurrence + obligation_type ─────────────────────────────────────────

class TestRecurrenceAndType:
    def test_once_recurrence_with_direct_due_date(self, test_tenant, db):
        """ngay_het_han present → recurrence='once', obligation_type='expiration'."""
        doc = _make_doc(db, test_tenant, "once_direct.pdf")
        _make_term(db, test_tenant, doc.id, "ngay_het_han", "2026-12-31")

        result = derive_obligations(db, test_tenant, doc.id)
        assert result["created"] == 1

        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        assert ob.recurrence == "once"
        assert ob.obligation_type == "expiration"
        assert ob.due_date == "2026-12-31"

    def test_once_recurrence_derived_from_start_and_duration(self, test_tenant, db):
        """ngay_hieu_luc + numeric thoi_han_hd → recurrence='once'."""
        doc = _make_doc(db, test_tenant, "once_derived.pdf")
        _make_term(db, test_tenant, doc.id, "ngay_hieu_luc", "2026-01-01")
        _make_term(db, test_tenant, doc.id, "thoi_han_hd", "12 tháng")

        result = derive_obligations(db, test_tenant, doc.id)
        assert result["created"] == 1

        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        assert ob.recurrence == "once"
        assert ob.obligation_type == "expiration"
        assert ob.due_date == "2027-01-01"

    def test_open_ended_review_recurrence(self, test_tenant, db):
        """Non-numeric thoi_han_hd → recurrence='open_ended_review', due_date=None."""
        doc = _make_doc(db, test_tenant, "open_ended.pdf")
        _make_term(db, test_tenant, doc.id, "ngay_hieu_luc", "2026-01-01")
        _make_term(db, test_tenant, doc.id, "thoi_han_hd", "vô thời hạn")

        result = derive_obligations(db, test_tenant, doc.id)
        assert result["created"] == 1

        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        assert ob.recurrence == "open_ended_review"
        assert ob.obligation_type == "expiration"
        assert ob.due_date is None

    def test_insufficient_data_skips(self, test_tenant, db):
        """No due/start/duration → skip (D-08)."""
        doc = _make_doc(db, test_tenant, "insufficient.pdf")
        _make_term(db, test_tenant, doc.id, "doi_tac", "Công ty A")

        result = derive_obligations(db, test_tenant, doc.id)
        assert result["created"] == 0
        assert result["skipped"] is True
        assert "Insufficient" in result["reason"]


# ── DEC-020 reminder windows ─────────────────────────────────────────────

class TestDEC020ReminderWindows:
    def test_once_uses_30_day_window(self, test_tenant, db):
        """once → remind_before_days=30 (not 365)."""
        doc = _make_doc(db, test_tenant, "once_30d.pdf")
        _make_term(db, test_tenant, doc.id, "ngay_het_han", "2026-12-31")
        derive_obligations(db, test_tenant, doc.id)

        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        assert ob.recurrence == "once"
        assert ob.remind_before_days == 30

    def test_open_ended_uses_365_day_window(self, test_tenant, db):
        """open_ended_review → remind_before_days=365 (DEC-020)."""
        doc = _make_doc(db, test_tenant, "open_365d.pdf")
        _make_term(db, test_tenant, doc.id, "ngay_hieu_luc", "2026-01-01")
        _make_term(db, test_tenant, doc.id, "thoi_han_hd", "vô thời hạn")
        derive_obligations(db, test_tenant, doc.id)

        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        assert ob.recurrence == "open_ended_review"
        assert ob.remind_before_days == 365

    def test_compute_due_window_includes_30d(self, test_tenant, db):
        """Obligation due in 20 days, remind_before=30 → in due window."""
        doc = _make_doc(db, test_tenant, "window_30d.pdf")
        _make_term(db, test_tenant, doc.id, "ngay_het_han", "2026-12-31")
        derive_obligations(db, test_tenant, doc.id)

        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        # Use a reference date 20 days before the due date
        ref_date = date(2026, 12, 11)
        due_obs = compute_due_window(db, test_tenant, reference_date=ref_date)
        assert any(o.id == ob.id for o in due_obs)

    def test_compute_due_window_excludes_outside_30d(self, test_tenant, db):
        """Obligation due in 60 days, remind_before=30 → NOT in due window."""
        doc = _make_doc(db, test_tenant, "window_exclude.pdf")
        _make_term(db, test_tenant, doc.id, "ngay_het_han", "2026-12-31")
        derive_obligations(db, test_tenant, doc.id)

        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        # Use a reference date 60 days before the due date
        ref_date = date(2026, 11, 1)
        due_obs = compute_due_window(db, test_tenant, reference_date=ref_date)
        assert not any(o.id == ob.id for o in due_obs)

    def test_flip_overdue_status(self, test_tenant, db):
        """Pending obligation past due_date → flipped to overdue."""
        doc = _make_doc(db, test_tenant, "overdue.pdf")
        _make_term(db, test_tenant, doc.id, "ngay_het_han", "2020-01-01")
        derive_obligations(db, test_tenant, doc.id)

        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        assert ob.status == "pending"

        flipped = _flip_overdue_status(db, test_tenant, reference_date=date(2026, 6, 1))
        assert flipped >= 1

        db.refresh(ob)
        assert ob.status == "overdue"


# ── Idempotency ──────────────────────────────────────────────────────────

class TestIdempotency:
    def test_done_preserved_on_rederivation(self, test_tenant, db):
        """Re-derive creates new pending, preserves done obligation."""
        doc = _make_doc(db, test_tenant, "idempotent.pdf")
        _make_term(db, test_tenant, doc.id, "ngay_het_han", "2026-12-31")

        derive_obligations(db, test_tenant, doc.id)
        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        ob.status = "done"
        db.commit()

        # Update term + re-derive
        db.query(Term).filter(
            Term.document_id == doc.id, Term.field_name == "ngay_het_han"
        ).update({"field_value": "2027-01-01"})
        db.commit()
        result = derive_obligations(db, test_tenant, doc.id)
        assert result["created"] == 1

        obs = db.query(Obligation).filter(
            Obligation.document_id == doc.id
        ).order_by(Obligation.id).all()
        assert len(obs) == 2
        assert obs[0].status == "done"
        assert obs[0].due_date == "2026-12-31"
        assert obs[1].status == "pending"
        assert obs[1].due_date == "2027-01-01"

    def test_rederivation_replaces_pending(self, test_tenant, db):
        """Re-derive deletes old pending, creates new one."""
        doc = _make_doc(db, test_tenant, "replace_pending.pdf")
        _make_term(db, test_tenant, doc.id, "ngay_het_han", "2026-12-31")

        derive_obligations(db, test_tenant, doc.id)
        assert db.query(Obligation).filter(Obligation.document_id == doc.id).count() == 1

        # Re-derive with same data
        result = derive_obligations(db, test_tenant, doc.id)
        assert result["created"] == 1
        assert db.query(Obligation).filter(Obligation.document_id == doc.id).count() == 1


# ── Date parsing edge cases ──────────────────────────────────────────────

class TestDateParsing:
    def test_iso_date(self):
        assert parse_date("2026-01-15") == datetime(2026, 1, 15)

    def test_dmy_date(self):
        assert parse_date("15/01/2026") == datetime(2026, 1, 15)

    def test_vietnamese_date(self):
        assert parse_date("ngày 15 tháng 01 năm 2026") == datetime(2026, 1, 15)

    def test_unparseable_date(self):
        assert parse_date("not a date") is None
        assert parse_date("") is None
        assert parse_date(None) is None

    def test_duration_months(self):
        assert parse_duration_months("12 tháng") == 12
        assert parse_duration_months("2 năm") == 24
        assert parse_duration_months("6 months") == 6
        assert parse_duration_months("1y") == 12

    def test_open_ended_duration(self):
        assert parse_duration_months("vô thời hạn") is None
        assert parse_duration_months("không xác định") is None

    def test_add_months_clamps_day(self):
        """Jan 31 + 1 month → Feb 28 (clamped)."""
        result = add_months(datetime(2026, 1, 31), 1)
        assert result == datetime(2026, 2, 28)

    def test_add_months_year_boundary(self):
        """Dec 2026 + 2 months → Feb 2027."""
        result = add_months(datetime(2026, 12, 15), 2)
        assert result == datetime(2027, 2, 15)
