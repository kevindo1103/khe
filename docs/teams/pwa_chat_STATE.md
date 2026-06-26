# KHE_PWA_Chat — Team STATE

*Owner: KHE_PWA_Chat (lead, Claude Code) + Windsurf_PWA (dev) · Branch: `claude/feat-chat-m0-shell`*
*Last updated: 2026-06-18 — Sprint 1 kickoff · issue #32 UNBLOCKED (PR #36 merged)*

> **Role-lock:** Lead plans + assigns to Windsurf via issues, reviews PRs, does NOT self-implement (exception: PM-approved hotfix). Scope-lock HARD: only `frontend/src/pwa/**`.
> ❌ KHÔNG sửa `frontend/src/pages/admin/**` · `backend/**` · `docs/**` · `.github/workflows/**` · root `*.md`
> ❌ KHÔNG implement AI logic (KHE_AI scope) — PWA chỉ gọi API backend
> D-08 HARD: chat response không match → trả `"Không tìm thấy thông tin này trong hồ sơ của bạn."` — KHÔNG phỏng đoán

---

## Bootstrap status (2026-06-18)

| Step | Status |
|---|---|
| STEP 0 branch rename → `claude/feat-chat-m0-shell` | ✅ |
| mockups + design_system on main (PR #36) | ✅ all 5 present |
| CLAUDE.md §D-rules (D-08 critical) + Bug Patterns + Security | ✅ read |
| Sprint 0 baseline #23 (API contract) | ✅ read |
| compliance_STATE.md §A.3 (`nd13-v1` consent text) | ✅ read |
| #32 epic + 3 comments | ✅ read (UNBLOCKED per PR #36) |

**Key finding:** `frontend/` does NOT exist yet — PWA must be scaffolded from scratch (Vite + React + Tailwind, design tokens → theme config).

---

## Sprint 1 task (#32) — M0 Chat-first SME UI

4 screens theo mockup (`docs/mockup_pwa_*.jsx`, Kevin approved):

| Screen | Mockup | API dep |
|---|---|---|
| PWA shell (Vite + manifest + SW, installable) | design_system_v0.1 tokens | none |
| Login | `mockup_pwa_login_v0.1.jsx` | `POST /auth/login` |
| Chat UI + D-08 empty state | `mockup_pwa_chat_v0.1.jsx` | `POST /chat/query` (#27, planned) |
| Consent flow (nd13-v1) + Telegram opt-in | `mockup_pwa_consent_v0.1.jsx` | Consent gate (#22) |

---

## API contracts (from #23 / #27 / compliance §A)

| Endpoint | Body | Returns | Source |
|---|---|---|---|
| `POST /auth/login` | `{tenant_id, username, password}` | JWT `{sub, tenant_id, role, exp}` | #23 |
| `POST /chat/query` | `{question}` | answer + source chip; D-08 not-found string | #27 (planned) |
| consent gate | consent Event `purpose="vision_extraction"`, `consent_text_version="nd13-v1"` | 403 if missing before extract | #22 / compliance §A.2 |
| Telegram opt-in | `reminder_send` consent Event + deep-link `t.me/<bot>?start=<token>` | — | compliance §A.5, DEC-006 |

**D-08 HARD string (exact):** `"Không tìm thấy thông tin này trong hồ sơ của bạn."`
Sub-text: `"Khế chỉ trả lời từ tài liệu bạn đã tải lên — không phỏng đoán. Bạn có thể hỏi cách khác hoặc tải thêm tài liệu."`

**Consent text version:** `nd13-v1` — final VN copy in `compliance_STATE.md §A.3`. Mockup copy is DRAFT; use `nd13-v1` before go-live. Counsel/Kevin sign-off required (DEC-010).

---

## Design source (PR #36, on main)

- `docs/mockup_design_system_v0.1.jsx` — tokens (color/space/font/shadow) + 8 components → re-express as Tailwind theme.
- `docs/mockup_pwa_login_v0.1.jsx` — login + `PhoneFrame` (390×800 mobile frame).
- `docs/mockup_pwa_chat_v0.1.jsx` — chat bubbles, source chip (FR-CQ-02), D-08 EmptyState.
- `docs/mockup_pwa_consent_v0.1.jsx` — NĐ 13/2023 first-login dialog.
- `docs/mockup_pwa_notification_v0.1.jsx` — Telegram opt-in deep-link.

---

## Decisions tracked

| ID | Decision | Impact |
|---|---|---|
| DEC-006 | Telegram opt-in deep-link `t.me/?start=` | Consent flow screen |
| DEC-010 | US LLM OK với consent + audit log | Consent dialog must name Google/Anthropic |
| DEC-014 | KHÔNG claim "ký số" / "ký điện tử" | Copy review guard |
| Option C (revocation) | block future + soft-flag; obligations tiếp tục chạy | "Để sau" button logic |

---

## Open dependencies

- `#27` `POST /chat/query` — backend, `status:planned`. Chat UI build against contract + mock until live.
- `#22` consent gate endpoint — backend, CRITICAL. Consent flow POSTs the Event.
- Bot username for Telegram deep-link — from KHE_Infra (env / DEC-006).

---

## Mobile-first checklist (mỗi PR)

- [ ] Test viewport 375px trước khi push
- [ ] `npm run dev` + browser console clean (no React error, no 401/422/500)
- [ ] D-08: test manually path "không tìm thấy" trả đúng string
- [ ] PWA manifest + service worker không broken
- [ ] Consent flow: user không qua được extract trước khi consent logged

---

## Task log

| Date | Task | Issue/PR | Status |
|---|---|---|---|
| 2026-06-18 | Bootstrap: branch rename, read mockups + compliance §A.3 + #32 | spawn | ✅ done |
| 2026-06-18 | #32 M0 — scaffold frontend + 4 screens (login/consent/chat/shell) | #32 | ✅ committed |
| 2026-06-18 | Fix 3 pre-staging blockers (ConsentGuard, mock API, ConsentModal delete) | #32 | ✅ committed |
| 2026-06-18 | Security issue JWT localStorage filed | #43 | ✅ open, for:pm |
| 2026-06-18 | PR opened → staging | **PR #44** | 🔄 review |

---

*Created 2026-06-18 by KHE_PWA_Chat lead · branch `claude/feat-chat-m0-shell`.*
