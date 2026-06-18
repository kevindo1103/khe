"""Khế Vision Extraction module (KHE_AI scope).

Single-call vision extraction per DEC-002: one `VisionExtractionProvider.extract()`
reads document images and returns structured Terms. NO separate OCR + LLM pipeline.

Guardrails (CLAUDE.md §D-rules):
- D-01 / P-1: AI is never the system of record — it only reads.
- D-06 / FR-EX-03: extraction is READ-ONLY. Providers MUST NOT generate or modify
  legal content. They surface what is on the page, with confidence + needs_review.

Public API kept import-light: importing this package pulls in only stdlib + pydantic.
Provider SDKs (anthropic, google-genai) are imported lazily inside each provider so
CI `python -c "import ..."` and the benchmark scaffold work without keys installed.
"""

from .schemas import (
    CANONICAL_FIELDS,
    BENCHMARK_TARGET_FIELDS,
    DocType,
    ExtractedField,
    ExtractionResult,
    TokenUsage,
)
from .provider import VisionExtractionProvider

__all__ = [
    "VisionExtractionProvider",
    "ExtractionResult",
    "ExtractedField",
    "TokenUsage",
    "DocType",
    "CANONICAL_FIELDS",
    "BENCHMARK_TARGET_FIELDS",
]
