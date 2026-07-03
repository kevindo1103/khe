# Khế — PROJECT_PLAN v0.1

> Milestone roadmap. Source: BRD §13. Sprint cadence drives session work assignment.

---

## Document control

| Mục | Nội dung |
|---|---|
| Phiên bản | v0.7 |
| Trạng thái | Fold cycle 7 — DEC-055 Servanda tier + DEC-056 Obligation OS + Design System v1.1 + ~15 impl entries |
| Owner | KHE_Docs |
| Source | BRD v0.10 §13 milestones (upstream: `PRODUCT_STRATEGY_Khe_v0.2.md` §5c/§5d/§10) |

---

## Changelog

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| v0.1 | 2026-06-11 | KHE_Docs | Initial. Fold PM_Assistant draft (entry 3) + Strategy v2 milestones (entry 4: M-1 concierge, 2-firm pilot). Mark Sprint 0 ✅ COMPLETE per backend #19 + infra #21. |
| v0.2 | 2026-06-18 | KHE_Docs | Add cascade reference to upstream `PRODUCT_STRATEGY_Khe_v0.2.md` §10 (3 giai-đoạn + kill signals canonical). Add DEC-018 (Vertical OPEN) to Open Decisions. No milestone changes. |
| v0.3 | 2026-06-19 | KHE_Docs | Cycle 3 fold. Sprint 1 backlog adds: FR-TN-01..03 quota guard (Backend) + #26 obligation engine + reminder scheduler. M0 vertical slice marked staging-complete (Backend PR #54 ingest + PR #59 relationships + PR #60 extraction worker). Sprint 0 infra final ✅ (Infra PR #48: domain khe.iceflow.cloud + migrate_all_tenants + CORS). Open decisions: domain confirmed (khe.iceflow.cloud), DEC-016 still open, DEC-018 wedge selection post-pilot, FR-TN policy ratified cycle 3. |
| v0.7 | 2026-07-03 | KHE_Docs | **Cycle 7 fold — DEC-055 + DEC-056 + DS v1.1 + impl entries.** Decision log +DEC-055 (Servanda + Ledger/AI tier + D-16) + DEC-056 (Obligation OS + D-17) + DS v1.1 (2026-07-03 supersedes v1.0). Sprint 5 pilot backlog partial done (bulk endpoint PR #475 + obligation tab reorg FE #476). NEW Sprint 6+ DEC-056 rule pack pilot planning (1 firm đại lý thuế, thuế + BHXH cơ bản). Numbering conflicts resolved: PM D-11/D-12 → D-16/D-17 canonical. |
| v0.6 | 2026-06-29 | KHE_Docs | **Cycle 6 fold — EPIC #362 (DEC-050) production promote PR #402 2026-06-29.** 11/13 R1-R10 shipped (R4b ingest-split + Nhóm B metadata deferred). DEC-049 hybrid OCR (KHE_AI PR #341 — staging, opt-in, default policy chờ Kevin). Sprint 2 EPIC #397 filed: P0 staging→main promote chain + DEC-002 revision · P1 obligation/rights reorg + compliance #105 + relationship UI #398 · P2 R4b + Nhóm B #399 · P3 signature/image pipeline. Decision log +DEC-049/050. Pilot tenant `tran-thai-cam-ranh` continues. 5 layer commits this cycle (BRD v0.9 + SRS v0.6 + Glossary v0.7 + CLAUDE.md v0.10 + this PROJECT_PLAN). |
| v0.5 | 2026-06-27 | KHE_Docs | **Cycle 5 fold — EPIC #300 production promote `ce48bbd` 2026-06-27.** Pilot tenant `tran-thai-cam-ranh` live (issue #336). DEC-048 RATIFIED (Obligation Fulfillment + Dependency Chain). 6 layer commits (BRD v0.8 + SRS v0.5 + Glossary v0.6 + CLAUDE.md v0.9 + USER_MANUAL_PILOT_v0.1.md + this PROJECT_PLAN). Sprint 5 backlog filed: KHE_AI LLM re-extraction path cho POST /reread v2, Document.provider column ratify (clause-gap), open_ended recurrence Sprint 6+. |
| v0.4 | 2026-06-20 | KHE_Docs | **Cycle 4 fold (16 entries).** Sprint 1 → 🟢 STAGING-COMPLETE: obligation engine (PR #64) + reminder service (PR #66) + chat (PR #68/#104/#115/#125/#132) + admin chat (PR #133) + clauses populate (PR #108) + extraction schema v2 (PR #135 + #140 + #141) + party roles (PR #142). M0 core loop verified 2026-06-19. Decision log: DEC-025 (PWA standalone Vite + Option A nginx routing), DEC-027 (obligation_type 8 categories), DEC-028 (chat learning + compliance debt), DEC-029 (doc_type_group taxonomy + schema v2), DEC-030 (direction/Quyền lợi/legal_name). Sprint 2 backlog filed: re-extraction script, Document.provider column ratify, monthly recurrence expansion, NĐ 13 chat consent close pre-prod, CONTRACT_LOGIC_Khe.md skeleton (lawyer-partner kickoff). |

---

## Sprint 0 — Infrastructure bootstrap ✅ COMPLETE

**Goal:** Unblock all feature sessions. Ran in parallel with M-1 prep.

**Status:** ✅ COMPLETE (2026-06-11). Backend #19 + Infra #21 + AI #17 all on `main`.

Tasks:
- [x] FastAPI + multi-tenant DB scaffold (KHE_Backend issue #2 — PR #19 merged `cf6d022`)
- [x] CI/CD skeleton: `pr-quality-gate.yml`, `deploy-staging.yml`, `deploy-main.yml` (KHE_Infra PRs #7/#8/#13/#18/#21)
- [x] VisionExtractionProvider Sprint 0 — Gemini 2.5 Flash + Claude Haiku/Sonnet (KHE_AI #17)
- [ ] Telegram bot wired: bot token, `send_message` utility — **Sprint 1 carry-over** (env vars provisioned, code Sprint 1)
- [x] OCR + LLM provider decided (DEC-002 ratified)
- [x] Hosting + domain + SSL — VPS provisioned + TLS live via certbot (Infra PR #48): `khe.iceflow.cloud` (prod) + `staging.khe.iceflow.cloud` (staging); DNS A → `14.225.212.116`; CORS_ORIGINS injected; `migrate_all_tenants.py` wired post-alembic
- [ ] 2 firm design-partner LOI signed — **M-1 prep, user action ongoing** (DEC-013, thay 1-firm cũ)

**Exit criteria met:**
- ✅ `python -c "import main"` passes (Sprint 0 import guard)
- ✅ `GET /health` returns 200
- ✅ CI runs on PR (pr-quality-gate enforced)
- ✅ Deploy pipeline `staging` + `main` operational

---

## M-1 — Concierge baseline (DEC-012/013, ~2 weeks)

**Goal:** 2 firm pilot signed (1 đại lý thuế + 1 law firm) + 20 SME concierge baseline kho.

Tasks:
- [ ] 2 firm LOI signed (user action — DEC-013)
- [ ] Concierge SOP draft (Khế đội + firm partner workflow)
- [ ] 20 SME tenant provisioned trong `master.db`
- [ ] Số hóa tận nơi 20 kho doc baseline → upload batch → tenant kho ready

Exit criteria:
- 2 firm partner accounts live, billing setup
- 20 SME tenant có ≥10 doc baseline mỗi tenant
- 0 SME bị block bởi ma sát upload

---

## M0 — Vertical slice (~2 weeks, Sprint 1) — 🟢 STAGING-VERIFIED 2026-06-19

**Goal:** End-to-end qua 1 real document — chứng minh value loop.

Flow: Upload PDF → vision extract → derive `ngay_het_han` (xem SRS §6.1) → store Obligation → send Telegram reminder → answer 1 chat query.

Doc type: HĐ thuê mặt bằng (Backend M0 contract `hd_thue_mat_bang` — highest SME frequency).

**Status update (cycle 4, 2026-06-20):** Full M0 vertical slice live trên `staging` + PM manual verification 2026-06-19:
- [x] `POST /ingest/upload` + `/ingest/bulk` (Backend PR #54)
- [x] `get_extraction_provider()` factory (KHE_AI PR #58, staging)
- [x] BG task `run_extraction` populate Terms + `extraction_performed` audit Event với `consent_reference` (Backend PR #60)
- [x] Dynamic field iteration + `payment_schedule` → payment Obligation (Backend PR #141, DEC-027)
- [x] Extraction schema v2: doc_type_group + 12 universal + 9 type-specific + parties + clauses (KHE_AI PR #135 + #140 + #142, DEC-029/030)
- [x] `GET /documents/{id}/relationships` + PATCH với `last_writer_wins` chain (Backend PR #59)
- [x] Obligation engine FR-OB-01 derivation + chain-aware terminal attach (Backend PR #64, closes #26)
- [x] Telegram reminder service + APScheduler 08:00 ICT daily sweep + per-tenant routing (Backend PR #66, DEC-025)
- [x] Chat `POST /chat/query` LLM function-calling 3 tools + D-08 hard fallback (Backend PR #68/#104/#115/#125/#132, DEC-026)
- [x] Admin chat UI `/admin/chat` (FE PR #133); PWA chat shell (FE PR #44)
- [x] HttpOnly cookie auth — Bearer retired (Backend PR #46 + FE PR #91)
- [x] DEC-025 routing locked: Admin `/` + PWA `/pwa/` (FE PR #95 Option A)
- [x] PM milestone confirm 2026-06-19: HĐ thật `hd_nha_cung_cap` → 7 fields → D-08 honored (`ngay_het_han=null + needs_review=true`) → `obligation_count=1`
- [ ] DEC-030 Backend wiring (#145): `recurrence` rename migration + `direction`/`obligor` + `legal_name` auto-match
- [ ] DEC-030 Frontend (#146): Nghĩa vụ / Quyền lợi tabs + self-party confirm UI
- [ ] Promote `staging → main` batch (gom #135+#140+#141+#142+#145 sau khi #145 ship)

Exit criteria:
- 1 real lease contract uploaded, Term bóc đúng + `ngay_het_han` derived
- Obligation stored, reminder scheduled
- Telegram message received by test user
- Chat query "hợp đồng này hết hạn khi nào?" trả lời đúng
- No manual DB edits end-to-end
- Promoted to `main`

---

## Sprint 1 backlog — 🟢 STAGING-COMPLETE (2026-06-20)

**Goal:** Complete M0 vertical slice + harden quota guard. *(Status updated cycle 4.)*

Done on staging:
- [x] **FR-TN-01..03 Quota guard** — pre-ingest 429 hard block; APScheduler monthly reset; D-11 enforcement
- [x] **#26 Obligation engine + Telegram reminder** (Backend PR #64 + #66) — chain-aware derivation + daily 08:00 ICT sweep + per-tenant routing (DEC-025)
- [x] **#27 Chat query interface** (Backend PR #68 + #104) — FR-CQ-01..06 with LLM function-calling
- [x] **Per-tenant Alembic migration loop** (`migrate_all_tenants.py` wired Infra PR #48)
- [x] **#61 chain invariant** — closes via PR #64 obligation engine

## Sprint 2-4 (M0/M1 complete + DEC-030/031 wiring) — 🟢 PRODUCTION

**Status:** All Sprint 2 tasks shipped to production via EPIC #300 promote (PR #335 `ce48bbd` 2026-06-27). DEC-030 + DEC-048 wired. Pilot tenant live.

- [x] #145 DEC-030 Backend wiring (tenant_005 migration + tenant_profile + legal_name auto-match)
- [x] #146 DEC-030 Frontend (Nghĩa vụ / Quyền lợi tabs + self-party confirm Settings page PR #174)
- [x] Re-extraction wired qua extraction runner upgrade (DOC_TYPE_GROUPS + parties + clauses)
- [x] VPS timezone — Asia/Ho_Chi_Minh confirmed
- [ ] **`Document.provider` column** — still open (clause-gap rationale)
- [ ] **NĐ 13 chat learning consent gate (#119)** — DEC-028 compliance debt vẫn chưa close, COMPLIANCE BLOCKER trước full prod
- [ ] **Monthly/quarterly recurrence expansion** — Sprint 6 carry-over
- [ ] **CONTRACT_LOGIC_Khe.md (issue #147)** — Lawyer partner kickoff Sprint 6 (deferred)

## EPIC #300 — Production live (2026-06-27)

**Promote:** PR #335 `staging` → `main` merged `ce48bbd`. Tenant pilot `tran-thai-cam-ranh` (Công ty Cổ phần Trần Thái Cam Ranh) provisioned issue #336.

**Scope live:**
- DEC-048 Obligation Fulfillment + Dependency Chain (FR-OB-09..13)
- Clause edit + AI re-read flow (§13 addendum, FR-EX-09)
- Evidence document support (FR-IN-05, `is_evidence` skip-extraction)
- Date-anchored obligation resolver (FR-OB-13, `waiting_trigger` → `pending`)
- Provenance: `source_clause_num` + `derived_from` per obligation (Kevin Option B 0a)
- Cascade chain anchor G1 fix: `parent.fulfilled_at` NOT `date.today()`
- Cascade-past → `awaiting_confirmation` D-02 (NOT auto-overdue)
- P1 source-aware merge + derive delete path-2 guard (PR #311)
- Audit events expansion: `obligation_fulfilled`, `cascade_triggered`, `clause_edited` (PII-safe), `evidence_attached`, etc.
- User manual `docs/USER_MANUAL_PILOT_v0.1.md` published cho SME pilot onboarding

## EPIC #362 (DEC-050) — Production live (2026-06-29)

**Promote:** PR #402 `staging` → `main`. 11/13 R1-R10 shipped. Builds on top of EPIC #300 (DEC-048).

**Scope live:**
- R1 contract title + contract_number denormalized + PATCH endpoint D-07 (PR #379)
- R2 party details: address, representative, tax_code, is_self, aliases (PR #383)
- R3 clause hierarchy: parent_id, level, clause_path (PR #384)
- R4 annex relationship type (3-value enum, PR #385). **R4b deferred** — ingest-split multi-doc per file
- R5a markdown tables trong clause content (FE PR #396)
- R5b signature flags + badge UI (Backend PR #400 + FE PR #401)
- R6 date taxonomy: signing_date + commencement_date denormalized (PR #386)
- R7 auto-renewal Obligation (in PR cluster)
- R8 lifecycle_status 5-state enum (PR #388, FE PR designer mockup v3)
- R9 definitions table CRUD (PR #389)
- R10 cross-reference resolution + orphan detection (Backend PR #392 + FE PR #395)
- AI schema v3 R1-R10 (PR #381)

**Deferred:**
- R4b ingest-split flow → Sprint 2 EPIC #397
- Nhóm B metadata (governing law, currency, bilingual, orphan-attachment) → issue #399 Sprint 2+

## Sprint 5 backlog — Pilot hardening (2026-06-27 →) — partial done

**Goal:** Pilot tenant `tran-thai-cam-ranh` actively used. Lawyer partner kickoff. Compliance debt close.

Tasks:
- [x] EPIC #362 production promote (PR #402 2026-06-29)
- [ ] **KHE_AI LLM re-extraction path cho `POST /reread` v2** — v1 derives từ existing Terms only; v2 cần LLM call trên edited clause content
- [ ] **`Document.provider` column ratify** (carry-over) — phân biệt Claude vs Gemini path, enable re-extract-prefer-Gemini cho clause-gap
- [ ] **NĐ 13 chat learning consent gate (#119)** (carry-over BLOCKER) — explicit consent flow for query logging trước prod scale-out
- [ ] **Pilot feedback loop** — Issue #336 hub cho `tran-thai-cam-ranh` feedback collection
- [ ] **CONTRACT_LOGIC_Khe.md (#147)** — Lawyer kickoff Sprint 5/6
- [ ] **Open observability items:** VPS timezone re-verify post-promote; inverted-range guard `due_from > due_to` (FR-CQ-02); Vietnamese accent-folding for chat NOT_FOUND patterns
- [ ] **2-firm pilot expansion (DEC-013)** — second firm sign + 10 SME each, 90-day evaluation per Kill Signals K-1..K-3
- [x] **Bulk complete + obligation reorg** (cycle 7 shipped) — Backend PR #475 (PATCH /obligations/bulk + penalty enum tenant_030) + FE PR #476 (3-axis IA reorg per DEC-055)
- [ ] **D-02 readback modal for bulk complete** — Kevin/QC decision pre-prod (flagged in FE PR #476)
- [ ] **KHE_AI `Party.aliases` LLM schema fold** — root cause block for D-13 alias-match (PR #475 gap). Filed relay for KHE_AI.
- [ ] **CompletenessVerifier LLM impl** — populate `may_have_unextracted_obligations` (schema wired PR #492, verifier fast-follow). D-03 honest completeness.
- [ ] **Two-pass metadata recovery** (issue #464) — extend PR #463 auto-two-pass to also recover fields/parties/obligations/definitions/cross_refs/signature. Current: clauses-only.

## Sprint 6 backlog — DEC-056 Obligation OS validation (post-Sprint 5)

**Goal:** Validate compliance-as-source-2 thesis cheap. NO Sprint push-in per §5c.6.

Tasks:
- [ ] **DEC-056 pilot rule pack v1** — với 1 đại lý thuế (DEC-013 existing pilot firm): thuế GTGT + BHXH cơ bản theo loại hình DN. Structured rule pack format finalize (schema TBD).
- [ ] **`Obligation.document_id` nullable** or NEW **`compliance_dossier` container entity** — Backend BA khi rule pack v1 stable
- [ ] **Rule engine expander** — lịch luật định ("ngày 20 tháng sau", "quý +30 ngày", dời ngày nghỉ lễ)
- [ ] **Firm portfolio view** — DEC-056 §5c.4 gap (b): firm sees compliance obligations across all their SME clients in 1 place
- [ ] **Kill signal check DEC-056** — firm không dùng rule pack v1 sau 30 ngày → thesis chết sớm, save effort
- [ ] **DEC-016 pricing pin-down** — sử dụng DEC-055 tier shape đã có + rule pack tier positioning (Ledger free hay AI-adjacent paid?)

## Sprint 2 backlog — EPIC #397 (PM filed 2026-06-29)

**Goal:** post-pilot consolidation. 4 priority tiers.

**P0 — Foundations:**
- [ ] Staging → main promote chain audit (verify EPIC #362 fully propagated)
- [ ] DEC-002 revision — cost model refresh with cycle 6 data (hybrid_ocr + DEC-050 schema v3 actual cost-per-doc)

**P1 — Critical path:**
- [ ] Obligation / Rights reorganization (#274/#275/#276/#277 — status check pending Backend)
- [ ] Compliance #105 NĐ 13 chat learning consent close (BLOCKER pre full prod, DEC-028 debt)
- [ ] Document Relationship Link UI (#398) — frontend surface cho existing headless API
- [ ] DEC-049 hybrid_ocr routing policy ratify (default vs opt-in)

**P2 — Extraction depth completion:**
- [ ] R4b ingest-split flow — multi-doc trong 1 file → N linked Documents (classify phụ lục loại A vs B)
- [ ] Nhóm B metadata BA (#399) — governing law / currency / bilingual / orphan-attachment

**P3 — Future:**
- [ ] Signature / image pipeline expansion
- [ ] CONTRACT_LOGIC_Khe.md lawyer-partner doc kickoff (#147)

## Decision log

| ID | Date | Decision | Source |
|---|---|---|---|
| DEC-025 | 2026-06-19 | PWA standalone Vite project (`frontend/pwa/**`), separate from Admin. Nginx routing Option A: Admin `/` + PWA `/pwa/`. | PM ratify FE PR #95 |
| DEC-026 | 2026-06-19 | Chat LLM function-calling (Gemini Flash) + 3 tools + `clauses` table; D-08 hard fallback exact string. 2-tier schema (Claude lean / Gemini full) addendum. | Kevin ratify issue #100 |
| DEC-027 | 2026-06-19 | Generalized typed obligation extraction — `obligation_type` enum 8 categories. `other` catch-all (D-08). | PM #116/#117 |
| DEC-028 | 2026-06-19 | Chat query learning loop (log → weekly review → catalog #118). 🔴 NĐ 13 compliance debt pre-prod. | PM #118/#119 |
| DEC-029 | 2026-06-20 | `doc_type_group` taxonomy 11 (collapse từ 126 loại) + CANONICAL_FIELDS 7 → 12 + 9 type-specific field sets + `doc_type_filter` chat param. | Kevin ratify |
| DEC-030 | 2026-06-20 | Obligation `direction` (`nghĩa_vụ`/`quyền_lợi`/null) + `obligor` + self-party `legal_name` auto-match. `obligation_type` axis #122 resolved via Option B (cadence → `recurrence`). | Kevin ratify |
| DEC-031 | 2026-06-20 | Chat architecture v2 — Result-seeded Progressive State (structured state JSON, NOT prose history). Scope chip mandatory, ambiguity ask-clarify, 30-min invalidation. | Kevin ratify |
| DEC-047 | 2026-06-20 | PR Scope-Lock Enforcement — PR chỉ chứa files trong session lane; cross-lane = file issue. Trigger: PR #288 incident. | PM operational |
| DEC-048 | 2026-06-27 | Obligation Fulfillment + Dependency Chain (EPIC #300 production `ce48bbd`). `fulfilled_at` G1 anchor (NOT date.today()), `awaiting_confirmation` status cascade-past D-02. `source_clause_num` provenance (Kevin Option B 0a). `is_evidence` skip-extraction P2. ClauseEditEvent + re-read flow §13 addendum. P1 source-aware merge guard + derive delete path-2 (PR #311 V1). Date-anchored resolver (FR-OB-13). | Kevin ratify |
| DEC-049 | 2026-06-27 | Hybrid OCR pipeline (KHE_AI PR #341 staging). 2-pass: scan_detect → Document AI/pdftotext → Gemini text-mode. 4th provider trong factory `_REGISTRY`. System dep VPS `poppler-utils` + `GOOGLE_APPLICATION_CREDENTIALS` gate. Routing default policy (auto vs opt-in) **OPEN**. | Kevin ratify decision; routing default open |
| DEC-055 | 2026-07-02 | **Servanda brand** (R-7 resolved) + **Ledger/AI 2-tier structure** (Ledger free với full core loop + AI paid với per-doc quota) + **D-16 no-paywall-safety** (renumbered from PM D-11 collision). Design System "Sổ cái" v1.0 companion (upgraded → v1.1 2026-07-03). | Kevin ratify |
| DEC-056 | 2026-07-03 | **Obligation OS North Star** — compliance obligations (thuế/BHXH/ngành dọc) = source 2. Engine treats obligation-source-agnostic (P-6 BRD). Rule pack curated (NO AI reads laws). **D-17 firm-confirms-compliance** (renumbered from PM D-12 collision). DEC-018 wedge candidate: wedge = obligation TYPE not vertical. | Kevin ratify |
| DS v1.1 | 2026-07-03 | Design System "Sổ cái" v1.1 supersedes v1.0. Measured contrast (WCAG 2.1 formula). +`border-strong #7E8983` token (WCAG 3:1). Hợp đồng A11y binding. 4 ratified components. Elevation e0-e3. Lục Khế `#1E5C49` primary + Be Vietnam Pro + Source Serif 4 fonts self-host. | Kevin ratify |
| DEC-050 | 2026-06-28 | Contract Extraction & Display Depth — 10 requirements (R1-R10): R1 title+number, R2 party details, R3 clause hierarchy, R4 annex relationship + ingest-split (R4a only; R4b defer), R5 table/signature, R6 date taxonomy, R7 auto-renewal, R8 lifecycle status enum 5-state, R9 definitions glossary, R10 cross-references. 8 tenant migrations (`tenant_021..028`) + 2 NEW entities (Definition, CrossReference). EPIC #362 production PR #402 2026-06-29 (11/13 shipped). | Kevin ratify |

---

## M1 — 3 doc types + self-serve (~3 weeks, Sprint 2)

**Goal:** SME tự onboard và dùng không cần guide (sau concierge baseline).

Doc types: HĐ thuê mặt bằng + HĐ nhà cung cấp + HĐ lao động.

Features: Search + filter, edit extracted term, event ledger visible, multi-user tenant.

Exit criteria:
- All 3 doc types ingestible với ≥80% extraction accuracy
- SME user signup, upload, find, set reminder không cần support
- Edit term → Event logged
- 60% SME upload ≥3 docs post-concierge (M-1 BRD metric)

---

## M2 — Firm portal (~2 weeks, Sprint 3)

**Goal:** 2 firm pilot dùng read-only view + lead signals.

Features: Firm partner login, cross-tenant read (consent), obligation signal feed, consent grant/revoke flow.

Exit criteria:
- 2 firm partner accounts live
- Firm thấy SME's upcoming obligations (consent granted)
- SME revoke consent → firm access blocked ngay
- NĐ 13/2023 consent log ghi mọi access
- 90-day pilot evaluation milestone (Kill signals K-1..K-3 measurable)

---

## M3 — Harden + launch (~2 weeks, Sprint 4)

**Goal:** Production-ready public launch.

Tasks: Reminder reliability ≥99%, security audit, NĐ 13/2023 compliance sign-off, performance baseline, naming finalized (R-7).

Exit criteria:
- 30-day reminder delivery rate ≥99% on staging
- Security review: no P0/P1 findings open
- KHE_Compliance sign-off NĐ 13/2023 + NĐ 337/2025 + NĐ 70/2025
- Public domain live, SSL, monitoring alerts configured
- Naming "Khế" finalized (R-7)

---

## Strategy v2 roadmap (DEC-014 / §3.8 BRD)

| Giai đoạn | Thời gian | Trọng tâm | Revenue |
|---|---|---|---|
| **GĐ1 — Troy + Concierge** | Q3-Q4 2026 (current) | M-1 → M3 above | Firm trả per-client |
| **GĐ2 — Lawyer-in-loop drafting/review** | 2027 | Template + review pháp lý | SME-pays + firm rev share |
| **GĐ3 — Obligation graph hạ tầng** | 2027+ | Tích hợp công nợ / hóa đơn ĐT / ngân hàng | Platform fee + integration |

---

## Kill / Pivot signals (DEC-015 — measured M2 90-day mark)

| Signal | Trigger | Pivot |
|---|---|---|
| K-1 | W4 retention SME < 30% post-concierge | DMS B2B cho firm nhỏ |
| K-2 | Firm không trả + SME convert tốt | Direct freemium SME-first |
| K-3 | 2 firm không kéo nổi 10 SME/90 ngày | Đổi kênh hiệp hội / F&B community |

---

## Open decisions

| ID | Item | Owner |
|---|---|---|
| DEC-016 | Freemium paywall lever (conflicts DEC-006 Telegram) — Plan B input ~$30-100/mo self-serve | Kevin |
| DEC-018 | Vertical wedge selection — currently OPEN; chọn theo pilot signal (a/b/c criteria) | Kevin (post-pilot) |
| FR-TN policy | Default firm-configurable per SME / calendar-month reset / hard block 429 — **ratified cycle 3 2026-06-19** | ✅ closed |
| Domain | `khe.iceflow.cloud` (prod) + `staging.khe.iceflow.cloud` — **confirmed Infra PR #48** | ✅ closed |
| DEC-025/026/027/028/029/030 | All ratified Kevin 2026-06-19/20 — folded cycle 4 | ✅ closed |
| `Document.provider` column | Distinguish Claude vs Gemini-extracted (clause-gap rationale) — PM proposal #143 | Kevin |
| `thoi_han_hd` phi-số policy | (a) skip / (b) flag-for-human / (c) recurring — SRS §6.1 fallback unchanged | Kevin |
| R-7 naming | "Khế" placeholder — pre-launch | Kevin |
| NĐ 13 chat learning consent | DEC-028 compliance debt — explicit consent gate before prod | KHE_Compliance #119 |
| DEC-017 | Domain `khe.vn` confirm | Kevin |
| Naming R-7 | "Khế" final hoặc rename trước M3 launch | Kevin |
| Policy O-3 | `thoi_han_hd` phi-số (a/b/c) | PM |

---

*Hết v0.7 — cycle 7 fold. DEC-055 Servanda tier + DEC-056 Obligation OS + DS v1.1 ratified. Sprint 5 partial done (bulk endpoint + obligation reorg). Sprint 6 backlog filed for DEC-056 rule pack v1 pilot with existing DEC-013 firm. Next: DEC-016 pricing pin-down with tier shape resolved.*

*Hết v0.6 — cycle 6 fold. EPIC #362 (DEC-050) production live PR #402 2026-06-29. 11/13 R1-R10 shipped (R4b + Nhóm B defer Sprint 2). DEC-049 hybrid OCR staging opt-in. Sprint 2 EPIC #397 filed (4 priority tiers). Next: DEC-049 routing default ratify, Sprint 2 P0 promote audit + DEC-002 revision, NĐ 13 chat consent close.*

*Hết v0.5 — cycle 5 fold. EPIC #300 production live (`ce48bbd` 2026-06-27). Pilot tenant `tran-thai-cam-ranh` provisioned. DEC-048 ratified. USER_MANUAL_PILOT_v0.1.md published.*

*Hết v0.4 — cycle 4 fold. Sprint 1 staging-complete; Sprint 2 backlog filed (DEC-030 wiring + NĐ 13 compliance close + re-extraction + Frontend Quyền lợi UI). Next: staging→main batch promote sau khi #145 ship.*
