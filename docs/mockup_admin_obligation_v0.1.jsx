/**
 * Khế — Admin · Obligations  (mockup_admin_obligation_v0.1.jsx)
 * KHE_Designer · Phase 2 · issue #24
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.1.
 *
 * Obligation = MVP heart (BRD §6). FR-OB:
 *   - upcoming-due list grouped by urgency (overdue / due_soon / upcoming)
 *   - status + mark-done / hoãn / hủy → ghi Event (FR-OB-04)
 *   - one-time + recurring (FR-OB-02)
 *   - deterministic "what's due in [range]" — NOT an AI guess (FR-OB-03)
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Badge, Toast, EmptyState } from "./mockup_design_system_v0.1.jsx";

const SEED = [
  { id: 1, mo_ta: "Gia hạn/chấm dứt HĐ thuê Q7 (báo trước 60 ngày)", doc: "HĐ thuê mặt bằng Q7", han: "01/08/2026", loai: "một lần", bucket: "overdue", status: "pending" },
  { id: 2, mo_ta: "Thanh toán tiền thuê 45.000.000đ", doc: "HĐ thuê mặt bằng Q7", han: "05/07/2026", loai: "lặp · hàng tháng", bucket: "due_soon", status: "pending" },
  { id: 3, mo_ta: "Đóng BHXH nhân viên", doc: "HĐ lao động — N.V.An", han: "31/07/2026", loai: "lặp · hàng tháng", bucket: "upcoming", status: "pending" },
  { id: 4, mo_ta: "Gia hạn HĐ cung cấp bao bì", doc: "HĐ cung cấp bao bì", han: "15/07/2026", loai: "một lần", bucket: "due_soon", status: "done" },
];

const BUCKETS = [
  { key: "overdue", label: "Quá hạn", badge: "overdue" },
  { key: "due_soon", label: "Sắp tới hạn (≤30 ngày)", badge: "due_soon" },
  { key: "upcoming", label: "Sắp tới", badge: "neutral" },
];

function ObRow({ ob, onAction }) {
  const done = ob.status === "done";
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between", gap: t.space[3],
      padding: `${t.space[3]}px 0`, borderBottom: `1px solid ${t.color.border}`, opacity: done ? 0.6 : 1,
    }}>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: t.font.size.md, color: t.color.ink, fontWeight: t.font.weight.medium, textDecoration: done ? "line-through" : "none" }}>
          {ob.mo_ta}
        </div>
        <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: 2, display: "flex", gap: t.space[2], flexWrap: "wrap" }}>
          <span>📄 {ob.doc}</span><span>•</span><span>hạn {ob.han}</span><span>•</span><span>{ob.loai}</span>
        </div>
      </div>
      <div style={{ display: "flex", gap: t.space[2], alignItems: "center", flexShrink: 0 }}>
        {done ? (
          <Badge kind="done">✓ hoàn thành</Badge>
        ) : (
          <>
            <Button size="sm" onClick={() => onAction("done", ob)}>Hoàn thành</Button>
            <Button size="sm" variant="ghost" onClick={() => onAction("snooze", ob)}>Hoãn</Button>
          </>
        )}
      </div>
    </div>
  );
}

export default function AdminObligations() {
  const [toast, setToast] = useState(null);
  const act = (kind) => {
    setToast(kind === "done" ? "Đã đánh dấu hoàn thành — ghi Event ✓" : "Đã hoãn nhắc — ghi Event ✓");
    setTimeout(() => setToast(null), 2500);
  };

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 820, margin: "0 auto" }}>
        <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>Nghĩa vụ & hạn</h1>
        <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>
          Danh sách tất định từ kho — không phải AI đoán (FR-OB-03). Nhắc qua Telegram trước 30 + 7 ngày.
        </p>

        {/* summary strip */}
        <div style={{ display: "flex", gap: t.space[3], margin: `${t.space[5]}px 0`, flexWrap: "wrap" }}>
          {[["Quá hạn", 1, t.color.danger], ["Sắp tới hạn", 2, t.color.warning], ["Hoàn thành", 1, t.color.success]].map(([lbl, n, c]) => (
            <Card key={lbl} style={{ flex: "1 1 160px" }}>
              <div style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: c }}>{n}</div>
              <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>{lbl}</div>
            </Card>
          ))}
        </div>

        {BUCKETS.map((b) => {
          const items = SEED.filter((o) => o.bucket === b.key);
          if (items.length === 0) return null;
          return (
            <Card key={b.key} title={b.label} style={{ marginBottom: t.space[5] }}>
              {items.map((ob) => <ObRow key={ob.id} ob={ob} onAction={act} />)}
            </Card>
          );
        })}

        {SEED.length === 0 && <EmptyState icon="✅" title="Không có nghĩa vụ nào sắp tới" description="Khế sẽ nhắc bạn khi có hạn mới." />}
      </div>

      {toast && (
        <div style={{ position: "fixed", bottom: t.space[6], left: "50%", transform: "translateX(-50%)", zIndex: t.z.toast }}>
          <Toast kind="success">{toast}</Toast>
        </div>
      )}
    </div>
  );
}
