/**
 * Khế — Journey · Stage 6 Chat  (mockup_journey_stage6_chat_v0.1.jsx)
 * KHE_Designer · issue #198 Phase B · builds on Design System v0.2 + journey primitives v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Root cause #198: chat returned D-08 ("Không tìm thấy…") for an AGGREGATE query
 * ("Các nghĩa vụ của tôi?") and showed D-08-returning chips on an EMPTY tenant.
 *
 * Fixes shown:
 *   1. Split AGGREGATE (structured query over the store) from RETRIEVAL (RAG over
 *      clauses). "Các nghĩa vụ của tôi?" is aggregate → always answerable from the
 *      obligation store; it is NOT a no-match.
 *   2. Suggestion chips derived from REAL data — on a cold tenant, show an
 *      onboarding nudge instead of chips that would just return D-08.
 *   3. Every answer cites a source (FR-CQ-02), tappable.
 *   4. D-08 reserved for genuine retrieval no-match → integrity + an exit (not a chip).
 *
 * SPEC WATCH: aggregate-vs-retrieval routing + all-clear answer touch FR-CQ →
 *   DOCS_INBOX when this composes into the built chat (coordinate Backend #27/#146).
 *
 * AGGREGATE RESPONSE CONTRACT (#199 — LOCKED 2026-06-23, backend builds to this)
 *   Backend adds a 4th LLM tool `aggregate_obligations` (no separate classifier).
 *   Decisions: (1) NO amount_raw sum in v1 — count + series progress only (D-06:
 *   summing free-text money fabricates figures). (2) group_by axes = direction /
 *   status / obligation_type / series. (3) Shape below (formalized from the
 *   "có data" tab, line ~84):
 *     {
 *       intent: "aggregate" | "retrieval",
 *       found: true,                 // ALWAYS true for aggregate — even total=0 (never D-08)
 *       answer: "Bạn có 7 nghĩa vụ…",// composed prose
 *       summary: {
 *         total: 7, group_by: "direction",
 *         groups: [{ key, label, count, nearest?: {title, days_left | trigger} }],
 *         status_breakdown: { waiting_trigger, overdue, due_soon }  // cheap; powers the 3rd bullet
 *       },
 *       source: { obligation_count, doc_count, label: "7 nghĩa vụ · 3 hợp đồng" },
 *       sources: [...]               // drill-down refs (FR-CQ-02)
 *     }
 *   THREE distinct zero-states (FE renders differently — keep separate):
 *     • cold_start  → tenant has 0 docs → found:true + `tenant_empty:true` → onboarding nudge (NOT "0", NOT D-08)
 *     • aggregate-0 → has data, filter count 0 → found:true, total:0 → "Bạn không có … quá hạn."
 *     • retrieval no-match → found:false, intent:"retrieval", D-08 exact string, sources:[]
 *   Suggestion chips are FE-static (not backend). Acceptance = QC 9-case surface on #199.
 *
 *   DASHBOARD CONSUMER RULE (Tổng quan home — QC #199 drift fix): the two axes do
 *   NOT add together. Direction cards come from `summary.groups[]` (nghĩa_vụ /
 *   quyền_lợi / null) and SUM to `summary.total`. Status (Chờ sự kiện / Sắp tới /
 *   Quá hạn) comes from `summary.status_breakdown` and CROSS-CUTS direction — render
 *   it as a separate strip, never as a 4th direction card. Reassurance copy must use
 *   the same group/total numbers (no phantom "tháng này" subset unless backend adds
 *   a due_within_days breakdown).
 */
import React, { useState } from "react";
import { tokens as t, Button } from "./mockup_design_system_v0.2.jsx";
import { JourneyEmptyState } from "./mockup_journey_primitives_v0.1.jsx";

