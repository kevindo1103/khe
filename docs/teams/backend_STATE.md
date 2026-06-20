# KHE_Backend — Session STATE

> Owner: **KHE_Backend** (lead: Claude Code; dev: Windsurf_Backend).
> Scope: `backend/**` — FastAPI, modules (ingest, extraction, obligation, reminders,
> firm_portal, auth, audit), alembic, scheduler. Multi-tenant: `master.db` + per-tenant.
> Lead branch: `claude/feat-backend-scaffold-nm2942`.

_Last updated: 2026-06-20 (#155 self-party assigned → Windsurf, contract frozen for FE #158; #164 migration bumped 007→008)_

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
| `tenant_006_obligation_series_chain` | +8 cols for DEC-030 Phase 2 (series + event-chain + amount_raw) | PR #162 |
| **`tenant_007_parties_doc_role` (NEXT)** | `parties.document_id` + `role_label` for self-party (#155, gates FE #158) | #155 assigned |
| `tenant_008_*` | chat token tracking — see #164 (bumped from 007 to avoid collision) | #164 queued |

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
| PR #161 | #154 | KHE_AI: `payment_schedule[]` → `obligation_schedule[]` generalization (+ compat shim) |
| PR #162 | #153 | DEC-030 Phase 2: 4-axis obligation model (series + event-chain + T2 expand + dedup + audit Event) |

**Status:** All 10 PRs on `staging`. Batch promote to `main` planned (gate: #163 nitpicks land first — optional).

---

## In-flight

| # | Title | Status | Notes |
|---|-------|--------|-------|
| #155 | DEC-030 self-party endpoints — legal_name + confirm_self_party + parties[] persist | assigned → Windsurf_Backend | Gates FE #158 (HIGH). Plan posted [#155 comment](https://github.com/kevindo1103/khe/issues/155). Migration `tenant_007` (extend existing `parties` table — +`document_id`/`role_label`). Contract frozen + relayed to #158 (FE soft-unblocked, building vs mocks). Branch `windsurf/feat-backend-self-party-endpoints` off staging. |

---

## Blocked

*(none)*

---

## Pending backlog (ordered by priority)

### High priority

| # | Title | Status | Notes |
|---|-------|--------|-------|
| #97 | 5 docs stuck "Đang xử lý" on staging | `status:planned` | Verify `GET /api/health/extraction` → `any_provider_configured: true`. Re-trigger extraction now #162 shipped (populates `obligation_schedule` data). |
| #77 | Set `ENVIRONMENT=staging/production` in deploy `.env` + `get_db` isolation hardening | `status:planned` | Originally critical multi-tenant isolation bug — partially addressed; hardening still needed. |

### Medium priority

| # | Title | Status | Notes |
|---|-------|--------|-------|
| #62 | Reminder service + Telegram + APScheduler daily job | `status:planned` `blocker:waiting-dependency` | Depends on obligation engine stable (#26 PR-A merged ✅). Unblock now. |
| #63 | Quota guard: `doc_quota` per tenant + ingest middleware + monthly reset | `status:planned` `blocker:waiting-dependency` | Required before firm portal (#65). |
| #65 | Firm portal scaffold: firm auth + quota view/set + D-10 consent gate | `status:planned` `blocker:waiting-dependency` | Depends on #63. |
| #56 | Ingest hardening: upload size limit (413) + atomic event logging | `status:planned` | Non-blocking quality; defer past #153. |

### Fast-follow (DEC-030 Phase 2 tail)

| # | Title | Status | Notes |
|---|-------|--------|-------|
| #163 | Obligation enum coercion + trigger/date consistency (nitpicks 3+4) | `status:planned` | Low priority. Coerce unknown `obligation_type`→`other`, `trigger`→`date`; null `due_date` when `trigger=event`. Optional gate before staging→main. |
| #164 | Chat tokenomics: token + cost tracking on ChatQueryLog | `status:planned` (was `blocker:waiting-dependency` #162 — **now unblocked**) | Migration **`tenant_008`** (bumped from 007 — #155 claimed 007). Fix spec issues first (JWT-scope stats endpoint, `cost_vnd` already exported via PR #165, plumbing). Branch off staging. |

### Low priority / relay

| # | Title | Status | Notes |
|---|-------|--------|-------|
| — | DOC/DOCX upload support | `status:planned` (no issue yet) | Convert DOC/DOCX → PDF via `libreoffice --headless` before extraction. Scope: expand `_is_pdf()` → `_validate_file_type()`, add conversion step in `_persist_upload()`, KHE_Infra cài `libreoffice-core` trên VPS. Vision providers unchanged (receive PDF bytes). |
| #118 | Chat query pattern catalog | `relay` `for:backend` `for:qc` `for:docs` | Backend pick ~8 few-shot examples for `_select_tools` prompt. QC uses full catalog for test cases. |
| #96 | Chat retrieval Unicode fix + expiring_within + find_by_party | `status:planned` | **Superseded** by DEC-026 overhaul (PR #99). Close as duplicate after verifying DEC-026 covers all 3 fixes. |

### Closeable (done-staging)

| # | Title | Status | Action |
|---|-------|--------|--------|
| #99 | LLM chat query + clauses table (DEC-026) | `status:done-staging` | Close after staging → main promotes. |

---

## Staging → main promotion plan

**Batch ready (10 PRs):** PR #135, #138, #140, #141, #142, #148, #149, #151, #161, #162.
**Gate:** Optional — let #163 (nitpicks) land first so the obligation tail is clean. Not a hard blocker.
**Pre-promote forward-merge:** ensure `pr-quality-gate.yml` fix is on all long-lived branches (`main → staging`) before opening the promote PR (CLAUDE.md bug pattern: `pull_request` workflow reads HEAD branch YAML).
**Re-extraction needed:** #162 shipped — re-run extraction on existing docs (esp. the 5 stuck in #97) to populate `obligation_schedule` data (series, event-chain, amount_raw, correct recurrence).
**Post-promotion:** DOCS_INBOX already covers PRs #148/#149/#151/#161/#162; confirm KHE_Docs folded before promote.

---

## DOCS_INBOX status

✅ **Posted 2026-06-20** for #162 (DEC-030 Phase 2) — [issue #1 comment](https://github.com/kevindo1103/khe/issues/1). Covers +8 obligation cols, OBLIGATION_STATUSES, obligation_chain/obligation_expander services, `obligation_schedule[]` cutover, dedup limitation. Awaiting KHE_Docs fold into BRD §6 (Obligation lifecycle), SRS FR-OB-*, Glossary (status values + series/trigger terms), CLAUDE.md (D-02 chain). PM ratified DEC-030 Ph2 2026-06-20 — no open ambiguity.

---

## Key invariants (enforce in every PR review)

- `get_tenant_session(tid)` mandatory — NEVER `SessionLocal()` directly
- Every query filters by `tenant_id`
- No raw SQL with f-string (ORM only)
- No PII in logs (party names, question text from chat_query_log)
- `python-dateutil` (and any new dep) declared directly in `requirements.txt`
- Migration number must be next in sequence (currently `tenant_007` is next — 006 shipped via #162)
- Alembic single-head enforced by `pr-quality-gate.yml`
- D-08: chat returns "không tìm thấy" — never fabricates
- D-06: extraction reads only — never generates legal content
