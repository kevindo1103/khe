/**
 * Khế — Admin · Hồ sơ hợp đồng · Empty state  (mockup_documents_list_v2_empty.jsx)
 * KHE_Designer · issue #278 · DEC-043 · DEC-012 (concierge onboarding)
 * STATIC PROTOTYPE — scope-lock docs/mockup_*.jsx. Not production code.
 * ----------------------------------------------------------------------------
 * Day-1 concierge tenant: 0 docs in the portfolio. This is the FIRST screen a
 * newly-onboarded SME sees, so it must teach the product's promise (obligation &
 * rights tracking — DEC-043) and offer one obvious next action, not a dead grid.
 *
 * Shares tokens + Sidebar shell language with mockup_documents_list_v2.jsx, but is
 * authored standalone (self-contained tokens) so it previews with zero build setup.
 * B&W minimalist (DS v0.2 / #197): emerald CTA only, everything else black/white/gray.
 *
 * Counter chips show 0/0 — but stay present so the layout the user will "grow into"
 * is legible from the first contract. Subtitle is action-first even at zero.
 */
import React from "react";

const t = {
  color: {
    ink: "#1A1A1A", inkMuted: "#6B7280", inkSubtle: "#9CA3AF",
    surface: "#FFFFFF", border: "#E5E7EB", borderStrong: "#D1D5DB",
    primary: "#0F7A56", primarySoft: "#E7F3EE", amber: "#D97706", amberSoft: "#FEF3E2", graySoft: "#F3F4F6",
  },
  font: { family: "'Inter', 'Be Vietnam Pro', system-ui, -apple-system, sans-serif",
    size: { xs: 12, sm: 13, md: 14, base: 15, lg: 18, xl: 22, "2xl": 26 },
    weight: { regular: 400, medium: 500, semibold: 600, bold: 700 } },
  space: { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48 },
  radius: { sm: 6, md: 8, lg: 12, pill: 999 },
};

function NavItem({ glyph, label, active, beta }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: t.space[2],
      padding: `${t.space[2]}px ${t.space[3]}px`, borderRadius: t.radius.md, cursor: "pointer",
      background: active ? t.color.primarySoft : "transparent",
      color: active ? t.color.primary : t.color.ink,
      fontWeight: active ? t.font.weight.semibold : t.font.weight.regular, fontSize: t.font.size.md,
    }}>
      <span style={{ width: 16, textAlign: "center", color: active ? t.color.primary : t.color.inkMuted }}>{glyph}</span>
      <span style={{ flex: 1 }}>{label}</span>
      {beta && <span style={{ fontSize: 10, fontWeight: t.font.weight.semibold, color: t.color.amber, background: t.color.amberSoft, padding: "1px 6px", borderRadius: t.radius.pill }}>Beta</span>}
    </div>
  );
}

function Sidebar() {
  const grp = { fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.inkSubtle,
    letterSpacing: 0.5, textTransform: "uppercase", padding: `${t.space[2]}px ${t.space[3]}px ${t.space[1]}px` };
  return (
    <aside style={{ width: 232, borderRight: `1px solid ${t.color.border}`, padding: t.space[4], boxSizing: "border-box", background: t.color.surface }}>
      <div style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.bold, color: t.color.primary, padding: `${t.space[2]}px ${t.space[3]}px ${t.space[5]}px` }}>Khế</div>
      <div style={grp}>Theo dõi</div>
      <NavItem glyph="○" label="Tổng quan" />
      <NavItem glyph="◇" label="Nghĩa vụ & Quyền lợi" />
      <div style={grp}>Tài liệu</div>
      <NavItem glyph="■" label="Hồ sơ hợp đồng" active />
      <NavItem glyph="↑" label="Tải lên" />
      <div style={grp}>Trợ lý</div>
      <NavItem glyph="✦" label="Hỏi-đáp" beta />
    </aside>
  );
}

