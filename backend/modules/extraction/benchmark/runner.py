"""Benchmark runner (issue #3).

Runs each provider over a manifest of PII-scrubbed contract samples, scores them,
and renders a Markdown report.

Manifest JSON shape (see fixtures/manifest.example.json):
    {
      "samples": [
        {
          "id": "lease-01",
          "image": "data/lease-01.jpg",     # relative to manifest dir (or absolute)
          "doc_type": "hd_thue_mat_bang",   # caller hint, "auto" allowed
          "ground_truth": {
            "doi_tac": "Cong ty A; Ong B",
            "ngay_het_han": "2026-12-31",
            "gia_tri_hd": "50000000",
            "thoi_han_hd": "12 thang"
          }
        }
      ]
    }

Usage:
    export GEMINI_API_KEY=... ANTHROPIC_API_KEY=...
    python -m backend.modules.extraction.benchmark.runner \\
        --manifest backend/modules/extraction/benchmark/fixtures/manifest.json \\
        --providers gemini_flash,claude_haiku,claude_sonnet \\
        --out docs/benchmark_vision_extraction_v0.1.results.md

NĐ 13/2023 / DEC-010: a real run sends document images to US-hosted APIs. Per
tenant, log `consent_reference` to the events table BEFORE the first extraction
(handled by KHE_Backend at the ingest call site, not here).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import date
from pathlib import Path
from typing import Optional

from ..schemas import BENCHMARK_TARGET_FIELDS
from .metrics import ProviderScore, score

# Target thresholds (issue #3).
TARGET_ACCURACY = 0.90
TARGET_LATENCY_P95_MS = 10_000.0
TARGET_COST_VND = {"gemini_flash": 150.0, "claude_haiku": 300.0, "claude_sonnet": 600.0}

_PROVIDER_REGISTRY = {
    "gemini_flash": ("providers.gemini_flash", "GeminiFlashProvider"),
    "claude_haiku": ("providers.claude_haiku", "ClaudeHaikuProvider"),
    "claude_sonnet": ("providers.claude_sonnet", "ClaudeSonnetProvider"),
}


def _instantiate(name: str):
    """Import + construct a provider by registry name (raises on missing SDK/key)."""
    mod_suffix, cls_name = _PROVIDER_REGISTRY[name]
    import importlib

    module = importlib.import_module(f"backend.modules.extraction.{mod_suffix}")
    return getattr(module, cls_name)()


def _load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("samples", [])


async def run(
    manifest_path: Path, provider_names: list[str]
) -> tuple[list[ProviderScore], list[str]]:
    samples = _load_manifest(manifest_path)
    notes: list[str] = []
    if not samples:
        notes.append(f"Manifest {manifest_path} has 0 samples — nothing to benchmark.")

    base_dir = manifest_path.parent
    scores: list[ProviderScore] = []

    for name in provider_names:
        try:
            provider = _instantiate(name)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"Skipped provider '{name}': {type(exc).__name__}: {exc}")
            continue

        pairs = []
        for s in samples:
            img_path = Path(s["image"])
            if not img_path.is_absolute():
                img_path = base_dir / img_path
            if not img_path.exists():
                notes.append(f"[{name}] sample '{s.get('id')}' image missing: {img_path}")
                continue
            image_bytes = img_path.read_bytes()
            result = await provider.extract(image_bytes, s.get("doc_type", "auto"))
            pairs.append((result, s.get("ground_truth", {})))

        scores.append(score(name, getattr(provider, "model", name), pairs))

    return scores, notes


# --- report rendering ------------------------------------------------------

def _fmt(v: Optional[float], suffix: str = "") -> str:
    return "—" if v is None else f"{v}{suffix}"


def _pct(v: Optional[float]) -> str:
    return "—" if v is None else f"{v * 100:.1f}%"


def render_report(scores: list[ProviderScore], notes: list[str], manifest_path: Path) -> str:
    n_samples = scores[0].samples if scores else 0
    lines: list[str] = []
    lines.append(f"# Benchmark results — vision extraction (auto-generated)\n")
    lines.append(f"- Date: {date.today().isoformat()}")
    lines.append(f"- Manifest: `{manifest_path}`")
    lines.append(f"- Samples: {n_samples}")
    lines.append("")

    if not scores:
        lines.append("> No provider produced results. See notes below.")
        lines.append("")
    else:
        # Accuracy table — target fields + mean.
        header = "| Provider | " + " | ".join(BENCHMARK_TARGET_FIELDS) + " | **Mean (target)** |"
        sep = "|" + "---|" * (len(BENCHMARK_TARGET_FIELDS) + 2)
        lines.append("## Accuracy (per target field)\n")
        lines.append(header)
        lines.append(sep)
        for ps in scores:
            cells = [
                _pct(ps.fields[k].accuracy) if k in ps.fields else "—"
                for k in BENCHMARK_TARGET_FIELDS
            ]
            lines.append(f"| {ps.provider} | " + " | ".join(cells) + f" | {_pct(ps.target_accuracy)} |")
        lines.append("")

        # Latency + cost + verdict.
        lines.append("## Latency, cost & verdict\n")
        lines.append("| Provider | Model | p50 (ms) | p95 (ms) | Cost/doc (đ) | Errors | Meets targets? |")
        lines.append("|---|---|---|---|---|---|---|")
        for ps in scores:
            verdict = _verdict(ps)
            lines.append(
                f"| {ps.provider} | `{ps.model}` | {_fmt(ps.latency_p50)} | "
                f"{_fmt(ps.latency_p95)} | {_fmt(ps.cost_mean)} | {ps.errors}/{ps.samples} | {verdict} |"
            )
        lines.append("")
        lines.append(
            f"_Targets: accuracy ≥ {TARGET_ACCURACY:.0%} on target fields · "
            f"p95 < {TARGET_LATENCY_P95_MS:.0f} ms · "
            f"cost ≤ 150đ (primary) / 300đ (fallback)._\n"
        )

    if notes:
        lines.append("## Notes\n")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")

    return "\n".join(lines)


def _verdict(ps: ProviderScore) -> str:
    checks = []
    if ps.target_accuracy is not None:
        checks.append(ps.target_accuracy >= TARGET_ACCURACY)
    if ps.latency_p95 is not None:
        checks.append(ps.latency_p95 < TARGET_LATENCY_P95_MS)
    if ps.cost_mean is not None:
        checks.append(ps.cost_mean <= TARGET_COST_VND.get(ps.provider, float("inf")))
    if not checks:
        return "n/a (no data)"
    return "✅ pass" if all(checks) else "⚠️ review"


def main() -> None:
    parser = argparse.ArgumentParser(description="Khế vision-extraction benchmark runner")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument(
        "--providers",
        default="gemini_flash,claude_haiku,claude_sonnet",
        help="comma-separated provider names",
    )
    parser.add_argument("--out", type=Path, default=None, help="write Markdown report here")
    args = parser.parse_args()

    provider_names = [p.strip() for p in args.providers.split(",") if p.strip()]
    unknown = [p for p in provider_names if p not in _PROVIDER_REGISTRY]
    if unknown:
        parser.error(f"unknown providers: {unknown}. known: {list(_PROVIDER_REGISTRY)}")

    scores, notes = asyncio.run(run(args.manifest, provider_names))
    report = render_report(scores, notes, args.manifest)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"Wrote report → {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
