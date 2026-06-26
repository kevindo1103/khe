"""LRU eviction for the per-tenant engine cache (#184).

The cache must never exceed TENANT_ENGINE_CACHE_SIZE, and evicted engines
must be disposed (releasing their SQLite file handle). Active/recent tenants
must stay cached so the hot path keeps its pooled connection.
"""
import os
import sys

import pytest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.db import database


@pytest.fixture
def clean_cache(monkeypatch):
    """Start each test with an empty cache and a small, known cap."""
    # Dispose + clear whatever the import-time / prior tests left behind.
    for eng in list(database._engine_cache.values()):
        eng.dispose()
    database._engine_cache.clear()
    monkeypatch.setattr(settings, "TENANT_ENGINE_CACHE_SIZE", 5)
    yield
    for eng in list(database._engine_cache.values()):
        eng.dispose()
    database._engine_cache.clear()


def test_cache_never_exceeds_cap(clean_cache):
    """Spawning more tenants than the cap keeps cache size at the cap."""
    for i in range(30):
        database._get_tenant_engine(f"lru-fake-{i}")
        assert len(database._engine_cache) <= 5

    assert len(database._engine_cache) == 5
    # Only the 5 most-recently-created remain.
    assert set(database._engine_cache.keys()) == {f"lru-fake-{i}" for i in range(25, 30)}


def test_evicted_engine_is_disposed(clean_cache, monkeypatch):
    """The least-recently-used engine has dispose() called on eviction."""
    disposed: list[str] = []
    real_dispose = database.Engine.dispose

    # Fill to cap.
    for i in range(5):
        database._get_tenant_engine(f"lru-disp-{i}")

    # Wrap dispose so we can observe the eviction of lru-disp-0.
    target = database._engine_cache["lru-disp-0"]
    orig = target.dispose

    def _spy(*args, **kwargs):
        disposed.append("lru-disp-0")
        return orig(*args, **kwargs)

    monkeypatch.setattr(target, "dispose", _spy)

    # One more tenant → evicts the LRU (lru-disp-0).
    database._get_tenant_engine("lru-disp-5")

    assert "lru-disp-0" in disposed
    assert "lru-disp-0" not in database._engine_cache


def test_access_refreshes_lru_order(clean_cache):
    """Re-accessing a tenant moves it to MRU so it survives later eviction."""
    for i in range(5):
        database._get_tenant_engine(f"lru-order-{i}")

    # Touch the oldest so it becomes most-recently-used.
    database._get_tenant_engine("lru-order-0")

    # Insert a new tenant → LRU is now lru-order-1, not lru-order-0.
    database._get_tenant_engine("lru-order-5")

    assert "lru-order-0" in database._engine_cache
    assert "lru-order-1" not in database._engine_cache


def test_cache_hit_returns_same_engine(clean_cache):
    """A cached tenant returns the identical engine object (pool reuse)."""
    eng1 = database._get_tenant_engine("lru-same")
    eng2 = database._get_tenant_engine("lru-same")
    assert eng1 is eng2
    assert len(database._engine_cache) == 1
