# backend_STATE — KHE_Backend (ERP_Backend lead)

> Lead coordination + sprint state for the `backend/**` scope.
> Kept under `backend/` (in-scope) per scope-lock — `docs/teams/` is ERP_Docs-owned.

*Last updated: 2026-06-10 — Sprint 0 kickoff*

---

## Current sprint: Sprint 0 — Infrastructure bootstrap

**Goal:** Unblock all feature sessions. FastAPI + multi-tenant DB scaffold.

### Active tasks

| Task | Issue | Owner | Status |
|---|---|---|---|
| FastAPI + multi-tenant DB skeleton | #2 → Windsurf task | Windsurf_Backend | `planned` (assignment posted) |

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
