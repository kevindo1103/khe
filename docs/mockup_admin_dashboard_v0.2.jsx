/**
 * Khế — Admin · Dashboard "Tổng quan" v0.2  (mockup_admin_dashboard_v0.2.jsx)
 * KHE_Designer · NEW canonical screen (formalizes the responsive preview) · DS v0.2
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * RESPONSIVE app shell — adopts the real nav components from #204:
 *   • ≥760px → AppSidebar (desktop)            • <760px → AppMobileHeader + AppBottomTabs
 * Switch via injected <style> media queries (inline-style mockups can't do @media).
 *
 * Content = SME home answering "cần lo gì?":
 *   • reassurance headline (legitimate-only, aria-live) — numbers match the cards (#198).
 *   • DIRECTION cards = #199 summary.groups[] (nghĩa_vụ/quyền_lợi/null) → SUM to total.
 *   • STATUS strip = #199 summary.status_breakdown → CROSS-CUTS direction (separate, not a card).
 *   • source chip = provenance (primary) · ScopeCard = honest scope (info), no overpromise.
 * (See DASHBOARD CONSUMER RULE in mockup_journey_stage6_chat header.)
 *
 * DEC-040 (#238 ratify): nav-lock = first-session + pre-CONFIRMED only; is_first_session
 *   clears at CONFIRMED (NOT ACTIVATED). Option (B) means a tenant can reach CONFIRMED /
 *   steady WITHOUT a reminder channel → "silent product failure". MANDATORY mitigation:
 *   the CONFIRMED-without-channel dashboard shows a prominent ReminderNudge (#198 primitive)
 *   + a "2/3 bước" progress chip (doc reviewed ✅ · nhắc Telegram ⬜ · steady ⬜). Toggle the
 *   showcase between this state and full steady-state.
 */
import React, { useState } from "react";
import { tokens as t } from "./mockup_design_system_v0.2.jsx";
import { AppSidebar, AppBottomTabs, AppMobileHeader } from "./mockup_app_nav_v0.2.jsx";
import { ReminderNudge } from "./mockup_journey_primitives_v0.1.jsx";

const GROUPS = [
  { key: "nghĩa_vụ", label: "Bạn cần", count: 4, dot: t.color.primary, near: "Gần nhất: gia hạn mặt bằng Q7", pill: "còn 23 ngày" },
  { key: "quyền_lợi", label: "Đối tác cần làm cho bạn", count: 2, dot: t.color.info, near: "Cty Bao Bì Việt giao hàng đợt 2" },
  { key: "null", label: "Cần xác nhận", count: 1, dot: t.color.warning, near: "1 nghĩa vụ chưa rõ bên →", link: true },
];
const STATUS = [["🔥", "Sắp tới", 3], ["⏳", "Chờ sự kiện", 1], ["✅", "Quá hạn", 0]];
const UPCOMING = [
  { dir: "Bạn cần", dk: t.color.primary, dbg: t.color.primarySoft, dbd: t.color.primaryBorder, title: "Gia hạn / chấm dứt HĐ thuê mặt bằng Q7", sub: "HĐ thuê mặt bằng Q7 · Điều 3", chip: "còn 23 ngày", ck: "due" },
  { dir: "Bạn cần", dk: t.color.primary, dbg: t.color.primarySoft, dbd: t.color.primaryBorder, title: "Thanh toán đợt 2/3 — bao bì", sub: "HĐ cung cấp bao bì · Cty CP Bao Bì Việt", chip: "còn 8 ngày", ck: "due" },
  { dir: "Đối tác", dk: t.color.info, dbg: t.color.info_soft, dbd: t.color.infoBorder, title: "Cty Bao Bì Việt giao hàng đợt 2", sub: "Quyền lợi của bạn", chip: "đúng hạn", ck: "ok" },
];

