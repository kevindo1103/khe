# KHE_AI — Session STATE

> Owner: **KHE_AI** (single-owner Phase 1). Scope: `backend/modules/extraction/**`,
> `docs/teams/ai_STATE.md`, `docs/benchmark_*.md` (via DOCS_INBOX).
> Branch: `claude/feat-ai-vision-extraction-3k3gup`.

_Last updated: 2026-06-18 (issue #53 — provider factory for Backend #25 PR-B)_

## Decisions in force
- **DEC-002** — single `VisionExtractionProvider.extract()` interface; NO separate
  OCR + LLM pipeline.
- **DEC-010** — US-hosted APIs OK in Phase 1; log `consent_reference` to `events`
  before first extraction per tenant (NĐ 13/2023).
- **D-01 / D-06** — extraction is READ-ONLY; AI never authors/edits legal content.

## Provider lineup
| Provider | Role | Model | ~Cost/doc target |
|---|---|---|---|
| GeminiFlashProvider | primary | `gemini-2.5-flash` | 150đ |
| ClaudeHaikuProvider | fallback (<90% accuracy) | `claude-haiku-4-5` | 300đ |
| ClaudeSonnetProvider | complex / handwritten | `claude-sonnet-4-6` | — |

## Done (issue #53 — provider factory for Backend #25 PR-B)
- [x] `get_extraction_provider(prefer="gemini_flash")` exported from
      `modules.extraction` public API — returns a ready `VisionExtractionProvider`.
- [x] Typed `ExtractionUnavailable` (RuntimeError subclass) when no key/SDK present
      → Backend maps to 503 / status=failed (infra condition, not a doc error).
- [x] Key handling encapsulated (lazy; `GEMINI_API_KEY`/`CLAUDE_API_KEY` + Google/
      Anthropic fallbacks). `import main` stays green without keys/SDKs.
- [x] Fallback policy encapsulated (DEC-002): Gemini primary → Claude Haiku.
      `_FallbackProvider` advances **only on hard failure** (`ExtractionResult.is_error`)
      — happy path charged once; never re-routes on mere `needs_review`.
- [x] `ExtractionResult.is_error` property (warnings + 0 input tokens) — lets Backend
      distinguish failure from a successful-but-uncertain extraction (D-08).
- [x] +8 unit tests (no keys/SDKs); 18 total passing. README usage updated.
- Final signature posted to #53 for KHE_Backend to wire PR-B.

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
- **Live benchmark numbers (full 15-sample run)** — needs:
  1. 15 HĐ thật F&B/bán lẻ (PM decision 2026-06-11: **không dùng synthetic**, chờ
     bộ thật để số liệu có giá trị quyết định).
  2. Gemini quota — billing đang process (PM screenshot 2026-06-11). Claude OK.
  3. PII scrub trước khi đưa vào fixtures (NĐ 13/2023).
  → `blocker:waiting-dependency` (samples + Gemini billing).
- **Long PDFs (>~100 trang, >~32MB)** — file FIDIC 193pp/18.8MB vượt Claude inline
  + Gemini inline limit. Cần File API path (deferred to Sprint 1; F&B SME contracts
  thường ngắn → low priority).

## Live test 2026-06-11 — H_MB_6.pdf (HĐ mua bán BĐS, 59pp scan)
First end-to-end run with real provider keys. Pipeline verified on a **scanned
(no text layer) PDF** — single vision call (DEC-002), no separate OCR step.

| Metric | Haiku | Sonnet |
|---|---|---|
| doc_type | hd_nha_cung_cap (wrong — hallucinated MVP type) | khac (truthful — doc is out of MVP scope) |
| doi_tac | ✅ correct | ✅ correct |
| ngay_hieu_luc | 2021-07-11 ✅ | 2021-07-11 ✅ |
| thoi_han_hd | "36 tháng" | "36 tháng kể từ ngày Bên Bán ký biên bản nghiệm thu…" (full context) |
| ngay_het_han / gia_tri_hd | None (D-08 ✅ — no guessing) | None (D-08 ✅) |
| Latency | 32.5s | **9.1s** (3.5× faster, counter-intuitive) |
| Cost | 560đ | 1,693đ (3×) |

Gemini added 2026-06-11 (after billing active; gemini-2.0-flash retired → using
`gemini-2.5-flash`):

| Metric | Gemini 2.5 Flash |
|---|---|
| doc_type | khac (1.00) ✅ truthful |
| doi_tac / ngay_hieu_luc / thoi_han_hd | ✅ all correct (1.00) |
| dieu_khoan_thanh_toan | ✅ **full clause — both Claude models MISSED this** |
| ngay_het_han / gia_tri_hd | None (same as Claude) |
| Input tokens | **3,652** (vs Claude ~20,577 — 5.6× fewer) |
| Cost | **59đ** (vs Haiku 560đ / Sonnet 1,693đ — ~10× cheaper) |
| Latency | 14.6s |

→ Gemini Flash extracted MORE than Claude at 1/10 cost on this doc — supports
DEC-002 (Gemini primary, Claude fallback). Pricing **verified 2026-06-11**:
gemini-2.5-flash $0.30/$2.50, gemini-2.5-flash-lite $0.10/$0.40 per 1M. So 59đ is
accurate; even 2.5-flash sits well under the 150đ primary target (lite ≈14đ).

Notes:
- File **out of MVP seed** (HĐ mua bán căn hộ chung cư, không thuộc F&B/bán lẻ
  thuê/NCC/lao động). Used only as pipeline-verification, not benchmark sample.
- **Sonnet faster than Haiku on long scans** — surprising. Re-measure on 5–10
  more samples in Sprint 1; if pattern holds, Sonnet role in DEC-002 may broaden
  from "complex/handwritten" to "complex OR long-scan".
- Both providers respected D-08 (return None, never fabricate).

## DOCS_INBOX note — TO POST AFTER MERGE
Spec-impact insight to fold into BRD §6 (Term) + obligation engine spec:

```
### 2026-06-11 — KHE_AI / claude/feat-ai-vision-extraction-3k3gup
- **PR / trigger:** TBD → main (post-merge)
- **Đã đụng:** backend/modules/extraction/** (scope-only), docs/benchmark_*, docs/teams/ai_STATE.md
- **Thay đổi:** Live-test trên HĐ thật cho thấy **HĐ VN thường ghi
  `ngày hiệu lực + thời hạn`, không ghi thẳng `ngày hết hạn`**. Trong sample
  H_MB_6: model trả `ngay_het_han=None` (đúng D-08, không bịa) nhưng
  `thoi_han_hd="36 tháng"` + `ngay_hieu_luc=2021-07-11` ⇒ engine có thể suy ra.
- **Docs cần cập nhật:**
  - BRD §6 (Term/Field) — clarify: `ngày hết hạn` có thể derived = `ngày hiệu lực
    + thời hạn` ở tầng Obligation, không bắt buộc bóc trực tiếp từ Document.
  - SRS / Obligation engine spec — FR-OB-01: thêm rule "if ngay_het_han is null
    AND ngay_hieu_luc + thoi_han_hd both present ⇒ derive ngay_het_han".
- **Ambiguity / cần PM xác nhận:** xử lý `thoi_han_hd` dạng phi-số ("không xác
  định thời hạn", "kể từ khi nghiệm thu") — engine không derive được; cần định
  nghĩa: skip (no obligation) vs flag-for-human?
```

## Next
- Wait for 15 real F&B/bán lẻ HĐ + Gemini billing → run full 3-provider benchmark.
- Post DOCS_INBOX note above after Sprint-0 PR merges.
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
- issue #53 (`for:ai`, `from:backend`, `task-assignment`) — export `get_extraction_provider()`
  factory for #25 PR-B. Status: **done** — factory + typed error + fallback shipped, signature posted.
