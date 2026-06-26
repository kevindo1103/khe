/**
 * Khế — PWA · Chat  (mockup_pwa_chat_v0.1.jsx)
 * KHE_Designer · Phase 3 · issue #24 (gates PWA #32)
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.1.
 *
 * PRIMARY SME experience. FR-CQ: NL query (VN), retrieve-only, cited answers.
 * D-08 is the headline rule here: when nothing matches, say plainly
 *   "Không tìm thấy thông tin này trong hồ sơ của bạn." — never fabricate.
 * Answers carry a source chip (→ Document/Obligation) per FR-CQ-02 (no bịa).
 */
import React, { useState } from "react";
import { tokens as t, Button, EmptyState } from "./mockup_design_system_v0.1.jsx";
import { PhoneFrame } from "./mockup_pwa_login_v0.1.jsx";

const SEED = [
  { role: "user", text: "Quý này hợp đồng nào sắp hết hạn?" },
  {
    role: "bot",
    text: "Có 1 hợp đồng sắp hết hạn trong quý này:\n• HĐ thuê mặt bằng Q7 — hết hạn 30/09/2026 (còn 104 ngày).",
    source: "HĐ thuê mặt bằng Q7",
  },
  { role: "user", text: "Phí gửi xe trong hợp đồng đó là bao nhiêu?" },
  // D-08: not in the docs → must say so, not guess.
  { role: "bot", notFound: true },
];

const SUGGESTIONS = ["Cái gì sắp hết hạn?", "Tìm HĐ với Hải Đăng", "HĐ thuê Q7 còn hạn bao lâu?"];

function Bubble({ m }) {
  const isUser = m.role === "user";
  if (m.notFound) {
    // D-08 inline empty-answer bubble
    return (
      <div style={{ alignSelf: "flex-start", maxWidth: "85%" }}>
        <div style={{
          background: t.color.warning_soft, color: t.color.warning, borderRadius: t.radius.lg,
          padding: t.space[3], fontSize: t.font.size.sm, lineHeight: t.font.lineHeight.relaxed,
        }}>
          <strong>Không tìm thấy thông tin này trong hồ sơ của bạn.</strong>
          <div style={{ color: t.color.inkMuted, marginTop: t.space[1] }}>
            Khế chỉ trả lời từ tài liệu bạn đã tải lên — không phỏng đoán. Bạn có thể hỏi cách khác hoặc tải thêm tài liệu.
          </div>
        </div>
      </div>
    );
  }
  return (
    <div style={{ alignSelf: isUser ? "flex-end" : "flex-start", maxWidth: "85%" }}>
      <div style={{
        background: isUser ? t.color.primary : t.color.surfaceAlt,
        color: isUser ? "#fff" : t.color.ink,
        borderRadius: t.radius.lg, padding: t.space[3], fontSize: t.font.size.sm,
        whiteSpace: "pre-line", lineHeight: t.font.lineHeight.relaxed,
      }}>
        {m.text}
      </div>
      {m.source && (
        /* FR-CQ-02: every answer traces to a concrete Document/Obligation */
        <a href="#" style={{
          display: "inline-flex", alignItems: "center", gap: 4, marginTop: t.space[1],
          fontSize: t.font.size.xs, color: t.color.primary, textDecoration: "none",
          background: t.color.primarySoft, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill,
        }}>
          📄 Nguồn: {m.source}
        </a>
      )}
    </div>
  );
}

export default function PwaChat({ empty = false }) {
  const [text, setText] = useState("");
  const msgs = empty ? [] : SEED;
  return (
    <PhoneFrame>
      {/* header */}
      <div style={{ padding: `${t.space[3]}px ${t.space[4]}px`, borderBottom: `1px solid ${t.color.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ fontWeight: t.font.weight.bold, color: t.color.primary, fontSize: t.font.size.lg }}>Khế</div>
        <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>Hỏi-đáp hồ sơ</span>
      </div>

      {/* thread */}
      <div style={{ flex: 1, overflowY: "auto", padding: t.space[4], display: "flex", flexDirection: "column", gap: t.space[3] }}>
        {msgs.length === 0 ? (
          <EmptyState icon="💬" title="Hỏi Khế về hợp đồng của bạn" description="Ví dụ: cái gì sắp hết hạn, tìm HĐ với một đối tác, còn hạn bao lâu…" />
        ) : (
          msgs.map((m, i) => <Bubble key={i} m={m} />)
        )}
      </div>

      {/* suggestions + composer */}
      <div style={{ borderTop: `1px solid ${t.color.border}`, padding: t.space[3] }}>
        <div style={{ display: "flex", gap: t.space[2], overflowX: "auto", marginBottom: t.space[2] }}>
          {SUGGESTIONS.map((s) => (
            <span key={s} style={{
              flexShrink: 0, fontSize: t.font.size.xs, color: t.color.primary, background: t.color.primarySoft,
              padding: `${t.space[1]}px ${t.space[2]}px`, borderRadius: t.radius.pill, cursor: "pointer", whiteSpace: "nowrap",
            }}>{s}</span>
          ))}
        </div>
        <div style={{ display: "flex", gap: t.space[2], alignItems: "center" }}>
          <input
            value={text} onChange={(e) => setText(e.target.value)} placeholder="Hỏi về hợp đồng của bạn…"
            style={{
              flex: 1, height: 44, padding: `0 ${t.space[3]}px`, fontSize: t.font.size.md,
              border: `1px solid ${t.color.border}`, borderRadius: t.radius.pill, outline: "none", fontFamily: t.font.family,
            }}
          />
          <Button style={{ borderRadius: t.radius.pill, height: 44, width: 44, padding: 0 }}>➤</Button>
        </div>
      </div>
    </PhoneFrame>
  );
}
