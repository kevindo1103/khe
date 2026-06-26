# KHE_PM_Assistant STATE — Khế MVP

*Branch: `claude/pm-assistant` | Last updated: 2026-06-26 | v3.5*

> **2026-06-26 (b):** Kevin approved **"Nội dung hợp đồng" tab** on doc-detail page. Posted: #281 addendum spec ([comment](https://github.com/kevindo1103/khe/issues/281#issuecomment-4810615167)) + **#284** new Backend issue (`GET /documents/{id}/clauses`). Doc-detail IA = 3 tabs: Tổng quan / Nghĩa vụ & Quyền lợi / Nội dung hợp đồng. Clause↔obligation cross-nav = fast-follow (no `source_clause_num` on Obligation today, verified staging `05f20bd`).

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

## ⚓⚓ CORE REPOSITIONING (Kevin 2026-06-25) — Khế = Obligation Management Platform

> **"Khế là nền tảng đảm bảo MỌI nghĩa vụ + quyền lợi pháp lý của một tổ chức được quản trị + thực hiện — khi đã được văn bản hóa qua tài liệu pháp lý. Chat + nhắc việc chỉ là PHÁI SINH của chức năng phân tích hợp đồng (CORE)."**

**Không phải pivot — là SHARPEN của cái đã có** (Obligation = "MVP heart" BRD §6 / DEC-027/030). QC review (Kevin endorsed 2026-06-25) xác nhận: reframe này *focus hơn*, không scatter. Kỷ luật ưu tiên:
- Đầu tư dồn vào **extraction completeness + obligation model depth**
- Chat chỉ cần "đủ tin, không bịa" (D-08) — không fancy
- Reminder chỉ cần "surface đúng cái đã phân tích"

**Tài liệu pháp lý** = bất kỳ văn bản tạo ràng buộc pháp lý (HĐ, MoU, thỏa thuận, quyết định tòa án, quyết định bên sở hữu...). **MVP = CHỈ HĐ trước**, mở rộng qua document type (Kevin confirm).

**Nghĩa vụ + Quyền lợi = cùng obligation model, khác CHIỀU** (direction axis DEC-030 — không phải 2 concept). Cả tài chính (thanh toán, phạt, cọc, bảo lãnh) + phi tài chính (bảo mật, độc quyền, không cạnh tranh, báo cáo định kỳ, tuân thủ, bảo hành).

### Hệ quả ưu tiên (re-prioritize — KHÔNG hủy việc đang chạy)
- **extraction depth > chat polish**
- #268 (chat trace) redefine: không phải "chat hay hơn" mà "**chứng minh Khế không bỏ sót cái nó đã phân tích**" — proof of the core promise
- #259/#251 (journey/confirm) = nền D-02, càng critical (mọi obligation phải human-verify)
- **HOLD start feature mới.** Firm portal #65/#237 vẫn pre-pilot (DEC-042) nhưng XẾP SAU core BA. Việc đang chạy dở (#268/#251/#259) tiếp tục, không hủy.

