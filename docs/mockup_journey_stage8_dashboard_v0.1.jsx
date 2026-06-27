/**
 * Khế — Journey · Stage 8 Steady-state Dashboard  (mockup_journey_stage8_dashboard_v0.1.jsx)
 * KHE_Designer · issue #198 Phase C · Design System v0.2 + journey primitives v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Stage 8 = STEADY (J-E "yên tâm"). The "Tổng quan" tab answers ONE question:
 * "Tôi có cần lo gì không?" — reassurance is only shown when it is LEGITIMATE
 * (real data + genuinely nothing urgent), per-scope honest, never overpromised.
 * Two variants: all-clear (legitimate) vs has-work.
 *
 * PHASE-2-IA-DEBT: "Tổng quan" sits atop a 6-tab entity nav (Phase 1). Job-shaped
 *   IA ("Hôm nay cần lo / Sắp tới / Đã xong / Khám phá") is the post-pilot candidate.
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Badge } from "./mockup_design_system_v0.2.jsx";
import { LockedNav, ScopeCard } from "./mockup_journey_primitives_v0.1.jsx";

function Stat({ n, label, tone }) {
  return (
    <Card style={{ flex: "1 1 150px" }}>
      <div style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: tone, fontVariantNumeric: "tabular-nums" }}>{n}</div>
      <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>{label}</div>
    </Card>
  );
}

export default function Stage8Dashboard() {
  const [view, setView] = useState("has_work");
  const clear = view === "all_clear";
  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 820, margin: "0 auto" }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Issue #198 · Stage 8 · STEADY (J-E)</span>
        <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[1]}px 0 ${t.space[4]}px` }}>Tổng quan</h1>

        <LockedNav isFirstSession={false} active="home" />

        <div style={{ display: "flex", gap: t.space[2], margin: `${t.space[4]}px 0` }}>
          {[["has_work", "Có việc"], ["all_clear", "Yên tâm (all-clear)"]].map(([k, l]) => (
            <button key={k} onClick={() => setView(k)} style={{ padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, cursor: "pointer", fontFamily: t.font.family, fontSize: t.font.size.sm, fontWeight: t.font.weight.medium, border: `1px solid ${view === k ? t.color.primary : t.color.border}`, background: view === k ? t.color.primarySoft : t.color.surface, color: view === k ? t.color.primary : t.color.inkMuted }}>{l}</button>
          ))}
        </div>

        {/* the single answer to "tôi có cần lo gì không?" */}
        <Card style={clear ? { borderColor: t.color.successBorder, background: t.color.success_soft } : { borderColor: t.color.warningBorder, background: t.color.warning_soft }}>
          <div style={{ display: "flex", alignItems: "center", gap: t.space[3] }}>
            <span style={{ fontSize: 28 }}>{clear ? "🌿" : "👀"}</span>
            <div>
              <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink, letterSpacing: t.font.tracking.snug }}>
                {clear ? "Mọi thứ trong tầm kiểm soát." : "Có 2 việc cần chú ý tuần này."}
              </div>
              <div style={{ fontSize: t.font.size.base, color: t.color.inkBody, marginTop: 2 }}>
                {clear ? "Hạn gần nhất còn 23 ngày — Khế sẽ nhắc trước." : "Gần nhất: gia hạn mặt bằng Q7 — còn 7 ngày."}
              </div>
            </div>
          </div>
          {!clear && <div style={{ marginTop: t.space[4] }}><Button>Xem việc cần làm</Button></div>}
        </Card>

        {/* legitimate-reassurance footing: real counts, scoped */}
        <div style={{ display: "flex", gap: t.space[3], marginTop: t.space[4], flexWrap: "wrap" }}>
          <Stat n={clear ? 0 : 2} label="Sắp tới hạn" tone={clear ? t.color.success : t.color.warning} />
          <Stat n={1} label="Quyền lợi cần đòi" tone={t.color.info} />
          <Stat n={12} label="Hợp đồng đang theo dõi" tone={t.color.ink} />
        </div>

        {/* honest scope reminder — never "đã được bảo vệ toàn kho" */}
        <div style={{ marginTop: t.space[4] }}>
          <ScopeCard contractName="12 hợp đồng" onAddMore={() => {}} />
        </div>
      </div>
    </div>
  );
}