function Device({ title, children, footer }) {
  return (
    <div style={{ width: 390, height: 720, border: `1px solid ${t.color.border}`, borderRadius: t.radius.xl, overflow: "hidden", background: t.color.surface, boxShadow: t.elevation.e2, display: "flex", flexDirection: "column", fontFamily: t.font.family }}>
      <div style={{ padding: `${t.space[3]}px ${t.space[4]}px`, borderBottom: `1px solid ${t.color.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontWeight: t.font.weight.bold, color: t.color.primary }}>Khế · Hỏi-đáp</span>
        <span style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle }}>{title}</span>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: t.space[4], display: "flex", flexDirection: "column", gap: t.space[3] }}>{children}</div>
      {footer}
    </div>
  );
}
function Composer({ chips = [] }) {
  return (
    <div style={{ borderTop: `1px solid ${t.color.border}`, padding: t.space[3] }}>
      {chips.length > 0 && (
        <div style={{ display: "flex", gap: t.space[2], overflowX: "auto", marginBottom: t.space[2] }}>
          {chips.map((c) => (
            <span key={c} style={{ flexShrink: 0, fontSize: t.font.size.xs, color: t.color.primary, background: t.color.primarySoft, border: `1px solid ${t.color.primaryBorder}`, padding: `${t.space[1]}px ${t.space[2]}px`, borderRadius: t.radius.pill, whiteSpace: "nowrap", cursor: "pointer" }}>{c}</span>
          ))}
        </div>
      )}
      <div style={{ display: "flex", gap: t.space[2], alignItems: "center" }}>
        <input placeholder="Hỏi về hợp đồng của bạn…" style={{ flex: 1, height: 44, padding: `0 ${t.space[3]}px`, border: `1px solid ${t.color.border}`, borderRadius: t.radius.pill, outline: "none", fontFamily: t.font.family, fontSize: t.font.size.base }} />
        <Button iconOnly style={{ borderRadius: t.radius.pill }}>➤</Button>
      </div>
    </div>
  );
}
function User({ children }) {
  return <div style={{ alignSelf: "flex-end", maxWidth: "85%", background: t.color.primary, color: "#fff", borderRadius: t.radius.lg, padding: t.space[3], fontSize: t.font.size.sm }}>{children}</div>;
}
function Bot({ children, source }) {
  return (
    <div style={{ alignSelf: "flex-start", maxWidth: "88%" }}>
      <div style={{ background: t.color.surfaceSunken, color: t.color.ink, borderRadius: t.radius.lg, padding: t.space[3], fontSize: t.font.size.sm, lineHeight: t.font.lineHeight.relaxed, whiteSpace: "pre-line" }}>{children}</div>
      {source && <a href="#" style={{ display: "inline-flex", gap: 4, marginTop: t.space[1], fontSize: t.font.size.xs, color: t.color.primary, textDecoration: "none", background: t.color.primarySoft, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill }}>📄 Nguồn: {source}</a>}
    </div>
  );
}

export default function Stage6Chat() {
  const [tab, setTab] = useState("populated");
  return (
    <div style={{ background: t.color.surfaceAlt, minHeight: "100vh", padding: t.space[8], fontFamily: t.font.family }}>
      <header style={{ marginBottom: t.space[7], maxWidth: 760 }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Issue #198 · Stage 6</span>
        <div style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, marginTop: t.space[1] }}>Hỏi đáp — aggregate ≠ retrieval</div>
        <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, marginTop: t.space[2], lineHeight: t.font.lineHeight.relaxed }}>
          "Các nghĩa vụ của tôi?" là câu <strong>aggregate</strong> → trả lời từ kho, KHÔNG phải no-match. Chip theo data thật. D-08 chỉ cho retrieval no-match thật.
        </p>
        <div style={{ display: "flex", gap: t.space[2], marginTop: t.space[4], flexWrap: "wrap" }}>
          {[["populated", "Có data (aggregate + retrieval)"], ["cold", "Cold-start (nudge, không chip-D-08)"], ["nomatch", "No-match thật (D-08)"]].map(([k, l]) => (
            <button key={k} onClick={() => setTab(k)} style={{ padding: `${t.space[2]}px ${t.space[4]}px`, borderRadius: t.radius.md, cursor: "pointer", fontFamily: t.font.family, fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, background: tab === k ? t.color.primary : t.color.surface, color: tab === k ? "#fff" : t.color.inkBody, border: `1px solid ${tab === k ? "transparent" : t.color.border}` }}>{l}</button>
          ))}
        </div>
      </header>

      {tab === "populated" && (
        <Device title="có data" footer={<Composer chips={["Cái gì sắp hết hạn?", "Còn mấy đợt thanh toán?", "Việc gì đang chờ sự kiện?"]} />}>
          <User>Các nghĩa vụ của tôi?</User>
          {/* AGGREGATE — answered from the obligation store, not RAG, never D-08 */}
          <Bot source="7 nghĩa vụ · 3 hợp đồng">
            {"Bạn có 7 nghĩa vụ đang theo dõi:\n• Bạn cần: 4 (gần nhất — gia hạn mặt bằng Q7, còn 23 ngày)\n• Đối tác cần làm cho bạn: 2\n• Chờ sự kiện: 1 (giao hàng — sau nghiệm thu)"}
          </Bot>
          <User>HĐ thuê Q7 còn hạn bao lâu?</User>
          {/* RETRIEVAL — specific, cited */}
          <Bot source="HĐ thuê mặt bằng Q7 · đ.3">Bạn cần gia hạn hoặc chấm dứt trước 60 ngày. Hợp đồng hết hạn 30/09/2026 — còn 99 ngày.</Bot>
        </Device>
      )}

      {tab === "cold" && (
        <Device title="cold-start" footer={<Composer />}>
          {/* Cold tenant: an onboarding nudge — NOT chips that would just return D-08 */}
          <div style={{ margin: "auto 0" }}>
            <JourneyEmptyState state="cold_start" onUpload={() => {}} />
            <div style={{ textAlign: "center", fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[2], padding: `0 ${t.space[5]}px`, lineHeight: t.font.lineHeight.relaxed }}>
              Khi đã có hợp đồng, hỏi Khế: "cái gì sắp hết hạn?", "tìm HĐ với bên ABC"…
            </div>
          </div>
        </Device>
      )}

      {tab === "nomatch" && (
        <Device title="no-match" footer={<Composer chips={["Cái gì sắp hết hạn?", "Còn mấy đợt thanh toán?"]} />}>
          <User>Phí gửi xe trong HĐ thuê Q7 là bao nhiêu?</User>
          {/* genuine retrieval no-match → D-08 integrity + an exit (state 4 of matrix) */}
          <div style={{ alignSelf: "flex-start", width: "100%" }}>
            <JourneyEmptyState state="no_match" onRetry={() => {}} onUpload={() => {}} />
          </div>
        </Device>
      )}
    </div>
  );
}
