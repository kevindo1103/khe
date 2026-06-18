"""Scoring: normalized field comparison + accuracy / latency / cost aggregation.

Normalization is field-type aware so trivial format differences (date layout,
thousand separators, casing/whitespace) don't count as misses — accuracy reflects
whether the *Term* was read correctly, not whether the string matched byte-for-byte.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from statistics import median
from typing import Iterable, Optional

from ..schemas import BENCHMARK_TARGET_FIELDS, ExtractionResult

_DATE_FIELDS = {"ngay_hieu_luc", "ngay_het_han"}
_NUMERIC_FIELDS = {"gia_tri_hd"}


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def normalize(field_key: str, value: Optional[str]) -> str:
    """Field-type-aware normalization for comparison. Returns "" for missing."""
    if value is None:
        return ""
    v = str(value).strip()
    if not v:
        return ""

    if field_key in _DATE_FIELDS:
        nums = [int(d) for d in re.findall(r"\d+", v)]
        # Order-/zero-pad-agnostic signature so 05/01/2026 == 2026-01-05 == 5-1-2026.
        return "-".join(str(n) for n in sorted(nums)) if nums else _norm_text(v)

    if field_key in _NUMERIC_FIELDS:
        digits = re.sub(r"\D", "", v)
        return digits or _norm_text(v)

    return _norm_text(v)


def _norm_text(v: str) -> str:
    v = _strip_accents(v.lower())
    v = re.sub(r"[^a-z0-9; ]+", " ", v)
    return re.sub(r"\s+", " ", v).strip()


def field_match(field_key: str, predicted: Optional[str], truth: Optional[str]) -> bool:
    """True if the predicted value matches ground truth after normalization.

    For `doi_tac` (multi-party, ";"-joined) we require the predicted set to cover
    every ground-truth party (order-independent), which is how a human would judge
    "did it get the signing parties"."""
    np_, nt = normalize(field_key, predicted), normalize(field_key, truth)
    if nt == "":
        # No ground truth for this field on this sample → not scored (caller skips).
        return np_ == ""
    if field_key == "doi_tac":
        truth_parts = {p.strip() for p in nt.split(";") if p.strip()}
        pred_parts = {p.strip() for p in np_.split(";") if p.strip()}
        return truth_parts.issubset(pred_parts) and bool(pred_parts)
    return np_ == nt


@dataclass
class FieldScore:
    field_key: str
    correct: int = 0
    scored: int = 0  # samples where ground truth had a value for this field

    @property
    def accuracy(self) -> Optional[float]:
        return (self.correct / self.scored) if self.scored else None


@dataclass
class ProviderScore:
    provider: str
    model: str
    fields: dict[str, FieldScore] = field(default_factory=dict)
    latencies_ms: list[float] = field(default_factory=list)
    costs_vnd: list[float] = field(default_factory=list)
    samples: int = 0
    errors: int = 0  # extractions that returned a warning / no structured output

    # --- aggregates -------------------------------------------------------
    @property
    def latency_p50(self) -> Optional[float]:
        return round(median(self.latencies_ms), 1) if self.latencies_ms else None

    @property
    def latency_p95(self) -> Optional[float]:
        return _percentile(self.latencies_ms, 95)

    @property
    def cost_mean(self) -> Optional[float]:
        return round(sum(self.costs_vnd) / len(self.costs_vnd), 2) if self.costs_vnd else None

    @property
    def target_accuracy(self) -> Optional[float]:
        """Mean accuracy across the four benchmark target fields (issue #3)."""
        accs = [
            self.fields[k].accuracy
            for k in BENCHMARK_TARGET_FIELDS
            if k in self.fields and self.fields[k].accuracy is not None
        ]
        return round(sum(accs) / len(accs), 4) if accs else None


def _percentile(values: list[float], pct: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 1)
    rank = (pct / 100) * (len(ordered) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    frac = rank - lo
    return round(ordered[lo] + (ordered[hi] - ordered[lo]) * frac, 1)


def score(
    provider_name: str,
    model: str,
    results: Iterable[tuple[ExtractionResult, dict[str, Optional[str]]]],
) -> ProviderScore:
    """Aggregate one provider's results.

    results: iterable of (ExtractionResult, ground_truth_field_map).
    """
    ps = ProviderScore(provider=provider_name, model=model)
    for result, truth in results:
        ps.samples += 1
        ps.latencies_ms.append(result.latency_ms)
        ps.costs_vnd.append(result.cost_vnd)
        if result.warnings:
            ps.errors += 1
        for field_key, truth_value in truth.items():
            if normalize(field_key, truth_value) == "":
                continue  # no ground truth → don't score
            fs = ps.fields.setdefault(field_key, FieldScore(field_key))
            fs.scored += 1
            predicted = result.fields.get(field_key)
            pred_value = predicted.value if predicted else None
            if field_match(field_key, pred_value, truth_value):
                fs.correct += 1
    return ps
