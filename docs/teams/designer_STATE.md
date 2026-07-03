# KHE_Designer — Session STATE

> Owner: **KHE_Designer** (single-owner, no dev pair Phase 1).
> Scope: `docs/mockup_*.jsx` + `docs/teams/designer_STATE.md` only.
> Read-only on BRD/SRS — report DOCS_INBOX (#1) on spec gap, never edit canonical docs.
> Branch: `claude/design-system-m0`.

_Last updated: 2026-07-03 (#481 — document list v3 on DS v1.1, closes rollout gap 3/3)_

> Branch (current task): `claude/design-doc-detail-reread-305` (issues #281, #305).

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

### v0.1 → v0.2 migration — Admin (7/7 DONE) — branch `claude/design-migrate-admin-ds-v02`
Per migrate-on-touch policy (#208), admin screens migrated DS v0.1 → v0.2: `admin_login`,
`admin_upload`, `admin_document_list`, `admin_document_detail`, `admin_obligation_v0.1`,
`admin_obligation_v0.2`, `admin_self_party_confirm`. **Import-path swap only** — verified
zero token/component drift (all used tokens + Button/Input/Card/Table/Badge/EmptyState/
ConfidenceMeter/Toast/Modal exist in v0.2 with identical API; Badge kinds done/due_soon/
needs_review/neutral + Toast success all valid). Filenames unchanged (file-version ≠ DS-version,
same as journey suite). **Still on v0.1: PWA (4)** — `pwa_login/chat/consent/notification`,
deferred to KHE_PWA_Chat / next touch.
- Optional a11y follow-up (NOT in migration): some admin text uses `inkSubtle` (v0.2 below-AA,
  exempt-only) → should move to `inkMuted`; legacy `admin_obligation_v0.1` line ~95 still has
  the #198 false-reassurance string but is SUPERSEDED by v0.2 — left untouched.

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
- **#199 Stage 6 aggregate contract LOCKED (2026-06-23)** — formalized prose → structured shape; backend adds `aggregate_obligations` tool. NO amount sum v1 (D-06); axes direction/status/obligation_type/series; 3 zero-states (cold_start `tenant_empty` / aggregate-0 / retrieval-D-08). Folded into `mockup_journey_stage6_chat_v0.1.jsx` header. Backend unblocked.

### QC #198 packet review — conditional GO, gaps addressed (2026-06-23)
- **Gap B (drift enforcement):** `JourneyEmptyState` now CLOSED contract — `EMPTY_STATES` enum + dev-warn on unknown + render-null (can't silently regress to false reassurance). Recommend lint: block literal "Khế sẽ nhắc" outside primitive.
- **Missing-scope (failure/refuse):** added `ExtractionFailure` (Stage 2, no stuck skeleton, retry/manual) + `PartialUpload` (Stage 1, failed docs don't block tenant stage). Stage 4 refuse handled by `ReminderNudge` (CONFIRMED + nudge, no hard block).
- **Gap A (backend coord):** Stage 6 aggregate-vs-retrieval = FR-CQ spec change (chat intent classifier: aggregate answers from store, not D-08). → DOCS_INBOX #1 + relay `for:backend`, coordinate #27/#146. NOT pure UI rewrite.
- **Gap C (v0.1 freeze, EXPLICIT):** v0.1 FROZEN, fix-forward in v0.2, migration MANDATORY. Proposed deadline: remove v0.1 imports within 2 weeks of all screens migrating — **needs PM/Frontend confirm**.
- **QC open-Q accepted:** lock Stage 0/6 first (defer Stage 3 — heaviest, rework risk); OPEN PR for inline review; defer job-shaped nav post-pilot.

## App navigation v0.2 — responsive (Kevin-ratified 2026-06-23, layout-only) — branch `claude/design-nav-responsive-sidebar`
`mockup_app_nav_v0.2.jsx` (imports Design System v0.2 only). Switch horizontal top nav →
**desktop vertical sidebar (grouped sections) + mobile bottom-tab bar** (thumb-reach;
SME owner mobile-first). Reason: group theo category + scale khi thêm feature.
- LAYOUT-only: nhãn vẫn **entity-shaped** (Phase 1 ratified); job-shaped IA vẫn defer (`PHASE-2-IA-DEBT`).
- Giữ nav-lock first-session-only (clear ở ACTIVATED) — supersedes `LockedNav` layout in journey primitives (lock semantics identical).
- Sections: Theo dõi (Tổng quan/Nghĩa vụ) · Tài liệu (Kho/Tải lên) · Trợ lý (Hỏi-đáp) · footer Cài đặt+account. Bottom-tab = 5 primary, center = upload action.
- Firm section sau này drop-in được mà không đụng phần còn lại.
- **MERGED PR #204 (`10287b49` → staging)** sau QC holistic. Review-5 fixed inline trước merge: (#1) nav items = `<button>`+focus ring+aria, (#2) `AppMobileHeader` cho Settings/đăng xuất trên mobile, (#3) first-session unlock `upload` (onboarding action) + home, (#4) badge mobile unify warning-soft = `Badge due_soon`, (#5) `LockedNav` deprecation note + follow-up.

## A11y handoff contract (#206) — DONE on Design System v0.2 — branch `claude/sweet-thompson-jixt9y`
QC holistic của #200 + #204 surfaced **1 systemic a11y pattern** (interactive `<div>`/`<span>` thay vì `<button>`/`<a>`; thiếu `aria-live`). Gốc là pattern → fix ở contract level, KHÔNG sửa rải rác.
- `mockup_design_system_v0.2.jsx` §2b **a11y-correct primitives** (exported): `NavItem` (auto picks `<a>`/`<button>`; locked → `<button disabled>`), `Dropzone` (role+tabIndex+Enter/Space+drag+aria), `IconButton` (mandatory `label`→aria-label, dev-warn nếu thiếu), `LiveRegion` (aria-live polite), `VisuallyHidden`.
- Header doc: **A11Y HANDOFF CONTRACT** block — 4 rules (semantic elements / keyboard / live regions / icon semantics), BINDING on Frontend khi build production components.
- Showcase: "A11y primitives (#206)" section demos cả 5.
- **Downstream (follow-up, không block):** #200 stages (`LockedNav`, Stage 1 dropzone, Stage 2/8 aria-live) + nav re-import từ corrected primitives khi journey mockups adopt. Gate: trước Frontend nav/journey production build.

## Admin steady-state re-layout + Settings — branch `claude/design-admin-relayout-settings`
Lấp gap "đủ cho FE revamp chưa": admin steady-state mới chỉ token-swap (#215), chưa re-layout. Thêm:
- `mockup_admin_document_detail_v0.2.jsx` — **re-layout** minimalist (supersedes v0.1): side-by-side D-06 immutable | extracted Terms; per-field confidence + needs_review (FR-EX-05) + edit→Event (D-07) + **ref-link** anchor vào bản gốc (PDF.js scroll-to = FE wires); **Parties panel** + derived Obligations có **direction** (DEC-030/D-13); sticky original; a11y.
- `mockup_admin_settings_v0.1.jsx` — **NEW** (lấp nav "Cài đặt"): Hồ sơ DN (legal_name DEC-030) · Kênh nhắc (Telegram/email DEC-006; windows KHÔNG hardcode — DEC-020 pending) · Tài khoản (đổi MK Modal) · NĐ13 consent + thu hồi (D-10 Modal) · Firm access placeholder (M2+).
- **QC #199 drift fix (preview Tổng quan):** direction cards = `summary.groups[]` (sum = total); status (Chờ sự kiện) = `summary.status_breakdown` cross-cut → strip riêng, KHÔNG cộng vào direction. Reassurance numbers khớp cards. Rule folded vào stage6 header (DASHBOARD CONSUMER RULE). +chip color semantics note (provenance=primary vs scope=info) vào DS v0.2 header.
- Preview artifact: `khe_tong_quan_preview.html` (chưa commit — file HTML review).
- **Còn lại:** PWA (4) vẫn v0.1; document_list/upload re-layout = next; firm portal/quota-429 chưa mock.

## Admin list/upload re-layout + responsive Dashboard — branch `claude/design-admin-list-upload-dashboard`
Đóng phần còn lại của "đủ cho FE revamp" (PWA defer cả app — không làm):
- `mockup_admin_upload_v0.2.jsx` — re-layout; **adopt `Dropzone` a11y primitive** (#206) thay div tự chế; queue có failed-row (PartialUpload, không kẹt) + quota hint (D-11). Supersedes v0.1.
- `mockup_admin_document_list_v0.2.jsx` — re-layout; doc count + filter chips (count per-status, aria-pressed); **2 empty states honest** (cold-start CTA vs filter no-match). Supersedes v0.1.
- `mockup_admin_dashboard_v0.2.jsx` — **NEW canonical** Tổng quan, **responsive THẬT** (adopt AppSidebar/AppMobileHeader/AppBottomTabs từ #204 + `<style>` media-query @760px). Content = QC-fixed: direction cards (groups[], sum=7) + status strip (status_breakdown cross-cut) + reassurance khớp + ScopeCard honest. Formalize từ `khe_tong_quan_preview.html`.
- **Admin dashboard responsive = DONE (canonical JSX)**, không chỉ HTML preview.
- **Coverage giờ:** Admin web đủ cho FE revamp (login/upload/list/detail/obligation/settings/dashboard trên v0.2). NGOÀI scope còn: firm portal, quota-429 screen, PWA (defer cả app).

## Firm journey (#236, DEC-039) — primitives DONE — branch `claude/design-firm-primitives-236`
Firm = economic buyer (Chị Hằng, B2B2B). Portal = lead-generator (J5), KHÔNG dashboard. PM resolved 4 blockers + 9 items trên #236; backend contract = #237 (build không cần #237 merged).
- `mockup_firm_journey_primitives_v0.1.jsx` — 6 primitives: `ConsentStatus` (pending/granted/revoked) · `DataRestrictedLabel` (labor PII metadata-only, PM B4) · `FirmEmptyState` (CLOSED 4-state: cold_start/processing/all_clear/revoked, cold≠clear) · `RevokeBanner` (D-10 instant vanish, no cache) · `LeadSignalCard` (J5: WHO+WHEN+WHY + mailto CTA "Liên hệ tư vấn", urgency ≤7/8-30/31-90) · `ClientCard` (full business data DEC-039, truncate 3 + xem tất cả, read-only). +`urgencyOf()` helper.
- Constraints: D-09 read-only (no edit affordance) · D-10 SME-only revoke · DEC-039 full data · labor exception field map · desktop-first · inherits #206 a11y.
- Primitives **#242 MERGED** (PM approved; ConsentStatus granted → `done` kind per PM note; urgencyOf tokens verified).
- ⚠ DEC-039 chưa fold canonical — PM post DOCS_INBOX sau Kevin ratify. Firm digest = email-only MVP; no chat/export/push (PM items 4/5/8).

### F-stages DONE — ✅ MERGED PR #243 → staging (PM retrospective LGTM)
- `mockup_firm_stage_F0_F1_v0.1.jsx` — F0 cold-start (Mời client) + F1 **dual path** (F1a concierge: tạo tenant + activation link / F1b invite: SME đã có account) + sent-confirm + pending list. **Exports `FirmShell`** (desktop sidebar, reused). NavItem #206.
- `mockup_firm_stage_F3_F4_v0.1.jsx` — F3 portfolio (ClientCard grid, sort due/name/count + filter 30/60/90, all-clear empty) + F4 lead signals (grouped Khẩn cấp/Sắp tới/Theo dõi, mailto CTA, LiveRegion count, all-clear).
- `mockup_firm_stage_F5_F6_v0.1.jsx` — F5 digest (stat cards + bản tin tháng + **email-only toggle**, all-clear) + F6 consent settings (active consents list + RevokeBanner transition; **no firm-side revoke** — D-10/PM #9).
- All read-only (D-09), consent-gated (D-10), desktop-first, inherit #206. Built to #237 contract.

## DEC-040 confirm-flow design (#238 ratify) — ✅ MERGED PR #245 (`09d2a61` → staging)
Kevin ratified #238: `POST /documents/{id}/confirm` + nav-unlock = **Option (B) CONFIRMED** (is_first_session clears tại CONFIRMED, không phải ACTIVATED). Option B ⇒ user có thể tới steady WITHOUT reminder channel → "silent product failure" → MANDATORY nudge. Designer A+B+C:
- **A (MANDATORY):** `mockup_admin_dashboard_v0.2.jsx` thêm state **CONFIRMED-without-channel** → `ReminderNudge` (#198 primitive) + chip **"N/M bước"** (doc ✅ · nhắc Telegram ⬜ · steady ⬜) + nút Bật nhắc. Showcase toggle 2 state.
- **B:** DEC-040 fix nav-lock refs **ACTIVATED → CONFIRMED** trong `mockup_app_nav_v0.2.jsx` + `mockup_journey_primitives_v0.1.jsx` (header + LockedNav note). Giữ nguyên ACTIVATED ở chỗ = stage enum + reminder-channel gate (vẫn đúng).
- **C:** `mockup_admin_document_detail_v0.2.jsx` thêm footer **"Xác nhận document này"** (disabled khi đang sửa field) + confirmed badge + toast (X/Y) — design ref cho FE item 1/2 (#238).
- **ProgressChip → journey primitive (§6b):** promoted từ dashboard-local sang exported `ProgressChip({ steps })` trong `mockup_journey_primitives_v0.1.jsx` (generalized `{label,done}[]` prop, cùng shape `SetupProgress` §3). Reusable trên doc-detail/doc-list.
- ⚠ DEC-040 = clarification của #213, KHE_Docs fold DOCS_INBOX (PM note). Mockup-scope, no BRD/SRS edit by me.
- **FE follow-up #247:** (1) lift ProgressChip lên shared component khi surface thứ 2 cần; (2) X/Y từ `confirmed_by_user_at` — ✅ đã có trong FE #246.

### #246 FE impl review (2026-06-25, COMMENT — not our branch)
FE confirm-flow impl (JourneyContext refactor + confirm button + mandatory nudge). Architecture solid (one fetch, atomic sidebar unlock via refetch). **1 fix flagged:** DocList `needsConfirm = status !== 'processing' && !confirmed_by_user_at` shows unclearable "Cần xác nhận" badge trên `status=failed` docs (no terms → no confirm card). Suggest gate trên `extracted || needs_review`. Left for PR owner. Non-blocking notes: `/consent` fail-open cuts against DEC-040 intent; StepsChip/ReminderNudge local (= #247).

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
- Both files esbuild-transpile clean. Browser preview `mockup_documents_list_v2_preview.html` (self-contained vanilla, no CDN).
- **✅ APPROVED by Kevin 2026-06-26.** → open PR `claude/design-documents-list-v2` + file FE-build task.

## Issue #281 — /admin/documents/:id doc-detail v2 revamp (DEC-043 + QC doc-detail report) — IN PROGRESS
- Branch `claude/design-doc-detail-reread-305`. Full redesign of document-detail page, sibling to #278.
- **IA inverted (DEC-043):** derived title → self-party gate (BLOCKING) → Nghĩa vụ & Quyền lợi → Terms (demoted).
- **3-tab structure (Kevin comment 2026-06-26):**
  1. Tổng quan — snapshot, self-party gate, completeness banner, term-fields (⚠ only, no raw %)
  2. Nghĩa vụ & Quyền lợi — THE CORE. Direction badges per-row (NV/QL/NULL). Event-anchored CTAs. Standing commitments. DEC-020 review row.
  3. Nội dung hợp đồng — clauses accordion (backend #283). ≤8 expanded. Empty state honest (D-08).
- **PM corrections baked:** DRL-09 rejected (no X/N counter on detail). DEC-020 review row kept, type="Review", excluded from tally. FR-EX-05 = ⚠ badge only.
- **Sample data:** Công nghệ & IP contract with ALPHATECH — exercises all obligation types, direction cases, event-anchored dates, standing commitments, overdue, completeness=amber.
- **Issue #305 — DEC-048 §13 (re-read surfaces):** 3 new mockup surfaces added:
  1. ReReadBanner (§13-D2) — Tab 3: "Bạn đã sửa N điều khoản. Khế đọc lại nghĩa vụ?" [Đọc lại] disabled pre-P1 (#309) + [Bỏ qua]
  2. DiffConfirmModal (§G2, D-02) — per-obligation diff. Manual-precedence: [Giữ của bạn ✓] pre-selected. 3 sample diffs (2 AI + 1 manual-source "🔒 Thủ công").
  3. StaleEditBanner (§G3, D-08) — Tab 2: "⚠️ N điều khoản đã sửa chưa đọc lại — nghĩa vụ có thể chưa cập nhật."
- **QC review fixes (D1–D4):**
  - D1: separated `rereadPromptDismissed` from `editedNotReread` — "Bỏ qua" hides prompt only, stale banner persists until actual re-read (apply diff)
  - D2: added 3rd manual-source diff sample with "🔒 Thủ công" badge (§G2 manual-source protection)
  - D3: tooltip now cites P1 (#309) as hard-blocker, not just source_clause_num
  - D4: relabeled "§G1" → "§13-D2" (§G1 is QC's re-read scope concern, not the banner)
- Delivered:
  - `mockup_document_detail_v2.jsx` — full page, 3 tabs, all states + 3 DEC-048 surfaces
  - `mockup_document_detail_v2_preview.html` — self-contained vanilla HTML/CSS/JS preview (no CDN), toggle controls for stale/diff-modal
  - `docs/teams/designer_STATE.md` updated
- Awaiting Kevin review.

## Spec-gap watch (post DOCS_INBOX #1 if confirmed)
- Field list for document detail mockup pulled from BRD §6 Term + #23 per-tenant
  `terms` table. If a needed field is missing from the ratified schema during
  Phase 2 detail design, flag via DOCS_INBOX (do not self-resolve).
- `thoi_han_hd` phi-số ("vô thời hạn") state — BRD FR-OB-01 leaves policy open;
  Sprint 2 "Vô thời hạn" obligation display flagged but NOT designed in M0.

## Session wrap-up 2026-06-25
- **#243 firm F-stages** — PM retrospective LGTM, merged to staging. DOCS_INBOX filed (4 forward notes: F1a concierge backend, F4 mailto source, F1 PWA badge, DEC-039 fold).
- **#245 DEC-040 confirm-flow** — ProgressChip → §6b primitive. PM LGTM, merged staging (`09d2a61`). DOCS_INBOX filed (DEC-040 canonical fold pending KHE_Docs).
- **#246 FE impl** — reviewed (LGTM + 1 fix: failed-doc badge). Not our branch.
- **#247** — FE follow-up filed (note 2 already done in #246).

### Open for next session
- **#470 DS v1.1 — MERGED to staging** (PR #473, `8e86844`). Canonical for ALL mockups going forward. PR #468 (#467) is grandfathered on v0.2 tokens (already reviewed OK, no rework needed for token reasons).
- **#467 obligation tab v3** — PR #468: Kevin review PASS + QC review addressed (2 findings fixed: `nullDir` status-exclusion bug, `SourceClauseLink` icon glyph removed) + 2 open notes carried to Frontend kickoff (bulk-complete confirm step, Phạt badge should follow v1.1 outline treatment in production). Rebased onto current staging. Ready for merge.
- **#378 DEC-050 v3** — PR #380 merged to staging.
- **PR #310** — approved by QC, awaiting Kevin merge (will auto-close #305).
- **#312 follow-up** — F1 audit drawer remaining (F2/F3 baked into v3).
- **DEC-055 icon cleanup** — obligation_v0.2 + other screens flagged for emoji removal (Q7 system-wide) — now superseded by v1.1's absolute icon-ban (1 exception: `IconButton`).
- **DEC-040 canonical fold** — awaiting KHE_Docs → BRD/SRS.

## Servanda Design System v1.1 — CANONICAL (supersedes DS v0.2) — ratified 2026-07-03
PM relay history on #467/#469 was messy (v1.0 proposed → retracted as unratified → Kevin overrode retraction, kept v1.0 → promoted to v1.1 folding 3 v0.2 strengths). **Net result: v1.1 is canonical for every mockup from this point forward.** DS v0.2 (`mockup_design_system_v0.2.jsx`) is superseded but NOT retroactively required on already-reviewed work (PR #468 grandfathered).

**Philosophy — "Sổ cái" (Ledger), 5 principles from D-rules:**
1. Ledger, not startup dashboard — warm paper ground, dark ink, no gradients/glassmorphism
2. State never lies (D-08) — including "Chưa rõ hướng" (unknown direction)
3. Urgency must be "earned" (Von Restorff) — red is a scarce resource
4. **Serif = the contract's words, Sans = the software's words** (D-06) — every verbatim contract quote renders serif
5. Confirmation is a ritual: readback → decide → record (D-02), no dark patterns (D-11)

**Token table (full, v1.1):**

| Token | Value | Note |
|---|---|---|
| paper / surface | `#FBFAF7` / `#FFFFFF` | |
| ink / ink-muted / ink-faint | `#1C2420` (15.21:1) / `#5A6660` (5.74:1) / `#8B948F` (2.99:1, intentionally sub-AA) | ink-faint = placeholder/disabled ONLY |
| **border-strong** (v1.1 NEW) | `#7E8983` (3.47:1 vs paper, WCAG 1.4.11 pass) | interactive borders: input/button/checkbox. Replaces `n-300` for these uses |
| n-200 / n-300 | `#E6E5DE` / `#D2D2C9` | decorative borders ONLY — NOT interactive components (they fail 3:1) |
| primary / hover / tint | `#1E5C49` (7.5:1) / `#174A3B` / `#EAF1EC` | "Lục Khế" |
| danger / warn / info / done (+tint each) | `#A6372B` / `#8A5800` / `#33597E` / `#5A6660` | 5.2–6.4:1 per badge pair |
| radius | 6px control / 10px card / pill badge only | |
| spacing | 4px rhythm: 4/8/12/16/24/32/48/64 | content max-width ≤880px |
| **elevation** (v1.1 NEW) | `e0: none` · `e1: 0 1px 2px rgba(28,36,32,.06)` · `e2: 0 2px 6px rgba(28,36,32,.09)` · `e3: 0 16px 32px rgba(28,36,32,.20)` | replaces flat 1-tier shadow — "layered paper" metaphor |
| font | Be Vietnam Pro (UI, self-host VN subset) + Source Serif 4 (contract verbatim text ONLY, never UI chrome) | type scale 28/22/16/15/13.5/12.5 + 11 uppercase label; weights 400/500/600; `tabular-nums` all digits |

**Icon rule:** absolute ban, ONE exception — `IconButton` (single functional glyph, tight space, mandatory `aria-label`). Business/status state ALWAYS uses text badge, never icon.

**13 canonical status badges (vocabulary, do not invent new ones):** Quá hạn N ngày (danger) · Hôm nay / Còn N ngày (warn) · future date (neutral) · Chờ kích hoạt / Chờ xác nhận (info) · **Phạt** (red OUTLINE + transparent fill — visually distinct from solid-fill danger overdue) · Đã hoàn thành / Đã thanh lý (done — quiet gray, NOT celebratory green) · Đã hủy (done + line-through) · Chưa rõ hướng (neutral + Settings link) · Đợt 07/14 (primary) · Nhập tay / AI·đã duyệt (neutral — 2-tier provenance per DEC-055).

**8 hard color rules:** danger exclusive to overdue+destructive · max ONE red zone per screen · completion = quiet gray, never celebratory green · color never sole channel of meaning · no gradients, elevation via e0-e3 only (not ad-hoc shadows) · (+3 more, see style guide artifact Kevin holds — ping PM on #467/#469 if offline HTML reference needed).

**4 new mandatory components (a11y contract, #206 folded in):** `NavItem` (always `<button>`/`<a>`, never `<div onClick>`) · `IconButton` (icon-only, mandatory `aria-label`) · `Dropzone` (`role="button"` + `tabIndex=0` + Enter/Space) · `LiveRegion` (`aria-live="polite"` for self-changing text, e.g. extraction progress).

**10 components with real render (in Kevin's style-guide artifact):** 4-tier button (1 primary per viewport) · obligation card (checkbox + ≤2 badges + tabular meta + right-aligned action) · series card collapsed (progress + next installment + amount) · bulk action bar (inverted-ink background) · 3-level banner replacing icons (SelfPartyGate→Settings link is the worked example) · D-02 readback modal (serif) · form label-above/error-says-fix · tabs-with-counts · D-08 honest empty state · event-chain narrating toast.

**11 UI/UX laws checklist** (Jakob/Hick/Miller/Fitts/Von Restorff/Gestalt/Doherty/Peak-End/Tesler/Postel/Aesthetic-Usability) — QC uses this at gate step 3 to verify mockups.

**Voice:** address as "bạn", self-refer "Servanda", no exclamation marks, facts before framing, errors = what+why+how-to-fix.

**Migration note:** next NEW mockup (not #467/PR #468, which is grandfathered) must build on v1.1 tokens. Reference `mockup_design_system_v0.2.jsx` component *shapes* are still useful (Button/Card/Badge/Modal structure) but every hex/shadow/border value must switch to the v1.1 table above — especially swap any `border`/`borderStrong` usage to the new `border-strong` token, not `n-300`.

## Issue #470 — Servanda DS v1.1 formalized (supersedes v0.2) — branch `claude/design-system-v1.1-formalize-470`
Kevin ratified v1.1 "Sổ cái" on #467/#469 (2026-07-03) via comment relay (messy history: v1.0 proposed → PM wrongly retracted it as unratified → Kevin overrode the retraction, kept v1.0 → promoted to v1.1 folding 3 v0.2 strengths). This task turns that comment-thread spec into an actual living file, mirroring `mockup_design_system_v0.2.jsx`'s format (tokens export + component set + gallery showcase, self-contained, zero build).
- **Delivered:** `mockup_design_system_v1.1.jsx` — esbuild-transpile clean, 19 exports (`tokens` + 18 components).
- **Tokens — completely distinct from v0.2** (do not mix): paper `#FBFAF7`/surface `#FFFFFF`/ink `#1C2420`/inkMuted `#5A6660`/inkFaint `#8B948F` (intentionally sub-AA, placeholder-only) · **`borderStrong` `#7E8983`** (NEW, 3.47:1, the ONLY border for interactive components — n200/n300 decorative-only) · primary "Lục Khế" `#1E5C49` · danger `#A6372B`/warning `#8A5800`/info `#33597E`/**done `#5A6660`** (no `success` token — deliberate, completion is quiet gray not celebratory green) · radius 6/10/pill · **elevation e0–e3** (NEW, "paper stacked in layers" metaphor) · font Be Vietnam Pro (UI) + Source Serif 4 (contract verbatim text only, D-06).
- **3 things folded from v0.2** (only these — see file header for full rationale): (1) measured-contrast methodology, which surfaced the real `borderStrong` gap; (2) #206 A11y handoff contract wholesale — `NavItem`/`IconButton`/`Dropzone`/`LiveRegion`/`VisuallyHidden` ported and re-themed; (3) layered elevation e0–e3 replacing v1.0's flat single shadow.
- **New v1.1-only components:** `ContractQuote` (serif D-06 quote block), `ReadbackModal` (D-02 confirm ritual: readback→decide→record), `Banner` (3-level, bold-label-replaces-icon — worked example replaces old SelfPartyGate emoji), `ActionBar` (inverted-ink bulk-select bar), `Tabs` (counted).
- **Badge — full 13-entry status vocabulary** implemented as `kind` presets (`overdue`/`dueSoon`/`future`/`waiting`/`penalty`/`done`/`cancelled`/`unclear`/`series`/`manual`/`aiVerified`), solid-vs-outline variant distinguishes urgency from provenance/info (`penalty` outline explicitly distinct from `overdue` solid, per spec).
- **Icon rule enforced structurally:** only `IconButton` renders a glyph, and it dev-warns if `label` is missing; every other component is text+color only.
- **Showcase gallery:** renders full token set (ground/ink/brand/semantic swatches, type scale incl. live `ContractQuote` sample, spacing/radius/elevation), all 13 badges, `ReadbackModal` demo, `Banner` worked example (SelfPartyGate replacement), `Tabs`+`ActionBar` interactive demo, and all 4 a11y primitives.
- **NOT retroactive:** PR #468 (#467) stays on v0.2 tokens — grandfathered, not touched. Migrate-on-touch policy applies (same as v0.1→v0.2 precedent) — only NEW mockups from here build on v1.1.
- Awaiting Kevin/QC review (gate — same pattern as #466/#467).

## Issue #378 — DEC-050 doc-detail v3 (6 new surfaces, EPIC #362) — branch `claude/design-doc-detail-dec050-378`
- Extends `mockup_document_detail_v2.jsx` (#281) with 6 DEC-050 surfaces into a new file.
- **Delivered:** `mockup_document_detail_v3.jsx` (~1055 lines) — 4-tab layout:
  1. **Tổng quan** — R8 lifecycle badge (5 states: active/expiring/expired/settled/suspended) + existing snapshot
  2. **Nghĩa vụ & Quyền lợi** — condensed from v2 (unchanged logic)
  3. **Bên ký kết** (NEW R2 #364) — `PartyCard` with self-party emerald highlight vs counterparty gray; grid details (address/representative/MST/contact); D-07 edit buttons
  4. **Nội dung hợp đồng** — R3 (#365) clause hierarchy (recursive nested accordion, 24px indent, └ connector, child count badge) + R5 (#368) `ClauseTable` HTML tables + `ImageCropRef` dashed-border + `SignatureStampSection` ✍️/🔴 + R9 (#372) `GlossarySection` collapsible term/definition pairs + R10 (#373) `renderClauseContent()` with `{{term}}` → dashed-underline tooltip and `[[ref]]` → blue link or red wavy orphan indicator + `OrphanRefPanel` warning banner
- **QC #312 fixes baked in:** F2 sidebar badge [3] on Tổng quan tab; F3 H1 reactive to self-party (shows counterparty name when self-party selected)
- **Sample data:** Công nghệ & IP contract ALPHATECH ↔ Cty TNHH Minh Phát — exercises all party states, hierarchical clauses (3 levels), payment table, image ref, signature/stamp, glossary, orphan ref
- **Design tokens:** B&W minimalist (DS v0.2 direction). Color rationed: primary `#0F7A56`, amber `#D97706`, red `#DC2626`, muted `#6B7280`.
- Awaiting Kevin review.

## Issue #481 — Document list v3 on DS v1.1 (rollout gap 3/3) — branch `claude/design-documents-list-v1.1-481`
QC filed #481: after PR #476 shipped DS v1.1 only for the obligation tab, the other 3 screens felt visually inconsistent. Gap 1+2 (doc-detail Tổng quan + Nội dung hợp đồng tabs) closed by `mockup_document_detail_v4.jsx` / PR #480 (#478, awaiting ratify). This closes **gap 3/3: document list page** (`/admin/documents`).
- **Delivered:** `mockup_documents_list_v3.jsx` — real import from v1.1 (`tokens, Button, Card, Table, EmptyState`), esbuild-clean, every `t.*` token reference audited against real v1.1 exports (caught + fixed one typo: `t.font.weight.bold` doesn't exist, v1.1 only has regular/medium/semibold — fixed to `semibold`).
- **Research (Explore agent) against real `DocumentList.tsx` (634 lines) + backend `routers/documents.py`/`schemas/documents.py` + `AdminShell.tsx`.** Findings beyond a naive re-skin:
  - `StatusPill` confirmed ad-hoc (doesn't use the app's own `Badge.tsx` atom) — but `LifecycleBadge.tsx` IS a proper shared atom already (just uses its own unrelated 5-color scheme).
  - **`StatusPill` has a real logic bug** (Designer-found, not in #481's brief): doesn't branch on `status==="failed"` — failed docs render "Cần xác nhận" (misleading). Flagged as **Q-Status-Failed**, opt-in toggle, default OFF (mockup mirrors today's real, buggy behavior by default — not silently fixing production logic in a visual PR).
  - `may_have_unextracted_obligations` (drives ⚠/? `CompletenessIcon`) is hardcoded `None` in the router (`TODO(#276)`) — dead code, never renders in production today. Opt-in preview only.
  - `duplicate` field doesn't exist in the backend schema at all — dead in both production AND the old `mockup_documents_list_v2.jsx`. **Omitted** from v3 rather than reproducing UI for a field that never has a value.
  - List API does **not** return `doc_type_group` (only legacy `doc_type`, 10 values) — confirmed real API gap vs. doc-detail's `doc_type_group` (11 values). Flagged as informational, not an open decision (API change out of scope for a visual redesign).
  - `AdminShell.tsx:21` confirmed exact `max-w-5xl` with no per-page override — demoed as **Q-Width** toggle (1024px vs 1400px comparison).
  - **`LifecycleBadge.tsx` (real, shared) also uses `bg-success-soft`** — extends #478's Q1 (ConfidenceMeter/SignatureBadge green conflict with v1.1's no-success-token philosophy) to a 3rd component. Reused v4's exact `LifecycleBadge` local component verbatim for consistency — one open question, one answer, not two mockups disagreeing.
- **4 open decisions** (all framed as dashed-callout, default-off toggles): Q1-ext (LifecycleBadge success color, tie to #478's Q1), Q-Status-Failed (real bug), Q-CompletenessIcon (dead field, needs #276 first), Q-Width (AdminShell constraint).
- No pagination proposed (app has none anywhere today, out of scope). Mobile `DocCard` view not rebuilt (unchanged pattern, not what #481 flagged).
- Awaiting Kevin review.

## Issue #478 — Doc-detail v4, 3-tab reorg on DS v1.1 — branch `claude/design-doc-detail-v4-478`
Scope: chỉ 3 tab (Tổng quan / Nội dung hợp đồng / Bên ký kết). Tab Nghĩa vụ & Quyền lợi KHÔNG đụng — đã có #466/#467/#468/#472, tránh 2 nguồn sự thật song song.
- **Delivered:** `mockup_document_detail_v4.jsx` — **import THẬT** từ `mockup_design_system_v1.1.jsx` (`tokens`, `Button`, `Card`, `Modal`, `Badge`), khác v3 (mirror token inline). Verify: esbuild bundle 2 file thành công (63.7kb), toàn bộ `t.color.*` dùng trong file đối chiếu đúng key thật trong v1.1 (không typo).
- **Research trước khi build (Explore agent, 2026-07-03):** verify field/component thật qua backend models + `DocumentDetail.tsx` + `mockup_design_system_v1.1.jsx`. Phát hiện lệch so với brief #478 gốc:
  - `Term.source` có **3 giá trị thật**: `"extracted"|"remap"|"manual"` (brief chỉ nói 2) — field này **chưa có trong API** (`TermOut` schema, backend/app/schemas/documents.py:73-84)
  - Field tên thật `contract_term` (tenant.py:57), không phải `contract_duration` (kể cả CLAUDE.md ghi nhầm)
  - `content_status` 4 giá trị thật: `NULL/"skeleton"/"filled"/"truncated"` (không phải "skeleton"/"complete"), tenant_029, 0% API + 0% frontend
  - `DocumentRelationship.relationship_type` xác nhận đúng 3 giá trị amends/references_framework/annex, 0% frontend UI
  - `clause_count` không phải cột DB — tính động qua COUNT query
  - ConfidenceMeter + SignatureBadge XÁC NHẬN đang dùng success/xanh lá thật hôm nay
  - Card "Loại hợp đồng" disabled + card "Thời hạn hợp đồng" tint xám XÁC NHẬN đúng hành vi/copy thật — dùng nguyên văn copy/tooltip gốc trong mockup
- **4 fix theo feedback Kevin:** bỏ tint xám card Thời hạn (Card mặc định v1.1); label Term đổi `ink` đậm thay `ink-muted`; rẽ nhánh `Term.source` (manual→`<Badge kind="manual">` outline có sẵn, không tự chế class — bài học #468); panel cross-ref mồ côi cap `maxHeight:160px` + nút "Xem tất cả (N) →" mở `Modal` thật từ v1.1.
- **4 quyết định mở** (3 từ PM #478 + 1 Designer tự phát hiện) — đóng khung `OpenDecisionCallout` riêng (viền đứt vàng, nhãn "chờ Kevin ratify"), mỗi callout trích file:line thật:
  1. ConfidenceMeter/SignatureBadge màu success → đổi `done`/`warning`? (v1.1 không có token success)
  2. UI cho `content_status` (two-pass) — vào scope sprint này không? (cần Backend thêm field vào `ClauseOut` trước)
  3. UI cho `DocumentRelationship` — vào scope không? (cần Backend thêm endpoint expose, hiện chưa có)
  4. (Designer tự phát hiện) `Term.source="remap"` chưa được brief nhắc — hiển thị thế nào?
- **Sample data:** cùng hợp đồng ALPHATECH ↔ Minh Phát như v3 (dễ so sánh), nhưng field shape khớp model thật 100%: 3 loại cross-ref (`clause`/`appendix`/`document`), đủ 4 giá trị `content_status`, marker stub thật `'(tổng hợp từ mục con)'`, 3 loại `DocumentRelationship`.
- **QC review (PR #480) — 3 findings, tất cả confirmed + fixed:**
  1. `content_status="skeleton"` loading text không gate theo toggle `showContentStatus` (Q2 unratified) — fix: thêm `showContentStatus &&` vào điều kiện `isLoading`, mặc định (toggle tắt) giờ hiện đúng hành vi thật hôm nay (clause rỗng, không có loading text đề xuất).
  2. Glyph `▴/▾/└` không có `aria-hidden`, nút toggle không có `aria-expanded` — dùng glyph trần thay vì đi qua `IconButton` (cơ chế a11y riêng của v1.1 cho glyph chức năng). Fix: thêm `aria-hidden="true"` trên glyph, `aria-expanded={expanded}` trên button cha (đúng hơn ép dùng `IconButton` vì các nút này đã có text label thấy được, không phải icon-only).
  3. Comment "14 orphan refs" gây hiểu lầm — sample data chỉ có 6 orphan. Fix: sửa comment nói rõ 6 orphan đủ trigger cap/overflow, case thật doc #14 (14 refs) không được tái tạo 1:1.
- Awaiting re-verify.

## Issue #467 — Obligation tab v3 reorg (parent #466, DEC-055) — branch `claude/design-obligation-tab-reorg-467`
- Full reorg of doc-detail tab "Nghĩa vụ & Quyền lợi". Replaces v2 flat list + obligation_v0.2 emoji patterns.
- **Delivered:** `mockup_obligation_tab_v3.jsx` — 3-axis IA (Direction × Temporal × Series):
  - **Q1:** SelfPartyGate per-doc REMOVED → `SettingsNudge` "Sửa pháp nhân trong Cài đặt" link
  - **Q2:** Checkbox multi-select + floating `ActionBar` "Hoàn thành đã chọn (N)"
  - **Q3:** `SeriesCard` collapsible — progress bar X/Y + "Kế tiếp: Đợt N" preview (14→1 card)
  - **Q4:** "Chờ kích hoạt" separate section — triggers + penalties with "Phạt" badge
  - **Q5:** `formatCurrency()` — parse to "130.000.000 đ" or hide entirely
  - **Q7:** ZERO emoji — all status via `TextBadge` (text + color token). Flagged obligation_v0.2 + other screens for icon cleanup.
- **IA structure:** Cần xác nhận (NULL, top) → Nghĩa vụ (Quá hạn → Tuần này → Sắp tới) → Quyền lợi → Chờ kích hoạt → Đã hoàn thành (collapsed)
- **Design tokens:** DS v0.2 canonical. "Servanda" brand voice (DEC-055).
- **Sample data:** HĐ mua bán căn hộ Sunrise Tower — 14-installment series, overdue, upcoming, triggers, penalties, NULL direction, parseable + unparseable amounts.
- **Kevin review (2026-07-03) — PASS.** Verified: 3 commits = 1 real fix (series-card dedupe, `6898cce`, landed before Kevin's review) + 1 STATE.md-only doc commit (`24a06fb`, zero code). No further mockup changes requested.
- **1 item carried forward to Frontend kickoff (gate step 4) — open decision, NOT a blocker:**
  1. **Bulk-complete has no confirm step.** `handleBulkComplete` (`mockup_obligation_tab_v3.jsx` ~L610) fires immediately on click — no `ReadbackModal`/confirm gate before marking N obligations done. Kevin: open Frontend decision, not a hard blocker — Backend endpoint shape is unaffected either way (bulk PATCH takes an ID array regardless of whether FE confirms first).
- **Phạt badge styling — FIXED (PR #468 follow-up).** PM flagged pre-merge (comment 05:23) that the mockup used v0.2-era solid fill; the fix landed in a follow-up patch AFTER #468 had already merged with the bug still present (missed because only CI status was checked before merging, not all open comments — noted for next time: always read outstanding PR comments before merge, not just checks). Now `<TextBadge fg={t.color.danger} border={t.color.danger}>Phạt</TextBadge>` — outline, transparent bg, matches `mockup_design_system_v1.1.jsx`'s `penalty` kind exactly.
- Status: Kevin-approved, QC-verified, merged (`a426e0f`) + penalty-badge follow-up fix. Gate #466 step 1-3 done — Frontend/Backend kickoff (step 4) can file.

## Inbox
- issue #24 (`for:designer`, `task-assignment`, GATING #30 + #31) — Sprint 1
  Design System + M0 mockups. Status: Phase 1 done, awaiting Kevin approve.
