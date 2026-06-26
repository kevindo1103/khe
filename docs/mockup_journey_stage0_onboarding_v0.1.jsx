/**
 * Khế — Journey · Stage 0 Onboarding  (mockup_journey_stage0_onboarding_v0.1.jsx)
 * KHE_Designer · issue #198 Phase B · builds on Design System v0.2 + journey primitives v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Stage 0 = first login. TWO cold-starts (brief #198):
 *   (A) Concierge (DEC-012): tenant lands at NEEDS_REVIEW — data PRE-FILLED by the
 *       firm operator, user self-confirms (D-02 Option B, Kevin-ratified). NOT empty.
 *   (B) Self-serve: genuinely empty → ONE big CTA, nav locked (Hick's law).
 *
 * Single app (PWA discontinued, chat folded into Admin) — mobile-first frame.
 */
import React, { useState } from "react";
import { tokens as t, Button, Card } from "./mockup_design_system_v0.2.jsx";
import { LockedNav, JourneyEmptyState, ConciergeWelcome, SetupProgress } from "./mockup_journey_primitives_v0.1.jsx";

function Device({ children }) {
  return (
    <div style={{ width: 390, border: `1px solid ${t.color.border}`, borderRadius: t.radius.xl, overflow: "hidden", background: t.color.surfaceAlt, boxShadow: t.elevation.e2 }}>
      <div style={{ padding: `${t.space[2]}px ${t.space[4]}px`, background: t.color.surface, borderBottom: `1px solid ${t.color.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontWeight: t.font.weight.bold, color: t.color.primary, fontFamily: t.font.family }}>Khế</span>
        <span style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, fontFamily: t.font.family }}>Anh Dũng</span>
      </div>
      <div style={{ padding: t.space[4], display: "flex", flexDirection: "column", gap: t.space[4] }}>{children}</div>
    </div>
  );
}

export default function Stage0Onboarding() {
  const [tab, setTab] = useState("concierge");
  return (
    <div style={{ background: t.color.surfaceAlt, minHeight: "100vh", padding: t.space[8], fontFamily: t.font.family }}>
      <header style={{ marginBottom: t.space[7], maxWidth: 720 }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Issue #198 · Stage 0</span>
        <div style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, marginTop: t.space[1] }}>Mới sử dụng — first login</div>
        <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, marginTop: t.space[2], lineHeight: t.font.lineHeight.relaxed }}>
          Hai cold-start tách biệt: concierge (đã có data, NEEDS_REVIEW) vs self-serve (rỗng, 1 CTA, nav khoá).
        </p>
        <div style={{ display: "flex", gap: t.space[2], marginTop: t.space[4] }}>
          {[["concierge", "A · Concierge (DEC-012)"], ["self", "B · Self-serve (rỗng)"]].map(([k, l]) => (
            <button key={k} onClick={() => setTab(k)} style={{
              padding: `${t.space[2]}px ${t.space[4]}px`, borderRadius: t.radius.md, cursor: "pointer", fontFamily: t.font.family,
              fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold,
              background: tab === k ? t.color.primary : t.color.surface, color: tab === k ? "#fff" : t.color.inkBody,
              border: `1px solid ${tab === k ? "transparent" : t.color.border}`,
            }}>{l}</button>
          ))}
        </div>
      </header>

      {tab === "concierge" ? (
        <Device>
          {/* concierge: full nav (data exists) + pre-filled welcome → self-confirm */}
          <LockedNav isFirstSession={false} active="home" />
          <ConciergeWelcome
            firmName="Đại lý thuế Chị Hằng" docCount={3} oblCount={7}
            nearest={{ label: "gia hạn mặt bằng Q7", days: 23 }}
          />
          <Card title="Còn lại để hoàn tất">
            <SetupProgress steps={[
              { label: "Hợp đồng đã được tải (Chị Hằng)", done: true },
              { label: "Kiểm tra & xác nhận thông tin", done: false },
              { label: "Bật nhắc (Telegram/email)", done: false },
            ]} />
          </Card>
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, textAlign: "center" }}>
            D-02: Chị Hằng chỉ chuẩn bị sẵn — bạn là người xác nhận cuối.
          </div>
        </Device>
      ) : (
        <Device>
          {/* self-serve: nav LOCKED to focus the one onboarding action (first session) */}
          <LockedNav isFirstSession active="home" />
          <div style={{ textAlign: "center", padding: `${t.space[6]}px ${t.space[2]}px` }}>
            <div style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.snug }}>
              Chào anh Dũng 👋
            </div>
            <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, marginTop: t.space[2], lineHeight: t.font.lineHeight.relaxed }}>
              Tải hợp đồng đầu tiên lên — Khế tự đọc, bóc hạn và nhắc bạn trước khi tới hạn.
            </p>
          </div>
          {/* exactly ONE primary action (Hick's law) */}
          <JourneyEmptyState state="cold_start" onUpload={() => {}} />
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, textAlign: "center" }}>
            Chưa có gì khác để làm — các mục khác mở sau khi bạn tải hợp đồng đầu tiên.
          </div>
        </Device>
      )}
    </div>
  );
}
