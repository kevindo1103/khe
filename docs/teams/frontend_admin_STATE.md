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

### 2026-06-19 — BUG #89 (Admin 401 on upload) → assigned Windsurf #90
- QC + Backend lead confirmed: Admin still on Bearer/localStorage; backend migrated to HttpOnly cookie (`khe_session`, #46) AFTER scaffold #47 → login stores `"undefined"`, fake-auth, upload 401. Frontend-only fix.
- Verified backend surface on staging: `/auth/login`→`LoginOut{user,tenant_id}`, `/auth/me`→`UserOut{user_id,username,tenant_id,role}`, `/auth/logout`. PWA `api.js` = reference (credentials:'include').
- Assigned **#90** `windsurf/fix-admin-cookie-auth` — 2-file migration (api.ts drop Bearer/+credentials; useAuth drop localStorage/+/auth/me) + ProtectedRoute isLoading guard + purge stale localStorage.
- **Note:** this is debt from my #47 scaffold (shipped Bearer before #46 cookie migration). Lesson: re-verify auth contract when backend changes it.
- Await Windsurf PR → review + staging verify per #89 repro.

### 2026-06-19 — #86 dep: Admin `base:'/admin/'` (DEC-025 routing)
- Infra #86 blocked on FE adding `base:'/admin/'` to vite.config (PWA→`/`, Admin→`/admin`). Verified: no base today, routes already `/admin/*`-prefixed, no BrowserRouter basename → 1-line change, no router refactor.
- **Folded into #90** (one Admin staging-readiness PR: cookie-auth + base). Commented #86 with lockstep coordination: #70 deploy/vhost fix → #90 merge → Infra nginx `/admin`+`/` blocks → joint verify.
- No PWA dep on FE side.

### 2026-06-19 — PR #91 (cookie auth) reviewed → CHANGES REQUESTED
- Frontend auth code correct (4 files: api credentials:'include', useAuth /auth/me model, types, App isLoading guard). CI green.
- 🔴 BUT branch cut from #27/#68 backend chat branch → drags 2 backend commits (chat.py/schemas/services/tests + main.py wire) NOT in scope, not on staging. Would backdoor unreviewed backend into staging. Requested rebase onto clean origin/staging keeping only frontend commit 3d1652e.
- 🟡 Missing `base:'/admin/'` (#86 dep) — requested to add in same PR.
- NOT merged. Await rebased PR → re-review.
- **Lesson:** Windsurf must branch from fresh origin/staging, not from another feature branch.

### 2026-06-19 — PR #91 rebased clean → MERGED (#89 + #86 base)
- Windsurf rebased onto clean origin/staging (dropped backend chat commits), added `base:'/admin/'`. Diff 6 files frontend-only, CI green.
- Reviewed → approved → **merged to staging** (squash `14ce575`). #89 + #90 closed.
- Admin now on HttpOnly cookie auth (resolves upload 401) + serves under `/admin` (DEC-025). Commented #86 → Infra unblocked for nginx routing.
- DOCS_INBOX #1 post-merge note posted.
- Filed **#92** chore: remove re-tracked `vite.config.js`/.d.ts artifact (low priority, after #70).
- **Still blocked on #70** (deploy-staging 0-jobs + vhost) for live e2e verify. Verify queued: /admin/login → cookie → upload 201 → refresh → logout 401.

### 2026-06-19 — DEC-025 Option A: remove base:'/admin/' (#95)
- PM locked **Option A**: Admin at `/`, PWA at `/pwa/`. PM authorized lead to implement directly (1-line change).
- Removed `base: '/admin/'` from `frontend/vite.config.ts`. Also `git rm frontend/vite.config.js` (artifact cleanup, #92).
- `npm run build` verified locally. **PR #95** → staging. CI 3/3 green.
- Updated #86 comment with corrected nginx topology (no `/admin` block needed). Posted DOCS_INBOX #1.
- **Awaiting:** merge #95 → Infra #70 deploy fix → e2e verify on staging.

### 2026-06-19 — clause_count badge relay (DEC-026 / #99) → assigned Windsurf #106
- PM relay: add `clause_count` badge. Two corrections to relay before assigning:
  1. "bundle vào vite base fix (#86)" **stale** — that PR (#95) already merged → own PR.
  2. "cạnh term_count + obligation_count **hiện có**" — those render on **list table** (DocumentList cols), NOT detail page (DocumentDetail header has no counts; DocumentDetailOut has no count fields).
- **PM decision (AskUserQuestion): Both** — DocumentList column + DocumentDetail header.
- Field sources: detail term/oblig counts derive client-side (`doc.terms.length`/`doc.obligations.length`); `clause_count` needs #99.
- **Backend gap flagged on #99:** AC only adds clause_count to `GET /documents/{id}` (detail), NOT list endpoint. List column needs `clause_count` per `DocumentListItem` → asked Backend to extend list endpoint (watch N+1). If declined, ship detail-header half alone, list-column as follow-up.
- Opened **#106** Windsurf task (`windsurf/feat-frontend-clause-count`, base staging). `blocker:waiting-dependency` on #99.

### 2026-06-19 — #99 unblocked (PR #104) → #106 detail-half unblocked, list-half still blocked
- PR #104 merged to staging: `DocumentDetailOut.clause_count` (+`failure_reason`) live on `GET /documents/{id}`. List endpoint NOT touched.
- **#106 updated:** detail-header half (3 counts: terms.length/obligations.length/clause_count) **unblocked → status:planned, ready for Windsurf.** List-column half kept blocked (no `clause_count` on `DocumentListItem`).
- Re-raised list-endpoint ask on #99: either add `clause_count` to list query (grouped COUNT, no N+1) OR defer list column to Phase 2 (narrows "Both" → detail-only). Awaiting PM/Backend call.
- Note: `failure_reason` also shipped in #104 (#79 follow-up) — added to FE types for parity, render optional.

### 2026-06-19 — PR #107 (clause_count detail header) MERGED
- Reviewed #107: 2 files FE-only (+5), types mirror backend exactly (`clause_count`/`failure_reason`), graceful `?? 0`, no DocumentList changes, CI 3/3 green, clean base staging.
- Approved (as comment — self-approve blocked) → **squash-merged `2f5c223`**. #106 closed.
- Detail header now shows 3 counts: 📋 thuộc tính · ⏰ nghĩa vụ · 📄 điều khoản.
- **List-column half:** still deferred, awaiting PM/Backend call on #99 (add `clause_count` to list endpoint vs defer Phase 2).

### 2026-06-20 — Admin chat relay (#129) → scope-gated → assigned Windsurf #131
- #129: KHE_PWA_Chat handed off `POST /chat/query` contract + D-08 + source-chip pattern for an Admin chat UI.
- **Decision Review Gate caught it:** Admin chat NOT in M0 screen set, NO Designer mockup (only `mockup_pwa_chat_v0.1`), chat is PWA's primary UX. Flagged PM before assigning.
- **PM: "proceed, no mockup."** Opened **#131** Windsurf task: NEW `pages/admin/Chat.tsx` + `types/chat.ts`, route + nav wire, reuse `apiFetch` (cookie auth), byte-exact D-08, source chip with `clause_num`, #96 limitation note. Reimplement in Tailwind/design-system (NOT import from `pwa/`).
- Backend dep #96 (unmerged): VN-filename + cross-doc queries → `found:false`. Non-blocking (single-doc queries work).
- Commented #129 ack. Await Windsurf PR → review.

### 2026-06-20 — PR #133 (Admin chat) reviewed → CHANGES REQUESTED (1 AC gap)
- Reviewed #133 (4 files FE-only, +250): NEW Chat.tsx + types/chat.ts, route + nav wire.
- ✅ D-08 byte-exact (verified), apiFetch cookie auth (no Bearer), source chip w/ clause_num, error≠not-found, Tailwind idiom (no pwa import), custom classes resolve vs config, CI 3/3, base staging.
- 🟡 **Missing AC:** #96 muted note ("tìm kiếm nâng cao đang được cải thiện") not rendered — matters during #96 gap (VN-filename query → misleading D-08). Requested one-liner + TODO-remove.
- 🟢 Nit: `scrollbar-none` is a no-op (no tailwind-scrollbar plugin). Optional.
- Posted as comment (self-approve blocked). NOT merged — await note fix → re-review + merge.

### 2026-06-20 — PR #133 (Admin chat) re-reviewed → MERGED, #131 closed
- Windsurf force-pushed `56041c2`: added #96 muted note (TODO-tagged) + replaced `scrollbar-none` with inline `scrollbarWidth:'none'`. Both review items resolved.
- Re-verified: D-08 byte-exact intact, contract unchanged, CI 3/3. Approved (comment) → **squash-merged `dc9465c`**. #131 closed, #129 acked.
- Admin chat live on staging: `/admin/chat`, "Hỏi-đáp" nav. DOCS_INBOX #1 posted (flagged: no mockup, temp #96 note, no consent gating — PM to confirm).
- **Follow-ups:** remove #96 note when backend #96 merges; confirm consent-gating intent; backfill Designer mockup if PM wants.

### 2026-06-20 — Admin login fails on staging → diagnosed /api proxy mismatch → relay #136
- User report: can't log in to Admin. Login page renders, login call fails.
- **Frontend ruled out:** routes internally consistent; `LoginRequest{tenant_id,username,password}` == backend `LoginIn` exactly (no body drift); cookie auth correct.
- **Root cause:** namespace mismatch. `deploy-staging.yml` builds Admin with `VITE_API_BASE_URL=.../api` → calls `/api/auth/login`. Backend mounts routers at ROOT (no `/api` prefix, no root_path). No nginx config in repo (VPS-side). So `/api/*` only reaches backend if nginx strips `/api` (trailing-slash proxy_pass). Missing/misconfigured → 404 or SPA fallthrough → login fails.
- Relayed **#136** (`from:frontend`+`for:infra`+`relay`+`blocker:human-needed`): nginx `/api/`→`:8001/` with cookie pass-through + SPA try_files + `/pwa/` block; Backend confirm `/api` namespace contract. Couldn't curl-probe (egress 403 in this env).
- **Blocked on Infra** for all Admin staging e2e verify.

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
