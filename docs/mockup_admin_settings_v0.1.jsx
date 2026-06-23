/**
 * Khế — Admin · Settings / Hồ sơ SME  (mockup_admin_settings_v0.1.jsx)
 * KHE_Designer · NEW screen (fills the nav "Cài đặt" gap) · Design System v0.2
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Sections:
 *   1. Hồ sơ doanh nghiệp — legal_name (DEC-030: auto-match obligor → direction D-13)
 *      + display name + tax id + aliases. Edit → Event (D-07).
 *   2. Kênh nhắc (DEC-006) — Telegram connect (deep-link) + email fallback. Reminder
 *      SCHEDULE shown generically ("theo chính sách Khế") — windows (30/7) NOT hardcoded
 *      (DEC-020 pending ratify, see DOCS_INBOX #1).
 *   3. Tài khoản — username + đổi mật khẩu (Modal).
 *   4. Quyền riêng tư & dữ liệu (NĐ 13/2023) — consent status, purpose, US recipients
 *      (Google/Anthropic, DEC-010), revoke (D-10, Modal confirm). ⚠ copy = DRAFT, counsel pending.
 *   5. Đối tác (firm access, D-09/D-10) — read-only placeholder; cross-tenant grant deferred M2+.
 *
 * a11y: real <button>/<a>/<label>, aria-live toast, Modal focus semantics.
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Badge, Input, Toast, Modal } from "./mockup_design_system_v0.2.jsx";

function Section({ title, desc, children, footer }) {
  return (
    <Card title={title} subtitle={desc} style={{ marginBottom: t.space[5] }} footer={footer}>
      <div style={{ padding: t.space[2], display: "flex", flexDirection: "column", gap: t.space[4] }}>{children}</div>
    </Card>
  );
}

function Row({ label, children, hint }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", gap: t.space[4], alignItems: "center" }}>
      <span>
        <span style={{ display: "block", fontSize: t.font.size.sm, fontWeight: t.font.weight.medium, color: t.color.inkBody }}>{label}</span>
        {hint && <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: 2 }}>{hint}</span>}
      </span>
      <div>{children}</div>
    </div>
  );
}

export default function AdminSettings() {
  const [toast, setToast] = useState(null);
  const [pwOpen, setPwOpen] = useState(false);
  const [revokeOpen, setRevokeOpen] = useState(false);
  const [legal, setLegal] = useState("Công ty TNHH Quán Cơm Tấm ABC");

  const flash = (m) => { setToast(m); setTimeout(() => setToast(null), 2500); };

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family }}>
      <div style={{ maxWidth: 760, margin: "0 auto", padding: t.space[7] }}>
        <a href="#" style={{ fontSize: t.font.size.sm, color: t.color.primary }}>← Tổng quan</a>
        <h1 style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[2]}px 0 ${t.space[6]}px` }}>Cài đặt</h1>

        {/* 1. Hồ sơ doanh nghiệp */}
        <Section title="Hồ sơ doanh nghiệp" desc="Tên pháp lý dùng để Khế xác định đâu là nghĩa vụ của bạn (DEC-030).">
          <Row label="Tên pháp lý" hint="Khớp với 'bên' trong hợp đồng → suy ra hướng nghĩa vụ (D-13)">
            <Input value={legal} onChange={setLegal} editable onEdit={() => flash("Đã cập nhật tên pháp lý — ghi Event ✓")} />
          </Row>
          <Row label="Tên hiển thị"><Input value="Quán Cơm Tấm ABC" onChange={() => {}} /></Row>
          <Row label="Mã số thuế"><Input value="0312345678" onChange={() => {}} /></Row>
          <Row label="Tên gọi khác" hint="Bí danh/viết tắt để match tốt hơn">
            <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", alignItems: "center" }}>
              <Badge kind="neutral">Cơm Tấm ABC</Badge>
              <Badge kind="neutral">Quán ABC</Badge>
              <Button size="sm" variant="secondary" onClick={() => flash("Thêm tên gọi khác")}>+ Thêm</Button>
            </div>
          </Row>
        </Section>

        {/* 2. Kênh nhắc */}
        <Section title="Kênh nhắc" desc="Khế nhắc các hạn đã bóc tách qua kênh bạn chọn (DEC-006).">
          <Row label="Telegram" hint="Kênh chính">
            <div style={{ display: "flex", gap: t.space[3], alignItems: "center", flexWrap: "wrap" }}>
              <Badge kind="extracted">Đã kết nối</Badge>
              <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>@quancomtam_abc</span>
              <Button size="sm" variant="ghost" onClick={() => flash("Đã ngắt kết nối Telegram")}>Ngắt</Button>
            </div>
          </Row>
          <Row label="Email dự phòng" hint="Dùng khi Telegram lỗi">
            <Input type="email" value="dung@quancomtam.vn" onChange={() => {}} editable onEdit={() => flash("Đã lưu email dự phòng ✓")} />
          </Row>
          <Row label="Lịch nhắc" hint="Quét hằng ngày 08:00 (giờ VN)">
            <span style={{ fontSize: t.font.size.sm, color: t.color.inkBody }}>
              Nhắc trước hạn theo chính sách của Khế.
              <span style={{ color: t.color.inkSubtle }}> (số ngày nhắc đang được chốt — DOCS_INBOX #1)</span>
            </span>
          </Row>
        </Section>

        {/* 3. Tài khoản */}
        <Section title="Tài khoản">
          <Row label="Tên đăng nhập"><span style={{ fontSize: t.font.size.base, color: t.color.ink }}>dung_abc</span></Row>
          <Row label="Mật khẩu"><Button size="sm" variant="secondary" onClick={() => setPwOpen(true)}>Đổi mật khẩu</Button></Row>
        </Section>

        {/* 4. Quyền riêng tư & dữ liệu (NĐ 13) */}
        <Section title="Quyền riêng tư & dữ liệu" desc="Theo Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.">
          <Row label="Trạng thái đồng ý"><Badge kind="extracted">Đã đồng ý · 12/06/2026</Badge></Row>
          <Row label="Mục đích xử lý"><span style={{ fontSize: t.font.size.sm, color: t.color.inkBody }}>Bóc tách thông tin hợp đồng bằng AI (vision_extraction)</span></Row>
          <Row label="Bên nhận dữ liệu" hint="Nhà cung cấp AI (đặt tại Hoa Kỳ — DEC-010)">
            <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap" }}>
              <Badge kind="neutral">Google (Gemini)</Badge>
              <Badge kind="neutral">Anthropic (Claude)</Badge>
            </div>
          </Row>
          <Row label="Thu hồi đồng ý" hint="Dừng xử lý AII với dữ liệu mới">
            <Button size="sm" variant="danger" onClick={() => setRevokeOpen(true)}>Thu hồi đồng ý</Button>
          </Row>
          <p style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, margin: 0 }}>⚠ Nội dung pháp lý đang chờ luật sư duyệt (DEC-010).</p>
        </Section>

        {/* 5. Đối tác (firm access) */}
        <Section title="Đối tác được cấp quyền" desc="Văn phòng luật / đại lý thuế bạn cho phép xem hồ sơ (D-09: chỉ xem; D-10: thu hồi được).">
          <div style={{ textAlign: "center", padding: `${t.space[5]}px 0`, color: t.color.inkMuted }}>
            <div style={{ fontSize: 28 }} aria-hidden="true">🤝</div>
            <div style={{ fontSize: t.font.size.sm, marginTop: t.space[2] }}>Chưa cấp quyền cho đối tác nào.</div>
            <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: t.space[1] }}>Tính năng chia sẻ với đối tác sẽ mở ở giai đoạn sau (M2+).</div>
          </div>
        </Section>
      </div>

      {/* Đổi mật khẩu */}
      <Modal open={pwOpen} title="Đổi mật khẩu" onClose={() => setPwOpen(false)}
        footer={<><Button variant="ghost" onClick={() => setPwOpen(false)}>Hủy</Button><Button onClick={() => { setPwOpen(false); flash("Đã đổi mật khẩu ✓"); }}>Lưu</Button></>}>
        <div style={{ display: "flex", flexDirection: "column", gap: t.space[3] }}>
          <Input label="Mật khẩu hiện tại" type="password" value="" onChange={() => {}} />
          <Input label="Mật khẩu mới" type="password" value="" onChange={() => {}} hint="Tối thiểu 8 ký tự" />
          <Input label="Nhập lại mật khẩu mới" type="password" value="" onChange={() => {}} />
        </div>
      </Modal>

      {/* Thu hồi đồng ý (D-10) */}
      <Modal open={revokeOpen} title="Thu hồi đồng ý xử lý dữ liệu?" onClose={() => setRevokeOpen(false)}
        footer={<><Button variant="ghost" onClick={() => setRevokeOpen(false)}>Để sau</Button><Button variant="danger" onClick={() => { setRevokeOpen(false); flash("Đã thu hồi đồng ý — ghi Event ✓"); }}>Thu hồi</Button></>}>
        <p style={{ fontSize: t.font.size.sm, color: t.color.inkBody, lineHeight: t.font.lineHeight.relaxed, margin: 0 }}>
          Khế sẽ ngừng dùng AI để bóc tách tài liệu mới. Dữ liệu đã bóc trước đó vẫn được giữ cho tới khi bạn xoá.
          Bạn có thể đồng ý lại bất cứ lúc nào.
        </p>
      </Modal>

      {toast && (
        <div style={{ position: "fixed", bottom: t.space[6], left: "50%", transform: "translateX(-50%)", zIndex: t.z.toast }} aria-live="polite">
          <Toast kind="success">{toast}</Toast>
        </div>
      )}
    </div>
  );
}
