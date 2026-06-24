/**
 * Khế — Firm Journey · F0 Onboard + F1 Consent handshake  (mockup_firm_stage_F0_F1_v0.1.jsx)
 * KHE_Designer · issue #236 (DEC-039) · Design System v0.2 + firm primitives v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Inherits #206 a11y. Desktop-first.
 *
 * F0 — Firm onboard (0 clients): honest cold-start + single CTA "Mời client".
 * F1 — Add client + consent handshake (PM B1 — DUAL PATH):
 *   • F1a Concierge (SME chưa có account): business name + email → tạo tenant +
 *     gửi link kích hoạt. Backend: POST /firm/tenants/invite (#237).
 *   • F1b Invite (SME đã có account): tìm email SME → gửi consent request.
 *     Backend: POST /firm/consent-requests (#237). Delivery = email + in-app badge (PM B3).
 *   • Pending state giống nhau sau cả 2 path: ConsentStatus "Chờ xác nhận".
 * Firm KHÔNG thấy data SME cho tới khi granted (D-10). Read-only (D-09).
 *
 * Exports FirmShell (desktop sidebar) — reused by F3/F4 + F5/F6 stage files.
 */
import React, { useState } from "react";
import { tokens as t, Button, Input, Badge, NavItem } from "./mockup_design_system_v0.2.jsx";
import { FirmEmptyState, ConsentStatus } from "./mockup_firm_journey_primitives_v0.1.jsx";

/* ============================================================================
 * FirmShell — desktop sidebar shell for the firm portal (Principle 6).
 * ========================================================================== */
