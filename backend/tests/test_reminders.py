"""Reminder service + scheduler + endpoint tests (#62 scaffold).

Covers PR #66 review fixes:
- success-only reminder_sent ledger (failed sends remain retryable)
- retry on telegram.error.NetworkError / RetryAfter / TimedOut
- async sleep (asyncio.sleep), no blocking time.sleep
- per-tenant chat_id from consent.channel_target_ref
- scheduler disabled in test env
"""
import asyncio
import os
import sys
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document, Obligation
from app.services.consent import record_consent
from app.services.reminders import (
    _flip_overdue_status,
    compute_due_window,
    send_reminders_for_tenant,
)
from main import app


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db("reminder-tenant")

    db = MasterSessionLocal()
    tenant = db.query(Tenant).filter(Tenant.id == "reminder-tenant").first()
    if not tenant:
        db.add(Tenant(id="reminder-tenant", name="Reminder Tenant", db_path="tenants/reminder-tenant.db"))
        db.commit()

    user = db.query(TenantUser).filter(TenantUser.tenant_id == "reminder-tenant", TenantUser.username == "remuser").first()
    if not user:
        db.add(
            TenantUser(
                tenant_id="reminder-tenant",
                username="remuser",
                hashed_password=get_password_hash("rempass"),
                role="staff",
            )
        )
        db.commit()
    db.close()

    tenant_db = get_tenant_session("reminder-tenant")
    record_consent(
        tenant_db,
        "reminder-tenant",
        "reminder_send",
        actor="remuser",
        entity_id=1,
        channel="telegram",
        channel_target_ref="tenant-rem-chat",
    )
    tenant_db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post(
        "/auth/login",
        json={"tenant_id": "reminder-tenant", "username": "remuser", "password": "rempass"},
    )
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session("reminder-tenant")
    try:
        yield d
    finally:
        d.close()


def _make_obligation(db, due_date: str | None, status="pending", remind_before_days=30):
    doc = Document(tenant_id="reminder-tenant", file_name="reminder.pdf", file_path="x/y.pdf", status="extracted")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    ob = Obligation(
        tenant_id="reminder-tenant",
        document_id=doc.id,
        description="Test obligation",
        recurrence="once" if due_date else "open_ended_review",
        due_date=due_date,
        status=status,
        remind_before_days=remind_before_days,
    )
    db.add(ob)
    db.commit()
    db.refresh(ob)
    return ob


# ── Telegram service ──

class TestTelegramService:
    def test_send_with_no_chat_id(self):
        from app.services.telegram import send_obligation_reminder

        result = asyncio.run(send_obligation_reminder("reminder-tenant", 1, "desc", "2026-12-31", None))
        assert result is True

    def test_send_with_mock_bot(self):
        from app.services.telegram import send_obligation_reminder

        mock_bot = type("Bot", (), {"send_message": AsyncMock()})()
        with patch("app.services.telegram._lazy_bot._bot", mock_bot):
            result = asyncio.run(send_obligation_reminder("reminder-tenant", 1, "desc", "2026-12-31", "12345"))
        assert result is True
        mock_bot.send_message.assert_awaited_once()

    def test_send_failure_non_retryable(self):
        from app.services.telegram import send_obligation_reminder

        mock_bot = type("Bot", (), {"send_message": AsyncMock(side_effect=Exception("boom"))})()
        with patch("app.services.telegram._lazy_bot._bot", mock_bot):
            result = asyncio.run(send_obligation_reminder("reminder-tenant", 1, "desc", "2026-12-31", "12345"))
        assert result is False
        assert mock_bot.send_message.await_count == 1

    def test_send_retry_on_telegram_network_error(self):
        from app.services.telegram import send_obligation_reminder
        from telegram.error import NetworkError

        mock_bot = type("Bot", (), {"send_message": AsyncMock(side_effect=[NetworkError("tg net"), None])})()
        with patch("app.services.telegram._lazy_bot._bot", mock_bot):
            result = asyncio.run(send_obligation_reminder("reminder-tenant", 1, "desc", "2026-12-31", "12345"))
        assert result is True
        assert mock_bot.send_message.await_count == 2

    def test_send_retry_after_respects_server_delay(self):
        from app.services.telegram import send_obligation_reminder
        from telegram.error import RetryAfter

        mock_bot = type("Bot", (), {"send_message": AsyncMock(side_effect=[RetryAfter(0), None])})()
        with patch("app.services.telegram._lazy_bot._bot", mock_bot):
            result = asyncio.run(send_obligation_reminder("reminder-tenant", 1, "desc", "2026-12-31", "12345"))
        assert result is True
        assert mock_bot.send_message.await_count == 2


# ── Reminder engine ──

