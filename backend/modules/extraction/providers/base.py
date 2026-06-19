"""Shared provider helpers: mime sniffing, USD→VND cost, LLM→ExtractionResult mapping."""

from __future__ import annotations

from ..schemas import (
    ContractExtractionLLM,
    DocType,
    ExtractionResult,
    TokenUsage,
)

# Approx FX for cost reporting (issue #3 targets are in đồng). Single constant so
# all providers report comparable VND. Update when FX moves materially.
USD_TO_VND: float = 25_400.0


def sniff_mime(image_bytes: bytes) -> str:
    """Best-effort media-type detection from magic bytes. Defaults to image/jpeg."""
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_bytes[:4] == b"%PDF":
        return "application/pdf"
    if image_bytes[:4] in (b"RIFF",) and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def cost_vnd(usage: TokenUsage, in_usd_per_mtok: float, out_usd_per_mtok: float) -> float:
    """Cost of one extraction in VND from token usage and per-1M-token USD pricing."""
    usd = (
        usage.input_tokens / 1_000_000 * in_usd_per_mtok
        + usage.output_tokens / 1_000_000 * out_usd_per_mtok
    )
    return round(usd * USD_TO_VND, 2)


def to_result(
    parsed: ContractExtractionLLM,
    *,
    provider: str,
    model: str,
    latency_ms: float,
    usage: TokenUsage,
    cost: float,
    warnings: list[str] | None = None,
) -> ExtractionResult:
    """Map the model's structured output → the canonical ExtractionResult."""
    return ExtractionResult(
        doc_type=parsed.doc_type,
        doc_type_confidence=parsed.doc_type_confidence,
        fields=parsed.as_field_map(),
        # DEC-026: Gemini uses ContractExtractionLLMFull (has clauses); Claude uses
        # the flat base ContractExtractionLLM (no clauses — grammar compiler timeout).
        # getattr defaults to [] so both paths produce a valid ExtractionResult.
        clauses=list(getattr(parsed, "clauses", [])),
        provider=provider,
        model=model,
        latency_ms=round(latency_ms, 2),
        usage=usage,
        cost_vnd=cost,
        warnings=warnings or [],
    )


def empty_result(*, provider: str, model: str, latency_ms: float, warning: str) -> ExtractionResult:
    """Fallback result when a provider cannot produce structured output (no guessing)."""
    from ..schemas import CANONICAL_FIELDS, ExtractedField

    return ExtractionResult(
        doc_type=DocType.OTHER,
        doc_type_confidence=0.0,
        fields={k: ExtractedField() for k in CANONICAL_FIELDS},
        provider=provider,
        model=model,
        latency_ms=round(latency_ms, 2),
        usage=TokenUsage(),
        cost_vnd=0.0,
        warnings=[warning],
    )
