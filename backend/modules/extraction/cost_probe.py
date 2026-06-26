"""Batch cost probe — run a FOLDER of real documents through provider(s) and report
the actual per-doc cost distribution from live token counts.

Unlike `benchmark.runner` (which scores accuracy against ground truth and needs a
manifest), this needs no ground truth — point it at a directory of contracts and it
reports cost mean/p50/p95 + token split, so you can re-confirm DEC-002's cost figure
with real numbers. Output tokens at $2.50/M (Gemini) are the swing factor, so the
summary breaks out the output-token share of cost (DEC-026 clause-echo check).

Usage:
    export GEMINI_API_KEY=...            # for --provider gemini_flash
    # or: export CLAUDE_API_KEY=...          for claude_haiku / claude_sonnet
    python -m backend.modules.extraction.cost_probe \\
        --dir /path/to/real_contracts --provider gemini_flash
    # multiple providers + markdown report:
    python -m backend.modules.extraction.cost_probe \\
        --dir docs/samples --provider gemini_flash,claude_haiku \\
        --out docs/cost_probe_results.md

Never prints the API key. Accepts PDF + image (PNG/JPEG/WebP).

NĐ 13/2023 / DEC-010: a real run sends document images to US-hosted APIs. Use only
PII-scrubbed or consented samples — same rule as the benchmark runner.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, median
from typing import Optional

from .benchmark.metrics import _percentile

# Per-provider cost ceilings (issue #3 / DEC-002). primary 150đ, fallbacks higher.
TARGET_COST_VND = {"gemini_flash": 150.0, "claude_haiku": 300.0, "claude_sonnet": 600.0}

_PROVIDER_REGISTRY = {
    "gemini_flash": ("providers.gemini_flash", "GeminiFlashProvider"),
    "claude_haiku": ("providers.claude_haiku", "ClaudeHaikuProvider"),
    "claude_sonnet": ("providers.claude_sonnet", "ClaudeSonnetProvider"),
}

_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def _instantiate(name: str):
    mod_suffix, cls = _PROVIDER_REGISTRY[name]
    module = importlib.import_module(f"backend.modules.extraction.{mod_suffix}")
    return getattr(module, cls)()


def _collect_files(directory: Path, glob: Optional[str]) -> list[Path]:
    if glob:
        files = sorted(directory.glob(glob))
    else:
        files = sorted(p for p in directory.rglob("*") if p.suffix.lower() in _EXTENSIONS)
    return [p for p in files if p.is_file()]


@dataclass
class DocCost:
    file: str
    doc_type: str
    input_tokens: int
    output_tokens: int
    cost_vnd: float
    latency_ms: float
    warning: Optional[str] = None


@dataclass
class ProviderCost:
    provider: str
    model: str
    docs: list[DocCost] = field(default_factory=list)
    in_usd_per_mtok: float = 0.0
    out_usd_per_mtok: float = 0.0

    @property
    def ok_docs(self) -> list[DocCost]:
        """Successful extractions — failed calls return cost 0 and would skew stats."""
        return [d for d in self.docs if not d.warning]

    @property
    def costs(self) -> list[float]:
        return [d.cost_vnd for d in self.ok_docs]

    @property
    def errors(self) -> int:
        return sum(1 for d in self.docs if d.warning)

    @property
    def output_cost_share(self) -> Optional[float]:
        """Fraction of mean cost driven by output tokens (DEC-026 clause-echo check)."""
        if not self.ok_docs or self.out_usd_per_mtok == 0:
            return None
        in_usd = mean(d.input_tokens for d in self.ok_docs) / 1e6 * self.in_usd_per_mtok
        out_usd = mean(d.output_tokens for d in self.ok_docs) / 1e6 * self.out_usd_per_mtok
        total = in_usd + out_usd
        return round(out_usd / total, 3) if total else None


async def run(directory: Path, provider_names: list[str], glob: Optional[str],
              doc_type: str) -> tuple[list[ProviderCost], list[str]]:
    files = _collect_files(directory, glob)
    notes: list[str] = []
    if not files:
        notes.append(f"No documents found under {directory} (glob={glob or _EXTENSIONS}).")

    results: list[ProviderCost] = []
    for name in provider_names:
        try:
            provider = _instantiate(name)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"Skipped provider '{name}': {type(exc).__name__}: {exc}")
            continue

        pc = ProviderCost(
            provider=name,
            model=getattr(provider, "model", name),
            in_usd_per_mtok=getattr(provider, "in_usd_per_mtok", 0.0),
            out_usd_per_mtok=getattr(provider, "out_usd_per_mtok", 0.0),
        )
        for fp in files:
            result = await provider.extract(fp.read_bytes(), doc_type)
            pc.docs.append(DocCost(
                file=fp.name,
                doc_type=result.doc_type.value,
                input_tokens=result.usage.input_tokens,
                output_tokens=result.usage.output_tokens,
                cost_vnd=result.cost_vnd,
                latency_ms=result.latency_ms,
                warning=result.warnings[0] if result.warnings else None,
            ))
        results.append(pc)

    return results, notes


# --- report rendering ------------------------------------------------------

def _fmt(v: Optional[float], suffix: str = "") -> str:
    return "—" if v is None else f"{v}{suffix}"


def render_report(results: list[ProviderCost], notes: list[str], directory: Path) -> str:
    lines: list[str] = ["# Cost probe — real per-doc extraction cost\n"]
    n = len(results[0].docs) if results else 0
    lines.append(f"- Directory: `{directory}`")
    lines.append(f"- Documents: {n}")
    lines.append("")

    for pc in results:
        costs = pc.costs
        lines.append(f"## {pc.provider} — `{pc.model}`\n")
        if not costs:
            if pc.docs:
                lines.append(f"> All {len(pc.docs)} extractions failed — no cost data. "
                             f"First warning: {pc.docs[0].warning}\n")
            else:
                lines.append("> No documents extracted.\n")
            continue

        ceiling = TARGET_COST_VND.get(pc.provider)
        cost_mean = round(mean(costs), 2)
        verdict = ""
        if ceiling is not None:
            verdict = " ✅" if cost_mean <= ceiling else " ⚠️ over ceiling"

        share = pc.output_cost_share
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        lines.append(f"| Cost mean | **{cost_mean}đ** (ceiling {_fmt(ceiling)}đ){verdict} |")
        lines.append(f"| Cost p50 / p95 | {median(costs):.2f}đ / {_fmt(_percentile(costs, 95))}đ |")
        lines.append(f"| Cost min / max | {min(costs):.2f}đ / {max(costs):.2f}đ |")
        lines.append(f"| Input tokens (mean) | {round(mean(d.input_tokens for d in pc.ok_docs))} |")
        lines.append(f"| Output tokens (mean) | {round(mean(d.output_tokens for d in pc.ok_docs))} |")
        if share is not None:
            lines.append(f"| Output-token cost share | {share * 100:.1f}% |")
        lines.append(f"| Latency p50 / p95 | {_fmt(_percentile([d.latency_ms for d in pc.docs], 50))} / "
                     f"{_fmt(_percentile([d.latency_ms for d in pc.docs], 95))} ms |")
        lines.append(f"| Errors | {pc.errors}/{len(pc.docs)} (cost stats over {len(pc.ok_docs)} ok) |")
        lines.append("")

        # Per-doc detail.
        lines.append("| Doc | doc_type | in tok | out tok | cost đ | latency ms | warn |")
        lines.append("|---|---|---|---|---|---|---|")
        for d in pc.docs:
            warn = "⚠️" if d.warning else ""
            lines.append(f"| {d.file} | {d.doc_type} | {d.input_tokens} | {d.output_tokens} | "
                         f"{d.cost_vnd:.2f} | {d.latency_ms:.0f} | {warn} |")
        lines.append("")

    if notes:
        lines.append("## Notes\n")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description="Batch cost probe over a folder of documents")
    p.add_argument("--dir", required=True, type=Path, help="directory of contracts (recursed)")
    p.add_argument("--provider", default="gemini_flash",
                   help="comma-separated provider names")
    p.add_argument("--glob", default=None,
                   help="optional glob within --dir (default: all pdf/png/jpg/jpeg/webp)")
    p.add_argument("--doc-type", default="auto", help="hint passed to every doc")
    p.add_argument("--out", type=Path, default=None, help="write Markdown report here")
    args = p.parse_args()

    names = [n.strip() for n in args.provider.split(",") if n.strip()]
    unknown = [n for n in names if n not in _PROVIDER_REGISTRY]
    if unknown:
        p.error(f"unknown providers: {unknown}. known: {list(_PROVIDER_REGISTRY)}")

    results, notes = asyncio.run(run(args.dir, names, args.glob, args.doc_type))
    report = render_report(results, notes, args.dir)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"Wrote report → {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