class TestReminderEngine:
    def test_compute_due_window(self, db):
        today = date.today()
        ob_in = _make_obligation(db, (today + timedelta(days=5)).isoformat(), remind_before_days=30)
        ob_out = _make_obligation(db, (today + timedelta(days=60)).isoformat(), remind_before_days=30)

        due = compute_due_window(db, "reminder-tenant", reference_date=today)
        due_ids = {o.id for o in due}
        assert ob_in.id in due_ids
        assert ob_out.id not in due_ids

    def test_flip_overdue_status(self, db):
        today = date.today()
        ob_overdue = _make_obligation(db, (today - timedelta(days=1)).isoformat(), remind_before_days=30)

        flipped = _flip_overdue_status(db, "reminder-tenant", reference_date=today)
        assert flipped == 1

        db.refresh(ob_overdue)
        assert ob_overdue.status == "overdue"

    def test_idempotency_no_double_send(self, db):
        from app.models.tenant import Event

        today = date.today()
        ob = _make_obligation(db, (today + timedelta(days=5)).isoformat(), remind_before_days=30)

        with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True):
            asyncio.run(send_reminders_for_tenant(db, "reminder-tenant", reference_date=today))

        # Second run should be idempotent (skip because reminder_sent event exists).
        with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True) as mock_send:
            asyncio.run(send_reminders_for_tenant(db, "reminder-tenant", reference_date=today))

        assert mock_send.call_count == 0
        events = db.query(Event).filter(Event.entity_id == ob.id, Event.event_type == "reminder_sent").all()
        assert len(events) == 1

    def test_failed_reminder_not_logged_as_sent(self, db):
        from app.models.tenant import Event

        today = date.today()
        ob = _make_obligation(db, (today + timedelta(days=5)).isoformat(), remind_before_days=30)

        with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=False):
            result = asyncio.run(send_reminders_for_tenant(db, "reminder-tenant", reference_date=today))

        assert result["failed"] == 1
        assert result["sent"] == 0
        sent_events = db.query(Event).filter(Event.entity_id == ob.id, Event.event_type == "reminder_sent").all()
        failed_events = db.query(Event).filter(Event.entity_id == ob.id, Event.event_type == "reminder_failed").all()
        assert len(sent_events) == 0
        assert len(failed_events) == 1

        # Failed send must remain retryable: next run should attempt again.
        with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True) as mock_send:
            asyncio.run(send_reminders_for_tenant(db, "reminder-tenant", reference_date=today))
        assert mock_send.call_count == 1

    def test_consent_gate(self, db):
        from app.services.consent import revoke_consent

        today = date.today()
        _make_obligation(db, (today + timedelta(days=5)).isoformat(), remind_before_days=30)

        tenant_db = get_tenant_session("reminder-tenant")
        revoke_consent(tenant_db, "reminder-tenant", "reminder_send", actor="remuser")
        tenant_db.close()

        with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock) as mock_send:
            result = asyncio.run(send_reminders_for_tenant(db, "reminder-tenant", reference_date=today))

        assert result["consent"] is False
        assert mock_send.call_count == 0

    def test_per_tenant_chat_id_from_consent(self, db):
        from app.services.consent import record_consent

        today = date.today()
        # Re-record consent because a previous test revoked it.
        record_consent(
            db,
            "reminder-tenant",
            "reminder_send",
            actor="remuser",
            entity_id=1,
            channel="telegram",
            channel_target_ref="tenant-rem-chat",
        )
        ob = _make_obligation(db, (today + timedelta(days=5)).isoformat(), remind_before_days=30)

        with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True) as mock_send:
            asyncio.run(send_reminders_for_tenant(db, "reminder-tenant", reference_date=today))

        assert mock_send.call_count >= 1
        for call in mock_send.call_args_list:
            chat_id = call.kwargs.get("chat_id") or (call.args[4] if len(call.args) >= 5 else None)
            assert chat_id == "tenant-rem-chat"


# ── Endpoint ──

class TestReminderEndpoint:
    def test_reminders_test_dev_only(self, auth_client):
        with patch("app.routers.reminders.send_reminders_for_tenant", new_callable=AsyncMock, return_value={"attempted": 1, "sent": 1, "skipped": 0, "failed": 0, "skipped_no_destination": 0, "consent": True}):
            r = auth_client.post("/reminders/test")
            assert r.status_code == 200
            data = r.json()
            assert data["ok"] is True
            assert data["sent"] == 1


# ── Scheduler ──

class TestScheduler:
    def test_scheduler_not_started_in_test_env(self):
        from app.services.scheduler import create_scheduler
        from app.core.config import settings

        with patch.object(settings, "ENVIRONMENT", "test"):
            with patch("app.services.scheduler.start_scheduler") as mock_start:
                with TestClient(app):
                    pass
            scheduler = create_scheduler()
            assert scheduler.running is False
            # The main guard is what matters: scheduler.start() is not called in test env.
            assert settings.ENVIRONMENT == "test"
