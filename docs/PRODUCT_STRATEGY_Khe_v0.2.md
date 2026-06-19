# Khế — Product Strategy Foundation (v0.2)

> **Vai trò tài liệu:** Đây là **tài liệu nền** của Khế. Mọi tài liệu downstream — **BRD → SRS → roadmap → mockup → code** — phải dẫn xuất và nhất quán với file này. Khi có mâu thuẫn, file này là nguồn chân lý về *tại sao / cho ai / job gì*; BRD quyết *hệ thống phải làm gì*.
> **Trạng thái:** **Canonical** (KHE_Docs adopted 2026-06-18 from PM draft on branch `claude/pm-assistant`). Cascade upstream của BRD → SRS.
> **Last updated:** 2026-06-18
> **Tham chiếu:** `docs/MVP_BRD_Khe_v0.1.md` (v0.2) · `docs/SRS_v0.1.md` · `CLAUDE.md` (D-rules) · DEC log (`docs/teams/pm_assistant_STATE.md`)

---

## 0. TL;DR

Khế là **Hệ điều hành nghĩa vụ hợp đồng hậu-ký** cho SME Việt Nam — nơi mọi hợp đồng *đã ký* được số hóa, tra cứu tức thì bằng chat, và nhắc hạn tự động. Khế **không** soạn thảo, **không** ký số, **không** review rủi ro (đó là các tầng upsell sau). Khế được **phân phối qua cố vấn ngoài** (đại lý thuế / law firm) — họ là khách hàng trả tiền (B2B2B), vận hành Khế trên kho client của họ; SME dùng miễn phí ở Phase 1. Wedge là **deadline + tuân thủ**, đón hậu sóng NĐ 337/2025 — không phải tốc độ chốt sale.

---

## 1. Vấn đề

SME Việt Nam ký hợp đồng liên tục — thuê mặt bằng, nhà cung cấp, lao động, dịch vụ — rồi **ném file vào ngăn kéo / Google Drive / Zalo / email và quên**. Hệ quả:

- **Thất thoát do quên hạn:** quên gia hạn, quên nghĩa vụ thanh toán, lỡ mốc tuân thủ lao động.
- **Mất dấu khi cần:** không tìm lại được điều khoản lúc tranh chấp; nhân sự nghỉ việc → HĐ mất dấu.
- **Không có phòng pháp lý in-house:** chủ doanh nghiệp/quản lý tự ôm, hoặc nhờ đại lý thuế/luật sư nhắc rời rạc, thủ công.

Đây là nỗi đau **"phải có"** (must-have), không phải "có thì tốt" — vì nó **bào mòn dòng tiền trực tiếp**. Nỗi đau **không bị khóa theo ngành**: bất kỳ SME nào có lượng HĐ đủ lớn để tạo đau đều là ứng viên (xem §9 — Vertical OPEN).

---

## 2. Personas

Mô hình B2B2B có hai phía: **firm** (người trả tiền) và **SME** (người dùng cuối, free Phase 1). Ví dụ giữ ngành-agnostic vì vertical còn mở.

### 2.1 — Firm Champion / Economic Buyer — *"Chị Hằng, chủ đại lý thuế"*
- **Bối cảnh:** điều hành đại lý thuế phục vụ ~40 SME, 3-5 nhân viên. Hoặc partner một law firm nhỏ.
- **Mục tiêu:** giữ chân client, tăng phí dịch vụ, không để client gặp sự cố (vì đó là uy tín của chị).
- **Nỗi đau:** theo dõi hạn HĐ + nghĩa vụ của hàng chục client bằng Excel/trí nhớ; client trách khi lỡ hạn; khó tạo dịch vụ mới để upsell.
- **Quan hệ với Khế:** **người trả tiền**; vận hành Khế trên kho client; là người onboard SME vào hệ thống.
- **Đo thành công:** số client giữ được + dịch vụ giá trị gia tăng bán thêm.

