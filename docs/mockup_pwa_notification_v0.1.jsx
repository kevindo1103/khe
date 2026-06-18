/**
 * Khế — PWA · Notification opt-in (Telegram)  (mockup_pwa_notification_v0.1.jsx)
 * KHE_Designer · Phase 3 · issue #24 (gates PWA #32)
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.1.
 *
 * DEC-006: Telegram bot is the primary reminder channel (email = fallback).
 * Opt-in is a deep-link `t.me/<bot>?start=<link_token>` that ties the user's
 * Telegram chat_id back to their tenant. Reminder defaults: 30 + 7 days (FR-RM-02).
 */
import React, { useState } from "react";
import { tokens as t, Button, Badge } from "./mockup_design_system_v0.1.jsx";
import { PhoneFrame } from "./mockup_pwa_login_v0.1.jsx";

function Step({ n, children, done }) {
  return (
    <div style={{ display: "flex", gap: t.space[3], alignItems: "flex-start" }}>
      <div style={{
        width: 24, height: 24, borderRadius: "50%", flexShrink: 0,
        background: done ? t.color.success : t.color.primarySoft,
        color: done ? "#fff" : t.color.primary,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: t.font.size.xs, fontWeight: t.font.weight.bold,
      }}>{done ? "✓" : n}</div>
      <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>{children}</div>
    </div>
  );
}

export default function PwaNotification() {
  const [linked, setLinked] = useState(false);
  return (
    <PhoneFrame>
      <div style={{ flex: 1, padding: t.space[5], display: "flex", flexDirection: "column", gap: t.space[5] }}>
        <div>
          <div style={{ fontSize: 32, marginBottom: t.space[2] }}>🔔</div>
          <h2 style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>
            Nhận nhắc hạn qua Telegram
          </h2>
          <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, lineHeight: t.font.lineHeight.relaxed, marginTop: t.space[2] }}>
            Khế nhắc trước <strong>30 ngày</strong> và <strong>7 ngày</strong> khi hợp đồng sắp hết hạn. Bật Telegram để không bỏ lỡ.
          </p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: t.space[4] }}>
          <Step n={1} done={linked}>Nhấn nút bên dưới — mở Telegram tới bot của Khế.</Step>
          <Step n={2} done={linked}>Trong Telegram, nhấn <strong>Start</strong> để liên kết.</Step>
          <Step n={3} done={linked}>Xong! Bạn sẽ nhận nhắc hạn tại đây.</Step>
        </div>

        <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: t.space[3] }}>
          {linked ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: t.space[2] }}>
              <Badge kind="done">✓ Đã kết nối Telegram</Badge>
            </div>
          ) : (
            // deep-link: t.me/<bot>?start=<link_token bound to tenant+user>
            <Button size="lg" style={{ width: "100%" }} onClick={() => setLinked(true)}>
              📲 Mở Telegram & liên kết
            </Button>
          )}
          <button
            onClick={() => {}}
            style={{ background: "none", border: "none", color: t.color.inkMuted, fontSize: t.font.size.sm, cursor: "pointer", fontFamily: t.font.family }}
          >
            Dùng email thay thế
          </button>
          <div style={{ textAlign: "center", fontSize: t.font.size.xs, color: t.color.inkSubtle }}>
            Bạn có thể đổi kênh nhắc bất cứ lúc nào trong Cài đặt.
          </div>
        </div>
      </div>
    </PhoneFrame>
  );
}
