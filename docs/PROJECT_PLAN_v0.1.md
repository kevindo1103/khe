# Khế — PROJECT_PLAN v0.1

> Milestone roadmap. Source: BRD §13. Sprint cadence drives session work assignment.

---

## Document control

| Mục | Nội dung |
|---|---|
| Phiên bản | v0.4 |
| Trạng thái | Fold cycle 4 — Sprint 1 staging-complete (obligation+reminder+chat live) + DEC-027/028/029/030 |
| Owner | KHE_Docs |
| Source | BRD v0.6 §13 milestones (upstream: `PRODUCT_STRATEGY_Khe_v0.2.md` §10 + §7.1 billing) |

---

## Changelog

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| v0.1 | 2026-06-11 | KHE_Docs | Initial. Fold PM_Assistant draft (entry 3) + Strategy v2 milestones (entry 4: M-1 concierge, 2-firm pilot). Mark Sprint 0 ✅ COMPLETE per backend #19 + infra #21. |
| v0.2 | 2026-06-18 | KHE_Docs | Add cascade reference to upstream `PRODUCT_STRATEGY_Khe_v0.2.md` §10 (3 giai-đoạn + kill signals canonical). Add DEC-018 (Vertical OPEN) to Open Decisions. No milestone changes. |
| v0.3 | 2026-06-19 | KHE_Docs | Cycle 3 fold. Sprint 1 backlog adds: FR-TN-01..03 quota guard (Backend) + #26 obligation engine + reminder scheduler. M0 vertical slice marked staging-complete (Backend PR #54 ingest + PR #59 relationships + PR #60 extraction worker). Sprint 0 infra final ✅ (Infra PR #48: domain khe.iceflow.cloud + migrate_all_tenants + CORS). Open decisions: domain confirmed (khe.iceflow.cloud), DEC-016 still open, DEC-018 wedge selection post-pilot, FR-TN policy ratified cycle 3. |
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

## Sprint 2 backlog (in-flight, post DEC-027/028/029/030)

**Goal:** Complete DEC-030 + harden NĐ 13 compliance + Frontend Quyền lợi UI.

Tasks:
- [ ] **#145 DEC-030 Backend wiring** — `tenant_005` migration rename `obligation_type` → `recurrence` + new category column + direction + obligor + tenant_profile model + legal_name auto-match + re-derive background task
- [ ] **#146 DEC-030 Frontend** — Nghĩa vụ / Quyền lợi tabs + self-party confirm extraction review UI
- [ ] **Re-extraction script** `scripts/re_extract_all.py` — loop all tenant docs → repopulate doc_type_group + parties + clauses + obligations với new schema (post #145 promote)
- [ ] **`Document.provider` column ratify** — phân biệt Claude-extracted (empty clauses/parties) vs Gemini-extracted; enable re-extract-prefer-Gemini policy
- [ ] **NĐ 13 chat learning consent gate (#119)** — close DEC-028 compliance debt trước prod; explicit consent flow for query logging
- [ ] **Monthly/quarterly recurrence expansion** — `dieu_khoan_thanh_toan` parser + expand `payment_schedule[].recurrence != "once"` items thành múltiple Obligation rows
- [ ] **VPS timezone** — confirm `Asia/Ho_Chi_Minh` cho chat today's-date injection (Backend PR #125/#132 fast-follow)
- [ ] **CONTRACT_LOGIC_Khe.md** (issue #147) — tracking-only this sprint; lawyer-partner skeleton kickoff Sprint 3 (Kevin cycle 4 q4: defer skeleton until lawyer kickoff)

## Decision log

| ID | Date | Decision | Source |
|---|---|---|---|
| DEC-025 | 2026-06-19 | PWA standalone Vite project (`frontend/pwa/**`), separate from Admin. Nginx routing Option A: Admin `/` + PWA `/pwa/`. | PM ratify FE PR #95 |
| DEC-026 | 2026-06-19 | Chat LLM function-calling (Gemini Flash) + 3 tools + `clauses` table; D-08 hard fallback exact string. 2-tier schema (Claude lean / Gemini full) addendum. | Kevin ratify issue #100 |
| DEC-027 | 2026-06-19 | Generalized typed obligation extraction — `obligation_type` enum 8 categories. `other` catch-all (D-08). | PM #116/#117 |
| DEC-028 | 2026-06-19 | Chat query learning loop (log → weekly review → catalog #118). 🔴 NĐ 13 compliance debt pre-prod. | PM #118/#119 |
| DEC-029 | 2026-06-20 | `doc_type_group` taxonomy 11 (collapse từ 126 loại) + CANONICAL_FIELDS 7 → 12 + 9 type-specific field sets + `doc_type_filter` chat param. | Kevin ratify |
| DEC-030 | 2026-06-20 | Obligation `direction` (`nghĩa_vụ`/`quyền_lợi`/null) + `obligor` + self-party `legal_name` auto-match. `obligation_type` axis #122 resolved via Option B (cadence → `recurrence`). | Kevin ratify |

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

*Hết v0.4 — cycle 4 fold. Sprint 1 staging-complete; Sprint 2 backlog filed (DEC-030 wiring + NĐ 13 compliance close + re-extraction + Frontend Quyền lợi UI). Next: staging→main batch promote sau khi #145 ship.*
