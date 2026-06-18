# KHE_Frontend_Admin — Session STATE

*Owner: KHE_Frontend_Admin lead · Branch (current feature): `claude/feat-admin-m0-screens`*
*Last updated: 2026-06-18 (session kickoff)*

---

## Role

Lead for `frontend/src/pages/{admin,firm,public}/**` + `components/`, `hooks/`, `lib/`.
Stack: React + Vite + Tailwind CSS + React Router v6. **Plan + review only — KHÔNG tự implement** (assign Windsurf_Frontend). Exception: emergency hotfix + PM approve.

## Scope-lock

- ✅ `frontend/src/pages/{admin,firm,public}/**`, `frontend/src/components/**`, `frontend/src/hooks/**`, `frontend/src/lib/**`
- ❌ `frontend/src/pwa/**` (KHE_PWA_Chat), `backend/**`, `docs/**` (canonical), `.github/workflows/**`, root `*.md`

## Session log

### 2026-06-18 — kickoff
- STEP 0: renamed auto-spawn branch `claude/sweet-carson-zsx6xp` → `claude/feat-admin-m0-screens` ✅. Synced origin/main (HEAD `d6e9079`).
- Verified all 5 admin mockups + design system v0.1 present on main (PR #36, #24 merged).
- Read API contract: Sprint 0 #23 (`POST /auth/login` body `{tenant_id, username, password}`), #25 (ingest API), #26 (obligation API).
- **FINDING:** `frontend/` directory does NOT exist yet — no Vite/React scaffold. M0 needs scaffold step before screens.
- Inbox `for:frontend`: only #31 open (EPIC M0 admin UI, was blocker:waiting-dependency on #24 — now UNBLOCKED).

### 2026-06-18 — PR #47 review (scaffold + auth, M0 part 1/2)
- Assigned #40 → Windsurf opened PR #47 (`windsurf/feat-frontend-scaffold-auth`, commit `3b40333`).
- **Contract verified vs backend:** `LoginIn {tenant_id,username,password}` + `TokenOut {access_token,token_type}` match FE types exactly — no drift.
- **Review = CHANGES REQUESTED** (posted as COMMENT — GH blocks formal request-changes on same-account PR). Blockers:
  1. 🔴 CI Frontend Build RED — `package-lock.json` gitignored → setup-node cache path unresolved. Fix: un-ignore + commit lockfile.
  2. 🔴 PR base `main` → must retarget `staging` (feature→staging→main).
  3. 🔴 Committed `vite.config.js` + `vite.config.d.ts` (tsc emit) → delete + gitignore.
  - 🟡 BadgeKind missing `neutral`; vite `/api` proxy dead config.
- Awaiting Windsurf fixes → re-review → approve/merge. NOT merged.

## Open dependencies

| Dep | Status | Note |
|---|---|---|
| #24 design | ✅ MERGED | Design system + 5 admin mockups on main |
| #25 ingest API shape | ⏳ backend in progress | `POST /ingest/upload`, `POST /ingest/bulk`, `GET /documents/{id}` — coordinate exact response shape via DOCS_INBOX |
| #26 obligation API shape | ⏳ backend in progress | `GET /obligations?due_within=N`, mark-done endpoint — coordinate shape |

## Known contract (ratified Sprint 0 #23)

- `POST /auth/login` body `{tenant_id, username, password}` → JWT `{sub, tenant_id, role, exp}`
- master.db: tenants, tenant_users, firm_partners, firm_tenant_access
- per-tenant: documents, terms, obligations, parties, events, branches, employees
- Insight: VN HĐ ghi `ngày hiệu lực + thời hạn`, không trực tiếp `ngày hết hạn` → obligation derives. UI shows derived badge (mockup already handles).
