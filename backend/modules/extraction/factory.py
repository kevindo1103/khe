"""Provider factory + typed availability error (issue #53 — unblocks #25 PR-B).

KHE_Backend consumes extraction read-only: it calls `get_extraction_provider()`
once, then `await provider.extract(image_bytes, "auto")`. Everything policy-shaped
— which provider, key handling, the Gemini→Claude fallback (DEC-002) — lives HERE
so Backend stays policy-free and never reaches into provider internals (KHE_AI scope).

Design notes:
- **Lazy / no import-time failure.** Provider classes import their SDKs only in
  `__init__`, and keys are read from the environment at call time, so importing
  this module (and `import main`) stays green without keys or SDKs installed.
- **Typed error.** When no provider is configured we raise `ExtractionUnavailable`
  (a RuntimeError subclass) — Backend maps it to a clean 503 / status=failed, not
  to a per-document error.
- **Fallback charges once.** The composite advances to the next provider only on a
  *hard failure* (`ExtractionResult.is_error`), never on mere `needs_review` — a
  successful-but-uncertain extraction (D-08) is returned as-is.
"""

from __future__ import annotations

import os

from .provider import VisionExtractionProvider
from .providers import (
    ClaudeHaikuProvider,
    ClaudeSonnetProvider,
    GeminiFlashProvider,
    HybridOCRProvider,
)
from .schemas import ExtractionResult


class ExtractionUnavailable(RuntimeError):
    """No vision-extraction provider is configured (no API key / SDK present).

    This is an *infrastructure* condition, not a document problem — Backend should
    surface it as 503 / status=failed rather than as a failed extraction result.
    """


# name → (provider class, env vars that enable it). The env-var tuples mirror each
# provider's own lookup order (CLAUDE_API_KEY canonical, ANTHROPIC_API_KEY fallback).
_REGISTRY: dict[str, tuple[type, tuple[str, ...]]] = {
    "gemini_flash": (GeminiFlashProvider, ("GEMINI_API_KEY", "GOOGLE_API_KEY")),
    "claude_haiku": (ClaudeHaikuProvider, ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY")),
    "claude_sonnet": (ClaudeSonnetProvider, ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY")),
    # DEC-049: hybrid OCR pipeline — Document AI + Gemini Flash text extraction.
    # Requires Gemini key + GOOGLE_APPLICATION_CREDENTIALS (service account for DocAI).
    # GOOGLE_APPLICATION_CREDENTIALS gates the registry — without it, scanned PDFs
    # hit DocAI and fail. pdftotext-only (digital PDFs) still works but not worth
    # advertising as "ready" without the full pipeline.
    "hybrid_ocr": (HybridOCRProvider, ("GOOGLE_APPLICATION_CREDENTIALS",)),
}

# DEC-002 default preference: Gemini primary, Claude Haiku fallback. `prefer` moves
# a provider to the front; the rest of this chain follows for resilience.
_DEFAULT_CHAIN: tuple[str, ...] = ("gemini_flash", "claude_haiku")


def _has_key(env_vars: tuple[str, ...]) -> bool:
    return any(os.environ.get(v) for v in env_vars)


def _resolve_chain(prefer: str) -> tuple[str, ...]:
    """`prefer` first, then the default chain — deduped, order preserved."""
    if prefer not in _REGISTRY:
        raise ValueError(
            f"Unknown provider {prefer!r}. Known: {sorted(_REGISTRY)}."
        )
    ordered = [prefer, *(n for n in _DEFAULT_CHAIN if n != prefer)]
    # Keep only registered names (registry may be narrower than the default chain).
    return tuple(n for n in dict.fromkeys(ordered) if n in _REGISTRY)


def get_extraction_provider(prefer: str = "gemini_flash") -> VisionExtractionProvider:
    """Return a ready `VisionExtractionProvider`. Gemini primary; falls back to
    Claude Haiku (DEC-002). Reads keys from the environment.

    Args:
        prefer: provider name to try first ("gemini_flash" | "claude_haiku" |
            "claude_sonnet"). Others remain in the chain for resilience.

    Returns:
        A single provider if only one is configured, else a fallback composite
        that tries each in order and advances on a hard failure (`is_error`).

    Raises:
        ExtractionUnavailable: no candidate has a key present / SDK installed.
        ValueError: `prefer` is not a known provider name.
    """
    skipped: list[str] = []
    ready: list[VisionExtractionProvider] = []
    for nm in _resolve_chain(prefer):
        cls, env_vars = _REGISTRY[nm]
        if not _has_key(env_vars):
            skipped.append(f"{nm} (set {' or '.join(env_vars)})")
            continue
        try:
            ready.append(cls())
        except RuntimeError as exc:  # SDK not installed (lazy import in __init__)
            skipped.append(f"{nm} ({exc})")

    if not ready:
        raise ExtractionUnavailable(
            "No vision-extraction provider configured. Candidates skipped: "
            + "; ".join(skipped)
        )
    if len(ready) == 1:
        return ready[0]
    return _FallbackProvider(ready)


class _FallbackProvider:
    """Composite provider: tries each backend in order, advancing only on a hard
    failure (`ExtractionResult.is_error`). A successful-but-uncertain result is
    returned as-is, so the happy path is charged exactly once. Satisfies the
    `VisionExtractionProvider` Protocol. DEC-002 fallback policy lives here."""

    def __init__(self, providers: list[VisionExtractionProvider]) -> None:
        if not providers:
            raise ValueError("_FallbackProvider needs at least one provider.")
        self._providers = providers
        self.name = "fallback:" + ">".join(p.name for p in providers)

    async def extract(self, image_bytes: bytes, doc_type: str = "auto") -> ExtractionResult:
        result: ExtractionResult | None = None
        for provider in self._providers:
            result = await provider.extract(image_bytes, doc_type)
            if not result.is_error:
                return result
        # Every provider failed — return the last honest error result (it carries
        # the warnings); never fabricate (D-08).
        assert result is not None  # _providers is non-empty by construction
        return result
