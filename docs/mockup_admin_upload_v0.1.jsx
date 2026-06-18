/**
 * Khế — Admin · Upload  (mockup_admin_upload_v0.1.jsx)
 * KHE_Designer · Phase 2 · issue #24
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.1.
 *
 * Covers FR-IN-01 (camera / drag-drop PDF·Word / forward-email) + FR-IN-03
 * (async queue, "đang đọc…" per doc). Two modes:
 *   - Single drag-drop (everyday SME admin)
 *   - Bulk concierge mode ≤20 docs (DEC-012 — "ôm cả ngăn kéo", first 20 SME)
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Badge } from "./mockup_design_system_v0.1.jsx";

const queueSeed = [
  { name: "HĐ thuê Q7.pdf", state: "extracted" },
  { name: "HĐ bao bì Việt.jpg", state: "processing" },
  { name: "HĐ lao động An.pdf", state: "needs_review" },
];

function Tab({ active, children, onClick }) {
  return (
    <button onClick={onClick} style={{
      padding: `${t.space[2]}px ${t.space[4]}px`, fontFamily: t.font.family,
      fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, cursor: "pointer",
      background: "transparent", border: "none",
      color: active ? t.color.primary : t.color.inkMuted,
      borderBottom: `2px solid ${active ? t.color.primary : "transparent"}`,
    }}>{children}</button>
  );
}

function Dropzone({ multi }) {
  return (
    <div style={{
      border: `2px dashed ${t.color.borderStrong}`, borderRadius: t.radius.lg,
      background: t.color.surfaceAlt, padding: t.space[10], textAlign: "center",
    }}>
      <div style={{ fontSize: 40, marginBottom: t.space[2] }}>{multi ? "🗂️" : "📤"}</div>
      <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink }}>
        {multi ? "Kéo-thả tối đa 20 tài liệu" : "Kéo-thả hoặc chụp ảnh hợp đồng"}
      </div>
      <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>
        PDF · Word · ảnh (JPG/PNG){multi ? " — chế độ concierge số hóa hàng loạt" : ""}
      </div>
      <div style={{ marginTop: t.space[4], display: "flex", gap: t.space[2], justifyContent: "center", flexWrap: "wrap" }}>
        <Button>Chọn tệp</Button>
        <Button variant="secondary">📷 Chụp ảnh</Button>
      </div>
      <div style={{ marginTop: t.space[3], fontSize: t.font.size.xs, color: t.color.inkSubtle }}>
        Hoặc chuyển tiếp email tới: <strong>sme-abc@in.khe.vn</strong> (FR-IN-01)
      </div>
    </div>
  );
}

export default function AdminUpload() {
  const [mode, setMode] = useState("single");
  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 760, margin: "0 auto" }}>
        <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>Tải tài liệu</h1>
        <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>
          File gốc được lưu bất biến; Khế chỉ đọc để bóc tách (D-06).
        </p>

        <div style={{ display: "flex", gap: t.space[2], borderBottom: `1px solid ${t.color.border}`, margin: `${t.space[5]}px 0` }}>
          <Tab active={mode === "single"} onClick={() => setMode("single")}>Tải đơn lẻ</Tab>
          <Tab active={mode === "bulk"} onClick={() => setMode("bulk")}>Concierge — hàng loạt (≤20)</Tab>
        </div>

        {mode === "bulk" && (
          <div style={{
            background: t.color.info_soft, color: t.color.info, borderRadius: t.radius.md,
            padding: t.space[3], fontSize: t.font.size.sm, marginBottom: t.space[4],
          }}>
            ⓘ Chế độ concierge (DEC-012): dành cho 20 SME đầu — số hóa cả ngăn kéo một lần. Khế/firm nhập batch giúp, SME chỉ cần kiểm tra lại.
          </div>
        )}

        <Dropzone multi={mode === "bulk"} />

        <Card title="Hàng đợi xử lý" subtitle="FR-IN-03 — bất đồng bộ, trạng thái theo từng tài liệu" style={{ marginTop: t.space[6] }}>
          <div style={{ display: "flex", flexDirection: "column", gap: t.space[3] }}>
            {queueSeed.map((q, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: t.font.size.sm, color: t.color.ink }}>📄 {q.name}</span>
                <Badge kind={q.state}>
                  {q.state === "processing" ? "đang đọc…" : q.state === "extracted" ? "đã bóc tách" : "⚠ cần kiểm tra"}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
