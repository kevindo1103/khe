# backend_STATE — KHE_Backend (ERP_Backend lead)

> Lead coordination + sprint state for the `backend/**` scope.
> Kept under `backend/` (in-scope) per scope-lock — `docs/teams/` is ERP_Docs-owned.

*Last updated: 2026-06-11 — Sprint 0 scaffold merged*

---

## Current sprint: Sprint 0 — Infrastructure bootstrap

**Goal:** Unblock all feature sessions. FastAPI + multi-tenant DB scaffold.

### Active tasks

| Task | Issue | Owner | Status |
|---|---|---|---|
| FastAPI + multi-tenant DB skeleton | #2 / #4 (PR #6) | Windsurf_Backend | ✅ `done` — merged to lead branch `7236ff6`, all 5 exit criteria lead-verified |

### Promote path (ratified 2026-06-11): `lead → staging → main`

| Step | Status |
|---|---|
| 1. Infra sync `staging ← main` (staging stale + no CI workflows) | **BLOCKED on Infra #15** (`blocker:waiting-dependency`) |
| 2. PR `claude/feat-backend-scaffold-nm2942` → `staging` (CI gate runs) | waiting on step 1 |
| 3. Verify on staging → promote `staging → main` | waiting |
| 4. DOCS_INBOX (#1) report within 24h of main merge | waiting |

### Pre-main blockers — RESOLVED

| Task | Issue | Status |
|---|---|---|
| Fix `get_db()` env-gated fallback (CRITICAL #9) + passlib removal + ERP branding | #11 / PR #12 | ✅ merged `a950595`, #9+#11 closed |

### Sprint 1 carry-over (from PR #6 review — DO in feature work, not scaffold)

1. **`get_db` tenant isolation** — couple `get_db` to `get_current_user` so tenant is derived strictly from the authenticated user (current scaffold falls back to `DEFAULT_TENANT_ID`).
2. **bcrypt 72-byte guard** at the auth boundary.
3. **Per-tenant Alembic loop** — scaffold bootstraps tenant tables via `create_all`; replace with versioned per-tenant migrations applied across all tenants.

### Decisions in effect (from DOCS_INBOX #1)

- **DEC-006** — Reminder channel = **Telegram bot** (python-telegram-bot), NOT Zalo ZNS. No OA approval needed.
- **DEC-002** — Extraction = single `VisionExtractionProvider` (Gemini 2.0 Flash primary, Claude Haiku/Sonnet fallback). **Lives in `backend/modules/extraction/**` = KHE_AI scope — backend does NOT touch; coordinate interface via PM.**
- **DEC-010** — NĐ 13/2023: US-hosted LLM API OK Phase 1; SME explicit consent logged to `events` before first extraction call.
- **DEC-011/012** — B2B2B (firm = paying customer), concierge onboarding. Sprint 1 priority: bulk-ingest (batch upload + extraction queue). Sprint 0 scope unchanged.

### Blockers

- None for Sprint 0 scaffold.

---

## Architecture notes (canonical = CLAUDE.md §Multi-Tenant DB)

- `master.db`: `tenants`, `tenant_users`, `firm_partners`, `firm_tenant_access`.
- `tenants/<slug>.db`: `documents`, `terms`, `obligations`, `parties`, `events`, `branches`, `employees`.
- **ALWAYS** `get_tenant_session(tid)`. **NEVER** `SessionLocal()` on per-tenant data.
- Alembic chain: first migration `down_revision = None` (master.db foundation). `alembic heads | wc -l` MUST = 1 before any PR merge.
- `python -c "import main"` must exit 0 (CI quality gate) — `main.py` at `backend/` root.

## Lead workflow reminders

- Lead does NOT self-implement feature code → assign Windsurf via `from:backend` + `for:backend` + `task-assignment` issue with `## Plan`.
- Review Windsurf PR before merge; lead does not self-merge feature PRs.
- Post-merge: if schema/API/business-rule/known-bug touched → DOCS_INBOX (#1) comment within 24h.
- Schema/router change → run `backend/scripts/regen_openapi.py` + commit `backend/openapi.json`.
