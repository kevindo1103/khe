# KHE_PM_Assistant STATE — Khế MVP

*Branch: `claude/pm-assistant` | Last updated: 2026-06-20 | v2.0*

> **2026-06-18 (b):** Fold BRD v0.1 → **v0.2** trực tiếp (PM-direct, Kevin authorize exception). 13 thay đổi: Zalo→Telegram, B2B2B §2.4, vertical OPEN, 2-firm pilot, concierge, VisionExtractionProvider, consent gate, derive ngày hết hạn, kill signals §12.1, NFR-3 US-hosted reconcile. NĐ 337 date reconciled (01/01/2026 hiệu lực + 01/07/2026 nền tảng) khớp CLAUDE.md. DOCS_INBOX noted để KHE_Docs canonical-hóa, KHÔNG re-fold (tránh clobber).
> **2026-06-18 (a):** Tạo `docs/PRODUCT_STRATEGY_Khe.md` (v0.2, PM draft) — **tài liệu nền độc lập** (foundation → BRD → SRS). Gồm Personas + JTBD (J1-J5) + Why-How-What (Golden Circle) + định vị April Dunford 5-component + GTM motion (B2B channel vs self-serve contingency). Vertical OPEN (DEC-018). Routed DOCS_INBOX cho KHE_Docs canonical fold. *(Bối cảnh: review phân tích CLM-SME của cộng sự Kevin — giữ thesis Khế, self-serve playbook lưu làm contingency motion cho DEC-015 #2, pricing input cho DEC-016.)*

---

## ⚓ Product Anchor Principle (Kevin ratified 2026-06-20)

> **"Khế giải multi-turn chat không phải bằng conversation memory —**
> **mà bằng structured data + UI architecture."**

Đây là **anchor quyết định mọi decision thiết kế chat**, từ API shape đến UX đến cost model.

### Tại sao đây là moat, không chỉ là trade-off

Generic RAG chatbots buộc phải dùng prose conversation history (Option C) vì chúng không có gì ngoài text. Khế có structured extraction — `obligations`, `terms`, `parties[]`, `clauses`, obligation graph — những thứ không AI chatbot nào tự có mà không có extraction pipeline. Điều đó cho phép Khế maintain **semantic state** (50 tokens JSON) thay vì **prose history** (2,000–5,000 tokens), và resolve reference bằng **structured lookup** thay vì LLM guessing.

### 4 nguyên tắc triển khai từ anchor này

| Nguyên tắc | Implication |
|---|---|
| **Context từ navigation, không từ NLP** | Chat sidebar trong DocumentDetail/Obligation view inherit context từ URL — zero LLM cost, zero hallucination |
| **Structured semantic state, không prose history** | Mỗi turn server maintain `{active_doc_id, active_obligation_id, mentioned_parties[], last_intent}` — compact, cacheable, deterministic |
| **Domain resolvers trước LLM** | "Bên A/B/thuê/cho thuê" → `parties[]` lookup deterministic. "Nghĩa vụ này" → `obligation_id` từ navigation. Không cần pronoun detection NLP |
| **Narrow-first search, widen on miss** | Khi không có explicit doc reference, search last-mentioned doc trước → widen nếu miss → surface assumption rõ ràng ("Tìm trong HĐ Penfield — không thấy → mở rộng ra tất cả HĐ") |

### Failure mode cần tránh

Nếu "này/đó/kia" resolve sai mà không báo → **im lặng sai** trong domain pháp lý = nguy hiểm hơn stateless (D-08 spirit). Mọi context carry-over phải **visible + correctable** (chip hiển thị doc đang scope, 1-tap để widen/switch).

### Phase roadmap từ anchor

- **MVP (now):** UI-contextual sidebar + `prev_doc_id` narrow-first + domain resolver parties[] + visible scope chip
- **Phase 2:** Entity-level state (mentioned_dates, amounts) + persistent thread per doc/obligation (cross-session memory)
- **Phase 3:** Obligation graph queries ("tất cả nghĩa vụ liên quan đến Penfield qua các HĐ") — genuine moat vs bất kỳ AI chatbot nào

*DEC-031 — xem bảng Ratified Decisions bên dưới. KHE_Docs: fold vào PRODUCT_STRATEGY §Chat Architecture + BRD §FR-CQ.*

---

## Active Sprint Context

**Current phase:** **Sprint 0 COMPLETE (2026-06-11)** — see nghiệm thu issue #23. Ready Sprint 1 kickoff.
**Sprint 0 goal (ĐÃ ĐẠT):** FastAPI + multi-tenant DB scaffold, CI/CD, Telegram bot, Vision extraction interface + 3 providers. Architecture/contract baseline ratified.
**Sprint 1 prep:** Spawn KHE_Docs (fold 11 DOCS_INBOX entries) + KHE_Frontend_Admin/PWA/QC/Compliance. Carry-over: #10 per-tenant Alembic, #22 NĐ 13 consent gate.

---

## Strategy v2 (2026-06-10 — user relay từ Claude.ai session)

> **Core:** Đừng bán "phần mềm quản lý hợp đồng" cho SME. Trở thành "Hệ điều hành nghĩa vụ"
> mà cố vấn ngoài (đại lý thuế / law firm) vận hành trên khách của họ —
> **firm trả tiền trước, SME free** — rồi lật sang SME-pays khi mở tầng soạn/review.

**3 điểm gãy được giải:**
1. WTP — SME không trả cho "nhắc hạn" → B2B2B: firm trả theo đầu client (~50-100k/client/năm)
2. Activation (M-1 60% upload là giả định rủi ro nhất, không phải extraction) → **concierge onboarding** 20 SME đầu: số hóa cả ngăn kéo trong 1 ngày
3. Kênh firm chưa proven → pilot **2 firm song song** (1 đại lý thuế + 1 law firm), mỗi firm 10 SME, đo 90 ngày

**Timing positioning:** NĐ 337 hiệu lực 01/01/2026; nền tảng quốc gia vận hành chậm nhất 01/07/2026 — KHÔNG cạnh tranh tầng ký,
positioning **"ngôi nhà cho mọi hợp đồng sau khi ký"** đón hậu sóng.

**3 giai đoạn:**
| GĐ | Thời gian | Bán gì | Moat |
|---|---|---|---|
| 1. Troy + Concierge | Q3-Q4/2026 | Firm-pays per client; SME free; concierge 20 SME | Kho nghĩa vụ + extraction VN tuned |
| 2. Soạn/Review lawyer-in-loop | 2027 | SME-pays drafting từ template firm duyệt; firm revenue share | Template library + firm network |
| 3. Obligation graph hạ tầng | 2027+ | Nghĩa vụ thanh toán ↔ công nợ, hóa đơn ĐT/ngân hàng, benchmark | Graph xuyên nghìn SME |

**Kill / pivot signals (falsifiable):**
- Retention tuần 4 < 30% sau concierge → pivot wedge sang DMS cho firm nhỏ
- Firm không trả nhưng SME convert tốt qua reminder paywall → bỏ B2B2B, direct freemium
- Cả 2 firm không đẩy nổi 10 SME trong 90 ngày → kênh sai → thử hiệp hội ngành / cộng đồng F&B

---

## Ratified Decisions

| ID | Decision | Status | Date |
|---|---|---|---|
| DEC-001 | Stack: FastAPI + SQLite multi-tenant per BRD A-1 | Draft | 2026-06-09 |
| DEC-002 | `VisionExtractionProvider` — Gemini 2.0 Flash primary (~150đ/doc) + Claude Haiku fallback (~300đ/doc if accuracy <90%). Sprint 0 benchmark on 15 PII-scrubbed Bingxue HĐ samples. | **Ratified** | 2026-06-09 |
| DEC-003 | Hosting provider + data residency | Draft | 2026-06-09 |
| DEC-004 | Naming "Khế" finalization (R-7) | Draft | 2026-06-09 |
| DEC-005 | Sprint cadence | Draft | 2026-06-09 |
| DEC-006 | Telegram bot replaces Zalo ZNS | **Ratified** | 2026-06-09 |
| DEC-007 | Sprint 0 infra parallel with M0 | **Ratified** | 2026-06-09 |
| DEC-008 | KHE_Backend first session to spawn | **Ratified** | 2026-06-09 |
| DEC-009 | Session prefix ERP_ → KHE_ | **Ratified** | 2026-06-09 |
| DEC-010 | NĐ 13/2023 Phase 1: US-hosted LLM OK with explicit consent + audit log | **Ratified** | 2026-06-09 |
| DEC-011 | **B2B2B model:** firm là khách hàng trả tiền (per-client ~50-100k/năm), SME free Phase 1. SME-pays mở ở GĐ2 (drafting/review). | **Ratified** (user relay) | 2026-06-10 |
| DEC-012 | **Concierge onboarding:** 20 SME đầu KHÔNG bắt tự upload — số hóa tận nơi/firm thu hộ. M-1 (60%) đo SAU concierge baseline. | **Ratified** (user relay) | 2026-06-10 |
| DEC-013 | **2-firm pilot:** 1 đại lý thuế + 1 law firm song song, mỗi firm 10 SME, đánh giá 90 ngày. Thay mục tiêu "1 firm LOI". | **Ratified** (user relay) | 2026-06-10 |
| DEC-014 | **Positioning:** "Ngôi nhà cho mọi hợp đồng sau khi ký" — đón hậu sóng NĐ 337 (hiệu lực 01/01/2026, nền tảng quốc gia 01/07/2026), KHÔNG cạnh tranh tầng ký số. | **Ratified** (user relay) | 2026-06-10 |
| DEC-015 | **Kill/pivot signals** ghi vào BRD: retention W4 <30% post-concierge → DMS pivot; firm không trả + SME convert → direct freemium; 2 firm không đủ 10 SME/90d → đổi kênh. | **Ratified** (user relay) | 2026-06-10 |
| DEC-016 | **Reminder paywall lever:** Strategy gốc đề xuất ZNS paywall (email free / Zalo paid) — NHƯNG DEC-006 Telegram giữ nguyên per user 2026-06-10. Freemium value metric cần lever khác hoặc re-evaluate Zalo paid channel GĐ2. | **Open — cần Kevin quyết** | 2026-06-10 |
| DEC-017 | **Design-first Sprint 1:** Design System đồng nhất + M0 mockups (#24) phải approve TRƯỚC khi Frontend_Admin (#30) + PWA_Chat (#31) code. Tránh revamp UI. KHE_Designer gating. | **Ratified** | 2026-06-11 |
| DEC-018 | **Vertical = OPEN:** KHÔNG khóa focus F&B/bán lẻ. Lõi general; chọn wedge theo tín hiệu pilot (lượng HĐ đủ đau + kênh firm sẵn + HĐ có nghĩa vụ ngày tháng). Điều chỉnh D-05/BRD/CLAUDE.md wording "sắc trong seed" → "sắc theo wedge chọn bởi pilot". | **Ratified** (Kevin 2026-06-18) | 2026-06-18 |
| DEC-019 | **Document relationship model = EDGE table** (`document_relationships`, n-n), KHÔNG dùng `parent_doc_id`. MVP scope 2 quan hệ: `amends` (last-writer-wins theo seq_order) + `references_framework` (HĐ khung → call-off: inherit + selective override). Defer `supersedes`/`renews`/`related`. AI **suggest** quan hệ → SME **confirm** (D-02). Khế **KHÔNG phán tính hợp lệ pháp lý** — chỉ surface facts (chữ ký, replacement_language), SME/luật sư quyết. Theo CLM industry pattern (Ironclad/Icertis/SAP Ariba). Ref: BA_contract_processing_logic v0.3. | **Ratified** (Kevin 2026-06-18) | 2026-06-18 |
| DEC-020 | **Q-1 thời hạn phi-số:** HĐ "vô thời hạn"/"đến khi thanh lý" → KHÔNG tạo deadline alert giả. Flag rõ "vô thời hạn" cho SME + 1 nhắc review/năm (tùy chọn). Vẫn track nghĩa vụ định kỳ khác (thanh toán) nếu có. Tinh thần D-08: không bịa deadline. | **Ratified** (Kevin 2026-06-18) | 2026-06-18 |
| DEC-021 | **Q-2 orphan amendment:** SME upload phụ lục/amendment khi chưa có HĐ gốc → KHÔNG block. Lưu với relationship pending, flag "chưa tìm thấy HĐ gốc", cho link sau (concierge/SME). Hợp DEC-012 (bỏ ma sát upload). | **Ratified** (Kevin 2026-06-18) | 2026-06-18 |
| DEC-022 | **Q-3 conflict UI = timeline đầy đủ:** Hiển thị lịch sử thay đổi từng field (HĐ gốc → PL01 → PL02), KHÔNG chỉ final value + badge. Phục vụ audit + firm/luật sư. Tăng scope UI Sprint 2 (KHE_Designer #24 + Frontend_Admin #30). | **Ratified** (Kevin 2026-06-18) | 2026-06-18 |
| DEC-023 | **Quota guard in MVP scope** (issue #63): Soft doc quota per tenant/month để prevent vision extraction cost runaway. `effective_quota = firm_tenant_access.custom_quota ?? tenants.doc_quota` (default 500). Calendar month reset (cron ngày 1). Hard 429 khi exceeded. Atomic UPDATE (no read-then-write TOCTOU). Bulk upload: per-file accept/reject, không fail cả batch. No quota refund on extraction failure (slot = upload accepted). D-11 mới: quota check bắt buộc trước ingest. | **Ratified** (Kevin 2026-06-19) | 2026-06-19 |
| DEC-024 | **Firm portal descoped từ #63 → #65.** Quota guard (ingest side) = issue #63. Firm portal endpoint = issue #65 (dep #63). Sequencing: PR-A (#26 obligation derive) → PR-B (#62 audit trail) → #63 (quota guard) → #65 (firm portal). | **Ratified** (Kevin 2026-06-19) | 2026-06-19 |
| DEC-025 | **Frontend = 2 standalone Vite apps.** `frontend/` = Admin SPA (base `/admin/`). `frontend/pwa/` = PWA Chat (base `/`). Nginx: `/` → PWA 5174, `/admin` → Admin 5173. Admin needs `base: '/admin/'` in `vite.config.ts` before nginx switch. Issue #86 tracks Infra nginx switch. | **Ratified** (Kevin 2026-06-19) | 2026-06-19 |
| DEC-026 | **LLM function-calling cho chat query.** `chat_query.py` refactor: Gemini Flash nhận query → call 3 tools (`search_terms`, `search_obligations`, `search_clauses`) → format answer từ kết quả. D-08 là hard fallback bất biến khi tất cả tools empty (~5đ/query). Thêm `clauses` table per-tenant (doc_id, clause_num, title, content) — populated từ vision extraction cùng 1 call. 7 canonical fields giữ nguyên. Unicode regex fix cho `_extract_doc_hint`. | **Ratified** (Kevin 2026-06-19) | 2026-06-19 |
| DEC-027 | **Generalized typed obligation extraction.** `obligation_type` controlled enum 8 loại: `payment` · `delivery` · `handover` · `expiration` · `renewal` · `review` · `warranty` · `other`. Extraction đổi `payment_schedule[]` → typed `obligation_schedule[]`; LLM tự suy type từ context + vai trò bên, KHÔNG hardcode contract-type→obligation-type (giữ lõi general DEC-018). Single vision call (DEC-026), đọc luôn clause text, không thêm cost. `other` = catch-all giữ description, không ép loại (D-06). Issues #116 (query side) + #117 (data side) giữ tách. | **Ratified** (Kevin 2026-06-19) | 2026-06-19 |
| DEC-028 | **Chat query learning loop.** Log question/tool_calls/found → PM/QC weekly review → fold misroute vào catalog #118 → update few-shot + QC test. Phase 2: auto few-shot retrieval (RAG). **NĐ 13: tạm bypass (assume consent) cho staging/pilot-dev — COMPLIANCE DEBT, phải đóng trước prod** (#119, KHE_Compliance track). Cross-tenant leak guard: few-shot trong shared prompt phải synthetic/scrubbed. | **Ratified** (Kevin 2026-06-19) | 2026-06-19 |
| DEC-029 | **doc_type_group taxonomy + full field schema.** Nguồn: lawyer Danh mục HĐ 126 loại → collapse 10 groups: `dan_su` · `thuong_mai` · `lao_dong` · `bat_dong_san` · `van_tai_logistics` · `xay_dung` · `cong_nghe_ip` · `tai_chinh` · `bao_dam` · `hanh_chinh` · `other`. 5 universal fields thêm vào CANONICAL_FIELDS: `doc_type_group` (required, classified first) · `ngay_ky` · `tien_dat_coc` · `thoi_han_bao_hanh` · `thoi_han_thong_bao`. 9 type-specific field sets (~30 fields): lao_dong (3) · bat_dong_san (3) · xay_dung (3) · bao_dam (3) · cong_nghe_ip (3) · thuong_mai (4) · van_tai_logistics (3) · tai_chinh (3) · hanh_chinh (2). Extraction strategy: classify doc_type_group FIRST → extract universal + type-specific conditional trong 1 vision call. Chat: thêm `doc_type_filter` param vào search_terms + search_obligations (exact match, not ILIKE). Issues: #123 (KHE_AI schema) + #124 (Backend chat filter, dep #123). ALL IN CURRENT PHASE (user ratified 2026-06-20). | **Ratified** (Kevin 2026-06-20) | 2026-06-20 |

| DEC-030 | **4-axis Obligation model — REVISED (Kevin 2026-06-20 merge Phase 2 into MVP: PMF core).** Obligation = điểm trong không gian 4 trục độc lập: **(A) obligation_type** (category DEC-027) · **(B) direction + obligor** (góc SME) · **(C) recurrence** (cadence, renamed) · **(D) series metadata** (milestone_series_id / milestone_index / milestone_total / milestone_trigger). **Temporal taxonomy 4 pattern — tất cả MVP:** T1 once · T2 lặp đều (auto-expand engine) · T3 nhiều đợt hữu hạn (series grouping) · T4 vô thời hạn. **Event-chaining (MVP):** `trigger_obligation_id` FK self-ref + `trigger_delay_days` + `trigger_condition` — khi parent done → engine tính due_date con + notify. **Status enum mở rộng:** `pending · in_progress · partial · done · cancelled · waiting_trigger`. **amount_raw + amount_total_raw** lưu string (% hay tuyệt đối, không arithmetic MVP). **Direction:** `nghĩa_vụ / quyền_lợi / null` từ obligor match. **#122 RESOLVED** via Option B. **Extraction generalize:** `payment_schedule[]` → `obligation_schedule[]` (tất cả category). **KHE_AI thêm:** `trigger_condition`, `trigger_delay_days`, `series_id`, `milestone_index/total`, `trigger=date\|event`. **Backend:** migration tenant_005 (+8 cols) + event-chaining service + T2 auto-expand scheduler. **Frontend:** T3 progress chip "Đợt N/total", T3-event "Chờ: X", partial badge, dependency chain view. **Phase 3 còn lại:** cross-doc graph · bank/accounting integration · % parse → VND. D-06 ✅ D-02 ✅ D-08 ✅ D-01 ✅. Issues: #144 (KHE_AI revised) · #145 (Backend revised) · #146 (Frontend revised). | **Ratified** (Kevin 2026-06-20, Phase 2 → MVP) | 2026-06-20 |

| DEC-031 | **Chat context = Result-seeded Progressive State (v2). Anchor: Khế giải multi-turn chat bằng structured data, KHÔNG phải conversation memory.** Model: mỗi query result tự động seeds `chat_sessions.state_json` cho turn tiếp theo — "conversational computation" (Excel filter→SUM; shell pipe; SQL cursor). Generic chatbot không có structured data → buộc dùng prose history (5K tok). Khế có obligations/parties/amounts với ID → maintain 50-token JSON state. **5 invariants (tất cả mandatory):** (1) **State model** — server maintain `chat_sessions.state_json = {active_doc_ids[], active_obligation_ids[], working_set_label, last_tool_call}` per conversation thread, KHÔNG phải prose; (2) **Visibility invariant (mandatory — không drop)** — scope chip hiển thị trong mỗi response bubble "📌 Đang trong context: HĐ Penfield ▾"; tap để widen/reset/switch. Excel/Shell work vì operator explicit — chat không có → chip là operator; (3) **Ambiguity guard** — multi-doc results → ask-clarify KHÔNG auto-narrow silent ("Ý bạn là HĐ nào trong 3 HĐ vừa tìm?"); (4) **Cold-start** — turn 1 deictic ("HĐ này?" khi chưa có context) → ask-clarify ("Bạn muốn hỏi về HĐ nào? [list]"); (5) **Invalidation** — time decay 30-min session timeout + explicit "🔄 Hỏi mới" button + intent-shift detection high threshold → ask trước khi switch. **Spec debt (file cùng engineering task):** result content schema chi tiết; alias resolution rules parties[]; NĐ 13 audit log cho state_json (pointer tới PII data → compliance debt tương tự DEC-028, KHE_Compliance track). **Frontend impact:** scope chip + reset button = mandatory change (không phải zero-frontend). **Engineering hold:** assign sau khi #155 (parties[]) + #156 (type sync) ship. Ref: #178 (KHE_QC BA × 3 rounds). | **Ratified v2** (Kevin 2026-06-20) | 2026-06-20 |

**Giữ nguyên (user confirm 2026-06-10):** DEC-002 (VisionExtractionProvider Gemini+Claude), DEC-006 (Telegram), DEC-010 (NĐ 13 Phase 1).

---

## Sprint 1 Plan (ratified 2026-06-11) — M0 vertical slice + concierge foundation

**Goal:** End-to-end 1 lease contract: upload → vision extract → obligation (derived) → Telegram reminder → chat query. NĐ 13 consent gate live. Per-tenant Alembic. ~2 tuần.

**Design-first (DEC-017):** Designer làm Design System + mockups TRƯỚC, Frontend/PWA build sau.

### Issues created

| Issue | Team | Status | Blocker |
|---|---|---|---|
| #24 | KHE_Designer | planned | — (GATING cho #30/#31) |
| #25 | KHE_Backend | planned | dep #22 consent |
| #26 | KHE_Backend | planned | dep #25 |
| #27 | KHE_Backend | planned | dep #26 |
| #22 | KHE_Backend | planned (Sprint 0 carry) | CRITICAL — trước first extraction |
| #10 | KHE_Backend | planned (Sprint 0 carry) | HIGH |
| #28 | KHE_AI | planned | blocker:human — 15 samples từ Kevin |
| #29 | KHE_Infra | planned | dep #10, domain confirm |
| #30 | KHE_Frontend_Admin | ⛔ blocked | #24 design |
| #31 | KHE_PWA_Chat | ⛔ blocked | #24 design |
| #32 | KHE_Compliance | planned | feeds #22/#31 |
| #33 | KHE_QC | planned | dep backend modules |

### Spawn order Sprint 1
1. **KHE_Docs** (urgent — fold 11 DOCS_INBOX) — đang chạy
2. **KHE_Designer** (#24 — gating, spawn ngay để unblock Frontend sớm)
3. **KHE_Backend** (continue — #22, #10, #25-27 critical path)
4. **KHE_Compliance** (#32 — consent spec feeds Backend + PWA)
5. **KHE_AI** (#28 — chờ samples Kevin)
6. **KHE_Infra** (#29)
7. **KHE_Frontend_Admin** / **KHE_PWA_Chat** — sau khi #24 approve
8. **KHE_QC** (#33 — backend pytest tuần 1, E2E tuần 2)

### Critical dependencies
- #22 consent gate → blocks first production extraction (Backend ← Compliance spec #32)
- #24 design → blocks #30 + #31 (Kevin approve gate)
- Backend ingest/obligation API shape → Frontend/PWA (coordinate DOCS_INBOX)
- #10 per-tenant Alembic → Infra deploy wire #29

### Kevin action items Sprint 1
- [ ] Approve Design System + mockups (#24) khi Designer submit
- [ ] Cung cấp 15 PII-scrubbed F&B/bán lẻ HĐ samples (#28)
- [ ] Confirm domain `khe.vn` / `staging.khe.vn` (#29)
- [ ] DEC-016 freemium lever decision
- [ ] Policy `thoi_han_hd` phi-số: skip / flag-for-human / recurring (#26)

---

## Day-1 Blockers

| Blocker | Risk | Action | Owner |
|---|---|---|---|
| **2 firm pilots** (DEC-013) | Cần 1 đại lý thuế + 1 law firm ký pilot trước Sprint 1 ship | Identify + contact + pitch 1-trang | User (Kevin) |
| NĐ 13/2023 obligation verification | Compliance baseline chưa verify chi tiết | Xác minh nghĩa vụ tuần này (user action per strategy) | User (Kevin) + KHE_Compliance |
| Hosting + data residency | VPS provider decision | Confirm provider + region | Sprint 0 |
| Naming finalization | R-7 trademark risk | Trademark check | Pre-launch |
| DEC-016 reminder paywall lever | Freemium value metric chưa chốt (Telegram giữ, ZNS bỏ) | Kevin quyết | User (Kevin) |

---

## Session Topology Status

| # | Session | Status |
|---|---|---|
| 1 | KHE_Docs | Branch created ✅ — **NEEDS spawn Sprint 1** (11 DOCS_INBOX pending fold) |
| 2 | KHE_PM_Assistant | Active ✅ |
| 3 | KHE_Backend | Sprint 0 ✅ DONE (#2 closed, PR #19 merged `cf6d022`). Sprint 1 backlog: #10 (per-tenant alembic), #22 (NĐ 13 consent gate) |
| 4-5 | KHE_Frontend_Admin / PWA_Chat | **NEEDS spawn Sprint 1** (M0 vertical slice) |
| 6 | KHE_QC | **NEEDS spawn Sprint 1** (E2E smoke) |
| 7 | KHE_Designer | Not spawned |
| 8 | KHE_Infra | Sprint 0 ✅ DONE (PRs #7, #8, #13, #18, #21 merged). VPS pattern + 8 secrets live |
| 9 | KHE_AI | Sprint 0 ✅ DONE (#3 closed, PR #17 merged). Pending: 15 PII-scrubbed samples từ Kevin |
| 10 | KHE_Compliance | **NEEDS spawn Sprint 1** (consent UX for #22) |

---

## Bootstrap Checklist (2026-06-09)

- [x] CLAUDE.md at root
- [x] MVP_BRD_Khe.md at root (KHE_Docs to move to docs/)
- [x] DOCS_INBOX [#1](https://github.com/kevindo1103/khe/issues/1)
- [x] `claude/edit-git-docs-Khe01` branch
- [x] `docs/spawn/SPAWN_KHE_*.md` (all 10 sessions)
- [x] DEC-002, DEC-006, DEC-007, DEC-008, DEC-009, DEC-010 ratified
- [x] KHE_Backend [#2](https://github.com/kevindo1103/khe/issues/2) + KHE_AI [#3](https://github.com/kevindo1103/khe/issues/3)
- [x] PROJECT_PLAN v0.1 draft in DOCS_INBOX
- [x] KHE_Backend + KHE_AI + KHE_Infra sessions spawned + Sprint 0 delivered
- [x] **Sprint 0 nghiệm thu — issue [#23](https://github.com/kevindo1103/khe/issues/23) (2026-06-11)**
- [ ] GitHub labels created (Settings → Labels) — vẫn pending Kevin
- [ ] KHE_Docs spawned — Sprint 1 priority (fold 11 DOCS_INBOX entries)
- [ ] Sprint 1 kickoff: Frontend/PWA/QC/Compliance spawn

---

## Sprint 0 Nghiệm thu Summary (2026-06-11)

**All 10 exit criteria PASS** — full table in issue [#23](https://github.com/kevindo1103/khe/issues/23).

**Architecture baseline ratified:**
- master.db (4 bảng) + per-tenant (7 bảng skeleton)
- API: `POST /auth/login` body `{tenant_id, username, password}` → JWT
- VisionExtractionProvider Protocol + 3 providers (Gemini 2.5 Flash primary)
- Deploy flow: `feature → staging → main`, 8/8 secrets live
- D-rules enforced ở extraction (D-01/06/08); D-10 enforced ở `get_db()` env-gate

**Sprint 1 carry-over:**
- 🔴 #22 NĐ 13/2023 consent gate (CRITICAL trước first production extraction)
- 🔴 #10 per-tenant Alembic migration chain
- 🟡 DEC-016 freemium paywall lever (Kevin quyết)
- 🟡 Domain `khe.vn`/`staging.khe.vn` confirm + VPS systemd unit deploy
- 🟡 15 PII-scrubbed F&B/bán lẻ HĐ samples từ Kevin cho full vision benchmark

**Sprint 0 PRs merged:** #6, #7, #8, #12, #13, #14, #16, #17, #18, #19, #21
**Docs PRs merged:** #35 (KHE_Docs cycle 1+2 — full doc suite v0.1→v0.4 vào main, 2026-06-18)
**Issues closed:** #2, #3, #5, #9, #11, #15, #20
**Open Sprint 1:** #10, #22, #1 (DOCS_INBOX long-lived), #23 (nghiệm thu reference)

**Post-#35 status (2026-06-18):**
- main canonical: PRODUCT_STRATEGY v0.2 · BRD v0.3 · SRS v0.1 · Glossary v0.2 · PROJECT_PLAN v0.2 · CLAUDE.md v0.4
- pm-assistant synced với main (merged, CLAUDE.md/BRD lấy bản canonical, xóa draft PRODUCT_STRATEGY_Khe.md trùng)
- **Chờ KHE_Docs cycle 3:** fold BA_contract_processing_logic v0.4 (DEC-019..022) vào BRD §3.3 + §7.3/7.4 (FR-DR/FR-OB) + SRS schema + Glossary. DOCS_INBOX có đủ instruction.
- BA doc chỉ sống ở branch `claude/pm-assistant` (chưa lên main); KHE_Docs `git fetch origin claude/pm-assistant` để đọc khi fold.

---

## INC Log / FM Log

*No incidents or failure modes yet.*

---

## 🎯 M0 Core Loop Milestone — 2026-06-19

**Confirmed live on staging** by Kevin + Backend lead (manual end-to-end verification):

| Layer | Result | Notes |
|---|---|---|
| Auth (HttpOnly cookie) | ✅ | `POST /auth/login` + `GET /auth/me` working |
| Ingest | ✅ | `status: processing → extracted` |
| Real Gemini extraction | ✅ | 7 canonical fields, `doc_type=hd_nha_cung_cap` correct |
| D-08 under real data | ✅ | `ngay_het_han=null + needs_review=true` — no fabrication |
| **Obligation derivation** | ✅ | **`obligation_count=1` — FR-OB-01 fired** |

**Remaining #75 UAT (open):** §B bulk, §D term edit, §F chat, §G D-10 (needs `uat-demo-b`), §H consent gate (needs `uat-demo-noconsent`), §I reminders, §J audit trail.

**PRs open post-M0:** #102 (PWA clause_num chip — dep #99 extraction wiring). **Bugs open:** none critical post-#78 (#70 nginx trailing-slash fixed on both staging+prod).

---

## DEC-026 Implementation Status (2026-06-19)

| Track | Issue | PR | Status | Notes |
|---|---|---|---|---|
| KHE_Backend (clauses + LLM chat) | #99 | #104 | `status:done-staging` (partial) | PR #104 merged `2cd5a3e`. **Carry-over:** `extraction_runner.py` clause insert wiring (open) |
| KHE_AI (ClauseItem schema) | #101 | #103 | ✅ **Closed** (merged `ff4fb0b`) | `ClauseItem` importable from `backend.modules.extraction` |
| KHE_Docs (BRD/SRS fold) | #100 | — | In progress | Gates full merge of #99 to main |
| PWA Frontend (clause_num chip) | relay sent | #102 | Open — awaiting #99 wiring | Backward compat, merge after extraction_runner wiring |

### Open carry-overs for #99

1. **`extraction_runner.py` clause insert** — Backend (Windsurf) now unblocked (PR #103 merged). Attribute access: `c.num`, `c.title`, `c.content`. `page_num=None`.
2. **`clause_count` on `GET /api/documents/` list endpoint** — PM APPROVED (2026-06-19). Use grouped aggregate query (not N+1). Add `clause_count: int = 0` to `DocumentListItem`.
3. **5 stuck docs re-trigger** — after clause wiring lands on staging.
4. **PR #102 merge** — after extraction_runner wiring PR merges to staging.
5. **Issue #105** (Compliance — PII→Gemini purpose/consent logging) — BLOCKING for prod, not staging.
6. **`provider` column on `Document`** — tracks Gemini vs Claude fallback (clause-gap handling). Pending Backend spec.

### Architectural notes locked
- Claude fallback always returns `clauses=[]` (grammar-compiler timeout on `list[ClauseItem]` — deterministic). `clauses=[]` is valid, not error.
- `_select_tools()` + `_format_answer()` all exception paths → D-08, never 500. `_format_answer_deterministic()` fallback exists.
- `temperature=0.0` on both Gemini LLM calls (extraction + chat formatting).

---

## Quota Guard Triage Log (2026-06-19)

**Issue #63** — triage by Backend lead trước khi assign Windsurf. Kết quả:

| Item | Decision |
|---|---|
| Firm portal endpoint | Descoped → #65 (separate task, dep #63) |
| Path drift | `POST /documents/upload` → thực tế `POST /ingest/upload` — Windsurf phải verify pre-PR |
| Sequencing | PR-A (#26) → PR-B (#62) → #63 → #65 |
| TOCTOU | Atomic UPDATE `WHERE docs_used_month < doc_quota`, rowcount==1 gate |
| Bulk near-quota | Per-file accept/reject array, không fail batch |
| Quota refund on failure | No refund — slot = upload accepted |
| DEC-016 freemium | `doc_quota` sẽ là freemium lever Phase 2 (flag only, không block MVP) |

**Status #63:** `blocker:waiting-dependency` (chờ PR-A merge)

---

## Weekly Review Log

*No reviews yet.*
