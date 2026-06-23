/**
 * Khế — Journey · Stage 3 Document Review  (mockup_journey_stage3_review_v0.1.jsx)
 * KHE_Designer · issue #198 Phase B · builds on Design System v0.2 + journey primitives v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Stage 3 = THE TRUST DECISION POINT (NEEDS_REVIEW → CONFIRMED). Until the user
 * confirms, the doc is NOT a reminder source (D-02). Layout:
 *   • LEFT  : immutable original (D-06) — page refs.
 *   • RIGHT : extracted fields, each with confidence + a link to the spot in the
 *             doc, inline-editable (D-07: edit → "Bạn đã cập nhật" + Event).
 *   • Self-party (DEC-030 / PR #172): "Đâu là BẠN?" → splits nghĩa vụ vs quyền lợi.
 *   • Confirm (D-02): "Xác nhận hợp đồng đã đúng" → READBACK → preview → confirm.
 *     Only AFTER confirm does it feed reminders.
 *
 * Failure path: low-confidence fields flagged needs_review; if extraction itself
 *   failed, the ExtractionFailure primitive (journey v0.1) is shown instead.
 */
import React, { useState } from "react";
import {
  tokens as t, Button, Card, Badge, ConfidenceMeter, Modal, Toast, Input,
} from "./mockup_design_system_v0.2.jsx";

const FIELDS0 = [
  { key: "doi_tac", label: "Đối tác", value: "Cty TNHH Hải Đăng", conf: 0.97, ref: "tr.1 §A" },
  { key: "ngay_hieu_luc", label: "Ngày hiệu lực", value: "01/10/2024", conf: 0.95, ref: "tr.1 §2" },
  { key: "thoi_han", label: "Thời hạn", value: "24 tháng", conf: 0.88, ref: "tr.1 §2" },
  { key: "ngay_het_han", label: "Ngày hết hạn", value: "30/09/2026", conf: 0.62, ref: "suy ra", derived: true },
  { key: "gia_tri", label: "Giá trị", value: "45.000.000đ/tháng", conf: 0.91, ref: "tr.2 §4" },
  { key: "gia_han", label: "Điều khoản gia hạn", value: "Báo trước 60 ngày", conf: 0.55, ref: "tr.3 §9" },
];

const PARTIES = [{ name: "Cty TNHH Hải Đăng", role: "Bên cho thuê" }, { name: "Quán Cơm Tấm ABC", role: "Bên thuê" }];