const CSS = `
.khe-shell{display:flex;min-height:100vh;background:${t.color.surfaceAlt};font-family:${t.font.family};}
.khe-desk-nav{display:block;}
.khe-mob-top,.khe-mob-tabs{display:none;}
.khe-main{flex:1;min-width:0;display:flex;flex-direction:column;}
.khe-content{flex:1;width:100%;max-width:920px;margin:0 auto;padding:32px;}
.khe-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
@media (max-width:760px){
  .khe-desk-nav{display:none;}
  .khe-mob-top{display:flex;}
  .khe-mob-tabs{display:block;position:sticky;bottom:0;}
  .khe-content{padding:16px 16px 24px;}
  .khe-cards{grid-template-columns:1fr;}
}`;

function Card({ g }) {
  return (
    <div style={{ background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, padding: t.space[5], boxShadow: t.elevation.e1 }}>
      <div style={{ display: "flex", alignItems: "center", gap: t.space[2], fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.inkMuted }}>
        <span aria-hidden="true" style={{ width: 8, height: 8, borderRadius: "50%", background: g.dot }} />{g.label}
      </div>
      <div style={{ fontSize: t.font.size["4xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, marginTop: t.space[2] }}>{g.count}</div>
      <div style={{ marginTop: t.space[2], fontSize: t.font.size.sm, color: t.color.inkBody }}>
        {g.link ? <a href="#" style={{ color: t.color.primary }}>{g.near}</a> : g.near}
        {g.pill && <span style={{ marginLeft: 4, fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill, background: t.color.warning_soft, color: t.color.warning, border: `1px solid ${t.color.warningBorder}` }}>{g.pill}</span>}
      </div>
    </div>
  );
}

/* "2/3 bước" onboarding progress — visible forward motion at CONFIRMED-without-channel (DEC-040). */
function ProgressChip() {
  const steps = [["Đã duyệt tài liệu", true], ["Bật nhắc Telegram", false], ["Theo dõi tự động", false]];
  const done = steps.filter(([, d]) => d).length;
  return (
    <div role="group" aria-label={`Tiến độ thiết lập ${done}/${steps.length} bước`} style={{ display: "inline-flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap", padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, background: t.color.surfaceSunken, border: `1px solid ${t.color.border}` }}>
      <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.bold, color: t.color.ink }}>{done}/{steps.length} bước</span>
      {steps.map(([label, d], i) => (
        <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: t.font.size.xs, color: d ? t.color.success : t.color.inkMuted }}>
          <span aria-hidden="true">{d ? "✅" : "⬜"}</span>{label}
        </span>
      ))}
    </div>
  );
}

