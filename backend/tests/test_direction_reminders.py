"""Direction-aware reminder tests (#275).

Covers direction-aware windowing, quyền_lợi re-fires, Telegram templates,
party-name fallback, and snooze gating.
"""
import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.models.tenant import Document, Event, Obligation, Party
from app.services.consent import record_consent
from app.services.reminders import (
    _build_reminder_message,
    _flip_overdue_status,
    _party_name,
    compute_due_window,
    send_reminders_for_tenant,
)


@pytest.fixture
def tenant_id():
    return "dir-reminder-tenant"


def _seed_consent(db, tenant_id):
    record_consent(
        db,
        tenant_id,
        "reminder_send",
        actor="test",
        channel="telegram",
        channel_target_ref="123456",
    )


def _seed_doc(db, tenant_id, title="HĐ mẫu"):
    doc = Document(
        tenant_id=tenant_id,
        file_name="test.pdf",
        file_path=f"{tenant_id}/test.pdf",
        title=title,
        doc_type="manual",
        status="extracted",
        confirmed_by_user_at=datetime.utcnow(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _seed_party(db, tenant_id, document_id, name="Công ty ABC", is_self=False):
    party = Party(
        tenant_id=tenant_id,
        document_id=document_id,
        name=name,
        is_self=is_self,
    )
    db.add(party)
    db.commit()
    return party


def _seed_obligation(
    db,
    tenant_id,
    due_date,
    direction,
    document_id=None,
    obligor=None,
    remind_before_days=7,
    status="pending",
    snoozed_until=None,
):
    ob = Obligation(
        tenant_id=tenant_id,
        document_id=document_id,
        description="Test obligation",
        obligation_type="payment",
        direction=direction,
        due_date=due_date.isoformat() if isinstance(due_date, date) else due_date,
        remind_before_days=remind_before_days,
        status=status,
        obligor=obligor,
        snoozed_until=snoozed_until,
    )
    db.add(ob)
    db.commit()
    db.refresh(ob)
    return ob


def _log_reminder_sent_on_date(db, tenant_id, obligation_id, on_date):
    ev = Event(
        tenant_id=tenant_id,
        entity_type="obligation",
        entity_id=obligation_id,
        event_type="reminder_sent",
        actor="system",
        purpose="reminder_send",
        channel="telegram",
        channel_target_ref="123456",
        created_at=datetime.combine(on_date, datetime.min.time()),
    )
    db.add(ev)
    db.commit()


# ── compute_due_window direction branching ─────────────────────────────────


def test_compute_due_window_nghia_vu_pre_due(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 8, 1)
    ob = _seed_obligation(db, test_tenant, due, "nghĩa_vụ", document_id=doc.id)

    today = date(2026, 7, 28)
    result = compute_due_window(db, test_tenant, reference_date=today)
    assert ob in result


def test_compute_due_window_nghia_vu_not_yet_in_window(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 8, 15)
    _seed_obligation(db, test_tenant, due, "nghĩa_vụ", document_id=doc.id)

    today = date(2026, 7, 28)
    result = compute_due_window(db, test_tenant, reference_date=today)
    assert not result


def test_compute_due_window_quyen_loi_at_due(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 7, 28)
    ob = _seed_obligation(db, test_tenant, due, "quyền_lợi", document_id=doc.id)

    today = date(2026, 7, 28)
    result = compute_due_window(db, test_tenant, reference_date=today)
    assert ob in result


def test_compute_due_window_quyen_loi_not_before_due(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 8, 1)
    _seed_obligation(db, test_tenant, due, "quyền_lợi", document_id=doc.id)

    today = date(2026, 7, 28)
    result = compute_due_window(db, test_tenant, reference_date=today)
    assert not result


def test_compute_due_window_null_direction_fallback(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 8, 1)
    ob = _seed_obligation(db, test_tenant, due, None, document_id=doc.id)

    today = date(2026, 7, 28)
    result = compute_due_window(db, test_tenant, reference_date=today)
    assert ob in result


def test_compute_due_window_snooze_respected(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 8, 1)
    _seed_obligation(
        db,
        test_tenant,
        due,
        "nghĩa_vụ",
        document_id=doc.id,
        snoozed_until=datetime.utcnow() + timedelta(days=1),
    )

    today = date(2026, 7, 28)
    result = compute_due_window(db, test_tenant, reference_date=today)
    assert not result


# ── quyền_lợi re-fire sequence ──────────────────────────────────────────────


def test_compute_due_window_quyen_loi_refire_day_7(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 7, 21)
    ob = _seed_obligation(db, test_tenant, due, "quyền_lợi", document_id=doc.id)

    today = date(2026, 7, 28)
    result = compute_due_window(db, test_tenant, reference_date=today)
    assert ob in result


def test_compute_due_window_quyen_loi_refire_day_30(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 6, 28)
    ob = _seed_obligation(db, test_tenant, due, "quyền_lợi", document_id=doc.id)

    today = date(2026, 7, 28)
    result = compute_due_window(db, test_tenant, reference_date=today)
    assert ob in result


def test_compute_due_window_quyen_loi_no_refire_after_max(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 6, 28)
    ob = _seed_obligation(db, test_tenant, due, "quyền_lợi", document_id=doc.id)
    _log_reminder_sent_on_date(db, test_tenant, ob.id, due + timedelta(days=7))
    _log_reminder_sent_on_date(db, test_tenant, ob.id, due + timedelta(days=30))

    today = date(2026, 7, 28)
    result = compute_due_window(db, test_tenant, reference_date=today)
    assert not result


# ── flip_overdue_status quyền_lợi guard ─────────────────────────────────────


def test_flip_overdue_status_keeps_quyen_loi_pending_for_refires(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 7, 21)
    ob = _seed_obligation(db, test_tenant, due, "quyền_lợi", document_id=doc.id)

    today = date(2026, 7, 28)
    flipped = _flip_overdue_status(db, test_tenant, reference_date=today)
    assert flipped == 0
    db.refresh(ob)
    assert ob.status == "pending"


def test_flip_overdue_status_flips_quyen_loi_after_day_30(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 6, 20)
    ob = _seed_obligation(db, test_tenant, due, "quyền_lợi", document_id=doc.id)

    today = date(2026, 7, 21)
    flipped = _flip_overdue_status(db, test_tenant, reference_date=today)
    assert flipped == 1
    db.refresh(ob)
    assert ob.status == "overdue"


def test_flip_overdue_status_flips_nghia_vu_normally(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 7, 21)
    ob = _seed_obligation(db, test_tenant, due, "nghĩa_vụ", document_id=doc.id)

    today = date(2026, 7, 28)
    flipped = _flip_overdue_status(db, test_tenant, reference_date=today)
    assert flipped == 1
    db.refresh(ob)
    assert ob.status == "overdue"


# ── templates and party name ───────────────────────────────────────────────


def test_build_nghia_vu_template(db, test_tenant):
    doc = _seed_doc(db, test_tenant, title="HĐ thuê")
    due = date(2026, 8, 1)
    ob = _seed_obligation(db, test_tenant, due, "nghĩa_vụ", document_id=doc.id)
    text = _build_reminder_message(db, ob, None, 0, date(2026, 7, 28))
    assert "📋 Nhắc việc" in text
    assert "Hạn chót" in text
    assert "HĐ thuê" in text


def test_build_quyen_loi_initial_template_with_party(db, test_tenant):
    doc = _seed_doc(db, test_tenant, title="HĐ cung cấp")
    due = date(2026, 8, 1)
    ob = _seed_obligation(
        db, test_tenant, due, "quyền_lợi", document_id=doc.id, obligor="Cty XYZ"
    )
    text = _build_reminder_message(db, ob, "Cty XYZ", 0, date(2026, 8, 1))
    assert "💰 Đến hạn nhận" in text
    assert "Cty XYZ" in text


def test_build_quyen_loi_refire_template(db, test_tenant):
    doc = _seed_doc(db, test_tenant, title="HĐ cung cấp")
    due = date(2026, 7, 1)
    ob = _seed_obligation(
        db, test_tenant, due, "quyền_lợi", document_id=doc.id, obligor="Cty XYZ"
    )
    text = _build_reminder_message(db, ob, "Cty XYZ", 2, date(2026, 7, 31))
    assert "⚠️ Chưa xác nhận đã nhận" in text
    assert "30 ngày trước" in text
    assert "Cty XYZ" in text


def test_build_null_direction_template(db, test_tenant):
    doc = _seed_doc(db, test_tenant, title="HĐ lao động")
    due = date(2026, 8, 1)
    ob = _seed_obligation(db, test_tenant, due, None, document_id=doc.id)
    text = _build_reminder_message(db, ob, None, 0, date(2026, 7, 28))
    assert "📋 Nhắc việc" in text
    assert "⏰ Ngày" in text


def test_party_name_from_obligor(db, test_tenant):
    doc = _seed_doc(db, test_tenant)
    ob = _seed_obligation(db, test_tenant, date(2026, 8, 1), "quyền_lợi", document_id=doc.id, obligor="Cty XYZ")
    assert _party_name(db, ob) == "Cty XYZ"


def test_party_name_from_non_self_party(db, test_tenant):
    doc = _seed_doc(db, test_tenant)
    _seed_party(db, test_tenant, doc.id, name="Cty ABC", is_self=False)
    ob = _seed_obligation(db, test_tenant, date(2026, 8, 1), "quyền_lợi", document_id=doc.id)
    assert _party_name(db, ob) == "Cty ABC"


def test_party_name_omits_self_party(db, test_tenant):
    doc = _seed_doc(db, test_tenant)
    _seed_party(db, test_tenant, doc.id, name="Tên tôi", is_self=True)
    ob = _seed_obligation(db, test_tenant, date(2026, 8, 1), "quyền_lợi", document_id=doc.id)
    assert _party_name(db, ob) is None


# ── send_reminders_for_tenant integration ──────────────────────────────────


def test_send_reminders_for_tenant_nghia_vu_once(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 8, 1)
    _seed_obligation(db, test_tenant, due, "nghĩa_vụ", document_id=doc.id)

    today = date(2026, 7, 28)
    with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True) as mock_send:
        result = asyncio.run(send_reminders_for_tenant(db, test_tenant, reference_date=today))

    assert result["sent"] == 1
    assert result["skipped"] == 0
    args = mock_send.call_args
    assert "📋 Nhắc việc" in args.kwargs["message_text"]

    # Second run is idempotent.
    with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True) as mock_send:
        result = asyncio.run(send_reminders_for_tenant(db, test_tenant, reference_date=today))
    assert result["skipped"] == 1
    assert mock_send.call_count == 0