### 3 gap — VERIFIED vs shipped staging code (fold vào #272)
1. **🔴 Standing/continuous obligations KHÔNG managed (gap lớn nhất).** Verified: `extraction_runner` chỉ tạo obligation từ `obligation_schedule[]` (= "nghĩa vụ CÓ LỊCH/ĐỢT") + 1 `expiration`. Nghĩa vụ liên tục phi-lịch (bảo mật/không cạnh tranh/độc quyền/báo cáo/tuân thủ) → chỉ thành Term field, KHÔNG thành managed obligation. Đây chính là "tool nhắc hạn ≠ nền tảng đảm bảo MỌI nghĩa vụ". → mở enum + temporal T5 standing + StandingObligationDeriver.
2. **🟠 Rights chưa first-class.** Verified: `reminders.py` KHÔNG filter direction → quyền lợi CÓ due_date *được* nhắc ✅, nhưng dùng `ob.description` thô (không phân biệt "bạn trả" vs "đối tác trả cho bạn"), không có rights surface riêng, direction=NULL mơ hồ. → direction-aware copy + rights tab + MVP chỉ quyền lợi có due_date.
3. **🟡 Completeness/recall.** Verified: benchmark chỉ chấm 4 field per-field accuracy. `clauses[]` (toàn văn, đã có trong DB) = backstop chưa dùng. → completeness pass text-only trên clauses (pattern #258) + runtime flag + obligation-recall metric hạng mới (D-08 mở rộng field→obligation level).

**Architecture (DEC-044):** Modular monolith + Protocol contracts (KHÔNG microservice). Extractable "Contract Analysis Core" = ExtractionProvider → ObligationDeriver pipeline (Protocol mới, tách inline schedule loop) → Obligation+Rights model → CompletenessVerifier. Refactor reversible, rẻ.

**Core BA issue:** **#272** (filed 2026-06-25). 3-phase plan (P1 core / P2 depth / P3 recall metric). Đề xuất DEC-043/044/045.

**🚦 P1 GATES PILOT (Kevin 2026-06-25).** P1 = (a) ObligationDeriver Protocol + tách inline schedule loop, (b) completeness runtime flag từ clauses[], (c) direction-aware reminder copy — PHẢI ship TRƯỚC concierge 20 SME. → **P1 core = pre-pilot critical path #1.**
- **✅ Sequencing RESOLVED (DEC-046):** firm portal deferred post-pilot → **P1 core = sole pre-pilot critical path.** No contention.
- **Open Q1–Q3 (#272):** top-N standing types + labeled recall samples + schedule-vs-new-list = P2/P3 input, KHÔNG block P1.

### ✅ QC Architecture Review — accepted 2026-06-25 (all 8 points)

**Architecture corrections applied:**
- **Event Bus → REMOVED.** Actual mechanism = D-07 append-only Event Ledger (exists) + APScheduler daily tick. No in-process pub/sub needed or built.
- **`may_have_unextracted_obligations` = `documents` column ONLY** (not obligations). Three states: NULL=unknown, True=miss detected, False=cleared.

**Critical-path re-cut (QC point 1 + Kevin ratified):**
```
Pre-pilot:  #274 StandingDeriver (surface-only)
            #275 Direction-aware reminders (quyền_lợi trigger semantics, not just copy)
            #276 Honest completeness flag (always-on disclaimer, no LLM call)
            #277 Chat reliability (#268 trace fix + #263 clause fallback)
Fast-follow: Smart CompletenessVerifier + recall corpus
```

**P1 issues filed:** #274 / #275 / #276 / #277 (2026-06-25). QC response posted on #272. DOCS_INBOX comment posted #1.
**QC offers accepted:** (a) post review on DEC thread, (b) draft §FR-OB completeness AC block → PM folds when received.
**Standing obligations surface:** doc-detail "Cam kết đang hiệu lực" section — PM default. Kevin confirm needed before Designer mockup.


## Active Sprint Context

**Current phase:** **Sprint 1 IN PROGRESS** — Backend M1+ vertical slice complete on staging. Frontend wiring + QC smoke = critical path to pilot.
**Sprint 0 goal (ĐÃ ĐẠT 2026-06-11):** FastAPI + multi-tenant DB scaffold, CI/CD, Telegram bot, Vision extraction interface + 3 providers.
**Sprint 1 status (2026-06-24):** Backend shipped ALL pre-pilot tasks (#199/#213/#214/#63/#217/#241 + earlier #201/#203). DEC-039/040 ratified. Designer firm journey F0–F6 complete (PRs #242/#243). Frontend wiring Stage 3/6/0/8 + #238 confirm flow. QC #187 Playwright pre-pilot. KHE_AI #230 done. #255 cost tracking + #258 clause remap BA filed.

---

## Pre-Pilot Status Snapshot — 2026-06-24

### ✅ Backend — ALL DONE (staging)

| PR | Issue | What |
|---|---|---|
| #202+#205 | #201/#203 | DEC-031 v2 chat sessions (`tenant_009_chat_sessions`) |
| shipped | #199 | `aggregate_obligations` 4th chat tool — 3 zero-states |
| shipped | #213 | `tenants.journey_stage` + `is_first_session` master.db |
| shipped | #214 | `obligations.snoozed_until` — snooze 3 days |
| shipped | #63 | Quota guard 500 docs/month hard block, calendar reset |
| PR #229 | #217 | `TermOut` ref/page_num/bbox — Stage 3 anchor contract |
| PR #241 | #238 | `POST /documents/{id}/confirm` — CRITICAL nav-lock fix, DEC-040 |

### 🔄 In Progress / Pending

| Team | Issue | What | Gates |
|---|---|---|---|
| **KHE_AI** | ~~#230~~ ✅ | page_num/ref/bbox anchors — DONE (PR #232, staging green) | — |
| **KHE_AI** | #248 (next) | Flash-lite benchmark → DEC-041 ratification | Cost optimization |
| **Frontend** | #238 | 4 items: confirm button, Home CTA chip, `journey_advanced` refetch, DocList badge | Nav-lock live end-to-end |
| **Frontend** | #238 | MANDATORY: ReminderNudge + "X/Y bước" chip for CONFIRMED-without-channel | DEC-040 mitigation |
| **Frontend** | #238 | Interim: false-success toast 3-state fix (no backend dep) | Ship now |
| **Frontend** | (no issue) | Wire Stage 6 aggregate (#199 staging) | Stage 6 complete |
| **Frontend** | (no issue) | Wire Stage 0/8 real journey_stage API (#213 staging) | Onboarding nav-lock |
| **Frontend** | (no issue) | Wire Stage 3 ref-nav (#217 staging) | Trust gate live |
| **Frontend** | merge #216 | DS v0.2 token foundation | Everything |
| **Backend** | **#274** | StandingObligationDeriver — extract + surface "Cam kết đang hiệu lực" | **P1 pre-pilot** |
| **Backend** | **#275** | Direction-aware reminders — quyền_lợi trigger semantics + 4 Telegram templates | **P1 pre-pilot** |
| **Backend + Frontend** | **#276** | Honest completeness flag — always-on disclaimer, backfill=NULL | **P1 pre-pilot** |
| **Backend** | **#277** | Chat reliability — #268 trace fix + #263 clause fallback | **P1 pre-pilot 🔴** |
| **Designer** | **#278** ✅ | /admin/documents LIST full revamp — mockup merged PR #283 → `main` (2026-06-26) | **Done — gates FE #285** |
| **Backend** | **#279** | GET /documents/ list API delta — 6 new fields + search extends to `primary_party` (spec updated in comment 2026-06-26) | **Pre-pilot, gates FE #285** |
| **Frontend** | **#285** ✅ filed | /admin/documents list v2 implementation — F1 (Cần kiểm tra chip), F2 (hydration flash), N3 (standing obligation weight fix), N4 (badge hide), full 7-row-state spec. Blocks on #279 for populated state; empty state shippable now. | **Pre-pilot** |
| **Designer** | **#281** | /admin/documents/:id DETAIL full revamp — inverted IA, self-party-gated, rights surface (QC doc-detail report + PM adversarial verify 2026-06-26). **+ "Nội dung hợp đồng" tab** (Kevin approved 2026-06-26, addendum in §PENDING POSTS — promote clauses[] to peer tab) | **Pre-pilot, gates FE** |
| **Backend+AI** | **#282** | Doc-detail data/logic correctness — party separation (root cause), due-date resolution, per-obligation direction, event-trigger activation, counter integrity | **Pre-pilot 🔴 (B1-B5 blockers)** |
| **Backend** | **#284** ✅ filed | DETAIL clauses API delta — `GET /documents/{id}/clauses` + `ClauseOut`/`ClauseListOut`. Read-only surface of existing clause data for "Nội dung hợp đồng" tab | **Pre-pilot, parallel with #281** |
| ~~Backend~~ | #270/#65/#237 | **Firm portal ⏸️ DEFERRED post-pilot (DEC-046).** BA #270 frozen as Phase 2 spec. Build resumes post-pilot. | — (out of pilot) |
| **QC** | #187 | Playwright e2e — upload→extract→confirm→assert nav unlock + Event ledger | Pre-pilot gate |
| **QC** | #75/#175 | UAT smoke M0/M1 + E2E script (needs uat-demo-b + uat-demo-noconsent) | Pre-pilot gate |

### ⏳ Non-pilot (before go-live)

| Team | Issue | What |
|---|---|---|
| KHE_Docs | DOCS_INBOX | Fold 5 backend schema changes from 2026-06-23 (Backend must post) |
| KHE_Docs | DOCS_INBOX | Fold DEC-039 (supersedes #182, posted 2026-06-24 ✅) |
| KHE_Docs | DOCS_INBOX | Fold DEC-040 (is_first_session @ CONFIRMED, posted 2026-06-24 ✅) |
| KHE_Docs | #147 | CONTRACT_LOGIC doc (lawyer partner review) |
| Compliance | #38 | 90d retention verify-back — counsel confirm (DEC-010 sign-off gate) |
| Backend | #65 | Firm portal scaffold — #63 now merged → unblocked, but firm journey Phase 2 → LOW |

### ✅ Closed this session (2026-06-24)
DEC-039 ratified (firm full data model). DEC-040 ratified + amended via #249 (first-confirm gate). DEC-011 pricing revised to 100k/month. Economics locked: 177đ/call, 82.3% GM at 100 docs/month. Backend PR #241 merged. Designer PRs #242/#243 merged (firm journey F0–F6). KHE_AI #230 + #248 closed. Issues filed: #250/#251 (#249 fix), #255 (cost tracking), #258 (clause remap BA).

### ⚙️ Architectural insight locked (2026-06-24)
**`clauses[]` = source of truth for downstream text processing.** Vision call extracts full clause content once (DEC-026). All subsequent field-level operations (type remap, future schema additions, firm-specific extraction) use text-only LLM calls on clauses — no vision quota, ~2–3đ vs 177đ. Pattern generalizes to: re-classification, multi-language, incremental field addition without re-upload.

**Clause remap (#258) status:** Backend ✅ staging · KHE_AI ✅ staging · Frontend #262 filed (task assignment, in progress).

### 🏛️ Firm Portal BA #270 — Q0=B RESOLVED → pre-pilot (DEC-042, Kevin 2026-06-24)
Consolidated engineering BA (#65 scaffold + #237 handshake/feed) in #258 format. Core value-add over #237: **cross-tenant read fan-out** (consent in master.db + obligations in N per-tenant DBs → scatter-gather via `get_tenant_session()`, caller-close lifecycle = leak risk #1), consent state machine (D-09 firm-cannot-self-grant/revoke, re-request = UPDATE-in-place on `(firm_id,tenant_id)` unique), DEC-039 visibility matrix (gate = `contains_personal_data` boolean not type string), per-tenant Event ledger for consent changes.
**✅ Q0 = B (Kevin 2026-06-24):** firm portal vào pre-pilot → **DEC-042 amends DEC-037** (firm-journey-defer clause only). Priority HIGH. **#65 UNBLOCKED + assigned Backend** (dep #63 merged, `blocker:waiting-dependency` cleared). Sequence #65 → #237. KHE_AI `contains_personal_data` flag = dep of #237 Phase C. DOCS_INBOX post pending (DEC-042 amends DEC-037).

### ✅ Closed previous session (2026-06-23)
#179 (DEC-031 storage decision), #201 (DEC-031 implement), #203 (DEC-031 retro fixes).

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
| DEC-011 | **B2B2B model:** firm là khách hàng trả tiền, SME free Phase 1. SME-pays mở ở GĐ2 (drafting/review). **Pricing revised 2026-06-24: 100,000 VND/client/tháng** (= 1,200,000 VND/client/năm). Rationale: cheap price signals low quality in B2B channel — tax agents + law firms judge product grade by price. **Planning baseline: 100 docs/month per SME** → cost 17,700đ, GM 82.3% (Kevin ratified 2026-06-24). Quota hard cap 500/month unchanged (DEC-023). | **Ratified** (user relay 2026-06-10; pricing + baseline revised Kevin 2026-06-24) | 2026-06-24 |
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

| DEC-032 | **D-02 Concierge — Option B ratified (Kevin 2026-06-23).** Concierge pre-fills data, user must self-confirm on first login. Flow: concierge uploads + pre-fills fields → tenant lands at `NEEDS_REVIEW` → user taps confirm on first login → advances to `ACTIVATED`. D-02 preserved (human confirm required, AI never final authority). Filed in #198 PM amendments. | **Ratified** (Kevin 2026-06-23) | 2026-06-23 |

| DEC-033 | **tenant_journey_stage state machine (2026-06-23).** Per-tenant monotonic state machine in `master.db`: `NEW → EXTRACTING → NEEDS_REVIEW → CONFIRMED → ACTIVATED → STEADY`. `home = f(stage)` routing. Nav-lock = `is_first_session` flag only (cleared at ACTIVATED, not persistent punishment). ACTIVATED = ≥1 channel (Telegram OR email) — no hard-block requiring both. Backend task: #213 (shipped 2026-06-23). DOCS_INBOX fold pending. | **Ratified** (Kevin 2026-06-23, via UX BA #198) | 2026-06-23 |

| DEC-034 | **4-state empty matrix — closed contract (2026-06-23).** Applies to ALL list surfaces. States: (1) `cold_start` = 0 docs → "Chưa có tài liệu..." + upload CTA. (2) `processing` = has doc, extraction pending → progress. (3) `all_clear` = has extracted doc, 0 obligations due → "Đã quét — bạn không có hạn nào." ✅ (legitimate). (4) `no_match` = query no match → D-08 + exit. CRITICAL: cold_start ≠ all_clear wording. "Khế sẽ nhắc khi có hạn mới" NEVER on cold tenant. | **Ratified** (Kevin 2026-06-23, via UX BA #198) | 2026-06-23 |

| DEC-035 | **Snooze "Nhắc lại sau 3 ngày" approved (2026-06-23).** `Event.type = reminder_snoozed`, `obligations.snoozed_until = scheduled_at + 3 days`, scheduler skips if `snoozed_until > now`. POST /obligations/{id}/snooze → `{snoozed_until}`. v1: always 3 days, no custom duration. Backend task: #214 (shipped 2026-06-23). | **Ratified** (Kevin 2026-06-23, via #208 comment) | 2026-06-23 |

| DEC-036 | **Quota guard parameters confirmed (Kevin 2026-06-23).** Hard block (HTTP 429) when quota exceeded. Calendar month reset (1st of month). Default 500 docs/month. Response: `{error:"quota_exceeded", limit, used, reset_date}`. Backend #63 shipped. | **Ratified** (Kevin 2026-06-23) | 2026-06-23 |

| DEC-037 | **PWA vs Admin stage split ratified (2026-06-23).** PWA primary: Stage 0 self-serve, 1, 4, 5, 6. Admin primary: Stage 0 concierge, 3. Both: Stage 2, 7, 8. Firm journey deferred to Phase 2 entirely. | **Ratified** (Kevin 2026-06-23, via #208 PM comment) | 2026-06-23 |

| DEC-038 | **FR-CQ ID mapping (deviation accepted 2026-06-23).** KHE_Docs landed DEC-031 FRs as FR-CQ-07/08/09/10 (not 04/05/06/07 as PM spec'd) because 04-06 were occupied by extraction cycles 3+4. Mapping: FR-CQ-07=state_json, FR-CQ-08=scope chip visibility, FR-CQ-09=ambiguity guard+cold-start, FR-CQ-10=session invalidation. PM accepted — no re-number. | **Ratified** (PM accept 2026-06-23) | 2026-06-23 |

| DEC-039 | **Firm portal data model: full business data with explicit SME consent (Kevin ratified 2026-06-24). Supersedes #182 (counts-only).** NĐ 13/2023 only covers personal data of natural persons (thể nhân) — B2B commercial data (pháp nhân names, contract amounts, deadlines) is NOT personal data under NĐ 13. Firm sees full business data per consented SME client: `doi_tac` names, `gia_tri_hd`, obligations + due dates. Exception: `hd_lao_dong` docs with `contains_personal_data = true` → show metadata only, hide `doi_tac` (employee name) + `gia_tri_hd` (individual salary). Consent model: `firm_tenant_access` with `consent_status`, `granted_at`, `revoked_at`. SME can revoke at any time (D-10). Firm cannot self-remove from access — firm must request client to revoke (D-09). DOCS_INBOX posted 2026-06-24. Backend: issue #237. Designer: F3/F4/F5/F6 mockups shipped (PRs #242/#243). | **Ratified** (Kevin 2026-06-24) | 2026-06-24 |

| DEC-040 | **`is_first_session` clears at first-confirm (amended 2026-06-24 via #249).** Original: clears when all docs confirmed. **Amendment:** gate = `confirmed_count >= 1` (first doc confirmed). Rationale: Kevin UAT `uat-demo` (17 docs) — confirmed 1, sidebar still locked — proved "all-confirmed" is pilot-blocking friction for concierge onboarding (DEC-012). Semantic separation: D-02 = per-doc audit (hard rule, intact) ≠ journey gate (UX policy, now relaxed to first-confirm). Unconfirmed docs invisible to Khế (scheduler, obligations) — D-02 fully preserved. Backend: 1-line change in `confirm_document()`. FE mandatory: persistent "X/N tài liệu cần xác nhận" counter on dashboard. Priority: HIGH (pre-pilot). DOCS_INBOX posted 2026-06-24. | **Ratified** (Kevin 2026-06-24 via #238); **amended** (PM 2026-06-24 via #249) | 2026-06-24 |

| DEC-041 | **Flash-lite benchmark — CANCELLED (Kevin 2026-06-24).** Economics acceptable at 177đ/call + 100k VND/client/month. No re-measurement needed. Gemini 2.5 Flash stays as primary provider (DEC-002 unchanged). Issue #248 closed. | **Closed — not proceeding** | 2026-06-24 |

| DEC-046 | **Firm Portal DEFERRED to post-pilot (Kevin 2026-06-25). Supersedes DEC-042.** Pilot = Khế core ONLY (DEC-043 repositioning — core obligation+rights IS the product; firm portal = derivative surface, không gate pilot promise). Reverts to DEC-037 Phase 2 posture. #65/#237/#270 frozen as Phase 2 spec (architecture stands, build post-pilot). Resolves P1-vs-firm-portal tension → **Contract Analysis Core P1 (#272) = sole pre-pilot critical path.** | **Ratified** (Kevin 2026-06-25) | 2026-06-25 |
| DEC-043 | **Core repositioning: Khế = Obligation & Rights Management Platform (Kevin 2026-06-25).** Khế đảm bảo MỌI nghĩa vụ + quyền lợi pháp lý của tổ chức (đã văn bản hóa) được quản trị + thực hiện — tài chính + phi tài chính, nghĩa vụ + quyền lợi (cùng model khác direction). Chat + reminder = PHÁI SINH của Contract Analysis Core. Không pivot — sharpen Obligation "MVP heart". Ưu tiên: extraction completeness + obligation depth > chat/reminder polish. Tài liệu MVP = HĐ, mở rộng qua document type. Engineering BA #272. | **Ratified** (Kevin 2026-06-25) | 2026-06-25 |
| DEC-044 | **Architecture = Modular Monolith + Protocol contracts (Kevin endorse QC 2026-06-25). NOT microservice deploy.** "Dễ extend + reuse" đạt qua module boundary sạch + Protocol (precedent VisionExtractionProvider) trong monolith; giữ multi-tenant SQLite + atomic transaction + D-07. Extractable "Contract Analysis Core" = ExtractionProvider→ObligationDeriver pipeline→Obligation+Rights model→CompletenessVerifier. Tách microservice CHỈ khi scale thật. Platform/reuse play = DEC riêng nếu Kevin muốn sau. Rationale QC: microservice ≠ modularity; team 2-dev + pre-PMF → 5× ops cost, phá get_tenant_session, mất atomicity. | **Ratified** (Kevin 2026-06-25, QC review) | 2026-06-25 |
| DEC-045 | **Completeness = mission-critical metric (Kevin endorse QC 2026-06-25).** Bỏ sót 1 obligation (vd điều khoản phạt) = top-severity failure ≠ sai 1 field. Tách obligation-recall metric riêng khỏi per-field accuracy (M-3 ≥90%). `clauses[]` = completeness backstop (completeness pass text-only, pattern #258). D-rule mới D-COMPLETENESS (KHE_Docs gán số — D-11/D-13 đã dùng): tối ưu recall, flag clause sinh-nghĩa-vụ chưa-capture, thà flag thiếu hơn silent miss (D-08 mở rộng field→obligation). Metric def trong BA #272. | **Ratified** (principle) (Kevin 2026-06-25) | 2026-06-25 |
| DEC-042 | **[SUPERSEDED by DEC-046 — firm portal deferred post-pilot]** Firm Portal vào pre-pilot scope (Kevin 2026-06-24). Amends DEC-037** (chỉ clause "firm journey deferred to Phase 2 entirely"; PWA-vs-Admin stage split giữ nguyên). Rationale: DEC-013 pilot firm-paid → firm cần portfolio surface ngày 1 ("firm-pays, firm operates"). Engineering BA = #270 (cross-tenant fan-out + consent state machine + DEC-039 visibility). Build sequence: #65 scaffold (unblocked, dep #63 merged) → #237 handshake+feed. KHE_AI `contains_personal_data` flag = dep #237 Phase C. Priority HIGH. | **Ratified** (Kevin 2026-06-24) | 2026-06-24 |

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
| 1 | KHE_Docs | Active — branch `claude/edit-git-docs-Khe01`. DOCS_INBOX 5 entries pending from 2026-06-23 backend merges. |
| 2 | KHE_PM_Assistant | Active ✅ — this file |
| 3 | KHE_Backend | **Sprint 1 COMPLETE** — all pre-pilot tasks shipped to staging (#199/#213/#214/#63/#217 + earlier). Pending: #65 firm portal (Phase 2, low), #230 KHE_AI side. |
| 4-5 | KHE_Frontend_Admin / PWA_Chat | Active — DS v0.2 migration in progress. Pending: wire Stage 3/6/0/8, merge #216. |
| 6 | KHE_QC | Active — #187 Playwright e2e (HIGH, pre-pilot), #75/#175 UAT smoke pending. |
| 7 | KHE_Designer | Active — PRs #197/#200/#204/#210/#242/#243 all merged. 8-stage SME mockup suite + full firm journey F0–F6 complete. |
| 8 | KHE_Infra | Low-touch. VPS 2 environments (staging :8001 / prod :8000). CI/CD green. |
| 9 | KHE_AI | **#230 DONE** — page_num/ref/bbox anchors merged, staging green (12/12 tests, PR #232). #248 cost figure ratified (177đ/doc Gemini 2.5 Flash). Flash-lite benchmark queued as next task (→ DEC-041 pending). |
| 10 | KHE_Compliance | Active — #38 open (90d retention counsel verify-back, pre go-live gate). #105 NĐ13 PII logging debt tracked. |

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

## Design System v0.2 + 8-Stage UX Journey Status — 2026-06-23

### Design System v0.2 (PR #197 merged)
- 11-step neutral ramp, one accent `khế-emerald #0F7A56`
- Soft layered elevation e1/e2/e3; motion tokens; focus rings WCAG 2.4.7
- Components: Button (subtle/iconOnly), Badge (dot), Skeleton, ConfidenceMeter (FR-EX-05), EmptyState (generic + D-08 notFound)
- §2b a11y primitives (PR #210): NavItem, Dropzone, IconButton, LiveRegion, VisuallyHidden
- Back-compat: `shadow.*` alias for `elevation.*`
- warning color fix: `#9A6700→#8A6300` (contrast)

### 8-Stage Mockup Suite (all PRs merged)
| PR | Content |
|---|---|
| #200 | journey primitives (state machine, 4-state empty), + all 8 stage mockups |
| #204 | App nav v0.2 — desktop sidebar + mobile bottom tab, nav-lock first-session |
| #210 | a11y primitives (§2b) + Stage 6 aggregate contract (frozen) |

### Stage wire-up status
| Stage | Mockup | FE code | Backend dep |
|---|---|---|---|
| 0 self-serve | ✅ | Building (mock heuristic) | #213 staging ✅ |
| 0 concierge | ✅ | Building (D-02 Opt B ratified) | #213 staging ✅ |
| 1 upload | ✅ | Done | — |
| 2 processing | ✅ | Done | — |
| 3 review side-by-side | ✅ | Shell done, ref-nav pending | #217 staging ✅, #230 KHE_AI pending |
| 4 obligation AHA | ✅ | Done | — |
| 5 Telegram | ✅ | Done | — |
| 6 chat | ✅ | PR #211 done (POST shape) | #199 staging ✅ — wire aggregate |
| 7 3-tab obligations | ✅ | Done (#146 chain) | — |
| 8 steady dashboard | ✅ | Building | #213 staging ✅ |

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
