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

import logging
import os

logger = logging.getLogger(__name__)

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
    # DEC-049: hybrid OCR pipeline — 2 paths:
    #   Digital PDFs → pdftotext (free, local) → Gemini text extraction
    #   Scanned PDFs → Document AI OCR → Gemini text extraction
    # Gated on Gemini key only — pdftotext path works without DocAI credentials.
    # Scanned path gracefully fails if GOOGLE_APPLICATION_CREDENTIALS is missing
    # (provider returns empty_result, fallback chain picks up).
    "hybrid_ocr": (HybridOCRProvider, ("GEMINI_API_KEY", "GOOGLE_API_KEY")),
}

# DEC-002 default preference: Gemini primary, Claude Haiku fallback. `prefer` moves
# a provider to the front; the rest of this chain follows for resilience.
_DEFAULT_CHAIN: tuple[str, ...] = ("gemini_flash", "claude_haiku")

# PDF-specific chain (#436, QC #435): claude_haiku uses the lean
# ContractExtractionLLM schema (7 flat fields, no clauses/parties/obligations) —
# a "successful" Haiku extraction on a PDF is silently useless. Excluded here so a
# Gemini outage keeps the doc retryable instead of masquerading as done with 0
# clauses. Haiku stays available for image-only inputs (still extracts base fields).
_PDF_CHAIN: tuple[str, ...] = ("hybrid_ocr", "gemini_flash")


def _has_key(env_vars: tuple[str, ...]) -> bool:
    return any(os.environ.get(v) for v in env_vars)


def _resolve_chain(prefer: str) -> tuple[str, ...]:
    """`prefer` first, then the rest of its base chain — deduped, order preserved.

    `prefer="hybrid_ocr"` (PDFs, per DEC-049) uses `_PDF_CHAIN` — no claude_haiku.
    Everything else (image inputs) uses `_DEFAULT_CHAIN`, which keeps haiku as a
    fallback since it still extracts the 7 base fields from a single image.
    """
    if prefer not in _REGISTRY:
        raise ValueError(
            f"Unknown provider {prefer!r}. Known: {sorted(_REGISTRY)}."
        )
    base = _PDF_CHAIN if prefer == "hybrid_ocr" else _DEFAULT_CHAIN
    ordered = [prefer, *(n for n in base if n != prefer)]
    # Keep only registered names (registry may be narrower than the base chain).
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
        prior_warnings: list[str] = []
        for provider in self._providers:
            result = await provider.extract(image_bytes, doc_type)
            if not result.is_error:
                if prior_warnings:
                    result.warnings = [*prior_warnings, *result.warnings]
                return result
            logger.warning(
                "Provider %s failed, advancing fallback: %s",
                provider.name,
                "; ".join(result.warnings),
            )
            prior_warnings.extend(
                f"[{provider.name}] {w}" for w in result.warnings
            )
        assert result is not None
        result.warnings = [*prior_warnings, *result.warnings]
        return result
