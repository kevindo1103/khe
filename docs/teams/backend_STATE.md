# KHE_Backend — Session STATE

> Owner: **KHE_Backend** (lead: Claude Code; dev: Windsurf_Backend).
> Scope: `backend/**` — FastAPI, modules (ingest, extraction, obligation, reminders,
> firm_portal, auth, audit), alembic, scheduler. Multi-tenant: `master.db` + per-tenant.
> Lead branch: `claude/feat-backend-scaffold-nm2942`.

_Last updated: 2026-06-20 (post-DEC-030 Phase 2 triage + #153 assignment)_

---

## Decisions in force

| DEC | Summary | Where |
|-----|---------|-------|
| DEC-002 | Single `VisionExtractionProvider.extract()` — no separate OCR step | extraction_runner.py |
| DEC-006 | Telegram bot for reminders (`python-telegram-bot`). Zalo deprecated for MVP. | scheduler.py |
| DEC-010 | US-hosted APIs OK Phase 1; log consent_reference before first extraction per tenant | extraction_runner.py |
| DEC-020 | Recurrence pattern: `once` / `open_ended_review` / `monthly` / `quarterly` / `yearly` | models/tenant.py |
| DEC-026 | LLM function-calling chat (Gemini 2.5 Flash) — 3 tools: search_terms, search_obligations, search_clauses | services/chat_query.py |
| DEC-027 | `obligation_type` = category enum (8 values); `recurrence` = cadence axis | models/tenant.py |
| DEC-028 | `chat_query_log` per-tenant table — purgeable PII, separate from events ledger | models/tenant.py |
| DEC-029 | `doc_type_filter` in chat tools — exact match on `doc_type_group` Term row | services/chat_query.py |
| DEC-030 Ph1 | `direction` + `obligor` + `TenantProfile.legal_name` + `_derive_direction()` | services/extraction_runner.py |
| DEC-030 Ph2 | 4-axis obligation model: series + event-chain + T2 auto-expand + amount_raw | #153 in-flight |

---

## Alembic tenant migrations (current head on staging)

| Migration | Contents | PR |
|-----------|----------|-----|
| `tenant_001_initial` | Base schema: documents, terms, obligations, parties, events, branches, employees | — |
| `tenant_002_consent_and_relationships` | Consent + relationships tables | — |
| `tenant_003_clauses` | `clauses` table (DEC-026) | #140 |
| `tenant_004_obligation_direction` | direction, obligor, obligation_type, recurrence, source_doc_chain, resolution_method | PR #148 |
| `tenant_005_chat_query_log` | `chat_query_log` table (DEC-028) | PR #149 |
| **`tenant_006_*` (NEXT)** | +8 cols for DEC-030 Phase 2 (see #153 Part 1) | #153 pending |

**Master.db migrations:**
- `master_001_*` — tenants, tenant_users, firm_partners, firm_tenant_access
- `master_002_*` — TenantProfile (legal_name) — PR #148

---

## Done — merged to staging (batch ready for staging → main)

| PR | Issue | Summary |
|----|-------|---------|
| PR #135 | — | Schema additions (parties, obligation_type enum, etc.) |
| PR #138 | — | SQLite Unicode `lower()` fix for Vietnamese diacritics |
| PR #140 | #99 | `clauses` table migration + `tenant_003_clauses` |
| PR #141 | #26 | Obligation engine PR-A (derive + CRUD) |
| PR #142 | — | Ingest pipeline wiring |
| PR #148 | #145 | DEC-030 Phase 1: direction/obligor/recurrence/TenantProfile |
| PR #149 | #119 | DEC-028: chat_query_log learning loop |
| PR #151 | #124 | DEC-029: doc_type_filter for all 3 chat tools |

**Status:** All 8 PRs on `staging`. Batch promote to `main` planned after #153 merges.

---

## In-flight

### #153 — DEC-030 Phase 2: 4-axis obligation model
**Branch:** `windsurf/feat-backend-obligation-phase2`
**Assigned to:** Windsurf_Backend
**Status:** `status:planned` — Windsurf coding

**Parts in-flight (1/3/4/5 parallel):**
- **Part 1** — Alembic migration `tenant_006_obligation_phase2`: +8 cols on obligations (milestone_series_id, milestone_index, milestone_total, milestone_trigger, trigger_condition, trigger_delay_days, trigger_obligation_id, amount_raw). Add `OBLIGATION_STATUSES` constant.
- **Part 3** — `app/services/obligation_chain.py` new: `propagate_obligation_done()`. Wire into `PATCH /obligations/{id}` (expand allowed statuses to OBLIGATION_STATUSES, add `activated_count: int = 0` to `ObligationPatchOut`).
- **Part 4** — `app/services/obligation_expander.py` new: `expand_recurring_obligations()`. Weekly APScheduler job Mon 02:00 (`run_expand_all_tenants`). Add `python-dateutil` to `requirements.txt`.
- **Part 5** — `chat_query.py` additions: `series_id` + `waiting_trigger` params to `search_obligations`, updated prompt rules.

**Part 2 — UNBLOCKED (PR #161 merged 2026-06-20):** `extraction_runner.py` mapping of `obligation_schedule[]`. Compat shim on `result.payment_schedule` keeps existing code working; Windsurf cuts over to `result.obligation_schedule` in this PR. Delete shim after confirmed green.

**Critical notes for Windsurf:**
- Migration must be `tenant_006` (tenant_005 is taken by PR #149)
- Scheduler follows `run_daily_reminder_job` tenant-loop pattern (`MasterSessionLocal → loop active tenants → get_tenant_session`)
- `python-dateutil` MUST be declared directly in `requirements.txt` (CLAUDE.md bug pattern)
- `OBLIGATION_STATUSES = ["pending", "in_progress", "partial", "done", "cancelled", "waiting_trigger"]`

---

## Blocked

*(none — #154 merged PR #161 → staging 2026-06-20)*

---

## Pending backlog (ordered by priority)

### High priority

| # | Title | Status | Notes |
|---|-------|--------|-------|
| #97 | 5 docs stuck "Đang xử lý" on staging | `status:planned` | Verify `GET /api/health/extraction` → `any_provider_configured: true`. Re-trigger extraction after #153 ships. |
| #77 | Set `ENVIRONMENT=staging/production` in deploy `.env` + `get_db` isolation hardening | `status:planned` | Originally critical multi-tenant isolation bug — partially addressed; hardening still needed. |

### Medium priority

| # | Title | Status | Notes |
|---|-------|--------|-------|
| #62 | Reminder service + Telegram + APScheduler daily job | `status:planned` `blocker:waiting-dependency` | Depends on obligation engine stable (#26 PR-A merged ✅). Unblock now. |
| #63 | Quota guard: `doc_quota` per tenant + ingest middleware + monthly reset | `status:planned` `blocker:waiting-dependency` | Required before firm portal (#65). |
| #65 | Firm portal scaffold: firm auth + quota view/set + D-10 consent gate | `status:planned` `blocker:waiting-dependency` | Depends on #63. |
| #56 | Ingest hardening: upload size limit (413) + atomic event logging | `status:planned` | Non-blocking quality; defer past #153. |

### Low priority / relay

| # | Title | Status | Notes |
|---|-------|--------|-------|
| #118 | Chat query pattern catalog | `relay` `for:backend` `for:qc` `for:docs` | Backend pick ~8 few-shot examples for `_select_tools` prompt. QC uses full catalog for test cases. |
| #96 | Chat retrieval Unicode fix + expiring_within + find_by_party | `status:planned` | **Superseded** by DEC-026 overhaul (PR #99). Close as duplicate after verifying DEC-026 covers all 3 fixes. |

### Closeable (done-staging)

| # | Title | Status | Action |
|---|-------|--------|--------|
| #99 | LLM chat query + clauses table (DEC-026) | `status:done-staging` | Close after staging → main promotes. |
| #117 | Payment-schedule obligation derivation | `status:planned` | Close after #153 Part 2 ships (absorbed). |
| #27 | Chat query MVP (Sprint 1) | `status:planned` | Superseded by #99 DEC-026. Close. |
| #26 | Obligation engine + reminder service | `status:planned` | Core shipped (PR #141, PR #148). Close; #62 tracks remaining reminder service. |

---

## Staging → main promotion plan

**Batch ready (8 PRs):** PR #135, #138, #140, #141, #142, #148, #149, #151.
**Gate:** Wait for #153 to merge to staging first (migration head alignment).
**Post-promotion:** DOCS_INBOX comment required (schema changes in PRs #148/#149/#151/#153).
**Re-extraction needed:** After #153 Part 2 ships, re-run extraction on all existing docs to populate correct `recurrence` + `obligation_schedule` data.

---

## DOCS_INBOX pending (post-merge duty)

After #153 merges:
```
### 2026-06-20 — KHE_Backend / claude/feat-backend-scaffold-nm2942
- **PR / trigger:** #153 → staging
- **Đã đụng:** backend/app/models/tenant.py, backend/app/services/obligation_chain.py,
  backend/app/services/obligation_expander.py, backend/app/services/chat_query.py,
  backend/alembic_tenant/versions/tenant_006_*
- **Thay đổi:** DEC-030 Phase 2 — 4-axis obligation model: +8 cols (series, event-chain,
  amount_raw), new OBLIGATION_STATUSES enum, obligation_chain propagation service,
  T2 weekly auto-expand scheduler, search_obligations series_id/waiting_trigger params.
- **Docs cần cập nhật:** BRD §6 (Obligation lifecycle), SRS FR-OB-*, Glossary
  (new status values + series/trigger terms), CLAUDE.md (D-rules expand for D-02 chain)
- **Ambiguity / cần PM xác nhận:** none — DEC-030 Ph2 ratified 2026-06-20
```

---

## Key invariants (enforce in every PR review)

- `get_tenant_session(tid)` mandatory — NEVER `SessionLocal()` directly
- Every query filters by `tenant_id`
- No raw SQL with f-string (ORM only)
- No PII in logs (party names, question text from chat_query_log)
- `python-dateutil` (and any new dep) declared directly in `requirements.txt`
- Migration number must be next in sequence (currently `tenant_006` is next)
- Alembic single-head enforced by `pr-quality-gate.yml`
- D-08: chat returns "không tìm thấy" — never fabricates
- D-06: extraction reads only — never generates legal content