### 2.2 — SME Owner (người dùng chính, free) — *"Anh Dũng, giám đốc SME ~25 người"*
- **Bối cảnh:** chủ doanh nghiệp, **không có phòng pháp lý**, tự ôm hợp đồng.
- **Mục tiêu:** vận hành trơn tru, không mất tiền oan, không phải tự nhớ chi tiết hành chính.
- **Nỗi đau:** ký xong quên; phát hiện trễ hạn gia hạn mặt bằng / lỡ mốc thanh toán; mất file khi nhân viên nghỉ.
- **Quan hệ với Khế:** dùng **chat** để hỏi, nhận **nhắc Telegram**; được firm onboard (concierge Phase 1).
- **Đo thành công:** không còn "sự cố hợp đồng"; yên tâm.

### 2.3 — SME Admin / Ops (người dùng phụ trợ) — *"Bạn Linh, kế toán/hành chính"*
- **Bối cảnh:** người thực tế xử lý giấy tờ, upload, tra cứu trong SME.
- **Mục tiêu:** làm nhanh, không bị sếp hỏi "HĐ X đâu rồi?".
- **Nỗi đau:** lục tìm file rải rác, nhập liệu thủ công.
- **Quan hệ với Khế:** upload (hoặc concierge giúp), sửa field đã bóc (D-07), dùng chat tra cứu.

---

## 3. Jobs to be Done (JTBD)

Khách "thuê" Khế để hoàn thành các job sau (format: *Khi [tình huống], tôi muốn [động lực], để [kết quả mong đợi]*).

| ID | Persona | Job statement | Chiều | Năng lực Khế phục vụ |
|---|---|---|---|---|
| **J1** | SME Owner / Admin | Khi vừa ký một HĐ, tôi muốn cất nó vào nơi tìm lại được tức thì, để khi cần (đối chiếu, tranh chấp, nhân sự nghỉ) tôi không mất dấu | Functional | Ingest + kho tài liệu bất biến + chat retrieve |
| **J2** | SME Owner | Khi một nghĩa vụ/thời hạn sắp đến, tôi muốn được nhắc trước đủ sớm, để không mất tiền vì quên gia hạn / lỡ mốc / bị phạt | Functional (**core**) | Obligation engine + Telegram reminder |
| **J3** | SME Owner / Admin | Khi tôi có câu hỏi về HĐ của mình, tôi muốn câu trả lời ngay, để không phải lục file hay làm phiền luật sư cho việc nhỏ | Functional | Chat-first, retrieve-only (D-08) |
| **J-E** | SME Owner | (Emotional) ...để tôi **yên tâm** rằng không có "quả bom hẹn giờ" nào trong đống giấy tờ đã ký | Emotional | Toàn hệ — nghĩa vụ hiển thị + chủ động nhắc |
| **J4** | Firm | Khi tôi phục vụ nhiều client, tôi muốn thấy toàn bộ nghĩa vụ HĐ của họ ở một nơi, để chủ động cảnh báo/tư vấn trước khi có sự cố | Functional | Firm portal đa-tenant (consent-gated) |
| **J5** | Firm | (Social/business) Khi tôi muốn giữ và tăng giá trị client, tôi muốn công cụ tạo dịch vụ giá trị gia tăng định kỳ, để client thấy tôi **không thể thay thế** | Social | B2B2B — reminder đẻ việc cho firm |

**J2 là trái tim** (the core job). Toàn bộ MVP tồn tại để hoàn thành J1→J2→J3 cho SME, và J4→J5 cho firm.

---

## 4. Why — How — What (để thực hiện JTBD)

### WHY (niềm tin — lý do Khế tồn tại)
> **Không một SME nào nên mất tiền hay cơ hội chỉ vì một hợp đồng đã ký bị bỏ quên.** Mọi cam kết đã ký xứng đáng được nhớ và thực hiện đúng hạn.

