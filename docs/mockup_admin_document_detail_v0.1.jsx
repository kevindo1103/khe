/**
 * Khế — Admin · Document Detail  (mockup_admin_document_detail_v0.1.jsx)
 * KHE_Designer · Phase 2 · issue #24
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.1.
 *
 * FR-DR-01: original file + structured Terms + derived Obligations.
 * D-07: every extracted field is EDIT-IN-PLACE (edit → ghi Event).
 * FR-EX-05: confidence + needs_review shown PER FIELD.
 * Note (BRD §6 / KHE_AI): ngày_hết_hạn often null → derived from
 *       ngày_hiệu_lực + thời_hạn at obligation tier (shown as a hint here).
 */
import React, { useState } from "react";
import {
  tokens as t, Button, Card, Badge, ConfidenceMeter, Toast, Input,
} from "./mockup_design_system_v0.2.jsx";

const FIELDS = [
  { key: "doi_tac", label: "Đối tác", value: "Cty TNHH Hải Đăng", conf: 0.97 },
  { key: "ngay_hieu_luc", label: "Ngày hiệu lực", value: "01/10/2024", conf: 0.95 },
  { key: "thoi_han_hd", label: "Thời hạn", value: "24 tháng", conf: 0.88 },
  { key: "ngay_het_han", label: "Ngày hết hạn", value: "30/09/2026", conf: 0.62, derived: true },
  { key: "gia_tri_hd", label: "Giá trị HĐ", value: "45.000.000 đ/tháng", conf: 0.91 },
  { key: "dieu_khoan_gia_han", label: "Điều khoản gia hạn", value: "Báo trước 60 ngày", conf: 0.55 },
];

function FieldRow({ f, editing, onEdit, onSave, onCancel }) {
  const [draft, setDraft] = useState(f.value);
  const needsReview = f.conf < 0.8;
  return (
    <div style={{
      display: "grid", gridTemplateColumns: "160px 1fr auto", gap: t.space[3], alignItems: "center",
      padding: `${t.space[3]}px ${t.space[2]}px`, borderBottom: `1px solid ${t.color.border}`,
      background: needsReview ? t.color.warning_soft + "55" : "transparent",
    }}>
      <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, fontWeight: t.font.weight.medium }}>
        {f.label}
      </span>

      {editing ? (
        <Input value={draft} onChange={setDraft} />
      ) : (
        <span style={{ fontSize: t.font.size.md, color: t.color.ink, display: "flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap" }}>
          {f.value}
          {f.derived && <Badge kind="neutral">suy ra: hiệu lực + thời hạn</Badge>}
          {needsReview && <Badge kind="needs_review">⚠ cần kiểm tra</Badge>}
        </span>
      )}

      <div style={{ display: "flex", alignItems: "center", gap: t.space[3], justifySelf: "end" }}>
        {!editing && <ConfidenceMeter value={f.conf} />}
        {editing ? (
          <>
            <Button size="sm" onClick={() => onSave(draft)}>Lưu</Button>
            <Button size="sm" variant="ghost" onClick={onCancel}>Hủy</Button>
          </>
        ) : (
          /* D-07: edit affordance — sửa field → ghi Event */
          <Button size="sm" variant="secondary" onClick={onEdit}>✎ Sửa</Button>
        )}
      </div>
    </div>
  );
}

export default function AdminDocumentDetail() {
  const [editKey, setEditKey] = useState(null);
  const [toast, setToast] = useState(null);

  const save = () => {
    setEditKey(null);
    setToast("Đã lưu thay đổi — ghi Event ✓"); // D-07: edit writes an append-only Event
    setTimeout(() => setToast(null), 2500);
  };

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 960, margin: "0 auto" }}>
        <a href="#" style={{ fontSize: t.font.size.sm, color: t.color.primary, textDecoration: "none" }}>← Tài liệu</a>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: t.space[3], marginTop: t.space[2] }}>
          <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>
            HĐ thuê mặt bằng Q7
          </h1>
          <Badge kind="needs_review">⚠ có field cần kiểm tra</Badge>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: t.space[5], marginTop: t.space[5], alignItems: "start" }}>
          {/* Original file (immutable) */}
          <Card title="File gốc (bất biến)" subtitle="FR-IN-02">
            <div style={{
              height: 380, borderRadius: t.radius.md, background: t.color.surfaceAlt,
              border: `1px solid ${t.color.border}`, display: "flex", alignItems: "center",
              justifyContent: "center", color: t.color.inkSubtle, fontSize: t.font.size.sm,
            }}>
              📄 Xem trước PDF
            </div>
            <Button variant="secondary" size="sm" style={{ marginTop: t.space[3], width: "100%" }}>Tải bản gốc</Button>
          </Card>

          {/* Extracted Terms (editable) */}
          <div style={{ display: "flex", flexDirection: "column", gap: t.space[5] }}>
            <Card title="Thông tin bóc tách" subtitle="AI chỉ đọc (D-06). Field nào cũng sửa được (D-07); độ tin cậy theo từng field (FR-EX-05).">
              {FIELDS.map((f) => (
                <FieldRow
                  key={f.key} f={f}
                  editing={editKey === f.key}
                  onEdit={() => setEditKey(f.key)}
                  onSave={save}
                  onCancel={() => setEditKey(null)}
                />
              ))}
            </Card>

            <Card title="Nghĩa vụ phát sinh" subtitle="Tự sinh từ Term (FR-OB-01)">
              <div style={{ display: "flex", flexDirection: "column", gap: t.space[3] }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: t.font.size.sm }}>Gia hạn/chấm dứt trước 60 ngày — hạn 01/08/2026</span>
                  <Badge kind="due_soon">sắp tới</Badge>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: t.font.size.sm }}>Thanh toán 45tr — ngày 5 hàng tháng (lặp)</span>
                  <Badge kind="neutral">định kỳ</Badge>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>

      {toast && (
        <div style={{ position: "fixed", bottom: t.space[6], left: "50%", transform: "translateX(-50%)", zIndex: t.z.toast }}>
          <Toast kind="success">{toast}</Toast>
        </div>
      )}
    </div>
  );
}
