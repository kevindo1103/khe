/**
 * Khế — Journey · Stage 7 Obligations (3 tabs)  (mockup_journey_stage7_obligations_v0.1.jsx)
 * KHE_Designer · issue #198 Phase B · builds on Design System v0.2 + journey primitives v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Stage 7 = the two-sided ledger as 3 tabs (brief #198):
 *   • Nghĩa vụ      (direction=nghĩa_vụ)  — bạn phải làm
 *   • Quyền lợi     (direction=quyền_lợi) — người khác phải làm cho bạn
 *   • Cần xác nhận  (direction=null)      — D-02: chưa biết self-party
 *
 * Per-tab EMPTY STATE uses the 4-state matrix (journey v0.1) — each tab's empty is
 * honest & distinct, never "Khế sẽ nhắc khi có hạn" on a cold tenant.
 *   - Nghĩa vụ empty: branch by tenant state (cold_start / all_clear).
 *   - Quyền lợi empty: "Khế cũng theo dõi điều người khác phải làm cho bạn."
 *   - Cần xác nhận empty: gentle nudge "Không còn gì cần xác nhận."
 * Digest (FR-RM-04): "Tháng này: N hạn của bạn, M quyền lợi cần đòi."
 *
 * Row rendering (category/series/obligor/amount/trigger chips + status actions)
 * follows mockup_admin_obligation_v0.2 — kept compact here; that file = full spec.
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Badge, Toast } from "./mockup_design_system_v0.2.jsx";
import { JourneyEmptyState } from "./mockup_journey_primitives_v0.1.jsx";

const CAT = { payment: "💵 Thanh toán", delivery: "📦 Giao hàng", renewal: "🔁 Gia hạn", compliance: "📋 Tuân thủ" };

const SEED = {
  "nghĩa_vụ": [
    { id: 1, desc: "Gia hạn/chấm dứt HĐ thuê Q7", cat: "renewal", due: "01/08/2026", bucket: "due_soon", obligor: "Bạn" },
    { id: 2, desc: "Thanh toán tiền thuê 45tr", cat: "payment", due: "05/07/2026", bucket: "due_soon", obligor: "Bạn", series: "2/3" },
    { id: 3, desc: "Đóng BHXH nhân viên", cat: "compliance", due: null, bucket: "open_ended", obligor: "Bạn", recurring: true },
  ],
  "quyền_lợi": [
    { id: 4, desc: "Nhận lô hàng đợt 1", cat: "delivery", trigger: "sau nghiệm thu", bucket: "waiting", obligor: "Cty Bao Bì Việt" },
  ],
  "null": [
    { id: 5, desc: "Thanh toán phí hợp tác 50tr", cat: "payment", due: "20/08/2026", bucket: "upcoming", obligor: "Bên A" },
  ],
};

const TABS = [
  { key: "nghĩa_vụ", label: "Nghĩa vụ", hint: "bạn phải làm" },
  { key: "quyền_lợi", label: "Quyền lợi", hint: "người khác làm cho bạn" },
  { key: "null", label: "Cần xác nhận", hint: "chưa biết bên nào là bạn" },
];

function Row({ o, onDone }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: t.space[3], padding: `${t.space[3]}px 0`, borderBottom: `1px solid ${t.color.border}` }}>
      <div>
        <div style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.medium, color: t.color.ink }}>{o.desc}</div>
        <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginTop: t.space[2] }}>
          <Badge kind="neutral">{CAT[o.cat]}</Badge>
          {o.series && <Badge kind="brand">Đợt {o.series}</Badge>}
          {o.obligor && <Badge kind="neutral">{o.obligor} phải làm</Badge>}
          {o.bucket === "waiting" ? <Badge kind="due_soon">⏳ Chờ: {o.trigger}</Badge>
            : o.due ? <Badge kind={o.bucket === "due_soon" ? "due_soon" : "neutral"}>📅 {o.due}</Badge>
            : <Badge kind="neutral">Vô thời hạn</Badge>}
          {o.recurring && <Badge kind="neutral">🔁 định kỳ</Badge>}
        </div>
      </div>
      <Button size="sm" onClick={onDone}>Hoàn thành</Button>
    </div>
  );
}

export default function Stage7Obligations({ tenantState = "STEADY" }) {
  const [tab, setTab] = useState("nghĩa_vụ");
  const [toast, setToast] = useState(null);
  const items = SEED[tab];
  const counts = { "nghĩa_vụ": SEED["nghĩa_vụ"].length, "quyền_lợi": SEED["quyền_lợi"].length, "null": SEED["null"].length };

  const renderEmpty = () => {
    if (tenantState === "NEW") return <JourneyEmptyState state="cold_start" onUpload={() => {}} />;
    if (tab === "quyền_lợi") return <div style={{ textAlign: "center", padding: `${t.space[8]}px ${t.space[5]}px`, color: t.color.inkMuted, fontFamily: t.font.family }}>
      <div style={{ fontSize: 22, marginBottom: t.space[2] }}>🤝</div>
      <div style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, color: t.color.ink }}>Chưa có quyền lợi nào</div>
      <div style={{ fontSize: t.font.size.sm, marginTop: t.space[1] }}>Khế cũng theo dõi điều người khác phải làm cho bạn.</div>
    </div>;
    if (tab === "null") return <div style={{ textAlign: "center", padding: `${t.space[8]}px ${t.space[5]}px`, color: t.color.inkMuted, fontFamily: t.font.family }}>
      <div style={{ fontSize: 22, marginBottom: t.space[2] }}>✓</div>
      <div style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, color: t.color.ink }}>Không còn gì cần xác nhận</div>
    </div>;
    return <JourneyEmptyState state="all_clear" />; // Nghĩa vụ, có data, 0 hạn
  };

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 820, margin: "0 auto" }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Issue #198 · Stage 7</span>
        <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[1]}px 0 0` }}>Nghĩa vụ & quyền lợi</h1>

        {/* digest (FR-RM-04) */}
        <div style={{ marginTop: t.space[4], padding: `${t.space[3]}px ${t.space[4]}px`, background: t.color.primarySoft, border: `1px solid ${t.color.primaryBorder}`, borderRadius: t.radius.md, fontSize: t.font.size.sm, color: t.color.ink }}>
          📨 <strong>Tháng này:</strong> 2 hạn của bạn · 1 quyền lợi cần đòi · 1 việc chờ sự kiện.
        </div>

        {/* 3 tabs */}
        <div style={{ display: "flex", gap: t.space[2], borderBottom: `1px solid ${t.color.border}`, margin: `${t.space[5]}px 0` }}>
          {TABS.map((tb) => {
            const active = tab === tb.key;
            const warn = tb.key === "null" && counts.null > 0;
            return (
              <button key={tb.key} onClick={() => setTab(tb.key)} title={tb.hint} style={{
                padding: `${t.space[2]}px ${t.space[4]}px`, background: "transparent", border: "none", cursor: "pointer",
                fontFamily: t.font.family, fontSize: t.font.size.base, fontWeight: t.font.weight.semibold,
                color: active ? t.color.primary : t.color.inkMuted, borderBottom: `2px solid ${active ? t.color.primary : "transparent"}`,
                display: "flex", alignItems: "center", gap: t.space[2],
              }}>
                {tb.label}
                <span style={{ fontSize: t.font.size.xs, background: warn ? t.color.warning_soft : t.color.surfaceSunken, color: warn ? t.color.warning : t.color.inkMuted, borderRadius: t.radius.pill, padding: `0 ${t.space[2]}px` }}>{counts[tb.key]}</span>
              </button>
            );
          })}
        </div>

        {/* "Cần xác nhận" CTA → self-party (Stage 3) */}
        {tab === "null" && counts.null > 0 && (
          <div style={{ background: t.color.warning_soft, border: `1px solid ${t.color.warningBorder}`, borderRadius: t.radius.md, padding: t.space[4], marginBottom: t.space[5], display: "flex", justifyContent: "space-between", alignItems: "center", gap: t.space[3], flexWrap: "wrap" }}>
            <span style={{ fontSize: t.font.size.sm, color: t.color.warning }}><strong>{counts.null} chỗ cần bạn kiểm tra (1 phút).</strong> Xác nhận “bên nào là bạn” để Khế tách đúng. (D-02)</span>
            <Button onClick={() => {}}>Xác nhận ngay</Button>
          </div>
        )}

        <Card>
          {items.length === 0 ? renderEmpty()
            : items.map((o) => <Row key={o.id} o={o} onDone={() => { setToast("Hoàn thành — ghi Event ✓"); setTimeout(() => setToast(null), 2000); }} />)}
        </Card>
      </div>

      {toast && (
        <div style={{ position: "fixed", bottom: t.space[6], left: "50%", transform: "translateX(-50%)", zIndex: t.z.toast }}>
          <Toast kind="success">{toast}</Toast>
        </div>
      )}
    </div>
  );
}
