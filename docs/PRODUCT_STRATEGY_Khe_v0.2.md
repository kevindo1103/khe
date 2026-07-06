# Servanda (Khế) — Product Strategy Foundation (v0.4)

> **Vai trò tài liệu:** Đây là **tài liệu nền** của Servanda. Mọi tài liệu downstream — **BRD → SRS → roadmap → mockup → code** — phải dẫn xuất và nhất quán với file này. Khi có mâu thuẫn, file này là nguồn chân lý về *tại sao / cho ai / job gì*; BRD quyết *hệ thống phải làm gì*.
> **Trạng thái:** **Canonical**. Cascade upstream của BRD → SRS.
> **Last updated:** 2026-07-03
> **Tham chiếu:** `docs/MVP_BRD_Khe_v0.1.md` (v0.9) · `docs/SRS_v0.1.md` (v0.6) · `CLAUDE.md` (D-rules) · DEC log (`docs/teams/pm_assistant_STATE.md`)

---

## 0. TL;DR

**Servanda là "Obligation OS" cho SME Việt Nam** (DEC-056) — nền tảng hợp nhất **mọi nghĩa vụ có ngày**: nghĩa vụ hợp đồng (nguồn thứ nhất) + nghĩa vụ tuân thủ pháp luật thuế/BHXH/ngành dọc (nguồn thứ hai). CEO có sổ cái nghĩa vụ duy nhất, không phải phụ thuộc kế toán nhớ hạn thuế, phụ thuộc bộ phận sản phẩm nhớ tuân thủ. Servanda **không** soạn HĐ, **không** ký số, **không** review rủi ro, **không** tư vấn nghĩa vụ pháp lý (guardrail D-17 — firm là người kích hoạt + xác nhận rule pack, D-02 áp nguyên). Phân phối qua **đại lý thuế / law firm** (B2B2B DEC-011) — họ vừa là khách trả tiền, vừa là người cấu hình rule pack cho SME.

**Cấu trúc 2 gói (DEC-055):**
- **Ledger/"Sổ" tier (free):** nhập tay obligations/parties/metadata + full core loop (deadline reminder, D-02 confirm, D-07 edit, audit, consent) — an toàn không bao giờ paywall (D-16).
- **AI tier (paid, quota per-document không per-tenant):** vision extraction toàn văn + chat trích nguyên văn + cây điều khoản.

**Tên:** thương mại "**Servanda**" (từ *pacta sunt servanda*, R-7 resolved 2026-07-02). "Khế" giữ làm codename nội bộ.

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

## 5b. Chat Architecture Principle (DEC-031)

> **Khế giải multi-turn chat không phải bằng conversation memory —
> mà bằng structured data + UI architecture.**

### Tại sao đây là moat

Generic RAG chatbots buộc dùng prose conversation history (2–5K tokens/turn) vì không có gì ngoài text. Khế có structured extraction — `obligations`, `parties[]`, `terms`, `clauses` với ID — cho phép maintain semantic state (50 tokens JSON) và resolve reference bằng structured lookup, không phải LLM guessing.

Competitor sẽ copy "chatbot with memory" trong 6 tháng. Không ai copy được extraction pipeline + obligation graph trong thời gian ngắn.

### Model: Result-seeded Progressive State

Mỗi query result tự động seeds session state cho turn tiếp theo — "conversational computation":
- Turn 1: "HĐ đến hạn thanh toán tháng này?" → query → trả [Penfield, VILLA.CS, ABC] → state: `{active_doc_ids: [1,3,5], active_obligation_ids: [12,15,23]}`
- Turn 2: "tổng số tiền cần trả?" → SUM amount_raw trên active_obligation_ids → "67.604.940đ từ 3 HĐ"
- Turn 3: "HĐ nào nhiều nhất?" → rank trong active_doc_ids, không query lại toàn bộ

Tương đương Excel filter→SUM, shell pipe, SQL cursor — nhưng qua ngôn ngữ tự nhiên.

### 5 invariants bắt buộc

1. **State model:** `chat_sessions.state_json = {active_doc_ids[], active_obligation_ids[], working_set_label, last_tool_call}` per conversation thread. Không phải prose history.
2. **Visibility (mandatory):** Scope chip trong mỗi response bubble — `📌 Đang trong context: 3 HĐ tháng 7 ▾`. Tap để widen/reset/switch. Không có chip = silent wrong-scope = D-08 violation.
3. **Ambiguity guard:** Multi-doc result → ask-clarify, KHÔNG auto-narrow silent.
4. **Cold-start:** Turn 1 deictic khi state trống → ask-clarify ("Bạn muốn hỏi về HĐ nào?").
5. **Invalidation:** 30-min session timeout + explicit reset button + high-threshold intent-shift → ask trước khi switch.

### Không implement

- ❌ Full prose history (bất kỳ phase nào) — cost + hallucination risk không tương xứng
- ❌ Auto-widen on miss — D-08 spirit violation
- ❌ NLP pronoun detection layer — không cần với model này

---

## 5c. North Star: Obligation OS (DEC-056 — ratified Kevin 2026-07-03)

