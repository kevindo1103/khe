"""Pure unit tests for the extraction module — no API keys / SDKs required.

Run: `python -m backend.modules.extraction.tests.test_extraction` or `pytest`.
Covers schemas, metric normalization/matching, scoring, and report rendering.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from ..schemas import (
    BENCHMARK_TARGET_FIELDS,
    CANONICAL_FIELDS,
    DocType,
    ExtractedField,
    ExtractionResult,
    TokenUsage,
)
from .. import factory
from ..factory import ExtractionUnavailable, get_extraction_provider
from ..benchmark import metrics
from ..benchmark.runner import render_report
from ..benchmark.metrics import field_match, normalize, score


def test_package_imports_without_sdks() -> None:
    # provider Protocol + schemas import with only pydantic present.
    from ..provider import VisionExtractionProvider  # noqa: F401
    from ..prompts import SYSTEM_GUARDRAIL, build_instruction

    assert "KHÔNG" in SYSTEM_GUARDRAIL  # read-only guardrail present (D-06)
    assert "JSON" in build_instruction("hd_thue_mat_bang")
    assert set(BENCHMARK_TARGET_FIELDS).issubset(set(CANONICAL_FIELDS))


def test_extracted_field_defaults_safe() -> None:
    f = ExtractedField()
    assert f.value is None and f.needs_review is True and f.confidence == 0.0


def test_date_normalization_format_agnostic() -> None:
    # 05/01/2026 == 2026-01-05 == 5-1-2026 after digit-signature normalization.
    a = normalize("ngay_het_han", "05/01/2026")
    b = normalize("ngay_het_han", "2026-01-05")
    c = normalize("ngay_het_han", "5-1-2026")
    assert a == b == c
    assert normalize("ngay_het_han", None) == ""


def test_numeric_normalization_strips_separators() -> None:
    assert normalize("gia_tri_hd", "50.000.000 đ") == normalize("gia_tri_hd", "50000000")


def test_doi_tac_subset_match() -> None:
    # Predicted must cover every ground-truth party (order-independent).
    truth = "Cong ty ABC; Ong Nguyen Van X"
    assert field_match("doi_tac", "Ông Nguyễn Văn X; Công ty ABC", truth) is True
    assert field_match("doi_tac", "Cong ty ABC", truth) is False  # missing a party


def test_text_match_accent_insensitive() -> None:
    assert field_match("thoi_han_hd", "12 tháng", "12 thang") is True


def _result(fields: dict[str, str | None], *, latency=1000.0, cost=120.0, warn=False) -> ExtractionResult:
    return ExtractionResult(
        doc_type=DocType.LEASE,
        doc_type_confidence=0.95,
        fields={k: ExtractedField(value=fields.get(k), confidence=0.95, needs_review=False)
                for k in CANONICAL_FIELDS},
        provider="gemini_flash",
        model="gemini-2.5-flash",
        latency_ms=latency,
        cost_vnd=cost,
        warnings=["boom"] if warn else [],
    )


def test_scoring_accuracy_and_aggregates() -> None:
    truth = {
        "doi_tac": "Cong ty ABC; Ong X",
        "ngay_het_han": "2026-12-31",
        "gia_tri_hd": "50000000",
        "thoi_han_hd": "12 thang",
    }
    good = _result(
        {"doi_tac": "Cong ty ABC; Ong X", "ngay_het_han": "31/12/2026",
         "gia_tri_hd": "50.000.000", "thoi_han_hd": "12 tháng"},
        latency=800.0, cost=100.0,
    )
    bad = _result(
        {"doi_tac": "Cong ty ABC", "ngay_het_han": "2026-01-01",
         "gia_tri_hd": "999", "thoi_han_hd": "6 thang"},
        latency=1200.0, cost=140.0,
    )
    ps = score("gemini_flash", "gemini-2.5-flash", [(good, truth), (bad, truth)])

    assert ps.samples == 2
    assert ps.fields["ngay_het_han"].scored == 2 and ps.fields["ngay_het_han"].correct == 1
    assert ps.fields["ngay_het_han"].accuracy == 0.5
    # good matches all 4 targets, bad matches none → mean = 0.5
    assert ps.target_accuracy == 0.5
    assert ps.latency_p50 == 1000.0
    assert ps.cost_mean == 120.0
    assert ps.errors == 0


def test_unscored_when_no_ground_truth() -> None:
    # Empty ground-truth value (e.g. open-ended labor contract expiry) is not scored.
    truth = {"ngay_het_han": ""}
    r = _result({"ngay_het_han": "anything"})
    ps = score("p", "m", [(r, truth)])
    assert "ngay_het_han" not in ps.fields  # never scored → no FieldScore created


def test_percentile_single_and_multi() -> None:
    assert metrics._percentile([5.0], 95) == 5.0
    assert metrics._percentile([0.0, 100.0], 50) == 50.0


def test_render_report_smoke() -> None:
    ps = score(
        "gemini_flash", "gemini-2.5-flash",
        [(_result({"ngay_het_han": "2026-12-31"}), {"ngay_het_han": "2026-12-31"})],
    )
    md = render_report([ps], ["a note"], Path("manifest.json"))
    assert "# Benchmark results" in md and "gemini_flash" in md and "a note" in md


# --- factory (issue #53) ----------------------------------------------------


def _ok_result(provider: str = "fake") -> ExtractionResult:
    r = _result({"ngay_het_han": "2026-12-31"})
    r.provider = provider
    r.usage = TokenUsage(input_tokens=100, output_tokens=20)  # success → tokens used
    return r


def _err_result(provider: str = "fake") -> ExtractionResult:
    # Mirrors providers.base.empty_result: warning + zero tokens.
    return ExtractionResult(
        doc_type=DocType.OTHER, fields={}, provider=provider,
        usage=TokenUsage(), warnings=[f"{provider} boom"],
    )


def test_is_error_distinguishes_failure_from_needs_review() -> None:
    assert _err_result().is_error is True
    # A successful extraction that flags fields for review is NOT an error.
    ok = _ok_result()
    assert ok.is_error is False and ok.any_low_confidence is False
    # warning present but tokens consumed → not a hard failure.
    ok.warnings = ["partial page"]
    assert ok.is_error is False


def test_resolve_chain_prefers_then_defaults() -> None:
    assert factory._resolve_chain("gemini_flash") == ("gemini_flash", "claude_haiku")
    assert factory._resolve_chain("claude_haiku") == ("claude_haiku", "gemini_flash")
    # prefer outside the default chain still leads, defaults follow.
    assert factory._resolve_chain("claude_sonnet")[0] == "claude_sonnet"


def test_get_provider_unknown_prefer_raises() -> None:
    try:
        get_extraction_provider("does_not_exist")
    except ValueError as exc:
        assert "Unknown provider" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_get_provider_unavailable_when_no_keys() -> None:
    saved = {k: os.environ.pop(k, None)
             for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_API_KEY")}
    try:
        get_extraction_provider()
    except ExtractionUnavailable as exc:
        assert "No vision-extraction provider configured" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ExtractionUnavailable")
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v


class _FakeProvider:
    """Minimal VisionExtractionProvider for factory wiring tests (no SDK/keys)."""

    def __init__(self, name: str, *, fail: bool) -> None:
        self.name = name
        self._fail = fail
        self.calls = 0

    async def extract(self, image_bytes: bytes, doc_type: str = "auto") -> ExtractionResult:
        self.calls += 1
        return _err_result(self.name) if self._fail else _ok_result(self.name)


def _with_registry(entries: dict, fn):
    saved = factory._REGISTRY.copy()
    factory._REGISTRY.clear()
    factory._REGISTRY.update(entries)
    try:
        return fn()
    finally:
        factory._REGISTRY.clear()
        factory._REGISTRY.update(saved)


def test_get_provider_single_when_one_configured() -> None:
    os.environ["FAKE_PRIMARY"] = "x"
    try:
        prov = _with_registry(
            {"gemini_flash": (lambda: _FakeProvider("primary", fail=False), ("FAKE_PRIMARY",))},
            lambda: get_extraction_provider("gemini_flash"),
        )
        assert isinstance(prov, _FakeProvider) and prov.name == "primary"
    finally:
        os.environ.pop("FAKE_PRIMARY", None)


def test_fallback_advances_only_on_hard_failure() -> None:
    primary = _FakeProvider("primary", fail=True)
    backup = _FakeProvider("backup", fail=False)
    fb = factory._FallbackProvider([primary, backup])
    assert fb.name == "fallback:primary>backup"
    res = asyncio.run(fb.extract(b"img"))
    assert res.provider == "backup" and res.is_error is False
    assert primary.calls == 1 and backup.calls == 1


def test_fallback_charges_once_on_success() -> None:
    primary = _FakeProvider("primary", fail=False)
    backup = _FakeProvider("backup", fail=False)
    fb = factory._FallbackProvider([primary, backup])
    res = asyncio.run(fb.extract(b"img"))
    assert res.provider == "primary"
    assert primary.calls == 1 and backup.calls == 0  # backup never touched


def test_fallback_returns_last_error_when_all_fail() -> None:
    a = _FakeProvider("a", fail=True)
    b = _FakeProvider("b", fail=True)
    res = asyncio.run(factory._FallbackProvider([a, b]).extract(b"img"))
    assert res.is_error is True and res.provider == "b"


def _run_all() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
