# Khế — Product Strategy (v0.1)

> **Trạng thái:** PM draft (KHE_PM_Assistant) — chờ Kevin ratify + KHE_Docs fold thành canonical.
> **Mục đích:** Tài liệu nền để Kevin + cộng sự (và mọi session) *on the same page* về định vị, mô hình, phạm vi sản phẩm.
> **Last updated:** 2026-06-18 · Branch `claude/pm-assistant`
> **Tham chiếu:** `docs/MVP_BRD_Khe.md` · `docs/teams/pm_assistant_STATE.md` (DEC log) · `CLAUDE.md` (D-rules)

---

## 0. TL;DR — Một đoạn

Khế là **Hệ điều hành nghĩa vụ hợp đồng hậu-ký** cho SME Việt Nam — nơi mọi hợp đồng *đã ký* được số hóa, tra cứu tức thì bằng chat, và nhắc hạn tự động. Khế **không** soạn thảo, **không** ký số, **không** review rủi ro (đó là upsell các giai đoạn sau). Khế được **phân phối qua cố vấn ngoài** (đại lý thuế / law firm) — họ là khách hàng trả tiền (B2B2B), vận hành Khế trên kho client của họ; SME dùng miễn phí ở Phase 1. Wedge là **deadline + tuân thủ** (đón hậu sóng NĐ 337/2025), không phải tốc độ chốt sale.

---

## 1. Vấn đề (nỗi đau cốt lõi)

SME Việt Nam ký hợp đồng liên tục — thuê mặt bằng, nhà cung cấp, lao động, dịch vụ — rồi **ném file vào ngăn kéo / Google Drive / Zalo / email và quên**. Hệ quả:

- **Thất thoát do quên hạn:** quên gia hạn, quên nghĩa vụ thanh toán, lỡ mốc tuân thủ lao động.
- **Mất dấu khi cần:** không tìm lại được điều khoản lúc tranh chấp; nhân sự nghỉ việc → HĐ mất dấu.
- **Không có phòng pháp lý in-house:** chủ doanh nghiệp/quản lý tự ôm, hoặc nhờ đại lý thuế/luật sư nhắc rời rạc, thủ công.

Đây là pain **"phải có"** (must-have), không phải "có thì tốt" — vì nó **bào mòn dòng tiền trực tiếp**.

> **Lưu ý:** Nỗi đau này **không bị khóa theo ngành**. Bất kỳ SME nào có lượng HĐ đủ lớn để tạo đau đều là ứng viên. Xem §6 (Vertical = OPEN).

---

## 2. Định vị (April Dunford framework)

Định vị được làm tường minh qua 5 thành phần của April Dunford. Vì sản phẩm ở giai đoạn sớm, đây là **Positioning Thesis (giả thuyết lỏng)** — sẽ tinh chỉnh qua pilot thực tế, không khóa cứng.

### 2.1 — Competitive alternatives (khách dùng gì nếu không có Khế?)

| Đối tượng | Giải pháp thay thế hiện tại |
|---|---|
| **SME** | Ngăn kéo giấy · Google Drive/Zalo/email · Excel theo dõi hạn thủ công · **trí nhớ** · nhờ đại lý thuế/luật sư nhắc rời rạc |
| **Firm** (đại lý thuế/law firm) | Excel/thủ công theo dõi hạn HĐ của từng client · không có hệ thống tập trung xuyên client |

### 2.2 — Unique attributes (Khế có gì mà thứ khác không có)

- **Single-call Vision extraction** (OCR + phân loại + bóc nghĩa vụ trong 1 lần gọi) tuned cho HĐ **tiếng Việt**.
- **Obligation graph** — quản lý *cam kết rời rạc, có ngày, có trạng thái* — không chỉ lưu file.
- **Phân phối qua firm (B2B2B)** — firm vận hành trên kho client, không phải bán lẻ tới từng SME.
- **Chat-first, retrieve-only** — trả lời bằng dữ liệu đã bóc + xác nhận; **không bịa** (D-08).
- **Hậu-ký positioning** — không cạnh tranh tầng ký số; đón catalyst NĐ 337/70/13.
- **Multi-tenant, đa loại document** — lõi general, không khóa ngành.

### 2.3 — Value + proof (giá trị + bằng chứng)

| Cho ai | Giá trị | Bằng chứng (đo ở pilot) |
|---|---|---|
| SME | "Ngôi nhà" cho mọi HĐ sau khi ký — tìm trong giây, được nhắc trước hạn, không thất thoát | Retention W4 ≥30% post-concierge |
| Firm | Đẻ thêm dịch vụ giá trị gia tăng cho client → giữ chân client + doanh thu recurring | 2-firm pilot, 10 SME mỗi firm, 90 ngày |

### 2.4 — Target market characteristics (ai khao khát nhất)

