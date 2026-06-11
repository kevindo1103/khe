# Glossary — Khế MVP

> Canonical terminology. BRD/SRS/CLAUDE.md reference these definitions. If a new term shows up in code or comms, it goes here.

---

## Document control

| Mục | Nội dung |
|---|---|
| Phiên bản | v0.1 |
| Trạng thái | Initial — extract từ BRD §6 + fold Sprint 0 schema + Strategy v2 |
| Owner | KHE_Docs |

---

## Changelog

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| v0.1 | 2026-06-11 | KHE_Docs | Initial. Extract BRD §6 terms + fold Backend schema field map (entry 7/8), AI extraction concept (entry 9), Strategy v2 terms (entry 4), Telegram bot (entry 2). |

---

## A. Domain objects

### Document
Một văn bản: **file gốc (bất biến)** + phân loại + các Term + liên kết quan hệ. Không phải chỉ là file — là object có cấu trúc với lifecycle (`processing` / `ready` / `failed`).

### Term / Field
Giá trị có cấu trúc bóc từ Document.
- **Minimum set (FR-EX-02):** `doi_tac`, `ngay_hieu_luc`, `thoi_han_hd`, `ngay_het_han` (nullable), `gia_tri`, `dieu_khoan_gia_han`.
- **Quality attrs:** `confidence` (FR-EX-05), `needs_review` (D-08).
- **Mutability:** mọi field cho người sửa; sửa → ghi `Event` (FR-EX-04).

### Obligation **(MVP heart)**
Cam kết rời rạc, có ngày, có trạng thái, suy ra từ Document.
- **Schema field map (Sprint 0):** `id`, `document_id`, `description`, `obligation_type` (`once` / `monthly` / `quarterly` / `yearly`), `due_date`, `status` (`pending` / `done` / `overdue` / `cancelled`), `remind_before_days`.
- **Derived vs extracted:** `due_date` có thể derived ở Obligation tier (vd `ngay_het_han = ngay_hieu_luc + thoi_han_hd`) thay vì bóc trực tiếp từ Document. Term nullable hợp lệ; derivation chạy ở engine. Xem SRS §6.1 FR-OB-01.

### Party
Đối tác trong tài liệu, **chuẩn hóa** để query "mọi HĐ với bên ABC" chạy đúng. Per-tenant table `parties` (`name`, `tax_code`, `address`, contact info).

### Event (Ledger)
Append-only bản ghi mọi thay đổi trạng thái (ingest, sửa term, hoàn thành nghĩa vụ, đã gửi nhắc…). Sửa = ghi event mới (reversal), **không edit-in-place**. Pattern tái dùng từ SpurX.

### Template / Clause
Mẫu/điều khoản do firm thẩm định, có version. *Định nghĩa sẵn nhưng chưa kích hoạt ở MVP — mở GĐ2.*

---

## B. Tenancy & partner

### Tenant
Một SME — cô lập dữ liệu hoàn toàn.
- **Schema field map (master.db `tenants`):** `id` (slug PK, vd `sme-abc-restaurant`), `name`, `db_path`, `plan` (`free` mặc định MVP), `is_active`, `created_at`.
- **Storage:** mỗi tenant 1 file SQLite riêng tại `tenants/<slug>.db`.

### Partner (Firm)
Một firm; role **xuyên-tenant** (nhìn nhiều SME theo phân quyền + consent).
- **Schema field map (master.db `firm_partners`):** `id`, `name`, `contact_email`, `contact_phone`, `is_active`.
- **Trong B2B2B (DEC-011):** firm là **khách hàng trả tiền** Phase 1 (~50-100k VND/client/năm), không chỉ là kênh phân phối.

### FirmTenantAccess
Bảng cấp consent partner xuyên-tenant (FR-AC-03, D-10).
- **Schema field map (master.db `firm_tenant_access`):** `firm_id` FK, `tenant_id` FK, `consent_status` (`pending` / `granted` / `revoked`), `granted_at`, `revoked_at`. Unique `(firm_id, tenant_id)`.
- **Lifecycle:** `pending → granted → revoked` (one-way; revoke terminal).

### TenantUser
User trong một tenant.
- **Schema field map (master.db `tenant_users`):** `tenant_id` FK, `username`, `hashed_password` (bcrypt), `role` (`staff` / `manager` / `admin`), `is_active`. Unique `(tenant_id, username)`.

---

## C. AI extraction

