# KHE_Backend — Session STATE

> Owner: **KHE_Backend** (lead: Claude Code; dev: Windsurf_Backend).
> Scope: `backend/**` — FastAPI, modules (ingest, extraction, obligation, reminders,
> firm_portal, auth, audit), alembic, scheduler. Multi-tenant: `master.db` + per-tenant.
> Lead branch: `claude/feat-backend-scaffold-nm2942`.

_Last updated: 2026-06-25 (post Sprint 1 session — ~16 PRs merged to staging, 12 issues closed)_

---

## Decisions in force

| DEC | Summary | Where |
|-----|---------|-------|
| DEC-002 | Single `VisionExtractionProvider.extract()` — no separate OCR step | extraction_runner.py |
| DEC-006 | Telegram bot for reminders (`python-telegram-bot`). Zalo deprecated for MVP. | scheduler.py |
| DEC-010 | US-hosted APIs OK Phase 1; log consent_reference before first extraction per tenant | extraction_runner.py |
| DEC-020 | Recurrence pattern: `once` / `open_ended_review` / `monthly` / `quarterly` / `yearly` | models/tenant.py |
| DEC-026 | LLM function-calling chat (Gemini 2.5 Flash) — 4 tools: search_terms, search_obligations, search_clauses, aggregate_obligations | services/chat_query.py |
| DEC-027 | `obligation_type` = category enum (8 values); `recurrence` = cadence axis | models/tenant.py |
| DEC-028 | `chat_query_log` per-tenant table — purgeable PII, separate from events ledger | models/tenant.py |
| DEC-029 | `doc_type_filter` in chat tools — exact match on `doc_type_group` Term row | services/chat_query.py |
| DEC-030 Ph1 | `direction` + `obligor` + `TenantProfile.legal_name` + `_derive_direction()` | services/extraction_runner.py |
| DEC-030 Ph2 | 4-axis obligation model: series + event-chain + T2 auto-expand + amount_raw | models/tenant.py |
| DEC-040 | `is_first_session` clears at `>= CONFIRMED` (not ACTIVATED). Nav-unlock threshold. | services/tenant_journey.py |

---

## Alembic migrations (current heads on staging)

### Master chain (head: `005`)

| Migration | Contents | PR |
|-----------|----------|-----|
| `001_initial_master` | Base: tenants, tenant_users, firm_partners, firm_tenant_access | — |
| `002_master_tenant_profile` | TenantProfile (legal_name) — DEC-030 | PR #148 |
| `003_tenant_journey_stage` | +journey_stage, is_first_session on tenants | PR #218 |
| `004_tenant_quota` | +doc_quota, docs_used_month, quota_reset_at on tenants | PR #221 |
| `005_tenant_cost_aggregate` | +cost_vnd_month, cost_vnd_total on tenants | PR #257 |

### Tenant chain (head: `tenant_014`)

| Migration | Contents | PR |
|-----------|----------|-----|
| `tenant_001_initial` | Base schema: documents, terms, obligations, parties, events, branches, employees | — |
| `tenant_002_consent_and_relationships` | Consent + relationships tables | — |
| `tenant_003_clauses` | `clauses` table (DEC-026) | PR #140 |
| `tenant_004_obligation_direction` | direction, obligor, obligation_type, recurrence, source_doc_chain, resolution_method | PR #148 |
| `tenant_005_chat_query_log` | `chat_query_log` table (DEC-028) | PR #149 |
| `tenant_006_obligation_series_chain` | +8 cols for DEC-030 Phase 2 (series + event-chain + amount_raw) | PR #162 |
| `tenant_007_chat_token_tracking` | 4 cols on `chat_query_log` (input_tokens, output_tokens, cost_vnd, llm_calls) | PR #169 |
| `tenant_008_parties_doc_role` | `parties.document_id` + `role_label` for self-party | PR #172 |
| `tenant_009_chat_sessions` | `chat_sessions` table (session state, carry-over context) | — |
| `tenant_010_obligation_snooze` | +snoozed_until on obligations | PR #221 |
| `tenant_011_term_anchor` | +ref, page_num, bbox on terms | PR #228 |
| `tenant_012_document_confirm` | +confirmed_by_user_at on documents | PR #235 |
| `tenant_013_document_extraction_cost` | +extraction_provider, extraction_tokens_in/out, extraction_cost_vnd on documents | PR #257 |
| `tenant_014_term_source` | +source on terms (extracted/remap/manual provenance) | PR #261 |

