"""Scheduler benchmark instrumentation + /health/scheduler endpoint (#185)."""
import os
import sys

import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.services import scheduler


@pytest.fixture
def client():
    return TestClient(__import__("main").app)


def test_scheduler_metrics_endpoint_shape(client, monkeypatch):
    """GET /health/scheduler returns the metric keys in non-prod."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    r = client.get("/health/scheduler")
    assert r.status_code == 200
    data = r.json()
    for key in ("active_tenants", "last_reminder_tick_ms", "last_expand_tick_ms", "last_run_at"):
        assert key in data


def test_scheduler_metrics_404_in_production(client, monkeypatch):
    """Endpoint is hidden in production (tenant count is mildly sensitive)."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    r = client.get("/health/scheduler")
    assert r.status_code == 404


@pytest.mark.anyio
async def test_reminder_job_records_metrics(monkeypatch):
    """Running the daily job populates active_tenants + tick duration."""
    # Reset metrics to a known state.
    monkeypatch.setitem(scheduler._scheduler_metrics, "active_tenants", None)
    monkeypatch.setitem(scheduler._scheduler_metrics, "last_reminder_tick_ms", None)

    # Stub the master query to a fixed tenant list and the per-tenant send.
    class _FakeTenant:
        def __init__(self, tid):
            self.id = tid

    class _FakeQuery:
        def all(self):
            return [_FakeTenant("bench-a"), _FakeTenant("bench-b")]

    class _FakeDB:
        def query(self, *_a, **_k):
            return _FakeQuery()

        def close(self):
            pass

    monkeypatch.setattr(scheduler, "MasterSessionLocal", lambda: _FakeDB())
    monkeypatch.setattr(scheduler, "get_tenant_session", lambda tid: _FakeDB())

    async def _noop_send(db, tid, *a, **k):
        return {"sent": 0}

    monkeypatch.setattr(scheduler, "send_reminders_for_tenant", _noop_send)

    await scheduler.run_daily_reminder_job()

    m = scheduler.get_scheduler_metrics()
    assert m["active_tenants"] == 2
    assert isinstance(m["last_reminder_tick_ms"], float)
    assert m["last_run_at"] is not None


@pytest.fixture
def anyio_backend():
    return "asyncio"
