/**
 * Khế — PWA · Consent (NĐ 13/2023)  (mockup_pwa_consent_v0.1.jsx)
 * KHE_Designer · Phase 3 · issue #24 (gates PWA #32)
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.1.
 *
 * First-login dialog, BEFORE first upload/extract. Mobile-scrollable.
 * Copy + requirements per KHE_Compliance `nd13-v1` (issue #32 comment):
 *   - Buttons: "Đồng ý cho Khế đọc tài liệu của tôi" + "Để sau"
 *       (Để sau = app stays read-only, extraction blocked)
 *   - On agree → POST consent event purpose="vision_extraction",
 *       consent_text_version="nd13-v1" (Backend #22 wires the gate)
 *   - MUST name US recipients (Google / Anthropic) + revocation right
 *
 * ⚠ DRAFT copy — final legal wording from Compliance `nd13-v1` + Kevin/counsel
 *   sign-off before go-live (DEC-010). The exact paragraphs below are a faithful
 *   placeholder of the nd13-v1 spec, NOT ratified legal text.
 */
import React from "react";
import { tokens as t, Button } from "./mockup_design_system_v0.1.jsx";
import { PhoneFrame } from "./mockup_pwa_login_v0.1.jsx";

function Point({ children }) {
  return (
    <li style={{ marginBottom: t.space[2], color: t.color.inkMuted, fontSize: t.font.size.sm, lineHeight: t.font.lineHeight.relaxed }}>
      {children}
    </li>
  );
}

export default function PwaConsent() {
  return (
    <PhoneFrame>
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {/* scrollable body */}
        <div style={{ flex: 1, overflowY: "auto", padding: t.space[5] }}>
          <div style={{ fontSize: 32, marginBottom: t.space[2] }}>🔐</div>
          <h2 style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>
            Đồng ý để Khế đọc tài liệu của bạn
          </h2>
          <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, lineHeight: t.font.lineHeight.relaxed, marginTop: t.space[3] }}>
            Để nhắc hạn và trả lời câu hỏi, Khế cần đọc nội dung hợp đồng bạn tải lên.
            Theo Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân, bạn cần đồng ý trước:
          </p>
          <ul style={{ paddingLeft: t.space[5], margin: `${t.space[3]}px 0` }}>
            <Point><strong>Mục đích:</strong> bóc tách thông tin hợp đồng (đối tác, ngày, nghĩa vụ) để nhắc hạn — Khế chỉ đọc, không sửa nội dung pháp lý.</Point>
            <Point><strong>Nơi xử lý:</strong> tài liệu được gửi tới dịch vụ AI đặt tại Hoa Kỳ (<strong>Google LLC</strong> và <strong>Anthropic PBC</strong>) để đọc.</Point>
            <Point><strong>Lưu trữ:</strong> bản gốc tài liệu của bạn được lưu tại máy chủ ở Việt Nam.</Point>
            <Point><strong>Quyền của bạn:</strong> bạn có thể <strong>thu hồi đồng ý bất cứ lúc nào</strong> trong phần Cài đặt; khi thu hồi, Khế ngừng gửi tài liệu mới tới AI.</Point>
          </ul>
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, background: t.color.surfaceAlt, padding: t.space[3], borderRadius: t.radius.md }}>
            Bản tóm tắt — xem chính sách quyền riêng tư đầy đủ. (nội dung pháp lý cuối: nd13-v1, chờ duyệt)
          </div>
        </div>

        {/* sticky action footer */}
        <div style={{ borderTop: `1px solid ${t.color.border}`, padding: t.space[4], display: "flex", flexDirection: "column", gap: t.space[2] }}>
          {/* agree → POST consent event purpose=vision_extraction, version=nd13-v1 */}
          <Button size="lg" style={{ width: "100%" }}>Đồng ý cho Khế đọc tài liệu của tôi</Button>
          {/* defer → app stays read-only; extraction blocked (Backend #22 gate) */}
          <Button size="lg" variant="ghost" style={{ width: "100%" }}>Để sau</Button>
          <div style={{ textAlign: "center", fontSize: t.font.size.xs, color: t.color.inkSubtle }}>
            Chọn “Để sau”: bạn vẫn dùng được Khế ở chế độ chỉ-xem, nhưng chưa bóc tách tài liệu.
          </div>
        </div>
      </div>
    </PhoneFrame>
  );
}
