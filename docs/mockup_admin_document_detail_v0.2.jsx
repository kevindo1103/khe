/**
 * Khế — Admin · Document Detail v0.2  (mockup_admin_document_detail_v0.2.jsx)
 * KHE_Designer · steady-state re-layout on Design System v0.2 · supersedes v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Re-layout (not just token swap) of the v0.1 detail screen, minimalist v0.2:
 *   • Side-by-side trust gate (D-06 immutable original | extracted Terms) with a
 *     persistent header summary + clearer field hierarchy.
 *   • Each field: confidence + needs_review (FR-EX-05), edit-in-place (D-07 → Event),
 *     and a tappable REF-LINK back into the original (the "tr.1 §A" anchor — D-06).
 *   • Parties panel (DEC-030) + derived Obligations with DIRECTION (nghĩa_vụ /
 *     quyền_lợi / cần xác nhận, DEC-030/D-13).
 *   • a11y: real <button>/<a>, aria-current on the ref anchor in focus, aria-live toast.
 *
 * D-06 AI read-only · D-07 every field editable → Event · FR-EX-05 per-field confidence
 * · D-13 direction derivation · ref-link = Frontend wires PDF.js scroll-to (handover #208).
 */
import React, { useState } from "react";
import {
  tokens as t, Button, Card, Badge, ConfidenceMeter, Toast, Input,
} from "./mockup_design_system_v0.2.jsx";

const FIELDS = [
  { key: "doi_tac", label: "Đối tác", value: "Cty TNHH Hải Đăng", conf: 0.97, ref: "tr.1 §A" },
  { key: "ngay_hieu_luc", label: "Ngày hiệu lực", value: "01/10/2024", conf: 0.95, ref: "tr.1 §2" },
  { key: "thoi_han_hd", label: "Thời hạn", value: "24 tháng", conf: 0.88, ref: "tr.1 §2" },
  { key: "ngay_het_han", label: "Ngày hết hạn", value: "30/09/2026", conf: 0.62, derived: true, ref: "suy ra" },
  { key: "gia_tri_hd", label: "Giá trị HĐ", value: "45.000.000 đ/tháng", conf: 0.91, ref: "tr.2 §4" },
  { key: "dieu_khoan_gia_han", label: "Điều khoản gia hạn", value: "Báo trước 60 ngày", conf: 0.55, ref: "tr.3 §7" },
];

const PARTIES = [
  { name: "Quán Cơm Tấm ABC", role: "Bên thuê", self: true },
  { name: "Cty TNHH Hải Đăng", role: "Bên cho thuê", self: false },
];

const OBLIGATIONS = [
  { what: "Gia hạn / chấm dứt trước 60 ngày", when: "hạn 01/08/2026", dir: "nghĩa_vụ", urgency: "due_soon", tag: "còn 39 ngày" },
  { what: "Thanh toán 45tr — ngày 5 hàng tháng", when: "lặp hàng tháng", dir: "nghĩa_vụ", urgency: "neutral", tag: "định kỳ" },
];

const DIR = {
  "nghĩa_vụ":  { kind: "brand", label: "Bạn cần" },
  "quyền_lợi": { kind: "neutral", label: "Đối tác cần" },
  "null":      { kind: "needs_review", label: "Cần xác nhận" },
};

function RefLink({ children }) {
  // D-06: anchor back into the immutable original — Frontend wires scroll-to (PDF.js).
  return (
    <a href="#original" style={{
      fontSize: t.font.size.xs, color: t.color.primary, textDecoration: "none",
      background: t.color.primarySoft, border: `1px solid ${t.color.primaryBorder}`,
      borderRadius: t.radius.pill, padding: `1px ${t.space[2]}px`, whiteSpace: "nowrap",
    }}>📄 {children}</a>
  );
}

function FieldRow({ f, editing, onEdit, onSave, onCancel }) {
  const [draft, setDraft] = useState(f.value);
  const needsReview = f.conf < 0.8;
  return (
    <div style={{
      display: "grid", gridTemplateColumns: "150px 1fr auto", gap: t.space[3], alignItems: "center",
      padding: `${t.space[3]}px ${t.space[3]}px`, borderBottom: `1px solid ${t.color.border}`,
      background: needsReview && !editing ? t.color.warning_soft + "44" : "transparent",
    }}>
      <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, fontWeight: t.font.weight.medium }}>{f.label}</span>

      {editing ? (
        <Input value={draft} onChange={setDraft} hint="Sửa → ghi Event (D-07)" />
      ) : (
        <span style={{ fontSize: t.font.size.md, color: t.color.ink, display: "flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap" }}>
          {f.value}
          <RefLink>{f.ref}</RefLink>
          {f.derived && <Badge kind="neutral">suy ra</Badge>}
          {needsReview && <Badge kind="needs_review">cần kiểm tra</Badge>}
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
          <Button size="sm" variant="secondary" onClick={onEdit}>✎ Sửa</Button>
        )}
      </div>
    </div>
  );
}

