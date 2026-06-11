# Benchmark — Vision Extraction v0.1

> **Status:** v0.1 — methodology + harness ready. **Results PENDING** a live run
> (needs API keys + the 15 PII-scrubbed Bingxue HĐ samples; not available in the
> dev container). Numbers are filled by running the harness — none are guessed.
> **Owner:** KHE_AI · **Task:** issue #3 · **Branch:** `claude/feat-ai-vision-extraction-3k3gup`

---

## 1. Goal

Pick the **primary + fallback** vision-extraction provider for Sprint 1, per
DEC-002 (single `VisionExtractionProvider.extract()`, no separate OCR step).
Candidates:

| Provider | Role | Model | Pricing (USD /1M tok) |
|---|---|---|---|
| `gemini_flash` | primary (~150đ/doc) | `gemini-2.5-flash` | $0.30 in / $2.50 out (verified 2026-06-11) |
| `claude_haiku` | fallback when accuracy <90% (~300đ/doc) | `claude-haiku-4-5` | $1.00 in / $5.00 out |
| `claude_sonnet` | complex / handwritten | `claude-sonnet-4-6` | $3.00 in / $15.00 out |

FX for đồng reporting: **25,400 VND/USD** (`providers/base.USD_TO_VND` — update if it moves).

## 2. Targets (acceptance — issue #3)

| Metric | Target |
|---|---|
| Accuracy on `ngày hết hạn`, `giá trị HĐ`, `bên ký`, `thời hạn HĐ` | **≥ 90%** |
| Cost / doc | ≤ **150đ** primary · ≤ **300đ** fallback |
| Latency p95 / doc | < **10s** |

Maps to BRD M-3 (`ngày hết hạn` extraction ≥90%).

## 3. Method

- **Dataset:** 15 PII-scrubbed contracts (lease / supplier / labor, F&B–bán lẻ
  seed). Real PII never committed — scrub before use (NĐ 13/2023). See
  `backend/modules/extraction/benchmark/fixtures/README.md`.
- **Single call per doc** per provider (DEC-002) — image in, structured JSON out
  via Claude structured outputs / Gemini `response_schema`. Same VN prompt +
  read-only guardrail (D-06) across providers for fairness.
- **Scoring** (`benchmark/metrics.py`): normalized per-field comparison —
  - dates: order- & zero-pad-agnostic (`05/01/2026` == `2026-01-05`),
  - amounts: thousand separators / currency stripped,
  - text: accent- & case-insensitive,
  - `bên ký` (`doi_tac`): predicted must cover every ground-truth party.
  Fields with empty ground truth (e.g. open-ended labor contract expiry) are not scored.
- **Aggregates:** per-field accuracy, latency p50/p95, mean cost/doc, error rate.

## 4. How to reproduce

```bash
export GEMINI_API_KEY=...        # or GOOGLE_API_KEY
export CLAUDE_API_KEY=...
# Drop 15 scrubbed images in fixtures/data/, fill fixtures/manifest.json ground truth, then:
python -m backend.modules.extraction.benchmark.runner \
    --manifest backend/modules/extraction/benchmark/fixtures/manifest.json \
    --providers gemini_flash,claude_haiku,claude_sonnet \
    --out docs/benchmark_vision_extraction_v0.1.results.md
```

> **DEC-010 / NĐ 13/2023:** a live run sends document images to US-hosted APIs.
> Per tenant, `consent_reference` must be logged to the `events` table before the
> first extraction (KHE_Backend, at the ingest call site).

## 5. Results — PENDING

Run the harness to populate. Template the runner emits:

### Accuracy (per target field)

| Provider | ngay_het_han | gia_tri_hd | doi_tac | thoi_han_hd | **Mean (target)** |
|---|---|---|---|---|---|
| gemini_flash | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| claude_haiku | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| claude_sonnet | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |

### Latency, cost & verdict

| Provider | Model | p50 (ms) | p95 (ms) | Cost/doc (đ) | Meets targets? |
|---|---|---|---|---|---|
| gemini_flash | `gemini-2.5-flash` | _pending_ | _pending_ | _pending_ | _pending_ |
| claude_haiku | `claude-haiku-4-5` | _pending_ | _pending_ | _pending_ | _pending_ |
| claude_sonnet | `claude-sonnet-4-6` | _pending_ | _pending_ | _pending_ | _pending_ |

## 6. Recommendation — PENDING

To be written from §5: confirm Gemini Flash as primary if it clears ≥90% on the
target fields within the 150đ/p95-10s budget; else promote Claude Haiku as primary
and re-baseline. Route complex/handwritten scans to Claude Sonnet.

---

### Changelog
- **v0.1** (2026-06-10, KHE_AI) — methodology, targets, harness, provider configs.
  Results pending live run.