const NAV = [
  { key: "clients", icon: "👥", label: "Khách hàng" },
  { key: "signals", icon: "🔔", label: "Cảnh báo", badge: 5 },
  { key: "settings", icon: "⚙", label: "Cài đặt" },
];
export function FirmShell({ active = "clients", children, headerRight }) {
  return (
    <div style={{ display: "flex", minHeight: 640, background: t.color.surfaceAlt, fontFamily: t.font.family, borderRadius: t.radius.xl, overflow: "hidden", border: `1px solid ${t.color.border}` }}>
      <aside style={{ width: 232, flexShrink: 0, background: t.color.surface, borderRight: `1px solid ${t.color.border}`, display: "flex", flexDirection: "column" }}>
        <div style={{ padding: `${t.space[4]}px ${t.space[5]}px`, display: "flex", alignItems: "center", gap: t.space[2] }}>
          <span style={{ width: 28, height: 28, borderRadius: t.radius.md, background: t.color.primary, color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: t.font.weight.bold }}>K</span>
          <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.bold, color: t.color.ink }}>Khế · Đối tác</span>
        </div>
        <nav aria-label="Điều hướng cổng đối tác" style={{ flex: 1, padding: `${t.space[2]}px ${t.space[3]}px` }}>
          {NAV.map((n) => <NavItem key={n.key} icon={n.icon} label={n.label} href="#" active={active === n.key} badge={n.badge} />)}
        </nav>
        <div style={{ borderTop: `1px solid ${t.color.border}`, padding: t.space[3], display: "flex", alignItems: "center", gap: t.space[2] }}>
          <span style={{ width: 28, height: 28, borderRadius: "50%", background: t.color.surfaceSunken, border: `1px solid ${t.color.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: t.font.size.sm, color: t.color.inkMuted }} aria-hidden="true">H</span>
          <span style={{ minWidth: 0 }}>
            <span style={{ display: "block", fontSize: t.font.size.sm, fontWeight: t.font.weight.medium, color: t.color.ink }}>Chị Hằng</span>
            <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkSubtle, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>Đại lý thuế Minh Hằng</span>
          </span>
        </div>
      </aside>
      <main style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        {headerRight !== undefined && (
          <div style={{ display: "flex", justifyContent: "flex-end", padding: `${t.space[3]}px ${t.space[5]}px`, borderBottom: `1px solid ${t.color.border}`, background: t.color.surface }}>{headerRight}</div>
        )}
        <div style={{ flex: 1, overflowY: "auto", padding: t.space[6] }}>{children}</div>
      </main>
    </div>
  );
}

function H1({ children, sub }) {
  return (
    <div style={{ marginBottom: t.space[5] }}>
      <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: 0 }}>{children}</h1>
      {sub && <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, margin: `${t.space[1]}px 0 0` }}>{sub}</p>}
    </div>
  );
}

/* ---- F1 invite form (dual path) ---- */
function InviteForm({ path, onSent }) {
  const concierge = path === "concierge";
  return (
    <div style={{ maxWidth: 460 }}>
      <H1 sub={concierge
        ? "Client chưa có tài khoản Khế — Khế tạo giúp rồi gửi link kích hoạt + yêu cầu đồng ý."
        : "Client đã dùng Khế — gửi yêu cầu truy cập để họ đồng ý chia sẻ."}>
        {concierge ? "Số hoá giúp client" : "Mời client đã có Khế"}
      </H1>
      <div style={{ display: "flex", flexDirection: "column", gap: t.space[4], background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, padding: t.space[5], boxShadow: t.elevation.e1 }}>
        {concierge && <Input label="Tên doanh nghiệp client" value="Nhà hàng Phở Bắc" onChange={() => {}} />}
        <Input label="Email client" type="email" value={concierge ? "dung@phobac.vn" : ""} placeholder="email@congty.vn" onChange={() => {}}
          hint={concierge ? "Khế gửi link kích hoạt + yêu cầu đồng ý tới email này." : "Phải là email client đã đăng ký Khế."} />
        <Button onClick={onSent}>{concierge ? "Tạo & gửi link kích hoạt" : "Gửi yêu cầu truy cập"}</Button>
      </div>
      <p style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: t.space[3] }}>
        🔒 Bạn chỉ thấy dữ liệu sau khi client đồng ý. Client có thể thu hồi bất cứ lúc nào (D-10).
      </p>
    </div>
  );
}

function SentConfirm({ concierge }) {
  return (
    <div style={{ maxWidth: 460, textAlign: "center", padding: `${t.space[8]}px 0` }}>
      <div style={{ fontSize: 44 }} aria-hidden="true">📨</div>
      <h1 style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.bold, color: t.color.ink, margin: `${t.space[3]}px 0 ${t.space[2]}px` }}>
        {concierge ? "Đã gửi link kích hoạt đến client" : "Đã gửi yêu cầu truy cập"}
      </h1>
      <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, lineHeight: t.font.lineHeight.relaxed }}>
        {concierge
          ? "Client bấm link trong email để đặt mật khẩu và đồng ý chia sẻ. Bạn sẽ thấy hồ sơ khi họ hoàn tất."
          : "Client sẽ thấy yêu cầu qua email và trên ứng dụng. Bạn sẽ thấy hồ sơ khi họ đồng ý."}
      </p>
      <div style={{ marginTop: t.space[4] }}><ConsentStatus status="pending" /></div>
    </div>
  );
}

/* ---- F1 pending list ---- */
const PENDING = [
  { name: "Nhà hàng Phở Bắc", email: "dung@phobac.vn", path: "Đã gửi link kích hoạt", at: "hôm nay" },
  { name: "Tạp hoá Mai", email: "mai@example.vn", path: "Đã gửi yêu cầu", at: "2 ngày trước" },
];
function PendingList() {
  return (
    <div style={{ maxWidth: 620 }}>
      <H1 sub="Bạn chưa thấy dữ liệu cho tới khi client đồng ý.">Đang chờ client xác nhận</H1>
      <div style={{ background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden", boxShadow: t.elevation.e1 }}>
        {PENDING.map((p, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: t.space[3], padding: `${t.space[3]}px ${t.space[4]}px`, borderBottom: i < PENDING.length - 1 ? `1px solid ${t.color.border}` : "none" }}>
            <span style={{ flex: 1, minWidth: 0 }}>
              <span style={{ display: "block", fontSize: t.font.size.base, fontWeight: t.font.weight.medium, color: t.color.ink }}>{p.name}</span>
              <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkMuted }}>{p.email} · {p.path} · {p.at}</span>
            </span>
            <ConsentStatus status="pending" />
          </div>
        ))}
      </div>
    </div>
  );
}

/* ============================================================================
 * SHOWCASE — F0 + F1 (dual path) states.
 * ========================================================================== */
const SCREENS = [
  { key: "F0", label: "F0 · Onboard (0 client)" },
  { key: "F1a", label: "F1a · Concierge" },
  { key: "F1b", label: "F1b · Invite" },
  { key: "sent", label: "F1 · Đã gửi" },
  { key: "pending", label: "F1 · Đang chờ" },
];
export default function FirmF0F1Showcase() {
  const [screen, setScreen] = useState("F0");
  return (
    <div style={{ background: t.color.surfaceAlt, minHeight: "100vh", padding: t.space[7], fontFamily: t.font.family }}>
      <div style={{ maxWidth: 1040, margin: "0 auto" }}>
        <div style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Firm journey · F0–F1</div>
        <div style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[1]}px 0 ${t.space[4]}px` }}>Onboard + consent handshake</div>
        <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginBottom: t.space[5] }}>
          {SCREENS.map((s) => (
            <button key={s.key} type="button" onClick={() => setScreen(s.key)} style={{
              padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, cursor: "pointer", fontFamily: t.font.family,
              fontSize: t.font.size.sm, border: `1px solid ${screen === s.key ? t.color.primary : t.color.border}`,
              background: screen === s.key ? t.color.primarySoft : t.color.surface, color: screen === s.key ? t.color.primary : t.color.inkMuted,
            }}>{s.label}</button>
          ))}
        </div>

        <FirmShell active="clients" headerRight={screen !== "F0" && <Button size="sm">+ Mời client</Button>}>
          {screen === "F0" && <FirmEmptyState state="cold_start" onInvite={() => setScreen("F1a")} />}
          {screen === "F1a" && <InviteForm path="concierge" onSent={() => setScreen("sent")} />}
          {screen === "F1b" && <InviteForm path="invite" onSent={() => setScreen("sent")} />}
          {screen === "sent" && <SentConfirm concierge />}
          {screen === "pending" && <PendingList />}
        </FirmShell>
      </div>
    </div>
  );
}
