# `backend/modules/extraction` — Khế Vision Extraction (KHE_AI)

Single-call vision extraction (DEC-002): one `VisionExtractionProvider.extract()`
reads a contract image/PDF and returns structured **read-only** Terms. **No
separate OCR + LLM pipeline.**

## Guardrails (CLAUDE.md §D-rules)
- **D-01 / P-1** — AI is never the system of record; it only reads.
- **D-06 / FR-EX-03** — extraction is READ-ONLY. Providers never generate or
  modify legal content. Baked into `prompts.SYSTEM_GUARDRAIL`.
- **D-08 / FR-CQ-03** — missing field → `value=None`, `needs_review=True`. Never guess.
- **FR-EX-05** — every field carries `confidence` + `needs_review`.
- **DEC-010 / NĐ 13/2023** — US-hosted APIs OK in Phase 1; the ingest call site
  (KHE_Backend) must log `consent_reference` to `events` before the first
  extraction per tenant.

## Layout
```
schemas.py        ExtractionResult, ExtractedField, ContractExtractionLLM, DocType
provider.py       VisionExtractionProvider Protocol (the DEC-002 interface)
prompts.py        VN read-only extraction prompts (shared → fair benchmark)
providers/
  gemini_flash.py  primary  (~150đ/doc) — gemini-2.0-flash
  claude_haiku.py  fallback (~300đ/doc) — claude-haiku-4-5
  claude_sonnet.py complex/handwritten — claude-sonnet-4-6
  base.py / _claude.py  shared helpers
benchmark/
  runner.py        run providers over a manifest → Markdown report
  metrics.py       normalized per-field scoring, latency p50/p95, cost/doc
  fixtures/        manifest template + PII rules (data/ gitignored)
tests/            pure unit tests (no keys/SDKs required)
```

## Usage
```python
from backend.modules.extraction.providers import GeminiFlashProvider

provider = GeminiFlashProvider()              # reads GEMINI_API_KEY
result = await provider.extract(image_bytes, doc_type="hd_thue_mat_bang")
result.fields["ngay_het_han"].value           # → expiry date (or None)
result.fields["ngay_het_han"].needs_review    # → human-check flag
result.cost_vnd, result.latency_ms            # provenance/metrics
```

Importing the package needs only `pydantic`. Provider SDKs (`anthropic`,
`google-genai`) are imported lazily inside each provider.

## Benchmark
See `benchmark/fixtures/README.md`. Scores accuracy on `ngay_het_han`,
`gia_tri_hd`, `doi_tac`, `thoi_han_hd` (≥90% target) plus latency p95 (<10s) and
cost/doc (≤150đ primary / ≤300đ fallback). Output → `docs/benchmark_vision_extraction_v0.1.md`.

## Scope-lock
Changing `provider.py` (the interface) requires coordinating with KHE_Backend via
PM first. Benchmark results that change architecture → report to DOCS_INBOX (#1).