export default function AdminDocumentDetailV2() {
  const [editKey, setEditKey] = useState(null);
  const [toast, setToast] = useState(null);
  const lowCount = FIELDS.filter((f) => f.conf < 0.8).length;

  const save = () => {
    setEditKey(null);
    setToast("Đã lưu — ghi Event ✓");
    setTimeout(() => setToast(null), 2500);
  };

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family }}>
      <div style={{ maxWidth: 1040, margin: "0 auto", padding: t.space[7] }}>
        {/* breadcrumb + header */}
        <a href="#docs" style={{ fontSize: t.font.size.sm, color: t.color.primary }}>← Kho tài liệu</a>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: t.space[3], marginTop: t.space[2] }}>
          <div>
            <h1 style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: 0 }}>HĐ thuê mặt bằng Q7</h1>
            <div style={{ display: "flex", gap: t.space[2], marginTop: t.space[2], alignItems: "center" }}>
              <Badge kind="brand">Hợp đồng thuê</Badge>
              <Badge kind="extracted">đã bóc tách</Badge>
              {lowCount > 0 && <Badge kind="needs_review">{lowCount} field cần kiểm tra</Badge>}
            </div>
          </div>
          <Button variant="secondary" size="sm">Tải bản gốc</Button>
        </div>

        {/* side-by-side */}
        <div style={{ display: "grid", gridTemplateColumns: "minmax(300px, 360px) 1fr", gap: t.space[5], marginTop: t.space[6], alignItems: "start" }}>
          {/* LEFT — immutable original (D-06) */}
          <div id="original" style={{ position: "sticky", top: t.space[5] }}>
            <Card title="Bản gốc — bất biến" subtitle="D-06 · FR-IN-02">
              <div style={{ height: 420, borderRadius: t.radius.md, background: t.color.surfaceSunken, border: `1px solid ${t.color.border}`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: t.space[2], color: t.color.inkSubtle }}>
                <span style={{ fontSize: 40 }} aria-hidden="true">📄</span>
                <span style={{ fontSize: t.font.size.sm }}>Xem trước PDF (PDF.js)</span>
                <span style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle }}>bấm 📄 ref ở field để nhảy tới đoạn</span>
              </div>
              <div style={{ display: "flex", justifyContent: "center", gap: t.space[2], marginTop: t.space[3], alignItems: "center", color: t.color.inkMuted, fontSize: t.font.size.sm }}>
                <Button variant="ghost" size="sm" iconOnly aria-label="Trang trước">‹</Button>
                <span>tr. 1 / 3</span>
                <Button variant="ghost" size="sm" iconOnly aria-label="Trang sau">›</Button>
              </div>
            </Card>
          </div>

          {/* RIGHT — extracted + parties + obligations */}
          <div style={{ display: "flex", flexDirection: "column", gap: t.space[5] }}>
            <Card title="Thông tin bóc tách" subtitle="AI chỉ đọc (D-06). Field nào cũng sửa được (D-07); độ tin cậy theo field (FR-EX-05).">
              {FIELDS.map((f) => (
                <FieldRow key={f.key} f={f} editing={editKey === f.key}
                  onEdit={() => setEditKey(f.key)} onSave={save} onCancel={() => setEditKey(null)} />
              ))}
            </Card>

            <Card title="Các bên" subtitle="DEC-030 · bên nào là bạn → suy ra hướng nghĩa vụ">
              <div style={{ display: "flex", flexDirection: "column", gap: t.space[2] }}>
                {PARTIES.map((p) => (
                  <div key={p.name} style={{ display: "flex", alignItems: "center", gap: t.space[3], padding: t.space[2] }}>
                    <span style={{ width: 32, height: 32, borderRadius: "50%", background: t.color.surfaceSunken, border: `1px solid ${t.color.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: t.font.size.sm, color: t.color.inkMuted }} aria-hidden="true">{p.name[0]}</span>
                    <span style={{ flex: 1, minWidth: 0 }}>
                      <span style={{ display: "block", fontSize: t.font.size.base, color: t.color.ink, fontWeight: t.font.weight.medium }}>{p.name}</span>
                      <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkMuted }}>{p.role}</span>
                    </span>
                    {p.self && <Badge kind="brand">Bạn</Badge>}
                  </div>
                ))}
              </div>
            </Card>

            <Card title="Nghĩa vụ phát sinh" subtitle="Tự sinh từ Term (FR-OB-01) · hướng suy ra theo bên (D-13)">
              <div style={{ display: "flex", flexDirection: "column" }}>
                {OBLIGATIONS.map((o, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: t.space[3], padding: `${t.space[3]}px ${t.space[2]}px`, borderBottom: i < OBLIGATIONS.length - 1 ? `1px solid ${t.color.border}` : "none" }}>
                    <Badge kind={DIR[o.dir].kind}>{DIR[o.dir].label}</Badge>
                    <span style={{ flex: 1, minWidth: 0 }}>
                      <span style={{ display: "block", fontSize: t.font.size.sm, color: t.color.ink, fontWeight: t.font.weight.medium }}>{o.what}</span>
                      <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkMuted }}>{o.when}</span>
                    </span>
                    <Badge kind={o.urgency}>{o.tag}</Badge>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </div>

      {toast && (
        <div style={{ position: "fixed", bottom: t.space[6], left: "50%", transform: "translateX(-50%)", zIndex: t.z.toast }} aria-live="polite">
          <Toast kind="success">{toast}</Toast>
        </div>
      )}
    </div>
  );
}
