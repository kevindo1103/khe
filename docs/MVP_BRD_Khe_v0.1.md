# BRD — MVP "Khế" (Vibe Document OS cho SME)

> **Tên mã tạm:** Khế *(khế ước; placeholder — đổi tự do bằng find-replace)*
> Một trợ lý tài liệu kinh doanh chat-first cho chủ SME **không có phòng pháp chế**: đổ hết giấy tờ vào một chỗ, không bao giờ quên hạn, tìm trong vài giây — phân phối qua law firm / đại lý thuế.

---

## 0. Document control

| Mục | Nội dung |
|---|---|
| Phiên bản | v0.10 |
| Trạng thái | Ratified — fold cycle 7 (DEC-055 Servanda tier + DEC-056 Obligation OS + Design System v1.1 + ~15 impl entries) |
| Phạm vi | **Chỉ MVP** (tầng ingest + retrieve + deadline). Không phải full vision. |
| Owner | Kevin (PM) |
| Liên quan | Tái dùng hạ tầng SpurX (ledger, multi-tenant, infra v3) |
| Upstream cascade | `docs/PRODUCT_STRATEGY_Khe_v0.2.md` — tài liệu nền (WHY/Personas/JTBD/Positioning). BRD dẫn xuất từ đây; khi mâu thuẫn → Product Strategy thắng về *tại sao / cho ai / job gì*; BRD thắng về *hệ thống phải làm gì*. |

---

