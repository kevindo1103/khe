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
| 1 | Per-tenant Alembic foundation | #10 | `windsurf/feat-backend-tenant-alembic-v2` | ✅ **merged → staging** (PR #42 `11a24a9`, #10 closed) |
| 2 | Consent gate + full tenant_002 schema | #22 | `windsurf/feat-backend-tenant002-consent` (PR-A) | ✅ **merged → staging** (PR #52 `824f660`, #22 closed) |
| 3 | Doc relationships + chain logic (DEC-019/020/021) | #50 | `windsurf/feat-backend-doc-relationships` (PR-B) | 🟢 **unblocked** — schema on staging; logic only, no migration |
| 4 | Ingest core (upload/storage/CRUD/consent gate) | #25 PR-A | `windsurf/feat-backend-ingest-core` | 🟡 **assigned** — start now, no AI dep |
| 4b | Extraction worker (BackgroundTasks) | #25 PR-B | `windsurf/feat-backend-ingest-extraction` | ⏸ blocked on #53 (AI factory) + PR-A |
| 5 | Obligation engine + reminder + Telegram | #26 | `claude/feat-backend-obligation-*` | ⏸ queued — consumes #25 Terms |
| 6 | Chat query MVP (retrieve-only, D-08) | #27 | `claude/feat-backend-chat-*` | ⏸ queued — consumes #25/#26 |
| ‖ | Auth → HttpOnly cookie JWT (#43 Option A) | #46 | `windsurf/feat-backend-auth-cookie` | ✅ **merged → staging** (PR #49 `b750c5b`, #46 closed) |

> **#46 (parallel security track, runs alongside the chain):** switch JWT JSON→HttpOnly cookie.
> Linchpin = `deps.py::get_current_user` must read `khe_session` cookie **and keep setting
> `request.state.tenant_id`** (D-10/#12 chain). +`GET /auth/me` +`POST /auth/logout`, exp 24h→**8h**
> (= cookie Max-Age, single source). CORS already correct (`allow_credentials=True` + explicit origins).
> Auth **contract v2** posted to DOCS_INBOX #1 (supersedes frozen auth shape) → PWA/Admin refactor to
> `credentials:"include"` + `/auth/me`. Deps: HTTPS-on-staging + explicit `CORS_ORIGINS` env → Infra #45 (items 3-4).

### ⚠️ Branch-base rule (locked 2026-06-18 after PR #41)

**All Sprint 1 feature branches MUST base off `staging`, NOT `claude/feat-backend-scaffold-nm2942`.**
The scaffold branch is the defunct Sprint-0 lead branch (`6ea2ad9`) — it never received PR #12, so it
carries the pre-#12 `get_db()` (silent `DEFAULT_TENANT_ID` fallback = D-10 regression). PR #41 hit exactly
this: rebasing onto `staging` (which has the #12 fix) is required before merge. Flow = `feature → staging → main`.

### PR #42 (#10) — ✅ MERGED → staging 2026-06-18

- Replaced PR #41 (closed). Branched from `staging` → `get_db()` D-10 untouched; alembic Config paths anchored to `backend/` (CWD-safe). Quality Gate green; lead-merged squash `11a24a9`.
- Per-tenant Alembic rail live: `alembic_tenant/` env + `tenant_001` baseline + idempotent `migrate_all_tenants.py`. Sprint-0 carry-over #3 (per-tenant migration loop) CLOSED.
- **Follow-ups (non-blocking):** Infra #45 (wire `migrate_all_tenants.py` into `deploy-*.yml` + triage deploy failures) · nits 3-5 (server_default mirror, single-source path helper, rail regression test → KHE_QC).
- DOCS_INBOX #1 report posted (SRS §5 + CLAUDE.md Alembic/Multi-Tenant sections).

### PR #41 review (#10) — CHANGES REQUESTED 2026-06-18 (superseded by #42)

- 🔴 **Blocker:** stale base regresses #12 D-10 `get_db`. Rebuild on `staging`, reapply alembic additions only, retarget base → `staging`.
- 🟠 **Should-fix:** alembic `Config("alembic_tenant.ini")` is CWD-relative → breaks runtime `init_tenant_db()` tenant provisioning. Anchor paths to `__file__` (BACKEND_DIR).
- 🟡 Nits: baseline `server_default` vs model `default=` drift · duplicate tenant-db-path derivation · no rail regression test.
- Alembic rail itself ✅ (tenant_001 matches models, idempotent runner, baseline-stamp). Re-verify on rebase: `alembic_tenant heads==1`, `import main`, smoke 4/4, `get_db()` diff-clean vs staging.

### Migration `tenant_002` — schema delta (#22 + DEC-019, **1 migration / 2 PRs**)

Decisions (Kevin, 2026-06-18): **typed columns** on `events` (Compliance ask) · **single `tenant_002`
revision, split into PR-A (consent logic) + PR-B (relationship logic)**. PR-A carries the migration file
(full delta); PR-B builds on the schema with no new migration.

- **`events`** (#22, Compliance #22 comment): `purpose` (closed enum `vision_extraction` / `reminder_send` / `firm_partner_access`) · `consent_reference` · `consent_text_version` (e.g. `nd13-v1`) · `channel` (`telegram`/`email`) · `channel_target_ref` — all nullable; **reuse existing `actor` col** (no `created_by`); consent event uses `entity_type="consent"`, `entity_id=<actor id>` to satisfy existing NOT-NULL `entity_id` (avoids a column alter). **tenant_002 = additive only** (`add_column` + `create_table`, no `batch_alter_table`).
- **`document_relationships`** (DEC-019, edge n-n NEW): `from_doc_id`, `to_doc_id`, `relationship_type` (MVP `amends` / `references_framework`; defer `supersedes` / `renews` / `related`), `confirmed_by_sme` (D-02: AI suggest → SME confirm before resolve)
- **`terms`**: `overrides_term_id`, `inherited_from_doc_id`, `is_superseded`, `needs_review` (FR-EX-05)
- **`obligations`**: `source_doc_chain`, `resolution_method` (last-writer-wins by seq_order); `obligation_type` enum += `open_ended_review` (DEC-020 — phi-số → annual review nudge, no fake deadline)

**Consent gate logic** (Compliance-confirmed, #22): query `events` for `consent_logged` + `purpose=vision_extraction`
not superseded by `consent_revoked` → proceed; else `403 {"detail":"SME consent for AI extraction not recorded. Log consent first."}`.
After `extract()` → log `event_type="extraction_performed"` (US-recipient audit trail).

### Parallel tracks active 2026-06-18 (post tenant_002)

- **#25 PR-A** ingest core — assigned, off staging, no external dep. **#25 PR-B** extraction worker — blocked on **#53** (KHE_AI `get_extraction_provider()` factory — none exists today, only Protocol + 3 concrete providers) + PR-A.
- **#50 PR-B** relationships/chain — assigned, off staging, runs parallel to #25 (independent files; build with fixtures, wire into ingest later).
- **#53** `for:ai` provider factory — ✅ delivered by KHE_AI (`aa3a696`, branch `claude/feat-ai-vision-extraction-3k3gup`). Contract APPROVED: `get_extraction_provider(prefer="gemini_flash") -> VisionExtractionProvider`, lazy keys, `ExtractionUnavailable(RuntimeError)`, fallback advances only on `is_error` (bills once), + new `ExtractionResult.is_error` (warnings & 0 input tokens) for PR-B status mapping. **Awaiting:** KHE_AI opens PR → `staging` (clean diff). #53 closes when factory on staging → then #25 PR-B unblocked. Confirm-back asked: all 3 providers route hard failures via `empty_result()` (warning+0 tokens) so `is_error` is reliable.
- **Infra #45** — ✅ CLOSED. PR #48 wired `migrate_all_tenants.py` + `CORS_ORIGINS=https://staging.khe.iceflow.cloud` + HTTPS-check; deploy "failures" were phantom 0-job runs (not real). Forward-merge `main→staging` landed (staging YAML now `b5ecdac` = main). Staging host = `staging.khe.iceflow.cloud` (resolves #23 domain ambiguity). **Remaining ops gate:** certbot/TLS on that host → blocks browser cookie-auth (#46) end-to-end validation until installed (HTTPS-check warns meanwhile).
- **Field-name correction** posted to #1: vocab = extraction `CANONICAL_FIELDS` (7: `doi_tac, ngay_hieu_luc, ngay_het_han, gia_tri_hd, thoi_han_hd, dieu_khoan_gia_han, dieu_khoan_thanh_toan`); `doc_type` = DocType enum (`hd_thue_mat_bang|hd_nha_cung_cap|hd_lao_dong|khac`).

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