> **Servanda là hệ điều hành nghĩa vụ, không phải hệ điều hành hợp đồng.**
> Hợp đồng là **nguồn nghĩa vụ đầu tiên** — không phải là toàn bộ.

### 5c.1 Hai nguồn nghĩa vụ

- **Nguồn 1: Hợp đồng đã ký** — extraction pipeline (DEC-002 / DEC-026 / DEC-050) bóc obligations từ HĐ. Đây là core loop hiện tại.
- **Nguồn 2: Pháp luật** — thuế (GTGT, TNDN, TNCN, môn bài), BHXH, ngành dọc (PCCC, ATTP, môi trường, gia hạn giấy phép con). Nạp qua **rule pack curated** (§5c.3) + nhập tay.
- *(Nguồn 3 tương lai:* quy trình nội bộ / ISO — out of scope hiện tại.*)*

### 5c.2 Vì sao reframe: engine đã có hình dạng obligation, không phải contract

`recurrence` monthly/quarterly/yearly, deadline, penalty existence, event chain, fulfillment evidence, `source="user_manual"` đều đã build. "Nộp tờ khai GTGT quý" ánh xạ nguyên vẹn vào Obligation model. Câu bán "không bao giờ trượt deadline" vốn agnostic về nguồn nghĩa vụ.

Brand giãn tự nhiên: *pacta sunt servanda* (hợp đồng phải được tuân thủ) → *leges sunt servandae* (luật phải được tuân thủ).

### 5c.3 Kiến trúc nguồn nạp — rule pack curated

- **Đường chính:** thư viện **rule pack curated** theo hồ sơ doanh nghiệp (loại hình, có nhân viên không, kê khai GTGT tháng/quý, ngành nghề) + nhập tay (rail Ledger DEC-055).
- **KHÔNG dùng AI đọc văn bản luật** để sinh nghĩa vụ — lãnh địa tư vấn pháp lý, đụng D-01/D-08.
- **D-17 (new guardrail):** Servanda cung cấp template rule pack + engine nhắc; **firm (đại lý thuế/law firm) là người kích hoạt và xác nhận** lịch tuân thủ cho khách (D-02 áp nguyên). Servanda không bao giờ tự tư vấn nghĩa vụ pháp lý. Rule pack sai → firm bắt được ở bước xác nhận. Đây vừa là lá chắn trách nhiệm, vừa là product design.

### 5c.4 Luận điểm thị trường

- CEO hiện **phụ thuộc kế toán để nhớ** hạn thuế, phụ thuộc bộ phận sản phẩm để comply tiêu chuẩn kỹ thuật — single point of failure, CEO không có tầm nhìn riêng.
- Chi phí vi phạm **luật định, chắc chắn, đo được** (phạt chậm tờ khai hàng chục triệu, lãi chậm nộp theo ngày, BHXH vừa phạt vừa không chốt sổ) → ROI dễ bán hơn contract management thuần.
- TAM đảo chiều: không phải SME nào cũng nhiều HĐ, nhưng **mọi doanh nghiệp đều có nghĩa vụ thuế/BHXH**.
- **Điều chỉnh trung thực:** MISA / phần mềm kế toán có nhắc hạn thuế, eTax Mobile có notification. Khe hở thật: (a) **sổ cái nghĩa vụ HỢP NHẤT cho CEO** (HĐ + thuế + BHXH + giấy phép trong 1 chỗ — tool hiện có đều accountant-facing), (b) **portfolio view cho firm**, (c) **nghĩa vụ ngành dọc** — phân mảnh, chưa tool nào gom.

### 5c.5 Khớp chiến lược với DEC hiện hành

- **DEC-011 (B2B2B):** firm đã là khách trả tiền kiêm kênh — feature này biến chính công việc hằng ngày của kênh thành sản phẩm. Không đe dọa firm: giảm rủi ro nghề nghiệp của họ (khách trượt hạn = firm bị trách), giữ nguyên logic D-03 "đẻ việc" (reminder nổ → SME gọi firm xử lý → firm tính phí).
- **DEC-018 (wedge OPEN) — reframe:** wedge có thể không phải một *ngành* mà là một *loại nghĩa vụ* (compliance) cắt ngang mọi ngành. Đây là ứng viên trả lời cho câu hỏi wedge.
- **DEC-055 (Ledger/AI tier):** rule pack là structured data thuần, **không tốn AI call nào** → GM đẹp hơn extraction; "luật đổi → pack cập nhật" = lý do tự nhiên cho doanh thu định kỳ.

### 5c.6 Product gaps + sequencing

**Gap:**
1. `Obligation.document_id` NOT NULL hiện tại — nghĩa vụ tuân thủ không có tài liệu nguồn → nới schema hoặc container "hồ sơ tuân thủ". Small.
2. Rule engine lịch luật định ("ngày 20 tháng sau", "quý +30 ngày", dời ngày nghỉ lễ) — expander hiện chỉ monthly/quarterly đơn giản. Medium.
3. **Vận hành nội dung rule pack** — chi phí lớn nhất, VĨNH VIỄN (duy trì, cập nhật khi luật đổi, chịu trách nhiệm đúng sai). Mitigate bằng D-17 + firm-confirm.

