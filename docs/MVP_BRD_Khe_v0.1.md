# BRD — MVP "Khế" (Vibe Document OS cho SME)

> **Tên mã tạm:** Khế *(khế ước; placeholder — đổi tự do bằng find-replace)*
> Một trợ lý tài liệu kinh doanh chat-first cho chủ SME **không có phòng pháp chế**: đổ hết giấy tờ vào một chỗ, không bao giờ quên hạn, tìm trong vài giây — phân phối qua law firm / đại lý thuế.

---

## 0. Document control

| Mục | Nội dung |
|---|---|
| Phiên bản | v0.1 (draft) |
| Trạng thái | Đề xuất — chờ PM review |
| Phạm vi | **Chỉ MVP** (tầng ingest + retrieve + deadline). Không phải full vision. |
| Owner | Kevin (PM) |
| Liên quan | Tái dùng hạ tầng SpurX (ledger, multi-tenant, infra v3) |

---

## Changelog

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| v0.1 | 2026-06-09 | Kevin (PM) / ERP_PM_Assistant | Initial draft. Scope MVP ingest + retrieve + deadline. Topology 10 sessions. D-rules P-1..P-5. |

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

### 3.1 Mục tiêu kinh doanh
- B-1: Ký được **≥1 firm design-partner** (law firm hoặc đại lý thuế) đẩy sản phẩm cho khách của họ.
- B-2: Qua firm đó, **≥20 SME** kích hoạt thật.

### 3.2 Mục tiêu sản phẩm (đo được)
| ID | Chỉ số | Mục tiêu MVP |
|---|---|---|
| M-1 | Activation: SME upload ≥3 tài liệu trong tuần đầu | ≥60% SME onboarded |
| M-2 | Time-to-first-wow: từ upload đến lần nhắc hạn đúng đầu tiên | < 5 phút thao tác |
| M-3 | Độ chính xác trích xuất `ngày hết hạn` (trên ảnh/PDF VN) | ≥90% |
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
| P-4 | **Tích hợp, đừng tự build** | Ký số, hóa đơn ĐT, kênh nhắc (Zalo) → dùng bên thứ ba. |
| P-5 | **Đa loại document trong KIẾN TRÚC, sắc trong SEED** | Lõi general; nhưng seed/onboarding tập trung 1 vertical (HĐ thuê + NCC ngành F&B/bán lẻ). |

---

## 5. Đối tượng người dùng (MVP)

| Persona | Vai trò | Cần gì ở MVP |
|---|---|---|
| **Chủ SME** (primary user) | Người đổ tài liệu vào, nhận nhắc, hỏi-đáp | Đơn giản đến mức không cần học; nhắc đúng kênh (Zalo) |
| **Nhân viên SME** (kế toán/admin nội bộ, nếu có) | Upload hộ, tra cứu | Tìm nhanh, quyền hạn cơ bản |
| **Firm partner** (luật sư / đại lý thuế) | Kênh phân phối; xem danh mục khách (có phép); nhận tín hiệu lead | Cổng firm read-only + tín hiệu "khách sắp cần" |
| **Admin hệ thống** (nội bộ Khế) | Vận hành, hỗ trợ onboarding | Quản trị tenant/partner |

---

## 6. Domain glossary (object lõi)

| Thuật ngữ | Định nghĩa |
|---|---|
| **Document** | Một văn bản: file gốc (bất biến) + phân loại + các Term + liên kết. Không phải chỉ là file — là một object có cấu trúc. |
| **Term / Field** | Giá trị có cấu trúc bóc từ Document: loại, đối tác (Party), ngày hiệu lực, **ngày hết hạn**, giá trị, điều khoản thanh toán. |
| **Obligation** | **Object trung tâm của MVP.** Một cam kết rời rạc, *có ngày*, *có trạng thái*, suy ra từ Document. VD: "trả 50tr ngày 5 hàng tháng", "gia hạn/chấm dứt trước 60 ngày khi hết hạn". Trường: `id`, `document_id`, `loại` (một lần / lặp), `ngày_đáo_hạn` / lịch lặp, `mô_tả`, `trạng_thái` (chờ / hoàn thành / quá hạn / hủy), `nhắc_trước_X_ngày`. |
| **Party** | Đối tác trong tài liệu, được chuẩn hóa (để "tìm mọi HĐ với bên ABC" chạy đúng). |
| **Event (Ledger)** | Bản ghi append-only mọi thay đổi trạng thái (ingest, sửa term, hoàn thành nghĩa vụ, đã gửi nhắc…). Sửa = ghi event mới (reversal), **không** edit-in-place. Tái dùng pattern SpurX. |
| **Template / Clause** | Mẫu/điều khoản do firm thẩm định, có version. *Định nghĩa sẵn trong glossary nhưng chưa kích hoạt ở MVP.* |
| **Tenant** | Một SME (cô lập dữ liệu, theo pattern `tenantDb` của SpurX). |
| **Partner** | Một firm; role **xuyên tenant** (nhìn nhiều SME theo phân quyền). Là phần *mới* so với SpurX. |

