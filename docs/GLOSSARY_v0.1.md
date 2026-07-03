# Glossary — Khế MVP

> Canonical terminology. BRD/SRS/CLAUDE.md reference these definitions. If a new term shows up in code or comms, it goes here.

---

## Document control

| Mục | Nội dung |
|---|---|
| Phiên bản | v0.8 |
| Trạng thái | Fold cycle 7 — DEC-055 tier + DEC-056 Obligation OS + Design System v1.1 |
| Owner | KHE_Docs |

---

## Changelog

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| v0.1 | 2026-06-11 | KHE_Docs | Initial. Extract BRD §6 terms + fold Backend schema field map (entry 7/8), AI extraction concept (entry 9), Strategy v2 terms (entry 4), Telegram bot (entry 2). |
| v0.2 | 2026-06-18 | KHE_Docs | Fold DOCS_INBOX 13/14: add §G Strategy framework terms — Persona, JTBD, Golden Circle (Why-How-What), Dunford Positioning Thesis, B2B2B channel motion vs PLG, Obligation OS, Vertical wedge (DEC-018), Plan B contingency. |
| v0.3 | 2026-06-19 | KHE_Docs | Cycle 3 fold. Add §H Backend M0 vocab — CANONICAL_FIELDS (7), DocType enum. Add §I Document relationships — amends vs references_framework, last_writer_wins, source_doc_chain. Update §C Extraction — `get_extraction_provider`, `ExtractionUnavailable`, `is_error` vs `needs_review`. Add §J Tenant quota — FR-TN-01..03, doc_quota nullable, calendar reset, hard block 429. |
| v0.4 | 2026-06-19 | KHE_Docs | **DEC-026 fold (PRIORITY gate Backend #99 issue #100).** Add §A `Clause` entity — text nguyên gốc từ Document, distinct from Term/Field (structured). Per-tenant `clauses` table (SRS §5.9). Powers `search_clauses` tool (BRD FR-CQ-02). Rename old `Template / Clause` row → `Template (GĐ2)` to avoid name collision. |
| v0.8 | 2026-07-03 | KHE_Docs | **Cycle 7 fold — DEC-055 + DEC-056 + DS v1.1.** §N NEW Servanda / Ledger tier / AI tier / per-doc quota / R-7 resolved / rule pack / compliance obligation / Obligation OS / D-16 no-paywall-safety / D-17 firm-confirms-compliance. §A Obligation `obligation_type` +`penalty`. §A Document +`may_have_unextracted_obligations`. §D Design System v1.1 (Lục Khế / border-strong / 13 badges / Hợp đồng A11y / elevation e0-e3 / done tokens). §L Karpathy 3 process additions cross-ref CLAUDE.md. §M ProcessingStage enum extension. §O NEW `is_garbled_vietnamese` + Two-Pass Skeleton/Fill + FallbackProvider warnings. |
| v0.7 | 2026-06-29 | KHE_Docs | **Cycle 6 fold — DEC-049 hybrid OCR + DEC-050 R1-R10 EPIC #362 production.** §A NEW Definition entity (R9), CrossReference entity (R10), Lifecycle Status enum (R8). §A Document/Party/Clause entities expanded. §C +hybrid_ocr provider (DEC-049). §N NEW DEC-050 vocab section: title/contract_number, lifecycle_status state machine, clause_path hierarchy, party.is_self + aliases, annex relationship, Definition + CrossReference, signature flags, admin extraction metrics, processing pipeline stages. |
| v0.6 | 2026-06-27 | KHE_Docs | **Cycle 5 fold — DEC-048 EPIC #300 production.** §A Obligation rewrite expanded (fulfilled_at G1 anchor, awaiting_confirmation, source_clause_num, derived_from, source P1). §A NEW ClauseEditEvent (§13 addendum) + Evidence Document. §M NEW Fulfillment + Cascade Chain section (DEC-048 vocab: fulfillment capture, propagate_obligation_done, cascade-past, awaiting_confirmation, anchor=fulfilled_at G1, P1 merge rule, derive delete path-2 guard, waiting_trigger + _detect_anchor_field, obligation_fulfillment purpose enum, evidence_attached). |
| v0.5 | 2026-06-20 | KHE_Docs | **Cycle 4 fold.** §A: Obligation entity rewritten (8 categories + 5 cadences + direction + obligor + status enum correction). NEW Quyền lợi sub-concept. Party +role_label + self-party. §C augmented: 2-tier extraction schema (Claude lean / Gemini full), PaymentScheduleItem, PartyItem, NamedExtractedField, DOC_TYPE_GROUPS enum 11, BASE/V2_UNIVERSAL/TYPE_SPECIFIC field tiers. §K NEW Direction model (DEC-030) — direction, obligor, legal_name, tenant_profile, self-party match. §L NEW Chat tool surface evolved (value_contains, party_filter, doc_type_filter, due_from/to, truncation_hint, today's-date injection, _is_negative_answer, NĐ 13 compliance debt). §B Tenant +tenant_profile separate model row. |

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
Cam kết rời rạc, có ngày, có trạng thái, suy ra từ Document. **Schema rewritten cycle 4 per #122 Option B + DEC-027/030:**
- **`obligation_type`** = **category enum 8** (DEC-027): `payment` · `delivery` · `handover` · `expiration` · `renewal` · `review` · `warranty` · `other`. *Trước cycle 4 field này là cadence — đã renamed (xem `recurrence`).*
- **`recurrence`** = cadence enum: `once` · `monthly` · `quarterly` · `yearly` · `open_ended_review`. `open_ended_review` = `thoi_han_hd` phi-số case (DEC-020), `due_date=NULL`.
- **`status`** = `{pending, done, cancelled}` (FE PR #69 ratified). `overdue` = FE-derived urgency bucket NOT status.
- **`direction`** (DEC-030): `nghĩa_vụ` / `quyền_lợi` / `null` per `obligor` match `legal_name`.
- **`obligor`**: tên party chịu nghĩa vụ.
- **`source_doc_chain`**, **`resolution_method`**: chain resolution (DEC-019..021). Derived obligations luôn set; payment-schedule obligations KHÔNG set (idempotency key).
- **`fulfilled_at`** / **`fulfilled_by`** / **`evidence_doc_ids`** (DEC-048): ngày + actor + bằng chứng khi SME ghi nhận hoàn thành. `fulfilled_at` là **anchor** cho cascade chain (G1 fix per §M).
- **`source_clause_num`** + **`derived_from`** (Kevin Option B 0a, PR #303): clause provenance. Enables clause-scoped re-derive (§M).
- **`source`** (P1 merge rule, PR #311): `ai_extracted` / `user_manual` / `ai_re_derived`. `user_manual` obligations **protected from re-derive delete**.
- **Status enum extended** (DEC-048): `pending` · `done` · `cancelled` · `awaiting_confirmation` (cascade-past D-02) · `waiting_trigger` (FR-OB-13 unresolved date anchor).
- **Derived vs extracted:** `due_date` có thể derived (vd `ngay_het_han = ngay_hieu_luc + thoi_han_hd`); payment_schedule items → `payment` Obligation rows. Xem SRS §6.1/6.3.

### Quyền lợi (DEC-030)
Sub-concept Obligation. Cam kết của **đối tác** hướng *về* SME (đối tác trả tiền cho SME, đối tác bảo hành, đối tác giao hàng). UI tab riêng (Nghĩa vụ / Quyền lợi). Reminder label khác: *"Đối tác [obligor] cần [action] cho bạn trước [date]."*

### Party
Đối tác trong tài liệu, **chuẩn hóa** để query "mọi HĐ với bên ABC" chạy đúng. Per-tenant table `parties`:
- `name`, `tax_code`, `address`, contact info.
- **`role_label`** (DEC-030): vai trò trong HĐ (`"Owner"`, `"Bên A"`, `"NSDLĐ"`, `"Bên thuê"`, ...) — extracted verbatim, D-06 read-only. AI KHÔNG quyết bên nào là SME.

### Self-party (DEC-030)
SME entity = `tenant_profile.legal_name`. Auto-match `parties[].name` per Document để derive Obligation `direction`. Match fail → `direction=NULL` + `needs_review=true` (Kevin cycle 4 q3 ratify).

### `tenant_profile` (DEC-030)
Separate master.db model from `tenants` (Kevin cycle 4 q2 ratify — NOT PM-recommended column embed). 1:1 với `tenants`. Canonical store cho `legal_name` + `legal_name_aliases` + future SME profile fields (industry/size/address). Empty `legal_name` → all docs' obligations need user review. Detail SRS §4.5.

### Event (Ledger)
Append-only bản ghi mọi thay đổi trạng thái (ingest, sửa term, hoàn thành nghĩa vụ, đã gửi nhắc…). Sửa = ghi event mới (reversal), **không edit-in-place**. Pattern tái dùng từ SpurX.

### Clause (DEC-026)
Điều khoản rời từ Document, có số thứ tự (`clause_num`, vd `"Điều 8"`) + tiêu đề (`title`, vd `"Chấm dứt hợp đồng"`) + nội dung đầy đủ (`content`) + vị trí trang. **Phân biệt với Term/Field:** Term = giá trị có cấu trúc (CANONICAL_FIELDS, date/numeric coercion). Clause = **text nguyên gốc**, preserve wording. Per-tenant table `clauses` (SRS §5.9). Populated từ `VisionExtractionResult.clauses[]` cùng vision call. Powers `search_clauses` tool (FR-CQ-02).

**Editable (DEC-048 §13 addendum):** SME có thể sửa clause inline. Lần edit đầu Backend snapshot vào **`original_content`** (immutable sau first write — D-07 audit). UI surface "đã sửa" badge + "Xem bản gốc (AI)" toggle.

### ClauseEditEvent (DEC-048 §13 addendum)
Snapshot event khi SME sửa clause. Fields: `clause_id`, `clause_num`, `original_content` (immutable), `edited_content`, `edited_by`, `edited_at`, `re_read_triggered` (bool), `re_read_at`, `re_read_result_id`. Event ledger row có shape PII-safe: log content **lengths** không log raw text (D-12). Wired qua `PATCH /documents/{id}/clauses/{clause_id}` (PR #325, migration `tenant_018`).

### Evidence Document (DEC-048)
Document upload với `is_evidence=true` — biên bản nghiệm thu, hóa đơn thanh toán, biên nhận đính kèm khi SME ghi nhận hoàn thành nghĩa vụ. **Server-side skip `provider.extract()`** (P2 rule). `contains_personal_data` default `true` (conservative). DEC-039 firm gate: firm portal chỉ thấy metadata (file_name + created_at), không thấy binary. Link với obligation qua `Obligation.evidence_doc_ids[]`.

### Document (DEC-050 R1/R6/R8 expansion)
Trên top of DEC-026 (clauses) + DEC-048 (is_evidence), DEC-050 thêm dense business fields lên `documents` table (denormalized cho fast UI rendering):
- `title` + `contract_number` (R1) — bóc từ `tieu_de_hd`/`so_hop_dong`, user-editable D-07
- `signing_date` + `commencement_date` (R6) — bóc từ `ngay_ky`/`ngay_khai_truong`, ISO-normalized
- `contract_duration` + `lifecycle_status` (R8 — xem entry riêng)
- `has_signature` + `signature_pages` (R5b)
- `extraction_model`/`latency_ms`/`warnings` (admin metrics, cycle 6)
- `processing_stage`/`progress` (extraction polling, cycle 6)

### Definition (DEC-050 R9 — NEW entity)
Glossary entry từ section "Định nghĩa" của Document. Per-tenant `definitions` table (`tenant_027` migration). Fields: `id`, `document_id`, `clause_id` NULLABLE, `term`, `definition`, `original_term` (D-07 first-edit snapshot — pattern mirror `clauses.original_content`). CRUD endpoints: `GET/PATCH/DELETE /documents/{id}/definitions[/{def_id}]`. Event log mỗi edit/delete với old/new per field. Rollup `definition_count` trên `DocumentListItem` + `DocumentDetailOut`.

### CrossReference (DEC-050 R10 — NEW entity)
Tham chiếu nội bộ trong Document (`"Điều 5"`, `"Khoản 2 Điều 5"`, `"Phụ lục A"`, etc.). Service `app/services/cross_ref.py` (PR #392) detect VN legal patterns post-extraction. Resolve intra-doc clause refs + appendix-via-annex (qua `document_relationships`). Orphan flagged khi target không tồn tại. Field shape: `source_clause`, `target_ref` (raw), `target_type` (`clause` / `sub_clause` / `appendix`), `resolved`, `target_clause_id` (NULL khi orphan). Endpoints: `GET /documents/{id}/cross-refs`, `POST /documents/{id}/cross-refs/resolve` (re-run resolver). FE inline clickable rendering + `OrphanRefPanel` (PR #395).

### Lifecycle Status (DEC-050 R8 enum)
`documents.lifecycle_status` 5-state machine:
- **`active`** — đang hiệu lực (within term, not expired)
- **`expiring`** — sắp hết hạn (≤30 ngày tới `expiry_date`)
- **`expired`** — đã quá hạn
- **`settled`** — hoàn thành / kết thúc (manual override)
- **`suspended`** — tạm dừng (manual override)

Backend `lifecycle.py::derive_lifecycle_status()` compute 3 đầu auto từ `expiry_date` + `contract_term`. Last 2 = user manual flip qua UI. FE badge per `mockup_document_detail_v3.jsx` (5 colors).

### Annex relationship type (DEC-050 R4 extends DEC-019)
Third value trong `document_relationships.relationship_type` enum (migration `tenant_024` PR #385). Distinct from `amends`:
- `amends` requires keyword (sửa đổi / bổ sung / thay thế) — triggers `resolve_chain` overwrite
- `annex` = phụ lục độc lập đính kèm (alphanumeric capture với negative lookahead) — KHÔNG overwrite, excluded từ chain resolve filter

### Hybrid OCR provider (DEC-049, KHE_AI PR #341)
4th provider trong extraction `_REGISTRY`: `hybrid_ocr`. 2-pass: (1) `scan_detect.is_scanned_pdf()` heuristic (pdftotext < 50 chars/page → scanned); (2) Document AI OCR cho scanned (gated `GOOGLE_APPLICATION_CREDENTIALS`) hoặc `extract_embedded_text()` cho digital → Gemini Flash text-mode (`build_text_instruction()` prompt variant) → `ContractExtractionLLMFull`. System deps VPS: `poppler-utils`. Currently opt-in only (`prefer="hybrid_ocr"`); auto-route default chờ Kevin ratify.

### `clause_path` (DEC-050 R3)
Dot-separated hierarchy path trên `clauses.clause_path` (vd `"2.1.3"` = Điều 2, Khoản 1, Mục 3). Synthesized post-extraction bởi `clause_hierarchy.py` regex service (NOT LLM). Cho phép navigate tree, render indent UI, deep-link clause.

### Party aliases + `is_self` (DEC-050 R2)
`parties.aliases` JSON array — tên gọi khác / viết tắt (vd `["CTCP TTCR", "Tran Thai", "Trần Thái"]`). `is_self` BOOL — flipped `true` sau DEC-030 `legal_name` auto-match success. Cho phép chat tool `party_filter` match qua alias + render UI rõ "bên nào là bạn".

### Signature flags (DEC-050 R5b)
`documents.has_signature` BOOL NULLABLE + `signature_pages` JSON list[int]. NULL = pre-migration docs (UI hide badge). FE `SignatureBadge`: green "Đã ký (trang X, Y)" / yellow "Chưa ký" (PR #401).

### Admin extraction metrics (cycle 6, Backend PR #350)
Super-admin observability surface. Schema cols on `documents` (`tenant_019`): `extraction_model`, `extraction_latency_ms`, `extraction_warnings`. Endpoints `GET /admin/extraction-metrics` + `summary`. Gated `require_superadmin` (`SUPERADMIN_USERS` env-var allowlist, PM Option B no DB migration).

### Processing pipeline stages (cycle 6, Backend PR #374)
`documents.processing_stage` enum + `processing_progress` integer (`tenant_020`). 4 checkpoints: `ocr` 30% → `llm` 60% → `saving` 90% → `done` 100%. `_mark_failed()` reset → 0 + stage `failed`. FE polls `DocumentListItem`/`DetailOut` cho progress UX.

### Template (GĐ2)
Mẫu HĐ do firm thẩm định, có version. *Định nghĩa sẵn nhưng chưa kích hoạt ở MVP — mở GĐ2 (lawyer-in-loop drafting).*

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

### `get_extraction_provider()` factory
Public API entry point (Backend gọi) cho extraction module. Selection + key handling + DEC-002 fallback (Gemini → Haiku) gói trong factory. Backend stays policy-free. Backend KHÔNG construct provider trực tiếp. KHE_AI PR #55/#58.

### `ExtractionUnavailable`
Typed exception raised bởi factory khi không có API key / SDK missing. Backend map → **503** + `documents.status="failed"`. Khác per-field `needs_review`.

### `is_error` vs `needs_review` (do NOT conflate)
- `ExtractionResult.is_error` (property): extraction completed nhưng hit hard error. **Không có Term persist**. Map → `status="failed"`.
- `terms[].needs_review` (per-field): extraction succeeded nhưng confidence thấp. Term persist + flag. Map → human-verify queue + `documents.needs_review=true`.

### 2-tier schema (DEC-026 addendum + DEC-029)
Provider grammar limits → tách 2 schemas:
- **`ContractExtractionLLM`** — 7 BASE_CANONICAL_FIELDS lean. Used by Claude (fallback). Schema rộng → "Schema is too complex" 400 deterministic.
- **`ContractExtractionLLMFull`** — 12 universal + `clauses[]` + `parties[]` + `payment_schedule[]` + `NamedExtractedField` keyed list (type-specific). Used by Gemini Flash (primary).

**Consequence:** doc qua Claude fallback có `clauses=[]` / `parties=[]` / `payment_schedule=[]` / `doc_type_group=NULL`. Gemini path = full. Re-extract-prefer-Gemini policy chờ `Document.provider` column ratify.

### `DOC_TYPE_GROUPS` (DEC-029)
Enum 11 (10 contract groups + `other`): `dan_su` · `thuong_mai` · `lao_dong` · `bat_dong_san` · `van_tai_logistics` · `xay_dung` · `cong_nghe_ip` · `tai_chinh` · `bao_dam` · `hanh_chinh` · `other`. Collapse từ 126 loại HĐ (nguồn: lawyer Danh mục HĐ). Phân loại đầu tiên trong extraction → drive type-specific field set.

Old `DocType` enum (4 values: `hd_thue_mat_bang` / `hd_nha_cung_cap` / `hd_lao_dong` / `khac`) deprecated nhưng retained on Document for M0 legacy docs.

### `BASE_CANONICAL_FIELDS` / `V2_UNIVERSAL_FIELDS` / `TYPE_SPECIFIC_FIELDS`
3 tiers extraction fields per DEC-029:
- **BASE 7:** `doi_tac`, `ngay_hieu_luc`, `ngay_het_han`, `gia_tri_hd`, `thoi_han_hd`, `dieu_khoan_gia_han`, `dieu_khoan_thanh_toan`. Claude fallback floor.
- **V2_UNIVERSAL 5:** `doc_type_group`, `ngay_ky`, `tien_dat_coc`, `thoi_han_bao_hanh`, `thoi_han_thong_bao`. Gemini-only.
- **TYPE_SPECIFIC ~30:** 9 groups (lao_dong, bat_dong_san, xay_dung, bao_dam, cong_nghe_ip, thuong_mai, van_tai_logistics, tai_chinh, hanh_chinh) — bóc khi nhóm khớp. Emit qua `NamedExtractedField` keyed list.

### `NamedExtractedField`
Pydantic model `{name: str, value: ExtractedField}` — list of these in Gemini schema để workaround "too many states" error trên flat dict-of-fields. Backend PR #141 dynamic iteration `result.fields.items()` persist từng item thành Term row.

### `PaymentScheduleItem` (DEC-027 + DEC-030)
`{amount: str, due_date: date | None, milestone: str | None, recurrence: str | None, payer: str | None}`. Cùng vision call, không tốn cost. Backend derive thành `payment` Obligation per item có `due_date` (PR #141). `payer` (DEC-030) drives Obligation `obligor` + `direction`.

### `PartyItem` (DEC-030)
`{name: str, role_label: str}` — vai trò các bên trong HĐ extracted verbatim. Gemini-only.

### `pydantic-settings env_file` vs `os.environ` (Backend PR #80)
**Bug pattern:** `pydantic-settings` `env_file` populates `Settings` class only, **KHÔNG** `os.environ`. Providers reading `os.environ.get()` (vd `modules/extraction/providers/*`) miss vars → `ExtractionUnavailable`. Fix: systemd `EnvironmentFile=` directive on `.service` unit. `/health/extraction` diagnostic surface (non-prod) detects this.

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

---

## G. Strategy framework (DEC-018 / PRODUCT_STRATEGY v0.2)

### Persona
Mô tả profile người dùng cụ thể trong B2B2B motion. Khế có 3:
- **Firm Champion / Economic Buyer** (chị Hằng, chủ đại lý thuế) — người trả tiền.
- **SME Owner** (anh Dũng) — primary user, free Phase 1.
- **SME Admin / Ops** (bạn Linh, kế toán) — secondary user, xử lý upload + sửa field.

Định nghĩa đầy đủ trong `PRODUCT_STRATEGY_Khe_v0.2.md` §2.

### JTBD (Jobs to be Done)
Framework xác định **job** khách hàng "thuê" Khế hoàn thành. Format: *"Khi [tình huống], tôi muốn [động lực], để [kết quả]"*. Khế có 5+1 jobs (J1-J5 + J-E emotional). **J2 là trái tim** (nhắc trước hạn — Obligation engine + Telegram). Detail: PRODUCT_STRATEGY §3.

### Golden Circle (Why-How-What)
Framework Simon Sinek. Khế:
- **WHY:** Không SME nào nên mất tiền/cơ hội vì HĐ đã ký bị bỏ quên.
- **HOW:** (1) Đi qua người SME đã tin (firm), (2) AI chỉ-đọc bóc nghĩa vụ VN, (3) File tĩnh → dòng nhắc, (4) Tập trung hậu-ký.
- **WHAT:** Ingest + Retrieve + Deadline trên multi-tenant phân phối qua firm portal.

Detail: PRODUCT_STRATEGY §4.

### Dunford Positioning Thesis
Framework April Dunford 5-component (competitive alternatives / unique attributes / value+proof / target market / market category). Khế Positioning Thesis (lỏng, tinh chỉnh qua pilot):

> Cho SME VN không có phòng pháp lý nhưng đã có cố vấn ngoài, Khế là **Hệ điều hành nghĩa vụ hợp đồng hậu-ký** — vận hành bởi chính firm trên kho client của họ — khác Google Drive/Excel/trí nhớ ở chỗ biến nghĩa vụ rời rạc thành dòng nhắc có hệ thống, đón hậu sóng NĐ 337.

Detail: PRODUCT_STRATEGY §5.

### B2B2B channel motion vs PLG
2 GTM motion:
- **Channel-led B2B (Khế chọn Phase 1):** bán qua firm vốn có quan hệ SME; concierge onboarding; firm trả per-client.
- **Mass self-serve (PLG, contingency):** SME tự đăng ký, tự trả ($30-100/mo); CAC thấp, onboarding 15 phút. Kích hoạt nếu Kill signal K-2 trigger (firm không trả + SME convert tốt).

DEC-011 chọn channel-led; self-serve giữ làm Plan B. Detail: PRODUCT_STRATEGY §6 + §10.

### Obligation OS
Định danh category Khế: *"Hệ điều hành nghĩa vụ & tài liệu hợp đồng hậu-ký cho SME — phân phối qua cố vấn ngoài."* **KHÔNG** là CLM enterprise (drafting/redlining/e-sign). Tránh kỳ vọng sai.

### Vertical wedge (DEC-018 — OPEN)
Wedge = ngành cụ thể chọn làm beachhead. Khế **không khóa wedge trước** — lõi general (multi-tenant, đa loại doc, obligation graph), chọn theo tín hiệu pilot. Tiêu chí: (a) lượng HĐ tạo đau, (b) firm sẵn phục vụ, (c) HĐ có nghĩa vụ ngày-tháng để bóc. F&B/bán lẻ là 1 ứng viên; không độc quyền.

### Plan B blueprint
Self-serve PLG motion tham chiếu (~$30-100/mo SME-pays trực tiếp). Gắn DEC-015 K-2 kill signal — nếu firm không trả + SME tự convert tốt qua paywall reminder → bỏ B2B2B, chuyển direct freemium. Tracked PRODUCT_STRATEGY §6 + §10.

---

---

## H. Backend M0 contract vocab

### CANONICAL_FIELDS
Tập 7 giá trị **field_name** cố định cho `terms.field_name` (EAV per-tenant). Source: `backend/modules/extraction/schemas.py`. Frontend display + Backend persist đều dùng vocab này:

1. `doi_tac`
2. `ngay_hieu_luc`
3. `ngay_het_han` (nullable, derivable per FR-OB-01)
4. `gia_tri_hd` *(renamed from `gia_tri` 2026-06-18 — Backend M0 correction)*
5. `thoi_han_hd`
6. `dieu_khoan_gia_han`
7. `dieu_khoan_thanh_toan` *(new 2026-06-18 — Backend M0 correction)*

### DocType (enum)
`documents.doc_type` value (Backend M0 contract):
- `hd_thue_mat_bang` — HĐ thuê mặt bằng (lease)
- `hd_nha_cung_cap` — HĐ nhà cung cấp (supplier)
- `hd_lao_dong` — HĐ lao động (labor)
- `khac` — other

KHÔNG dùng placeholder string như `"lease"` — must be enum value.

---

## I. Document relationships (Backend PR #59, DEC-019/020/021)

### `document_relationships` (table)
Per-tenant edges between Documents. AI suggests `pending`; SME confirms (D-02).

### Relationship types
- **`amends`** — phụ lục / addendum chỉnh sửa parent contract.
- **`references_framework`** — HĐ con tham chiếu HĐ khung; không superseded.

Classified by phrasing heuristic. Conservative — DEC-019 no legal judgment by AI.

### Orphan amendment
Edge có `to_doc_id=null` + `unresolved_ref` chứa filename/phrase. **Late-link** khi parent doc upload sau.

### `last_writer_wins` chain resolution
Khi SME confirm relationship → `resolve_chain` traverses **amends topology** (không theo upload time) → supersede overlapping Terms via `is_superseded` + `overrides_term_id` + `inherited_from_doc_id`. Existing Obligations annotated với `source_doc_chain` + `resolution_method="last_writer_wins"`.

### `source_doc_chain`
Array of doc_ids ghi nguồn của Obligation đi qua amends chain. Audit trail cho conflict resolution.

---

## J. Tenant quota & billing (FR-TN, D-11)

### `doc_quota`
Per-tenant quota docs/month. Column `master.db tenants.doc_quota`. **Nullable** = unlimited (admin tenants). Default firm-configurable per SME (KHÔNG hard-code global).

### `docs_used_month` / `quota_reset_at`
Counter + reset boundary. Increment on success `POST /ingest/*`. Reset mùng 1 mỗi tháng via APScheduler.

### Calendar-month reset
Khế chọn **calendar month** (mùng 1) thay vì rolling 30 days. Đơn giản, dễ explain cho firm. Kevin ratified cycle 3 (2026-06-19).

### Hard block 429
Vượt quota → **HTTP 429** ngay, không proceed extraction (cost runaway prevention). Soft warn rejected. Kevin ratified cycle 3.

### D-11 (CLAUDE.md)
Quota check PHẢI chạy trước mọi ingest endpoint. Vượt → 429, no LLM call. Pairs với FR-TN-01.

### Phase 1 manual / Phase 2 automated billing
Roadmap PRODUCT_STRATEGY §7.1. Phase 1 manual invoice (~50-100k/client/năm). Phase 2 automated (Stripe / VN gateway, per-client metering từ quota counter).

---

---

## K. Direction model (DEC-030)

### `direction`
Obligation field. Values: `nghĩa_vụ` (SME phải làm) · `quyền_lợi` (đối tác phải làm cho SME) · `null` (chưa xác định). Driven by `obligor` ↔ `legal_name` match. Xem SRS §6.4.

### `obligor`
Obligation field — party name chịu nghĩa vụ. Lấy từ `payment_schedule[].payer` hoặc derive từ `parties[]` + clause analysis. NULL hợp lệ khi AI không xác định (D-08).

### `recurrence`
Obligation cadence enum (renamed from old `obligation_type`): `once`/`monthly`/`quarterly`/`yearly`/`open_ended_review`. Migration `tenant_005`.

### `role_label`
Party field — vai trò trong HĐ extracted verbatim ("Owner", "Bên A", "NSDLĐ", "Bên thuê", ...). D-06: AI bóc text, KHÔNG quyết SME là bên nào.

### `legal_name`
`tenant_profile.legal_name`. SME entity full legal name. Auto-match `parties[].name` per Document để derive `direction`.

### Self-party
SME = `legal_name` match. Đối lập "external party" (đối tác). User confirm qua UI extraction review screen (D-02) khi auto-match fail.

---

## L. Chat tool surface (post DEC-026 + DEC-029 + Backend PR #115/#125/#132)

### Tool params evolved
- **`search_terms`**: `field_name`, `doc_hint`, `value_contains`, `party_filter`, `doc_type_filter`. AND-compose. Max 10 rows + `truncation_hint` sentinel.
- **`search_obligations`**: `due_within_days` (forward-only window `>= today`), `status`, `doc_hint`, `due_from`/`due_to` (ISO inclusive both), `doc_type_filter`, `direction`.
- **`search_clauses`**: `query`, `doc_hint`. Gemini-extracted docs only (xem 2-tier schema).

### `PARTY_FIELDS`
Constant tuple `("doi_tac",)` — single party field in CANONICAL_FIELDS. Drives `party_filter` cross-field join trong `search_terms`. Future: add aliases (`ben_b`, `khach_hang`, ...) khi schema mở rộng — out of scope MVP.

### `truncation_hint`
Sentinel value Backend trả khi result count > 10. LLM `_format_answer` system prompt → "có N kết quả, hiển thị 10 mới nhất, mời thu hẹp." User-facing transparency.

### Today's-date injection
Backend `_build_router_system_prompt(today)` inject `date.today()` ISO into LLM system prompt + rule chuyển VN calendar phrases ("tháng này"/"tháng sau"/"quý này"/"quý sau"/"tuần này"/"X ngày tới") → `due_from`/`due_to`. LLM KHÔNG tự đoán ngày.

**Timezone caveat:** `date.today()` server-local. Edge case nếu VPS không phải `Asia/Ho_Chi_Minh`. Fast-follow: `ZoneInfo("Asia/Ho_Chi_Minh")`.

### `_is_negative_answer` (Backend PR #132 D-08 strict)
Narrow regex `không tìm thấy|không có thông tin|chưa có dữ liệu` — caller enforce exact `{answer: <D-08 string>, sources: [], found: False}` triple khi (a) LLM paraphrase HOẶC (b) all tools empty. Regex cố tình narrow để KHÔNG suppress valid content như `thoi_han_hd="không xác định thời hạn"`.

### Chat learning loop (DEC-028)
Log `{question, tool_calls, found}` mỗi query → PM/QC weekly review → fold misroute vào catalog (issue #118) → update few-shot. **🔴 COMPLIANCE DEBT (NĐ 13/2023):** assume-consent bypass cho staging/pilot-dev; phải đóng pre-prod (KHE_Compliance #119). Routing log shape PII-safe (tool name + canonical field_name + arg keys present only). Cross-tenant few-shot phải synthetic/scrubbed.

---

---

## M. Fulfillment + Cascade Chain (DEC-048)

### Fulfillment capture
Action SME ghi nhận hoàn thành nghĩa vụ qua `PATCH /obligations/{id}` body `{status:"done", fulfilled_at, fulfilled_by, evidence_doc_ids}`. UI: Tab Nghĩa vụ → "Đánh dấu đã hoàn thành" → FulfillModal (date picker + actor + evidence link). Event `obligation_fulfilled` ghi với `purpose=obligation_fulfillment` (no consent gate).

### `propagate_obligation_done(parent)`
Function trong `obligation_chain.py` invoked khi parent obligation `done`. Iterates dependent children; for each → computes `child.due_date = parent.fulfilled_at + child.trigger_delay_days`; if `< today` → child status = **`awaiting_confirmation`** (else `pending`). Logs `cascade_triggered` Event per child.

### Cascade-past (DEC-048 Option B, Kevin ratify)
Edge case: parent fulfilled long ago → child due also in past. **KHÔNG** auto-flip `overdue` hoặc spam reminder. **KHÔNG** treat as `pending`. Instead → `awaiting_confirmation` → SME confirm "đã hoàn thành chưa?" (D-02). PATCH-able sang `done`/`cancelled`/`pending`.

### `awaiting_confirmation` (status)
DEC-048 status enum value. UX: card "Cần xác nhận đã hoàn thành?" trong Tab Nghĩa vụ. Differs from `overdue` (FE-derived urgency của `pending` past-due) — `awaiting_confirmation` là legitimate state, không cần nhắc.

### Anchor = `fulfilled_at` (G1 fix)
Cascade chain MUST use `parent.fulfilled_at` làm anchor cho child due computation, **NOT** `date.today()`. Tại sao: replaying historical parent fulfillment phải sinh due dates relative to actual fulfillment date để audit reconstruct chính xác.

### P1 source-aware merge rule (PR #311)
Khi re-derive (clause edit / re-read / re-extraction): cleanup phase DELETE existing derived obligations với guard:
```sql
WHERE source != 'user_manual' AND fulfilled_at IS NULL
```
Mục đích: bảo vệ user edits + fulfilled state khỏi AI overwrite.

### Derive delete path-2 guard
PR #311 V1 fix. Cleanup path-2 (re-derive cleanup) phải có `fulfilled_at IS NULL` guard ngoài source check — prevents losing audit trail của fulfilled obligations dù `source` field bị sai.

### `waiting_trigger` (status)
DEC-048 status cho FR-OB-13 obligations chưa resolve được date anchor. Background resolver `resolve_date_anchored_obligations()` map trigger phrase → Term field → compute `due_date` → flip sang `pending`. D-08: anchor unknown → giữ `waiting_trigger`, không bịa.

### `_detect_anchor_field()`
Helper trong `obligation_engine.py` PR #322. Maps Vietnamese trigger phrases → CANONICAL_FIELDS names. MVP scope: `"ngày ký"` → `ngay_ky`, `"ngày hiệu lực"` → `ngay_hieu_luc`. Event-triggered anchors (`ngay_ban_giao`, `ngay_nghiem_thu`) handled by cascade chain qua `fulfilled_at`, không qua resolver.

### `obligation_fulfillment` (purpose enum)
KHE_Compliance §A.1 closed-set purpose enum value (PM #307 approve). Storage-only — no LLM transit, no cross-border. Event log only, no 403 consent gate. Folded as DEC-048 audit trail purpose tag.

### `evidence_attached` (Event type)
Logged khi upload với `is_evidence=true`. Payload: `{document_id, contains_personal_data, purpose=obligation_fulfillment}`. DEC-039 §G.2: firm portal visibility metadata-only cho evidence docs (hard condition, blocks firm portal go-live).

---

---

## N. DEC-055 + DEC-056 Strategy vocabulary (cycle 7)

### Servanda
Tên thương mại chính thức (R-7 resolved 2026-07-02 per DEC-055). Từ *pacta sunt servanda* (hợp đồng phải được tuân thủ). "**Khế**" giữ làm codename nội bộ. Đk tiên quyết công khai: Kevin verify nhãn hiệu NOIP + domain.

### Ledger/"Sổ" tier (free)
DEC-055 Phase 1 tier. Nhập tay obligations / parties / metadata + full core loop (deadline reminder, D-02 confirm, D-07 edit, audit log, consent). **Miễn phí vĩnh viễn** cho core safety loop (D-16 no-paywall-safety).

### AI tier (paid)
DEC-055 Phase 1 paid tier. Vision extraction toàn văn + chat trích nguyên văn + cây điều khoản. **Quota per-document** (không per-tenant) — mỗi doc dùng LLM call là 1 unit.

### Per-doc quota
DEC-055 pricing atomic unit. Khác quota per-tenant (DEC-011). Cho phép firm mua batch quota rồi phân bổ theo doc cần AI vs doc chỉ dùng Ledger.

### D-16 no-paywall-safety (guardrail)
Không bao giờ paywall các tool an toàn (reminder, D-02 confirm, D-07 edit, audit, consent). Chỉ monetize **trí tuệ** (extraction, chat) và **tiện lợi** (bulk, portfolio). Renumbered từ PM-proposed D-11 (conflict với existing D-11 quota).

### Obligation OS (North Star, DEC-056)
Servanda là hệ điều hành nghĩa vụ, không phải hệ điều hành hợp đồng. Hợp đồng = **nguồn nghĩa vụ đầu tiên**; **pháp luật = nguồn thứ hai** (thuế/BHXH/ngành dọc). Engine đối xử thống nhất mọi obligation, agnostic về nguồn (P-6).

### Rule pack (DEC-056)
Thư viện curated nghĩa vụ tuân thủ theo hồ sơ DN (loại hình, có nhân viên, kê khai GTGT tháng/quý, ngành nghề). Structured data thuần, **KHÔNG tốn AI call**. Firm là người kích hoạt + xác nhận (D-17).

### Nghĩa vụ tuân thủ (compliance obligation)
Obligation nguồn từ pháp luật thay vì HĐ. Cùng model, cùng `recurrence`/`due_date`/`status` như obligation HĐ. Fields khác: `document_id` cần nullable (gap #1 DEC-056 §5c.6) hoặc container "hồ sơ tuân thủ".

### Hồ sơ tuân thủ (compliance dossier)
Container-level entity đề xuất DEC-056 cho compliance obligations — schema chưa chốt. Tương lai gộp: nghĩa vụ thuế theo quý + BHXH tháng + gia hạn giấy phép con thành 1 dossier per SME. Nới ràng buộc `Obligation.document_id NOT NULL` hoặc tạo entity riêng.

### D-17 firm-confirms-compliance (guardrail)
Servanda cung cấp template rule pack + engine nhắc; **firm (đại lý thuế/law firm) là người kích hoạt và xác nhận** lịch tuân thủ cho SME (D-02 áp nguyên). Servanda KHÔNG bao giờ tự tư vấn nghĩa vụ pháp lý. Rule pack sai → firm bắt được ở bước xác nhận. Renumbered từ PM-proposed D-12 (conflict với existing D-12 chat learning).

### P-6 obligation-source-agnostic (principle BRD §4)
Nghĩa vụ có thể đến từ (1) HĐ (2) pháp luật (3 tương lai) quy trình nội bộ. Engine đối xử thống nhất. Xem PRODUCT_STRATEGY §5c + BRD §4 P-6.

---

## O. Cycle 7 impl vocabulary

### `is_garbled_vietnamese()` (PR #422)
Heuristic trong `scan_detect.py`: diacritical ratio < 2% → detected garbled Vietnamese output từ pdftotext (scanned PDFs với embedded OCR layers thường bị này). Trigger fallback DocAI.

### Two-pass extraction (PR #463)
Auto-triggered pipeline khi `is_max_tokens_truncation()` detect trên `hybrid_ocr` text-mode. Steps: `extract_skeleton()` → `persist_skeleton()` → `run_content_fill()`. **⚠️ Gap:** chỉ khôi phục clauses, KHÔNG metadata (fields/parties/obligations/definitions/cross_refs/signature). Filed #464.

### `processing_stage` enum (cycle 7 extension)
Cycle 6 stages (`queued`/`ocr`/`llm`/`saving`/`done`/`failed`) plus cycle 7: **`retry_needed`** (PR #458 transient failure — 503 or MAX_TOKENS trap) + **`two_pass_skeleton`** + **`two_pass_fill`** (PR #463 checkpoints).

### FallbackProvider warnings accumulation (PR #426)
`_FallbackProvider.extract()` giờ accumulate warnings từ failed providers với `[provider_name]` prefix, carry forward tới final result. Cho phép diagnose chain failures.

### `may_have_unextracted_obligations` (PR #492, tenant_031)
Three-state completeness flag on `documents`: `NULL` = CompletenessVerifier never ran (default + legacy), `true` = detected miss, `false` = cleared. LLM impl fast-follow. D-03 honest completeness — FE show always-on disclaimer pre-pilot.

### `Term.source` provenance (PR #487)
`extracted` / `remap` / `manual` / `null` (legacy). Cho FE display/filter obligation origin.

### `obligation_type = "penalty"` (PR #475, tenant_030)
Enum category value cho nghĩa vụ phạt / bồi thường. Category axis, không cadence.

### `PATCH /obligations/bulk` (PR #475)
Bulk complete endpoint. 1 Event/obligation D-07, D-10 tenant-isolated no-leak, cascade per item. Requires D-02 readback modal (FE PR #476 flag pre-prod).

### PL- clause_path convention (PR #425/#433)
Sub-clauses under Phụ lục → `clause_path="PL-X.Y"` (vd `"PL-A.1"`) để tránh collision với Điều path numeric (`"1.2.3"`). `clause_hierarchy.py` `_PHU_LUC_RE` handles. Cross-ref resolver có intra-doc fallback: khi "Phụ lục A" ref không tìm thấy external DocumentRelationship → search same-doc clauses `clause_path="PL-{id}"`.

---

## P. Design System "Sổ cái" v1.1 (DEC-055 companion, ratified 2026-07-03)

### Lục Khế
Primary color `#1E5C49`. Ratified DEC-055. Signal thương hiệu Servanda.

### `border-strong`
Token `#7E8983`, WCAG 2.1 contrast **3.47:1** (đo thật, không khẳng định). Dùng cho input/button/checkbox borders per SC 1.4.11 non-text contrast. `n-300`/`n-400` giữ lại **chỉ cho viền trang trí** — KHÔNG dùng cho interactive components.

### `done` / `done-soft` tokens
`#5A6660` / `#F0F0EB`. Ratified 2026-07-03 (PR #488 "green-creep cleanup"). "Hoàn thành = xám lặng" per DS principle — replace `bg-success`/`text-success`.

### 13 badges chuẩn hóa (vocabulary)
Không icon/emoji. Statuses: "Chờ kích hoạt", "Đã thanh lý", "Đang xử lý", "Cần kiểm tra", "Đã xác nhận", "Chờ xác nhận", "Đã ký", "Chưa ký", "Sắp hết hạn", "Đang hiệu lực", "Quá hạn", "Đã hoàn thành", "Chờ sự kiện". Vocabulary thống nhất tab tài liệu → dashboard → Telegram.

### Hợp đồng A11y binding (v1.1)
Semantic-element mandate + keyboard-operable + `LiveRegion` cho văn bản tự đổi + icon-only bắt buộc `aria-label`. WCAG 2.1 AA target. Fold nguyên #206 từ DS v0.2.

### Elevation e0-e3
4-tầng shadow ẩn dụ "giấy xếp lớp" thay 1 shadow phẳng. Rationale design, không tùy hứng.

### Design System component roster (4)
`NavItem` · `IconButton` (**ngoại lệ duy nhất** cho luật no-icon) · `Dropzone` · `LiveRegion`.

### Voice + tone
Xưng "**bạn**". Tự gọi "**Servanda**" (không "Khế" trong copy user-facing). KHÔNG dấu chấm than. Dark mode = v2 (chưa design MVP).

---

*Hết v0.8 — cycle 7 DEC-055/056 + DS v1.1 fold.*

*Hết v0.7 — cycle 6 DEC-049 hybrid OCR + DEC-050 R1-R10 fold. Bước kế tiếp: thêm UI terms khi Frontend session spawn, CONTRACT_LOGIC_Khe.md role conventions khi lawyer partner kickoff Sprint 6.*

*Hết v0.6 — cycle 5 DEC-048 fold. Bước kế tiếp: thêm UI terms khi Frontend session spawn, CONTRACT_LOGIC_Khe.md role conventions khi lawyer partner kickoff.*
