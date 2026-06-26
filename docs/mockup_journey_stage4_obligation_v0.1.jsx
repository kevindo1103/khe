/**
 * Khế — Journey · Stage 4 Obligation appears (AHA)  (mockup_journey_stage4_obligation_v0.1.jsx)
 * KHE_Designer · issue #198 Phase C · Design System v0.2 + journey primitives v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Stage 4 = the AHA moment (CONFIRMED → ACTIVATED). The first obligation card,
 * DEC-030 4-axis humanised into plain language:
 *   GÌ · KHI (còn N ngày + ngày) · NGUỒN (HĐ + điều khoản) · HƯỚNG (bạn làm / bạn nhận) · LẶP
 * First-time coaching overlay + Telegram bridge (DEC-006). ACTIVATED gate = ≥1
 * channel (Telegram OR email); skip both → CONFIRMED + ReminderNudge (no block).
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Badge, Modal, Toast } from "./mockup_design_system_v0.2.jsx";
import { ReminderNudge } from "./mockup_journey_primitives_v0.1.jsx";

function ObligationCard({ coaching }) {
  return (
    <div style={{ position: "relative" }}>
      <Card interactive>
        {/* HƯỚNG */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: t.space[2] }}>
          <Badge kind="brand" dot>Bạn cần làm</Badge>
          <Badge kind="due_soon">còn 23 ngày</Badge>
        </div>
        {/* GÌ */}
        <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink, marginTop: t.space[3], letterSpacing: t.font.tracking.snug }}>
          Gia hạn hoặc chấm dứt hợp đồng thuê
        </div>
        {/* KHI */}
        <div style={{ fontSize: t.font.size.base, color: t.color.inkBody, marginTop: t.space[1] }}>
          Hạn chót: <strong>01/08/2026</strong> (báo trước 60 ngày trước khi HĐ hết hạn 30/09/2026).
        </div>
        {/* NGUỒN */}
        <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[3], display: "flex", gap: t.space[2], flexWrap: "wrap", alignItems: "center" }}>
          <a href="#" style={{ color: t.color.primary, textDecoration: "none", background: t.color.primarySoft, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill }}>📄 HĐ thuê mặt bằng Q7 · điều 9</a>
          <Badge kind="neutral">🔁 không lặp</Badge>
        </div>
      </Card>

      {coaching && (
        <div style={{ position: "absolute", inset: 0, borderRadius: t.radius.lg, boxShadow: `0 0 0 3px ${t.color.ring}`, pointerEvents: "none" }}>
          <div style={{ position: "absolute", top: -10, right: t.space[4], background: t.color.ink, color: "#fff", fontSize: t.font.size.xs, padding: `${t.space[1]}px ${t.space[2]}px`, borderRadius: t.radius.sm, fontFamily: t.font.family }}>
            Đây là nghĩa vụ đầu tiên Khế tìm ra ✨
          </div>
        </div>
      )}
    </div>
  );
}

export default function Stage4Obligation() {
  const [coaching, setCoaching] = useState(true);
  const [bridge, setBridge] = useState(false);
  const [channel, setChannel] = useState(null); // null | telegram | email
  const [toast, setToast] = useState(null);

  const enable = (c) => { setChannel(c); setBridge(false); setToast(c === "telegram" ? "Đã bật nhắc Telegram — bạn đã sẵn sàng ✓" : "Đã bật nhắc qua email ✓"); setTimeout(() => setToast(null), 2800); };

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 640, margin: "0 auto", display: "flex", flexDirection: "column", gap: t.space[5] }}>
        <div>
          <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Issue #198 · Stage 4 · CONFIRMED → ACTIVATED</span>
          <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[1]}px 0 0` }}>Khế tìm ra nghĩa vụ đầu tiên</h1>
        </div>

        <ObligationCard coaching={coaching} />
        {coaching && <Button variant="ghost" onClick={() => setCoaching(false)}>Đã hiểu</Button>}

        {/* Telegram bridge OR persistent nudge if not yet enabled */}
        {channel ? (
          <Card><div style={{ display: "flex", alignItems: "center", gap: t.space[2] }}><Badge kind="done" dot>Đã bật nhắc qua {channel === "telegram" ? "Telegram" : "email"}</Badge><span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>Khế sẽ nhắc trước 30 & 7 ngày.</span></div></Card>
        ) : (
          <>
            <Card title="Nhận nhắc trước khi tới hạn?" subtitle="DEC-006 — Telegram (chính) hoặc email. Bật ≥1 kênh để hoàn tất.">
              <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap" }}>
                <Button onClick={() => setBridge(true)}>📲 Bật nhắc Telegram</Button>
                <Button variant="secondary" onClick={() => enable("email")}>Dùng email</Button>
              </div>
            </Card>
            {/* if user skips, this persistent nudge keeps it reachable (no hard block) */}
            <ReminderNudge onEnable={() => setBridge(true)} />
          </>
        )}
      </div>

      <Modal open={bridge} title="Liên kết Telegram" onClose={() => setBridge(false)}
        footer={<><Button variant="ghost" onClick={() => setBridge(false)}>Để sau</Button><Button onClick={() => enable("telegram")}>Mở Telegram</Button></>}>
        <div style={{ fontSize: t.font.size.sm, lineHeight: t.font.lineHeight.relaxed }}>
          Nhấn “Mở Telegram” → bấm <strong>Start</strong> trong bot của Khế để liên kết. Sau đó bạn nhận nhắc hạn ngay trên Telegram (deep-link <code>t.me/khe_bot?start=…</code>).
        </div>
      </Modal>

      {toast && <div style={{ position: "fixed", bottom: t.space[6], left: "50%", transform: "translateX(-50%)", zIndex: t.z.toast }}><Toast kind="success">{toast}</Toast></div>}
    </div>
  );
}
