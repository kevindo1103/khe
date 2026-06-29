# SRS — Khế MVP (Software Requirements Specification)

> Technical contract spec. Drives backend/frontend implementation. Pairs with `MVP_BRD_Khe_v0.1.md` (business intent) — SRS is the **how**.

---

## Document control

| Mục | Nội dung |
|---|---|
| Phiên bản | v0.6 |
| Trạng thái | Fold cycle 6 — DEC-049 hybrid OCR + DEC-050 R1-R10 EPIC #362 production (PR #402) |
| Owner | KHE_Docs |
| Source of truth | BRD v0.9 (`MVP_BRD_Khe_v0.1.md`) — SRS không định ra business rule mới |

---

## Changelog

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| v0.1 | 2026-06-11 | KHE_Docs | Initial. Fold Sprint 0 backend scaffold: API contract `/auth/login` + `/health`, JWT claims, master.db (4 bảng) + per-tenant (7 bảng) schema. Fold FR-OB-01 derivation rule (entry 9). |
| v0.2 | 2026-06-19 | KHE_Docs | Cycle 3 fold (5 Backend + 1 AI + 1 PM comments). Add §2 ingest/documents/relationships API (PR #54 + #59 + #60 — staging live). Add §4 tenants quota columns (FR-TN). Update §5.2 terms CANONICAL_FIELDS 7 + §5.1 doc_type enum. Add §5.8 `document_relationships` table. Add §9 Extraction module API (`get_extraction_provider` factory, `ExtractionUnavailable`, `is_error` vs `needs_review`). Add §10 Audit Events (`extraction_performed` w/ `consent_reference`, term `updated` PII). |
| v0.3 | 2026-06-19 | KHE_Docs | **DEC-026 fold (PRIORITY gate Backend #99 issue #100).** Add §5.9 `clauses` table per-tenant (`doc_id` FK CASCADE, `clause_num`, `title`, `content`, `page_num`; idx_clauses_doc; migration `tenant_003_clauses.py` down_revision `tenant_002`). Populated từ `VisionExtractionResult.clauses[]` (same vision call). Powers `search_clauses` tool in FR-CQ-02. |
| v0.4 | 2026-06-20 | KHE_Docs | **Cycle 4 fold.** §2 +`/obligations` GET/PATCH (PR #64), +`/chat/query` POST (PR #68), +`/reminders/test` (PR #66), +`/health/extraction` (PR #80 non-prod). §4 +`tenant_profile` table (Kevin choice: separate model, NOT tenants column — DEC-030 legal_name storage). §5.3 obligations schema rewrite: rename `obligation_type` (cadence) → `recurrence`; new `obligation_type` (category enum 8 per DEC-027); +`direction`, +`obligor`, +`source_doc_chain`, +`resolution_method`; status enum corrected to `{pending,done,cancelled}`. §5.2 terms expanded to 12 CANONICAL_FIELDS + type-specific via NamedExtractedField (DEC-029). §5.10 NEW `parties` schema with role_label (DEC-030). §6 +6.3 payment_schedule derivation (DEC-027), +6.4 direction derivation (DEC-030). §9 2-tier extraction schema (Claude lean / Gemini full). §10 +chat_query_logged Event (DEC-028 compliance debt) + reminder_*. |
| v0.6 | 2026-06-29 | KHE_Docs | **Cycle 6 fold — DEC-049 hybrid OCR + DEC-050 R1-R10 EPIC #362 production (PR #402 staging→main).** §2 NEW admin endpoints (`/admin/extraction-metrics` + summary, super-admin gated via `SUPERADMIN_USERS` env). §2 NEW document detail endpoints expansion: GET/PATCH definitions, GET/POST cross-refs, GET parties extended, GET clauses with hierarchy. §2 PATCH `/documents/{id}` D-07 editable title/contract_number. §5.1 documents +10 cols (title, contract_number, signing_date, commencement_date, contract_duration, lifecycle_status, has_signature, signature_pages, extraction_model/latency_ms/warnings, processing_stage/progress). §5.4 parties +6 cols (address, representative, tax_code, is_self, aliases). §5.9 clauses hierarchy +3 cols (parent_id, level, clause_path). §5.10 NEW `definitions` table (R9). §5.11 NEW cross-ref storage (R10 — verify exact shape). §5.12 `document_relationships.relationship_type` enum extended +`annex`. §9 extraction module +hybrid_ocr provider (DEC-049). §9 schema v3 (CANONICAL 12→15: +tieu_de_hd/so_hop_dong/ngay_khai_truong; ClauseItem +level/clause_path; PartyItem +address/representative/tax_code; new DefinedTermItem + CrossReferenceItem; has_signature/signature_pages flags). Migrations: tenant_019-028. |
| v0.5 | 2026-06-27 | KHE_Docs | **Cycle 5 fold — DEC-048 EPIC #300 production.** §2.7 PATCH /obligations expanded (fulfilled_at/by/evidence_doc_ids; awaiting_confirmation status). §2.12 NEW endpoints: PATCH /documents/{id}/clauses/{clause_id} (clause edit + original_content snapshot, PR #325 migration tenant_018), POST /documents/{id}/reread (clause-scoped re-derive diff-confirm D-02, PR #326), POST /documents/{id}/re-derive-clause (PR #303 tenant_017), GET /documents/{id}/clauses (PR #320), GET /documents/{id}/events (PR #323 audit). §5.1 documents +`is_evidence` BOOL. §5.3 obligations REWRITE: +fulfilled_at/by/evidence_doc_ids, status enum +awaiting_confirmation +waiting_trigger, +source_clause_num, +derived_from, +source (P1). §5.9 clauses +`original_content` immutable +`edited_by_user` +`edited_at` (tenant_018). §6.5 NEW cascade chain anchor rule (fulfilled_at G1). §6.6 NEW date-anchored resolver (FR-OB-13). §6.7 NEW P1 source-aware merge + derive delete path-2 guard. §10 Audit Events +obligation_fulfilled/reverted, cascade_triggered, clause_edited (PII-safe), evidence_attached, obligation_date_resolved, re_read_triggered. |
| v0.4.1 | 2026-06-20 | KHE_Docs | **Cycle 4.1 fix-up fold** (2 entries: Backend lead response + PR #138). §4.5 `tenant_profile` → `tenant_profiles` (plural) với Backend lead exact spec (`id` integer PK + `tenant_id` UNIQUE FK). §6.3 staging caveat: PR #141 `obligation_type="once"` pre-#145, flip post-migration. §3.3 SQLite Unicode `lower()` override (PR #138) for VN diacritics support. |

---

## 1. Scope

SRS này pin-down **technical contract** cho MVP Khế: schema DB, API contract, derivation rules, security boundary. Mọi requirement business-level vẫn ở BRD; SRS chỉ định cách implement chúng để các session backend/frontend đồng bộ.

**Out of scope:** UX flow chi tiết (mockup), deploy pattern (CLAUDE.md §Deploy), provider selection (decisions docs).

---

## 2. API Contract — Sprint 0 baseline

### 2.1 `POST /auth/login`

Yêu cầu login đa-tenant. Body **bắt buộc** chứa `tenant_id` (slug). Một username giống nhau có thể tồn tại ở nhiều tenant — `tenant_id + username` là khóa lookup.

**Request body** (JSON):
```json
{
  "tenant_id": "sme-abc-restaurant",
  "username": "admin",
  "password": "<plaintext>"
}
```

**Response 200** (JSON):
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

**JWT payload claims:**
- `sub`: username
- `tenant_id`: tenant slug
- `role`: `staff` | `manager` | `admin`
- `exp`: expiry (Unix timestamp)

**Errors:**
- `401` — invalid credentials hoặc tenant không tồn tại
- `403` — user `is_active=false`
- `422` — missing `tenant_id` / `username` / `password`

**Note (KHE_Backend, ambiguity):** Login identifier shape có thể đổi sang email→tenant lookup ở giai đoạn sau (out of Sprint 0). Frontend MUST gửi `tenant_id` rõ ràng cho MVP.

### 2.2 `GET /health`

Liveness probe (no auth).

**Response 200:**
```json
{ "status": "healthy" }
```

### 2.3 `GET /`

Root endpoint — service metadata (name, version). No auth.

### 2.4 Ingest endpoints — M0 (Backend PR #54, staging live `badfd32`)

Auth: cookie-based (per Backend M0 frozen contract).

#### `POST /ingest/upload`
Multipart: `file` (required), `doc_type?` (optional, see DocType §5.1).
- **201:** `{doc_id, file_name, status: "processing"}`
- **403:** no `vision_extraction` consent for tenant
- **429:** quota exceeded (FR-TN-01) — hard block, no extraction proceeds
- **Side effect (PR #60):** FastAPI `BackgroundTasks` schedules `run_extraction(doc_id, tenant_id, doc_type)` after 201 response. Status `processing → extracted | failed` poll-able via §2.5.

#### `POST /ingest/bulk`
Multipart: `files[]` (≤20 — `422` otherwise).
- **201:** `{count, documents: [{doc_id, file_name, status}, ...]}`
- Same 403/429 semantics as `/upload`. Each file scheduled independently.

### 2.5 Document endpoints (Backend PR #54)

#### `GET /documents?status&needs_review&q&page&page_size`
Filter + paginate. Default `page=1, page_size=20`.
- **200:** `{items: [{id, file_name, doc_type, status, needs_review, term_count, obligation_count, created_at}], page, page_size, total}`
- `obligation_count` returns `0` until issue #26 (FR-OB) lands.

#### `GET /documents/{id}`
- **200:** `{id, file_name, doc_type, status, needs_review, file_url: "/documents/{id}/file", terms: [...], obligations: [], created_at}`
- `terms[]`: `{id, field_name (CANONICAL_FIELDS §5.2), field_value, confidence, needs_review}`
- `obligations[]` empty until #26.

#### `GET /documents/{id}/file`
Streams PDF bytes (original file).

#### `PATCH /documents/{id}/terms/{term_id}`
Body: `{field_value}` — updates term, clears `needs_review=false`, logs `Event(event_type="updated", entity_type="term", payload={"old", "new"})`.
- **D-07 enforcement:** every edit ghi Event với old/new values.
- **⚠️ Compliance flag (Backend PR #54):** Event `payload.old/new` carries extracted contract values = **PII** in append-only `events` ledger. Intended NĐ 13/2023 audit trail (who-changed-what), retained per policy. Approved data-flow.

### 2.6 Document relationships (Backend PR #59, DEC-019/020/021)

#### `GET /documents/{id}/relationships`
- **200:** `{items: [{id, from_doc_id, to_doc_id, unresolved_ref, relationship_type, status, confirmed_by_sme, confidence, created_at}]}`
- `relationship_type`: `"amends"` | `"references_framework"`
- `status`: `"pending"` (AI suggested) | `"confirmed"` (SME ratified per D-02)

#### `PATCH /documents/{id}/relationships/{rel_id}`
Body: `{confirmed_by_sme: true}` — only `true` accepted.
- **200:** confirms + triggers `resolve_chain` (last_writer_wins overrides terms across amends topology, writes `is_superseded` / `overrides_term_id` / `inherited_from_doc_id` / `source_doc_chain`).
- **400:** `{confirmed_by_sme: false}` rejected (one-way confirm).
- **404:** cross-tenant or not-found.

### 2.7 Obligation endpoints (Backend PR #64)

#### `GET /obligations?due_within=<days>&status=<…>&doc_type_filter=<group>&direction=<…>&due_from=<iso>&due_to=<iso>&page&page_size`
- **200:** `{items: [{id, document_id, description, obligation_type, recurrence, due_date, status, direction, obligor, remind_before_days, source_doc_chain, source_clause_num, derived_from, source, fulfilled_at, fulfilled_by, evidence_doc_ids, ...}], page, page_size, total}`
- `due_within` forward-only (`due_date >= today`); excludes `awaiting_confirmation` + `waiting_trigger` + `fulfilled_at IS NOT NULL` (FR-RM-07).
- `status` extended (DEC-048): `pending` | `done` | `cancelled` | `awaiting_confirmation` (cascade-past D-02) | `waiting_trigger` (FR-OB-13 unresolved date anchor).
- `direction` (DEC-030): `nghĩa_vụ` / `quyền_lợi` / `null`.

#### `PATCH /obligations/{id}` (DEC-048 expanded — PR #311 + #335)
Body now accepts fulfillment fields:
```json
{
  "status": "done",
  "fulfilled_at": "2026-06-25T14:30:00",
  "fulfilled_by": "Nguyễn Văn A",
  "evidence_doc_ids": [42, 43]
}
```
- Status-only edit (legacy) still supported: `{status: "pending"|"done"|"cancelled"|"awaiting_confirmation"}`.
- **Side effects:** Event `obligation_fulfilled` (with `purpose=obligation_fulfillment`, no consent gate per KHE_Compliance §A.1); if obligation is parent in cascade chain → `propagate_obligation_done()` activates children with anchor = `fulfilled_at` (G1 fix); backfill child due < today → child `awaiting_confirmation` + `cascade_triggered` Event.
- Revert (status `done` → `pending` or `cancelled`): `obligation_fulfillment_reverted` Event; child cascade rolled back conservatively.
- **200:** updated row + Events logged.
- **400:** invalid status, `fulfilled_at` future. **404:** cross-tenant.

### 2.8 Chat query (Backend PR #68, refactored PR #104 + #115/#125/#132)

#### `POST /chat/query`
Body: `{question: str}`. Cookie auth + tenant-scoped.
- **200:** `{answer: str, found: bool, sources: [{type: "obligation"|"term"|"document"|"clause", document_id, file_name, field_name?, value?, clause_num?, clause_title?, status?}]}`
- LLM (Gemini Flash) function-calling with 3 tools (FR-CQ-02). D-08 hard fallback: `{answer: "Không tìm thấy thông tin này trong hồ sơ của bạn.", sources: [], found: False}` (byte-exact).
- Graceful degradation: LLM error (no key/network/5xx/timeout/malformed JSON) → deterministic fallback, **never 500**.
- **PII routing log (DEC-028):** tool name + canonical `field_name` + arg keys present only. **NEVER** raw `party_filter`/`value_contains`/`doc_hint` value or `question`.

### 2.9 Reminders (Backend PR #66)

#### `POST /reminders/test` (dev/staging only)
Smoke endpoint — fire test reminder via active `reminder_send` consent channel. 404 in production.

Scheduler: APScheduler daily sweep 08:00 ICT, multi-tenant. Routing per FR-RM-05 (per-tenant consent `channel_target_ref`). Event types: `reminder_sent` / `reminder_failed` / `reminder_batch` / `obligation_overdue`.

### 2.10 Diagnostic — `GET /api/health/extraction` (Backend PR #80)

**Non-production only** (404 if `ENVIRONMENT not in {development, staging, test, local}`).

- **200:** `{environment, any_provider_configured, providers: [{name, env_vars: [...], configured: bool, present_per_var: {KEY: bool, ...}}], hint}`
- **Locked invariant:** NEVER echoes key VALUES — only env-var NAMES + presence booleans. Test `test_diagnostic_with_gemini` asserts no key value in response.

### 2.12 DEC-048 Clause + Re-read + Audit endpoints (cycle 5)

#### `GET /documents/{doc_id}/clauses` (Backend PR #320)
- **200:** `{clauses: [{id, clause_num, title, content, page_num, original_content, edited_by_user, edited_at}], clause_count, document_id, page_min, page_max}`
- Empty clauses → `200` with empty array (Claude fallback docs valid case, not 404).

#### `PATCH /documents/{doc_id}/clauses/{clause_id}` (Backend PR #325, migration `tenant_018`)
Body: `{content: "<new text>"}`.
- **D-07 snapshot:** lần edit đầu tiên preserve AI-extracted content vào `original_content` column (immutable sau first write).
- Sets `edited_by_user` (JWT sub) + `edited_at` (DATETIME).
- Logs `clause_edited` Event (D-12 PII-safe: content lengths only, KHÔNG raw text).
- **200:** `{id, clause_num, content, original_content, edited_by_user, edited_at}` (`ClausePatchOut`).

#### `POST /documents/{doc_id}/reread` (Backend PR #326)
Body: `{clause_ids?: int[]}` (omit → re-read all edited clauses since last re-read).
- D-02 diff-confirm gate: returns proposed diffs **WITHOUT** auto-applying.
- Source-aware: obligations with `source=user_manual` marked `protected=true` in diffs.
- Quota-gated (D-11) — 429 if doc_quota exceeded.
- **v1 scope:** derives from existing Terms (`ref=clause_num`). Full LLM re-extraction from edited clause text = KHE_AI TODO.
- **200:** `{re_read_at, diffs: [{obligation_id?, action: "add"|"update"|"remove", before?, after?, protected?, source_clause_num}]}` (`ReReadOut`).

#### `POST /documents/{doc_id}/re-derive-clause` (Backend PR #303 + #314, migration `tenant_017`)
Body: `{clause_num: "Điều X"}`.
- Clause-scoped re-derive — deletes+recreates ONLY obligations tagged to that clause via `source_clause_num`.
- Source-aware merge: `user_manual` / `done` / `cancelled` / `fulfilled_at IS NOT NULL` obligations protected.
- Sets `derived_from="user_edit"` cho re-derive path; AI extraction path sets `"original"`.
- No-churn guarantee: obligations từ clause khác KHÔNG bị touch.
- **200:** `{deleted_count, created_count, obligation_ids: [...]}`. **404:** clause_num not found.

#### `GET /documents/{doc_id}/events?limit&offset` (Backend PR #323 — D-07 audit history)
- **200:** `{events: [{id, event_type, entity_type, entity_id, payload (JSON), actor, created_at}], total}`
- Document-scoped + obligation-scoped events (tenant-isolated). Ordered `created_at DESC`.
- Surfaces `clause_edited`, `obligation_fulfilled`, `cascade_triggered`, etc. for UI audit timeline.

### 2.11 Public API surface boundary

Cookie auth (not Bearer — Backend PR #46/#91, Bearer fully retired). All endpoints above except `/auth/*` + `/health` + `/` require active session. Admin SPA at `/`, PWA at `/pwa/` (DEC-025 Option A — locked PR #95).

---

## 3. Auth & tenancy boundary

### 3.1 Dependency stack

| Dependency | Mục đích |
|---|---|
| `get_master_db()` | Yields session on `master.db`. Dùng cho auth + tenant registry. |
| `get_tenant_session(tid)` | Yields session on `tenants/<tid>.db`. **BẮT BUỘC** cho mọi per-tenant data access. |
| `get_db()` | Env-gated wrapper. Prod: raise HTTP 500 nếu thiếu tenant context. Dev: fallback `DEFAULT_TENANT_ID`. |
| `get_current_user()` | Verify JWT, attach `tenant_id` + `role` vào request state. |
| `require_manager`, `require_admin` | Role-gating wrappers. |

### 3.2 Hard rules

- **NEVER** dùng `SessionLocal()` trực tiếp trên per-tenant data — luôn `get_tenant_session(tid)`.
- JWT `tenant_id` PHẢI match `tenant_id` filter trên mọi query (FR-AC-01).
- `get_db()` không bao giờ fallback ở prod — silent fallback đã bị remove (CRITICAL fix PR #12).
- Engine cache: per-tenant SQLite engines được cache theo `tid` — tránh re-open cost.

### 3.3 SQLite tuning (anti-deadlock + Unicode)

- WAL mode enabled (`PRAGMA journal_mode=WAL`).
- `synchronous=NORMAL` (mitigate same-thread deadlock pattern — xem CLAUDE.md Common Bug Patterns).
- **Unicode `lower()` override (Backend PR #138):** Tenant engines register Python `str.lower()` as SQLite `lower()` function via `_register_unicode_lower` listener. Required for `.ilike()` to match VN diacritics (e.g., `Ệ` trong `DANH VIỆT`). SQLite default `lower()` is ASCII-only. Affects chat `party_filter` + `value_contains` searches.

---

## 4. Schema — `master.db` (4 bảng)

Global registry. Migration `001_initial_master.py` (single head, `down_revision=None`).

### 4.1 `tenants`

| Column | Type | Constraints | Note |
|---|---|---|---|
| `id` | VARCHAR | PK | Slug (vd `sme-abc-restaurant`) |
| `name` | VARCHAR | NOT NULL | Tên SME hiển thị |
| `db_path` | VARCHAR | NOT NULL | Đường dẫn file SQLite per-tenant |
| `plan` | VARCHAR | DEFAULT `'free'` | `free` (MVP) / future paid tier |
| `is_active` | BOOLEAN | DEFAULT `true` | Soft delete |
| `created_at` | DATETIME | DEFAULT now | |
| `doc_quota` | INTEGER | NULLABLE | FR-TN-01. Quota docs/month per tenant. Firm-configurable per SME (set at onboarding). `NULL` = unlimited (admin tenants). |
| `docs_used_month` | INTEGER | DEFAULT `0` | FR-TN-01. Counter incremented on every successful `POST /ingest/*`. Reset mùng 1 via APScheduler. |
| `quota_reset_at` | DATE | NULLABLE | FR-TN-02. Next reset boundary (mùng 1 tháng tới). |

### 4.2 `tenant_users`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK autoinc |
| `tenant_id` | VARCHAR | FK → `tenants.id` |
| `username` | VARCHAR | NOT NULL |
| `hashed_password` | VARCHAR | NOT NULL (bcrypt) |
| `role` | VARCHAR | `staff` / `manager` / `admin` |
| `is_active` | BOOLEAN | DEFAULT `true` |

**Unique constraint:** `(tenant_id, username)` — same username allowed across tenants.

*Sprint 1 carry-over:* add index on `tenant_id` (currently FK only).

### 4.3 `firm_partners`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK autoinc |
| `name` | VARCHAR | NOT NULL |
| `contact_email` | VARCHAR | |
| `contact_phone` | VARCHAR | |
| `is_active` | BOOLEAN | DEFAULT `true` |

### 4.4 `firm_tenant_access`

Implements FR-AC-03 / D-10 — partner xuyên-tenant chỉ mở khi SME consent.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK autoinc |
| `firm_id` | INTEGER | FK → `firm_partners.id` |
| `tenant_id` | VARCHAR | FK → `tenants.id` |
| `consent_status` | VARCHAR | `pending` / `granted` / `revoked` |
| `granted_at` | DATETIME | NULLABLE |
| `revoked_at` | DATETIME | NULLABLE |

**Unique constraint:** `(firm_id, tenant_id)`.

**Lifecycle:** `pending → granted → revoked` (one-way; revoke is terminal until new consent row).

### 4.5 `tenant_profiles` (DEC-030 — Kevin choice + Backend lead spec)

Separate model from `tenants` (Kevin chose this over PM-recommended embed in `tenants` table — keeps registry minimal + profile fields can grow). Per-SME profile data; **canonical store for `legal_name`** used by FR-OB-07/08 direction derivation. Backend lead exact schema spec (comment [4757964128](https://github.com/kevindo1103/khe/issues/1#issuecomment-4757964128)):

| Column | Type | Constraints | Note |
|---|---|---|---|
| `id` | INTEGER | PK AUTOINCREMENT | Integer surrogate key |
| `tenant_id` | VARCHAR | FK → `tenants.id` UNIQUE NOT NULL | 1:1 với tenant (slug) |
| `legal_name` | VARCHAR | NULLABLE | SME entity legal name — auto-match `parties[].name` for self-party (DEC-030). User-editable. NULL → all docs' obligations `direction=NULL + needs_review=true` (FR-OB-07). |
| `legal_name_aliases` | TEXT | NULLABLE | JSON array of common variants (vd shortened name, English name). Future enrichment. |
| `created_at` | DATETIME | DEFAULT `now` | |
| `updated_at` | DATETIME | DEFAULT `now` ON UPDATE | |

**Helper:** `get_tenant_legal_name(tenant_id)` queries `tenant_profiles`. Backend pattern per Backend lead response.

**Why separate model:** legal_name + future profile fields (industry, size, registered address, tax ID) are SME-business data, not auth/registry data. Tenants table stays minimal (slug, db_path, plan, quota). Migration adds `tenant_profiles` table in master.db (NOT per-tenant DB — registry-level for cross-tenant query).

**Lifecycle:** Created on tenant onboarding (concierge or self-serve). Empty `legal_name` → all docs' obligations get `direction=NULL, needs_review=true` until configured. User updates → re-derive direction via background task.

---

## 5. Schema — per-tenant `tenants/<slug>.db` (9 bảng — DEC-026 clauses + DEC-030 parties)

Skeleton landed in Sprint 0 via `create_all()` (no Alembic per-tenant loop yet — carry-over Sprint 1). Mọi bảng có cột `tenant_id` (indexed) cho query parity dù DB file đã cô lập.

### 5.1 `documents`
File metadata + phân loại.

| Column | Note |
|---|---|
| `id` | PK |
| `file_name` | Original filename |
| `file_path` | Immutable storage path under `STORAGE_DIR` |
| `doc_type` | `DocType` enum (M0 contract): `hd_thue_mat_bang` (lease), `hd_nha_cung_cap` (supplier), `hd_lao_dong` (labor), `khac` (other) |
| `status` | `processing` (BG task pending) / `extracted` (Terms populated) / `failed` (extraction error per D-08) |
| `needs_review` | Aggregate flag — `true` if any child Term has `needs_review=true` |
| `is_evidence` | BOOLEAN DEFAULT `false`. DEC-048 — biên bản/nghiệm thu đính kèm fulfillment. Khi `true` → skip `provider.extract()` server-side (P2) + `contains_personal_data` default `true` conservative. |
| `contains_personal_data` | BOOLEAN — NĐ 13 PII flag; DEC-039 firm gate uses to restrict firm portal visibility to metadata-only |
| **`title`** (DEC-050 R1, `tenant_021`) | VARCHAR NULLABLE — denormalized từ `tieu_de_hd` Term; user-editable qua PATCH `/documents/{id}` (D-07 Event) |
| **`contract_number`** (DEC-050 R1, `tenant_021`) | VARCHAR NULLABLE — `so_hop_dong` denormalized |
| **`signing_date`** (DEC-050 R6, `tenant_025`) | DATE-as-string NULLABLE — `ngay_ky` denormalized; ISO normalize via `_normalize_date_iso()` (VN "15/03/2025" → "2025-03-15"); unparseable → NULL |
| **`commencement_date`** (DEC-050 R6, `tenant_025`) | DATE-as-string NULLABLE — `ngay_khai_truong` (commencement / kick-off) denormalized |
| **`contract_duration`** (DEC-050 R8, `tenant_026`) | VARCHAR NULLABLE — thời hạn HĐ free text |
| **`lifecycle_status`** (DEC-050 R8, `tenant_026`) | VARCHAR enum: `active` / `expiring` (≤30 days to expiry) / `expired` / `settled` (manual) / `suspended` (manual). Backend `lifecycle.py` `derive_lifecycle_status()` computes 3 đầu từ `expiry_date` + `contract_term`; `settled`/`suspended` user override. |
| **`has_signature`** (DEC-050 R5b, `tenant_028`) | BOOLEAN NULLABLE — signature detection flag (NULL = pre-migration docs, UI hide badge) |
| **`signature_pages`** (DEC-050 R5b, `tenant_028`) | TEXT JSON list[int] — page numbers where signatures detected |
| **`extraction_model`** (cycle 6, `tenant_019`) | VARCHAR NULLABLE — provider+model snapshot (`gemini_flash:gemini-2.5-flash`, etc.) per extraction |
| **`extraction_latency_ms`** (`tenant_019`) | FLOAT NULLABLE — total extraction time in ms |
| **`extraction_warnings`** (`tenant_019`) | TEXT JSON list — warnings from result.warnings (clamp violations, etc.) |
| **`processing_stage`** (cycle 6, `tenant_020`) | VARCHAR DEFAULT `"queued"` — pipeline checkpoint: `queued` / `ocr` / `llm` / `saving` / `done` / `failed` |
| **`processing_progress`** (`tenant_020`) | INTEGER DEFAULT `0` — 0/30/60/90/100 per stage. Reset to 0 on `_mark_failed()`. |
| `created_at` | Upload timestamp |

### 5.2 `terms` — EAV with CANONICAL_FIELDS vocab v2 (DEC-029 Backend PR #135)

Per-Document extracted Term rows. Schema is **EAV** (entity-attribute-value); `field_name` constrained to vocab tổng **12 universal + ~30 type-specific** (Backend `modules/extraction/schemas.py`):

**7 BASE_CANONICAL_FIELDS** (Claude fallback trả tới đây — schema lean per PR #135 grammar limit):
1. `doi_tac` · 2. `ngay_hieu_luc` · 3. `ngay_het_han` (nullable, derivable §6.1)
4. `gia_tri_hd` · 5. `thoi_han_hd` · 6. `dieu_khoan_gia_han` · 7. `dieu_khoan_thanh_toan`

**5 V2_UNIVERSAL_FIELDS** (Gemini-only):
8. `doc_type_group` (enum 11 — xem §9.5) · 9. `ngay_ky` · 10. `tien_dat_coc`
11. `thoi_han_bao_hanh` · 12. `thoi_han_thong_bao`

**9 TYPE_SPECIFIC_FIELDS sets (~30 fields)** — emit qua `NamedExtractedField` keyed array; persist 1 Term row per item (Backend PR #141 dynamic iteration):
- `lao_dong`: `luong_co_ban`, `thoi_gian_thu_viec`, ...
- `bat_dong_san`: ...
- `xay_dung`, `bao_dam`, `cong_nghe_ip`, `thuong_mai`, `van_tai_logistics`, `tai_chinh`, `hanh_chinh`: per-group field sets per `modules/extraction/schemas.py` `TYPE_SPECIFIC_FIELDS` dict.

| Column | Note |
|---|---|
| `id` | PK |
| `document_id` | FK → `documents` |
| `field_name` | VARCHAR ∈ 12 universal ∪ type-specific |
| `field_value` | TEXT (free form; date/numeric coercion at consumer) |
| `confidence` | FLOAT (per FR-EX-05) — Gemini grammar workaround: removed `ge/le` bounds, `@field_validator` clamps server-side (PR #135) |
| `needs_review` | BOOLEAN, D-08 / FR-EX-05 |
| `is_superseded` | BOOLEAN (DEC-019/020/021 chain resolution) |
| `overrides_term_id`, `inherited_from_doc_id` | NULLABLE (chain resolution annotations) |

| Column | Note |
|---|---|
| `id` | PK |
| `document_id` | FK → `documents` |
| `field_name` | VARCHAR, value ∈ CANONICAL_FIELDS above |
| `field_value` | TEXT (free form; date/numeric coercion at consumer) |
| `confidence` | FLOAT, per FR-EX-05 |
| `needs_review` | BOOLEAN, D-08 / FR-EX-05 |

### 5.3 `obligations` (trái tim MVP) — **schema rewrite DEC-027/030 #122 Option B**

| Column | Note |
|---|---|
| `id` | PK |
| `document_id` | FK → `documents` (chain terminal per FR-OB-05) |
| `description` | Mô tả nghĩa vụ; `amount` embedded vào string cho payment rows (no dedicated column yet — Backend PR #141 ambiguity) |
| **`obligation_type`** | **Category enum 8 (DEC-027):** `payment` · `delivery` · `handover` · `expiration` · `renewal` · `review` · `warranty` · `other`. *Renamed concept: trước v0.4 `obligation_type` = cadence; per #122 Option B → cadence moved to `recurrence`.* |
| **`recurrence`** | **Cadence enum (renamed from old `obligation_type`):** `once` · `monthly` · `quarterly` · `yearly` · `open_ended_review`. `open_ended_review` = `thoi_han_hd` phi-số case (DEC-020), `due_date=NULL`. Migration `tenant_005` per PM relay. |
| `due_date` | DATE — derived per FR-OB-01 hoặc từ `payment_schedule[].due_date`. NULL khi `recurrence=open_ended_review`. |
| `status` | **Enum extended DEC-048:** `pending` · `done` · `cancelled` · `awaiting_confirmation` (cascade-past D-02 backfill) · `waiting_trigger` (FR-OB-13 unresolved date anchor). **`overdue` KHÔNG phải status** — FE-derived urgency bucket. |
| `remind_before_days` | INTEGER (default 30, 7) |
| **`direction`** (DEC-030) | `nghĩa_vụ` / `quyền_lợi` / `NULL`. Derived per FR-OB-07 (legal_name auto-match). NULL → `needs_review=true`. |
| **`obligor`** (DEC-030) | VARCHAR — bên chịu nghĩa vụ (party name từ `parties[]`). NULL hợp lệ khi AI không xác định (D-08). |
| `source_doc_chain` | TEXT JSON array of doc_ids per chain (DEC-019/020/021). Derived obligations luôn set; payment rows từ `payment_schedule[]` KHÔNG set (idempotency key) |
| `resolution_method` | VARCHAR — `"last_writer_wins"` (Backend PR #59) |
| `needs_review` | BOOLEAN — flag cho user verify (D-02), vd `direction=NULL` |
| **`fulfilled_at`** (DEC-048) | DATETIME NULLABLE — ngày SME thực sự hoàn thành. Dùng làm **anchor** cho cascade chain (G1 fix per DEC-048: NOT `date.today()`). Scheduler exclude từ overdue flip + reminder khi `IS NOT NULL` (FR-RM-07). |
| **`fulfilled_by`** (DEC-048) | VARCHAR NULLABLE — actor name (SME user hoặc concierge) |
| **`evidence_doc_ids`** (DEC-048) | TEXT JSON array of doc_ids — link tới documents với `is_evidence=true` (FR-IN-05) |
| **`source_clause_num`** (Kevin Option B 0a, migration `tenant_017`) | VARCHAR NULLABLE — clause gốc sinh obligation (FR-OB-11). Set từ winning Term's `ref` field trong `derive_obligations()`. Enables clause-scoped re-derive. |
| **`derived_from`** (PR #303) | VARCHAR NULLABLE — `"original"` (AI initial extraction) / `"user_edit"` (clause edit triggered re-derive) / `"ai_re_derived"` (POST /reread path). |
| **`source`** (P1 merge rule) | VARCHAR — `ai_extracted` / `user_manual` / `ai_re_derived`. **`user_manual` obligations protected from re-derive delete** (FR-OB-12). |

### 5.4 `parties` — **schema update DEC-030**

Party normalization (FR-DR-02 + FR-EX-06).

| Column | Note |
|---|---|
| `id` | PK |
| `name` | NOT NULL — extracted verbatim |
| `tax_code` | NULLABLE |
| `address` | NULLABLE |
| `contact_email`, `contact_phone` | NULLABLE |
| **`role_label`** (DEC-030) | VARCHAR — vai trò trong HĐ (`"Owner"`, `"Bên A"`, `"NSDLĐ"`, `"Bên thuê"`, ...) — extracted verbatim, D-06 read-only. AI KHÔNG quyết bên nào là SME. |
| **`address`** (DEC-050 R2, `tenant_022`) | VARCHAR NULLABLE — địa chỉ pháp lý |
| **`representative`** (`tenant_022`) | VARCHAR NULLABLE — người đại diện ký kết |
| **`tax_code`** existing | VARCHAR NULLABLE — MST đã có; `tenant_022` consolidate |
| **`is_self`** (DEC-050 R2, `tenant_022`) | BOOLEAN — flip true sau khi `legal_name` auto-match thành công (DEC-030 self-party rule) |
| **`aliases`** (DEC-050 R2, `tenant_022`) | TEXT JSON array — tên viết tắt / khác (vd `["CTCP TTCR", "Tran Thai", ...]`) |
| `document_id` | FK — parties per-document (1 party có thể appear nhiều docs với role_label khác) |

### 5.5 `events`
Append-only ledger (FR-AU-01, P-2). Fields: `id`, `event_type`, `entity_type`, `entity_id`, `payload` (JSON), `actor_user_id`, `created_at`. **NEVER UPDATE** — sửa = ghi event reversal.

### 5.6 `branches`
Per-branch khi SME multi-location.

### 5.7 `employees`
Per-tenant employee directory (optional usage).

### 5.8 `document_relationships` (Backend PR #59, DEC-019/020/021)

Edges between Documents (amendments, framework references). AI suggests `pending`; SME confirms (D-02).

| Column | Note |
|---|---|
| `id` | PK |
| `from_doc_id` | FK → `documents` (the amending/referencing doc) |
| `to_doc_id` | FK → `documents` (parent). **Nullable** — orphan amendments late-link when parent arrives. |
| `unresolved_ref` | TEXT — filename or phrase awaiting resolution (when `to_doc_id IS NULL`) |
| `relationship_type` | `amends` (phụ lục) / `references_framework` (HĐ khung) — classified by phrasing heuristic, conservative per DEC-019 no-legal-judgment |
| `status` | `pending` (AI suggested) / `confirmed` (SME ratified per D-02) |
| `confirmed_by_sme` | BOOLEAN — only `true` accepted via PATCH (one-way) |
| `confidence` | FLOAT |
| `created_at` | DATETIME |

**Chain resolution (on confirm):** `resolve_chain` traverses amends topology (not upload time) → supersedes overlapping Terms in parent chain via `terms.is_superseded` + `terms.overrides_term_id` + `terms.inherited_from_doc_id`. Existing Obligations get `source_doc_chain` + `resolution_method="last_writer_wins"` annotations.

**Open caveat (#61):** re-extraction may invalidate `is_superseded` invariants. Full re-resolution lands with #26.

### 5.9 `clauses` (Backend #99, DEC-026)

Per-Document clause storage — text nguyên gốc (text-as-extracted), phục vụ `search_clauses` tool (FR-CQ-02). Populated từ `VisionExtractionResult.clauses[]` (cùng vision call, không tốn thêm API).

| Column | Type | Note |
|---|---|---|
| `id` | INTEGER | PK AUTOINCREMENT |
| `doc_id` | INTEGER | NOT NULL, FK → `documents(id)` **ON DELETE CASCADE** |
| `clause_num` | TEXT | NULLABLE — vd `"Điều 8"`, `"Khoản 2.3"` |
| `title` | TEXT | NULLABLE — vd `"Chấm dứt hợp đồng"` |
| `content` | TEXT | NOT NULL — text nguyên gốc, đầy đủ |
| `page_num` | INTEGER | NULLABLE — vị trí trong file gốc |
| `created_at` | DATETIME | DEFAULT `CURRENT_TIMESTAMP` |
| **`original_content`** (DEC-048 §13 addendum, migration `tenant_018`) | TEXT | NULLABLE — snapshot AI-extracted content lần edit đầu tiên. **Immutable sau first write** (D-07). NULL = chưa edit. |
| **`edited_by_user`** (`tenant_018`) | VARCHAR | NULLABLE — JWT sub của user sửa lần gần nhất |
| **`edited_at`** (`tenant_018`) | DATETIME | NULLABLE — timestamp edit gần nhất |

**Indexes:** `idx_clauses_doc ON clauses(doc_id)`.

**Hierarchy expansion (DEC-050 R3, `tenant_023`):**

| Column | Note |
|---|---|
| `parent_id` | INTEGER NULLABLE FK → `clauses.id` self-ref |
| `level` | INTEGER NULLABLE — 1 = Điều, 2 = Khoản, 3 = Mục, etc. |
| `clause_path` | VARCHAR NULLABLE — dot-separated (vd `"2.1.3"`) |

Synthesized post-extraction via `app/services/clause_hierarchy.py` (PR #384) from clause numbering patterns. Not LLM-driven — deterministic regex.

**Migration revisions:**
- `tenant_003_clauses.py` (`down_revision = "tenant_002"`) — initial clauses table (DEC-026)
- `tenant_018_clause_edit_fields.py` — adds `original_content` + `edited_by_user` + `edited_at` (PR #325)
- `tenant_023_clause_hierarchy.py` — adds `parent_id` + `level` + `clause_path` (PR #384, DEC-050 R3)

### 5.10 `definitions` (DEC-050 R9 — NEW per-tenant table, `tenant_026`/`tenant_027` Backend PR #389)

Glossary entries bóc từ "Định nghĩa" section của Document.

| Column | Type | Note |
|---|---|---|
| `id` | INTEGER | PK AUTOINCREMENT |
| `document_id` | INTEGER | NOT NULL FK → `documents(id)` |
| `tenant_id` | VARCHAR | NOT NULL — multi-tenant isolation parity |
| `clause_id` | INTEGER | NULLABLE FK → `clauses(id)` — clause nguồn nếu detected |
| `term` | VARCHAR | NOT NULL — term name |
| `definition` | TEXT | NOT NULL — full definition body |
| `original_term` | VARCHAR | NULLABLE — D-07 first-edit snapshot (mirrors `clauses.original_content` pattern) |
| `created_at` | DATETIME | DEFAULT now |

**Endpoints (Backend PR #389):**
- `GET /documents/{doc_id}/definitions` → `{definitions: [...], definition_count}`
- `PATCH /documents/{doc_id}/definitions/{def_id}` body `{term?, definition?}` — D-07 snapshot first edit, Event per field
- `DELETE /documents/{doc_id}/definitions/{def_id}` — Event before removal

Rollup `definition_count` on `DocumentListItem` + `DocumentDetailOut`.

### 5.11 Cross-references (DEC-050 R10 — Backend PR #392)

Service `app/services/cross_ref.py` detects Vietnamese legal refs (`Điều X`, `Khoản Y Điều Z`, `Mục N.M`, `Phụ lục A`) trong `clauses.content` post-extraction. Resolves intra-document refs + appendix-via-annex (FR-DR-04). Orphans flagged.

**Storage shape:** ClauseCrossRef model (verify exact DB column layout from PR #392 — table or JSON field on clauses). Each ref carries: `source_clause_id`, `target_ref` (raw text), `target_type` (`clause` / `sub_clause` / `appendix`), `resolved` BOOL, `target_clause_id` (NULL if orphan).

**Endpoints:**
- `GET /documents/{doc_id}/cross-refs` → list with resolution status
- `POST /documents/{doc_id}/cross-refs/resolve` — re-run resolver (vd sau khi target doc upload)

Extraction-runner uses `db.flush()` cho atomicity giữa clauses persist + cross-ref detect.

### 5.12 `document_relationships.relationship_type` enum (DEC-050 R4 — `tenant_024` Backend PR #385)

Extended from 2-value to **3-value enum**:
- `amends` (sửa đổi — overwrites parent terms via `resolve_chain`)
- `references_framework` (HĐ con của khung)
- **`annex`** NEW — phụ lục độc lập đính kèm; **excluded** từ `resolve_chain` (filter `relationship_type == "amends"`); FE separately surface

Heuristic split:
- Amendment pattern: requires keyword (`sửa đổi` / `bổ sung` / `thay thế`) + capped `.{0,80}?` lookbehind
- Annex pattern: `[A-Za-z0-9\-]+` capture với negative lookahead guard (matches lettered appendices "Phụ lục A")

**Distinction vs `terms`:**
- `terms` = EAV structured fields (CANONICAL_FIELDS vocab, date/numeric coercion).
- `clauses` = raw text passages preserving original wording. Search by full-text (LIKE / FTS5 future), not field_name.

**Tool consumption:** `search_clauses(query, doc_hint)` — substring/full-text search trong `content`; filter `doc_hint` qua join `documents.file_name LIKE` hoặc `clauses.doc_id IN (...)`.

---

## 6. Derivation rules — Obligation engine

### 6.1 FR-OB-01: `ngay_het_han` derivation

**Input:** Term row với `ngay_hieu_luc`, `thoi_han_hd`, `ngay_het_han`.

**Rule:**
```
IF ngay_het_han IS NULL
   AND ngay_hieu_luc IS NOT NULL
   AND thoi_han_hd parses to numeric months/years
THEN
   ngay_het_han = ngay_hieu_luc + parsed(thoi_han_hd)
   needs_review = false (derivation succeeded)
ELIF thoi_han_hd is non-numeric ("vô thời hạn", "kể từ khi nghiệm thu", ...)
THEN
   policy: PENDING PM (a) skip / (b) flag-for-human / (c) recurring trigger
   v0.1 fallback: skip expiry obligation; still generate recurring (vd BHXH) independent of expiry.
```

**Rationale (KHE_AI 2026-06-11 live test):** HĐ Việt Nam phổ biến ghi `ngay_hieu_luc + thoi_han_hd`, không ghi thẳng `ngay_het_han`. Model VisionExtractionProvider trả `ngay_het_han=None` đúng D-08 (không bịa) — engine phải derive ở Obligation tier.

### 6.2 Recurrence rules (Sprint 1+)

`recurrence` lặp (`monthly`/`quarterly`/`yearly`) → expand instances per FR-OB-02. Detail TBD Sprint 2 (PR #66 reminder service handles `once` + chain-derived; monthly/quarterly recurrence parsing deferred — needs `dieu_khoan_thanh_toan` parser).

### 6.3 Payment schedule derivation (DEC-027 — Backend PR #141)

`ExtractionResult.payment_schedule[]` items với `due_date` → `pending` Obligation rows:
```
For each item in payment_schedule[]:
   IF item.due_date IS NOT NULL:
      INSERT obligations(
         description = f"{item.milestone or 'Thanh toán'} — {item.amount} VND",
         obligation_type = "payment",
         recurrence = "once",  # monthly/quarterly collapse to single 'once' rows per due_date (Sprint 2 will expand)
         due_date = item.due_date,
         obligor = item.payer,
         direction = derive_direction(item.payer, legal_name),  # §6.4
         source_doc_chain = NULL,  # idempotency key — distinguishes payment from chain-derived
         status = "pending",
      )
```

**Idempotency:** re-extraction delete `WHERE source_doc_chain IS NULL` then re-insert. Derived obligations always set `source_doc_chain`; payment rows never set.

**Staging caveat (Backend lead correction [4757964128](https://github.com/kevindo1103/khe/issues/1#issuecomment-4757964128)):** PR #141 shipped với `obligation_type="once"` (NOT `"payment"` as PM catch-up table said). Đây là deliberate override — pre-#145 schema `obligation_type` vẫn là cadence axis (engine/scheduler/tests recognize `"once"` + `"open_ended_review"`). **Post-#145 migration** (tenant_005): runner flip thành `obligation_type="payment"` + `recurrence="once"`. Expiry obligations: `obligation_type="expiration"` + `recurrence="once"`|`"open_ended_review"`.

### 6.4 Direction derivation (DEC-030)

Mỗi Obligation phải có `direction`:
```
legal_name = tenant_profile.legal_name  # NULL = chưa configured

IF legal_name IS NULL:
   direction = NULL
   needs_review = True
ELIF obligor LIKE legal_name OR legal_name LIKE obligor (case-insensitive, alias-aware):
   direction = "nghĩa_vụ"
ELIF obligor IS NOT NULL:
   direction = "quyền_lợi"
ELSE:  # obligor NULL → AI không xác định
   direction = NULL
   needs_review = True
```

**Auto-match fail behavior (Kevin cycle 4 q3 ratify):** `direction=NULL` + `needs_review=true`. User confirm via UI extraction review screen (D-02). NOT block extraction, NOT default to `nghĩa_vụ`.

**Re-derivation:** when `tenant_profile.legal_name` changes, background task re-derive direction across all obligations. Open task — implementation deferred Sprint 2.

### 6.5 Cascade chain anchor (DEC-048 — G1 fix, Backend PR #313/#319)

`propagate_obligation_done(parent_obligation)` invoked when parent flips to `done`:

```
For each child in chain_dependents(parent):
   delay_days = child.trigger_delay_days  # vd 30 ngày
   anchor    = parent.fulfilled_at        # G1 fix: NOT date.today()
   child.due_date = anchor + delay_days
   IF child.due_date < today:
      child.status = "awaiting_confirmation"  # D-02 SME confirm
   ELSE:
      child.status = "pending"
   Log Event("cascade_triggered", payload={parent_id, child_id, anchor, delay_days})
```

**G1 rationale:** if anchor were `date.today()`, replaying a historical parent fulfillment would generate due dates relative to NOW instead of the actual fulfillment date — breaks audit reconstruction.

**Reminder integration (FR-RM-07):** `_flip_overdue_status()` + `compute_due_window()` exclude `awaiting_confirmation` + `fulfilled_at IS NOT NULL` via `status == "pending"` filter — no code change needed, just documented invariant.

### 6.6 Date-anchored obligation resolver (FR-OB-13, Backend PR #322)

Obligations with text trigger ("30 ngày từ ngày ký", "60 ngày sau ngày hiệu lực") that lack `due_date` at extraction time persist as `status="waiting_trigger"`, then resolved when anchor Term exists.

```
resolve_date_anchored_obligations(tenant_session):
   For each obligation with status="waiting_trigger":
      anchor_field = _detect_anchor_field(obligation.trigger_condition)
      # Currently maps: "ngày ký" → "ngay_ky", "ngày hiệu lực" → "ngay_hieu_luc"
      IF anchor_field is None:
         continue  # D-08: don't guess
      anchor_term = find_term(tenant, doc_id=obligation.document_id, field_name=anchor_field)
      IF anchor_term and anchor_term.field_value parses to date:
         obligation.due_date = parse(anchor_term.field_value) + obligation.trigger_delay_days
         obligation.status = "pending"
         Log Event("obligation_date_resolved", payload={anchor_field, anchor_value, computed_due})
```

**Conservative scope:** only `ngay_ky` + `ngay_hieu_luc` anchors mapped MVP. Event-triggered anchors (`ngay_ban_giao`, `ngay_nghiem_thu`) handled by FR-OB-10 cascade chain qua `fulfilled_at`.

### 6.7 P1 source-aware merge + derive delete path-2 guard (Backend PR #311)

Khi re-derive (clause edit / re-read / re-extraction):

```
# Cleanup phase (DELETE existing derived obligations before re-create)
DELETE FROM obligations
WHERE document_id = ? AND source_clause_num = ?
  AND source != "user_manual"
  AND fulfilled_at IS NULL        # ← path-2 guard, PR #311 V1 fix
```

**Rationale:** user_manual obligations represent SME's explicit intent → never overwrite. `fulfilled_at IS NOT NULL` means SME has captured fulfillment with evidence → audit-immutable.

**Re-create phase** sets new obligations with `derived_from = "user_edit"` (re-derive endpoint) hoặc `"ai_re_derived"` (re-read endpoint). `source_clause_num` propagated từ winning Term `ref`.

---

## 7. Security boundary

- JWT bắt buộc trên mọi endpoint mutate data (CLAUDE.md Security Rules).
- Endpoint SME-side verify `tenant_id` match JWT (FR-AC-01).
- Firm portal verify consent (FR-FP-03 + `firm_tenant_access.consent_status='granted'`).
- KHÔNG log: passwords, JWT secret, Telegram bot token, OCR/LLM API keys.
- Raw SQL với f-string CẤM — chỉ ORM.
- NĐ 13/2023 DLCN hooks: PII processing log purpose + consent reference.

---

## 9. Extraction module API (KHE_AI PR #55/#58 — currently on `staging`, not `main`)

Backend tiêu thụ extraction qua **public factory** trong scope KHE_AI. **KHÔNG** construct provider trực tiếp.

### 9.1 Factory entry point

```python
from modules.extraction import get_extraction_provider, ExtractionUnavailable

provider = get_extraction_provider(prefer="gemini_flash")
result = await provider.extract(file_bytes, doc_type_hint="auto")
```

- `prefer` parameter: `"gemini_flash"` (default) | `"claude_haiku"` | `"claude_sonnet"`.
- Factory handles **provider selection + key handling + DEC-002 fallback** (Gemini primary → Claude Haiku). Backend stays policy-free.
- **`VisionExtractionProvider` Protocol unchanged** — interface scope-locked, additive change only.

### 9.2 Error semantics — `is_error` vs `needs_review`

Two distinct concepts. Do **NOT** conflate.

| Concept | Where | Meaning | Backend response |
|---|---|---|---|
| `ExtractionUnavailable` exception | Raised by factory | No API key / SDK missing — provider not constructable | Map to **503 Service Unavailable** + `documents.status="failed"` |
| `ExtractionResult.is_error` | Property on result | Extraction completed but hit hard error (no fabrication per D-08) | `documents.status="failed"`, no Terms persisted |
| Per-field `needs_review` | `terms[].needs_review` | Extraction succeeded but field confidence low — human verify queue | `documents.needs_review=true`, Term persisted with confidence + flag |

### 9.3 Worker integration (Backend PR #60)

`app/services/extraction_runner.run_extraction(doc_id, tenant_id, doc_type)`:
1. Open own tenant session (`get_tenant_session`).
2. Defensive consent re-check — revoked since upload → `status="failed"`, no LLM call.
3. `get_extraction_provider()` → `await provider.extract(bytes, "auto")`.
4. `is_error` → `failed`. Else persist 7 CANONICAL_FIELDS Terms (`field_value` + `confidence` + `needs_review`); set `documents.doc_type = result.doc_type.value`, `status="extracted"`.
5. **Idempotent:** re-run deletes existing Terms in same transaction before re-insert.

**Trigger:** FastAPI `BackgroundTasks` scheduled in `POST /ingest/upload` + `/bulk` after 201 response.

### 9.4 Promote path note

Factory currently on `staging` (PR #58). PR #55 was reverted from `main` via #57 (wrong base — skipped `feature → staging → main` flow). Re-lands on `main` at next promote.

### 9.5 2-tier schema (DEC-026 addendum + DEC-029 + DEC-030)

Provider grammar limits buộc tách 2-tier:

| Schema | Used by | Fields | Why |
|---|---|---|---|
| **`ContractExtractionLLM`** | Claude Haiku/Sonnet (fallback) | 7 BASE_CANONICAL_FIELDS (flat) | Schema rộng → `Schema is too complex` (deterministic 400) trên Claude `messages.parse()` với `list[ClauseItem]` hoặc many bounded fields |
| **`ContractExtractionLLMFull`** | Gemini Flash (primary) | 12 universal + `clauses[]` + `parties[]` + `payment_schedule[]` + `NamedExtractedField` keyed list for type-specific | Gemini chấp nhận nested + larger schema |

**`to_result()` mapping:** `getattr(parsed, "clauses", [])` — safe accessor cho fallback path.

**Consequence:** doc extract qua Claude fallback có `clauses=[]`, `parties=[]`, `payment_schedule=[]`, `doc_type_group=NULL`, no type-specific fields. **Carry-over ambiguity (PM #143):** propose `Document.provider` column để phân biệt "HĐ không có clauses" vs "extract qua Claude, clauses unavailable" + enable re-extract-prefer-Gemini policy cho docs cần clauses.

### 9.6 DOC_TYPE_GROUPS enum (DEC-029)

11 values (10 contract groups + `other`), reflect `modules/extraction/schemas.py`:
`dan_su` · `thuong_mai` · `lao_dong` · `bat_dong_san` · `van_tai_logistics` · `xay_dung` · `cong_nghe_ip` · `tai_chinh` · `bao_dam` · `hanh_chinh` · `other`

Old `DocType` enum (4 values: `hd_thue_mat_bang`/`hd_nha_cung_cap`/`hd_lao_dong`/`khac`) **deprecated** but retained on Document for M0 legacy docs.

### 9.7 PaymentScheduleItem (DEC-027 + DEC-030)

```python
class PaymentScheduleItem:
    amount: str                # text — VN currency variants
    due_date: date | None
    milestone: str | None      # "Tạm ứng 30%", "Bàn giao mặt bằng", ...
    recurrence: str | None     # "monthly"/"quarterly"/"once" — Sprint 2 expand
    payer: str | None          # party name — DEC-030
```

### 9.8 PartyItem (DEC-030 + DEC-050 R2 expansion)

```python
class PartyItem:
    name: str          # extracted verbatim, D-06
    role_label: str    # "Owner", "Bên A", "NSDLĐ", ... — verbatim
    # DEC-050 R2 additions (Gemini-only — Claude lean schema unchanged):
    address: str | None
    representative: str | None
    tax_code: str | None
```

### 9.9 Hybrid OCR provider (DEC-049, KHE_AI PR #341)

Fourth provider trong `_REGISTRY` (alongside `gemini_flash` / `claude_haiku` / `claude_sonnet`).

```python
provider = get_extraction_provider(prefer="hybrid_ocr")
```

**2-pass pipeline:**
1. `scan_detect.is_scanned_pdf(file_bytes)` — heuristic `pdftotext` extract < 50 chars/page → scanned
2. Pass A — text extraction:
   - Scanned → Document AI OCR (gated `GOOGLE_APPLICATION_CREDENTIALS`)
   - Digital → `extract_embedded_text()` (pdftotext)
3. Pass B — `prompts.build_text_instruction()` text-mode prompt cho Gemini Flash → `ContractExtractionLLMFull`

**System deps:** `poppler-utils` (pdftotext / pdfinfo) on VPS. Document AI credential gated.

**Routing policy (DEC-049 OPEN):** opt-in only currently — set `prefer="hybrid_ocr"` explicit. Auto-route default (hybrid for PDFs) chờ Kevin ratify. Non-PDF input → explicit error → `_FallbackProvider` advances to next provider (Gemini Flash vision).

### 9.10 Schema v3 — DEC-050 R1-R10 (KHE_AI PR #381)

CANONICAL_FIELDS: 12 → **15**:
- +`tieu_de_hd` (R1 title)
- +`so_hop_dong` (R1 contract number)
- +`ngay_khai_truong` (R6 commencement date)

`ClauseItem` extended (R3):
- `level: int | None`
- `clause_path: str | None`

`PartyItem` extended (R2): see §9.8.

New models:
```python
class DefinedTermItem:    # R9
    term: str
    definition: str
    clause_ref: str | None

class CrossReferenceItem: # R10
    source_clause: str   # source clause_num/path
    target_ref: str      # raw target text
    target_type: str     # "clause" / "sub_clause" / "appendix"
    resolved: bool
```

`ContractExtractionLLMFull` new flags:
- `has_signature: bool`
- `signature_pages: list[int]`
- `defined_terms: list[DefinedTermItem]`
- `cross_references: list[CrossReferenceItem]`

**Claude `ContractExtractionLLM` lean schema unchanged** (7 BASE fields) — Claude grammar limits preserved.

---

## 10. Audit Event types (NĐ 13/2023 compliance)

Events in per-tenant `events` ledger. Append-only.

| `event_type` | `entity_type` | Actor | Trigger | Payload |
|---|---|---|---|---|
| `consent_granted` | `tenant` / `firm_partner` | SME / admin | Consent grant flow | `{consent_kind, consent_reference}` |
| `consent_revoked` | `tenant` / `firm_partner` | SME / admin | Consent revoke | `{consent_kind, consent_reference}` |
| `extraction_performed` | `document` | `"system"` | Backend PR #60 worker post-extract | `{provider, model, cost_vnd, latency_ms, consent_reference}` — `consent_reference` provides O(1) back-link to the consent record per Compliance §A.2 |
| `extraction_failed` | `document` | `"system"` | Worker hit `is_error` or `ExtractionUnavailable` | `{reason, provider}` — reason now richer per PR #80 (names exact env vars missing) but **NEVER key values** |
| `obligation_derived` | `obligation` | `"system"` | Backend PR #64 engine | `{document_id, source_doc_chain, resolution_method, recurrence, obligation_type}` |
| `reminder_sent` | `obligation` | `"system"` | Backend PR #66 scheduler | `{channel, channel_target_ref, consent_reference, direction, message}` — `message` text per FR-RM-06 |
| `reminder_failed` | `obligation` | `"system"` | Telegram delivery error | `{reason, retry_at}` |
| `reminder_batch` | `tenant` | `"system"` | Daily 08:00 ICT sweep | `{total_sent, total_failed, scheduler_run_id}` |
| `obligation_overdue` | `obligation` | `"system"` | Status flip when `due_date < today` | `{previous_status}` |
| `chat_query_logged` (DEC-028) | `tenant` | User | Every `/chat/query` | **PII-safe (FR-CQ-05):** `{tool_name, field_name_canonical, arg_keys_present, found, source_count}`. **NEVER** raw `question` or filter values. **🔴 COMPLIANCE DEBT:** assume-consent bypass; must add explicit consent gate before prod (KHE_Compliance #119). |
| `obligation_fulfilled` (DEC-048) | `obligation` | User | PATCH `/obligations/{id}` with fulfillment fields | `{previous_status, fulfilled_at, fulfilled_by, evidence_doc_ids, purpose: "obligation_fulfillment"}` — purpose enum closed-set (KHE_Compliance §A.1). No consent gate (storage-only, no LLM transit). |
| `obligation_fulfillment_reverted` (DEC-048) | `obligation` | User | PATCH `done` → `pending` / `cancelled` | `{previous_fulfilled_at, previous_fulfilled_by, evidence_doc_ids_cleared}` — child cascade rolled back conservatively. |
| `cascade_triggered` (DEC-048) | `obligation` | `"system"` | `propagate_obligation_done()` activates child | `{parent_obligation_id, child_obligation_id, anchor (= parent.fulfilled_at), delay_days, child_due_computed, child_status (pending or awaiting_confirmation)}` |
| `clause_edited` (DEC-048 §13) | `clause` | User | PATCH `/documents/{id}/clauses/{clause_id}` | **PII-safe (D-12):** `{clause_id, clause_num, original_content_length, edited_content_length, is_first_edit, edited_by_user}` — **NEVER** raw content text. |
| `re_read_triggered` (DEC-048 §13) | `document` | User | POST `/documents/{id}/reread` | `{clause_ids_scope, diffs_count_by_action: {add, update, remove}, cost_vnd}` |
| `obligation_date_resolved` (FR-OB-13) | `obligation` | `"system"` | Background resolver maps trigger phrase → Term anchor | `{anchor_field, anchor_value, trigger_delay_days, computed_due_date}` |
| `evidence_attached` (KHE_Compliance §G) | `document` | User | Upload với `is_evidence=true` | `{document_id, contains_personal_data, purpose: "obligation_fulfillment"}` — no consent gate per §A.1; metadata-only firm visibility per DEC-039 §G.2. |
| `updated` | `term` | User | PATCH term (D-07) | `{old, new}` — **PII flag:** carries extracted contract values, intended NĐ 13 audit trail per PR #54 ack |

**Compliance pipeline:** `consent_granted` (logged) → `extraction_performed` (with back-link via `consent_reference`) → `updated` (term edits with old/new PII). End-to-end traceability who-changed-what.

---

## 8. Open items (Sprint 1+)

| ID | Item | Owner |
|---|---|---|
| O-1 | Per-tenant Alembic migration loop (replace `create_all`) | KHE_Backend |
| O-2 | `tenant_users.tenant_id` index in migration | KHE_Backend |
| O-3 | `thoi_han_hd` phi-số policy (a/b/c) | PM decision |
| O-4 | Login email→tenant lookup (replace explicit `tenant_id`) | PM / KHE_Backend |
| O-5 | `regen_openapi.py` run khi `docs/openapi.json` ready | KHE_Backend |

---

*Hết v0.6 — cycle 6 fold (DEC-049 hybrid OCR + DEC-050 R1-R10 EPIC #362 production PR #402). 8 tenant migrations consolidated (`tenant_019..028`). 2 new entities (Definition, CrossReference). Schema v3 extraction (15 canonical + 2 new arrays). Annex relationship type. Lifecycle status enum 5 states. Open items: DEC-049 routing default policy, R10 cross-ref exact storage shape verify, Sprint 2 EPIC #397 (obligation/rights reorg + Nhóm B metadata).*

*Hết v0.5 — cycle 5 DEC-048 EPIC #300 production fold (fulfillment + cascade chain + clause edit/re-read + provenance + evidence + date-anchored resolver). Bước kế tiếp: Document.provider column ratify (clause-gap), open_ended recurrence handling, NĐ 13 chat consent close pre-prod, KHE_AI LLM re-extraction path cho POST /reread v2.*

*Hết v0.4 — cycle 4 mega-fold (DEC-027/028/029/030 + Sprint 1 staging-complete). Bước kế tiếp: re-extraction script post-promote, `Document.provider` column ratify (clause-gap), open_ended_review recurrence handling Sprint 2, NĐ 13 chat learning consent close pre-prod.*