### VisionExtractionProvider
Protocol (Python `Protocol`) cho 1-call vision extraction (DEC-002 — không tách OCR + LLM riêng). Implementations Sprint 0:
- `GeminiFlashProvider` — `gemini-2.5-flash` (primary, ~59đ/doc)
- `ClaudeHaikuProvider` — Claude Haiku 4.5 (fallback, ~560đ/doc)
- `ClaudeSonnetProvider` — Claude Sonnet 4.6 (complex cases, ~1693đ/doc)

### ExtractionResult / ExtractedField
Output schemas. `ExtractedField` carries `value` + `confidence` + `needs_review` (D-08 enforcement: model trả `value=None` + `needs_review=True` khi không chắc, **không bịa**).

### Derived field
Field tính ở tầng Obligation thay vì bóc trực tiếp từ Document — vd `ngay_het_han` derive từ `ngay_hieu_luc + thoi_han_hd`. Xem SRS §6.1.

---

## D. Reminders & channels

### Telegram bot (DEC-006)
Kênh nhắc **chính** MVP. Bot token từ @BotFather (không cần approval). Replaced Zalo ZNS vì OA registration 4-6 tuần là blocker timeline.
- Env vars: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- Fallback: email.

### ~~Zalo ZNS~~ (deprecated MVP)
Originally proposed kênh chính, deprecated bởi DEC-006. Có thể reconsider GĐ2 làm paid channel — chờ DEC-016 decision (freemium paywall lever).

---

## E. Strategy v2 concepts (DEC-011..015)

### B2B2B
Mô hình Khế Phase 1: **Firm pays**, **SME free**. Firm (đại lý thuế / law firm) mua suất cho danh mục SME của họ (~50-100k VND/client/năm). SME-pays mở ở GĐ2 (drafting/review lawyer-in-loop, 2027). DEC-011.

### Concierge onboarding
Quy trình "ôm cả ngăn kéo": Khế hoặc firm partner tới văn phòng SME, **số hóa tận nơi** toàn bộ kho giấy tờ trong 1 ngày. Áp dụng 20 SME đầu để chứng minh value loop khỏi ma sát upload. M-1 chỉ đo retention sau concierge baseline. DEC-012.

### 2-firm pilot
Thay mục tiêu cũ "1 firm LOI" → song song **1 đại lý thuế + 1 law firm**, mỗi firm 10 SME, so sánh kênh sau 90 ngày. DEC-013.

### Positioning — hậu sóng NĐ 337
Khế **không cạnh tranh tầng ký số** (VNPT eSign, FPT.CA, nền tảng NĐ 337). Đón **hậu sóng** — sau khi HĐ điện tử được ký, Khế là "ngôi nhà cho mọi HĐ sau khi ký". DEC-014.

### Kill / Pivot signals
3 signals trigger pivot sau 90 ngày 2-firm pilot:
- **K-1:** Retention W4 SME < 30% post-concierge → pivot DMS cho firm nhỏ.
- **K-2:** Firm không trả + SME tự convert tốt → pivot direct freemium.
- **K-3:** 2 firm không đẩy nổi 10 SME/90 ngày → đổi kênh hiệp hội/community.

DEC-015.

### Obligation graph (GĐ3)
Vision dài hạn 2027+: Khế làm **hạ tầng** đồng bộ nghĩa vụ — nối Obligation core với công nợ, hóa đơn điện tử, ngân hàng. Khế trở thành lớp sync nghĩa vụ tài chính + pháp lý.

---

## F. Process / ops terms

### DOCS_INBOX
GitHub issue #1 (pinned). Single queue cho mọi report cần fold vào canonical docs. Owner: KHE_Docs. Sessions khác MUST comment trong 24h sau merge.

### FM-XX
Failure Mode — recurring process bug. Append vào CLAUDE.md Common Bug Patterns.

### INC-XX
Incident — specific bad event với root cause. Tracked riêng.

### Sprint 0 / M-1 / M0..M3
Milestones per BRD §13:
- **Sprint 0**: Infrastructure bootstrap (FastAPI scaffold, CI/CD, Telegram wired).
- **M-1**: Concierge baseline — 2 firm pilot signed + 20 SME baseline kho.
- **M0**: Vertical slice — 1 doc end-to-end.
- **M1**: Real product — 3 doc types + self-serve.
- **M2**: Firm portal.
- **M3**: Harden + launch.

### D-rules / P-rules
- **P-1..P-5**: Top-level principles (BRD §4). Guardrails ràng buộc mọi requirement.
- **D-01..D-10**: Derived business rules (CLAUDE.md §Business Rules). Implementation-facing.

---

*Hết v0.1. Bước kế tiếp: thêm UI terms khi Frontend session spawn.*
