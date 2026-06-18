# KHE_Compliance — Team State

*Owner: KHE_Compliance (single-owner, low-touch) · Branch: `claude/compliance-nd13-consent-spec`*
*Last updated: 2026-06-18 — Sprint 1 first task (#30): NĐ 13/2023 consent UX spec + DEC-010 audit sign-off · **3 PM decisions LOCKED** (revocation / retention / LLM DPA)*

> **Scope (HARD):** Compliance **spec** only — NĐ 13/2023 (DLCN/PII) · NĐ 337/2025 (lao động ĐT) · NĐ 70/2025 (hóa đơn ĐT) · consent flows · data residency · retention · audit-log spec.
> ❌ KHÔNG implement application code (`backend/**`, `frontend/**`, `.github/workflows/**`) — file issues cho KHE_Backend / KHE_Infra.
> ❌ KHÔNG legal advice — spec **requirements**, không interpret luật. "Verify với counsel" mọi điểm pháp lý cần phán quyết.
> Finding ảnh hưởng canonical docs → report [DOCS_INBOX #1](https://github.com/kevindo1103/khe/issues/1) cho KHE_Docs fold.

---

## Ratified decisions tracked

| ID | Nội dung | Compliance impact |
|---|---|---|
| **DEC-010** | US-hosted LLM (Gemini / Claude) OK Phase 1 **chỉ khi** explicit consent + audit log `events` table. Phase 2+ re-eval self-host. | Consent gate trước extraction (FR-EX-06 — xem §A). Audit checklist (§E). |
| **DEC-014** | Positioning "ngôi nhà sau khi ký" — KHÔNG claim "ký số" (NĐ 337 guard). | Positioning guard (§F). |
| **D-09** | Firm KHÔNG sửa dữ liệu SME ở MVP (chỉ xem). | Firm portal consent scope = read-only (§C). |
| **D-10** | Quyền partner xuyên-tenant chỉ mở khi SME consent rõ ràng, thu hồi được. | `firm_partner_access` consent + revocation (§C, §D). |

### PM-locked decisions (2026-06-18, on #30)

| Q | Decision LOCKED | Spec section |
|---|---|---|
| **Revocation** | **Option C** — block future + soft-flag `consent_revoked` + ledger Event; **deadlines/obligations đã sinh vẫn chạy tiếp**. "Xóa dữ liệu" là một action riêng, rõ ràng (tôn trọng 2 quyền tách biệt của NĐ 13). | §D |
| **Retention** | **Tenant-active + 90 ngày post-close.** ⚠️ verify với thời hạn lưu trữ HĐ luật định — conflict thì flag back PM. | §B |
| **LLM DPA** | **Zero-retention tier bắt buộc** — Anthropic + Google no-train/no-log; verify **trước** first production extraction. | §E |

---

## ⚠️ Open findings → DOCS_INBOX (cho KHE_Docs fold)

| # | Finding | Đề xuất |
|---|---|---|
| CF-1 | **BRD v0.1 chưa có FR-EX-06.** #30 / #22 / spawn prompt đều reference "FR-EX-06 consent gate" nhưng BRD §7.2 chỉ có FR-EX-01..05. | Thêm **FR-EX-06** (consent gate trước extraction) vào BRD §7.2 — wording đề xuất §A.4. |
| CF-2 | NFR-2 ghi *"(Cần xác minh hiệu lực Luật Bảo vệ DLCN mới.)"* + NFR-3 *"(cân nhắc yêu cầu data residency)"* còn để ngỏ. DEC-010 đã giải: at-rest VN + LLM transit US Phase 1 với consent. | Update NFR-2/NFR-3 phản ánh DEC-010 split (at-rest vs transit). Verify counsel về NĐ 13 cross-border transfer. |
| CF-3 | NĐ 337/2025 hiệu lực: CLAUDE.md ghi 01/01/2026; BRD §dẫn-luật ghi nền tảng quốc gia chậm nhất 01/07/2026; spawn prompt ghi 01/07/2026. | Thống nhất: **NĐ hiệu lực 01/01/2026; nền tảng quốc gia vận hành chậm nhất 01/07/2026.** (§F) |

---

## §A — Consent gate spec (NĐ 13/2023) — feeds #22 (Backend) + #31 (PWA)

### A.1 — Purpose enum (`events.purpose`)

Mọi PII processing log một Event với `purpose` từ enum đóng dưới đây (NĐ 13/2023 yêu cầu *mục đích xử lý* rõ ràng + consent reference):

| `purpose` value | Khi nào | Bên nhận dữ liệu | Consent bắt buộc trước? |
|---|---|---|---|
| `vision_extraction` | Trước mỗi lần gửi ảnh/PDF tài liệu tới Vision LLM (Gemini/Claude, US-hosted) | Google LLC / Anthropic PBC (US) | ✅ YES — gate 403 (A.2) |
| `reminder_send` | Khi gửi nhắc qua Telegram bot / email | Telegram (Telegram FZ-LLC) / email provider | ✅ YES — opt-in tại first-login |
| `firm_partner_access` | Khi firm partner xem dữ liệu nghĩa vụ của tenant | Firm partner (đã ký DPA với SME) | ✅ YES — D-10, revocable (A.2 + §C) |

> **HARD:** enum **đóng**. Thêm purpose mới = compliance review trước, không tự thêm ở code.

### A.2 — Consent event schema (per-tenant `events` table)

Mỗi consent action ghi **một Event append-only** (FR-AU-01, không edit-in-place):

```python
Event(
    tenant_id=tenant_id,
    event_type="consent_logged",         # hoặc "consent_revoked"
    purpose=<purpose enum>,              # A.1
    consent_reference=<uuid|str>,        # ID duy nhất, hiển thị lại cho SME khi audit
    consent_text_version="nd13-v1",      # version text A.3 — bắt buộc, để truy ngược nội dung đã đồng ý
    created_by=current_user.id,          # ai bấm đồng ý
    created_at=<utc>,
)
```

**Required columns add vào `events`** (Backend, Alembic per-tenant): `purpose`, `consent_reference`, `consent_text_version`. (Đã align với #22 plan; thêm `consent_text_version` so với #22 — cần để chứng minh SME đồng ý đúng phiên bản text khi text đổi.)

**Gate logic (Backend, tại ingest call site — FR-EX-06):**
1. Trước `provider.extract()` → query `events` cho tenant: có `event_type="consent_logged"` AND `purpose="vision_extraction"` AND chưa bị `consent_revoked` sau đó?
2. Có → proceed.
3. Không → `HTTP 403 {"detail": "SME consent for AI extraction not recorded. Log consent first."}`
4. Sau extract → log một Event `event_type="extraction_performed"`, `purpose="vision_extraction"` (audit trail bên nhận US).

### A.3 — Consent dialog text VN (PWA first-login — mobile-readable)

> **Hiển thị:** modal first-login, trước upload/extract đầu tiên. Phải cuộn đọc được trên mobile. Nút "Đồng ý" + "Để sau" (để sau = chặn extract, vẫn dùng được app read-only). Version string: `nd13-v1`.

```
Khế xử lý dữ liệu tài liệu của bạn như thế nào

Để đọc và bóc tách thông tin từ hợp đồng bạn tải lên (đối tác, ngày
hết hạn, giá trị…), Khế gửi hình ảnh/tệp tài liệu tới dịch vụ trí tuệ
nhân tạo của Google (Gemini) và/hoặc Anthropic (Claude). Các dịch vụ
này đặt máy chủ tại Hoa Kỳ.

• Mục đích: chỉ để ĐỌC và bóc tách thông tin — Khế KHÔNG soạn, KHÔNG
  sửa, KHÔNG ký nội dung pháp lý của bạn.
• Dữ liệu gửi đi: hình ảnh/tệp tài liệu bạn chủ động tải lên.
• Bên nhận: Google LLC và Anthropic PBC (Hoa Kỳ).
• Lưu trữ: bản gốc tài liệu của bạn được lưu tại máy chủ ở Việt Nam.
• Quyền của bạn: bạn có thể THU HỒI đồng ý này bất cứ lúc nào trong
  phần Cài đặt. Khi thu hồi, Khế sẽ ngừng gửi tài liệu mới tới AI.

Bạn có quyền yêu cầu xem, sửa, hoặc xóa dữ liệu cá nhân theo Nghị định
13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.

[ Đồng ý cho Khế đọc tài liệu của tôi ]      [ Để sau ]
```

> **Counsel verify:** wording "thu hồi", mô tả cross-border transfer (US) phải khớp NĐ 13/2023 Điều về chuyển dữ liệu ra nước ngoài. Đây là **draft spec**, không phải bản pháp lý cuối — Kevin/counsel duyệt trước go-live.

### A.4 — Đề xuất wording FR-EX-06 (cho KHE_Docs fold vào BRD §7.2)

> **FR-EX-06** Trước lần extraction đầu tiên cho mỗi tenant, hệ thống PHẢI có consent event hợp lệ (`purpose="vision_extraction"`, chưa thu hồi) ghi ở `events`. Thiếu → chặn extraction (HTTP 403). Consent thu hồi được; thu hồi chặn extraction tương lai (NĐ 13/2023, DEC-010).

---

## §B — Retention policy (draft — verify counsel trước go-live)

NĐ 13/2023 nguyên tắc: giữ dữ liệu **không lâu hơn mục đích**. Draft baseline:

| Dữ liệu | Retention đề xuất | Lý do |
|---|---|---|
| File gốc tài liệu (immutable, FR-IN-02) | Giữ suốt đời tenant active; xóa **90 ngày** sau khi tenant đóng tài khoản (**LOCKED**) | File gốc là "ngôi nhà sau khi ký" — mục đích kéo dài; nhưng phải xóa khi hết quan hệ. |
| `terms` (field bóc ra) | Theo file gốc | Phái sinh từ file. |
| `obligations` | Theo file gốc | Phái sinh. |
| `events` (ledger, gồm consent) | **Giữ lâu hơn** — tối thiểu **5 năm** sau khi tenant đóng (audit/chứng minh consent) | Append-only ledger là bằng chứng tuân thủ; không xóa cùng file. Verify counsel thời hạn luật định. |
| `master.db` (tenant/user records) | Xóa/anonymize **90 ngày** sau đóng tài khoản, trừ trường tối thiểu cho nghĩa vụ kế toán/thuế | NĐ 13 + nghĩa vụ lưu sổ. |
| Dữ liệu gửi LLM (transit) | **Zero-retention tier (LOCKED)** — Anthropic + Google no-train/no-log; Khế không lưu transit. Ghi rõ trong DPA + consent text | Bên thứ ba; zero-retention loại bỏ rủi ro residual storage. |

> **Verify-back (không phải open ambiguity nữa — LOCKED 90 ngày):** thời hạn 90 ngày phải đối chiếu **thời hạn lưu trữ hợp đồng luật định** (kế toán/thuế/dân sự). Nếu luật buộc giữ lâu hơn 90 ngày → flag back PM, KHÔNG tự xóa sớm. `events` ledger giữ ≥5 năm (§B trên) độc lập với file gốc.

---

## §C — Firm partner access scope (D-09 / D-10)

- Firm chỉ thấy tenant có `firm_tenant_access.consent_status = "granted"` (master.db). (FR-FP-01)
- Firm **read-only** — KHÔNG sửa dữ liệu SME (D-09 / FR-FP-03). Spec: firm portal endpoints KHÔNG expose write trên per-tenant data.
- Mỗi lần firm truy cập dữ liệu tenant → log Event `purpose="firm_partner_access"` ở per-tenant `events` (audit ai-xem-gì).
- Consent `firm_partner_access` tách biệt với `vision_extraction` — SME đồng ý cái này KHÔNG tự đồng ý cái kia.

---

## §D — Revocation flow spec

Áp dụng cho mọi `purpose` revocable (vision_extraction, reminder_send, firm_partner_access).

**Decision LOCKED = Option C** (PM, 2026-06-18 on #30): block future + soft-flag + ledger; deadlines giữ chạy; "xóa dữ liệu" là action riêng.

1. SME bấm "Thu hồi" trong Cài đặt (PWA) → Backend ghi Event `event_type="consent_revoked"`, `purpose=<x>`, `consent_reference` (tham chiếu consent gốc). **Append-only — KHÔNG edit-in-place** consent cũ (FR-AU-01).
2. **Hiệu lực = block-future + soft-flag:**
   - Chặn **xử lý tương lai** cho purpose đó (extract mới / firm-view / reminder mới).
   - Set soft-flag `consent_revoked` (state derived từ ledger, không xóa Event gốc).
   - **Dữ liệu đã bóc + obligations/deadlines đã sinh VẪN CHẠY TIẾP.** Thu hồi `vision_extraction` consent **KHÔNG** dừng nhắc hạn của HĐ đã bóc trước đó — reminder do consent `reminder_send` riêng điều phối (J2 "trái tim" không bị tắt ngầm).
3. **"Xóa dữ liệu" là action RIÊNG, rõ ràng** (NĐ 13 quyền xóa — tách biệt với quyền thu hồi đồng ý). SME phải chủ động chọn "Xóa dữ liệu của tôi". MVP: log yêu cầu → xử lý thủ công (concierge) → ghi Event; tự động hóa Phase 2.
   - **Vì sao tách 2 quyền:** NĐ 13 phân biệt *rút lại sự đồng ý* (ngừng xử lý tương lai) và *quyền xóa* (xóa dữ liệu đã có). Gộp 2 = vừa over-delete (mất "ngôi nhà") vừa mơ hồ pháp lý.
4. `firm_partner_access` revoke → firm **mất quyền xem ngay** (BRD AC-5).

---

## §E — DEC-010 audit checklist + sign-off template

> Kevin (hoặc người được ủy quyền) PHẢI ký checklist này **trước first production extraction** (lần đầu ảnh tenant thật gửi LLM US). Lưu kết quả ký vào issue + DOCS_INBOX.

```
DEC-010 PRE-PRODUCTION EXTRACTION SIGN-OFF — NĐ 13/2023

Ngày: __________   Người ký: __________   Môi trường: [ ] staging  [ ] production

[ ] 1. Consent dialog (text nd13-v1, §A.3) LIVE trên PWA first-login.
[ ] 2. Consent gate (FR-EX-06) hoạt động: không consent → 403; có consent → 200.
       Evidence: test output / curl ________________________
[ ] 3. events table ghi consent_logged với purpose + consent_reference + consent_text_version.
       Evidence: query output ________________________
[ ] 4. Audit log READABLE: truy được "tenant X đồng ý lúc nào, text version nào".
[ ] 5. Revocation (Option C) hoạt động: revoke → extraction tương lai chặn + soft-flag;
       obligations/deadlines đã sinh VẪN chạy (không tắt ngầm).
       Evidence: test output ________________________
[ ] 6. Consent text mô tả đúng bên nhận US (Google/Anthropic) + quyền thu hồi.
[ ] 7. **DPA zero-retention tier CONFIRMED (HARD):** Anthropic + Google no-train/no-log
       enabled. Evidence: DPA / account setting screenshot ________________________
[ ] 8. Retention = tenant-active + 90 ngày post-close (LOCKED); ledger ≥5 năm.
       Verify-back: 90 ngày KHÔNG dưới thời hạn lưu HĐ luật định (counsel) — nếu có, đã flag PM.
[ ] 9. KHÔNG log PII cấm: passwords, JWT, bot token, API keys (CLAUDE.md §Security).

Sign-off: __________________   (Thiếu bất kỳ mục nào = KHÔNG go-live extraction)
```

---

## §F — NĐ 337/2025 positioning guard (DEC-014)

- **Sự thật pháp lý:** NĐ 337/2025/NĐ-CP (HĐ lao động điện tử) **hiệu lực 01/01/2026**; nền tảng quốc gia vận hành **chậm nhất 01/07/2026**.
- **Guard:** Khế là "ngôi nhà sau khi ký" (hậu-ký). Marketing/landing/PWA copy **KHÔNG được claim**: "ký số", "ký điện tử", "chữ ký số", "hợp đồng điện tử có giá trị pháp lý", "thay thế nền tảng ký". (DEC-014 + R-1 BRD: tránh đối đầu nền tảng quốc gia NĐ 337.)
- **Cho phép nói:** "lưu trữ", "tra cứu", "nhắc hạn", "bóc tách thông tin", "quản lý nghĩa vụ hợp đồng đã ký".
- **Action (track-only):** khi Frontend/PWA/Marketing copy xuất hiện → review chống claim cấm. File issue `for:frontend`/`for:pwa` nếu thấy vi phạm. KHÔNG sửa code trực tiếp.

---

## Inbox log

| Date | Issue | Action |
|---|---|---|
| 2026-06-18 | #30 | First task — spec drafted (§A–§F). Relay → #22, #31, DOCS_INBOX #1. |
| 2026-06-18 | #30 | **3 PM decisions LOCKED** (revocation Option C / retention 90d / LLM zero-retention) folded into §B/§D/§E. |
| 2026-06-18 | #22 | Backend consent gate — spec §A feeds; note `consent_text_version` column add. |
| 2026-06-18 | #32 | PWA epic (BLOCKED on #24 design) — consent UI text §A.3 ready khi unblock. |
| 2026-06-18 | spawn | Noted `SPAWN_KHE_COMPLIANCE.md` references #32 (PWA epic) instead of #30; file not in repo — PM to fix on template side. |

---

*Created 2026-06-18 by KHE_Compliance · branch `claude/compliance-nd13-consent-spec`. Spec = draft requirements, NOT legal advice; Kevin/counsel duyệt trước go-live.*
