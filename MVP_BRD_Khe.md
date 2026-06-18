# BRD — MVP "Khế" (Vibe Document OS cho SME)

> **Tên mã tạm:** Khế *(khế ước; placeholder — đổi tự do bằng find-replace)*
> Một trợ lý tài liệu kinh doanh chat-first cho chủ SME **không có phòng pháp chế**: đổ hết giấy tờ vào một chỗ, không bao giờ quên hạn, tìm trong vài giây — **phân phối qua law firm / đại lý thuế (B2B2B: firm trả tiền, SME free Phase 1)**.

---

## 0. Document control

| Mục | Nội dung |
|---|---|
| Phiên bản | **v0.2** |
| Trạng thái | Folded từ Product Strategy + DEC-006/010/011–018 — *PM-direct fold (exception, Kevin authorize 2026-06-18)* |
| Phạm vi | **Chỉ MVP** (tầng ingest + retrieve + deadline). Không phải full vision. |
| Owner | Kevin (PM) |
| **Tài liệu nền (upstream)** | **`docs/PRODUCT_STRATEGY_Khe.md`** — BRD này dẫn xuất từ Product Strategy (Personas/JTBD/Positioning). Khi mâu thuẫn: Strategy quyết *tại sao/cho ai/job gì*, BRD quyết *hệ thống làm gì*. |
| Liên quan | Tái dùng hạ tầng multi-tenant (ledger, per-tenant DB) — pattern A-1 |

---

## 1. Executive summary

Thị trường CLM hiện tại (HighQ, Icertis, Ironclad…) được thiết kế *cho phòng pháp chế / luật sư*. SME ở VN **đa số không có người làm pháp chế hay hành chính hợp đồng**, nên cả lớp sản phẩm đó lệch khỏi thực tế của họ. Khế lấp khe này: một lớp chat đơn giản đứng trên một **lõi tất định** lo template, deadline, nghĩa vụ và lưu vết.

MVP **không** cố làm tất cả. Nó chỉ giải một nỗi đau an toàn nhưng tần suất cực cao: *"đổ hết hợp đồng/giấy tờ vào đây, hệ thống tự nhắc hạn và cho tìm lại."* Đây là **"ngựa thành Troy"**: tầng này rủi ro pháp lý thấp (AI chỉ đọc, không đẻ nội dung), hút được *cả kho tài liệu* của SME về một chỗ → tạo data moat → mở đường cho soạn/review về sau. Định vị: **"ngôi nhà cho mọi hợp đồng sau khi ký"** — **không cạnh tranh tầng ký số**, đón hậu sóng NĐ 337/2025 (DEC-014).

**Mô hình B2B2B (DEC-011):** phân phối qua **law firm / đại lý thuế** làm kênh **và là khách hàng trả tiền** (per-client). SME dùng **miễn phí Phase 1**. Tầng nhắc hạn không cướp việc luật sư mà còn *đẻ lead* cho họ (nhắc "sắp hết hạn" → khách hỏi luật sư tái đàm phán → billable). SME-pays mở ở GĐ2 khi có tầng soạn/review.

---

## 2. Bối cảnh & vấn đề

### 2.1 Nỗi đau (SME end-user)
- Hợp đồng/giấy tờ nằm rải rác: email, Zalo, ngăn kéo, máy kế toán. Không có một chỗ.
- **Quên gia hạn / quên deadline** → mất quyền lợi, bị phạt, mất mặt bằng.
- Cần tìm một hợp đồng cũ → lục cả buổi.
- Không có người chuyên trách; chủ tự làm hoặc khoán cho kế toán/luật sư ngoài.

### 2.2 Vì sao bây giờ (catalyst)
- **NĐ 337/2025/NĐ-CP** (hợp đồng lao động điện tử): hiệu lực 01/01/2026; nền tảng quốc gia vận hành chậm nhất 01/07/2026 → cú hích lớn đẩy SME số hóa giấy tờ. *(Định vị "hậu-ký": Khế là ngôi nhà cho HĐ sau khi ký, KHÔNG cạnh tranh tầng ký số — DEC-014.)*
- **NĐ 70/2025** (hóa đơn điện tử, kết nối dữ liệu thuế) → áp lực compliance, SME buộc số hóa chứng từ.
- Giá SaaS quốc tế (USD) đắt lên → khe cho sản phẩm định giá nội địa.

