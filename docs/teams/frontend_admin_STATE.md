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
- Windsurf pushed fixes (commit `8b0ccbc`): lockfile committed, base→staging, artifacts removed, +neutral badge, dead proxy dropped. All 3 CI checks green.
- Re-reviewed → approved on merits. **PR #47 MERGED to `staging`** by Kevin (20:46). #40 CLOSED.
- Post-merge: DOCS_INBOX #1 comment posted (frontend stack realized, login contract no-drift, lockfile-gitignore bug-pattern candidate, CLAUDE.md §Local dev now fillable).
- **Next:** part 2/2 (upload, list, detail, obligations) blocked on #25/#26 response-shape freeze. Open Windsurf task once shapes confirmed on DOCS_INBOX. EPIC #31 stays open.

### 2026-06-19 — M0 part 2/2 planned (#67)
- #25/#26 merged to `staging`. Read backend schemas/routers directly (source of truth).
- **Status-vocab ambiguity RESOLVED:** obligation status = `{pending, done, cancelled}`; urgency buckets FE-derived from `due_date`; no snooze endpoint. Posted to DOCS_INBOX #1 (suggest SRS/BRD align).
- Opened **#67** (Windsurf task) with full verified contract embedded. Branch `windsurf/feat-frontend-m0-screens`, base `staging`.
- Flagged 2 minor backend UX gaps (no doc name on ObligationOut; no party/expiry on DocumentListItem) — non-blocking, FE workarounds in #67.
- **Awaiting:** Windsurf PR for #67 → review.

## Verified API contract (staging, #25/#26)

**Ingest:** `POST /ingest/upload` (multipart `file`, opt `doc_type`) → `{doc_id,file_name,status}`, 403 if no consent · `POST /ingest/bulk` (multipart `files[]` ≤20) → `{count,documents[]}`
**Documents:** `GET /documents/?status=&needs_review=&q=&page=&page_size=` → `{items:[{id,file_name,doc_type,status,needs_review,term_count,obligation_count,created_at}],page,page_size,total}` · `GET /documents/{id}` → `{...,file_url,terms:[{id,field_name,field_value,confidence,needs_review}],obligations:[]}` · `GET /documents/{id}/file` · `PATCH /documents/{id}/terms/{term_id}` body `{field_value}` (D-07)
**Obligations:** `GET /obligations/?due_within=&status=&page=&page_size=` → `{items:[{id,document_id,description,obligation_type,due_date,status,remind_before_days,source_doc_chain,resolution_method,created_at}],...}` · `PATCH /obligations/{id}` body `{status∈{pending,done,cancelled}}` → `{ok,obligation}`

### 2026-06-19 — M0 data screens MERGED (#69), EPIC #31 CLOSED
- Reviewed PR #69 (4 screens + types + multipart api). CI 3/3 green, base staging, contract-accurate.
- **Approved + merged to `staging`** (squash `66ffca9`). #67 + EPIC #31 closed.
- M0 admin UI complete: auth + upload + list + detail (D-07 edit) + obligations (buckets + mark-done).
- Non-blocking polish noted on #69: search debounce, wire/remove "Hủy" (→cancelled), confirm backend clears needs_review on term patch (asked Backend on DOCS_INBOX #1).
- **Next frontend work:** firm partner portal `pages/firm/**` (FR-FP, D-09/D-10 consent) when scheduled. No open `for:frontend` tasks.

### 2026-06-19 — staging not serving frontend → relayed to Infra (#70)
- User screenshot: `staging.khe.iceflow.cloud` shows default nginx page (domain resolved = iceflow.cloud, not khe.vn).
- Diagnosis (read-only, infra scope — did NOT edit workflows/nginx):
  1. `deploy-staging.yml` last 3 runs failed at startup, **0 jobs** (run #102 `27808283740` after #69). Deploy job (`environment: staging`) never runs → frontend dist never rsynced.
  2. No nginx vhost for staging host → default site serving. Needs root `/opt/khe/frontend-staging` + SPA try_files + `/api/`→:8001 proxy.
- Frontend code healthy/merged — purely deploy/infra. Relayed **#70** (`from:frontend`+`for:infra`+`relay`+`blocker:human-needed`).
- **Blocked on Infra** for staging verification. Will e2e-verify once routing up.

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