## Changelog

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| v0.1 | 2026-06-09 | Kevin (PM) / ERP_PM_Assistant | Initial draft. Scope MVP ingest + retrieve + deadline. Topology 10 sessions. D-rules P-1..P-5. |
| v0.2 | 2026-06-11 | KHE_Docs | Fold Strategy v2 (DEC-011..015): B2B2B firm-pays Phase 1, concierge onboarding, 2-firm pilot, positioning hậu sóng NĐ 337, 3-giai-đoạn roadmap, kill signals. Fold DEC-006: Telegram bot thay Zalo ZNS (FR-RM-01, §10, §11 A-3, §12 R-2, UC-02, AC-2). Fold KHE_AI insight: §6 Term/Field + §7 FR-EX/FR-OB-01 — `ngày_hết_hạn` derivable từ `ngày_hiệu_lực + thời_hạn`. **OPEN:** DEC-016 freemium paywall lever conflicts với DEC-006 — NOT folded, chờ PM quyết. `thoi_han_hd` phi-số policy (a/b/c) NOT folded — chờ PM. |
| v0.3 | 2026-06-18 | KHE_Docs | Fold DEC-018 (Vertical = OPEN — không khóa F&B/bán lẻ; wedge chọn theo tín hiệu pilot). Revise §11 A-5 (vertical seed → wedge OPEN). Update §1 Executive summary + §10 R-1 wording. Add cascade reference to upstream `PRODUCT_STRATEGY_Khe_v0.2.md` (Personas, JTBD, Golden Circle, Dunford positioning). |
| v0.4 | 2026-06-19 | KHE_Docs | Cycle 3 fold (8 DOCS_INBOX comments). Add **§7.11 FR-TN Tenant quota + billing** (FR-TN-01..03). Update §10 Tích hợp domain `khe.iceflow.cloud` (Infra PR #48). §7.2 FR-EX add CANONICAL_FIELDS 7 vocab (Backend M0 contract). §7.3 FR-DR add document_relationships (Backend PR #59 + DEC-019/020/021). §7.1 FR-IN reference ingest endpoints live (PR #54). |
| v0.5 | 2026-06-19 | KHE_Docs | **DEC-026 fold (PRIORITY gate Backend #99 issue #100).** §7.6 FR-CQ-01..03 rewrite from regex/SQL pattern → LLM function-calling (Gemini Flash) với 3 tools (`search_terms`, `search_obligations`, `search_clauses`). D-08 hard fallback exact string. **FR-CQ-04 NEW:** doc_hint + multi-doc search routing. Cross-ref SRS §5.9 clauses table. |
| v0.10 | 2026-07-03 | KHE_Docs | **Cycle 7 fold — DEC-055 tier + DEC-056 Obligation OS + DS v1.1 + impl entries.** Header rename Khế → Servanda (R-7 resolved). §4 P-6 NEW principle: obligation-source-agnostic (compliance = source 2). §7.2 FR-EX-15..17 NEW (all-PDFs→hybrid_ocr routing per PR #414; garbled detection PR #422; TOÀN VĂN rule + PL- convention PR #425). §7.2 FR-EX-18/19 (extraction retryable states — 503/UNAVAILABLE + MAX_TOKENS trap PR #458). §7.2 FR-EX-20 two-pass pipeline PR #463 (skeleton→fill, gap: clauses-only). §7.4 FR-OB-14 NEW obligation_type `penalty` enum (PR #475). §7.4 FR-OB-15 NEW `PATCH /obligations/bulk` (PR #475). §7.4 FR-OB-16 alias-match D-13 (PR #475). §7.4 FR-OB-17 `may_have_unextracted_obligations` field (PR #492). §7.10 FR-AU-06 `Term.source` provenance API (PR #487). NEW §9 NFR UI Design System v1.1 (Lục Khế token + Be Vietnam Pro + Source Serif 4 + 13 badges + WCAG 2.1 + Hợp đồng A11y binding). |
| v0.9 | 2026-06-29 | KHE_Docs | **Cycle 6 fold — DEC-049 hybrid OCR + DEC-050 R1-R10 EPIC #362 production (PR #402).** §6 Document expansion (+`title`/`contract_number`/`signing_date`/`commencement_date`/`contract_duration`/`lifecycle_status`/`has_signature`/`signature_pages`). §6 Party expansion (+`address`/`representative`/`tax_code`/`is_self`/`aliases`). §6 Clause hierarchy (+`parent_id`/`level`/`clause_path`). §6 NEW Definition + CrossReference + Annex relationship type. §7.2 FR-EX-01 add `hybrid_ocr` provider (DEC-049 2-pass pipeline). §7.2 FR-EX-10..14 NEW (R1-R10 extraction depth: title/contract_number, party details, clause hierarchy, dates taxonomy, signature flags, defined terms, cross-references, lifecycle status, auto-renewal). §7.3 FR-DR-04 annex relationship type (third value alongside amends/references_framework). §7.10 NEW admin endpoints (extraction metrics + extraction progress polling). |
| v0.8 | 2026-06-27 | KHE_Docs | **Cycle 5 fold — DEC-048 EPIC #300 production promote (sha `ce48bbd`).** §6 Obligation +`fulfilled_at`/`fulfilled_by`/`evidence_doc_ids` + status `awaiting_confirmation` + `source_clause_num` + `derived_from` + `source`. §6 Document +`is_evidence`. §6 NEW ClauseEditEvent entity (§13 addendum). §7.1 +FR-IN-05 evidence skip-extraction. §7.2 +FR-EX-09 clause edit + re-read flow. §7.4 +FR-OB-09..13 (fulfillment capture · cascade chain anchor `fulfilled_at` G1 · cascade-past awaiting_confirmation · source_clause_num provenance · P1 source-aware merge + derive delete path-2 guard · date-anchored waiting_trigger resolver). §7.5 +FR-RM-07 (exclude fulfilled + awaiting_confirmation + waiting_trigger). §7.10 +FR-AU-02 audit endpoint + FR-AU-03 new event types. |
| v0.7 | 2026-06-20 | KHE_Docs | **DEC-031 v2 fold (priority PM task).** §7.6 FR-CQ +FR-CQ-07/08/09/10 — Result-seeded Progressive State chat architecture: `state_json` structured (NOT prose), scope chip mandatory (silent wrong-scope = D-08 spirit violation), ambiguity ask-clarify + cold-start guard, 30-min session invalidation. Anchor principle upstream in `PRODUCT_STRATEGY_Khe_v0.2.md` §5b. **Note:** PM task spec gọi tên IDs `FR-CQ-04..07` nhưng `04..06` đã occupied từ cycle 3+4 (doc_hint / DEC-028 learning / D-08 strict); DEC-031 reqs landed làm `FR-CQ-07..10` để không break IDs. Out-of-scope: prose history, auto-widen, NLP pronoun layer. Discard DEC-031 v1 spec (`1f6c5ad`) — v2 (`dc307eb`) is canonical. |
| v0.6 | 2026-06-20 | KHE_Docs | **Cycle 4 fold (16 DOCS_INBOX entries).** Mega-decisions DEC-027 (8 obligation_type categories), DEC-028 (chat learning + compliance debt), DEC-029 (doc_type_group 11 + 12 canonical + 9 type-specific + payment_schedule), DEC-030 (direction/obligor/Quyền lợi/self-party/legal_name). §6 Obligation/Party schema update + Quyền lợi concept. §7.2 FR-EX-01/02 rewrite (taxonomy v2 + 2-tier schema), +FR-EX-06/07/08 (parties/payer/clauses). §7.4 FR-OB-04 status enum corrected ({pending,done,cancelled}; overdue=urgency), +FR-OB-05..08 (chain attach + payment derive + direction). §7.5 +FR-RM-05/06 (DEC-025 per-tenant routing + direction labels). §7.6 +FR-CQ-05/06 (chat learning + D-08 strict). Tool params evolved (party_filter, value_contains, due_from/to, doc_type_filter, direction, truncation). |

---

## 1. Executive summary

Thị trường CLM hiện tại (HighQ, Icertis, Ironclad…) được thiết kế *cho phòng pháp chế / luật sư*. SME ở VN **đa số không có người làm pháp chế hay hành chính hợp đồng**, nên cả lớp sản phẩm đó lệch khỏi thực tế của họ. Khế lấp khe này: một lớp chat đơn giản đứng trên một **lõi tất định** lo template, deadline, nghĩa vụ và lưu vết.

MVP **không** cố làm tất cả. Nó chỉ giải một nỗi đau an toàn nhưng tần suất cực cao: *"đổ hết hợp đồng/giấy tờ vào đây, hệ thống tự nhắc hạn và cho tìm lại."* Đây là **"ngựa thành Troy"**: tầng này rủi ro pháp lý thấp (AI chỉ đọc, không đẻ nội dung), hút được *cả kho tài liệu* của SME về một chỗ → tạo data moat → mở đường cho soạn/review về sau.

Phân phối qua **law firm / đại lý thuế** làm kênh: tầng nhắc hạn không cướp việc luật sư mà còn *đẻ lead* cho họ (nhắc "sắp hết hạn" → khách hỏi luật sư tái đàm phán → billable).

---

## 2. Bối cảnh & vấn đề

### 2.1 Nỗi đau (SME end-user)
- Hợp đồng/giấy tờ nằm rải rác: email, Zalo, ngăn kéo, máy kế toán. Không có một chỗ.
- **Quên gia hạn / quên deadline** → mất quyền lợi, bị phạt, mất mặt bằng.
- Cần tìm một hợp đồng cũ → lục cả buổi.
- Không có người chuyên trách; chủ tự làm hoặc khoán cho kế toán/luật sư ngoài.

### 2.2 Vì sao bây giờ (catalyst)
- **NĐ 337/2025/NĐ-CP** (hợp đồng lao động điện tử): hiệu lực 01/01/2026; nền tảng quốc gia vận hành chậm nhất 01/07/2026 → cú hích lớn đẩy SME số hóa giấy tờ.
- **NĐ 70/2025** (hóa đơn điện tử, kết nối dữ liệu thuế) → áp lực compliance, SME buộc số hóa chứng từ.
- Giá SaaS quốc tế (USD) đắt lên → khe cho sản phẩm định giá nội địa.

### 2.3 Vì sao kênh law firm / đại lý thuế
- Họ là "bộ phận pháp lý/hành chính thuê ngoài" mà SME **vốn đã có**.
- Đại lý thuế chạm mọi SME *hàng tháng* (khai thuế) → gắn sâu hơn cả law firm.
- Tầng nhắc hạn **đẻ việc** cho họ thay vì cạnh tranh → họ vui vẻ đẩy.

---

## 3. Mục tiêu & chỉ số thành công (MVP)

### 3.1 Mục tiêu kinh doanh (DEC-013 — 2-firm pilot)
- B-1: Ký được **2 firm design-partner song song** — 1 đại lý thuế + 1 law firm. So sánh kênh sau 90 ngày.
- B-2: Mỗi firm đẩy được **≥10 SME** kích hoạt thật (tổng ≥20 SME).
- B-3 (DEC-011): **Firm là khách trả tiền** (~50-100k/client/năm). SME FREE Phase 1. SME-pays mở ở GĐ2 (drafting/review lawyer-in-loop, 2027).

### 3.2 Mục tiêu sản phẩm (đo được)
| ID | Chỉ số | Mục tiêu MVP |
|---|---|---|
| M-1 | Activation: SME upload ≥3 tài liệu trong tuần đầu | ≥60% SME onboarded **(đo SAU concierge baseline — DEC-012)** |
| M-2 | Time-to-first-wow: từ upload đến lần nhắc hạn đúng đầu tiên | < 5 phút thao tác |
| M-3 | Độ chính xác trích xuất `ngày hết hạn` (trên ảnh/PDF VN) | ≥90% |
| M-4 | Độ tin cậy gửi nhắc (reminder delivery) | ≥99% |
| M-5 | Truy vấn chat "cái gì sắp hết hạn?" trả lời đúng | ≥95% |

### 3.3 Non-goals (MVP KHÔNG làm)
- KHÔNG soạn hợp đồng tự động (drafting) — *mở GĐ2 lawyer-in-loop*.
- KHÔNG review/cảnh báo rủi ro điều khoản.
- KHÔNG tự xây ký số — sẽ tích hợp bên thứ ba ở giai đoạn sau.
- KHÔNG đa thị trường — **VN-first**.
- KHÔNG marketplace template — firm cấp template để dành pha sau.
- KHÔNG cạnh tranh tầng ký số (DEC-014) — Khế đón **hậu sóng** NĐ 337, không tranh ngược dòng.

### 3.4 Business Model — B2B2B (DEC-011)

**Phase 1 (MVP, 2026 H2):** Firm (đại lý thuế / law firm) là **khách hàng trả tiền**, mua suất cho danh mục SME của họ. Đơn giá tham chiếu ~50-100k VND/client/năm. SME end-user **FREE**. Logic: SME chưa có ngân sách dòng riêng cho document OS; firm vốn đã thu phí dịch vụ tháng từ SME → bundle Khế vào gói firm là đường ngắn nhất tới revenue.

**Phase 2 (GĐ2, 2027):** Mở tầng drafting/review **lawyer-in-loop**. SME trả phí per-template/per-review; firm hưởng revenue share. AI vẫn tuân P-1 — chỉ điền template đã duyệt + đề xuất chỉnh; review pháp lý bắt buộc qua luật sư.

**Phase 3 (GĐ3, 2027+):** Obligation graph làm **hạ tầng** — nối công nợ, hóa đơn điện tử, ngân hàng. Khế trở thành lớp đồng bộ nghĩa vụ tài chính + pháp lý cho SME ecosystem.

### 3.5 Concierge onboarding (DEC-012)

20 SME đầu tiên **không tự upload**. Quy trình "ôm cả ngăn kéo" 1 ngày:
- Khế đội (hoặc firm partner) tới văn phòng SME, **số hóa tận nơi** mọi hợp đồng + giấy tờ.
- Nhập batch vào tenant SME → giao tài khoản → SME chỉ cần check.
- Lý do: ma sát upload là nguyên nhân lớn nhất thua. Bỏ ma sát ở 20 SME đầu để chứng minh value loop (upload → extract → reminder → query).

M-1 (60% upload ≥3 docs) chỉ đo **sau khi concierge baseline đã đẩy đủ kho ban đầu** — đo retention upload tiếp theo, không phải onboarding cold.

### 3.6 Positioning — "Ngôi nhà cho mọi hợp đồng sau khi ký" (DEC-014)

Khế **không** cạnh tranh tầng ký số (VNPT eSign, FPT.CA, MISA eContract, nền tảng NĐ 337 quốc gia). Khế đón **hậu sóng** NĐ 337 (hiệu lực 01/01/2026, nền tảng quốc gia chạy chậm nhất 01/07/2026):
- Tầng ký số sinh ra **dòng chảy HĐ điện tử khổng lồ** từ 2026 H2.
- Bài toán "ký rồi để đâu?" chưa ai giải tử tế cho SME — đó là khe Khế.
- Tagline: *"Ngôi nhà cho mọi hợp đồng sau khi ký — nhắc đúng hạn, tìm trong 3 giây."*

### 3.7 Kill / Pivot signals (DEC-015)

Sau 90 ngày 2-firm pilot, nếu xảy ra → pivot ngay:

| Signal | Trigger | Pivot |
|---|---|---|
| **K-1 (retention)** | W4 retention SME < 30% sau concierge | Pivot sang DMS B2B cho firm nhỏ (firm là user chính, không phải SME) |
| **K-2 (firm không trả)** | Firm không sẵn sàng trả per-client + SME tự convert tốt | Pivot direct freemium SME-first |
| **K-3 (kênh không đẩy)** | 2 firm không kéo nổi 10 SME mỗi firm trong 90 ngày | Đổi kênh — hiệp hội ngành F&B / community |

### 3.8 Roadmap 3 giai đoạn

| Giai đoạn | Thời gian | Trọng tâm | Revenue model |
|---|---|---|---|
| **GĐ1 — Troy + Concierge** | Q3-Q4 2026 | Ingest + retrieve + deadline. 2-firm pilot. Concierge onboarding. | Firm trả per-client |
| **GĐ2 — Soạn/Review lawyer-in-loop** | 2027 | Template drafting + review pháp lý. SME-pays per use. | SME-pays + firm revenue share |
| **GĐ3 — Obligation graph hạ tầng** | 2027+ | Nối công nợ + hóa đơn ĐT + ngân hàng. Khế = lớp sync nghĩa vụ. | Platform fee + integration partner |

---

## 4. Nguyên tắc & guardrail (ràng buộc mọi requirement bên dưới)

| ID | Nguyên tắc | Hệ quả |
|---|---|---|
| P-1 | **AI không bao giờ là system of record** | AI chỉ được *đọc/bóc tách* (vào) và *điền template đã duyệt* (ra, giai đoạn sau). Sự thật nằm ở lõi tất định + ledger. |
| P-2 | **Mọi ghi xuống lõi mang tính pháp lý phải qua xác nhận của người** | Authoring mode bắt readback → preview → user confirm. (MVP gần như chỉ có đọc, nên rủi ro thấp.) |
| P-3 | **Ngựa thành Troy** | Dẫn bằng ingest + retrieve + deadline. Drafting/review là upsell sau. |
| P-4 | **Tích hợp, đừng tự build** | Ký số, hóa đơn ĐT, kênh nhắc (Zalo) → dùng bên thứ ba. |
| P-5 | **Đa loại document trong KIẾN TRÚC, wedge OPEN trong SEED** | Lõi general (multi-tenant, đa loại doc, obligation graph không phụ thuộc ngành). **Wedge KHÔNG khóa trước (DEC-018)** — chọn theo tín hiệu pilot. F&B/bán lẻ là 1 ứng viên; agency/dịch vụ B2B, sản xuất nhỏ, giáo dục đều khả thi. Xem `PRODUCT_STRATEGY_Khe_v0.2.md` §9. |
| P-6 (DEC-056) | **Obligation-source-agnostic** | Nghĩa vụ có thể đến từ: (1) hợp đồng đã ký (extraction pipeline), (2) pháp luật (rule pack curated cho thuế/BHXH/ngành dọc), (3 tương lai) quy trình nội bộ. Engine đối xử **thống nhất** — cùng model Obligation, cùng reminder/fulfillment/cascade. Xem `PRODUCT_STRATEGY_Khe_v0.2.md` §5c. Servanda KHÔNG dùng AI đọc văn bản luật (đụng D-01/D-08) — dựa rule pack curated + firm confirm (D-17). |

---

## 5. Đối tượng người dùng (MVP)

| Persona | Vai trò | Cần gì ở MVP |
|---|---|---|
| **Chủ SME** (primary user) | Người đổ tài liệu vào, nhận nhắc, hỏi-đáp | Đơn giản đến mức không cần học; nhắc đúng kênh (Telegram bot — DEC-006) |
| **Nhân viên SME** (kế toán/admin nội bộ, nếu có) | Upload hộ, tra cứu | Tìm nhanh, quyền hạn cơ bản |
| **Firm partner** (luật sư / đại lý thuế) | Kênh phân phối; xem danh mục khách (có phép); nhận tín hiệu lead | Cổng firm read-only + tín hiệu "khách sắp cần" |
| **Admin hệ thống** (nội bộ Khế) | Vận hành, hỗ trợ onboarding | Quản trị tenant/partner |

---

## 6. Domain glossary (object lõi)

| Thuật ngữ | Định nghĩa |
|---|---|
| **Document** | Một văn bản: file gốc (bất biến) + phân loại + các Term + liên kết. Không phải chỉ là file — là một object có cấu trúc. Trường (DEC-048 + DEC-050): **`is_evidence`** BOOLEAN (DEC-048) · **`title`** (`tieu_de_hd`) · **`contract_number`** (`so_hop_dong`) · **`signing_date`** (`ngay_ky`) · **`commencement_date`** (`ngay_khai_truong`) · **`contract_duration`** · **`lifecycle_status`** (DEC-050 R8 enum: `active` / `expiring` / `expired` / `settled` / `suspended`) · **`has_signature`** BOOL + **`signature_pages`** JSON (DEC-050 R5b) · **`extraction_model`** + **`extraction_latency_ms`** + **`extraction_warnings`** (admin metrics) · **`processing_stage`** + **`processing_progress`** (extraction pipeline polling). Khi `is_evidence=true` → `contains_personal_data=true` mặc định + skip extraction (P2 rule). |
| **Term / Field** | Giá trị có cấu trúc bóc từ Document: loại, đối tác (Party), ngày hiệu lực, **ngày hết hạn**, thời hạn, giá trị, điều khoản thanh toán. **Lưu ý (KHE_AI 2026-06-11):** HĐ Việt Nam thường ghi `ngày_hiệu_lực + thời_hạn`, KHÔNG ghi thẳng `ngày_hết_hạn`. `ngày_hết_hạn` có thể **derived** (xem Obligation engine) — nullable hợp lệ ở tầng Term. |
| **Obligation** | **Object trung tâm của MVP.** Một cam kết rời rạc, *có ngày*, *có trạng thái*, suy ra từ Document. Trường (mới hậu DEC-027/030/048): `id`, `document_id`, `description`, **`obligation_type`** (category enum 8: `payment` · `delivery` · `handover` · `expiration` · `renewal` · `review` · `warranty` · `other`), **`recurrence`** (cadence: `once` · `monthly` · `quarterly` · `yearly` · `open_ended_review`), `due_date`, **`status`** (`pending` · `done` · `cancelled` · **`awaiting_confirmation`** per DEC-048 cascade-past; `overdue` = derived urgency, **không phải status**; `waiting_trigger` per FR-OB-13), `remind_before_days`, **`direction`** (`nghĩa_vụ` / `quyền_lợi` / `null`), **`obligor`**, **`fulfilled_at`** (DATETIME, DEC-048 — ngày thực sự hoàn thành, dùng làm anchor cho cascade chain), **`fulfilled_by`** (VARCHAR, actor name), **`evidence_doc_ids`** (JSON list[int], DEC-048 — biên bản/hóa đơn), **`source_clause_num`** (VARCHAR — clause provenance per Kevin Option B 0a), **`derived_from`** (`original` / `user_edit` / `ai_re_derived`), **`source`** (`ai_extracted` / `user_manual` / `ai_re_derived` — P1 source-aware merge rule). **Derived fields:** `due_date` derived FR-OB-01; `payment_schedule[]` → `payment` per item (DEC-027); cascade chain anchor = `fulfilled_at` (G1 fix per DEC-048). |
| **Quyền lợi** (DEC-030) | Sub-concept Obligation. Cam kết của **đối tác** hướng *về* SME (vd: đối tác trả tiền cho mình, bảo hành, giao hàng). Phân biệt với `nghĩa_vụ` (SME phải làm). Hiển thị tab riêng UI; reminder label khác ("đối tác cần… cho bạn"). |
| **Party** | Đối tác trong tài liệu, được chuẩn hóa. Trường (DEC-030 + DEC-050 R2): `name`, `tax_code`, **`address`**, **`representative`** (người đại diện ký), **contact**, **`role_label`** (DEC-030 — vai trò trong HĐ: "Owner", "Bên A", "NSDLĐ", ... — extracted verbatim, D-06 read-only), **`is_self`** BOOL (DEC-050 R2 — SME side flag), **`aliases`** JSON array (tên gọi khác / viết tắt). **Self-party (DEC-030):** SME entity name = `tenant_profile.legal_name`; auto-match `parties[].name` để derive Obligation `direction` + flip `is_self=true`. |
| **Event (Ledger)** | Bản ghi append-only mọi thay đổi trạng thái (ingest, sửa term, hoàn thành nghĩa vụ, đã gửi nhắc…). Sửa = ghi event mới (reversal), **không** edit-in-place. Tái dùng pattern SpurX. |
| **Template / Clause** | Mẫu/điều khoản do firm thẩm định, có version. *Định nghĩa sẵn trong glossary nhưng chưa kích hoạt ở MVP.* |
| **ClauseEditEvent** (DEC-048 §13 addendum) | Snapshot khi SME sửa điều khoản: `clause_id`, `clause_num`, `original_content` (**immutable** sau first edit — D-07 audit), `edited_content`, `edited_by`, `edited_at`, `re_read_triggered` (bool), `re_read_at`, `re_read_result_id`. Wired qua `PATCH /documents/{id}/clauses/{clause_num}` + `POST /documents/{id}/reread`. |
| **Clause** (DEC-050 R3 hierarchy expansion) | Điều khoản trong Document. Trường mở rộng: existing `clause_num`/`title`/`content`/`page_num`/`original_content`/`edited_by_user`/`edited_at` (DEC-026 + §13), **`parent_id`** FK self-ref, **`level`** INTEGER (1 = Điều, 2 = Khoản, 3 = Mục, ...), **`clause_path`** VARCHAR (vd `"2.1.3"` — dot-separated hierarchy path). Synthesized post-extraction via `clause_hierarchy.py` service. |
| **Definition** (DEC-050 R9 — NEW entity) | Glossary entry bóc từ section "Định nghĩa" của Document. Trường: `id`, `document_id` FK, `clause_id` FK NULLABLE (clause nguồn), `term` (VARCHAR), `definition` (TEXT), **`original_term`** (D-07 first-edit snapshot). Per-tenant `definitions` table (`tenant_027` migration). Editable qua CRUD endpoints; ghi Event mỗi edit/delete. |
| **CrossReference** (DEC-050 R10 — NEW entity) | Tham chiếu nội bộ trong Document (vd `"Điều 5"`, `"Khoản 2 Điều 5"`, `"Phụ lục A"`). Resolved khi target tồn tại; orphan khi không. Trường: `source_clause` ref, `target_ref` text raw, `target_type` (`clause` / `sub_clause` / `appendix`), `resolved` BOOL. Service: `cross_ref.py` (PR #392). Per-tenant table — verify exact storage shape (JSON column trên clauses HOẶC dedicated table). |
| **Annex relationship type** (DEC-050 R4 extends DEC-019) | Third value trong `document_relationships.relationship_type` enum: `amends` (sửa đổi) · `references_framework` (HĐ con của khung) · **`annex`** (phụ lục độc lập đính kèm — KHÔNG sửa terms parent, KHÔNG trigger `resolve_chain` overwrite). Annex edges excluded khỏi `last_writer_wins` chain resolution. |
| **Lifecycle Status** (DEC-050 R8 enum) | `documents.lifecycle_status`: `active` (đang hiệu lực) · `expiring` (sắp hết hạn ≤30 ngày) · `expired` (đã quá hạn) · `settled` (hoàn thành, manual override) · `suspended` (tạm dừng, manual override). Backend derive 3 đầu tự động từ `expiry_date` + `contract_term`; `settled`/`suspended` user manual flip. UI badge per `mockup_document_detail_v3.jsx`. |
| **Tenant** | Một SME (cô lập dữ liệu, theo pattern `tenantDb` của SpurX). |
| **Partner** | Một firm; role **xuyên tenant** (nhìn nhiều SME theo phân quyền). Là phần *mới* so với SpurX. |

---

## 7. Functional requirements (MVP)

### 7.1 Ingestion (FR-IN)
- **FR-IN-01** Upload qua: ảnh chụp (camera), kéo-thả PDF/Word, forward email tới địa chỉ riêng của tenant.
- **FR-IN-02** Lưu file gốc bất biến; mọi xử lý sau dựa trên bản gốc này.
- **FR-IN-03** Hàng đợi xử lý bất đồng bộ; hiển thị trạng thái "đang đọc…" cho từng tài liệu. *(MVP impl PR #54/#60: FastAPI `BackgroundTasks` schedule `run_extraction` sau response 201; `status: processing → extracted | failed`.)*
- **FR-IN-04** Endpoints live (staging): `POST /ingest/upload` (single, multipart) + `POST /ingest/bulk` (≤20 files) — xem SRS §2.
- **FR-IN-05 (NEW DEC-048):** Khi upload, nếu `is_evidence=true` (biên bản nghiệm thu / hóa đơn thanh toán đính kèm fulfillment) → server-side skip `provider.extract()` (P2 rule, KHE_Compliance §G). Document lưu metadata + binary, KHÔNG run vision API. `contains_personal_data` default `true` (conservative). Endpoint: `POST /ingest/upload?is_evidence=true` hoặc body flag.

### 7.2 Extraction — AI safe-read (FR-EX)
- **FR-EX-01 (DEC-029 v2):** Tự nhận **`doc_type_group`** trước (taxonomy 11 giá trị, collapse từ 126 loại HĐ): `dan_su` · `thuong_mai` · `lao_dong` · `bat_dong_san` · `van_tai_logistics` · `xay_dung` · `cong_nghe_ip` · `tai_chinh` · `bao_dam` · `hanh_chinh` · `other`. *(Old `DocType` enum 4 giá trị deprecated — M0 dùng for legacy docs.)*
- **FR-EX-02 (DEC-029 v2):** Bóc **12 universal CANONICAL_FIELDS**:
  - **7 BASE** (Claude fallback bóc tới đây): `doi_tac`, `ngay_hieu_luc`, `ngay_het_han` (nullable, derivable per FR-OB-01), `gia_tri_hd`, `thoi_han_hd`, `dieu_khoan_gia_han`, `dieu_khoan_thanh_toan`.
  - **5 V2_UNIVERSAL** (Gemini-only): `doc_type_group`, `ngay_ky`, `tien_dat_coc`, `thoi_han_bao_hanh`, `thoi_han_thong_bao`.
  - Plus **9 TYPE_SPECIFIC field sets** (~30 fields tổng) per `doc_type_group` (vd `lao_dong`: `luong_co_ban`, `thoi_gian_thu_viec`; `tai_chinh`: `lai_suat`...) — bóc qua `NamedExtractedField` keyed list.
  - **2-tier schema (KHE_AI PR #135):** Gemini Flash (primary) trả full v2; Claude Haiku/Sonnet (fallback) chỉ 7 BASE — schema rộng hơn → "too many states" hoặc "Schema is too complex" timeout deterministic. *(KHE_AI insight: HĐ VN thường ghi `ngày_hiệu_lực + thời_hạn`, không ghi thẳng `ngày_hết_hạn` → derive ở Obligation tier.)*
- **FR-EX-06 (NEW DEC-030):** Bóc `parties[]` = `{name, role_label}` — vai trò các bên trong HĐ (Owner/Operator/Bên A/NSDLĐ...) extracted verbatim. KHÔNG quyết bên nào là SME (Backend match `legal_name` + user confirm per D-02). Gemini-only.
- **FR-EX-07 (NEW DEC-027/030):** Bóc `payment_schedule[]` = `{amount, due_date, milestone, recurrence, payer}` — cùng 1 vision call (không thêm cost). `payer` = bên phải trả mỗi kỳ. Backend derive thành `payment` Obligations per item.
- **FR-EX-08 (NEW DEC-026):** Bóc `clauses[]` (xem FR-CQ-02 + SRS §5.9) — same vision call. Gemini-only (`list[ClauseItem]` không qua Claude grammar).
- **FR-EX-09 (NEW DEC-048 §13 addendum):** **Clause edit + AI re-read flow.** SME có thể sửa nội dung clause inline qua `PATCH /documents/{id}/clauses/{clause_num}` — Backend snapshot `original_content` lần edit đầu (immutable). Sau edit, banner "Khế đọc lại" trigger `POST /documents/{id}/reread` (clause-scoped re-derive, ~2-3đ text-only). Re-read trả về **diffs** — KHÔNG auto-apply, SME confirm từng diff (D-02). Source-aware merge: `user_manual` obligations protected by default. `derived_from = "user_edit"` cho obligations sinh từ re-read.
- **FR-EX-10 (NEW DEC-049 — Hybrid OCR pipeline):** `VisionExtractionProvider` registry mở rộng với **`hybrid_ocr`** provider (PR #341). 2-pass pipeline: (1) detect scanned vs digital PDF via `is_scanned_pdf()` (pdftotext heuristic < 50 chars/page = scanned); (2) Document AI OCR cho scanned (gated `GOOGLE_APPLICATION_CREDENTIALS`) hoặc `extract_embedded_text()` cho digital → Gemini Flash text extraction (`ContractExtractionLLMFull`). System dep VPS: `poppler-utils`. Routing: **opt-in only** (`prefer="hybrid_ocr"`); DEC-049 default policy chờ Kevin ratify.
- **FR-EX-11 (NEW DEC-050 R1 — Title + contract number):** Bóc `tieu_de_hd` (title) + `so_hop_dong` (contract number) → denormalized lên `documents.title` + `documents.contract_number`. User edit qua `PATCH /documents/{id}` (D-07 Event log per field).
- **FR-EX-12 (NEW DEC-050 R2/R3 — Party details + Clause hierarchy):** R2 expand `PartyItem` với `address`, `representative`, `tax_code`. R3 synthesize `Clause.parent_id`/`level`/`clause_path` post-extraction từ numbering patterns ("Điều 1" / "Khoản 1.2" / "Mục 1.2.a").
- **FR-EX-13 (NEW DEC-050 R5/R6 — Signature + Date taxonomy):** R5a render markdown tables trong clause content (FE composed `ClauseContent` + `react-markdown` + `remark-gfm` + `rehype-sanitize`). R5b extract `has_signature` BOOL + `signature_pages` JSON array; FE badge "Đã ký (trang X, Y)" / "Chưa ký" / hidden khi NULL. R6 date taxonomy denormalize `signing_date` + `commencement_date` lên `documents` (Term path preserved cho audit).
- **FR-EX-15 (NEW cycle 7 — All-PDFs → hybrid_ocr routing, KHE_AI PR #414):** Extraction runner detect PDF → auto-route `prefer="hybrid_ocr"` (DEC-049 routing default resolved). Rationale: Gemini vision-only ignore complex prompt rules (`_CLAUSES_SPEC`). Factory gate changed từ `GOOGLE_APPLICATION_CREDENTIALS` → `GEMINI_API_KEY`/`GOOGLE_API_KEY` (DocAI credential still gated separately trong hybrid path). *(Prior DEC-049 opt-in from cycle 6 superseded.)*
- **FR-EX-16 (NEW cycle 7 — Garbled OCR detection, PR #422):** `scan_detect.is_garbled_vietnamese()` — diacritical ratio < 2% → detected garbled → fallback DocAI. Deprecated PR #427 removed initial impl (cascade failure DocAI creds missing) then PR #422 reintroduced properly.
- **FR-EX-17 (NEW cycle 7 — TOÀN VĂN rule + PL- convention, PR #425):** Prompt rule QUY TẮC 2: `Clause.content` PHẢI include ALL lettered items (a/b/c...), no truncation. QUY TẮC PHỤ LỤC: sub-clauses under Phụ lục → `clause_path="PL-X.Y"` để tránh collision với Điều path numeric. `clause_hierarchy.py` add `_PHU_LUC_RE` (PR #433).
- **FR-EX-18 (NEW cycle 7 — Retryable extraction states, Backend PR #458):** Distinguish transient vs terminal failure:
  - Provider 503/UNAVAILABLE tạm thời → doc giữ `processing_stage="retry_needed"` (NOT `failed`), event `extraction_transient_failure`. FE hiển thị nút "Thử lại" gọi `POST /{doc_id}/re-extract`.
  - `finish=MAX_TOKENS` trap → dừng fallback chain ngay (không thử provider khác cùng giới hạn), doc `retry_needed` với message "Document quá lớn, đã cắt bớt kết quả."
- **FR-EX-19 (NEW cycle 7 — PDF fallback chain, PR #458):** `_PDF_CHAIN = (hybrid_ocr, gemini_flash)` — loại `claude_haiku` khỏi PDF fallback (Claude lean schema không có `clauses[]`/`parties[]` → extraction "thành công" giả trên PDF). Ảnh vẫn giữ `claude_haiku` fallback.
- **FR-EX-20 (NEW cycle 7 — Auto-trigger two-pass MAX_TOKENS, PR #463):** Khi `is_max_tokens_truncation()` + `result.ocr_text` có sẵn (chỉ path `hybrid_ocr` text-mode) → tự động chạy `extract_skeleton()` → `persist_skeleton()` → `run_content_fill()`. Mọi lỗi ở bất kỳ bước fallback về `_mark_transient_failure`. **⚠️ GAP:** two-pass **CHỈ khôi phục clauses**, KHÔNG khôi phục universal/type-specific fields / parties / obligation_schedule / definitions / cross_references / signature detection — filed #464 riêng cho metadata-pass fix. `extraction_warnings` cảnh báo user "clauses đầy đủ nhưng cần review trường/đối tác/nghĩa vụ thủ công".
- **FR-EX-14 (NEW DEC-050 R7/R9/R10 — Auto-renewal + Definitions + Cross-references):** R7 auto-renewal Obligation (renewal cadence + reminder window). R9 NEW `defined_terms[]` array on Gemini schema → persist vào `definitions` table (tenant_027). R10 NEW `cross_references[]` array → `cross_ref.py` service detects VN legal refs ("Điều X", "Khoản Y Điều Z", "Phụ lục A"), resolves intra-doc + appendix-via-annex, surfaces orphans. UI: inline clickable refs + orphan panel.
- **FR-EX-03** AI **chỉ đọc** — không sinh/sửa nội dung pháp lý (P-1).
- **FR-EX-04** Mọi field bóc ra phải **cho người sửa**; sửa → ghi Event (P-2).
- **FR-EX-05** Hiện độ tin cậy / cờ "cần kiểm tra" khi không chắc.

### 7.3 Document record & IR (FR-DR)
- **FR-DR-01** Mỗi Document có trang chi tiết: file gốc + các Term có cấu trúc + danh sách Obligation phát sinh.
- **FR-DR-02** Liên kết quan hệ cơ bản: phụ lục → hợp đồng gốc (MVP: thủ công cũng được).
- **FR-DR-03 Document relationships** (Backend PR #59, DEC-019/020/021): AI suggest `pending` edges ingest-time, SME confirm (D-02). Types: `amends` (phụ lục sửa đổi) vs `references_framework` (HĐ khung). Orphan amendments (`to_doc_id=null`) late-link khi parent arrives. Confirm trigger chain resolution `last_writer_wins` qua amends topology — supersede overlapping terms với `is_superseded` + `overrides_term_id` + `inherited_from_doc_id`. **Không tự tạo Obligation từ relationship** (out of scope MVP M0).
- **FR-DR-04 (NEW DEC-050 R4 — Annex relationship type, Backend PR #385):** `relationship_type` enum mở rộng third value: **`annex`** (phụ lục độc lập đính kèm — KHÔNG sửa terms parent). Heuristic split: amendment pattern requires keyword (sửa đổi / bổ sung / thay thế); standalone annex = alphanumeric capture `[A-Za-z0-9\-]+` với negative lookahead. `resolve_chain` filter `relationship_type == "amends"` (annex excluded — không trigger overwrite). R4b ingest-split flow (multi-doc in 1 file → N linked Documents) = Sprint 2 future, NOT in this milestone.

### 7.4 Obligation & deadline engine (FR-OB) — *trái tim MVP*
- **FR-OB-01** Tự sinh Obligation từ Term (vd: `ngày_hết_hạn` → nghĩa vụ "gia hạn/chấm dứt trước N ngày"). **Derivation rule:** nếu `ngày_hết_hạn IS NULL` AND cả `ngày_hiệu_lực` + `thời_hạn` (dạng số tháng/năm) đều có → derive `ngày_hết_hạn = ngày_hiệu_lực + thời_hạn`. Nếu `thời_hạn` phi-số ("vô thời hạn", "kể từ khi nghiệm thu") → policy chờ PM (tracked ambiguity v0.2 — engine fallback: skip expiry obligation, vẫn sinh được recurring obligations độc lập như BHXH).
- **FR-OB-02** Hỗ trợ nghĩa vụ **một lần** và **lặp** (hàng tháng/quý).
- **FR-OB-03** Tính tất định "nghĩa vụ nào tới hạn trong [khoảng]" — **không phải AI đoán**, là truy vấn trên kho.
- **FR-OB-04** Cho người đánh dấu hoàn thành / hủy → ghi Event. **Status enum chính thức (FE PR #69 ratified):** `pending` · `done` · `cancelled`. `overdue` / `due_soon` / `upcoming` = **FE-derived urgency buckets** từ `due_date` so với hôm nay, **không phải** status (BRD wording cũ `active/missed` superseded).
- **FR-OB-05 (Backend PR #64):** Obligation engine derive từ confirmed-amends chain effective terms; attach to chain **terminal** (newest amendment) doc; `source_doc_chain` + `resolution_method="last_writer_wins"` recorded. Re-derive deletes chỉ `pending` (preserve `done`/`cancelled` per D-02).
- **FR-OB-06 (NEW DEC-027):** `payment_schedule[]` items với `due_date` → `pending` Obligation rows, `obligation_type="payment"`. Idempotent re-extract via `source_doc_chain IS NULL` delete (derived obligations luôn set `source_doc_chain`; payment rows never set).
- **FR-OB-07 (NEW DEC-030 — Direction derivation):** Mỗi Obligation phải có `direction` từ góc nhìn SME:
  - `nghĩa_vụ` — `obligor` match `legal_name` (SME phải làm).
  - `quyền_lợi` — `obligor` match party khác (đối tác phải làm cho SME).
  - `null` + `needs_review=true` — `legal_name` chưa configured HOẶC auto-match fail. User confirm qua UI extraction review (D-02). **Ratified Kevin 2026-06-20.**
- **FR-OB-08 (NEW DEC-030):** Tenant phải có **`legal_name`** trong `tenant_profile` (separate model — xem SRS) để direction derivation hoạt động. Auto-match per-Document: cross-check `parties[].name` LIKE `legal_name`. Fail → fall through FR-OB-07.
- **FR-OB-09 (NEW DEC-048 — Fulfillment capture):** SME đánh dấu nghĩa vụ hoàn thành qua `PATCH /obligations/{id}` body `{status: "done", fulfilled_at, fulfilled_by, evidence_doc_ids}`. **`fulfilled_at`** là ngày thực sự hoàn thành (không nhất thiết hôm nay). `evidence_doc_ids` link tới documents với `is_evidence=true` (FR-IN-05). Event `obligation_fulfilled` ghi với `purpose=obligation_fulfillment` (no consent gate per KHE_Compliance §A.1 + §G). Revert flow: `obligation_fulfillment_reverted` event nếu user undo.
- **FR-OB-10 (NEW DEC-048 — Cascade chain + awaiting_confirmation):** Khi parent obligation `done` → child obligations với `trigger_condition` phụ thuộc parent → activate. **Anchor = `parent.fulfilled_at`** (G1 fix, **không phải** `date.today()`). Cascade case backfill: nếu `child_due = anchor + delay_days < today` → child status = **`awaiting_confirmation`** (D-02 SME confirm đã hoàn thành hay chưa, không auto-flip `overdue` hoặc spam reminder). Event `cascade_triggered` ghi audit. `awaiting_confirmation` PATCH-able sang `done`/`cancelled`/`pending`.
- **FR-OB-11 (NEW DEC-048 — Source clause provenance, Kevin Option B 0a):** Mỗi Obligation phải có **`source_clause_num`** (NULLABLE) — clause gốc sinh obligation. Set từ winning Term's `ref` field trong `derive_obligations()`. **`derived_from`**: `"original"` (AI extraction path) | `"user_edit"` (re-derive qua clause edit) | `"ai_re_derived"` (re-read endpoint). Cho phép clause-scoped re-derive qua `POST /documents/{id}/re-derive-clause` (text-only, không churn clause khác).
- **FR-OB-12 (NEW DEC-048 — P1 source-aware merge rule):** Khi re-derive (clause edit hoặc re-read), engine **KHÔNG xóa** obligations có `source = "user_manual"` HOẶC `fulfilled_at IS NOT NULL`. Derive delete path-2 (cleanup phase) có guard `WHERE fulfilled_at IS NULL` (PR #311 V1 fix). Mục đích: bảo vệ user edits + fulfilled state khỏi bị overwrite bởi AI re-extraction.
- **FR-OB-13 (NEW PR #322 — Date-anchored resolver):** Obligations với `trigger_condition` phi-event (vd "30 ngày từ ngày hiệu lực") persist ban đầu ở `status="waiting_trigger"` với `due_date=NULL`. Background resolver `resolve_date_anchored_obligations()` map trigger phrase → Term field (`ngay_ky` / `ngay_hieu_luc`); khi Term tồn tại trong DB → compute `due_date = term.value + trigger_delay_days` → flip sang `pending`. Audit Event `obligation_date_resolved`. D-08 preserved: anchor unknown → giữ `waiting_trigger`, không bịa ngày.
- **FR-OB-14 (NEW cycle 7 — obligation_type `penalty` enum, Backend PR #475 migration `tenant_030`):** `obligation_type` enum mở rộng thêm giá trị `"penalty"` (nghĩa vụ phạt / bồi thường). Category axis, không phải cadence. Anchor migration — TEXT column không cần ALTER thật.
- **FR-OB-15 (NEW cycle 7 — Bulk complete endpoint, PR #475):** `PATCH /obligations/bulk` body `{ids: number[], status: "done"|"cancelled", fulfilled_at?, fulfilled_by?}`. Tenant-isolated (cross-tenant ID skip âm thầm — D-10 no-leak). Log **1 Event/obligation** (không gộp — D-07/FR-OB-04). `fulfilled_at` bắt buộc khi `status="done"`. Gọi `propagate_obligation_done()` cho series chain. Response `{updated, skipped, items[]}`. Bulk complete triggers D-02 readback modal (Frontend TODO PR #476 flagged).
- **FR-OB-16 (cycle 7 clarification — D-13 alias-match, PR #475):** `_self_party_strings()` giờ unpack `Party.aliases` (JSON, DEC-050 R2). Trước chỉ match `Party.name` canonical → bỏ sót alias → `direction=NULL` sai (root cause doc #14). ⚠️ Prerequisite: `Party.aliases` chưa được LLM pipeline tự điền (`PartyItem` schema thiếu `aliases` field) — filed relay cho KHE_AI. Cho đến khi patch AI, user vẫn phải PATCH `Party.aliases` thủ công.
- **FR-OB-17 (NEW cycle 7 — `may_have_unextracted_obligations` completeness flag, Backend PR #492 migration `tenant_031`):** `documents.may_have_unextracted_obligations` BOOL NULLABLE — three-state: `NULL` = verifier never ran (legacy + all new docs), `true` = CompletenessVerifier detected likely miss, `false` = verifier cleared. Exposed on `DocumentListItem` + `DocumentDetailOut`. **No LLM call in this PR** — CompletenessVerifier fast-follow. FE show always-on disclaimer pre-pilot (D-03 honest completeness — issue #276).

### 7.5 Reminders / notifications (FR-RM)
- **FR-RM-01** Nhắc qua **Telegram bot** (kênh chính — DEC-006, bot token từ @BotFather, không cần approval) — fallback email. *(Thay Zalo ZNS để tránh blocker OA registration 4-6 tuần.)*
- **FR-RM-02** Mặc định nhắc trước 30 ngày + 7 ngày; cho chỉnh.
- **FR-RM-03** Ghi Event mỗi lần gửi nhắc: `reminder_sent` (success) · `reminder_failed` (delivery failed, retryable) · `reminder_batch` (audit) · `obligation_overdue` (status flip).
- **FR-RM-04** Digest định kỳ: "tuần này / tháng này có gì sắp tới." Scheduler daily sweep 08:00 ICT, multi-tenant (Backend PR #66).
- **FR-RM-05 (DEC-025 per-tenant routing — Backend PR #66):** Reminder destination = tenant's active **`reminder_send` consent** `channel_target_ref`. Global `TELEGRAM_CHAT_ID` là **dev-only fallback** — prod KHÔNG route qua đó. Tenant không có destination → skipped, không leak. `reminder_send` consent **separate** from `vision_extraction` consent.
- **FR-RM-06 (NEW DEC-030):** Reminder label theo `direction`:
  - `nghĩa_vụ` → "Bạn cần [action] trước [date]"
  - `quyền_lợi` → "Đối tác [obligor name] cần [action] cho bạn trước [date]"
- **FR-RM-07 (NEW DEC-048):** Scheduler `_flip_overdue_status()` + `compute_due_window()` **EXCLUDE**: (a) `fulfilled_at IS NOT NULL` (P5a — đã hoàn thành, không nhắc nữa); (b) `status = "awaiting_confirmation"` (P5b — chờ user xác nhận, không spam); (c) `status = "waiting_trigger"` (FR-OB-13 — chưa có due_date). Chỉ flip `overdue` cho `status="pending"` với `due_date < today` AND `fulfilled_at IS NULL`.

### 7.6 Chat — query/read mode (FR-CQ) — *DEC-026 LLM function-calling*
- **FR-CQ-01** Hệ thống nhận query ngôn ngữ tự nhiên (tiếng Việt) → **LLM (Gemini Flash) phân tích intent → gọi tool phù hợp → format answer từ kết quả tool**. LLM KHÔNG tự sinh nội dung pháp lý (D-06). Chat **chỉ đọc** ở MVP; mọi câu trả lời truy ra Document / Obligation / Clause cụ thể (có dẫn nguồn, không bịa).
- **FR-CQ-02** **3 tools available** (LLM function-calling surface, evolved Backend PR #115/#125/#132):
  - `search_terms(field_name, doc_hint, value_contains, party_filter, doc_type_filter)` — search trong 12 CANONICAL_FIELDS + type-specific. `doc_hint` = filename keyword (NOT party name). `value_contains` = substring trên `field_value`. `party_filter` = cross-field join lọc docs theo `doi_tac` ("field X của HĐ với công ty Y"). `doc_type_filter` (DEC-029) = exact `doc_type_group`. AND-compose all filters. Max 10 rows + `truncation_hint`.
  - `search_obligations(due_within_days, status, doc_hint, due_from, due_to, doc_type_filter, direction)` — `due_within_days` forward-only window (`due_date >= today`, không trả overdue). `due_from`/`due_to` ISO inclusive both ends. `status` ∈ `{pending, done, cancelled}` hoặc `overdue` (derived urgency). `direction` (DEC-030) = `nghĩa_vụ`/`quyền_lợi`. VN calendar phrases ("tháng này", "quý sau", "X ngày tới") → LLM resolve thành `due_from`/`due_to` qua today's-date injection in system prompt.
  - `search_clauses(query, doc_hint)` — full-text trong `clauses` table per-tenant (xem SRS §5.9). **Caveat (DEC-026 addendum):** chỉ available khi Gemini Flash xử lý extraction; Claude fallback → `clauses=[]` → tool returns empty (chat gracefully falls back sang `search_terms` + `search_obligations`).
- **FR-CQ-03 (D-08 hard fallback):** Nếu **tất cả tools trả empty** → trả về **exact string** `"Không tìm thấy thông tin này trong hồ sơ của bạn."` LLM KHÔNG được improvise/paraphrase fallback. KHÔNG phỏng đoán.
- **FR-CQ-04 (new):** Query có tên file hoặc tên đối tác → LLM extract làm `doc_hint` filter. Query không có hint + tenant có >1 doc → multi-doc search qua `search_clauses` + `search_obligations` (không hạn ở 1 doc).
- **FR-CQ-05 (NEW DEC-028 — Chat learning loop):** Log `{question, tool_calls, found}` mỗi query → PM/QC weekly review → fold misroute vào catalog (issue #118) → update few-shot prompt + QC test. **🔴 COMPLIANCE DEBT (NĐ 13/2023):** assume-consent bypass tạm thời cho staging/pilot-dev; **PHẢI đóng trước prod** (KHE_Compliance tracks #119). Routing log shape PII-safe (tool name + canonical `field_name` + arg keys present; **KHÔNG** log raw `party_filter`/`value_contains`/`doc_hint` value hoặc `question`). Cross-tenant few-shot trong shared prompt phải **synthetic/scrubbed**.
- **FR-CQ-06 (DEC-026 D-08 strict enforcement, Backend PR #132):** Backend caller enforce **exact triple** `{answer: "Không tìm thấy thông tin này trong hồ sơ của bạn.", sources: [], found: False}` khi (a) LLM paraphrase negation (`_is_negative_answer` narrow regex) HOẶC (b) all tools empty. Regex narrow để KHÔNG suppress valid content như `thoi_han_hd="không xác định thời hạn"`. Frontend match byte-exact (D-08 single source of truth).

**Multi-turn chat — Result-seeded Progressive State (DEC-031 v2):** Khế giải multi-turn KHÔNG bằng prose conversation history mà bằng **structured state + UI visibility**. Anchor principle xem `PRODUCT_STRATEGY_Khe_v0.2.md` §5b. Out-of-scope: full prose history (any phase), auto-widen on miss, NLP pronoun detection layer.

- **FR-CQ-07 (DEC-031):** Chat session duy trì `state_json` structured (`active_doc_ids[]`, `active_obligation_ids[]`, `working_set_label`, `last_tool_call`) per conversation thread — **KHÔNG dùng prose conversation history**. State được seeded từ query results của turn trước (result-seeded progressive state).
- **FR-CQ-08 (DEC-031):** Mọi response có carry-over context PHẢI hiển thị **scope chip visible + correctable** (vd `📌 Đang trong context: 3 HĐ tháng 7 ▾`). User phải có thể widen / reset / switch trong 1 tap. **Silent wrong-scope = D-08 spirit violation.**
- **FR-CQ-09 (DEC-031):** Ambiguous reference — multi-doc active hoặc deictic pronoun khi state trống → **ask-clarify, KHÔNG guess**. D-08 strict. Cold-start: Turn 1 deictic khi state trống → ask-clarify ("Bạn muốn hỏi về HĐ nào?").
- **FR-CQ-10 (DEC-031):** Session invalidation: **30-min timeout** + explicit reset button + high-threshold intent-shift detection → ask user trước khi switch context.

### 7.7 Search & retrieval (FR-SR)
- **FR-SR-01** Tìm theo: loại, đối tác, khoảng ngày hết hạn, từ khóa nội dung.
- **FR-SR-02** Bộ lọc nhanh: "sắp hết hạn", "đã hết hạn", "theo đối tác".

### 7.8 Firm partner portal (FR-FP) — read-only ở MVP
- **FR-FP-01** Firm thấy danh mục SME client **đã cấp quyền** (consent bắt buộc).
- **FR-FP-02** Tín hiệu lead: "client X có HĐ sắp hết hạn 30 ngày" (cơ hội tái đàm phán/tư vấn).
- **FR-FP-03** Firm **không** sửa dữ liệu SME ở MVP (chỉ xem + nhận tín hiệu).

### 7.9 Auth, tenancy & permissions (FR-AC)
- **FR-AC-01** Cô lập tenant chặt (pattern `tenantDb` — tái dùng SpurX).
- **FR-AC-02** Role: chủ SME / nhân viên SME / partner / admin.
- **FR-AC-03** Quyền partner xuyên-tenant chỉ mở khi SME **consent rõ ràng**, thu hồi được.

### 7.10 Audit / ledger (FR-AU)
- **FR-AU-01** Ledger append-only cho mọi thay đổi trạng thái (tái dùng SpurX).
- **FR-AU-02** Xem lịch sử một Document: ai sửa term gì, lúc nào. Endpoint: `GET /documents/{id}/events` (PR #323) — document-scoped + obligation-scoped events, ordered `created_at DESC`, paginated.
- **FR-AU-03 (NEW DEC-048):** Event types mới fold vào ledger: `obligation_fulfilled` (DEC-048), `obligation_fulfillment_reverted`, `cascade_triggered`, `clause_edited` (PII-safe: log content lengths không log raw text per D-12), `evidence_attached` (with `purpose=obligation_fulfillment`), `obligation_date_resolved` (FR-OB-13), `re_read_triggered`. Full audit chain: `consent_granted → clause_edited → re_read_triggered → obligation_fulfilled (with evidence_doc_ids) → cascade_triggered`.
- **FR-AU-04 (NEW cycle 6 — Admin extraction observability, Backend PR #350):** Super-admin endpoints `GET /admin/extraction-metrics` + `GET /admin/extraction-metrics/summary` — cross-tenant paginated metrics (provider, model, cost, latency, clause/party/obligation/field/low-confidence counts, warnings); aggregates total_docs/avg_cost/avg_latency/cost_by_provider/cost_by_tenant. Super-admin guard: `require_superadmin` đọc `SUPERADMIN_USERS` env-var allowlist (PM Option B no DB migration). Schema (`tenant_019`): `documents.extraction_model` / `extraction_latency_ms` / `extraction_warnings`.
- **FR-AU-05 (NEW cycle 6 — Extraction progress polling, Backend PR #374):** `documents.processing_stage` + `processing_progress` (`tenant_020` migration). 4 stages: `ocr` (30%) → `llm` (60%) → `saving` (90%) → `done` (100%). **Cycle 7 additions (PR #458 + #463):** enum values `retry_needed` (transient failure) + `two_pass_skeleton` + `two_pass_fill` (auto-triggered MAX_TOKENS recovery). `_mark_failed()` reset progress=0 + stage="failed". Surface trên `DocumentListItem` + `DocumentDetailOut` cho FE polling UX.
- **FR-AU-06 (NEW cycle 7 — `Term.source` provenance API, Backend PR #487):** `TermOut` response shape gains `source: str | None` — values `"extracted"` / `"remap"` / `"manual"` / `null` (legacy pre-migration). No DB migration (column already exists). Cho FE display/filter by extraction provenance.

### 7.11 Tenant quota & billing (FR-TN) — *cost-control MVP*

- **FR-TN-01 Quota check trước ingest:** Mọi `POST /ingest/upload` + `/ingest/bulk` MUST check `docs_used_month < doc_quota` của tenant TRƯỚC khi nhận file. Vượt → HTTP **429 Too Many Requests**, không proceed extraction (hard block per D-11). Phòng cost runaway (Gemini/Claude vision per-doc cost).
- **FR-TN-02 Monthly reset:** APScheduler cron mùng 1 mỗi tháng reset `docs_used_month = 0` cho mọi tenant. `quota_reset_at` cập nhật mốc tiếp theo. Calendar month (không rolling).
- **FR-TN-03 Firm portal usage view:** Firm thấy `docs_used_month / doc_quota` per SME client trong firm portal (sau khi consent grant). Tín hiệu cho firm upsell quota khi SME tiến gần limit.
- **Default quota:** firm-configurable per SME (override per tenant) — không hard-code global default. Quota field do firm set khi onboard tenant.
- **Phase 1 billing:** manual invoice firm (~50-100k VND/client/năm). **Phase 2 (post-MVP):** automated billing (Stripe/VNPay) — xem `PRODUCT_STRATEGY_Khe_v0.2.md` §7.1.

---

## 8. Use cases / luồng chính

- **UC-01 — Ingest & bóc tách:** Chủ quán chụp ảnh HĐ thuê → hệ thống đọc ra đối tác, ngày hết hạn, giá → chủ kiểm tra, sửa 1 field sai → lưu (ghi Event).
- **UC-02 — Nhắc hạn (wow moment):** 30 ngày trước hạn, Telegram bot bắn: "HĐ thuê mặt bằng Q7 hết hạn sau 30 ngày." → chủ chủ động xử lý.
- **UC-03 — Truy vấn:** Chủ hỏi chat "quý này HĐ nào sắp hết hạn?" → trả về danh sách đúng từ kho nghĩa vụ.
- **UC-04 — Tìm lại:** "tìm cái NDA với bên ABC" → ra ngay file gốc.
- **UC-05 — Firm thấy lead:** Đại lý thuế thấy "client X sắp hết HĐ thuê" → chủ động gọi chào dịch vụ → billable (không cướp việc, mà tạo việc).

---

## 9. Non-functional requirements

| ID | Loại | Yêu cầu |
|---|---|---|
| NFR-1 | **An toàn pháp lý (P-1)** | AI không ghi system of record; mọi field AI bóc đều người sửa được; chat read-only ở MVP. |
| NFR-2 | **Bảo mật & quyền riêng tư** | Tuân NĐ 13/2023/NĐ-CP (bảo vệ DLCN); cô lập tenant; consent partner thu hồi được. *(Cần xác minh hiệu lực Luật Bảo vệ DLCN mới.)* |
| NFR-3 | **Lưu trú dữ liệu** | Dữ liệu đặt tại VN (cân nhắc yêu cầu data residency). |
| NFR-4 | **Độ tin cậy nhắc** | Reminder delivery ≥99% (NFR khớp M-4); retry khi Telegram API 5xx; fallback email. |
| NFR-5 | **Hiệu năng** | Trích xuất 1 tài liệu < ~30s; truy vấn chat < ~3s. |
| NFR-6 | **Hạ tầng** | Kế thừa kỷ luật infra v3 SpurX: symlink release bất biến, snapshot trước migrate, giám sát disk. |
| **NFR-7 (NEW cycle 7 — Design System "Sổ cái" v1.1)** | **UI + Accessibility canonical:** Mọi frontend PHẢI theo design tokens từ `docs/mockup_design_system_v1.1.jsx`. **Palette:** primary `Lục Khế #1E5C49` + 4 semantic + paper `#FBFAF7` / ink `#1C2420` + **`border-strong #7E8983`** (WCAG 3:1 cho input/button/checkbox borders). **8 luật màu cứng:** đỏ độc quyền quá-hạn + phá-hủy; 1 vùng đỏ / màn hình; hoàn thành = xám lặng (`done #5A6660` / `done-soft #F0F0EB`), KHÔNG bg-success; v.v. **Font:** Be Vietnam Pro (UI sans) + Source Serif 4 (nguyên văn hợp đồng), self-host, weight 400/500/600. **13 badges chuẩn hóa** (KHÔNG icon/emoji): "Chờ kích hoạt", "Đã thanh lý", ... — vocabulary thống nhất từ tab tài liệu → dashboard → Telegram. **Hợp đồng A11y (v1.1):** semantic-element mandate (button/a không phải div), keyboard-operable, `LiveRegion` cho văn bản tự đổi, icon-only bắt buộc `aria-label`. **4 component ratified:** `NavItem`, `IconButton` (ngoại lệ DUY NHẤT cho luật không-icon), `Dropzone`, `LiveRegion`. **Elevation 4-tầng** (e0–e3, ẩn dụ "giấy xếp lớp"). **Giọng điệu:** xưng "bạn", tự gọi "**Servanda**", KHÔNG dấu chấm than. **WCAG 2.1 AA** — contrast đo thật (formula relative luminance), không khẳng định. Dark mode = v2 (chưa design MVP). |

---

## 10. Tích hợp

| Hệ thống | Vai trò | Trạng thái MVP |
|---|---|---|
| OCR + LLM | Trích xuất Term (đọc) | **Bắt buộc** |
| Telegram bot | Kênh nhắc chính (DEC-006) | **Bắt buộc** — chỉ cần bot token từ @BotFather (không cần approval) |
| Email | Kênh nhắc fallback | Bắt buộc |
| SpurX engine | (Option) chạy logic nhắc như tenant | Tùy chọn |
| Ký số (VNPT/FPT/bên thứ 3) | Ký hợp đồng | **Hoãn** (adapter sau) |
| Hóa đơn điện tử | Đồng bộ chứng từ | **Hoãn** |

---

## 11. Constraints & assumptions

- A-1: Tái dùng hạ tầng SpurX (ledger, multi-tenant, infra v3) — *giảm ~nửa phần khó nhất*.
- A-2: Có ≥1 firm design-partner đồng ý đẩy cho khách (điều kiện cần để chạy MVP thật).
- A-3: ~~Zalo ZNS cần OA doanh nghiệp + duyệt template~~ **Đã giải (DEC-006):** chuyển sang Telegram bot — chỉ cần bot token, không có timeline risk.
- A-4: Template do firm cấp là việc của giai đoạn sau, **không** chặn MVP.
- A-5 (DEC-018 revised): **Vertical = OPEN.** Không khóa F&B/bán lẻ trước. Wedge chọn theo tín hiệu pilot (xem `PRODUCT_STRATEGY_Khe_v0.2.md` §9). Tiêu chí: (a) lượng HĐ đủ tạo đau, (b) có sẵn firm phục vụ ngành đó, (c) loại HĐ có nghĩa vụ ngày-tháng để bóc. F&B/bán lẻ vẫn là ứng viên mạnh (network Mùa Vàng/Bingxue) nhưng không độc quyền.

---

## 12. Rủi ro & câu hỏi mở

| ID | Rủi ro / câu hỏi | Ghi chú |
|---|---|---|
| R-1 | **Rủi ro nền tảng nhà nước (NĐ 337)** | Mảng HĐ lao động có thể bị nền tảng quốc gia + vendor kết nối chiếm → **đừng** làm sản phẩm chỉ về HĐ lao động. Đây là 1 phần lý do **DEC-018 Vertical = OPEN** — đa loại doc trong danh mục, không khóa wedge nào (kể cả lao động) trước. |
| R-2 | ~~Timeline duyệt Zalo ZNS~~ **Closed (DEC-006)** | Đã chuyển Telegram bot — không còn timeline risk. |
| R-3 | **Độ chính xác trích xuất** | Ảnh chụp xấu, chữ ký tay, mẫu HĐ đa dạng → đặt mục tiêu thực tế (M-3 ≥90%), luôn cho người sửa. |
| R-4 | **Cannibalization với firm** | Tuyệt đối không marketing tầng (tương lai) drafting như "thay luật sư"; luôn là "luật sư của bạn, nhanh hơn." |
| R-5 | **Ai sở hữu quan hệ SME?** | Nếu firm "sở hữu" client → churn dính vào firm. Cần điều khoản dữ liệu rõ ràng. |
| R-6 | **Tuân thủ dữ liệu cá nhân** | Xác minh nghĩa vụ theo NĐ 13/2023 và luật DLCN mới trước khi go-live. |
| R-7 | **Naming** | "Khế" mới là tên tạm. |

---

## 13. Milestones (phỏng theo cách chia M1–M4 của SpurX)

| Mốc | Nội dung | Tiêu chí xong |
|---|---|---|
| **M-1 — Concierge baseline (DEC-012)** | 2 firm pilot signed (1 đại lý thuế + 1 law firm). Số hóa tận nơi 20 SME đầu — "ôm cả ngăn kéo". | 2 firm LOI + 20 SME tenant đã có kho doc baseline |
| **M0 — Vertical slice** | Ingest 1 ảnh HĐ thuê → bóc Term → derive `ngày_hết_hạn` (nếu cần) → vào kho nghĩa vụ → bắn 1 nhắc Telegram → chat trả lời "cái gì sắp hết hạn?" | Cả chuỗi chạy thật trên 1 tài liệu thật |
| **M1 — Real product** | Đủ 3 loại doc (thuê/NCC/lao động), search + filter, sửa term, ledger | SME tự onboard không cần hướng dẫn (sau concierge baseline) |
| **M2 — Firm portal** | Cổng firm read-only + tín hiệu lead + consent flow | 2 firm pilot xem được danh mục client (có phép) |
| **M3 — Harden** | Reliability nhắc ≥99%, bảo mật/tenant isolation, infra v3 | Đạt M-1…M-5 ở mục 3.2 |

### Định nghĩa "MVP done"
M-1 → M3 chạy, **2 firm partner trả tiền** + **≥20 SME** kích hoạt thật qua 2 kênh song song, đạt các chỉ số mục 3.2. **Pivot triggers:** xem §3.7 Kill Signals.

---

## 14. Acceptance criteria (rút gọn)

- AC-1: Một SME mới upload 3 tài liệu → trong 5 phút nhận được trang chi tiết đúng + nghĩa vụ tự sinh.
- AC-2: Một HĐ có hạn → nhắc Telegram bắn đúng mốc, ghi Event "đã gửi".
- AC-3: Chat "quý này hết hạn cái gì?" → danh sách khớp 100% với kho nghĩa vụ (zero bịa).
- AC-4: Sửa 1 field bóc sai → ghi Event, lịch sử xem lại được.
- AC-5: Firm chỉ thấy client đã consent; thu hồi consent → mất quyền xem ngay.

---

*Hết v0.10 — Cycle 7 fold (DEC-055 Servanda tier + DEC-056 Obligation OS + Design System v1.1 + ~15 impl entries). Bước kế tiếp: DEC-056 pilot rule pack (1 firm đại lý thuế, thuế + BHXH cơ bản), DEC-016 pricing pin-down với tier shape đã có, KHE_AI `Party.aliases` LLM schema fold, CompletenessVerifier LLM impl (D-03), metadata-pass fix cho two-pass gap (#464).*

*Hết v0.9 — Cycle 6 fold (DEC-049 hybrid OCR + DEC-050 R1-R10 EPIC #362 production PR #402). 8 tenant migrations (`tenant_021..028`) + 2 new entities (Definition + CrossReference) + annex relationship type + lifecycle status enum. Bước kế tiếp: DEC-049 routing policy (opt-in vs default), DEC-016 paywall, `thoi_han_hd` phi-số policy, naming R-7, DEC-028 NĐ 13 chat consent close pre-prod, `Document.provider` clause-gap column, Sprint 2 EPIC #397 (obligation/rights reorg + compliance #105 + Nhóm B metadata).*

*Hết v0.8 — DEC-048 EPIC #300 fold (Obligation fulfillment + dependency chain + clause edit/re-read + evidence + provenance).*

*Hết v0.7 — DEC-031 v2 chat architecture fold. Bước kế tiếp: chốt DEC-016 freemium lever, `thoi_han_hd` phi-số policy, naming R-7, đóng DEC-028 NĐ 13 compliance debt trước prod.*