---

## New services/modules added (Sprint 1)

| File | Purpose | PR |
|------|---------|-----|
| `services/tenant_journey.py` | Journey state machine: NEW→EXTRACTING→NEEDS_REVIEW→CONFIRMED→ACTIVATED→STEADY. Monotonic forward-only + self-heal. | PR #218 |
| `services/directions.py` | DB-backed obligation direction re-derivation (`rederive_document_directions`). Bidirectional substring match. | PR #218 |
| `services/quota.py` | `try_consume_quota()` (TOCTOU-safe atomic), `add_extraction_cost()`, `reset_all_quotas()`, `get_quota_status()` | PR #221 |
| `routers/admin.py` | `GET /admin/tenants/cost-summary` — admin-only cross-tenant cost report | PR #257 |
| `modules/extraction/remap.py` | `remap_type()` — text-only Gemini Flash clause remap at ~2-3đ/doc (KHE_AI authored) | PR #261 |
| `scripts/trace_chat_uat.py` | Diagnostic trace for chat UAT — read-only dump of query_log/sessions/terms/parties | PR #269 |
| `scripts/backfill_first_session_consistency.py` | One-shot fix for tenants stuck at {>=CONFIRMED, is_first_session=True} | PR #260 |

---

## Done — merged to staging

### Sprint 0 batch (PRs #135–#177)

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
| PR #161 | #154 | KHE_AI: `payment_schedule[]` → `obligation_schedule[]` generalization |
| PR #162 | #153 | DEC-030 Phase 2: 4-axis obligation model |
| PR #169 | #164 | DEC-028 Phase 2: chat tokenomics |
| PR #172 | #155, #176 | Self-party endpoints + GET legal_name (lead takeover) |
| PR #173 | #163 | DEC-030 tail: obligation_type/trigger enum coercion |
| PR #177 | #146 | Chat obligation sources enrichment + waiting_trigger fix |
| PR #188 | #184 | LRU engine cache for tenant sessions |
| PR #189 | #185 | Scheduler benchmark + `/health/scheduler` |
| PR #190 | #183 | Reminder retry-tick reliability |

### Sprint 1 session (2026-06-23 → 2026-06-25)

| PR | Issue(s) | Summary |
|----|----------|---------|
| PR #205 | #199, #203 | Chat aggregate intent (aggregate_obligations tool) + session reset API |
| PR #218 | #213 | Journey state machine + tenant `/me` + `/me/journey` endpoints |
| PR #221 | #63, #214 | Quota guard (TOCTOU-safe) + obligation snooze + monthly reset scheduler |
| PR #224 | #217 | Chat session cleanup: daily (was weekly), configurable retention |
| PR #228 | — | Term anchor fields (ref/page_num/bbox) — extraction_runner plumbing |
| PR #229 | #233 | Expose extraction provider/model on DocumentDetailOut |
| PR #235 | #238 | Document confirm flow (`POST /{id}/confirm`) + journey advance |
| PR #241 | #238 | Confirm endpoint fix: advance journey on first confirm |
| PR #252 | #250, #249 | First-confirm gate + reminders D-02 gate (only confirmed docs) |
| PR #253 | #199 | GET /obligations/summary — dashboard aggregate with `active_only` default |
| PR #254 | #253 FE | active_only default fix for dashboard counts |
| PR #257 | #255 | Per-tenant extraction cost tracking (doc + master aggregate) + admin cost-summary |
| PR #260 | #259 | Hotfix: is_first_session at CONFIRMED (DEC-040) + self-heal backfill |
| PR #261 | #258 | POST /documents/{id}/remap-type — clause remap doc_type_group |
| PR #267 | #263 | Clause-text fallback before D-08 on entity-query router miss |
| PR #269 | #268 | Q3 plural routing few-shot fix + trace tooling for Q2 |

---

## Issues closed this session

#63, #199, #203, #213, #214, #217, #233, #238, #250, #255, #259, #263

## Issues filed this session

