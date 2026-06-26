"""Tests for GET /health/extraction — provider-key diagnostic (#79 follow-up)."""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from main import app


def test_diagnostic_no_keys(monkeypatch):
    """With no provider env vars set: shape is correct and warns explicitly."""
    for v in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(v, raising=False)

    c = TestClient(app)
    r = c.get("/health/extraction")
    assert r.status_code == 200
    data = r.json()
    assert data["any_provider_configured"] is False
    names = {p["name"] for p in data["providers"]}
    assert names == {"gemini_flash", "claude_haiku", "claude_sonnet"}
    for p in data["providers"]:
        assert p["configured"] is False
    assert "NO PROVIDER CONFIGURED" in data["hint"]
    assert "EnvironmentFile" in data["hint"]


def test_diagnostic_with_gemini(monkeypatch):
    """With only GEMINI_API_KEY set: gemini configured, claude not. No key VALUE leaked."""
    for v in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "ultra-secret-do-not-leak")

    c = TestClient(app)
    r = c.get("/health/extraction")
    data = r.json()
    assert data["any_provider_configured"] is True
    gem = next(p for p in data["providers"] if p["name"] == "gemini_flash")
    assert gem["configured"] is True
    assert gem["present_per_var"]["GEMINI_API_KEY"] is True
    claude = next(p for p in data["providers"] if p["name"] == "claude_haiku")
    assert claude["configured"] is False
    assert "ultra-secret-do-not-leak" not in r.text  # critical: never echo the key value


def test_diagnostic_404_in_production(monkeypatch):
    """In production env: endpoint is hidden (404)."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    c = TestClient(app)
    r = c.get("/health/extraction")
    assert r.status_code == 404


@pytest.mark.parametrize("env_value", ["prod", "Production", "PRODUCTION", "stg", "", "live"])
def test_diagnostic_404_on_unknown_environment(monkeypatch, env_value):
    """Allowlist guard (QC #80 review item 1): only known non-prod values open
    the endpoint. A typo (`prod`, `Production`) or unknown value must 404."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "ENVIRONMENT", env_value)
    c = TestClient(app)
    r = c.get("/health/extraction")
    assert r.status_code == 404, f"ENVIRONMENT={env_value!r} unexpectedly opened the endpoint"


def test_diagnostic_hint_mentions_environmentfile(monkeypatch):
    """No-keys hint must point at the systemd EnvironmentFile gotcha (#79 root cause)."""
    for v in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    c = TestClient(app)
    r = c.get("/health/extraction")
    assert "EnvironmentFile" in r.json()["hint"]
    assert "systemctl" in r.json()["hint"]
