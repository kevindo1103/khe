/**
 * Khế — Firm Journey · F5 Steady/digest + F6 Consent lifecycle  (mockup_firm_stage_F5_F6_v0.1.jsx)
 * KHE_Designer · issue #236 (DEC-039) · DS v0.2 + firm primitives v0.1 + FirmShell
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Inherits #206 a11y. Desktop-first.
 *
 * F5 — Steady state / monthly digest (J5): summary ("Tháng này: N client có hạn,
 *   M khẩn cấp"), monthly digest card (in-app + EMAIL toggle — firm digest = email-only
 *   MVP per PM #4; Telegram = SME-only DEC-006). all-clear legitimate ONLY when truly clear.
 * F6 — Consent lifecycle (cross-cutting): RevokeBanner transition (D-10 instant vanish,
 *   no cache, in-flight → 404, auto-fade per PM #1) + Settings panel listing active
 *   consents (grant date + status). NO firm-side revoke — SME is data owner (PM #9 / D-10).
 * Read-only (D-09). Backend: GET /firm/lead-signals digest · DELETE /consent/firm-access/{id} (#237).
 */
import React, { useState } from "react";
import { tokens as t, Button, Badge, LiveRegion } from "./mockup_design_system_v0.2.jsx";
import { RevokeBanner, ConsentStatus, FirmEmptyState } from "./mockup_firm_journey_primitives_v0.1.jsx";
import { FirmShell } from "./mockup_firm_stage_F0_F1_v0.1.jsx";

/* ---- F5 digest ---- */
function StatCard({ n, label, accent }) {
  return (
    <div style={{ flex: 1, background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, padding: t.space[5], boxShadow: t.elevation.e1 }}>
      <div style={{ fontSize: t.font.size["4xl"], fontWeight: t.font.weight.bold, color: accent || t.color.ink, letterSpacing: t.font.tracking.tight, lineHeight: 1.1 }}>{n}</div>
      <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>{label}</div>
    </div>
  );
}

function Digest({ allClear }) {
  const [email, setEmail] = useState(true);
  return (
    <div style={{ maxWidth: 720 }}>
      <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: 0 }}>Tổng quan tháng 7</h1>
      <LiveRegion style={{ fontSize: t.font.size.base, color: t.color.inkBody, margin: `${t.space[2]}px 0 ${t.space[5]}px` }}>
        {allClear ? "Tháng này không có hạn khẩn cấp. ✅" : <>Tháng này: <strong>8 client</strong> có hạn, <strong style={{ color: t.color.danger }}>3 khẩn cấp</strong>.</>}
      </LiveRegion>

      {allClear ? (
        <div style={{ background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg }}>
          <FirmEmptyState state="all_clear" />
        </div>
      ) : (
        <>
          <div style={{ display: "flex", gap: t.space[4], marginBottom: t.space[5] }}>
            <StatCard n={8} label="Client có hạn tháng này" />
            <StatCard n={3} label="Khẩn cấp (≤7 ngày)" accent={t.color.danger} />
            <StatCard n={5} label="Cần liên hệ tư vấn" accent={t.color.primary} />
          </div>
          <div style={{ background: t.color.primarySoft, border: `1px solid ${t.color.primaryBorder}`, borderRadius: t.radius.lg, padding: t.space[5] }}>
            <div style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, color: t.color.ink }}>📨 Bản tin tháng 7 — 5 client cần liên hệ</div>
            <p style={{ fontSize: t.font.size.sm, color: t.color.inkBody, margin: `${t.space[2]}px 0`, lineHeight: t.font.lineHeight.relaxed }}>
              Anh Dũng (2 hạn) · Chị Mai · Cô Lan · Anh Phúc · Chị Thu — chủ động gọi trước khi tới hạn để giữ uy tín & bán thêm dịch vụ.
            </p>
            <Button size="sm">Xem chi tiết cảnh báo</Button>
          </div>
        </>
      )}

      {/* digest channel — email only (firm), MVP */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: t.space[6], padding: t.space[4], background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg }}>
        <span>
          <span style={{ display: "block", fontSize: t.font.size.base, fontWeight: t.font.weight.medium, color: t.color.ink }}>Bản tin email hàng tuần</span>
          <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: 2 }}>Gửi tới hang@minhhang.vn · firm dùng email (Telegram chỉ cho SME).</span>
        </span>
        <button type="button" role="switch" aria-checked={email} aria-label="Bản tin email hàng tuần" onClick={() => setEmail((v) => !v)} style={{
          width: 44, height: 26, borderRadius: 999, border: "none", cursor: "pointer", position: "relative",
          background: email ? t.color.primary : t.color.neutral[300], transition: `background ${t.motion.fast} ${t.motion.ease}`,
        }}>
          <span aria-hidden="true" style={{ position: "absolute", top: 3, left: email ? 21 : 3, width: 20, height: 20, borderRadius: "50%", background: "#fff", transition: `left ${t.motion.fast} ${t.motion.ease}` }} />
        </button>
      </div>
    </div>
  );
}

