# KHE_PM_Assistant STATE — Khế MVP

*Branch: `claude/pm-assistant` | Last updated: 2026-06-11 | v0.7*

---

## Active Sprint Context

**Current phase:** **Sprint 0 COMPLETE (2026-06-11)** — see nghiệm thu issue #23. Ready Sprint 1 kickoff.
**Sprint 0 goal (ĐÃ ĐẠT):** FastAPI + multi-tenant DB scaffold, CI/CD, Telegram bot, Vision extraction interface + 3 providers. Architecture/contract baseline ratified.
**Sprint 1 prep:** Spawn KHE_Docs (fold 11 DOCS_INBOX entries) + KHE_Frontend_Admin/PWA/QC/Compliance. Carry-over: #10 per-tenant Alembic, #22 NĐ 13 consent gate.

---

## Strategy v2 (2026-06-10 — user relay từ Claude.ai session)

> **Core:** Đừng bán "phần mềm quản lý hợp đồng" cho SME. Trở thành "Hệ điều hành nghĩa vụ"
> mà cố vấn ngoài (đại lý thuế / law firm) vận hành trên khách của họ —
> **firm trả tiền trước, SME free** — rồi lật sang SME-pays khi mở tầng soạn/review.

**3 điểm gãy được giải:**
1. WTP — SME không trả cho "nhắc hạn" → B2B2B: firm trả theo đầu client (~50-100k/client/năm)
2. Activation (M-1 60% upload là giả định rủi ro nhất, không phải extraction) → **concierge onboarding** 20 SME đầu: số hóa cả ngăn kéo trong 1 ngày
3. Kênh firm chưa proven → pilot **2 firm song song** (1 đại lý thuế + 1 law firm), mỗi firm 10 SME, đo 90 ngày

**Timing positioning:** NĐ 337 hiệu lực 01/07/2026 (~3 tuần) — KHÔNG cạnh tranh tầng ký,
positioning **"ngôi nhà cho mọi hợp đồng sau khi ký"** đón hậu sóng.

**3 giai đoạn:**
| GĐ | Thời gian | Bán gì | Moat |
|---|---|---|---|
| 1. Troy + Concierge | Q3-Q4/2026 | Firm-pays per client; SME free; concierge 20 SME | Kho nghĩa vụ + extraction VN tuned |
| 2. Soạn/Review lawyer-in-loop | 2027 | SME-pays drafting từ template firm duyệt; firm revenue share | Template library + firm network |
| 3. Obligation graph hạ tầng | 2027+ | Nghĩa vụ thanh toán ↔ công nợ, hóa đơn ĐT/ngân hàng, benchmark | Graph xuyên nghìn SME |

**Kill / pivot signals (falsifiable):**
- Retention tuần 4 < 30% sau concierge → pivot wedge sang DMS cho firm nhỏ
- Firm không trả nhưng SME convert tốt qua reminder paywall → bỏ B2B2B, direct freemium
- Cả 2 firm không đẩy nổi 10 SME trong 90 ngày → kênh sai → thử hiệp hội ngành / cộng đồng F&B

---

## Ratified Decisions

| ID | Decision | Status | Date |
|---|---|---|---|
| DEC-001 | Stack: FastAPI + SQLite multi-tenant per BRD A-1 | Draft | 2026-06-09 |
| DEC-002 | `VisionExtractionProvider` — Gemini 2.0 Flash primary (~150đ/doc) + Claude Haiku fallback (~300đ/doc if accuracy <90%). Sprint 0 benchmark on 15 PII-scrubbed Bingxue HĐ samples. | **Ratified** | 2026-06-09 |
| DEC-003 | Hosting provider + data residency | Draft | 2026-06-09 |
| DEC-004 | Naming "Khế" finalization (R-7) | Draft | 2026-06-09 |
| DEC-005 | Sprint cadence | Draft | 2026-06-09 |
| DEC-006 | Telegram bot replaces Zalo ZNS | **Ratified** | 2026-06-09 |
| DEC-007 | Sprint 0 infra parallel with M0 | **Ratified** | 2026-06-09 |
| DEC-008 | KHE_Backend first session to spawn | **Ratified** | 2026-06-09 |
| DEC-009 | Session prefix ERP_ → KHE_ | **Ratified** | 2026-06-09 |
| DEC-010 | NĐ 13/2023 Phase 1: US-hosted LLM OK with explicit consent + audit log | **Ratified** | 2026-06-09 |
| DEC-011 | **B2B2B model:** firm là khách hàng trả tiền (per-client ~50-100k/năm), SME free Phase 1. SME-pays mở ở GĐ2 (drafting/review). | **Ratified** (user relay) | 2026-06-10 |
| DEC-012 | **Concierge onboarding:** 20 SME đầu KHÔNG bắt tự upload — số hóa tận nơi/firm thu hộ. M-1 (60%) đo SAU concierge baseline. | **Ratified** (user relay) | 2026-06-10 |
| DEC-013 | **2-firm pilot:** 1 đại lý thuế + 1 law firm song song, mỗi firm 10 SME, đánh giá 90 ngày. Thay mục tiêu "1 firm LOI". | **Ratified** (user relay) | 2026-06-10 |
| DEC-014 | **Positioning:** "Ngôi nhà cho mọi hợp đồng sau khi ký" — đón hậu sóng NĐ 337 (01/07/2026), KHÔNG cạnh tranh tầng ký số. | **Ratified** (user relay) | 2026-06-10 |
| DEC-015 | **Kill/pivot signals** ghi vào BRD: retention W4 <30% post-concierge → DMS pivot; firm không trả + SME convert → direct freemium; 2 firm không đủ 10 SME/90d → đổi kênh. | **Ratified** (user relay) | 2026-06-10 |
| DEC-016 | **Reminder paywall lever:** Strategy gốc đề xuất ZNS paywall (email free / Zalo paid) — NHƯNG DEC-006 Telegram giữ nguyên per user 2026-06-10. Freemium value metric cần lever khác hoặc re-evaluate Zalo paid channel GĐ2. | **Open — cần Kevin quyết** | 2026-06-10 |