**Sequencing:**
- **KHÔNG chen vào Sprint 2** (obligation tab + DS rollout đang chạy).
- Validate rẻ nhất: DEC-013 pilot có sẵn 1 đại lý thuế → làm **MỘT rule pack đầu tiên** (thuế + BHXH cơ bản theo loại hình DN) cùng chính firm đó. Firm không dùng → thesis chết sớm giá rẻ.
- Backlog kỹ thuật (schema + rule engine) file sau khi rule pack đầu được firm pilot xác nhận có giá trị.

---

## 5d. Tier structure: Ledger / AI (DEC-055 — ratified Kevin 2026-07-02)

### 5d.1 Ledger/"Sổ" (free)

- Nhập tay obligations, parties, metadata + full core loop.
- Deadline reminder, D-02 confirm, D-07 edit, audit log, consent flow — **an toàn KHÔNG paywall** (D-16).
- Mọi tool an toàn (reminder, xác nhận, sửa, audit) miễn phí vĩnh viễn.

### 5d.2 AI tier (paid)

- Vision extraction toàn văn hợp đồng (DEC-002 + DEC-026 + DEC-050 schema v3).
- Chat trích nguyên văn (DEC-031 v2 structured state).
- Cây điều khoản (DEC-050 R3 clause hierarchy + R10 cross-refs).
- **Quota per-document** (không per-tenant) — mỗi doc dùng LLM call là 1 unit.

### 5d.3 D-16 (new guardrail): No paywall on safety

Không bao giờ paywall các tool an toàn (reminder, D-02 confirm, D-07 edit, audit, consent). Chỉ monetize **trí tuệ (extraction, chat)** và **tiện lợi** (bulk operations, portfolio view). Đây là kill switch cho model — Servanda phải cứu SME khỏi trượt hạn, kể cả khi họ không trả tiền.

### 5d.4 Sequencing với DEC-016 paywall lever

DEC-055 định **hình dạng tier** nhưng CHƯA quyết **pricing** — DEC-016 vẫn open. Rule pack (§5c) sẽ nằm ở tier nào (free vs paid) = quyết định pricing sau, gắn DEC-016 + kết quả pilot.

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

- **v0.4 (2026-07-03, KHE_Docs):** Fold DEC-055 (Servanda brand + Ledger/AI tier structure + D-16 no-paywall-safety guardrail — R-7 resolved) + DEC-056 (Obligation OS North Star + compliance as source-2 + D-17 firm-confirms-compliance guardrail). §0 TL;DR rewritten. §5c NEW Obligation OS section (2 sources, engine shape, rule pack architecture, market thesis, gap+sequencing). §5d NEW Tier structure section (Ledger free / AI paid quota-per-doc + D-16). Numbering: D-11/D-12 proposed by PM conflict with existing → renumbered D-16/D-17 in canonical registry. Cascade ripples: BRD FR-* + CLAUDE.md D-rules + Glossary NEW terms folded downstream cycle 7.

- **v0.3 (2026-06-20, KHE_Docs):** Add §5b Chat Architecture Principle (DEC-031 v2 Result-seeded Progressive State). Anchor principle: multi-turn chat via structured data + UI, NOT conversation memory. Model + 5 invariants (state_json, visibility scope chip, ambiguity guard, cold-start, invalidation). Out-of-scope: prose history (any phase), auto-widen, NLP pronoun layer. Supersedes DEC-031 v1 (commit `1f6c5ad`) which was discarded. Ratified Kevin 2026-06-20 commit `dc307eb`.
- **v0.2 cycle-3 fold (2026-06-19, KHE_Docs):** Add §7.1 Billing roadmap (Phase 1 manual / Phase 2 automated). Quota guard policy ratified per Kevin: firm-configurable per SME, calendar-month reset, hard block 429. Folds DOCS_INBOX comment 22.
- **v0.2 canonical-adoption (2026-06-18, KHE_Docs):** Pulled từ PM draft branch `claude/pm-assistant` vào docs lane. File rename: `PRODUCT_STRATEGY_Khe.md` → `PRODUCT_STRATEGY_Khe_v0.2.md` (version-in-filename per docs convention). No content edits — chỉ update §0 status line. Folded DOCS_INBOX comments 13 + 14 (DEC-018 + PRODUCT_STRATEGY adoption).
- **v0.2 (2026-06-18, KHE_PM_Assistant):** Tái cấu trúc thành **tài liệu nền độc lập** (bỏ framing thảo luận). Thêm **§2 Personas · §3 Jobs to be Done · §4 Why-How-What (Golden Circle)** + mapping WHAT→JTBD. Mục GTM motion viết lại trung tính (kênh B2B vs self-serve). Khẳng định vai trò: nền → BRD → SRS.
- **v0.1 (2026-06-18, KHE_PM_Assistant):** Bản đầu — định vị April Dunford 5-component + Positioning Thesis; vertical chuyển OPEN (DEC-018); roadmap 3 giai đoạn + kill signals.