---

## 7. Functional requirements (MVP)

### 7.1 Ingestion (FR-IN)
- **FR-IN-01** Upload qua: ảnh chụp (camera), kéo-thả PDF/Word, forward email tới địa chỉ riêng của tenant.
- **FR-IN-02** Lưu file gốc bất biến; mọi xử lý sau dựa trên bản gốc này.
- **FR-IN-03** Hàng đợi xử lý bất đồng bộ; hiển thị trạng thái "đang đọc…" cho từng tài liệu.

### 7.2 Extraction — AI safe-read (FR-EX)
- **FR-EX-01** Tự nhận **loại tài liệu** (MVP hỗ trợ tối thiểu: HĐ thuê mặt bằng, HĐ nhà cung cấp, HĐ lao động).
- **FR-EX-02** Bóc các Term tối thiểu: đối tác, ngày hiệu lực, **ngày hết hạn**, giá trị, điều khoản gia hạn.
- **FR-EX-03** AI **chỉ đọc** — không sinh/sửa nội dung pháp lý (P-1).
- **FR-EX-04** Mọi field bóc ra phải **cho người sửa**; sửa → ghi Event (P-2).
- **FR-EX-05** Hiện độ tin cậy / cờ "cần kiểm tra" khi không chắc.

### 7.3 Document record & IR (FR-DR)
- **FR-DR-01** Mỗi Document có trang chi tiết: file gốc + các Term có cấu trúc + danh sách Obligation phát sinh.
- **FR-DR-02** Liên kết quan hệ cơ bản: phụ lục → hợp đồng gốc (MVP: thủ công cũng được).

### 7.4 Obligation & deadline engine (FR-OB) — *trái tim MVP*
- **FR-OB-01** Tự sinh Obligation từ Term (vd: `ngày_hết_hạn` → nghĩa vụ "gia hạn/chấm dứt trước N ngày").
- **FR-OB-02** Hỗ trợ nghĩa vụ **một lần** và **lặp** (hàng tháng/quý).
- **FR-OB-03** Tính tất định "nghĩa vụ nào tới hạn trong [khoảng]" — **không phải AI đoán**, là truy vấn trên kho.
- **FR-OB-04** Cho người đánh dấu hoàn thành / hoãn / hủy → ghi Event.
- **FR-OB-05** *(Option kiến trúc)* Logic nhắc có thể chạy như **một tenant của SpurX** (rule: `hết_hạn − hôm_nay ≤ N → bắn nhắc`).

### 7.5 Reminders / notifications (FR-RM)
- **FR-RM-01** Nhắc qua **Zalo ZNS** (kênh chính, cần OA + template ZNS đã duyệt) — fallback email.
- **FR-RM-02** Mặc định nhắc trước 30 ngày + 7 ngày; cho chỉnh.
- **FR-RM-03** Ghi Event mỗi lần gửi nhắc (đã gửi / thất bại).
- **FR-RM-04** Digest định kỳ: "tuần này / tháng này có gì sắp tới."

### 7.6 Chat — query/read mode (FR-CQ)
- **FR-CQ-01** Hỏi-đáp ngôn ngữ tự nhiên (tiếng Việt) trên kho: "cái gì sắp hết hạn quý này?", "tìm HĐ với bên ABC", "HĐ thuê Q7 còn hạn bao lâu?".
- **FR-CQ-02** Chat **chỉ đọc** ở MVP; mọi câu trả lời truy ra Document/Obligation cụ thể (có dẫn nguồn, không bịa).
- **FR-CQ-03** Không trả lời được → nói thẳng "không tìm thấy", không phỏng đoán.

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
- **FR-AU-02** Xem lịch sử một Document: ai sửa term gì, lúc nào.

---

## 8. Use cases / luồng chính

- **UC-01 — Ingest & bóc tách:** Chủ quán chụp ảnh HĐ thuê → hệ thống đọc ra đối tác, ngày hết hạn, giá → chủ kiểm tra, sửa 1 field sai → lưu (ghi Event).
- **UC-02 — Nhắc hạn (wow moment):** 30 ngày trước hạn, Zalo ZNS bắn: "HĐ thuê mặt bằng Q7 hết hạn sau 30 ngày." → chủ chủ động xử lý.
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
| NFR-4 | **Độ tin cậy nhắc** | Reminder delivery ≥99% (NFR khớp M-4); retry khi ZNS lỗi. |
| NFR-5 | **Hiệu năng** | Trích xuất 1 tài liệu < ~30s; truy vấn chat < ~3s. |
| NFR-6 | **Hạ tầng** | Kế thừa kỷ luật infra v3 SpurX: symlink release bất biến, snapshot trước migrate, giám sát disk. |