**Giữ nguyên (user confirm 2026-06-10):** DEC-002 (VisionExtractionProvider Gemini+Claude), DEC-006 (Telegram), DEC-010 (NĐ 13 Phase 1).

---

## Day-1 Blockers

| Blocker | Risk | Action | Owner |
|---|---|---|---|
| **2 firm pilots** (DEC-013) | Cần 1 đại lý thuế + 1 law firm ký pilot trước Sprint 1 ship | Identify + contact + pitch 1-trang | User (Kevin) |
| NĐ 13/2023 obligation verification | Compliance baseline chưa verify chi tiết | Xác minh nghĩa vụ tuần này (user action per strategy) | User (Kevin) + KHE_Compliance |
| Hosting + data residency | VPS provider decision | Confirm provider + region | Sprint 0 |
| Naming finalization | R-7 trademark risk | Trademark check | Pre-launch |
| DEC-016 reminder paywall lever | Freemium value metric chưa chốt (Telegram giữ, ZNS bỏ) | Kevin quyết | User (Kevin) |

---

## Session Topology Status

| # | Session | Status |
|---|---|---|
| 1 | KHE_Docs | Branch created ✅ — **NEEDS spawn Sprint 1** (11 DOCS_INBOX pending fold) |
| 2 | KHE_PM_Assistant | Active ✅ |
| 3 | KHE_Backend | Sprint 0 ✅ DONE (#2 closed, PR #19 merged `cf6d022`). Sprint 1 backlog: #10 (per-tenant alembic), #22 (NĐ 13 consent gate) |
| 4-5 | KHE_Frontend_Admin / PWA_Chat | **NEEDS spawn Sprint 1** (M0 vertical slice) |
| 6 | KHE_QC | **NEEDS spawn Sprint 1** (E2E smoke) |
| 7 | KHE_Designer | Not spawned |
| 8 | KHE_Infra | Sprint 0 ✅ DONE (PRs #7, #8, #13, #18, #21 merged). VPS pattern + 8 secrets live |
| 9 | KHE_AI | Sprint 0 ✅ DONE (#3 closed, PR #17 merged). Pending: 15 PII-scrubbed samples từ Kevin |
| 10 | KHE_Compliance | **NEEDS spawn Sprint 1** (consent UX for #22) |

---

## Bootstrap Checklist (2026-06-09)

- [x] CLAUDE.md at root
- [x] MVP_BRD_Khe.md at root (KHE_Docs to move to docs/)
- [x] DOCS_INBOX [#1](https://github.com/kevindo1103/khe/issues/1)
- [x] `claude/edit-git-docs-Khe01` branch
- [x] `docs/spawn/SPAWN_KHE_*.md` (all 10 sessions)
- [x] DEC-002, DEC-006, DEC-007, DEC-008, DEC-009, DEC-010 ratified
- [x] KHE_Backend [#2](https://github.com/kevindo1103/khe/issues/2) + KHE_AI [#3](https://github.com/kevindo1103/khe/issues/3)
- [x] PROJECT_PLAN v0.1 draft in DOCS_INBOX
- [x] KHE_Backend + KHE_AI + KHE_Infra sessions spawned + Sprint 0 delivered
- [x] **Sprint 0 nghiệm thu — issue [#23](https://github.com/kevindo1103/khe/issues/23) (2026-06-11)**
- [ ] GitHub labels created (Settings → Labels) — vẫn pending Kevin
- [ ] KHE_Docs spawned — Sprint 1 priority (fold 11 DOCS_INBOX entries)
- [ ] Sprint 1 kickoff: Frontend/PWA/QC/Compliance spawn

---

## Sprint 0 Nghiệm thu Summary (2026-06-11)

**All 10 exit criteria PASS** — full table in issue [#23](https://github.com/kevindo1103/khe/issues/23).

**Architecture baseline ratified:**
- master.db (4 bảng) + per-tenant (7 bảng skeleton)
- API: `POST /auth/login` body `{tenant_id, username, password}` → JWT
- VisionExtractionProvider Protocol + 3 providers (Gemini 2.5 Flash primary)
- Deploy flow: `feature → staging → main`, 8/8 secrets live
- D-rules enforced ở extraction (D-01/06/08); D-10 enforced ở `get_db()` env-gate

**Sprint 1 carry-over:**
- 🔴 #22 NĐ 13/2023 consent gate (CRITICAL trước first production extraction)
- 🔴 #10 per-tenant Alembic migration chain
- 🟡 DEC-016 freemium paywall lever (Kevin quyết)
- 🟡 Domain `khe.vn`/`staging.khe.vn` confirm + VPS systemd unit deploy
- 🟡 15 PII-scrubbed F&B/bán lẻ HĐ samples từ Kevin cho full vision benchmark

**Sprint 0 PRs merged:** #6, #7, #8, #12, #13, #14, #16, #17, #18, #19, #21
**Issues closed:** #2, #3, #5, #9, #11, #15, #20
**Open Sprint 1:** #10, #22, #1 (DOCS_INBOX long-lived), #23 (nghiệm thu reference)

---

## INC Log / FM Log

*No incidents or failure modes yet.*

---

## Weekly Review Log

*No reviews yet.*
