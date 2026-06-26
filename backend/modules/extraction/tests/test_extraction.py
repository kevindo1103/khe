"""Pure unit tests for the extraction module — no API keys / SDKs required.

Run: `python -m backend.modules.extraction.tests.test_extraction` or `pytest`.
Covers schemas, metric normalization/matching, scoring, and report rendering.
"""

from __future__ import annotations

from pathlib import Path

from ..schemas import (
    BENCHMARK_TARGET_FIELDS,
    CANONICAL_FIELDS,
    DocType,
    ExtractedField,
    ExtractionResult,
)
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


def _run_all() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
