"""Quick look: run ONE document through a provider and print what it extracted.

Unlike the benchmark (which scores against ground truth), this just shows the raw
ExtractionResult — fields, confidence, doc_type, latency, cost — so you can eyeball
whether extraction works on a real PDF before assembling the 15-sample set.

Usage:
    export GEMINI_API_KEY=...        # for --provider gemini_flash
    # or: export CLAUDE_API_KEY=...      for claude_haiku / claude_sonnet
    python -m backend.modules.extraction.probe \\
        --file /path/to/contract.pdf --provider gemini_flash --doc-type auto

Never prints the API key. Accepts PDF or image (PNG/JPEG/WebP).
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
from pathlib import Path

from .schemas import CANONICAL_FIELDS, ExtractionResult

_REGISTRY = {
    "gemini_flash": ("providers.gemini_flash", "GeminiFlashProvider"),
    "claude_haiku": ("providers.claude_haiku", "ClaudeHaikuProvider"),
    "claude_sonnet": ("providers.claude_sonnet", "ClaudeSonnetProvider"),
}


def _instantiate(name: str):
    mod_suffix, cls = _REGISTRY[name]
    module = importlib.import_module(f"backend.modules.extraction.{mod_suffix}")
    return getattr(module, cls)()


def _print(result: ExtractionResult) -> None:
    print(f"\n=== {result.provider} ({result.model}) ===")
    print(f"doc_type      : {result.doc_type.value}  (conf {result.doc_type_confidence:.2f})")
    print(f"latency       : {result.latency_ms:.0f} ms")
    print(f"cost          : {result.cost_vnd:.2f} đ  "
          f"(in {result.usage.input_tokens} / out {result.usage.output_tokens} tok)")
    if result.warnings:
        print(f"warnings      : {result.warnings}")
    print("-" * 60)
    for key in CANONICAL_FIELDS:
        f = result.fields.get(key)
        if not f:
            continue
        flag = "⚠️ review" if f.needs_review else "ok"
        print(f"{key:24} | conf {f.confidence:.2f} | {flag:9} | {f.value!r}")
    print()


async def _main_async(args) -> None:
    provider = _instantiate(args.provider)
    image_bytes = Path(args.file).read_bytes()
    result = await provider.extract(image_bytes, args.doc_type)
    if args.json:
        print(result.model_dump_json(indent=2))
    else:
        _print(result)


def main() -> None:
    p = argparse.ArgumentParser(description="Probe one document through a provider")
    p.add_argument("--file", required=True, help="path to a PDF or image")
    p.add_argument("--provider", default="gemini_flash", choices=list(_REGISTRY))
    p.add_argument("--doc-type", default="auto",
                   help="hd_thue_mat_bang | hd_nha_cung_cap | hd_lao_dong | auto")
    p.add_argument("--json", action="store_true", help="dump full ExtractionResult JSON")
    args = p.parse_args()
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
