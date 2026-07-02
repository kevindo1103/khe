# KHE_AI — Session STATE

> Owner: **KHE_AI** (single-owner Phase 1). Scope: `backend/modules/extraction/**`,
> `docs/teams/ai_STATE.md`, `docs/benchmark_*.md` (via DOCS_INBOX).
> Branch: `claude/feat-ai-vision-extraction-3k3gup`.

_Last updated: 2026-07-02 (Cycle 6-7 — DEC-050 R1-R10 shipped, hybrid_ocr all-PDF routing, clause extraction quality 6-PR arc, Phụ lục PL- paths)_

## Decisions in force
- **DEC-002** — single `VisionExtractionProvider.extract()` interface; fallback chain.
- **DEC-010** — US-hosted APIs OK in Phase 1; log `consent_reference` to `events`.
- **DEC-049** — hybrid OCR pipeline: ALL PDFs → Document AI OCR / pdftotext → Gemini text mode.
- **DEC-050** — R1-R10 schema v3 (15 canonical + defined_terms + cross_references + signature flags).
- **D-01 / D-06** — extraction is READ-ONLY; AI never authors/edits legal content.

## Provider lineup
| Provider | Role | Model | ~Cost/doc |
|---|---|---|---|
| HybridOCRProvider | **primary for ALL PDFs** | `gemini-2.5-flash` (text mode) | ~39đ/page OCR + LLM |
| GeminiFlashProvider | images only (non-PDF) | `gemini-2.5-flash` (vision) | ~177đ |
| ClaudeHaikuProvider | fallback (<90% accuracy) | `claude-haiku-4-5` | ~560đ |
| ClaudeSonnetProvider | complex / handwritten | `claude-sonnet-4-6` | ~1,693đ |
| `remap_type()` | text-only remap (#258) | `gemini-2.5-flash` (text) | ~2-3đ |

> **Routing change (PR #414, #413):** ALL PDFs now route through `hybrid_ocr` instead of
> `gemini_flash` vision. Gemini text mode follows prompt rules (hierarchy, lettered items)
> accurately; vision mode ignores them. Factory gate changed from `GOOGLE_APPLICATION_CREDENTIALS`
> to `GEMINI_API_KEY` — pdftotext path works without DocAI creds.

## Done (Cycle 7 — clause extraction quality arc)

### PR #414 → staging (merged) — Route ALL PDFs through hybrid_ocr (#413)
- [x] `extraction_runner.py`: PDF detection → `prefer="hybrid_ocr"` instead of scan-only routing
- [x] `factory.py`: `hybrid_ocr` registry gated on Gemini key, not DocAI creds
- [x] Root cause: Gemini vision-only ignores complex prompt rules (_CLAUSES_SPEC)

### PR #419 → staging (merged) — TH-A sub-clause splitting (#416 A)
- [x] Added TH-A hierarchy examples to `_CLAUSES_SPEC` — sub-clauses (5.1, 10.1) as separate level=2
- [x] First round prompt tuning for sub-clause splitting

### PR #422 → staging (merged) — Num format + garbled pdftotext (#416 B/C, #420)
- [x] Enforced num format: TH-A level=1 → "Điều X", level=2 → "X.Y"
- [x] num↔clause_path consistency rules
- [x] `is_garbled_vietnamese()` in `scan_detect.py` — diacritical ratio < 2% → garbled → fallback to DocAI
- [x] Garble warning preserved when DocAI also fails
- [x] 5 unit tests for garble detection (`test_scan_detect.py`)

### PR #424 → staging (merged) — Restructure _CLAUSES_SPEC (#423)
- [x] Promoted sub-clause splitting to first rule (🔴 marker)
- [x] Concrete wrong-vs-right JSON output examples
- [x] Conditional self-check: "if all level=1 AND doc has sub-headings → split"
- [x] Removed contradictory example (showed sub-clause in content field)
- [x] Net -22 lines (more concise, stronger signal)

### PR #425 → staging (pending merge) — Lettered items + Phụ lục (#423, #439)
- [x] QUY TẮC 2 TOÀN VĂN: content must include ALL lettered items a-d, no truncation
- [x] QUY TẮC PHỤ LỤC: sub-clauses under Phụ lục → `clause_path="PL-X.Y"` (no collision with Điều)
- [x] Backend changes (`_stub_num`, PL- passthrough) filed as relay #440 per DEC-047

### Relay issues filed
- [x] #440 `from:ai` `for:backend` — `_stub_num()` for PL- stubs + `extraction_runner.py:291` PL- source_clause resolution

## Done (Cycle 6 — DEC-050 R1-R10 + DEC-049 hybrid OCR)

### PR #381 → staging (merged, QC reviewed) — DEC-050 R1-R10 EPIC #362
- [x] Schema v3: `ContractExtractionLLMFull` — 15 universal canonical fields + 30 type-specific
- [x] `V2_UNIVERSAL_FIELDS`: 8 new fields (tieu_de_hd, so_hop_dong, ngay_ky, ngay_khai_truong, tien_dat_coc, thoi_han_bao_hanh, thoi_han_thong_bao, doc_type_group)
- [x] R1 contract title/number, R2 parties address/representative/tax_code
- [x] R3 clause hierarchy (level/clause_path), R5b signature detection
- [x] R6 commencement date, R7 auto-renewal obligations
- [x] R8 payment schedule, R9 defined_terms[], R10 cross_references[]
- [x] Benchmarked on VPS: docs 1 + 22, all new fields populated correctly

### Infra coordination (PR #415 merged)
- [x] `GOOGLE_APPLICATION_CREDENTIALS` deployed to staging/prod systemd units
- [x] Scanned PDFs now have full Document AI OCR support

## Done (Sprint 1 — #230 anchors, #258 remap, #268 analysis)

### PR #232 → staging (merged, QC sign-off)
- [x] `AnchoredField(ExtractedField)` — `page_num` + `ref` anchors
- [x] `_ANCHOR_SPEC` prompt rewrite, smoke scripts, integration smoke

### Issue #258 — clause remap (shipped)
- [x] `remap.py` — text-only Gemini Flash call (~2-3đ), 9 unit tests

### Issue #268 — chat D-08 false-negatives (analysis posted, not AI scope)

## Done (issue #53 — provider factory)
- [x] `get_extraction_provider()` factory with fallback chain
- [x] `ExtractionUnavailable` typed error, +8 unit tests

## Done (issue #3 — Sprint 0)
- [x] Provider protocol + schemas + benchmark runner

## Blocked / pending
- **PR #425** — awaiting merge (lettered items + Phụ lục prompt rules)
- **Relay #440** — backend needs to add `_stub_num()` + PL- passthrough to `clause_hierarchy.py`
- **R4b (#367)** — sub-doc boundary detection, blocked by R4a (#366)
- **Rotate GCP service account key** — exposed in prior session, URGENT
- **Haiku-text remap benchmark** — needs PII-scrubbed samples with clauses[]
- **15-sample benchmark** — blocked on real HĐ samples + PII scrub
- **Issue #248** — cost figure ratification, awaiting PM

## _CLAUSES_SPEC evolution (prompt tuning arc)
| Round | PR | Problem | Fix |
|---|---|---|---|
| 1 | #407 | Preamble as Điều, lettered items as "Điều k/l/m" | TH-A/TH-B + QT2 lettered items |
| 2 | #411 | TH-B num=null | Explicit right/wrong examples |
| 3 | #414 | ALL PDFs vision-only (ignores rules) | Route ALL PDFs → hybrid_ocr |
| 4 | #419 | No TH-A sub-clause examples | Added 5.1/5.2 splitting example |
| 5 | #422 | num format inconsistent, garbled pdftotext | NUM FORMAT + is_garbled_vietnamese() |
| 6 | #424 | LLM still merging sub-clauses | Restructured: split rule first, 🔴 marker |
| 7 | #425 | Content truncation, Phụ lục collision | TOÀN VĂN + QUY TẮC PHỤ LỤC |

## Env / secrets
- GitHub Actions secrets: `GEMINI_API_KEY`, `CLAUDE_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`
- `hybrid_ocr` factory gated on `GEMINI_API_KEY`/`GOOGLE_API_KEY` (not DocAI creds)
- DocAI creds needed only for scanned PDFs; digital PDFs use pdftotext (free)
- Local dev: add keys to `backend/.env.local` (gitignored)

## Inbox
- issue #3 — Sprint 0 benchmark. Status: implementation done; awaiting samples.
- issue #53 — provider factory. Status: **done**.
- issue #258 — clause remap. Status: **done**.
- issue #248 — cost figure ratification. Status: **awaiting PM**.
- issue #268 — chat D-08 analysis. Status: **posted** (not AI scope).
- issue #440 — Phụ lục PL- backend relay. Status: **filed** `for:backend`.
