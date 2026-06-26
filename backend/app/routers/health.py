import os

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.schemas.health import HealthOut

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthOut)
def health_check():
    return {"status": "healthy"}


@router.get("/scheduler")
def scheduler_metrics():
    """One-time benchmark endpoint (#185): report the latest scheduler tick
    timing + active tenant count, to measure distance to the #181 scaling
    thresholds. Operational counts only (no PII/secrets), but gated to non-prod
    to avoid exposing tenant counts publicly. Returns 404 in production.
    """
    if settings.ENVIRONMENT not in {"development", "staging", "test", "local"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    from app.services.scheduler import get_scheduler_metrics

    metrics = get_scheduler_metrics()
    metrics["note"] = (
        "Nulls mean the job has not run since process start. "
        "Trigger a manual tick via POST /reminders/test or wait for the daily cron."
    )
    return metrics


@router.get("/extraction")
def extraction_config_diagnostic():
    """Non-prod diagnostic: report which extraction provider env vars the
    backend process actually sees. Never returns the key VALUES — only whether
    each env-var name is present and non-empty. Safe to expose because the
    factory's `ExtractionUnavailable` message already names these.

    Returns 404 in production.

    Wired for #79: lets QC self-diagnose `status=failed` without VPS access.
    """
    # Allowlist (not denylist) — fails closed on unknown / mistyped ENVIRONMENT
    # values (e.g. "prod", "Production"). Per QC review on #80. Info leak here
    # is bounded to env-var NAMES that already live in the repo, but
    # defense-in-depth wins over a one-character config typo.
    if settings.ENVIRONMENT not in {"development", "staging", "test", "local"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    # Mirror the factory _REGISTRY env-var tuples without importing it
    # (defensive — factory is KHE_AI scope; we only need the names).
    candidates = {
        "gemini_flash": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "claude_haiku": ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY"),
        "claude_sonnet": ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY"),
    }

    providers = []
    for name, env_vars in candidates.items():
        present = {v: bool(os.environ.get(v)) for v in env_vars}
        providers.append({
            "name": name,
            "env_vars": list(env_vars),
            "configured": any(present.values()),
            "present_per_var": present,
        })

    any_configured = any(p["configured"] for p in providers)
    return {
        "environment": settings.ENVIRONMENT,
        "any_provider_configured": any_configured,
        "providers": providers,
        "hint": (
            "OK — at least one provider has a key in the worker process env."
            if any_configured
            else "NO PROVIDER CONFIGURED. The .env file may exist on disk but "
            "systemd's EnvironmentFile= must point to it for the worker thread "
            "to see these vars. Check `systemctl show <service> | grep -i environment`."
        ),
    }