Theo Dunford: "SME" tự thân là phân khúc **tồi**. Best-fit của Khế (actionable):

- **SME không có phòng pháp lý in-house** — chủ/quản lý tự ôm HĐ.
- **ĐÃ có quan hệ với đại lý thuế / law firm** — kênh phân phối sẵn (không phải educate từ đầu).
- **Có lượng HĐ đủ tạo đau** — thuê mặt bằng (chi phí lớn nhất), nhà cung cấp, lao động (NĐ 337), dịch vụ.
- **Người trả tiền (Economic Buyer) = Firm**, không phải SME (Phase 1).

> **Vertical: OPEN** (xem §6). F&B/bán lẻ chỉ là *một* wedge ví dụ ban đầu, không phải vùng khóa.

### 2.5 — Market category (gọi tên để tạo đúng kỳ vọng)

- **KHÔNG** định vị là "CLM đầy đủ" → tránh kỳ vọng Enterprise (drafting, redlining, e-sign, tích hợp ERP).
- **Category:** *"Hệ điều hành nghĩa vụ & tài liệu hợp đồng hậu-ký cho SME"* (Document & Obligation OS) — **phân phối qua cố vấn ngoài**.
- Tên gọi tạo kỳ vọng: **không phải nơi soạn/ký**, mà là **nơi lưu + tra cứu + nhắc hạn sau khi ký**.

### 2.6 — Positioning Thesis (câu định vị lỏng, early-stage)

> **Cho** các SME Việt Nam không có phòng pháp lý nhưng đã có cố vấn ngoài (đại lý thuế / law firm),
> **Khế là** Hệ điều hành nghĩa vụ hợp đồng hậu-ký — nơi mọi HĐ đã ký được số hóa, tra cứu tức thì bằng chat, và nhắc hạn tự động —
> **vận hành bởi chính firm** trên kho client của họ.
> **Khác với** việc chắp vá Google Drive / Excel / trí nhớ, Khế biến nghĩa vụ rời rạc thành dòng nhắc có hệ thống,
> **đón hậu sóng NĐ 337/2025** (không cạnh tranh tầng ký số).

*Thesis này là giả thuyết — đem đi kiểm chứng qua concierge + 2-firm pilot, tinh chỉnh dần (xem §8 kill signals).*

---

## 3. Đính chính: "B2C → B2B" — đây là về MOTION BÁN, không phải vertical

Phân tích của cộng sự (April Dunford-style) đề xuất chuyển từ **bán mass kiểu B2C** sang **kênh B2B**. Làm rõ để tránh hiểu lầm:

| | **"B2C-style" motion** (cộng sự gọi) | **"B2B channel" motion** (Dunford / Khế đang theo) |
|---|---|---|
| Cách tiếp cận khách | Mass self-serve, media push/pull (ads, content, cold email PLG) | Bán qua kênh/đối tác, định vị sắc cho best-fit |
| Người mua | SME tự tìm, tự đăng ký, tự trả thẻ | Firm là kênh **và** người trả tiền |
| Onboarding | Self-serve 15 phút | Concierge / firm thu hộ |
| Khế? | = Plan B (DEC-015 fallback) | ✅ **= mô hình chính (B2B2B)** |

**Kết luận:** Cộng sự **pro-channel, pro-Dunford** — điều này **ALIGN** với Khế. Phần "tránh B2C retail" của cộng sự thực ra là *"tránh mass self-serve cho khách lẻ giá trị thấp"*, **không** phải bác bỏ ngành bán lẻ. Khế (B2B2B qua firm) chính là motion "B2B channel" mà cộng sự khuyến nghị.

> Bản phân tích self-serve $30-100/mo + Apollo + cold email của cộng sự được **lưu làm blueprint Plan B** (xem §8) — kích hoạt nếu kill signal "firm không trả nhưng SME convert" bật.

---

## 4. Mô hình kinh doanh — B2B2B (DEC-011)

- **Firm trả tiền** theo đầu client (~50-100k/client/năm). **SME free Phase 1.**
- **SME-pays mở ở GĐ2** khi mở tầng soạn/review (lawyer-in-loop).
- Lý do: SME VN **WTP thấp** cho "nhắc hạn" → bán trực tiếp self-serve rủi ro. Firm vốn là "phòng pháp lý thuê ngoài" của SME → đã có quan hệ, đã có niềm tin, đã thu phí.
- Tầng reminder **đẻ việc cho firm** thay vì cướp việc (D: firm không sợ bị thay thế).

---

## 5. Phạm vi sản phẩm (MVP)

**LÀM (M0→M3):** Ingest + Retrieve + Deadline.
**KHÔNG làm ở MVP:** soạn HĐ tự động (drafting) · review rủi ro · ký số (integrate sau) · đa thị trường (VN-first) · marketplace template.

