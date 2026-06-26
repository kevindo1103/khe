# KHE_Frontend_Admin — Team State

**Last updated:** 2026-06-26
**Branch:** `claude/chore-admin-lead-setup-5kaczt`
**Role:** Lead (Claude Code) — plan + review, no direct implementation

---

## Current Status

**Phase:** Pre-scaffold. Frontend directory does not exist yet. Backend has auth API only (`POST /auth/login`).

**Mockups available (Kevin-approved):**
- `docs/mockup_admin_login_v0.1.jsx` — `/auth/login`
- `docs/mockup_admin_upload_v0.1.jsx` — `/admin/upload`
- `docs/mockup_admin_document_list_v0.1.jsx` — `/admin/documents`
- `docs/mockup_admin_document_detail_v0.1.jsx` — `/admin/documents/:id`
- `docs/mockup_admin_obligation_v0.1.jsx` — `/admin/obligations`

**Backend API verified:**
- `POST /auth/login` — body: `{ tenant_id, username, password }` → `{ access_token, token_type }`
- JWT payload: `{ sub: username, tenant_id, role }`
- Other module routers (documents, obligations, etc.) not yet scaffolded

---

## Open Issues (for:frontend)

| # | Title | Priority | Status | Blocked? |
|---|-------|----------|--------|----------|
| 285 | Doc list v2 obligation-centric redesign | High | planned | Yes — #279 backend |
| 276 | Honest completeness flag | P1 | planned | Backend piece needed |
| 273 | Obligations on unconfirmed docs overdue | Med | decision-review | PM decision |
| 270 | Firm Portal BA | Med | decision-review | PM decision |
| 265 | Chat cardinality-tiered response | Low | decision-review | PM decision |
| 264 | Chat "ban cung co the hoi" chips | Low | planned | Designer needed |
| 262 | doc_type_group remap dropdown | Med | done-staging | — |
| 258 | doc_type_group correction BA | Med | decision-review | PM decision |
| 251 | Persistent unconfirmed counter | Med | done-staging | — |
| 249 | Journey gate first-doc-confirmed | High | planned | PM decision (spec-conflict) |
| 238 | Journey stage stuck NEEDS_REVIEW | CRITICAL | planned | PM decision (blocker:human-needed) |
| 227 | Admin v0.2 screens handover | Med | relay | — |
| 222 | Journey-Home follow-ups | Low | waiting-dependency | — |
| 208 | Design mockups handover | Med | relay | — |

---

## Next Actions

1. **Scaffold frontend project** — React + Vite + Tailwind CSS + React Router v6 (assign to Windsurf_Frontend)
2. **Implement login page** — first screen, matches mockup + verified backend schema
3. **Coordinate with KHE_Backend** on missing module APIs (documents, obligations, upload)

---

## Known Risks

- Backend only has auth router; document/obligation/upload APIs not yet available
- 6 issues pending PM decision-review — may change requirements
- #238 is CRITICAL UX blocker (journey stage stuck)
