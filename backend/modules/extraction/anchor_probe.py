"""Anchor probe — run ONE real document through a provider and report whether the
per-field source anchors (page_num / ref) come back populated (#230 / FR-EX-05).

This is the isolated, KHE_AI-scope validator for #230. The staging E2E smoke can NOT
test #230 until the feature branch is deployed there (the anchor schema + prompt live
only on the PR), and even then it couples the test to auth/nginx/tenant DBs. This probe
calls the VisionExtractionProvider directly: image in → ExtractionResult out → print
each field's value + page_num + ref. No HTTP, no auth, no DB.

It answers exactly one question: with the current schema + prompt, does Gemini fill the
anchor slots on a real contract? gemini_flash → anchors expected; claude_* → null by
design (lean base schema is anchor-free, graceful-degrade per #217).

Usage:
    export GEMINI_API_KEY=...                 # for --provider gemini_flash (default)
    # or: export CLAUDE_API_KEY=...               for claude_haiku / claude_sonnet
    python -m backend.modules.extraction.anchor_probe --file /path/to/contract.pdf
    python -m backend.modules.extraction.anchor_probe --file c.png --provider claude_haiku

Exit code: 0 if the anchor expectation for the provider is met, 1 otherwise — so it
doubles as the #230 gate (replaces the staging-smoke Step-8 gate that can't see the PR).

Never prints the API key. Accepts PDF + image (PNG/JPEG/WebP).

NĐ 13/2023 / DEC-010: a real run sends the document image to a US-hosted API. Use only
PII-scrubbed or consented samples — same rule as the benchmark + cost probes.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import sys
from pathlib import Path

_PROVIDER_REGISTRY = {
    "gemini_flash": ("providers.gemini_flash", "GeminiFlashProvider"),
    "claude_haiku": ("providers.claude_haiku", "ClaudeHaikuProvider"),
    "claude_sonnet": ("providers.claude_sonnet", "ClaudeSonnetProvider"),
}


def _instantiate(name: str):
    mod_suffix, cls = _PROVIDER_REGISTRY[name]
    module = importlib.import_module(f"backend.modules.extraction.{mod_suffix}")
    return getattr(module, cls)()


def _truncate(value: str | None, width: int = 32) -> str:
    if value is None:
        return "—"
    value = " ".join(value.split())
    return value if len(value) <= width else value[: width - 1] + "…"


async def _run(file_path: Path, provider_name: str) -> int:
    provider = _instantiate(provider_name)
    image_bytes = file_path.read_bytes()

    print(f"\nDocument : {file_path.name} ({len(image_bytes):,} bytes)")
    print(f"Provider : {provider_name} ({getattr(provider, 'model', '?')})")
    print("Probing  … (one live vision call)\n")

    result = await provider.extract(image_bytes)

    if result.is_error:
        print(f"  ✗ extraction FAILED: {'; '.join(result.warnings) or 'unknown'}")
        return 1

    fields = result.fields
    total = len(fields)
    with_value = sum(1 for f in fields.values() if f and f.value is not None)
    with_page = sum(1 for f in fields.values() if getattr(f, "page_num", None) is not None)
    with_ref = sum(1 for f in fields.values() if getattr(f, "ref", None) is not None)

    # Per-field table.
    print(f"  {'field':<26} {'value':<33} {'page':<5} ref")
    print(f"  {'-' * 26} {'-' * 33} {'-' * 5} {'-' * 12}")
    for name, f in fields.items():
        if f is None:
            continue
        page = getattr(f, "page_num", None)
        ref = getattr(f, "ref", None)
        print(
            f"  {name:<26} {_truncate(f.value):<33} "
            f"{('—' if page is None else str(page)):<5} {_truncate(ref, 28)}"
        )

    print(
        f"\n  doc_type={result.doc_type.value} "
        f"terms={total} with_value={with_value} "
        f"clauses={len(result.clauses)} parties={len(result.parties)} "
        f"obligations={len(result.obligation_schedule)}"
    )
    print(f"  anchored: page_num={with_page}/{total}  ref={with_ref}/{total}")
    print(
        f"  cost≈{result.cost_vnd:.1f}đ  latency={result.latency_ms:.0f}ms  "
        f"tokens in={result.usage.input_tokens} out={result.usage.output_tokens}"
    )

    # ── #230 gate ──
    # gemini_flash: anchors REQUIRED — at least one field with value should carry a
    #   page_num (single-page docs default to 1). Zero page_num across all valued fields
    #   = the model ignored the anchor ask → fix the prompt/schema, don't merge.
    # claude_*: anchors null is CORRECT (lean base schema has no anchor slots).
    print()
    if provider_name == "gemini_flash":
        if with_value == 0:
            print("  ⚠ no fields had a value — cannot judge anchors (is this a real contract?).")
            return 1
        if with_page > 0:
            print(f"  ✓ #230 PASS — Gemini populated page_num on {with_page}/{with_value} valued fields.")
            return 0
        print("  ✗ #230 FAIL — Gemini returned 0 page_num despite valued fields + anchor prompt.")
        print("    Next: strengthen _ANCHOR_SPEC further, or narrow anchor scope, then re-probe.")
        return 1
    if provider_name.startswith("claude"):
        if with_page == 0 and with_ref == 0:
            print("  ✓ #230 OK — Claude lean schema is anchor-free by design (graceful null).")
            return 0
        print(f"  ⚠ unexpected: Claude returned anchors (page={with_page}, ref={with_ref}).")
        return 0
    print(f"  ℹ provider={provider_name}: no #230 expectation defined.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe per-field source anchors (#230).")
    parser.add_argument("--file", required=True, help="Path to a real contract (PDF/PNG/JPEG/WebP).")
    parser.add_argument(
        "--provider",
        default="gemini_flash",
        choices=sorted(_PROVIDER_REGISTRY),
        help="Provider to probe (default: gemini_flash).",
    )
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.is_file():
        print(f"ERROR: file not found: {file_path}", file=sys.stderr)
        sys.exit(2)

    exit_code = asyncio.run(_run(file_path, args.provider))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
