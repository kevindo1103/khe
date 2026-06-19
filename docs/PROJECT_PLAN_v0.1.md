# Khế — PROJECT_PLAN v0.1

> Milestone roadmap. Source: BRD §13. Sprint cadence drives session work assignment.

---

## Document control

| Mục | Nội dung |
|---|---|
| Phiên bản | v0.3 |
| Trạng thái | Fold cycle 3 — Sprint 1 backlog (quota guard) + M0 vertical slice staging-complete |
| Owner | KHE_Docs |
| Source | BRD v0.4 §13 milestones (upstream: `PRODUCT_STRATEGY_Khe_v0.2.md` §10 + §7.1 billing) |

---

## Changelog

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| v0.1 | 2026-06-11 | KHE_Docs | Initial. Fold PM_Assistant draft (entry 3) + Strategy v2 milestones (entry 4: M-1 concierge, 2-firm pilot). Mark Sprint 0 ✅ COMPLETE per backend #19 + infra #21. |
| v0.2 | 2026-06-18 | KHE_Docs | Add cascade reference to upstream `PRODUCT_STRATEGY_Khe_v0.2.md` §10 (3 giai-đoạn + kill signals canonical). Add DEC-018 (Vertical OPEN) to Open Decisions. No milestone changes. |
| v0.3 | 2026-06-19 | KHE_Docs | Cycle 3 fold. Sprint 1 backlog adds: FR-TN-01..03 quota guard (Backend) + #26 obligation engine + reminder scheduler. M0 vertical slice marked staging-complete (Backend PR #54 ingest + PR #59 relationships + PR #60 extraction worker). Sprint 0 infra final ✅ (Infra PR #48: domain khe.iceflow.cloud + migrate_all_tenants + CORS). Open decisions: domain confirmed (khe.iceflow.cloud), DEC-016 still open, DEC-018 wedge selection post-pilot, FR-TN policy ratified cycle 3. |

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

## M0 — Vertical slice (~2 weeks, Sprint 1) — 🟡 STAGING-COMPLETE

**Goal:** End-to-end qua 1 real document — chứng minh value loop.

Flow: Upload PDF → vision extract → derive `ngay_het_han` (xem SRS §6.1) → store Obligation → send Telegram reminder → answer 1 chat query.

Doc type: HĐ thuê mặt bằng (Backend M0 contract `hd_thue_mat_bang` — highest SME frequency).

**Status update (cycle 3, 2026-06-19):** Ingest + extract + relationships pipeline functionally complete trên `staging`:
- [x] `POST /ingest/upload` + `/ingest/bulk` (Backend PR #54)
- [x] `get_extraction_provider()` factory (KHE_AI PR #58, staging)
- [x] BG task `run_extraction` populate 7 CANONICAL_FIELDS + `extraction_performed` audit Event với `consent_reference` (Backend PR #60)
- [x] `GET /documents/{id}/relationships` + PATCH với `last_writer_wins` chain (Backend PR #59)
- [ ] FR-OB obligation engine — issue #26 (Sprint 1 carry-over)
- [ ] Telegram reminder wiring — Sprint 1
- [ ] Chat query interface — Sprint 1
- [ ] Promote staging → main

Exit criteria:
- 1 real lease contract uploaded, Term bóc đúng + `ngay_het_han` derived
- Obligation stored, reminder scheduled
- Telegram message received by test user
- Chat query "hợp đồng này hết hạn khi nào?" trả lời đúng
- No manual DB edits end-to-end
- Promoted to `main`

---

## Sprint 1 backlog (in-flight)

**Goal:** Complete M0 vertical slice + harden quota guard.

Tasks:
- [ ] **FR-TN-01..03 Quota guard (Backend)** — pre-ingest check 429 hard block; APScheduler monthly reset (mùng 1); firm portal usage view. `doc_quota` firm-configurable per SME (nullable=unlimited). D-11 enforcement. *(NEW cycle 3 per PM comment 22)*
- [ ] **#26 Obligation engine + Telegram reminder scheduler (Backend)** — FR-OB-01..05 + FR-RM-01..04. Carry-over M0.
- [ ] **Chat query interface** — FR-CQ-01..03 read-only.
- [ ] **Per-tenant Alembic migration loop refinement** (SRS Open Items O-1) — `migrate_all_tenants.py` wired ✅ infra; spec versioned per-tenant migrations Sprint 1.
- [ ] **Re-extraction chain invariant fix (#61)** — invalidates `is_superseded` from PR #59. Full re-resolution với #26.

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
| DEC-017 | Domain `khe.vn` confirm | Kevin |
| Naming R-7 | "Khế" final hoặc rename trước M3 launch | Kevin |
| Policy O-3 | `thoi_han_hd` phi-số (a/b/c) | PM |

---

*Hết v0.1. Update khi M-1 LOI signed hoặc Sprint 1 kicks off.*