### HOW (cách Khế khác biệt để hiện thực hóa WHY)
1. **Đi qua người SME đã tin** (cố vấn ngoài / firm) thay vì bán lạnh — niềm tin có sẵn, kênh có sẵn.
2. **AI chỉ-đọc, bóc nghĩa vụ tiếng Việt** — không bịa, không thay người quyết (D-01 / D-06 / D-08).
3. **Biến file tĩnh → dòng nhắc có hệ thống** (obligation graph: cam kết rời rạc, có ngày, có trạng thái).
4. **Tập trung hậu-ký** — không ôm đồm soạn/ký; đón catalyst pháp lý (NĐ 337/70/13).

### WHAT (sản phẩm cụ thể)
**Ingest** (Vision extraction 1-lần-gọi) + **Retrieve** (chat) + **Deadline** (obligation + Telegram reminder), trên nền **multi-tenant**, **phân phối qua firm portal**.

### Mapping — WHAT thực hiện JTBD như thế nào
| Năng lực (WHAT) | Hoàn thành Job |
|---|---|
| Vision extraction → kho tài liệu | J1 (cất + tìm lại) |
| Obligation engine + Telegram reminder | **J2** (nhắc trước hạn) + J-E (yên tâm) |
| Chat retrieve-only | J3 (hỏi-đáp tức thì) |
| Firm portal đa-tenant (consent) | J4 (firm thấy toàn cảnh client) |
| Mô hình B2B2B + tầng reminder | J5 (firm tạo giá trị, giữ client) |

---

## 5. Định vị (April Dunford framework)

Vì sản phẩm giai đoạn sớm, đây là **Positioning Thesis (giả thuyết lỏng)** — tinh chỉnh qua pilot, không khóa cứng.

### 5.1 — Competitive alternatives (khách dùng gì nếu không có Khế?)
| Đối tượng | Giải pháp thay thế hiện tại |
|---|---|
| **SME** | Ngăn kéo giấy · Google Drive/Zalo/email · Excel theo dõi hạn thủ công · **trí nhớ** · nhờ firm nhắc rời rạc |
| **Firm** | Excel/thủ công theo dõi hạn HĐ từng client · không có hệ thống tập trung xuyên client |

### 5.2 — Unique attributes (Khế có gì khác)
- **Single-call Vision extraction** (OCR + phân loại + bóc nghĩa vụ trong 1 lần gọi) tuned cho HĐ **tiếng Việt**.
- **Obligation graph** — quản lý cam kết rời rạc có ngày/trạng thái, không chỉ lưu file.
- **Phân phối qua firm (B2B2B)** — firm vận hành trên kho client.
- **Chat-first, retrieve-only** — không bịa (D-08).
- **Hậu-ký positioning** — không cạnh tranh tầng ký số; đón NĐ 337/70/13.
- **Multi-tenant, đa loại document** — lõi general, không khóa ngành.

### 5.3 — Value + proof
| Cho ai | Giá trị | Bằng chứng (đo ở pilot) |
|---|---|---|
| SME | "Ngôi nhà" cho mọi HĐ sau khi ký — tìm trong giây, được nhắc trước hạn | Retention W4 ≥30% post-concierge |
| Firm | Dịch vụ giá trị gia tăng → giữ client + doanh thu recurring | 2-firm pilot, 10 SME/firm, 90 ngày |

### 5.4 — Target market characteristics (ai khao khát nhất)
"SME" tự thân là phân khúc **tồi**. Best-fit actionable của Khế:
- SME **không có phòng pháp lý in-house**.
- **ĐÃ có quan hệ với đại lý thuế / law firm** (kênh sẵn).
- **Có lượng HĐ đủ tạo đau** (mặt bằng, NCC, lao động, dịch vụ).
- **Người trả tiền = Firm** (Phase 1).

### 5.5 — Market category (gọi tên để tạo đúng kỳ vọng)
- **KHÔNG** là "CLM đầy đủ" → tránh kỳ vọng Enterprise (drafting/redlining/e-sign/ERP).
- **Category:** *"Hệ điều hành nghĩa vụ & tài liệu hợp đồng hậu-ký cho SME"* — phân phối qua cố vấn ngoài.