/* ---- F6 consent settings ---- */
const CONSENTS = [
  { name: "Anh Dũng — Nhà hàng Phở Bắc", since: "12/05/2026", status: "granted" },
  { name: "Chị Mai — Tạp hoá Mai", since: "03/06/2026", status: "granted" },
  { name: "Cô Lan — Xưởng may Lan", since: "20/06/2026", status: "granted" },
  { name: "Anh Phúc — Cà phê Phúc", since: "—", status: "pending" },
];
function ConsentSettings({ revoked }) {
  const [showBanner, setShowBanner] = useState(revoked);
  return (
    <div style={{ maxWidth: 720 }}>
      <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `0 0 ${t.space[4]}px` }}>Quyền truy cập client</h1>

      {revoked && showBanner && <div style={{ marginBottom: t.space[4] }}><RevokeBanner clientName="Anh Dũng — Nhà hàng Phở Bắc" onDismiss={() => setShowBanner(false)} /></div>}

      <div style={{ background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden", boxShadow: t.elevation.e1 }}>
        {CONSENTS.filter((c) => !(revoked && c.name.startsWith("Anh Dũng"))).map((c, i, arr) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: t.space[3], padding: `${t.space[3]}px ${t.space[4]}px`, borderBottom: i < arr.length - 1 ? `1px solid ${t.color.border}` : "none" }}>
            <span style={{ flex: 1, minWidth: 0 }}>
              <span style={{ display: "block", fontSize: t.font.size.base, color: t.color.ink, fontWeight: t.font.weight.medium }}>{c.name}</span>
              <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkMuted }}>{c.status === "granted" ? `Đồng ý từ ${c.since}` : "Đang chờ xác nhận"}</span>
            </span>
            <ConsentStatus status={c.status} />
          </div>
        ))}
      </div>

      {/* D-10 / PM #9: firm CANNOT revoke — only the SME (data owner) can */}
      <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[4], lineHeight: t.font.lineHeight.relaxed, display: "flex", gap: t.space[2] }}>
        <span aria-hidden="true">🔒</span>
        <span>Chỉ <strong>client</strong> mới có thể thu hồi quyền truy cập (họ là chủ dữ liệu). Khi thu hồi, dữ liệu của client biến mất ngay và không được lưu lại. Bạn không thể tự gỡ — nếu muốn dừng, đề nghị client thu hồi.</span>
      </p>
    </div>
  );
}

/* ============================================================================
 * SHOWCASE
 * ========================================================================== */
const SCREENS = [
  { key: "digest", label: "F5 · Digest (có việc)", nav: "signals" },
  { key: "digest_clear", label: "F5 · All-clear", nav: "signals" },
  { key: "settings", label: "F6 · Quyền truy cập", nav: "settings" },
  { key: "revoke", label: "F6 · Vừa bị thu hồi", nav: "settings" },
];
export default function FirmF5F6Showcase() {
  const [screen, setScreen] = useState("digest");
  const cur = SCREENS.find((s) => s.key === screen);
  return (
    <div style={{ background: t.color.surfaceAlt, minHeight: "100vh", padding: t.space[7], fontFamily: t.font.family }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Firm journey · F5–F6</div>
        <div style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[1]}px 0 ${t.space[4]}px` }}>Steady-state digest + consent lifecycle</div>
        <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginBottom: t.space[5] }}>
          {SCREENS.map((s) => (
            <button key={s.key} type="button" onClick={() => setScreen(s.key)} style={{
              padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, cursor: "pointer", fontFamily: t.font.family,
              fontSize: t.font.size.sm, border: `1px solid ${screen === s.key ? t.color.primary : t.color.border}`,
              background: screen === s.key ? t.color.primarySoft : t.color.surface, color: screen === s.key ? t.color.primary : t.color.inkMuted,
            }}>{s.label}</button>
          ))}
        </div>

        <FirmShell active={cur.nav}>
          {screen === "digest" && <Digest />}
          {screen === "digest_clear" && <Digest allClear />}
          {screen === "settings" && <ConsentSettings />}
          {screen === "revoke" && <ConsentSettings revoked />}
        </FirmShell>
      </div>
    </div>
  );
}