| # | Title | For | Notes |
|---|-------|-----|-------|
| #230 | Populate term anchors from VisionExtractionProvider | for:ai | Extraction provider should pass ref/page_num/bbox back |
| #244 | Bound self-party legal_name matcher | low-priority | Shared between directions.py + extraction_runner.py |

---

## In-flight / open

| # | Title | Status | Notes |
|---|-------|--------|-------|
| #268 | Chat Q2 — doc_hint fallback hints never resolve | **needs VPS trace** | Q3 (plural routing) shipped in PR #269. Q2 needs someone to run `scripts/trace_chat_uat.py` on VPS and post results. Backend ships fix once trace arrives. |
| #258 | Remap doc_type_group (FE wire) | **FE remaining** | Backend endpoint live (PR #261). FE "Map lại" dropdown may have shipped (#262/#266). QC test coverage done. |
| #249/#238 | Confirm button + sidebar unlock + DocList badge | **FE remaining** | Backend done (confirm endpoint, journey advance, first-confirm gate). FE needs confirm button + sidebar unlock wire. |
| #65 | Firm portal scaffold | `status:planned` | Needs PM decision on custom_quota. Depends on #63 (now done). |
| #118 | Chat catalog few-shot | `relay` | ~8 few-shot patterns already embedded in router prompt. Formal catalog for QC. |
| #230 | Populate term anchors from VisionExtractionProvider | `for:ai` | KHE_AI builds; backend plumbing ready (PR #228). |
| #244 | Bound self-party legal_name matcher | `low-priority` | Hardening: limit substring match scope in directions.py + extraction_runner.py. |
| #97 | 5 docs stuck "Đang xử lý" on staging | `status:planned` | Re-trigger extraction after staging→main promote. |

---

## Blocked

*(none)*

---

## Architectural invariants (enforce in every PR review)

- `get_tenant_session(tid)` mandatory — NEVER `SessionLocal()` directly
- Every query filters by `tenant_id`
- No raw SQL with f-string (ORM only)
- No PII in logs (party names, question text from chat_query_log — D-12)
- `python-dateutil` (and any new dep) declared directly in `requirements.txt`
- Alembic single-head enforced by `pr-quality-gate.yml`
- D-08: chat returns exact "Không tìm thấy thông tin này trong hồ sơ của bạn." — never fabricates
- D-06: extraction reads only — never generates legal content
- D-02: reminders only fire for `confirmed_by_user_at IS NOT NULL` docs (PR #252)
- D-13: obligation direction = NULL + needs_review when legal_name or obligor missing — never default to `nghĩa_vụ`
- Journey state machine: forward-only, monotonic (`services/tenant_journey.py`)
- Quota: atomic TOCTOU-safe `UPDATE ... WHERE docs_used_month < doc_quota` (`services/quota.py`)
- Entity fallback: clause-text search before D-08 only when proper-noun detected in query (PR #267)

---

## Staging → main promotion plan

**All Sprint 0 + Sprint 1 PRs on staging.** Total ~33 PRs.
**Pre-promote:** forward-merge `pr-quality-gate.yml` fix into all long-lived branches (CLAUDE.md bug pattern).
**Post-promote:** verify DOCS_INBOX entries cover all schema/API changes.
**Re-extraction needed:** re-run extraction on existing docs (esp. the 5 stuck in #97) to populate `obligation_schedule` data.

---

## DOCS_INBOX status

Multiple entries posted across Sprint 0+1 for schema, API, and architectural changes.
Key entries: DEC-030 Ph2 (#162), quota guard (#63), journey state machine (#213), cost tracking (#255), remap (#258), entity fallback (#263).
Awaiting KHE_Docs fold for Sprint 1 entries.

---

## Notes for next session

1. **#268 Q2**: Check if VPS trace has been posted. If yes, ship the hint-resolution fix.
2. **Staging → main promote**: ~33 PRs ready. Coordinate with PM + Infra.
3. **#65 firm portal**: Scaffold when PM decides on `custom_quota` field shape.
4. **#258 FE integration**: Verify remap dropdown works end-to-end once FE ships.
5. **#230**: Follow up with KHE_AI on term anchor population from extraction.
6. **Chat few-shot catalog (#118)**: Formalize the ~8 patterns already in the router prompt.
7. **DOCS_INBOX**: Post Sprint 1 batch entry covering all 16 PRs if not yet done.