### 5.6 — Positioning Thesis (câu định vị lỏng)
> **Cho** các SME Việt Nam không có phòng pháp lý nhưng đã có cố vấn ngoài (đại lý thuế / law firm),
> **Khế là** Hệ điều hành nghĩa vụ hợp đồng hậu-ký — nơi mọi HĐ đã ký được số hóa, tra cứu tức thì bằng chat, và nhắc hạn tự động —
> **vận hành bởi chính firm** trên kho client của họ.
> **Khác với** việc chắp vá Google Drive / Excel / trí nhớ, Khế biến nghĩa vụ rời rạc thành dòng nhắc có hệ thống,
> **đón hậu sóng NĐ 337/2025** (không cạnh tranh tầng ký số).

---

## 6. GTM motion — kênh B2B trước, self-serve là contingency

Có hai motion đưa sản phẩm tới SME:
- **Mass self-serve (PLG):** SME tự tìm qua ads/content/cold email, tự đăng ký, tự trả. Cần CAC thấp, onboarding ~15 phút, chu kỳ <14 ngày.
- **Kênh B2B (channel-led):** bán qua đối tác đã có quan hệ với SME (firm); định vị sắc cho best-fit; concierge onboarding.

**Khế chọn kênh B2B trước** vì: (a) SME VN **WTP thấp** cho "nhắc hạn" → self-serve rủi ro activation; (b) firm vốn là "phòng pháp lý thuê ngoài" của SME → đã có niềm tin + đã thu phí; (c) firm là người trả tiền (B2B2B). Mass self-serve được giữ làm **contingency** (xem kill signals §10).

---

## 7. Mô hình kinh doanh — B2B2B

- **Firm trả tiền** theo đầu client (~50-100k/client/năm). **SME free Phase 1.**
- **SME-pays mở ở GĐ2** khi mở tầng soạn/review (lawyer-in-loop).
- Tầng reminder **đẻ việc cho firm** thay vì cướp việc → firm không sợ bị thay thế.

### 7.1 Billing roadmap (DEC-2026-06-19)

| Phase | Billing motion | Tech |
|---|---|---|
| **Phase 1 (MVP)** | **Manual invoice** firm theo đầu client (~50-100k/client/năm). Cycle quý/năm. Quota guard ở backend ngăn cost runaway (FR-TN-01..03 BRD). | Excel/email invoice. Quota schema only. |
| **Phase 2 (post-MVP)** | **Automated billing** — Stripe / VN payment gateway. Per-client metering từ quota counter. Firm self-serve subscription. | Stripe/VNPay integration. Webhook → master.db `tenants.billing_status`. |

**Phase 1 cost-control:** D-11 (CLAUDE.md) bắt buộc quota check trước mọi ingest. Default quota **firm-configurable per SME** (override per tenant). Reset **calendar month — mùng 1** via APScheduler. Over-quota → **hard block 429** (no extraction proceeds — DEC-2026-06-19 ratified).

---

## 8. Phạm vi sản phẩm (MVP)

**LÀM (M0→M3):** Ingest + Retrieve + Deadline.
**KHÔNG làm ở MVP:** soạn HĐ tự động · review rủi ro · ký số (integrate sau) · đa thị trường (VN-first) · marketplace template.

**D-rules ràng buộc (trích `CLAUDE.md`):**
- **D-01:** AI không bao giờ là system of record.
- **D-03:** Dẫn bằng ingest + retrieve + deadline. Drafting là upsell sau.
- **D-06:** AI extraction CHỈ ĐỌC — không sinh/sửa nội dung pháp lý.
- **D-08:** Chat không trả lời được → nói "không tìm thấy", không phỏng đoán.
- **D-09 / D-10:** Firm không sửa data SME ở MVP; quyền xuyên-tenant chỉ mở khi SME consent rõ, thu hồi được.

---

## 9. Vertical strategy = **OPEN**

> **Quyết định (DEC-018, 2026-06-18):** KHÔNG khóa focus vào F&B/bán lẻ. Lõi general; chọn vertical theo **tín hiệu pilot**.

