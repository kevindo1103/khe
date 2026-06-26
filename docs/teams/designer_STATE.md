# KHE_Designer — Session STATE

> Owner: **KHE_Designer** (single-owner, no dev pair Phase 1).
> Scope: `docs/mockup_*.jsx` + `docs/teams/designer_STATE.md` only.
> Read-only on BRD/SRS — report DOCS_INBOX (#1) on spec gap, never edit canonical docs.
> Branch: `claude/design-system-m0`.

_Last updated: 2026-06-26 (#278 — /admin/documents v2 revamp: obligation-centric, B&W minimalist)_

> Branch (current task): `claude/design-documents-list-v2`.

## Decisions in force (design-relevant)
- **DEC-017** — Design System + mockups MUST land + Kevin-approve BEFORE Frontend
  (#30) / PWA (#31) code. Per-phase approval gate.
- **DEC-006** — Telegram bot as primary reminder channel (notification opt-in =
  deep-link, not Zalo).
- **DEC-012** — Concierge onboarding (≤20 SME) → upload screen needs a bulk mode.
- **D-07** — every extracted field must be user-editable with visible feedback
  (edit-in-place → Event); AI is not system of record.
- **D-08** — chat empty state MUST show "Không tìm thấy thông tin này trong hồ sơ
  của bạn." — never fabricate / suggest invented answers.
- **D-09** — firm portal read-only (M2+, not designed in M0).
- **FR-EX-05** — confidence + `needs_review` flag shown per field.

## Design tokens — source of truth
File `docs/mockup_design_system_v0.1.jsx` exports a `tokens` object (color,
typography, spacing on a 4px grid, radius, shadow, z-index). All later mockups
import/mirror these — do NOT redefine ad-hoc colors per screen.

Semantic color roles locked:
- `primary` — brand action (buttons, links, active nav)
- `success` — completed obligations, granted consent
- `warning` — `needs_review` badge, due-soon obligations
- `danger` — overdue obligations, destructive actions, revoked consent
- `info` — neutral notices, "đang xử lý" processing state
- `neutral` ramp — text, borders, surfaces (mobile-first contrast)

## Component library (Phase 1 — 8 components, done)
Built in `mockup_design_system_v0.1.jsx`:
1. **Button** — variants: primary / secondary / ghost / danger; sizes sm/md/lg; loading + disabled.
2. **Input** — label, hint, error, with optional inline edit affordance (D-07).
3. **Card** — surface container; header/body/footer slots.
4. **Table** — list/data table; status column friendly; mobile-stacked.
5. **Modal** — overlay dialog; used for consent (NĐ 13), confirm-destructive.
6. **Toast** — transient feedback (success/error/info); maps to Event-logged actions.
7. **Badge** — status pills; `needs_review` = warning, `confidence` = progress bar variant (FR-EX-05), doc status (processing/extracted/needs_review).
8. **EmptyState** — generic + the D-08 "Không tìm thấy" chat variant.

## Done
- [x] STEP 0 branch rename `claude/sweet-thompson-jixt9y` → `claude/design-system-m0`.
- [x] Cascade read: PRODUCT_STRATEGY v0.2 (personas/JTBD), BRD v0.3 (FR-IN/EX/OB/CQ/DR + §6 glossary), CLAUDE.md (D-rules + Decision Review Gate), #23 contract baseline, #24 task.
- [x] `docs/teams/designer_STATE.md` created.
- [x] **Phase 1** — `docs/mockup_design_system_v0.1.jsx` (tokens + 8 components + gallery showcase). **Kevin approved on #24.**
- [x] **Phase 2** — Admin 5 screens (all import Design System v0.1):
  - `mockup_admin_login_v0.1.jsx` — form {tenant_id, username, password} → POST /auth/login (#23)
  - `mockup_admin_upload_v0.1.jsx` — single drag-drop + bulk concierge ≤20 (DEC-012); FR-IN-01/03
  - `mockup_admin_document_list_v0.1.jsx` — status filter + search; FR-SR
  - `mockup_admin_document_detail_v0.1.jsx` — edit-in-place per field (D-07) + ConfidenceMeter + needs_review (FR-EX-05); obligations panel
  - `mockup_admin_obligation_v0.1.jsx` — urgency-bucketed due list, mark-done/hoãn → Event (FR-OB)

- [x] **Phase 3** — PWA 4 screens (mobile-first, PhoneFrame; import Design System v0.1). Kevin approved Phase 2 on #24.
  - `mockup_pwa_login_v0.1.jsx` — mobile login (same auth contract); exports shared `PhoneFrame`
  - `mockup_pwa_chat_v0.1.jsx` — chat thread, source chips (FR-CQ-02), **D-08 "Không tìm thấy" bubble**, empty state
  - `mockup_pwa_consent_v0.1.jsx` — NĐ 13/2023 first-login dialog per `nd13-v1` spec (#32 comment): buttons "Đồng ý…"/"Để sau", purpose=vision_extraction, names US recipients Google/Anthropic + revocation. ⚠ DRAFT copy, counsel sign-off pending (DEC-010)
  - `mockup_pwa_notification_v0.1.jsx` — Telegram opt-in deep-link `t.me/?start=` (DEC-006), 30+7 day reminders, email fallback

## Status: ALL Phase 1–3 mockups delivered. Awaiting Kevin Phase-3 approval to close #24 → unblock Frontend #30 + PWA #32.
- Each phase: commit → push → present to Kevin → await approve → next phase.

## Issue #278 — /admin/documents v2 revamp (DEC-043, B&W minimalist) — DELIVERED, awaiting Kevin
- Branch `claude/design-documents-list-v2`. From file-warehouse view → obligation & rights portfolio.
- **Design direction (Kevin 2026-06-25):** B&W base — body text #1A1A1A, white bg, borders #E5E7EB.
  Color rationed to CTA / active chip / status badges / completeness icons only. primary emerald
  `#0F7A56`, amber `#D97706`, red `#DC2626`, muted `#6B7280`. (Departs from DS v0.1 `#1F6F5C` — aligns
  with DS v0.2 #197, which is NOT yet in this branch → v2 mockups carry their own token block per #278 spec.)
- Delivered:
  - `mockup_documents_list_v2.jsx` — sidebar IA (REP-07, "Tải lên" typo fix) + header (action-first
    subtitle, counter chips, fixed "Tải hợp đồng" CTA) + commitment/pipeline filter rows + 5-col table
    (Hợp đồng / Loại / Nghĩa vụ·Quyền lợi / Hạn gần nhất / Trạng thái) + DEC-029 doc_type label map +
    all 7 row states + ↑NV/↓QL legend + on-page sort/scope annotations.
  - `mockup_documents_list_v2_empty.jsx` — Day-1 concierge empty state (DEC-012).
  - Token update folded inline: direction glyphs ↑↓, completeness ⚠/?, removable Beta chip flag.
- **PM decisions baked (QC G1–G10):** G1 classifier=for:ai out-of-scope · G2 sort order · G3 standing-only
  "Cam kết đang hiệu lực" · G4 honest NULL `?` (D-13) · G5 CTA fixed (no conditional) · G6 status pill carries
  color, NO amber row border · G7 glyph+text+legend · G8 snake_case lint = FE-impl AC · G10 Beta chip removable post-#277.
- Sequencing: mockup unblocked; FE-impl blocks on Backend API delta #279 (6 new fields) merged to staging.
- Both files esbuild-transpile clean. Awaiting Kevin approve.

## Spec-gap watch (post DOCS_INBOX #1 if confirmed)
- Field list for document detail mockup pulled from BRD §6 Term + #23 per-tenant
  `terms` table. If a needed field is missing from the ratified schema during
  Phase 2 detail design, flag via DOCS_INBOX (do not self-resolve).
- `thoi_han_hd` phi-số ("vô thời hạn") state — BRD FR-OB-01 leaves policy open;
  Sprint 2 "Vô thời hạn" obligation display flagged but NOT designed in M0.

## Inbox
- issue #24 (`for:designer`, `task-assignment`, GATING #30 + #31) — Sprint 1
  Design System + M0 mockups. Status: Phase 1 done, awaiting Kevin approve.
