/**
 * Khế — Admin · Self-party confirm  (mockup_admin_self_party_confirm_v0.1.jsx)
 * KHE_Designer · DEC-030 · design reference for FE #158 (#146c)
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.1.
 *
 * "Bên nào trong hợp đồng này là bạn?" — the gate that turns direction=null
 * obligations into nghĩa_vụ / quyền_lợi (feeds the obligation tabs, v0.2).
 *
 * D-02: direction is a USER-CONFIRMED legal write — never auto-derived.
 *   - dropdown source = document.parties[] {name, role_label} from backend #155
 *   - confirm → POST /documents/{id}/confirm_self_party { role_label }
 *               → backend re-derives direction per obligation (obligor==self ⇒ nghĩa_vụ)
 *   - optional one-time: PATCH /tenants/me/legal_name to auto-match future docs
 *
 * Two surfaces shown: (A) the modal, (B) the Settings legal-name field.
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Modal, Toast, Input, Badge } from "./mockup_design_system_v0.1.jsx";

const PARTIES = [
  { name: "Công ty CP ABC", role_label: "Bên A" },
  { name: "Tập đoàn XYZ", role_label: "Bên B" },
];

function PartyOption({ p, selected, onSelect }) {
  return (
    <button onClick={() => onSelect(p.role_label)} style={{
      width: "100%", textAlign: "left", display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: t.space[3], marginBottom: t.space[2], cursor: "pointer", fontFamily: t.font.family,
      border: `1px solid ${selected ? t.color.primary : t.color.border}`,
      background: selected ? t.color.primarySoft : t.color.surface, borderRadius: t.radius.md,
    }}>
      <span>
        <span style={{ fontSize: t.font.size.md, color: t.color.ink, fontWeight: t.font.weight.medium }}>{p.name}</span>
        <span style={{ marginLeft: t.space[2] }}><Badge kind="neutral">{p.role_label}</Badge></span>
      </span>
      <span style={{ color: selected ? t.color.primary : t.color.borderStrong, fontWeight: t.font.weight.bold }}>
        {selected ? "●" : "○"}
      </span>
    </button>
  );
}

export default function SelfPartyConfirm() {
  const [open, setOpen] = useState(true);
  const [choice, setChoice] = useState(null);
  const [remember, setRemember] = useState(true);
  const [legalName, setLegalName] = useState("Công ty CP ABC");
  const [toast, setToast] = useState(null);

  const confirm = () => {
    setOpen(false);
    // POST confirm_self_party {role_label: choice}; if remember → PATCH legal_name
    setToast(`Đã xác nhận “${choice}” là bạn — nghĩa vụ đã được phân hướng ✓`);
    setTimeout(() => setToast(null), 3000);
  };

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 640, margin: "0 auto", display: "flex", flexDirection: "column", gap: t.space[5] }}>
        <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>
          Self-party confirm (DEC-030)
        </h1>

        {/* (B) Settings legal-name field — one-time setup to auto-match future docs */}
        <Card title="Cài đặt · Tên pháp lý doanh nghiệp" subtitle="Đặt một lần → hợp đồng mới tự khớp, đỡ phải xác nhận thủ công">
          <div style={{ display: "flex", gap: t.space[3], alignItems: "flex-end" }}>
            <div style={{ flex: 1 }}>
              <Input label="Tên pháp lý" value={legalName} onChange={setLegalName} placeholder="vd: Công ty CP ABC" />
            </div>
            <Button onClick={() => { setToast("Đã lưu tên pháp lý ✓"); setTimeout(() => setToast(null), 2000); }}>Lưu</Button>
          </div>
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: t.space[2] }}>
            → PATCH /tenants/me/legal_name
          </div>
        </Card>

        <Button variant="secondary" onClick={() => { setChoice(null); setOpen(true); }}>Mở lại modal xác nhận</Button>
      </div>

      {/* (A) the confirm modal */}
      <Modal
        open={open} title="Bên nào trong hợp đồng này là bạn?" onClose={() => setOpen(false)}
        footer={<>
          <Button variant="ghost" onClick={() => setOpen(false)}>Để sau</Button>
          <Button disabled={!choice} onClick={confirm}>Xác nhận</Button>
        </>}
      >
        <div style={{ marginBottom: t.space[3], fontSize: t.font.size.sm }}>
          Hợp đồng <strong>HĐ hợp tác ABC-XYZ</strong> có nghĩa vụ ở cả hai bên. Chọn bên đại diện cho doanh nghiệp bạn để Khế tách
          đúng <em>nghĩa vụ của bạn</em> và <em>quyền lợi bạn được hưởng</em>.
        </div>
        <div>
          {PARTIES.map((p) => <PartyOption key={p.role_label} p={p} selected={choice === p.role_label} onSelect={setChoice} />)}
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: t.space[2], marginTop: t.space[2], fontSize: t.font.size.sm, color: t.color.inkMuted, cursor: "pointer" }}>
          <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
          Ghi nhớ làm tên pháp lý của tôi (tự khớp HĐ sau)
        </label>
        <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: t.space[2] }}>
          D-02: hướng nghĩa vụ chỉ được ghi sau khi bạn xác nhận — Khế không tự đoán.
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