---

## 10. Tích hợp

| Hệ thống | Vai trò | Trạng thái MVP |
|---|---|---|
| OCR + LLM | Trích xuất Term (đọc) | **Bắt buộc** |
| Zalo ZNS (qua OA) | Kênh nhắc chính | **Bắt buộc** — cần đăng ký OA + template ZNS duyệt trước |
| Email | Kênh nhắc fallback | Bắt buộc |
| SpurX engine | (Option) chạy logic nhắc như tenant | Tùy chọn |
| Ký số (VNPT/FPT/bên thứ 3) | Ký hợp đồng | **Hoãn** (adapter sau) |
| Hóa đơn điện tử | Đồng bộ chứng từ | **Hoãn** |

---

## 11. Constraints & assumptions

- A-1: Tái dùng hạ tầng SpurX (ledger, multi-tenant, infra v3) — *giảm ~nửa phần khó nhất*.
- A-2: Có ≥1 firm design-partner đồng ý đẩy cho khách (điều kiện cần để chạy MVP thật).
- A-3: Zalo ZNS cần OA doanh nghiệp + duyệt template — **rủi ro timeline**, phải khởi động sớm.
- A-4: Template do firm cấp là việc của giai đoạn sau, **không** chặn MVP.
- A-5: Seed vertical đầu tiên = HĐ thuê + NCC ngành F&B/bán lẻ (lợi thế network Mùa Vàng/Bingxue).

---

## 12. Rủi ro & câu hỏi mở

| ID | Rủi ro / câu hỏi | Ghi chú |
|---|---|---|
| R-1 | **Rủi ro nền tảng nhà nước (NĐ 337)** | Mảng HĐ lao động có thể bị nền tảng quốc gia + vendor kết nối chiếm → **đừng** làm sản phẩm chỉ về HĐ lao động; coi nó là một loại doc trong danh mục. |
| R-2 | **Timeline duyệt Zalo ZNS** | Có thể chậm; cần kế hoạch B (email-first) cho demo. |
| R-3 | **Độ chính xác trích xuất** | Ảnh chụp xấu, chữ ký tay, mẫu HĐ đa dạng → đặt mục tiêu thực tế (M-3 ≥90%), luôn cho người sửa. |
| R-4 | **Cannibalization với firm** | Tuyệt đối không marketing tầng (tương lai) drafting như "thay luật sư"; luôn là "luật sư của bạn, nhanh hơn." |
| R-5 | **Ai sở hữu quan hệ SME?** | Nếu firm "sở hữu" client → churn dính vào firm. Cần điều khoản dữ liệu rõ ràng. |
| R-6 | **Tuân thủ dữ liệu cá nhân** | Xác minh nghĩa vụ theo NĐ 13/2023 và luật DLCN mới trước khi go-live. |
| R-7 | **Naming** | "Khế" mới là tên tạm. |

---

## 13. Milestones (phỏng theo cách chia M1–M4 của SpurX)

| Mốc | Nội dung | Tiêu chí xong |
|---|---|---|
| **M0 — Vertical slice** | Ingest 1 ảnh HĐ thuê → bóc `ngày hết hạn` → vào kho nghĩa vụ → bắn 1 nhắc Zalo → chat trả lời "cái gì sắp hết hạn?" | Cả chuỗi chạy thật trên 1 tài liệu thật |
| **M1 — Real product** | Đủ 3 loại doc (thuê/NCC/lao động), search + filter, sửa term, ledger | SME tự onboard không cần hướng dẫn |
| **M2 — Firm portal** | Cổng firm read-only + tín hiệu lead + consent flow | 1 firm xem được danh mục client (có phép) |
| **M3 — Harden** | Reliability nhắc ≥99%, bảo mật/tenant isolation, infra v3 | Đạt M-1…M-5 ở mục 3.2 |

### Định nghĩa "MVP done"
M0 → M3 chạy, có **≥1 firm partner** và **≥20 SME** kích hoạt thật, đạt các chỉ số mục 3.2.

---

## 14. Acceptance criteria (rút gọn)

- AC-1: Một SME mới upload 3 tài liệu → trong 5 phút nhận được trang chi tiết đúng + nghĩa vụ tự sinh.
- AC-2: Một HĐ có hạn → nhắc Zalo bắn đúng mốc, ghi Event "đã gửi".
- AC-3: Chat "quý này hết hạn cái gì?" → danh sách khớp 100% với kho nghĩa vụ (zero bịa).
- AC-4: Sửa 1 field bóc sai → ghi Event, lịch sử xem lại được.
- AC-5: Firm chỉ thấy client đã consent; thu hồi consent → mất quyền xem ngay.

---

*Hết v0.1 — chờ PM review. Bước kế tiếp đề xuất: chốt naming, rồi mô hình giá ba phía.*
