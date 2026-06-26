/**
 * Khế — PWA · Login  (mockup_pwa_login_v0.1.jsx)
 * KHE_Designer · Phase 3 · issue #24 (gates PWA #32)
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.1.
 *
 * Mobile-first: PWA Chat is the PRIMARY SME experience (Strategy §2.2).
 * Same auth contract as admin: POST /auth/login { tenant_id, username, password }.
 * Rendered inside a phone frame so the mobile layout is reviewable on desktop.
 */
import React, { useState } from "react";
import { tokens as t, Button, Input } from "./mockup_design_system_v0.1.jsx";

export function PhoneFrame({ children }) {
  return (
    <div style={{ background: t.color.surfaceAlt, minHeight: "100vh", display: "flex", justifyContent: "center", alignItems: "center", padding: t.space[6], fontFamily: t.font.family }}>
      <div style={{
        width: 390, height: 800, background: t.color.surface, borderRadius: 36,
        border: `10px solid #1A1D1C`, boxShadow: t.shadow.lg, overflow: "hidden",
        position: "relative", display: "flex", flexDirection: "column",
      }}>
        {children}
      </div>
    </div>
  );
}

export default function PwaLogin() {
  const [form, setForm] = useState({ tenant_id: "", username: "", password: "" });
  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));
  return (
    <PhoneFrame>
      <div style={{ flex: 1, padding: t.space[6], display: "flex", flexDirection: "column", justifyContent: "center", gap: t.space[5] }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 44, fontWeight: t.font.weight.bold, color: t.color.primary }}>Khế</div>
          <div style={{ fontSize: t.font.size.md, color: t.color.inkMuted, marginTop: t.space[2] }}>
            Hỏi nhanh hợp đồng — nhắc đúng hạn
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: t.space[4] }}>
          <Input label="Mã đơn vị" value={form.tenant_id} onChange={set("tenant_id")} placeholder="vd: sme-abc" />
          <Input label="Tên đăng nhập" value={form.username} onChange={set("username")} placeholder="vd: anh.dung" />
          <Input label="Mật khẩu" type="password" value={form.password} onChange={set("password")} placeholder="••••••••" />
          <Button size="lg" style={{ width: "100%" }}>Đăng nhập</Button>
        </div>
        <div style={{ textAlign: "center", fontSize: t.font.size.xs, color: t.color.inkSubtle }}>
          Tài khoản do đại lý/luật sư của bạn cấp.
        </div>
      </div>
    </PhoneFrame>
  );
}
