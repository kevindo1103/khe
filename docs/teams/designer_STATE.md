# KHE_Designer — Session STATE

> Owner: **KHE_Designer** (single-owner, no dev pair Phase 1).
> Scope: `docs/mockup_*.jsx` + `docs/teams/designer_STATE.md` only.
> Read-only on BRD/SRS — report DOCS_INBOX (#1) on spec gap, never edit canonical docs.
> Branch: `claude/design-system-m0`.

_Last updated: 2026-06-18 (Phase 1+2 approved; Phase 3 PWA screens built)_

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

## Design System v0.2 — minimalist revamp (Atlassian/Stripe-grade) — branch `claude/design-system-revamp-minimal`
**`mockup_design_system_v0.2.jsx` supersedes v0.1.** Same API surface (export names +
token access keys) → other mockups upgrade by changing the import path only.
Upgrades: 11-step neutral ramp (slate), one restrained accent (khế-emerald `#0F7A56`),
soft layered elevation `e1/e2/e3` (not one flat shadow), **focus rings** on all
interactive elements (WCAG 2.4.7) + AA contrast text roles, type scale with negative
tracking on display sizes, **motion tokens** (duration + standard easing). New components:
Button `subtle` variant + `iconOnly`, Badge `dot`, **Skeleton**. Additive tokens:
`color.neutral[*]`, `color.ring`, `elevation.*`, `motion.*` (kept `shadow.*` alias for
back-compat). v0.1 marked SUPERSEDED.

### QC review of PR #197 — addressed (2026-06-23)
- **Contrast measured (not asserted):** ink 15.0 · inkBody 10.8 · inkMuted 4.78 · primary 5.33 · semantic-on-tint all AA. Fixed: `warning #9A6700→#8A6300` (was 4.34 FAIL → 4.85 PASS). `inkSubtle` (2.56) reclassified WCAG-exempt-only; Input hint rerouted to `inkMuted`.
- **Touch target:** md/lg bumped to 44/48px (44 = touch min). `sm` 32px = desktop-dense only (documented).
- **v0.1 freeze policy:** FROZEN (fix-forward), migration mandatory — documented in v0.1 + v0.2 headers.
- **Accent rule:** single brand accent (primary); semantic = functional state only, not decorative — documented.
- **Dark mode:** out of MVP; token structure theme-ready, dark elevation deferred — documented.
- **VN diacritics:** small labels weight 500+, body min 13px; real-device PWA QA = Frontend pre-prod item (flagged).
- **"No spec impact" clarified (NOT retracted for v0.2):** v0.2 = visual foundation, no BRD/SRS change. Activation-flow primitives (ProgressBar/Stepper/Achievement/locked-nav/progressive-extraction/4-state EmptyState) = **#198 scope**, built on v0.2 after ratify; DOCS_INBOX filed then if they touch FR-CQ/FR-EX/FR-RM. v0.2 is the base layer, not a "complete" library.

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

## Status: #24 DONE — merged via PR #36, closed. Frontend #30 + PWA #32 unblocked.

## DEC-030 obligation revamp (PM flag 2026-06-20 via backend relay) — branch `claude/design-obligation-direction-series`
Driven by BA contract logic (DEC-019..022) + DEC-030 self-party direction. Design references for FE #157 (#146b) + #158 (#146c):
- [x] `mockup_admin_obligation_v0.2.jsx` — **supersedes v0.1**. AXIS-1 direction tabs (Nghĩa vụ / Quyền lợi / Cần xác nhận=null, D-02); AXIS-2 buckets with #157 fix (waiting_trigger → 'waiting'; null due_date → 'open_ended'/"vô thời hạn" DEC-020; else date); milestone **series groups** collapsible w/ progress + chips (DEC-021); category/series/obligor/amount/trigger chips; expanded status actions (done/in_progress/cancel/waiting→trigger) → Event (FR-OB-04); chain-trigger toast.
- [x] `mockup_admin_self_party_confirm_v0.1.jsx` — "bên nào là bạn?" modal (#158): parties[] dropdown → confirm_self_party; Settings legal_name field; D-02 user-confirm framing.
- [x] v0.1 obligation marked SUPERSEDED.

### Coordination flags for the revamp
- "Cần xác nhận" tab + self-party modal depend on backend **#155** (parties[] persist + confirm_self_party) and **#156** type sync (ObligationOut +9 fields). Mockups assume the #157/#155 field shape (direction, obligation_type, milestone_series_id, milestone_index/total, obligor, trigger_condition, amount_raw, status incl. waiting_trigger).
- 2 PM/Backend ambiguities (per DOCS_INBOX): chat returns direction+series in sources? · parties persist = table vs JSON. Mockups don't depend on the resolution.

## #198 SME journey redesign (8-stage) — branch `claude/design-ux-journey-198`
Brief #198 (PM, ratified Kevin 2026-06-23: D-02 concierge Option B; firm journey deferred; SME-only). Build phased on Design System **v0.2** (#197 merged `9b4877f`).
- [x] **Phase A** — `mockup_journey_primitives_v0.1.jsx`: journey-layer primitives:
  - `tenant_journey_stage` state machine (NEW→EXTRACTING→NEEDS_REVIEW→CONFIRMED→ACTIVATED→STEADY, monotonic; home = f(stage))
  - **`JourneyEmptyState` 4-state matrix** (cold_start / processing / all_clear / no_match) — fixes the #198 false-reassurance anti-pattern; cold-start ≠ all-clear wording
  - `SetupProgress` stepper, `ReminderNudge` (ACTIVATED gate ≥1 channel, no hard-block), `LockedNav` (first-session only), `ScopeCard` (per-contract + hint loop, no "đã được bảo vệ"), `ConciergeWelcome` (D-02 Option B pre-fill→user self-confirm)
  - tagged `// PHASE-2-IA-DEBT` (entity vs job-shaped nav)
- [ ] **Phase B** — Stage 0/3/6/7 screen mockups (priority):
  - [x] Stage 0 `mockup_journey_stage0_onboarding_v0.1.jsx` — concierge (NEEDS_REVIEW pre-filled, D-02 Opt B) + self-serve (1 CTA, locked nav)
  - [x] Stage 6 `mockup_journey_stage6_chat_v0.1.jsx` — aggregate≠retrieval split; cold-start nudge (no D-08 chips); D-08 only on real no-match
  - [x] Stage 3 `mockup_journey_stage3_review_v0.1.jsx` — side-by-side (immutable original D-06 | extracted fields), confidence + ref-link + edit-in-place "Bạn đã cập nhật" (D-07), self-party selector, **confirm readback→preview→confirm (D-02)** gating reminder; low-confidence needs_review flag
  - [x] Stage 7 `mockup_journey_stage7_obligations_v0.1.jsx` — 3 tabs (Nghĩa vụ/Quyền lợi/Cần xác nhận) with **per-tab 4-state empties** (cold_start/all_clear branch + quyền_lợi/cần-xác-nhận honest empties), digest (FR-RM-04), Cần-xác-nhận CTA → Stage 3; row spec follows obligation v0.2
- [x] **Phase C** — Stage 1/2/4/5/8 (ALL #198 SME stages now mocked):
  - Stage 1 `mockup_journey_stage1_upload_v0.1.jsx` — dropzone (idle/dragging/ack) + 📷 chụp ảnh + ~30s expectation; PartialUpload failure path
  - Stage 2 `mockup_journey_stage2_processing_v0.1.jsx` — transparent narration + progressive field reveal (Skeleton→value), low-conf "sẽ nhờ bạn xác nhận"; ExtractionFailure path. PATTERN (SPEC-WATCH FR-EX)
  - Stage 4 `mockup_journey_stage4_obligation_v0.1.jsx` — AHA obligation card (GÌ·KHI·NGUỒN·HƯỚNG·LẶP humanised) + first-time coaching + Telegram bridge (DEC-006); ACTIVATED ≥1 channel, ReminderNudge if skip
  - Stage 5 `mockup_journey_stage5_reminder_v0.1.jsx` — Telegram message template (source + Đã xử lý/Nhắc lại sau + deep-link) + landing
  - Stage 8 `mockup_journey_stage8_dashboard_v0.1.jsx` — "Tổng quan" answers "cần lo gì?" — legitimate reassurance only (all-clear vs has-work) + ScopeCard (no overpromise)
- Watch: progressive-extraction (Stage 2) → FR-EX; chat aggregate/all-clear (Stage 6) → FR-CQ → DOCS_INBOX when those land.

### QC #198 packet review — conditional GO, gaps addressed (2026-06-23)
- **Gap B (drift enforcement):** `JourneyEmptyState` now CLOSED contract — `EMPTY_STATES` enum + dev-warn on unknown + render-null (can't silently regress to false reassurance). Recommend lint: block literal "Khế sẽ nhắc" outside primitive.
- **Missing-scope (failure/refuse):** added `ExtractionFailure` (Stage 2, no stuck skeleton, retry/manual) + `PartialUpload` (Stage 1, failed docs don't block tenant stage). Stage 4 refuse handled by `ReminderNudge` (CONFIRMED + nudge, no hard block).
- **Gap A (backend coord):** Stage 6 aggregate-vs-retrieval = FR-CQ spec change (chat intent classifier: aggregate answers from store, not D-08). → DOCS_INBOX #1 + relay `for:backend`, coordinate #27/#146. NOT pure UI rewrite.
- **Gap C (v0.1 freeze, EXPLICIT):** v0.1 FROZEN, fix-forward in v0.2, migration MANDATORY. Proposed deadline: remove v0.1 imports within 2 weeks of all screens migrating — **needs PM/Frontend confirm**.
- **QC open-Q accepted:** lock Stage 0/6 first (defer Stage 3 — heaviest, rework risk); OPEN PR for inline review; defer job-shaped nav post-pilot.

- Field list for document detail mockup pulled from BRD §6 Term + #23 per-tenant
  `terms` table. If a needed field is missing from the ratified schema during
  Phase 2 detail design, flag via DOCS_INBOX (do not self-resolve).
- `thoi_han_hd` phi-số ("vô thời hạn") state — BRD FR-OB-01 leaves policy open;
  Sprint 2 "Vô thời hạn" obligation display flagged but NOT designed in M0.

## Inbox
- issue #24 (`for:designer`, `task-assignment`, GATING #30 + #31) — Sprint 1
  Design System + M0 mockups. Status: Phase 1 done, awaiting Kevin approve.
