/**
 * Khế — Admin · Login  (mockup_admin_login_v0.1.jsx)
 * KHE_Designer · Phase 2 · issue #24
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports shared Design System v0.1.
 *
 * Contract: POST /auth/login  body { tenant_id, username, password } → JWT
 *           (Sprint 0 baseline #23). Form fields mirror that body exactly to
 *           avoid the "schema-vs-body shape drift" bug pattern (CLAUDE.md).
 */
import React, { useState } from "react";
import { tokens as t, Button, Input, Card } from "./mockup_design_system_v0.2.jsx";

export default function AdminLogin() {
  const [form, setForm] = useState({ tenant_id: "", username: "", password: "" });
  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <div style={{
      minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family,
      display: "flex", alignItems: "center", justifyContent: "center", padding: t.space[4],
    }}>
      <div style={{ width: "100%", maxWidth: 400 }}>
        <div style={{ textAlign: "center", marginBottom: t.space[6] }}>
          <div style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.primary }}>Khế</div>
          <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>
            Quản trị tài liệu — đăng nhập
          </div>
        </div>

        <Card>
          <div style={{ display: "flex", flexDirection: "column", gap: t.space[4] }}>
            <Input
              label="Mã đơn vị (tenant)" value={form.tenant_id} onChange={set("tenant_id")}
              placeholder="vd: sme-abc-restaurant" hint="Mã do firm/đại lý cấp khi onboard"
            />
            <Input label="Tên đăng nhập" value={form.username} onChange={set("username")} placeholder="vd: linh.ketoan" />
            <Input label="Mật khẩu" type="password" value={form.password} onChange={set("password")} placeholder="••••••••" />
            <Button size="lg" style={{ width: "100%" }}>Đăng nhập</Button>
            <div style={{ textAlign: "center", fontSize: t.font.size.xs, color: t.color.inkSubtle }}>
              Quên mật khẩu? Liên hệ đại lý/luật sư đã cấp tài khoản cho bạn.
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
