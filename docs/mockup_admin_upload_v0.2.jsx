/**
 * Khế — Admin · Upload v0.2  (mockup_admin_upload_v0.2.jsx)
 * KHE_Designer · steady-state re-layout on Design System v0.2 · supersedes v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Re-layout: adopts the a11y-correct `Dropzone` primitive (#206 — role=button +
 * keyboard + aria) instead of the hand-rolled <div> dropzone; cleaner queue with
 * per-doc progress + failure row (PartialUpload, no stuck state).
 * FR-IN-01 (camera / drag-drop / forward-email) · FR-IN-03 (async queue) ·
 * DEC-012 concierge bulk (≤20) · D-06 original immutable · D-11 quota note.
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Badge, Dropzone } from "./mockup_design_system_v0.2.jsx";

const QUEUE = [
  { name: "HĐ thuê Q7.pdf", state: "extracted" },
  { name: "HĐ bao bì Việt.jpg", state: "processing" },
  { name: "HĐ lao động An.pdf", state: "needs_review" },
  { name: "Ảnh mờ - trang 2.jpg", state: "failed" },
];

const STATE_LABEL = { processing: "đang đọc…", extracted: "đã bóc tách", needs_review: "cần kiểm tra", failed: "không đọc được" };
const STATE_KIND = { processing: "processing", extracted: "extracted", needs_review: "needs_review", failed: "overdue" };

function Tab({ active, children, onClick }) {
  return (
    <button onClick={onClick} type="button" aria-current={active ? "page" : undefined} style={{
      padding: `${t.space[2]}px ${t.space[4]}px`, fontFamily: t.font.family, background: "transparent", border: "none",
      fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, cursor: "pointer",
      color: active ? t.color.primary : t.color.inkMuted, borderBottom: `2px solid ${active ? t.color.primary : "transparent"}`,
    }}>{children}</button>
  );
}

export default function AdminUploadV2() {
  const [mode, setMode] = useState("single");
  const bulk = mode === "bulk";
  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family }}>
      <div style={{ maxWidth: 760, margin: "0 auto", padding: t.space[7] }}>
        <a href="#" style={{ fontSize: t.font.size.sm, color: t.color.primary }}>← Tổng quan</a>
        <h1 style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[2]}px 0 ${t.space[1]}px` }}>Tải tài liệu</h1>
        <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, margin: 0 }}>File gốc lưu bất biến; Khế chỉ đọc để bóc tách (D-06).</p>

        {/* quota hint (D-11) */}
        <div style={{ marginTop: t.space[3], fontSize: t.font.size.sm, color: t.color.inkMuted }}>
          Đã dùng <strong style={{ color: t.color.ink }}>18/30</strong> tài liệu tháng này.
        </div>

        <div style={{ display: "flex", gap: t.space[2], borderBottom: `1px solid ${t.color.border}`, margin: `${t.space[5]}px 0` }} role="tablist">
          <Tab active={!bulk} onClick={() => setMode("single")}>Tải đơn lẻ</Tab>
          <Tab active={bulk} onClick={() => setMode("bulk")}>Concierge — hàng loạt (≤20)</Tab>
        </div>

        {bulk && (
          <div style={{ background: t.color.info_soft, color: t.color.info, borderRadius: t.radius.md, padding: t.space[3], fontSize: t.font.size.sm, marginBottom: t.space[4], border: `1px solid ${t.color.infoBorder}` }}>
            ⓘ Chế độ concierge (DEC-012) — dành cho 20 SME đầu: số hóa cả ngăn kéo một lần. Khế/đối tác nhập batch giúp, bạn chỉ kiểm tra lại.
          </div>
        )}

        {/* a11y-correct dropzone primitive (#206) */}
        <Dropzone
          icon={bulk ? "🗂️" : "📤"}
          label={bulk ? "Kéo-thả tối đa 20 tài liệu" : "Kéo-thả, bấm, hoặc Enter để chọn hợp đồng"}
          hint={`PDF · Word · ảnh (JPG/PNG)${bulk ? " — số hóa hàng loạt" : ""}`}
        />
        <div style={{ display: "flex", gap: t.space[2], justifyContent: "center", marginTop: t.space[3] }}>
          <Button>Chọn tệp</Button>
          <Button variant="secondary">📷 Chụp ảnh</Button>
        </div>
        <p style={{ textAlign: "center", marginTop: t.space[3], fontSize: t.font.size.xs, color: t.color.inkMuted }}>
          Hoặc chuyển tiếp email tới <strong>sme-abc@in.khe.iceflow.cloud</strong> (FR-IN-01)
        </p>

        <Card title="Hàng đợi xử lý" subtitle="FR-IN-03 — bất đồng bộ, trạng thái theo từng tài liệu" style={{ marginTop: t.space[6] }}>
          <div style={{ display: "flex", flexDirection: "column" }}>
            {QUEUE.map((q, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: t.space[3], padding: `${t.space[3]}px ${t.space[2]}px`, borderBottom: i < QUEUE.length - 1 ? `1px solid ${t.color.border}` : "none" }}>
                <span style={{ fontSize: t.font.size.sm, color: t.color.ink, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>📄 {q.name}</span>
                <span style={{ display: "flex", alignItems: "center", gap: t.space[2], flexShrink: 0 }}>
                  <Badge kind={STATE_KIND[q.state]}>{STATE_LABEL[q.state]}</Badge>
                  {q.state === "failed" && <Button size="sm" variant="ghost">Thử lại</Button>}
                </span>
              </div>
            ))}
          </div>
          {/* PartialUpload honesty: a failed doc doesn't block the rest */}
          <p style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: t.space[3], marginBottom: 0 }}>
            1 tệp không đọc được — không ảnh hưởng các tệp còn lại. Bạn có thể chụp lại rõ hơn rồi thử lại.
          </p>
        </Card>
      </div>
    </div>
  );
}