**D-rules ràng buộc (trích `CLAUDE.md`):**
- **D-01:** AI không bao giờ là system of record.
- **D-03:** Dẫn bằng ingest + retrieve + deadline. Drafting là upsell sau.
- **D-06:** AI extraction CHỈ ĐỌC — không sinh/sửa nội dung pháp lý.
- **D-08:** Chat không trả lời được → nói "không tìm thấy", không phỏng đoán.
- **D-09 / D-10:** Firm không sửa data SME ở MVP; quyền xuyên-tenant chỉ mở khi SME consent rõ, thu hồi được.

---

## 6. Vertical strategy = **OPEN** (điều chỉnh 2026-06-18)

> **Quyết định (Kevin, 2026-06-18):** KHÔNG khóa focus vào F&B/bán lẻ. Lõi general; chọn vertical theo **tín hiệu pilot**.

- **Lõi general** (giữ nguyên): multi-tenant, đa loại document, obligation graph không phụ thuộc ngành.
- **Vertical seed = mở:** F&B/bán lẻ là *một* ứng viên wedge (HĐ thuê mặt bằng + NCC + lao động — giá trị cao, đau rõ), **nhưng không độc quyền**. Các vertical khác đều khả thi: agency/dịch vụ B2B, sản xuất nhỏ, giáo dục, v.v.
- **Tiêu chí chọn wedge** (đo ở pilot, không quyết trước): (a) lượng HĐ đủ tạo đau, (b) có sẵn kênh firm phục vụ ngành đó, (c) loại HĐ có nghĩa vụ rõ ngày tháng để bóc.
- **Hệ quả:** điều chỉnh wording D-05 + "Vertical seed" trong `CLAUDE.md`/BRD: *"sắc trong seed"* → *"sắc theo wedge chọn bởi tín hiệu pilot, không khóa ngành trước"*. (Flag DOCS_INBOX cho KHE_Docs fold.)

---

## 7. GTM (go-to-market)

- **Concierge onboarding (DEC-012):** 20 SME đầu KHÔNG bắt tự upload — số hóa cả ngăn kéo trong 1 ngày / firm thu hộ. M-1 (activation) đo SAU concierge baseline.
- **2-firm pilot (DEC-013):** 1 đại lý thuế + 1 law firm song song, mỗi firm 10 SME, đánh giá kênh 90 ngày.
- **Validation discipline** (harvest từ cộng sự): trong pilot conversations, lọc best-fit bằng phản ứng — ai *"thở dài"* khi nhắc quản lý HĐ là best-fit; ai nói *"Excel vẫn ổn"* → bỏ qua.

---

## 8. Roadmap 3 giai đoạn + Kill signals

| GĐ | Thời gian | Bán gì | Moat |
|---|---|---|---|
| **1. Troy + Concierge** | Q3-Q4/2026 | Firm-pays per client; SME free; concierge 20 SME | Kho nghĩa vụ + extraction VN tuned |
| **2. Soạn/Review lawyer-in-loop** | 2027 | SME-pays drafting từ template firm duyệt; firm revenue share | Template library + firm network |
| **3. Obligation graph hạ tầng** | 2027+ | Nghĩa vụ thanh toán ↔ công nợ, hóa đơn ĐT/ngân hàng, benchmark | Graph xuyên nghìn SME |

**Kill / pivot signals (DEC-015, falsifiable):**
1. Retention tuần 4 < 30% sau concierge → pivot wedge sang DMS cho firm nhỏ.
2. **Firm không trả nhưng SME convert tốt qua reminder paywall → bỏ B2B2B, direct freemium** → *(đây là lúc kích hoạt **Plan B**: playbook self-serve $30-100/mo + Apollo + cold email của cộng sự).*
3. Cả 2 firm không đẩy nổi 10 SME trong 90 ngày → kênh sai → thử hiệp hội ngành / cộng đồng.

---

## 9. Quyết định đang mở (cần Kevin chốt)

| ID | Vấn đề | Trạng thái |
|---|---|---|
| **DEC-016** | Freemium paywall lever — Telegram giữ (DEC-006), ZNS bỏ. Value metric/lever nào? Input mới: cộng sự gợi ý pricing self-serve $30-100/mo cho Plan B. | Open |
| **DEC-018** | Vertical = OPEN (đã quyết hướng 2026-06-18) — cần fold vào D-05/BRD/CLAUDE.md | Cần ratify wording |

---

## Changelog

- **v0.1 (2026-06-18):** Bản đầu. Định vị làm tường minh theo April Dunford 5-component + Positioning Thesis. Đính chính B2C→B2B (motion, không phải vertical). Vertical chuyển sang OPEN. Tích hợp phân tích cộng sự (align + Plan B blueprint). PM draft — chờ ratify + KHE_Docs canonical fold.
