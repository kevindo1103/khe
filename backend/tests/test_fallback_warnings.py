"""Tests for _FallbackProvider warning carry-forward (doc #10 root cause fix)."""

import asyncio

import pytest

from modules.extraction.factory import _FallbackProvider
from modules.extraction.schemas import (
    ContractExtractionLLM,
    DocType,
    ExtractionResult,
    TokenUsage,
)
from modules.extraction.providers.base import empty_result, to_result


class _FakeProvider:
    def __init__(self, name: str, result: ExtractionResult):
        self.name = name
        self._result = result

    async def extract(self, image_bytes: bytes, doc_type: str = "auto") -> ExtractionResult:
        return self._result


def _make_error(name: str, warning: str) -> ExtractionResult:
    return empty_result(provider=name, model="test", latency_ms=1.0, warning=warning)


def _make_success(name: str, warnings: list[str] | None = None) -> ExtractionResult:
    parsed = ContractExtractionLLM(
        doc_type=DocType.OTHER,
        doc_type_confidence=0.5,
        fields=[],
    )
    return to_result(
        parsed,
        provider=name,
        model="test",
        latency_ms=1.0,
        usage=TokenUsage(input_tokens=100, output_tokens=50),
        cost=1.0,
        warnings=warnings,
    )


def test_warnings_carried_on_fallback_success():
    """When provider A fails and B succeeds, A's warnings appear prefixed in B's result."""
    p_fail = _FakeProvider("ocr", _make_error("ocr", "Gemini API 503"))
    p_ok = _FakeProvider("flash", _make_success("flash", ["hybrid:pdftotext"]))
    fb = _FallbackProvider([p_fail, p_ok])
    result = asyncio.run(fb.extract(b"test"))

    assert not result.is_error
    assert "[ocr] Gemini API 503" in result.warnings
    assert "hybrid:pdftotext" in result.warnings


def test_warnings_carried_on_total_failure():
    """When all providers fail, all warnings are accumulated."""
    p1 = _FakeProvider("ocr", _make_error("ocr", "DocAI failed"))
    p2 = _FakeProvider("flash", _make_error("flash", "Gemini 429"))
    p3 = _FakeProvider("haiku", _make_error("haiku", "Claude timeout"))
    fb = _FallbackProvider([p1, p2, p3])
    result = asyncio.run(fb.extract(b"test"))

    assert result.is_error
    assert "[ocr] DocAI failed" in result.warnings
    assert "[flash] Gemini 429" in result.warnings
    assert "Claude timeout" in result.warnings


def test_no_prefix_when_first_provider_succeeds():
    """When the first provider succeeds, no prefix is added."""
    p_ok = _FakeProvider("ocr", _make_success("ocr", ["hybrid:pdftotext"]))
    p_unused = _FakeProvider("flash", _make_error("flash", "should not run"))
    fb = _FallbackProvider([p_ok, p_unused])
    result = asyncio.run(fb.extract(b"test"))

    assert not result.is_error
    assert result.warnings == ["hybrid:pdftotext"]
