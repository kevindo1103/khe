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
    ALL_TYPE_SPECIFIC_FIELDS,
    BASE_CANONICAL_FIELDS,
    CANONICAL_FIELDS,
    BENCHMARK_TARGET_FIELDS,
    DOC_TYPE_GROUPS,
    TYPE_SPECIFIC_FIELDS,
    V2_UNIVERSAL_FIELDS,
    ClauseItem,
    ContractExtractionLLM,
    ContractExtractionLLMFull,
    DocType,
    ExtractedField,
    ExtractionResult,
    NamedExtractedField,
    PaymentScheduleItem,
    TokenUsage,
)
from .provider import VisionExtractionProvider
from .factory import ExtractionUnavailable, get_extraction_provider

__all__ = [
    "VisionExtractionProvider",
    "get_extraction_provider",
    "ExtractionUnavailable",
    "ExtractionResult",
    "ExtractedField",
    "NamedExtractedField",
    "ClauseItem",
    "PaymentScheduleItem",
    "ContractExtractionLLM",
    "ContractExtractionLLMFull",
    "TokenUsage",
    "DocType",
    "CANONICAL_FIELDS",
    "BASE_CANONICAL_FIELDS",
    "V2_UNIVERSAL_FIELDS",
    "BENCHMARK_TARGET_FIELDS",
    "DOC_TYPE_GROUPS",
    "TYPE_SPECIFIC_FIELDS",
    "ALL_TYPE_SPECIFIC_FIELDS",
]