- **Lõi general:** multi-tenant, đa loại document, obligation graph không phụ thuộc ngành.
- **Vertical seed = mở:** F&B/bán lẻ chỉ là *một* ứng viên wedge, không độc quyền. Agency/dịch vụ B2B, sản xuất nhỏ, giáo dục... đều khả thi.
- **Tiêu chí chọn wedge** (đo ở pilot): (a) lượng HĐ đủ tạo đau, (b) có sẵn kênh firm phục vụ ngành đó, (c) loại HĐ có nghĩa vụ rõ ngày tháng để bóc.

---

## 10. Roadmap 3 giai đoạn + Kill signals

| GĐ | Thời gian | Bán gì | Moat |
|---|---|---|---|
| **1. Troy + Concierge** | Q3-Q4/2026 | Firm-pays per client; SME free; concierge 20 SME | Kho nghĩa vụ + extraction VN tuned |
| **2. Soạn/Review lawyer-in-loop** | 2027 | SME-pays drafting từ template firm duyệt; firm revenue share | Template library + firm network |
| **3. Obligation graph hạ tầng** | 2027+ | Nghĩa vụ thanh toán ↔ công nợ, hóa đơn ĐT/ngân hàng, benchmark | Graph xuyên nghìn SME |

**Concierge onboarding (DEC-012):** 20 SME đầu KHÔNG bắt tự upload — số hóa cả ngăn kéo / firm thu hộ. M-1 (activation) đo SAU concierge baseline.
**2-firm pilot (DEC-013):** 1 đại lý thuế + 1 law firm, mỗi firm 10 SME, đánh giá kênh 90 ngày.

**Kill / pivot signals (DEC-015, falsifiable):**
1. Retention tuần 4 < 30% sau concierge → pivot wedge sang DMS cho firm nhỏ.
2. Firm không trả nhưng SME convert tốt qua reminder paywall → **bỏ B2B2B, chuyển direct freemium** (kích hoạt motion mass self-serve ở §6: pricing self-serve ~$30-100/mo, growth tự động hóa).
3. Cả 2 firm không đẩy nổi 10 SME trong 90 ngày → kênh sai → thử hiệp hội ngành / cộng đồng.

---

## 11. Quyết định đang mở

| ID | Vấn đề | Trạng thái |
|---|---|---|
| **DEC-016** | Freemium paywall lever — Telegram giữ (DEC-006), ZNS bỏ. Value metric/lever nào? Pricing self-serve ~$30-100/mo là input cho motion contingency. | Open |
| **DEC-018** | Vertical = OPEN — đã quyết hướng; cần fold wording vào D-05/BRD/CLAUDE.md | Cần ratify wording |

---

## Changelog

- **v0.2 cycle-3 fold (2026-06-19, KHE_Docs):** Add §7.1 Billing roadmap (Phase 1 manual / Phase 2 automated). Quota guard policy ratified per Kevin: firm-configurable per SME, calendar-month reset, hard block 429. Folds DOCS_INBOX comment 22.
- **v0.2 canonical-adoption (2026-06-18, KHE_Docs):** Pulled từ PM draft branch `claude/pm-assistant` vào docs lane. File rename: `PRODUCT_STRATEGY_Khe.md` → `PRODUCT_STRATEGY_Khe_v0.2.md` (version-in-filename per docs convention). No content edits — chỉ update §0 status line. Folded DOCS_INBOX comments 13 + 14 (DEC-018 + PRODUCT_STRATEGY adoption).
- **v0.2 (2026-06-18, KHE_PM_Assistant):** Tái cấu trúc thành **tài liệu nền độc lập** (bỏ framing thảo luận). Thêm **§2 Personas · §3 Jobs to be Done · §4 Why-How-What (Golden Circle)** + mapping WHAT→JTBD. Mục GTM motion viết lại trung tính (kênh B2B vs self-serve). Khẳng định vai trò: nền → BRD → SRS.
- **v0.1 (2026-06-18, KHE_PM_Assistant):** Bản đầu — định vị April Dunford 5-component + Positioning Thesis; vertical chuyển OPEN (DEC-018); roadmap 3 giai đoạn + kill signals.
