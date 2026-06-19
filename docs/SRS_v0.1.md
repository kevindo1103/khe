# SRS — Khế MVP (Software Requirements Specification)

> Technical contract spec. Drives backend/frontend implementation. Pairs with `MVP_BRD_Khe_v0.1.md` (business intent) — SRS is the **how**.

---

## Document control

| Mục | Nội dung |
|---|---|
| Phiên bản | v0.2 |
| Trạng thái | Fold cycle 3 — ingest endpoints + relationships + CANONICAL_FIELDS + quota schema + extraction module API |
| Owner | KHE_Docs |
| Source of truth | BRD v0.4 (`MVP_BRD_Khe_v0.1.md`) — SRS không định ra business rule mới |

---

## Changelog

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| v0.1 | 2026-06-11 | KHE_Docs | Initial. Fold Sprint 0 backend scaffold: API contract `/auth/login` + `/health`, JWT claims, master.db (4 bảng) + per-tenant (7 bảng) schema. Fold FR-OB-01 derivation rule (entry 9). |
| v0.2 | 2026-06-19 | KHE_Docs | Cycle 3 fold (5 Backend + 1 AI + 1 PM comments). Add §2 ingest/documents/relationships API (PR #54 + #59 + #60 — staging live). Add §4 tenants quota columns (FR-TN). Update §5.2 terms CANONICAL_FIELDS 7 + §5.1 doc_type enum. Add §5.8 `document_relationships` table. Add §9 Extraction module API (`get_extraction_provider` factory, `ExtractionUnavailable`, `is_error` vs `needs_review`). Add §10 Audit Events (`extraction_performed` w/ `consent_reference`, term `updated` PII). |

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

### 2.7 Public API surface boundary

Cookie auth (not Bearer). All endpoints above except `/auth/*` + `/health` + `/` require active session.

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

### 3.3 SQLite tuning (anti-deadlock)

- WAL mode enabled (`PRAGMA journal_mode=WAL`).
- `synchronous=NORMAL` (mitigate same-thread deadlock pattern — xem CLAUDE.md Common Bug Patterns).

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

---

## 5. Schema — per-tenant `tenants/<slug>.db` (7 bảng)

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
| `created_at` | Upload timestamp |

### 5.2 `terms` — EAV with CANONICAL_FIELDS vocab (Backend M0 contract)

Per-Document extracted Term rows. Schema is **EAV** (entity-attribute-value); `field_name` is constrained to `CANONICAL_FIELDS` vocab (7 values, Backend `modules/extraction/schemas.py`):

1. `doi_tac` — đối tác
2. `ngay_hieu_luc` — ngày hiệu lực
3. `ngay_het_han` — ngày hết hạn (**nullable**, derivable per §6.1)
4. `gia_tri_hd` — giá trị HĐ *(renamed from `gia_tri` per Backend correction 2026-06-18)*
5. `thoi_han_hd` — thời hạn HĐ
6. `dieu_khoan_gia_han` — điều khoản gia hạn
7. `dieu_khoan_thanh_toan` — điều khoản thanh toán *(new per Backend correction 2026-06-18)*

| Column | Note |
|---|---|
| `id` | PK |
| `document_id` | FK → `documents` |
| `field_name` | VARCHAR, value ∈ CANONICAL_FIELDS above |
| `field_value` | TEXT (free form; date/numeric coercion at consumer) |
| `confidence` | FLOAT, per FR-EX-05 |
| `needs_review` | BOOLEAN, D-08 / FR-EX-05 |

### 5.3 `obligations` (trái tim MVP)

| Column | Note |
|---|---|
| `id` | PK |
| `document_id` | FK → `documents` |
| `description` | Mô tả nghĩa vụ |
| `obligation_type` | `once` / `monthly` / `quarterly` / `yearly` |
| `due_date` | DATE — derived hoặc trực tiếp |
| `status` | `pending` / `done` / `overdue` / `cancelled` |
| `remind_before_days` | INTEGER (default 30, 7) |

### 5.4 `parties`
Party normalization (FR-DR-02). Fields: `name`, `tax_code`, `address`, `contact_*`.

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

`obligation_type` lặp → expand instances per FR-OB-02. Detail TBD Sprint 1.

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

---

## 10. Audit Event types (NĐ 13/2023 compliance)

Events in per-tenant `events` ledger. Append-only.

| `event_type` | `entity_type` | Actor | Trigger | Payload |
|---|---|---|---|---|
| `consent_granted` | `tenant` / `firm_partner` | SME / admin | Consent grant flow | `{consent_kind, consent_reference}` |
| `consent_revoked` | `tenant` / `firm_partner` | SME / admin | Consent revoke | `{consent_kind, consent_reference}` |
| `extraction_performed` | `document` | `"system"` | Backend PR #60 worker post-extract | `{provider, model, cost_vnd, latency_ms, consent_reference}` — `consent_reference` provides O(1) back-link to the consent record per Compliance §A.2 |
| `extraction_failed` | `document` | `"system"` | Worker hit `is_error` or `ExtractionUnavailable` | `{reason, provider}` |
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

*Hết v0.2 — cycle 3 fold: ingest/documents/relationships endpoints + CANONICAL_FIELDS + DocType enum + quota schema + extraction module API + Audit Events. Bước kế tiếp: Sprint 1 obligation engine + reminder scheduler spec (issue #26).*