### 2.3 Vì sao kênh law firm / đại lý thuế
- Họ là "bộ phận pháp lý/hành chính thuê ngoài" mà SME **vốn đã có**.
- Đại lý thuế chạm mọi SME *hàng tháng* (khai thuế) → gắn sâu hơn cả law firm.
- Tầng nhắc hạn **đẻ việc** cho họ thay vì cạnh tranh → họ vui vẻ đẩy.

### 2.4 Mô hình kinh doanh — B2B2B (DEC-011)
- **Firm trả tiền** theo đầu client (~50-100k/client/năm). **SME free Phase 1.**
- **SME-pays mở ở GĐ2** khi mở tầng soạn/review (lawyer-in-loop) — xem Product Strategy §Roadmap.
- Lý do chọn kênh B2B trước (không mass self-serve): SME VN **WTP thấp** cho "nhắc hạn"; firm vốn có niềm tin + đã thu phí; firm là người trả tiền. Mass self-serve giữ làm **contingency** (kill signal #2, §12).

---

## 3. Mục tiêu & chỉ số thành công (MVP)

### 3.1 Mục tiêu kinh doanh
- B-1: **2-firm pilot song song** (DEC-013): **1 đại lý thuế + 1 law firm**, mỗi firm đẩy sản phẩm cho khách — đánh giá kênh sau **90 ngày**. *(Thay mục tiêu cũ "≥1 firm design-partner".)*
- B-2: Qua 2 firm đó, **≥20 SME** kích hoạt thật (10 SME mỗi firm).

### 3.2 Mục tiêu sản phẩm (đo được)
| ID | Chỉ số | Mục tiêu MVP |
|---|---|---|
| M-1 | Activation: SME có ≥3 tài liệu trong kho tuần đầu | ≥60% — **đo SAU concierge baseline** (DEC-012: 20 SME đầu KHÔNG bắt tự upload, số hóa tận nơi/firm thu hộ) |
| M-2 | Time-to-first-wow: từ upload đến lần nhắc hạn đúng đầu tiên | < 5 phút thao tác |
| M-3 | Độ chính xác trích xuất `ngày hết hạn` (trên ảnh/PDF VN) | ≥90% *(lưu ý: `ngày hết hạn` thường được **derive** = `ngày hiệu lực + thời hạn`, xem FR-OB-01)* |
| M-4 | Độ tin cậy gửi nhắc (reminder delivery) | ≥99% |
| M-5 | Truy vấn chat "cái gì sắp hết hạn?" trả lời đúng | ≥95% |

### 3.3 Non-goals (MVP KHÔNG làm)
- KHÔNG soạn hợp đồng tự động (drafting).
- KHÔNG review/cảnh báo rủi ro điều khoản.
- KHÔNG tự xây ký số — sẽ tích hợp bên thứ ba ở giai đoạn sau.
- KHÔNG đa thị trường — **VN-first**.
- KHÔNG marketplace template — firm cấp template để dành pha sau.

---

## 4. Nguyên tắc & guardrail (ràng buộc mọi requirement bên dưới)

| ID | Nguyên tắc | Hệ quả |
|---|---|---|
| P-1 | **AI không bao giờ là system of record** | AI chỉ được *đọc/bóc tách* (vào) và *điền template đã duyệt* (ra, giai đoạn sau). Sự thật nằm ở lõi tất định + ledger. |
| P-2 | **Mọi ghi xuống lõi mang tính pháp lý phải qua xác nhận của người** | Authoring mode bắt readback → preview → user confirm. (MVP gần như chỉ có đọc, nên rủi ro thấp.) |
| P-3 | **Ngựa thành Troy** | Dẫn bằng ingest + retrieve + deadline. Drafting/review là upsell sau. |
| P-4 | **Tích hợp, đừng tự build** | Ký số, hóa đơn ĐT, kênh nhắc (**Telegram**) → dùng bên thứ ba. |
| P-5 | **Đa loại document trong KIẾN TRÚC; vertical OPEN** | Lõi general; **không khóa ngành trước** (DEC-018). Chọn wedge theo tín hiệu pilot (lượng HĐ đủ đau + kênh firm sẵn + HĐ có nghĩa vụ ngày tháng). F&B/bán lẻ chỉ là *một* ứng viên wedge. |

---

## 5. Đối tượng người dùng (MVP)

*(Personas chi tiết: `docs/PRODUCT_STRATEGY_Khe.md` §2.)*

| Persona | Vai trò | Cần gì ở MVP |
|---|---|---|
| **Chủ SME** (primary user) | Người đổ tài liệu vào, nhận nhắc, hỏi-đáp | Đơn giản đến mức không cần học; nhắc đúng kênh (**Telegram**) |
| **Nhân viên SME** (kế toán/admin nội bộ, nếu có) | Upload hộ, tra cứu | Tìm nhanh, quyền hạn cơ bản |
| **Firm partner** (luật sư / đại lý thuế) | **Economic Buyer (trả tiền per-client)** + kênh phân phối; xem danh mục khách (có phép); nhận tín hiệu lead | Cổng firm read-only + tín hiệu "khách sắp cần"; quản lý kho client |
| **Admin hệ thống** (nội bộ Khế) | Vận hành, hỗ trợ onboarding (gồm concierge) | Quản trị tenant/partner |

---

## 6. Domain glossary (object lõi)

| Thuật ngữ | Định nghĩa |
|---|---|
| **Document** | Một văn bản: file gốc (bất biến) + phân loại + các Term + liên kết. Không phải chỉ là file — là một object có cấu trúc. |
| **Term / Field** | Giá trị có cấu trúc bóc từ Document: loại, đối tác (Party), ngày hiệu lực, **ngày hết hạn** (có thể derived), giá trị, điều khoản thanh toán. |
| **Obligation** | **Object trung tâm của MVP.** Một cam kết rời rạc, *có ngày*, *có trạng thái*, suy ra từ Document. VD: "trả 50tr ngày 5 hàng tháng", "gia hạn/chấm dứt trước 60 ngày khi hết hạn". Trường: `id`, `document_id`, `loại` (một lần / lặp), `ngày_đáo_hạn` / lịch lặp, `mô_tả`, `trạng_thái` (chờ / hoàn thành / quá hạn / hủy), `nhắc_trước_X_ngày`. |
| **Party** | Đối tác trong tài liệu, được chuẩn hóa (để "tìm mọi HĐ với bên ABC" chạy đúng). |
| **Event (Ledger)** | Bản ghi append-only mọi thay đổi trạng thái (ingest, sửa term, hoàn thành nghĩa vụ, đã gửi nhắc, consent…). Sửa = ghi event mới (reversal), **không** edit-in-place. |
| **VisionExtractionProvider** | Interface bóc tách 1-lần-gọi (OCR + phân loại + bóc Term) — **không tách OCR riêng** (DEC-002). Provider: Gemini Flash (primary) + Claude Haiku/Sonnet (fallback). |
| **Template / Clause** | Mẫu/điều khoản do firm thẩm định, có version. *Định nghĩa sẵn trong glossary nhưng chưa kích hoạt ở MVP.* |
| **Tenant** | Một SME (cô lập dữ liệu — per-tenant DB). |
| **Partner** | Một firm; **khách hàng trả tiền**; role **xuyên tenant** (nhìn nhiều SME theo phân quyền + consent). |

---

## 7. Functional requirements (MVP)

*(FR neo vào Jobs J1–J5 — xem Product Strategy §3 JTBD.)*

### 7.1 Ingestion (FR-IN) — *phục vụ J1*
- **FR-IN-01** Upload qua: ảnh chụp (camera), kéo-thả PDF/Word, forward email tới địa chỉ riêng của tenant.
- **FR-IN-02** Lưu file gốc bất biến; mọi xử lý sau dựa trên bản gốc này.
- **FR-IN-03** Hàng đợi xử lý bất đồng bộ; hiển thị trạng thái "đang đọc…" cho từng tài liệu.
- **FR-IN-04** **Bulk ingest (concierge mode):** nhận batch nhiều file (≤20/lần) để số hóa cả kho client trong 1 lần (DEC-012).

### 7.2 Extraction — AI safe-read (FR-EX) — *VisionExtractionProvider (DEC-002)*
- **FR-EX-01** Tự nhận **loại tài liệu** (MVP hỗ trợ tối thiểu các loại của wedge đã chọn, vd: HĐ thuê mặt bằng, HĐ nhà cung cấp, HĐ lao động).
- **FR-EX-02** Bóc các Term tối thiểu: đối tác, ngày hiệu lực, **ngày hết hạn**, **thời hạn HĐ**, giá trị, điều khoản gia hạn.
- **FR-EX-03** AI **chỉ đọc** — không sinh/sửa nội dung pháp lý (P-1, D-06). Single-call vision, không tách OCR.
- **FR-EX-04** Mọi field bóc ra phải **cho người sửa**; sửa → ghi Event (P-2, D-07).
- **FR-EX-05** Hiện độ tin cậy (confidence) / cờ "cần kiểm tra" (`needs_review`) per field; không chắc → `value=null`, không phỏng đoán (D-08).
- **FR-EX-06** **Consent gate (NĐ 13/2023, DEC-010):** trước lần extraction đầu tiên của tenant, phải có consent log (`purpose=vision_extraction` + `consent_reference`) trong `events`; thiếu → từ chối (403).

### 7.3 Document record & IR (FR-DR)
- **FR-DR-01** Mỗi Document có trang chi tiết: file gốc + các Term có cấu trúc + danh sách Obligation phát sinh.
- **FR-DR-02** Liên kết quan hệ cơ bản: phụ lục → hợp đồng gốc (MVP: thủ công cũng được).

### 7.4 Obligation & deadline engine (FR-OB) — *trái tim MVP (J2)*
- **FR-OB-01** Tự sinh Obligation từ Term. **Derive `ngày hết hạn`:** nếu Term có `ngày hết hạn` → dùng; nếu thiếu nhưng có `ngày hiệu lực` + `thời hạn HĐ` (dạng số) → derive `ngày hết hạn = ngày hiệu lực + thời hạn` *(HĐ VN thường ghi thời hạn, không ghi thẳng ngày hết hạn — insight pilot)*. Thời hạn phi-số ("vô thời hạn") → **policy chờ chốt** (skip / flag-for-human / recurring — câu hỏi mở §12).
- **FR-OB-02** Hỗ trợ nghĩa vụ **một lần** và **lặp** (hàng tháng/quý).
- **FR-OB-03** Tính tất định "nghĩa vụ nào tới hạn trong [khoảng]" — **không phải AI đoán**, là truy vấn trên kho.
- **FR-OB-04** Cho người đánh dấu hoàn thành / hoãn / hủy → ghi Event.

### 7.5 Reminders / notifications (FR-RM) — *phục vụ J2*
- **FR-RM-01** Nhắc qua **Telegram bot** (kênh chính — DEC-006; bot token từ @BotFather, không cần đăng ký OA/duyệt template) — fallback email.
- **FR-RM-02** Mặc định nhắc trước 30 ngày + 7 ngày; cho chỉnh.
- **FR-RM-03** Ghi Event mỗi lần gửi nhắc (đã gửi / thất bại); retry khi Telegram lỗi 5xx.
- **FR-RM-04** Digest định kỳ: "tuần này / tháng này có gì sắp tới."

### 7.6 Chat — query/read mode (FR-CQ) — *phục vụ J3*
- **FR-CQ-01** Hỏi-đáp ngôn ngữ tự nhiên (tiếng Việt) trên kho: "cái gì sắp hết hạn quý này?", "tìm HĐ với bên ABC", "HĐ thuê Q7 còn hạn bao lâu?".
- **FR-CQ-02** Chat **chỉ đọc** ở MVP; mọi câu trả lời truy ra Document/Obligation cụ thể (có dẫn nguồn, không bịa).
- **FR-CQ-03** Không trả lời được → nói thẳng "không tìm thấy thông tin này trong hồ sơ của bạn", không phỏng đoán (D-08).

### 7.7 Search & retrieval (FR-SR)
- **FR-SR-01** Tìm theo: loại, đối tác, khoảng ngày hết hạn, từ khóa nội dung.
- **FR-SR-02** Bộ lọc nhanh: "sắp hết hạn", "đã hết hạn", "theo đối tác".

### 7.8 Firm partner portal (FR-FP) — read-only ở MVP — *phục vụ J4/J5*
- **FR-FP-01** Firm thấy danh mục SME client **đã cấp quyền** (consent bắt buộc).
- **FR-FP-02** Tín hiệu lead: "client X có HĐ sắp hết hạn 30 ngày" (cơ hội tái đàm phán/tư vấn).
- **FR-FP-03** Firm **không** sửa dữ liệu SME ở MVP (chỉ xem + nhận tín hiệu — D-09).

### 7.9 Auth, tenancy & permissions (FR-AC)
- **FR-AC-01** Cô lập tenant chặt (per-tenant DB; `get_tenant_session(tid)`, không `SessionLocal()` trực tiếp).
- **FR-AC-02** Role: chủ SME / nhân viên SME / partner / admin.
- **FR-AC-03** Quyền partner xuyên-tenant chỉ mở khi SME **consent rõ ràng**, thu hồi được (D-10).

### 7.10 Audit / ledger (FR-AU)
- **FR-AU-01** Ledger append-only cho mọi thay đổi trạng thái.
- **FR-AU-02** Xem lịch sử một Document: ai sửa term gì, lúc nào.

---

## 8. Use cases / luồng chính

- **UC-01 — Ingest & bóc tách:** Chủ quán chụp ảnh HĐ thuê → hệ thống đọc ra đối tác, ngày hết hạn, giá → chủ kiểm tra, sửa 1 field sai → lưu (ghi Event).
- **UC-02 — Nhắc hạn (wow moment):** 30 ngày trước hạn, **Telegram** bắn: "HĐ thuê mặt bằng Q7 hết hạn sau 30 ngày." → chủ chủ động xử lý.
- **UC-03 — Truy vấn:** Chủ hỏi chat "quý này HĐ nào sắp hết hạn?" → trả về danh sách đúng từ kho nghĩa vụ.
- **UC-04 — Tìm lại:** "tìm cái NDA với bên ABC" → ra ngay file gốc.
- **UC-05 — Firm thấy lead:** Đại lý thuế thấy "client X sắp hết HĐ thuê" → chủ động gọi chào dịch vụ → billable (không cướp việc, mà tạo việc).
- **UC-06 — Concierge onboarding:** Firm thu hộ cả kho HĐ của SME → admin/firm bulk-upload (≤20/lần) → hệ thống bóc tách hàng loạt → SME có kho đầy đủ ngay từ ngày đầu (DEC-012).

---

## 9. Non-functional requirements

| ID | Loại | Yêu cầu |
|---|---|---|
| NFR-1 | **An toàn pháp lý (P-1)** | AI không ghi system of record; mọi field AI bóc đều người sửa được; chat read-only ở MVP. |
| NFR-2 | **Bảo mật & quyền riêng tư** | Tuân NĐ 13/2023/NĐ-CP (bảo vệ DLCN); cô lập tenant; consent partner thu hồi được. PII processing log `purpose` + `consent_reference` vào `events`. |
| NFR-3 | **Lưu trú dữ liệu** | Dữ liệu **at-rest đặt tại VN**. **Ngoại lệ (DEC-010):** ảnh/PDF gửi tới **LLM API US-hosted** (Gemini/Claude) cho Vision extraction được chấp nhận **Phase 1** với consent rõ + audit log; re-evaluate self-host Phase 2+. |
| NFR-4 | **Độ tin cậy nhắc** | Reminder delivery ≥99% (khớp M-4); retry khi Telegram lỗi 5xx. |
| NFR-5 | **Hiệu năng** | Trích xuất 1 tài liệu < ~30s (p95 mục tiêu <10s); truy vấn chat < ~3s. |
| NFR-6 | **Hạ tầng** | Deploy qua GitHub Actions CI/CD (không SSH trực tiếp bypass gate); snapshot trước migrate; per-tenant migration loop; giám sát. |

---

## 10. Tích hợp

| Hệ thống | Vai trò | Trạng thái MVP |
|---|---|---|
| **VisionExtractionProvider** (Gemini Flash primary + Claude Haiku/Sonnet fallback) | Trích xuất Term — **single-call, không tách OCR** (DEC-002) | **Bắt buộc** |
| **Telegram bot** (token @BotFather) | Kênh nhắc chính (DEC-006) — không cần OA/duyệt | **Bắt buộc** |
| Email | Kênh nhắc fallback | Bắt buộc |
| Ký số (VNPT/FPT/bên thứ 3) | Ký hợp đồng | **Hoãn** (adapter sau) |
| Hóa đơn điện tử | Đồng bộ chứng từ | **Hoãn** |

---

## 11. Constraints & assumptions

- A-1: Tái dùng pattern hạ tầng multi-tenant (ledger, per-tenant DB) — *giảm phần khó nhất*. Sprint 0 backend đã build (master.db + per-tenant).
- A-2: **2 firm pilot** (1 đại lý thuế + 1 law firm) đồng ý đẩy cho khách (DEC-013) — điều kiện cần để chạy MVP thật.
- A-3: **Telegram bot** — token từ @BotFather, **không cần duyệt OA** → rủi ro timeline kênh nhắc **đã loại bỏ** (so với Zalo ZNS cũ).
- A-4: Template do firm cấp là việc của giai đoạn sau, **không** chặn MVP.
- A-5: **Vertical = OPEN (DEC-018)** — không khóa ngành trước; chọn wedge theo tín hiệu pilot. F&B/bán lẻ là *một* ứng viên (lợi thế network Mùa Vàng/Bingxue), không độc quyền.

---

## 12. Rủi ro & câu hỏi mở

| ID | Rủi ro / câu hỏi | Ghi chú |
|---|---|---|
| R-1 | **Rủi ro nền tảng nhà nước (NĐ 337)** | Mảng HĐ lao động có thể bị nền tảng quốc gia + vendor kết nối chiếm → **đừng** làm sản phẩm chỉ về HĐ lao động; coi nó là một loại doc trong danh mục. Củng cố bởi DEC-018 (vertical OPEN). |
| R-2 | **Độ chính xác trích xuất** | Ảnh chụp xấu, chữ ký tay, mẫu HĐ đa dạng → mục tiêu thực tế (M-3 ≥90%), luôn cho người sửa; fallback Claude khi confidence thấp. |
| R-3 | **Cannibalization với firm** | Tuyệt đối không marketing tầng (tương lai) drafting như "thay luật sư"; luôn là "luật sư của bạn, nhanh hơn." |
| R-4 | **Ai sở hữu quan hệ SME?** | Nếu firm "sở hữu" client → churn dính vào firm. Cần điều khoản dữ liệu rõ ràng. |
| R-5 | **Tuân thủ dữ liệu cá nhân** | Xác minh nghĩa vụ theo NĐ 13/2023 trước go-live (KHE_Compliance). DEC-010: US-hosted LLM OK Phase 1 với consent + audit. |
| R-6 | **Naming** | "Khế" mới là tên tạm (R-7 cũ). |
| Q-1 | **Policy `thời hạn` phi-số** | "Vô thời hạn"/"kể từ khi nghiệm thu" → engine không derive `ngày hết hạn`. Chốt: (a) skip, (b) flag-for-human, hay (c) recurring trigger? — **cần PM quyết**. |
| Q-2 | **DEC-016 freemium lever** | Telegram giữ (DEC-006), ZNS bỏ. Value metric/paywall lever nào? — **cần Kevin quyết**. |

### 12.1 Kill / pivot signals (DEC-015 — falsifiable)
1. Retention tuần 4 < 30% sau concierge → pivot wedge sang DMS cho firm nhỏ.
2. Firm không trả nhưng SME convert tốt qua reminder paywall → **bỏ B2B2B, chuyển direct freemium** (kích hoạt motion mass self-serve — Product Strategy §6/§10).
3. Cả 2 firm không đẩy nổi 10 SME trong 90 ngày → kênh sai → thử hiệp hội ngành / cộng đồng.

---

## 13. Milestones

| Mốc | Nội dung | Tiêu chí xong |
|---|---|---|
| **M0 — Vertical slice** | Ingest 1 ảnh HĐ thuê → bóc/derive `ngày hết hạn` → vào kho nghĩa vụ → bắn 1 nhắc **Telegram** → chat trả lời "cái gì sắp hết hạn?" | Cả chuỗi chạy thật trên 1 tài liệu thật |
| **M1 — Real product** | Đủ các loại doc của wedge đã chọn, search + filter, sửa term, ledger, bulk-ingest concierge | SME tự onboard không cần hướng dẫn (sau concierge baseline) |
| **M2 — Firm portal** | Cổng firm read-only + tín hiệu lead + consent flow | 1 firm xem được danh mục client (có phép) |
| **M3 — Harden** | Reliability nhắc ≥99%, bảo mật/tenant isolation, per-tenant migration | Đạt M-1…M-5 ở mục 3.2 |

### Định nghĩa "MVP done"
M0 → M3 chạy, có **2 firm partner** (DEC-013) và **≥20 SME** kích hoạt thật, đạt các chỉ số mục 3.2.

---

## 14. Acceptance criteria (rút gọn)

- AC-1: Một SME mới có 3 tài liệu trong kho → trong 5 phút nhận được trang chi tiết đúng + nghĩa vụ tự sinh.
- AC-2: Một HĐ có hạn → nhắc **Telegram** bắn đúng mốc, ghi Event "đã gửi".
- AC-3: Chat "quý này hết hạn cái gì?" → danh sách khớp 100% với kho nghĩa vụ (zero bịa).
- AC-4: Sửa 1 field bóc sai → ghi Event, lịch sử xem lại được.
- AC-5: Firm chỉ thấy client đã consent; thu hồi consent → mất quyền xem ngay.
- AC-6: Extraction chỉ chạy sau khi consent đã log (NĐ 13/2023, DEC-010); thiếu consent → 403.

---

## Changelog

- **v0.2 (2026-06-18):** Fold Product Strategy + DEC-006/010/011–018. Zalo ZNS → **Telegram** (toàn bộ). Thêm **§2.4 mô hình B2B2B**, **§12.1 kill signals**. Vertical **OPEN** (P-5, A-5). Firm = **Economic Buyer**. 2-firm pilot (B-1, A-2). Concierge (M-1, FR-IN-04, UC-06). VisionExtractionProvider single-call (§10, FR-EX). Consent gate (FR-EX-06, AC-6). Derive `ngày hết hạn` (FR-OB-01). NFR-3 reconcile US-hosted LLM (DEC-010). FR neo JTBD. *PM-direct fold (exception — Kevin authorize); KHE_Docs canonical-hóa + đồng bộ version scheme khi spawn.*
- **v0.1 (2026-06-09):** Bản đầu — ingest + retrieve + deadline; Zalo ZNS; seed F&B/bán lẻ; ≥1 firm design-partner.

*Bước kế tiếp: chốt naming (R-6), policy thời hạn phi-số (Q-1), freemium lever (Q-2).*
