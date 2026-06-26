/**
 * Khế — Journey · Stage 5 Reminder drops (Telegram)  (mockup_journey_stage5_reminder_v0.1.jsx)
 * KHE_Designer · issue #198 Phase C · Design System v0.2
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Stage 5 = ACTIVATION off-app (J2 core). The reminder lands in Telegram with a
 * source line (D-08 spirit: traceable, not a bare alarm) + deep-link + actions
 * "Đã xử lý / Nhắc lại sau". Shows (A) the Telegram message template and
 * (B) the deep-link landing back in-app.
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Badge, Toast } from "./mockup_design_system_v0.2.jsx";

function TelegramBubble() {
  return (
    <div style={{ background: "#E7F2FB", border: "1px solid #CFE5F7", borderRadius: 14, padding: t.space[4], maxWidth: 320, fontFamily: t.font.family }}>
      <div style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.bold, color: "#1B6AA5", marginBottom: t.space[1] }}>Khế Bot</div>
      <div style={{ fontSize: t.font.size.base, color: "#0E141B", lineHeight: t.font.lineHeight.relaxed }}>
        ⏰ <strong>Còn 7 ngày</strong>: gia hạn HĐ thuê mặt bằng Q7 (hết hạn 30/06).
        <div style={{ marginTop: t.space[2], fontSize: t.font.size.sm, color: "#46627A" }}>Nguồn: HĐ thuê mặt bằng 2024 · điều 9</div>
      </div>
      <div style={{ display: "flex", gap: t.space[2], marginTop: t.space[3], flexWrap: "wrap" }}>
        <span style={{ background: "#fff", border: "1px solid #CFE5F7", borderRadius: t.radius.md, padding: `${t.space[1]}px ${t.space[3]}px`, fontSize: t.font.size.sm, color: "#1B6AA5", fontWeight: t.font.weight.semibold }}>✅ Đã xử lý</span>
        <span style={{ background: "#fff", border: "1px solid #CFE5F7", borderRadius: t.radius.md, padding: `${t.space[1]}px ${t.space[3]}px`, fontSize: t.font.size.sm, color: "#1B6AA5", fontWeight: t.font.weight.semibold }}>⏰ Nhắc lại sau</span>
      </div>
      <a href="#" style={{ display: "inline-block", marginTop: t.space[2], fontSize: t.font.size.sm, color: "#1B6AA5" }}>Mở trong Khế →</a>
    </div>
  );
}

export default function Stage5Reminder() {
  const [view, setView] = useState("telegram");
  const [toast, setToast] = useState(null);
  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 680, margin: "0 auto" }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Issue #198 · Stage 5 · ACTIVATION (off-app)</span>
        <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[1]}px 0 0` }}>Nhắc hạn rơi vào Telegram</h1>
        <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, marginTop: t.space[1] }}>Khoảnh khắc giá trị thật (J2). Có nguồn, có deep-link, có hành động.</p>

        <div style={{ display: "flex", gap: t.space[2], margin: `${t.space[5]}px 0` }}>
          {[["telegram", "Tin Telegram"], ["landing", "Deep-link landing"]].map(([k, l]) => (
            <button key={k} onClick={() => setView(k)} style={{ padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, cursor: "pointer", fontFamily: t.font.family, fontSize: t.font.size.sm, fontWeight: t.font.weight.medium, border: `1px solid ${view === k ? t.color.primary : t.color.border}`, background: view === k ? t.color.primarySoft : t.color.surface, color: view === k ? t.color.primary : t.color.inkMuted }}>{l}</button>
          ))}
        </div>

        {view === "telegram" ? (
          <div style={{ padding: t.space[5], background: "#D9E9F5", borderRadius: t.radius.lg }}><TelegramBubble /></div>
        ) : (
          <Card title="HĐ thuê mặt bằng Q7" subtitle="Mở từ nhắc Telegram">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: t.space[2] }}>
              <Badge kind="brand" dot>Bạn cần làm</Badge>
              <Badge kind="due_soon">còn 7 ngày</Badge>
            </div>
            <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink, marginTop: t.space[3] }}>Gia hạn hoặc chấm dứt hợp đồng thuê</div>
            <div style={{ fontSize: t.font.size.base, color: t.color.inkBody, marginTop: t.space[1] }}>Hạn chót 30/06/2026 · điều 9 (báo trước 60 ngày).</div>
            <div style={{ display: "flex", gap: t.space[2], marginTop: t.space[4], flexWrap: "wrap" }}>
              <Button onClick={() => { setToast("Đã đánh dấu xử lý — ghi Event ✓"); setTimeout(() => setToast(null), 2200); }}>Đã xử lý</Button>
              <Button variant="secondary" onClick={() => { setToast("Sẽ nhắc lại sau 3 ngày ✓"); setTimeout(() => setToast(null), 2200); }}>Nhắc lại sau</Button>
              <Button variant="ghost">Xem hợp đồng gốc</Button>
            </div>
          </Card>
        )}
      </div>
      {toast && <div style={{ position: "fixed", bottom: t.space[6], left: "50%", transform: "translateX(-50%)", zIndex: t.z.toast }}><Toast kind="success">{toast}</Toast></div>}
    </div>
  );
}