export default function DocumentsListV2Empty() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: t.color.surface, fontFamily: t.font.family, color: t.color.ink }}>
      <Sidebar />
      <main style={{ flex: 1, padding: t.space[8], minWidth: 0 }}>
        {/* Same header skeleton as populated state — action-first subtitle at zero */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: t.space[4], flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>Hồ sơ hợp đồng</h1>
            <div style={{ fontSize: t.font.size.md, color: t.color.inkMuted, marginTop: t.space[2] }}>
              Chưa có hợp đồng nào — tải lên để Khế bắt đầu theo dõi nghĩa vụ & quyền lợi.
            </div>
          </div>
          <button style={{
            background: t.color.primary, color: t.color.surface, border: "none",
            padding: `${t.space[2]}px ${t.space[5]}px`, borderRadius: t.radius.md,
            fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, cursor: "pointer", fontFamily: t.font.family,
          }}>+ Tải hợp đồng</button>
        </div>

        {/* Empty illustration + primary CTA + concierge reassurance (DEC-012) */}
        <div style={{
          marginTop: t.space[8], border: `1px dashed ${t.color.borderStrong}`, borderRadius: t.radius.lg,
          background: t.color.surface, padding: `${t.space[12]}px ${t.space[6]}px`, textAlign: "center",
        }}>
          <div style={{ fontSize: 48, lineHeight: 1 }} aria-hidden>📄</div>
          <div style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.bold, color: t.color.ink, marginTop: t.space[4] }}>
            Tải hợp đồng đầu tiên
          </div>
          <div style={{ fontSize: t.font.size.md, color: t.color.inkMuted, maxWidth: 460, margin: `${t.space[3]}px auto 0`, lineHeight: 1.6 }}>
            Khế đọc hợp đồng, bóc tách nghĩa vụ (mình phải làm) và quyền lợi (mình được nhận),
            rồi nhắc bạn trước khi tới hạn. Bắt đầu chỉ với một file PDF hoặc ảnh chụp.
          </div>
          <div style={{ display: "flex", gap: t.space[3], justifyContent: "center", marginTop: t.space[6], flexWrap: "wrap" }}>
            <button style={{
              background: t.color.primary, color: t.color.surface, border: "none",
              padding: `${t.space[3]}px ${t.space[6]}px`, borderRadius: t.radius.md,
              fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, cursor: "pointer", fontFamily: t.font.family,
            }}>+ Tải hợp đồng</button>
            <button style={{
              background: t.color.surface, color: t.color.ink, border: `1px solid ${t.color.borderStrong}`,
              padding: `${t.space[3]}px ${t.space[6]}px`, borderRadius: t.radius.md,
              fontSize: t.font.size.md, fontWeight: t.font.weight.medium, cursor: "pointer", fontFamily: t.font.family,
            }}>Tải nhiều file (≤20)</button>
          </div>
          {/* Concierge onboarding note (DEC-012) — bỏ ma sát upload cho 20 SME đầu */}
          <div style={{ fontSize: t.font.size.sm, color: t.color.inkSubtle, marginTop: t.space[6] }}>
            Được onboard theo diện concierge? Đại lý/luật sư của bạn có thể số hóa giúp tận nơi.
          </div>
        </div>

        <div style={{ marginTop: t.space[6], padding: t.space[4], background: t.color.graySoft, borderRadius: t.radius.md, fontSize: t.font.size.xs, color: t.color.inkMuted, lineHeight: 1.7 }}>
          <div style={{ fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[1] }}>📐 Ghi chú thiết kế</div>
          <div>Empty state giữ nguyên header skeleton của trạng thái có dữ liệu để user "lớn lên" vào layout. CTA chính = "Tải hợp đồng" (G5). Bulk ≤20 = concierge (DEC-012). KHÔNG bịa số liệu — subtitle action-first ngay cả khi 0 hợp đồng.</div>
        </div>
      </main>
    </div>
  );
}
