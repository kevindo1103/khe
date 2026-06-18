# backend_STATE — KHE_Backend (ERP_Backend lead)

> Lead coordination + sprint state for the `backend/**` scope.
> Kept under `backend/` (in-scope) per scope-lock — `docs/teams/` is ERP_Docs-owned.

*Last updated: 2026-06-18 — Sprint 1 kicked off (#10 foundation)*

---

## Current sprint: Sprint 1 — Ingest + Obligation + Chat (consent-gated)

**Goal:** First live data path. Per-tenant migration rail → consent gate + doc-relationship schema → ingest → obligation/reminders → chat.

### Execution order (dependency-correct — ratified 2026-06-18)

> ⚠️ PM listed `#22 → #10` but true dependency is reversed: #22 adds columns via a per-tenant
> Alembic migration that does not exist yet. **#10 is the foundation and lands FIRST.**

| Step | Task | Issue | Branch | Status |
|---|---|---|---|---|
| 1 | Per-tenant Alembic foundation | #10 | `windsurf/feat-backend-tenant-alembic` | 🟡 **assigned** (kickoff comment posted) |
| 2 | Consent gate (NĐ 13/2023, DEC-010) | #22 | `claude/feat-backend-consent-gate` (PR-A) | ⏸ queued — owns migration `tenant_002` |
| 3 | Doc relationships (DEC-019) | (DEC-019) | `claude/feat-backend-doc-relationships` (PR-B) | ⏸ queued — builds on PR-A schema |
| 4 | Ingest router + extraction queue | #25 | `claude/feat-backend-ingest-*` | ⏸ queued — consent-gated |
| 5 | Obligation engine + reminder + Telegram | #26 | `claude/feat-backend-obligation-*` | ⏸ queued — consumes #25 Terms |
| 6 | Chat query MVP (retrieve-only, D-08) | #27 | `claude/feat-backend-chat-*` | ⏸ queued — consumes #25/#26 |

### Migration `tenant_002` — schema delta (#22 + DEC-019, **1 migration / 2 PRs**)

Decisions (Kevin, 2026-06-18): **typed columns** on `events` (Compliance ask) · **single `tenant_002`
revision, split into PR-A (consent logic) + PR-B (relationship logic)**. PR-A carries the migration file
(full delta); PR-B builds on the schema with no new migration.

- **`events`** (#22, Compliance #22 comment): `purpose` (closed enum `vision_extraction` / `reminder_send` / `firm_partner_access`) · `consent_reference` · `consent_text_version` (e.g. `nd13-v1`)
- **`document_relationships`** (DEC-019, edge n-n NEW): `from_doc_id`, `to_doc_id`, `relationship_type` (MVP `amends` / `references_framework`; defer `supersedes` / `renews` / `related`), `confirmed_by_sme` (D-02: AI suggest → SME confirm before resolve)
- **`terms`**: `overrides_term_id`, `inherited_from_doc_id`, `is_superseded`, `needs_review` (FR-EX-05)
- **`obligations`**: `source_doc_chain`, `resolution_method` (last-writer-wins by seq_order); `obligation_type` enum += `open_ended_review` (DEC-020 — phi-số → annual review nudge, no fake deadline)

**Consent gate logic** (Compliance-confirmed, #22): query `events` for `consent_logged` + `purpose=vision_extraction`
not superseded by `consent_revoked` → proceed; else `403 {"detail":"SME consent for AI extraction not recorded. Log consent first."}`.
After `extract()` → log `event_type="extraction_performed"` (US-recipient audit trail).

### 🧊 Frozen API contract — M0 part 2/2 (DOCS_INBOX #1, 2026-06-18)

Frozen for Frontend M0 (upload · list · detail · obligations). #25/#26 implementations **MUST** conform.
Full shapes in #1 comment. Key locks:

- `POST /ingest/upload` → `{doc_id, file_name, status}` · `403` if consent absent (DEC-010) · `POST /ingest/bulk` ≤20.
- `GET /documents?status&needs_review&q&page` → `{items:[{id,file_name,doc_type,status,needs_review,term_count,obligation_count,created_at}], page, page_size, total}`.
- `GET /documents/{id}` → terms as **EAV** `[{id,field_name,field_value,confidence,needs_review}]` + obligations. `PATCH /documents/{id}/terms/{term_id}` → Event (D-07).
- `GET /obligations?due_within&status&page` → list w/ `obligation_type ∈ {once,monthly,quarterly,yearly,open_ended_review}`; `open_ended_review` ⇒ `due_date=null`. `PATCH /obligations/{id}` mark-done / hoãn → Event (D-02).
- **Frozen enums:** `documents.status` = `processing|extracted|failed` (aligns mockup #36; SRS §5.1 `ready`→`extracted` reconciliation flagged to Docs). Tenant strictly from JWT. Pagination `{items,page,page_size,total}`. ISO 8601 UTC.
- **Deferred (DEC-019 PR-B, NOT M0 v1):** detail `relationships:[]`; obligation `source_doc_chain`/`resolution_method`.

### Sprint 0 — ✅ COMPLETE (closed)

- FastAPI + multi-tenant DB scaffold on `main` (`cf6d022`, promoted via `lead → staging → main` #16/#19).
- CRITICAL fix (#9/#11, PR #12): `get_db()` env-gated; `bcrypt>=4.0.0` declared direct (passlib dropped).
- Infra #20/#21: VPS dirs provisioned + long-lived-branch gate exemption. No open blockers.
- DOCS_INBOX #1 Sprint 0 fold posted 2026-06-18.

### Decisions in effect (DOCS_INBOX #1 / ratified)

- **DEC-002** — Extraction = `VisionExtractionProvider` (Gemini 2.5 Flash primary, Claude Haiku/Sonnet fallback). **Lives in `backend/modules/extraction/**` = KHE_AI scope — backend does NOT modify; consume interface only (PR #17 merged).**
- **DEC-006** — Reminder channel = **Telegram bot**, NOT Zalo ZNS.
- **DEC-010** — NĐ 13/2023: US-hosted LLM OK Phase 1; explicit consent logged to `events` before first extraction.
- **DEC-011/012** — B2B2B (firm = paying customer), concierge onboarding → bulk-ingest priority (#25).
- **DEC-019** — Document relationship = edge model (`document_relationships`), `amends` + `references_framework`, **no legal judgment**.
- **DEC-020** — Thời hạn phi-số → no fake deadline; `open_ended_review` obligation type + annual nudge.
- **DEC-021** — Orphan amendment (upload before parent) → don't block; store + flag pending link.
- **DEC-022** — Conflict UI = full per-field timeline (Sprint 2 scope, Designer #24).

### Carry-over from Sprint 0 PR #6 review (fold into feature work)

1. `get_db` tenant isolation — derive tenant strictly from `get_current_user` (scaffold falls back to `DEFAULT_TENANT_ID` in dev only).
2. bcrypt 72-byte guard at the auth boundary.

### Blockers

- None. #10 unblocks the chain; downstream assigned as predecessors merge.

---

## Architecture notes (canonical = CLAUDE.md §Multi-Tenant DB)

- `master.db`: `tenants`, `tenant_users`, `firm_partners`, `firm_tenant_access`.
- `tenants/<slug>.db`: `documents`, `terms`, `obligations`, `parties`, `events`, `branches`, `employees` (+ `document_relationships` from `tenant_002`).
- **ALWAYS** `get_tenant_session(tid)`. **NEVER** `SessionLocal()` on per-tenant data.
- **Two Alembic envs:** `alembic/` (master, `down_revision=None` at `001`) + `alembic_tenant/` (TenantBase, `tenant_001` baseline = current models). `alembic heads | wc -l` MUST = 1 per env before merge.
- Per-tenant migrations applied via `scripts/migrate_all_tenants.py` (loop over all tenants, idempotent). `init_tenant_db()` uses alembic, NOT `create_all()`.
- `python -c "import main"` must exit 0 (CI quality gate) — `main.py` at `backend/` root.

## Lead workflow reminders

- Lead does NOT self-implement feature code → assign Windsurf via `from:backend` + `for:backend` + `task-assignment` issue with `## Plan`.
- Review Windsurf PR before merge; lead does not self-merge feature PRs.
- Post-merge: if schema/API/business-rule/known-bug touched → DOCS_INBOX (#1) comment within 24h.
- Schema/router change → run `backend/scripts/regen_openapi.py` + commit `backend/openapi.json`.
- Branch hygiene: each task gets its own `claude/feat-backend-<scope>-*` (lead plan) / `windsurf/...` (dev impl). Do NOT continue on the stale scaffold branch.
