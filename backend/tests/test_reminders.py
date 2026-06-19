"""Reminder service + scheduler + endpoint tests (#62 scaffold)."""
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
from app.services.reminders import compute_due_window, send_reminders_for_tenant
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
    record_consent(tenant_db, "reminder-tenant", "reminder_send", actor="remuser", entity_id=1)
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
        obligation_type="once" if due_date else "open_ended_review",
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

    def test_send_failure_no_retry(self):
        from app.services.telegram import send_obligation_reminder

        mock_bot = type("Bot", (), {"send_message": AsyncMock(side_effect=Exception("boom"))})()
        with patch("app.services.telegram._lazy_bot._bot", mock_bot):
            result = asyncio.run(send_obligation_reminder("reminder-tenant", 1, "desc", "2026-12-31", "12345"))
        assert result is False


# ── Reminder engine ──

class TestReminderEngine:
    def test_compute_due_window(self, db):
        today = date.today()
        ob_in = _make_obligation(db, (today + timedelta(days=5)).isoformat(), remind_before_days=30)
        ob_out = _make_obligation(db, (today + timedelta(days=60)).isoformat(), remind_before_days=30)
        ob_overdue = _make_obligation(db, (today - timedelta(days=1)).isoformat(), remind_before_days=30)

        due = compute_due_window(db, "reminder-tenant", reference_date=today)
        due_ids = {o.id for o in due}
        assert ob_in.id in due_ids
        assert ob_out.id not in due_ids
        assert ob_overdue.id not in due_ids

        db.refresh(ob_overdue)
        assert ob_overdue.status == "overdue"

    def test_idempotency_no_double_send(self, db):
        from app.models.tenant import Event

        today = date.today()
        ob = _make_obligation(db, (today + timedelta(days=5)).isoformat(), remind_before_days=30)

        with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True):
            asyncio.run(send_reminders_for_tenant(db, "reminder-tenant", "12345", reference_date=today))

        # Second run should be idempotent (skip because reminder_sent event exists).
        with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock, return_value=True) as mock_send:
            asyncio.run(send_reminders_for_tenant(db, "reminder-tenant", "12345", reference_date=today))

        assert mock_send.call_count == 0
        events = db.query(Event).filter(Event.entity_id == ob.id, Event.event_type == "reminder_sent").all()
        assert len(events) == 1

    def test_consent_gate(self, db):
        from app.services.consent import revoke_consent

        today = date.today()
        _make_obligation(db, (today + timedelta(days=5)).isoformat(), remind_before_days=30)

        tenant_db = get_tenant_session("reminder-tenant")
        revoke_consent(tenant_db, "reminder-tenant", "reminder_send", actor="remuser")
        tenant_db.close()

        with patch("app.services.reminders.send_obligation_reminder", new_callable=AsyncMock) as mock_send:
            result = asyncio.run(send_reminders_for_tenant(db, "reminder-tenant", "12345", reference_date=today))

        assert result["consent"] is False
        assert mock_send.call_count == 0


# ── Endpoint ──

class TestReminderEndpoint:
    def test_reminders_test_dev_only(self, auth_client):
        with patch("app.routers.reminders.send_reminders_for_tenant", new_callable=AsyncMock, return_value={"attempted": 1, "sent": 1, "skipped": 0, "consent": True}):
            r = auth_client.post("/reminders/test")
            assert r.status_code == 200
            data = r.json()
            assert data["ok"] is True
            assert data["sent"] == 1