def test_send_reminders_for_tenant_quyen_loi_initial_and_refire(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 7, 21)
    ob = _seed_obligation(db, test_tenant, due, "quyền_lợi", document_id=doc.id, obligor="Cty XYZ")

    # Day 7 re-fire.
    today = date(2026, 7, 28)
    with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True) as mock_send:
        result = asyncio.run(send_reminders_for_tenant(db, test_tenant, reference_date=today))
    assert result["sent"] == 1
    args = mock_send.call_args
    assert "⚠️ Chưa xác nhận đã nhận" in args.kwargs["message_text"]
    assert "Cty XYZ" in args.kwargs["message_text"]

    # Day 30 re-fire → second and final, status becomes overdue.
    today = date(2026, 8, 20)
    with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True) as mock_send:
        result = asyncio.run(send_reminders_for_tenant(db, test_tenant, reference_date=today))
    assert result["sent"] == 1
    args = mock_send.call_args
    assert args.kwargs["message_text"].count("⚠️") == 1
    db.refresh(ob)
    assert ob.status == "overdue"


def test_send_reminders_for_tenant_quyen_loi_same_day_idempotent(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 7, 28)
    _seed_obligation(db, test_tenant, due, "quyền_lợi", document_id=doc.id)

    today = date(2026, 7, 28)
    with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True) as mock_send:
        asyncio.run(send_reminders_for_tenant(db, test_tenant, reference_date=today))
        result = asyncio.run(send_reminders_for_tenant(db, test_tenant, reference_date=today))
    assert result["skipped"] == 1
    assert mock_send.call_count == 1


def test_send_reminders_for_tenant_quyen_loi_snooze_refire(db, test_tenant):
    _seed_consent(db, test_tenant)
    doc = _seed_doc(db, test_tenant)
    due = date(2026, 7, 21)
    _seed_obligation(
        db,
        test_tenant,
        due,
        "quyền_lợi",
        document_id=doc.id,
        snoozed_until=datetime.utcnow() + timedelta(days=1),
    )

    today = date(2026, 7, 28)
    with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True) as mock_send:
        result = asyncio.run(send_reminders_for_tenant(db, test_tenant, reference_date=today))
    assert result["sent"] == 0
    assert mock_send.call_count == 0
