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


def finish_reason(response: object) -> str | None:
    """Best-effort `finish_reason` off a google-genai response's first candidate.

    Used to detect MAX_TOKENS truncation (#442/#445) alongside candidates_token_count.
    """
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return None
    reason = getattr(candidates[0], "finish_reason", None)
    return str(reason) if reason is not None else None


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
    ocr_text: str | None = None,
) -> ExtractionResult:
    """Map the model's structured output → the canonical ExtractionResult."""
    return ExtractionResult(
        doc_type=parsed.doc_type,
        doc_type_confidence=parsed.doc_type_confidence,
        fields=parsed.as_field_map(),
        ocr_text=ocr_text,  # #450: raw OCR text (hybrid_ocr only) for ocr-text download (#444)
        # DEC-026/030: Gemini uses ContractExtractionLLMFull (clauses + obligation_schedule
        # + parties); Claude uses the flat base (none — grammar compiler timeout on nested
        # lists). getattr defaults to [] so both schema tiers produce a valid result.
        clauses=list(getattr(parsed, "clauses", [])),
        obligation_schedule=list(getattr(parsed, "obligation_schedule", [])),  # DEC-030 Phase 2 (#154)
        parties=list(getattr(parsed, "parties", [])),  # DEC-030 (Gemini Full only)
        defined_terms=list(getattr(parsed, "defined_terms", [])),  # R9 #372
        cross_references=list(getattr(parsed, "cross_references", [])),  # R10 #373
        has_signature=getattr(parsed, "has_signature", False),  # R5 #368
        signature_pages=list(getattr(parsed, "signature_pages", [])),  # R5 #368
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
