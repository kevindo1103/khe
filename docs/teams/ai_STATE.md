# KHE_AI — Session STATE

> Owner: **KHE_AI** (single-owner Phase 1). Scope: `backend/modules/extraction/**`,
> `docs/teams/ai_STATE.md`, `docs/benchmark_*.md` (via DOCS_INBOX).
> Branch: `claude/feat-ai-vision-extraction-3k3gup`.

_Last updated: 2026-06-25 (Sprint 1 wrap — #230 anchors live, #258 remap shipped, #268 analysis posted)_

## Decisions in force
- **DEC-002** — single `VisionExtractionProvider.extract()` interface; NO separate
  OCR + LLM pipeline.
- **DEC-010** — US-hosted APIs OK in Phase 1; log `consent_reference` to `events`
  before first extraction per tenant (NĐ 13/2023).
- **D-01 / D-06** — extraction is READ-ONLY; AI never authors/edits legal content.

## Provider lineup
| Provider | Role | Model | ~Cost/doc |
|---|---|---|---|
| GeminiFlashProvider | primary (vision) | `gemini-2.5-flash` | ~177đ (measured) |
| ClaudeHaikuProvider | fallback (<90% accuracy) | `claude-haiku-4-5` | ~560đ |
| ClaudeSonnetProvider | complex / handwritten | `claude-sonnet-4-6` | ~1,693đ |
| `remap_type()` | text-only remap (#258) | `gemini-2.5-flash` (text) | ~2-3đ |

> **Cost note:** 177đ measured on staging (vs 59đ on H_MB_6 local). Issue #248
> filed `for:pm` to ratify canonical figure for docs. `remap_type()` uses
> provider tag `gemini_flash_text` for cost tracking (#255).

## Done (Sprint 1 — #230 anchors, #258 remap, #268 analysis)

### PR #232 → staging (merged, QC sign-off ✓)
- [x] `AnchoredField(ExtractedField)` — `page_num` (1-based int) + `ref` (clause label).
      Gemini Full schema only; Claude lean stays anchor-free (grammar guard).
- [x] `_ANCHOR_SPEC` prompt rewrite — mandatory + example-driven (11 lines). Live-validated:
      7/8 valued fields populated by Gemini (`page_num=7/12`, `ref=5/12`).
- [x] `anchor_probe.py` — isolated #230 validator. Calls provider directly (no HTTP/auth/DB).
      Per-field table, exit code 0/1 as gate. Provider-conditional expectations.
- [x] Smoke scripts (`smoke_e2e_staging.py` + `.sh`) — `/api/` prefix fix, anchor gate
      softened to warning (deployed vs not-deployed ambiguity).
- [x] Post-deploy integration smoke: 12/12 steps green, `anchored(page_num)=7 with_ref=5`.

### Issue #258 — clause remap (KHE_AI scope shipped)
- [x] `remap.py` — `async remap_type(clauses, target_type) -> RemapResult`.
      Text-only Gemini Flash call (~2-3đ vs ~177đ vision). No quota, no file needed.
- [x] PM-ratified output: `RemapResult(fields, provider, cost_vnd, warnings)`,
      `RemapFieldResult(value, ref, page_num=None, confidence, needs_review)`.
- [x] `_to_remap_result()` — row for EVERY target key (D-07), drops invented keys,
      `page_num` always None (honest, text-only), confidence clamped.
- [x] No-op guards: empty clauses → `no_clauses`; no type-specific fields → `no_type_specific_fields_for_target`.
- [x] `build_remap_instruction()` — lists only target's fields from `TYPE_SPECIFIC_FIELDS`.
- [x] LLM schema: `_RemapExtractionLLM` with `list[_RemapFieldLLM]` — lean, Gemini-safe.
- [x] 9 unit tests (`test_remap.py`); all passing.
- [x] Public API exported: `remap_type`, `RemapResult`, `RemapFieldResult` in `__init__.py`.
- [x] Full #258 stack deployed to staging (Backend endpoint + KHE_AI + FE UI all merged).

### Issue #268 — chat D-08 false-negatives (analysis posted, not AI scope)
- [x] Root-cause analysis posted on #268:
      Q2 = SQLite `lower()` ASCII-only on Vietnamese diacritics (unicode-lower bug pattern).
      Q3 = tool-selection (model picks wrong tool for query type).
- [x] Not KHE_AI scope — Backend chat router owns the fix.

### DOCS_INBOX posts (×4)
- [x] AnchoredField schema + prompt (PR #232)
- [x] Cost figure (177đ staging vs 59đ local — issue #248 filed `for:pm`)
- [x] Provider/model field on DocumentDetailOut (#233/#235)
- [x] Remap module (#258 — new `remap.py`, output contract, provider tag)

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
- **Haiku-text benchmark for remap (#258 Q2):** PM ratified Gemini Flash text as
  default remap provider. Benchmark Haiku-text alternative post-ship. Needs PII-scrubbed
  samples with clauses. Unblocked but not yet run.
- **Issue #248 — cost figure ratification:** 177đ (staging) vs 59đ (local H_MB_6).
  Awaiting PM decision on canonical cost figure for docs. `for:pm` label.
- **Post-remap E2E smoke on staging:** Full #258 stack deployed but the remap endpoint
  path specifically not yet E2E-tested via smoke.
- **Key rotation:** Gemini + Claude API keys used in local testing should be rotated.
- **Live benchmark numbers (full 15-sample run)** — needs:
  1. 15 HĐ thật F&B/bán lẻ (PM decision 2026-06-11: **không dùng synthetic**, chờ
     bộ thật để số liệu có giá trị quyết định).
  2. PII scrub trước khi đưa vào fixtures (NĐ 13/2023).
  → `blocker:waiting-dependency` (samples).
- **Long PDFs (>~100 trang, >~32MB)** — file FIDIC 193pp/18.8MB vượt Claude inline
  + Gemini inline limit. Cần File API path (deferred; F&B SME contracts thường ngắn
  → low priority).

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

## Next (for incoming session)
- **Haiku-text remap benchmark** — compare Gemini Flash text vs Claude Haiku text on
  remap accuracy + cost. Needs PII-scrubbed samples with populated clauses[].
- **Post-remap staging smoke** — hit `POST /documents/{id}/remap-type` end-to-end on
  staging (upload → extract → remap to different type → verify new terms).
- **Rotate local API keys** used during anchor_probe + remap testing.
- **Issue #248 follow-up** — once PM ratifies cost figure, fold into docs (or post
  DOCS_INBOX for docs-editor).
- **15-sample benchmark** — still blocked on real HĐ samples + PII scrub.

## Env / secrets (relay KHE_Infra, 2026-06-11)
- GitHub Actions secrets set in repo: **`GEMINI_API_KEY`** (primary) and
  **`CLAUDE_API_KEY`** (fallback). Injected at runtime via deploy-main/staging.yml.
- Code reads `os.environ["GEMINI_API_KEY"]` / `os.environ["CLAUDE_API_KEY"]`
  (Claude provider falls back to `ANTHROPIC_API_KEY` for local/SDK default). Never log/hardcode.
- Local dev: add both to `backend/.env.local` (gitignored).

## Done (issue #445 — WS1-AI, parent #443 mini-sprint)
- [x] `max_output_tokens=65_536` set explicitly (model max) in both
      `gemini_flash.py` (`GeminiFlashProvider.extract`) and `hybrid_ocr.py`
      (`HybridOCRProvider._llm_extract`) — was previously unset (SDK implicit
      default), root cause of silent truncation on large docs (#442, doc #20).
- [x] `finish_reason()` helper added to `providers/base.py` — reads
      `response.candidates[0].finish_reason` off the google-genai response.
- [x] Both providers now `logger.info` per extraction call: `input_tokens`,
      `output_tokens` (`candidates_token_count`), `max_output_tokens`,
      `finish_reason`, `latency_ms` — builds the empirical corpus WS2
      (two-pass map-reduce, #448) needs for batch-sizing.
- [ ] **Not done in this pass:** WS1's `MAX_TOKENS` trap (`is_error=True`,
      no provider-advance) — that's the Backend half of WS1, coordinate via #443.
- [x] **Rebased branch onto `origin/staging`** (was stale off `main` — staging had
      ~20 commits ahead incl. PR #425 AI Phụ lục prompt fix for #439 and PR #441
      Backend hierarchy fix). Resolved 1 merge conflict in `hybrid_ocr.py`
      (`_response_diagnostic` tuple return vs my logging line — kept both).
- Unit tests: `test_extraction.py` 54/55 pass post-rebase (1 pre-existing unrelated
  failure, `test_canonical_fields_v2_expanded` — count assertion stale vs actual
  `CANONICAL_FIELDS` len, predates this change, confirmed via `git stash` both
  pre- and post-rebase).

## Coordination flag — #443 tracker discrepancy (2026-07-02)
- #443's tracker comment claimed PR #441 "bundles WS0 [#444 ocr-text download] +
  WS3-backend [#439/#440 hierarchy]" and #450 (AI relay) claimed
  `ExtractionResult.ocr_text` was "already on ExtractionResult (added in Backend
  PR #441)". **Verified false on staging**: merged PR #441 (`9a7d427`, branch
  `claude/fix-phu-luc-hierarchy-440`) only touches `clause_hierarchy.py` +
  `extraction_runner.py` (+tests) for #439/#440. No `ocr_text` field, no runner
  persistence, no `GET /documents/{id}/ocr-text` route anywhere on staging.
  No open PR has this either (checked `list_pull_requests`).
- **Did NOT implement #450's one-liner** — adding `ocr_text=ocr_text` to
  `HybridOCRProvider.extract()`'s result construction would require guessing the
  field's shape on `ExtractionResult` (schemas.py) since it doesn't exist yet.
  Commented on #450 + #443 flagging the gap; waiting on actual WS0 PR before
  wiring the one-liner.
- #439 AI-half (Phụ lục `PL-` prompt rules) **confirmed already merged** via PR
  #425 — no new prompt work needed there. Still need to re-check whether the
  original #439 bug (bare "Khoản N" under Phụ lục colliding with Điều N) is
  fully closed by #425 + #441 combined, or if a residual gap remains, before
  starting #448 (blocked on #439).

## Inbox
- issue #3 (`for:ai`, `task-assignment`) — Sprint 0 benchmark. Status: implementation
  done; awaiting live run for results (blocked on samples).
- relay KHE_Infra (2026-06-11) — secret names confirmed; provider key lookup aligned to `CLAUDE_API_KEY`.
- issue #53 (`for:ai`, `from:backend`, `task-assignment`) — export `get_extraction_provider()`
  factory for #25 PR-B. Status: **done**.
- issue #258 — clause remap. Status: **done** (KHE_AI scope shipped, full stack on staging).
- issue #248 — cost figure ratification. Status: **awaiting PM** (`for:pm`).
- issue #268 — chat D-08 false-negatives. Status: **analysis posted** (not AI scope).
- issue #445 (`for:ai`, WS1-AI, parent #443) — max_output_tokens + instrumentation. Status: **done**, this PR.
- issue #439 (Phụ lục sub-clause `clause_path`, Part 1 prompt fix) — **next up**.
- issue #448 (two-pass map-reduce prompts) — blocked on #439 + WS3 (Backend Phụ lục hierarchy parse).
