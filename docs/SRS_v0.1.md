# SRS — Khế MVP (Software Requirements Specification)

> Technical contract spec. Drives backend/frontend implementation. Pairs with `MVP_BRD_Khe_v0.1.md` (business intent) — SRS is the **how**.

---

## Document control

| Mục | Nội dung |
|---|---|
| Phiên bản | v0.1 |
| Trạng thái | Initial — fold Sprint 0 backend scaffold (DOCS_INBOX entries 7, 8) |
| Owner | KHE_Docs |
| Source of truth | BRD v0.2 (`MVP_BRD_Khe_v0.1.md`) — SRS không định ra business rule mới |

---

## Changelog

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| v0.1 | 2026-06-11 | KHE_Docs | Initial. Fold Sprint 0 backend scaffold: API contract `/auth/login` + `/health`, JWT claims, master.db (4 bảng) + per-tenant (7 bảng) schema. Fold FR-OB-01 derivation rule (entry 9). |

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
File metadata + phân loại. Fields per BRD §6 (file path bất biến, loại HĐ, upload_at, uploader_id, status `processing` / `ready` / `failed`).

### 5.2 `terms`
Extracted Term per Document. Khớp FR-EX-02:
- `doi_tac` (party)
- `ngay_hieu_luc` (DATE, nullable)
- `thoi_han_hd` (string, có thể số hoặc phi-số)
- `ngay_het_han` (DATE, **nullable** — derivable, xem FR-OB-01)
- `gia_tri` (numeric)
- `dieu_khoan_gia_han` (text)
- `confidence` (FLOAT, per FR-EX-05)
- `needs_review` (BOOLEAN, D-08 / FR-EX-05)

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

## 8. Open items (Sprint 1+)

| ID | Item | Owner |
|---|---|---|
| O-1 | Per-tenant Alembic migration loop (replace `create_all`) | KHE_Backend |
| O-2 | `tenant_users.tenant_id` index in migration | KHE_Backend |
| O-3 | `thoi_han_hd` phi-số policy (a/b/c) | PM decision |
| O-4 | Login email→tenant lookup (replace explicit `tenant_id`) | PM / KHE_Backend |
| O-5 | `regen_openapi.py` run khi `docs/openapi.json` ready | KHE_Backend |

---

*Hết v0.1 — Sprint 0 baseline. Bước kế tiếp: Sprint 1 obligation engine + reminder scheduler spec.*