function FieldRow({ f, edited, onEdit }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(f.value);
  const low = f.conf < 0.8;
  return (
    <div style={{ padding: `${t.space[3]}px 0`, borderBottom: `1px solid ${t.color.border}`, background: low && !edited ? t.color.warning_soft + "44" : "transparent" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: t.space[2] }}>
        <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, fontWeight: t.font.weight.medium }}>{f.label}</span>
        <a href="#" style={{ fontSize: t.font.size.xs, color: t.color.primary, textDecoration: "none" }}>↪ {f.ref}</a>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: t.space[2], marginTop: t.space[1] }}>
        {editing ? (
          <div style={{ flex: 1 }}><Input value={draft} onChange={setDraft} /></div>
        ) : (
          <span style={{ fontSize: t.font.size.md, color: t.color.ink, display: "flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap" }}>
            {f.value}
            {f.derived && <Badge kind="neutral">suy ra</Badge>}
            {edited && <Badge kind="brand" dot>Bạn đã cập nhật</Badge>}
            {low && !edited && <Badge kind="needs_review" dot>cần kiểm tra</Badge>}
          </span>
        )}
        <div style={{ display: "flex", alignItems: "center", gap: t.space[3], flexShrink: 0 }}>
          {!editing && <ConfidenceMeter value={f.conf} />}
          {editing ? (
            <>
              <Button size="sm" onClick={() => { onEdit(f.key); setEditing(false); }}>Lưu</Button>
              <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>Hủy</Button>
            </>
          ) : (
            <Button size="sm" variant="secondary" onClick={() => setEditing(true)}>✎ Sửa</Button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Stage3Review() {
  const [edited, setEdited] = useState({});
  const [self, setSelf] = useState(null);
  const [confirmStep, setConfirmStep] = useState(null); // null | "readback" | "preview"
  const [toast, setToast] = useState(null);
  const [confirmed, setConfirmed] = useState(false);

  const onEdit = (k) => { setEdited((e) => ({ ...e, [k]: true })); setToast("Đã cập nhật — ghi Event ✓"); setTimeout(() => setToast(null), 2000); };
  const doConfirm = () => { setConfirmStep(null); setConfirmed(true); setToast("Đã xác nhận — Khế bắt đầu nhắc bạn ✓"); setTimeout(() => setToast(null), 2800); };

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 980, margin: "0 auto" }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Issue #198 · Stage 3 · NEEDS_REVIEW → CONFIRMED</span>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: t.space[3], marginTop: t.space[1] }}>
          <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: 0 }}>Kiểm tra hợp đồng đầu tiên</h1>
          {confirmed ? <Badge kind="done" dot>đã xác nhận</Badge> : <Badge kind="needs_review" dot>cần bạn xác nhận</Badge>}
        </div>
        <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, marginTop: t.space[1] }}>
          Khế đọc và điền sẵn. Bạn kiểm tra, sửa nếu sai (D-07) rồi xác nhận — chỉ sau đó Khế mới bắt đầu nhắc (D-02).
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 360px) 1fr", gap: t.space[5], marginTop: t.space[5], alignItems: "start" }}>
          {/* LEFT — immutable original (D-06) */}
          <Card title="Bản gốc (bất biến)" subtitle="D-06 — Khế không sửa nội dung gốc">
            <div style={{ height: 420, borderRadius: t.radius.md, background: t.color.surfaceSunken, border: `1px solid ${t.color.border}`, display: "flex", alignItems: "center", justifyContent: "center", color: t.color.inkSubtle, fontSize: t.font.size.sm }}>
              📄 HĐ thuê mặt bằng Q7.pdf
            </div>
          </Card>

          {/* RIGHT — extracted + self-party + confirm */}
          <div style={{ display: "flex", flexDirection: "column", gap: t.space[5] }}>
            {/* self-party first — needed to split direction */}
            <Card title="Đâu là BẠN trong hợp đồng?" subtitle="DEC-030 / D-02 — để Khế tách đúng nghĩa vụ của bạn vs quyền lợi">
              <div style={{ display: "flex", flexDirection: "column", gap: t.space[2] }}>
                {PARTIES.map((p) => (
                  <button key={p.role} onClick={() => setSelf(p.role)} style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center", padding: t.space[3], cursor: "pointer",
                    border: `1px solid ${self === p.role ? t.color.primary : t.color.border}`, background: self === p.role ? t.color.primarySoft : t.color.surface,
                    borderRadius: t.radius.md, fontFamily: t.font.family,
                  }}>
                    <span style={{ fontSize: t.font.size.base, color: t.color.ink }}>{p.name} <Badge kind="neutral">{p.role}</Badge></span>
                    <span style={{ color: self === p.role ? t.color.primary : t.color.borderStrong, fontWeight: t.font.weight.bold }}>{self === p.role ? "●" : "○"}</span>
                  </button>
                ))}
              </div>
            </Card>

            <Card title="Thông tin bóc tách" subtitle="AI chỉ đọc (D-06). Field nào cũng sửa được (D-07); độ tin cậy theo từng field (FR-EX-05).">
              {FIELDS0.map((f) => <FieldRow key={f.key} f={f} edited={!!edited[f.key]} onEdit={onEdit} />)}
            </Card>

            {/* confirm gate (D-02) */}
            <div style={{ display: "flex", gap: t.space[3], alignItems: "center", flexWrap: "wrap" }}>
              <Button size="lg" disabled={!self || confirmed} onClick={() => setConfirmStep("readback")}>
                {confirmed ? "✓ Đã xác nhận" : "Xác nhận hợp đồng đã đúng"}
              </Button>
              {!self && <span style={{ fontSize: t.font.size.sm, color: t.color.warning }}>Chọn “bên nào là bạn” trước.</span>}
            </div>
          </div>
        </div>
      </div>

      {/* D-02: readback → preview → confirm */}
      <Modal
        open={confirmStep === "readback"} title="Đọc lại trước khi xác nhận" onClose={() => setConfirmStep(null)}
        footer={<>
          <Button variant="ghost" onClick={() => setConfirmStep(null)}>Quay lại sửa</Button>
          <Button onClick={() => setConfirmStep("preview")}>Đúng rồi, tiếp tục</Button>
        </>}
      >
        <div style={{ fontSize: t.font.size.sm, lineHeight: t.font.lineHeight.relaxed }}>
          Bạn là <strong>{self}</strong>. HĐ với <strong>Cty TNHH Hải Đăng</strong>, hết hạn <strong>30/09/2026</strong>, gia hạn báo trước <strong>60 ngày</strong>.
          {Object.keys(edited).length > 0 && <div style={{ marginTop: t.space[2], color: t.color.inkMuted }}>Đã sửa {Object.keys(edited).length} trường.</div>}
        </div>
      </Modal>
      <Modal
        open={confirmStep === "preview"} title="Khế sẽ bắt đầu nhắc bạn" onClose={() => setConfirmStep(null)}
        footer={<>
          <Button variant="ghost" onClick={() => setConfirmStep("readback")}>Quay lại</Button>
          <Button onClick={doConfirm}>Xác nhận & bật theo dõi</Button>
        </>}
      >
        <div style={{ fontSize: t.font.size.sm, lineHeight: t.font.lineHeight.relaxed }}>
          Sau khi xác nhận, Khế tạo nghĩa vụ: <strong>gia hạn/chấm dứt trước 60 ngày</strong> (hạn ~01/08/2026) + thanh toán hàng tháng. Bạn vẫn sửa được sau.
        </div>
      </Modal>

      {toast && (
        <div style={{ position: "fixed", bottom: t.space[6], left: "50%", transform: "translateX(-50%)", zIndex: t.z.toast }}>
          <Toast kind="success">{toast}</Toast>
        </div>
      )}
    </div>
  );
}
