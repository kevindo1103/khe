# KHE_AI — Session STATE

> Owner: **KHE_AI** (single-owner Phase 1). Scope: `backend/modules/extraction/**`,
> `docs/teams/ai_STATE.md`, `docs/benchmark_*.md` (via DOCS_INBOX).
> Branch: `claude/feat-ai-vision-extraction-3k3gup`.

_Last updated: 2026-06-10_

## Decisions in force
- **DEC-002** — single `VisionExtractionProvider.extract()` interface; NO separate
  OCR + LLM pipeline.
- **DEC-010** — US-hosted APIs OK in Phase 1; log `consent_reference` to `events`
  before first extraction per tenant (NĐ 13/2023).
- **D-01 / D-06** — extraction is READ-ONLY; AI never authors/edits legal content.

## Provider lineup
| Provider | Role | Model | ~Cost/doc target |
|---|---|---|---|
| GeminiFlashProvider | primary | `gemini-2.0-flash` | 150đ |
| ClaudeHaikuProvider | fallback (<90% accuracy) | `claude-haiku-4-5` | 300đ |
| ClaudeSonnetProvider | complex / handwritten | `claude-sonnet-4-6` | — |

## Done (issue #3 — Sprint 0)
- [x] `VisionExtractionProvider` Protocol + `ExtractionResult` / `ExtractedField` /
      `ContractExtractionLLM` schemas (confidence + needs_review; D-06/D-08 enforced).
- [x] GeminiFlash / ClaudeHaiku / ClaudeSonnet adapters (single-call vision +
      structured output; lazy SDK import; honest error reporting, no fabrication).
- [x] Shared VN read-only prompts; USD→VND cost + latency instrumentation.
- [x] Benchmark runner + normalized metrics (per-field accuracy, p50/p95, cost/doc).
- [x] Fixtures manifest template + PII rules (`data/`, `manifest.json` gitignored).
- [x] 10 pure unit tests (no keys/SDKs) — passing.
- [x] `docs/benchmark_vision_extraction_v0.1.md` (methodology + targets; results pending).

## Blocked / pending
- **Live benchmark numbers** — needs API keys + 15 PII-scrubbed Bingxue HĐ samples
  (not available in dev container). Harness ready; run per benchmark doc §4.
  → `blocker:waiting-dependency` (samples + keys).

## Next
- Run live benchmark → fill `docs/benchmark_vision_extraction_v0.1.md` §5/§6.
- If results change architecture spec → report DOCS_INBOX (#1).
- Coordinate with KHE_Backend on the ingest call site that invokes `extract()` +
  logs `consent_reference` (interface change → via PM first).

## Env / secrets (relay KHE_Infra, 2026-06-11)
- GitHub Actions secrets set in repo: **`GEMINI_API_KEY`** (primary) and
  **`CLAUDE_API_KEY`** (fallback). Injected at runtime via deploy-main/staging.yml.
- Code reads `os.environ["GEMINI_API_KEY"]` / `os.environ["CLAUDE_API_KEY"]`
  (Claude provider falls back to `ANTHROPIC_API_KEY` for local/SDK default). Never log/hardcode.
- Local dev: add both to `backend/.env.local` (gitignored).

## Inbox
- issue #3 (`for:ai`, `task-assignment`) — Sprint 0 benchmark. Status: implementation
  done; awaiting live run for results.
- relay KHE_Infra (2026-06-11) — secret names confirmed; provider key lookup aligned to `CLAUDE_API_KEY`.