export default function AdminDashboardV2() {
  const [hasChannel, setHasChannel] = useState(false); // false = CONFIRMED-without-channel (DEC-040 mandatory state)
  return (
    <div className="khe-shell">
      <style>{CSS}</style>

      <div className="khe-desk-nav"><AppSidebar active="home" /></div>

      <div className="khe-main">
        <div className="khe-mob-top"><AppMobileHeader /></div>

        {/* showcase toggle (not part of the screen) */}
        <div style={{ display: "flex", gap: t.space[2], padding: `${t.space[2]}px ${t.space[6]}px`, borderBottom: `1px solid ${t.color.border}`, background: t.color.surfaceSunken, alignItems: "center" }}>
          <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>State:</span>
          {[["Chưa bật nhắc (CONFIRMED)", false], ["Steady (đã bật nhắc)", true]].map(([lbl, v]) => (
            <button key={String(v)} type="button" onClick={() => setHasChannel(v)} style={{ fontSize: t.font.size.xs, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill, cursor: "pointer", fontFamily: t.font.family, border: `1px solid ${hasChannel === v ? t.color.primary : t.color.border}`, background: hasChannel === v ? t.color.primarySoft : t.color.surface, color: hasChannel === v ? t.color.primary : t.color.inkMuted }}>{lbl}</button>
          ))}
        </div>

        <main className="khe-content">
          <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, fontWeight: t.font.weight.medium, margin: 0 }}>Chào buổi sáng, Anh Dũng 👋</p>
          <h1 style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[1]}px 0 0` }}>Tổng quan</h1>

          {/* DEC-040 MANDATORY: CONFIRMED-without-channel → ReminderNudge + 2/3 progress (silent-failure guard) */}
          {!hasChannel && (
            <div style={{ display: "flex", flexDirection: "column", gap: t.space[3], margin: `${t.space[4]}px 0` }}>
              <ProgressChip />
              <ReminderNudge onEnable={() => setHasChannel(true)} />
            </div>
          )}
          {/* legitimate reassurance only; numbers match cards */}
          <p aria-live="polite" style={{ marginTop: t.space[2], fontSize: t.font.size.md, color: t.color.inkBody, lineHeight: t.font.lineHeight.relaxed }}>
            Bạn đang theo dõi <strong style={{ color: t.color.ink }}>7 nghĩa vụ</strong>. Việc gần nhất bạn cần lo: <strong style={{ color: t.color.ink }}>gia hạn mặt bằng Q7</strong> — còn 23 ngày.
          </p>

          {/* DIRECTION cards = summary.groups[] (sum=7) */}
          <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.inkMuted, margin: `${t.space[6]}px 0 ${t.space[3]}px` }}>Nghĩa vụ — theo hướng</div>
          <section className="khe-cards" aria-label="Nghĩa vụ theo hướng">
            {GROUPS.map((g) => <Card key={g.key} g={g} />)}
          </section>

          <span style={{ display: "inline-flex", alignItems: "center", gap: 6, marginTop: t.space[3], fontSize: t.font.size.xs, color: t.color.primary, background: t.color.primarySoft, border: `1px solid ${t.color.primaryBorder}`, padding: `2px ${t.space[3]}px`, borderRadius: t.radius.pill }}>📄 Nguồn: 7 nghĩa vụ · 3 hợp đồng</span>

          {/* STATUS strip = summary.status_breakdown (cross-cuts direction; NOT added to the 7) */}
          <div role="group" aria-label="Theo trạng thái" style={{ display: "flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap", marginTop: t.space[4], fontSize: t.font.size.sm, color: t.color.inkMuted }}>
            {STATUS.map(([ic, lbl, n], i) => (
              <React.Fragment key={lbl}>
                {i > 0 && <span aria-hidden="true" style={{ color: t.color.inkSubtle }}>·</span>}
                <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}><span aria-hidden="true">{ic}</span>{lbl} <b style={{ color: t.color.ink }}>{n}</b></span>
              </React.Fragment>
            ))}
          </div>

          {/* upcoming */}
          <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.inkMuted, margin: `${t.space[6]}px 0 ${t.space[3]}px` }}>Sắp tới</div>
          <div style={{ background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden", boxShadow: t.elevation.e1 }}>
            {UPCOMING.map((o, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: t.space[3], padding: `${t.space[3]}px ${t.space[4]}px`, borderBottom: i < UPCOMING.length - 1 ? `1px solid ${t.color.border}` : "none" }}>
                <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill, background: o.dbg, color: o.dk, border: `1px solid ${o.dbd}`, whiteSpace: "nowrap" }}>{o.dir}</span>
                <span style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ display: "block", fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{o.title}</span>
                  <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: 2 }}>{o.sub}</span>
                </span>
                <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill, whiteSpace: "nowrap",
                  background: o.ck === "ok" ? t.color.success_soft : t.color.warning_soft, color: o.ck === "ok" ? t.color.success : t.color.warning,
                  border: `1px solid ${o.ck === "ok" ? t.color.successBorder : t.color.warningBorder}` }}>{o.chip}</span>
              </div>
            ))}
          </div>

          {/* ScopeCard — honest scope, no overpromise (#198) */}
          <div style={{ marginTop: t.space[4], display: "flex", alignItems: "center", gap: t.space[3], background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, padding: t.space[4], boxShadow: t.elevation.e1 }}>
            <span aria-hidden="true" style={{ width: 40, height: 40, borderRadius: t.radius.lg, background: t.color.primarySoft, color: t.color.primary, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>🗂️</span>
            <span>
              <span style={{ display: "block", fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>Đang theo dõi 12 hợp đồng</span>
              <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: 2 }}>Khế nhắc các hạn đã bóc tách — không phải toàn bộ rủi ro pháp lý.</span>
            </span>
          </div>
        </main>

        <div className="khe-mob-tabs"><AppBottomTabs active="home" /></div>
      </div>
    </div>
  );
}
