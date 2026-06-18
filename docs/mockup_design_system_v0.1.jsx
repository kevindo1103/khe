/**
 * Khế — Design System v0.1  (KHE_Designer · Phase 1 · issue #24 · DEC-017)
 * ----------------------------------------------------------------------------
 * STATIC PROTOTYPE ONLY — not production code (scope-lock: docs/mockup_*.jsx).
 * Self-contained: inline styles driven by the `tokens` object so it renders with
 * zero build setup (no Tailwind/CSS pipeline needed to preview). Production
 * (Frontend #30 / PWA #31) will re-express these tokens as Tailwind theme config.
 *
 * Mobile-first: PWA Chat is the PRIMARY user experience (PRODUCT_STRATEGY §2.2).
 * Every later mockup (admin_*, pwa_*) MUST mirror these tokens — no ad-hoc colors.
 *
 * D-rules baked into components:
 *   D-07  → Input has an edit-in-place affordance; edits are meant to log Events.
 *   D-08  → EmptyState.notFound = "Không tìm thấy thông tin này trong hồ sơ của bạn."
 *   FR-EX-05 → Badge supports `needs_review` (warning) + a confidence progress variant.
 *
 * Default export <DesignSystemShowcase/> renders a gallery of all tokens + the 8
 * components for Kevin's per-phase approval.
 */

import React, { useState } from "react";

/* ===========================================================================
 * 1. DESIGN TOKENS  (single source of truth)
 * ========================================================================= */
export const tokens = {
  /* --- Color --------------------------------------------------------------
   * Semantic roles locked in designer_STATE.md. Neutral ramp tuned for
   * mobile contrast (SME owners read on phones in low light / outdoors). */
  color: {
    // Brand / primary action
    primary:       "#1F6F5C",  // khế-green (deep, trustworthy, not techy-blue)
    primaryHover:  "#185A4A",
    primarySoft:   "#E6F1ED",  // tinted surface / active nav bg

    // Semantic status
    success:       "#2E7D32",  success_soft: "#E7F4E8",
    warning:       "#B26A00",  warning_soft: "#FBEFD9",  // needs_review, due-soon
    danger:        "#C0392B",  danger_soft:  "#FBE9E7",  // overdue, destructive, revoked
    info:          "#2563A8",  info_soft:    "#E6EEF7",  // processing, neutral notice

    // Neutral ramp (text → border → surface)
    ink:           "#1A1D1C",  // primary text
    inkMuted:      "#5B6360",  // secondary text / labels
    inkSubtle:     "#8A918E",  // hints, disabled text
    border:        "#DADEDC",
    borderStrong:  "#C2C8C5",
    surface:       "#FFFFFF",  // cards
    surfaceAlt:    "#F5F7F6",  // page background
    overlay:       "rgba(20,29,28,0.45)", // modal scrim
  },

  /* --- Typography --------------------------------------------------------- */
  font: {
    family: "'Inter', 'Be Vietnam Pro', system-ui, -apple-system, sans-serif",
    size: { xs: 12, sm: 14, md: 16, lg: 18, xl: 22, "2xl": 28, "3xl": 34 },
    weight: { regular: 400, medium: 500, semibold: 600, bold: 700 },
    lineHeight: { tight: 1.25, normal: 1.5, relaxed: 1.65 },
  },

  /* --- Spacing — strict 4px grid ----------------------------------------- */
  space: { 0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48, 16: 64 },

  /* --- Radius ------------------------------------------------------------- */
  radius: { sm: 6, md: 10, lg: 14, xl: 20, pill: 999 },

  /* --- Shadow (soft, mobile-friendly) ------------------------------------ */
  shadow: {
    sm: "0 1px 2px rgba(20,29,28,0.06)",
    md: "0 2px 8px rgba(20,29,28,0.10)",
    lg: "0 8px 24px rgba(20,29,28,0.16)",
  },

  /* --- z-index scale ------------------------------------------------------ */
  z: { base: 0, sticky: 100, overlay: 1000, modal: 1100, toast: 1200 },
};

const t = tokens; // shorthand

/* ===========================================================================
 * 2. COMPONENTS
 * ========================================================================= */

/* --- 2.1 Button --------------------------------------------------------- */
export function Button({
  children, variant = "primary", size = "md",
  loading = false, disabled = false, onClick, style,
}) {
  const sizes = {
    sm: { padding: `${t.space[1]}px ${t.space[3]}px`, fontSize: t.font.size.sm, height: 32 },
    md: { padding: `${t.space[2]}px ${t.space[4]}px`, fontSize: t.font.size.md, height: 40 },
    lg: { padding: `${t.space[3]}px ${t.space[6]}px`, fontSize: t.font.size.lg, height: 48 },
  };
  const variants = {
    primary:   { background: t.color.primary, color: "#fff", border: "1px solid transparent" },
    secondary: { background: t.color.surface, color: t.color.primary, border: `1px solid ${t.color.borderStrong}` },
    ghost:     { background: "transparent", color: t.color.primary, border: "1px solid transparent" },
    danger:    { background: t.color.danger, color: "#fff", border: "1px solid transparent" },
  };
  const isOff = disabled || loading;
  return (
    <button
      onClick={isOff ? undefined : onClick}
      disabled={isOff}
      style={{
        ...sizes[size], ...variants[variant],
        display: "inline-flex", alignItems: "center", justifyContent: "center", gap: t.space[2],
        borderRadius: t.radius.md, fontFamily: t.font.family, fontWeight: t.font.weight.semibold,
        cursor: isOff ? "not-allowed" : "pointer", opacity: isOff ? 0.55 : 1,
        transition: "background .15s, opacity .15s", whiteSpace: "nowrap", ...style,
      }}
    >
      {loading && <Spinner />}
      {children}
    </button>
  );
}

function Spinner({ size = 16 }) {
  return (
    <span
      style={{
        width: size, height: size, borderRadius: "50%",
        border: "2px solid rgba(255,255,255,.5)", borderTopColor: "#fff",
        display: "inline-block", animation: "khe-spin .7s linear infinite",
      }}
    />
  );
}

/* --- 2.2 Input  (D-07: edit affordance + inline error/hint) ------------- */
export function Input({
  label, value, onChange, placeholder, hint, error,
  editable = false, onEdit, type = "text", style,
}) {
  const [hover, setHover] = useState(false);
  return (
    <label style={{ display: "block", fontFamily: t.font.family, ...style }}>
      {label && (
        <span style={{
          display: "block", fontSize: t.font.size.sm, fontWeight: t.font.weight.medium,
          color: t.color.inkMuted, marginBottom: t.space[1],
        }}>
          {label}
        </span>
      )}
      <div
        onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
        style={{ position: "relative", display: "flex", alignItems: "center" }}
      >
        <input
          type={type} value={value} placeholder={placeholder}
          onChange={(e) => onChange && onChange(e.target.value)}
          style={{
            width: "100%", height: 44, boxSizing: "border-box",
            padding: `0 ${t.space[3]}px`, fontSize: t.font.size.md, color: t.color.ink,
            background: t.color.surface, fontFamily: t.font.family,
            border: `1px solid ${error ? t.color.danger : t.color.border}`,
            borderRadius: t.radius.md, outline: "none",
          }}
        />
        {/* D-07: edit-in-place affordance — every extracted field is user-editable */}
        {editable && hover && (
          <button
            onClick={onEdit}
            title="Sửa (ghi Event)"
            style={{
              position: "absolute", right: t.space[2], background: t.color.primarySoft,
              color: t.color.primary, border: "none", borderRadius: t.radius.sm,
              fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold,
              padding: `${t.space[1]}px ${t.space[2]}px`, cursor: "pointer",
            }}
          >
            ✎ Sửa
          </button>
        )}
      </div>
      {error ? (
        <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.danger, marginTop: t.space[1] }}>
          {error}
        </span>
      ) : hint ? (
        <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: t.space[1] }}>
          {hint}
        </span>
      ) : null}
    </label>
  );
}

/* --- 2.3 Card ----------------------------------------------------------- */
export function Card({ title, subtitle, footer, children, style }) {
  return (
    <div style={{
      background: t.color.surface, border: `1px solid ${t.color.border}`,
      borderRadius: t.radius.lg, boxShadow: t.shadow.sm, overflow: "hidden",
      fontFamily: t.font.family, ...style,
    }}>
      {(title || subtitle) && (
        <div style={{ padding: `${t.space[4]}px ${t.space[5]}px`, borderBottom: `1px solid ${t.color.border}` }}>
          {title && <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{title}</div>}
          {subtitle && <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>{subtitle}</div>}
        </div>
      )}
      <div style={{ padding: `${t.space[5]}px` }}>{children}</div>
      {footer && (
        <div style={{ padding: `${t.space[3]}px ${t.space[5]}px`, borderTop: `1px solid ${t.color.border}`, background: t.color.surfaceAlt }}>
          {footer}
        </div>
      )}
    </div>
  );
}

/* --- 2.4 Table  (mobile-stacked via data-label) ------------------------- */
export function Table({ columns, rows, renderCell }) {
  return (
    <div style={{ overflowX: "auto", fontFamily: t.font.family }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: t.font.size.sm }}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} style={{
                textAlign: "left", padding: `${t.space[2]}px ${t.space[3]}px`,
                color: t.color.inkMuted, fontWeight: t.font.weight.semibold,
                borderBottom: `1px solid ${t.color.borderStrong}`, whiteSpace: "nowrap",
              }}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ borderBottom: `1px solid ${t.color.border}` }}>
              {columns.map((c) => (
                <td key={c.key} style={{ padding: `${t.space[3]}px`, color: t.color.ink }}>
                  {renderCell ? renderCell(c.key, row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* --- 2.5 Modal  (used for consent NĐ 13 + confirm-destructive) ---------- */
export function Modal({ open, title, children, onClose, footer }) {
  if (!open) return null;
  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, background: t.color.overlay, zIndex: t.z.modal,
        display: "flex", alignItems: "flex-end", justifyContent: "center", padding: t.space[4],
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: t.color.surface, borderRadius: t.radius.xl, boxShadow: t.shadow.lg,
          width: "100%", maxWidth: 440, fontFamily: t.font.family,
          /* bottom-sheet on mobile, centered feel on desktop via maxWidth */
        }}
      >
        <div style={{ padding: `${t.space[5]}px ${t.space[5]}px ${t.space[3]}px` }}>
          <div style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.bold, color: t.color.ink }}>{title}</div>
        </div>
        <div style={{ padding: `0 ${t.space[5]}px`, color: t.color.inkMuted, fontSize: t.font.size.md, lineHeight: t.font.lineHeight.relaxed }}>
          {children}
        </div>
        <div style={{ padding: t.space[5], display: "flex", gap: t.space[3], justifyContent: "flex-end" }}>
          {footer}
        </div>
      </div>
    </div>
  );
}

/* --- 2.6 Toast ---------------------------------------------------------- */
export function Toast({ kind = "success", children }) {
  const map = {
    success: { bg: t.color.success_soft, fg: t.color.success, icon: "✓" },
    error:   { bg: t.color.danger_soft,  fg: t.color.danger,  icon: "✕" },
    info:    { bg: t.color.info_soft,    fg: t.color.info,    icon: "ⓘ" },
  };
  const s = map[kind];
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: t.space[2],
      background: s.bg, color: s.fg, fontFamily: t.font.family,
      padding: `${t.space[2]}px ${t.space[4]}px`, borderRadius: t.radius.md,
      fontSize: t.font.size.sm, fontWeight: t.font.weight.medium, boxShadow: t.shadow.md,
    }}>
      <span aria-hidden style={{ fontWeight: t.font.weight.bold }}>{s.icon}</span>
      {children}
    </div>
  );
}

/* --- 2.7 Badge  (status pills + needs_review + confidence variant) ------ */
export function Badge({ kind = "neutral", children }) {
  const map = {
    neutral:      { bg: t.color.surfaceAlt,   fg: t.color.inkMuted },
    processing:   { bg: t.color.info_soft,    fg: t.color.info },     // "đang xử lý"
    extracted:    { bg: t.color.success_soft, fg: t.color.success },
    needs_review: { bg: t.color.warning_soft, fg: t.color.warning },  // FR-EX-05
    overdue:      { bg: t.color.danger_soft,  fg: t.color.danger },
    due_soon:     { bg: t.color.warning_soft, fg: t.color.warning },
    done:         { bg: t.color.success_soft, fg: t.color.success },
  };
  const s = map[kind] || map.neutral;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: t.space[1],
      background: s.bg, color: s.fg, fontFamily: t.font.family,
      padding: `${t.space[1]}px ${t.space[2]}px`, borderRadius: t.radius.pill,
      fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, lineHeight: 1,
    }}>
      {children}
    </span>
  );
}

/* Confidence indicator (FR-EX-05) — progress variant of the Badge family.
 * < 0.80 reads as needs_review (warning), else success. */
export function ConfidenceMeter({ value = 0 }) {
  const pct = Math.round(value * 100);
  const low = value < 0.8;
  const fg = low ? t.color.warning : t.color.success;
  const bg = low ? t.color.warning_soft : t.color.success_soft;
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: t.space[2], fontFamily: t.font.family }}>
      <div style={{ width: 64, height: 6, borderRadius: t.radius.pill, background: t.color.border, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: fg }} />
      </div>
      <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: fg, background: bg, padding: `2px ${t.space[1]}px`, borderRadius: t.radius.sm }}>
        {pct}%
      </span>
    </div>
  );
}

/* --- 2.8 EmptyState  (generic + D-08 chat "không tìm thấy" variant) ----- */
export function EmptyState({ icon = "📭", title, description, action, notFound = false }) {
  // D-08: chat retrieval must say it plainly, never fabricate.
  const t8 = notFound ? "Không tìm thấy thông tin này trong hồ sơ của bạn." : title;
  const d8 = notFound
    ? "Khế chỉ trả lời từ tài liệu bạn đã tải lên — không phỏng đoán. Hãy thử hỏi cách khác hoặc tải thêm tài liệu."
    : description;
  return (
    <div style={{
      textAlign: "center", padding: `${t.space[10]}px ${t.space[5]}px`,
      fontFamily: t.font.family, color: t.color.inkMuted,
    }}>
      <div style={{ fontSize: 40, marginBottom: t.space[3] }}>{notFound ? "🔍" : icon}</div>
      <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[2] }}>
        {t8}
      </div>
      {d8 && <div style={{ fontSize: t.font.size.sm, maxWidth: 360, margin: "0 auto", lineHeight: t.font.lineHeight.relaxed }}>{d8}</div>}
      {action && <div style={{ marginTop: t.space[5] }}>{action}</div>}
    </div>
  );
}

/* ===========================================================================
 * 3. SHOWCASE  (gallery for Kevin's Phase-1 approval)
 * ========================================================================= */
function Section({ title, note, children }) {
  return (
    <section style={{ marginBottom: t.space[12] }}>
      <h2 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>{title}</h2>
      {note && <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>{note}</p>}
      <div style={{ marginTop: t.space[5], display: "flex", flexWrap: "wrap", gap: t.space[5], alignItems: "flex-start" }}>
        {children}
      </div>
    </section>
  );
}

function Swatch({ name, hex }) {
  return (
    <div style={{ width: 120, fontFamily: t.font.family }}>
      <div style={{ height: 56, borderRadius: t.radius.md, background: hex, border: `1px solid ${t.color.border}` }} />
      <div style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, marginTop: t.space[1], color: t.color.ink }}>{name}</div>
      <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle }}>{hex}</div>
    </div>
  );
}

export default function DesignSystemShowcase() {
  const [modal, setModal] = useState(false);

  const colorRoles = [
    ["primary", t.color.primary], ["primaryHover", t.color.primaryHover], ["primarySoft", t.color.primarySoft],
    ["success", t.color.success], ["warning", t.color.warning], ["danger", t.color.danger], ["info", t.color.info],
    ["ink", t.color.ink], ["inkMuted", t.color.inkMuted], ["border", t.color.border],
    ["surface", t.color.surface], ["surfaceAlt", t.color.surfaceAlt],
  ];

  const docRows = [
    { ten: "HĐ thuê mặt bằng Q7", doi_tac: "Cty TNHH Hải Đăng", han: "2026-09-30", status: "extracted" },
    { ten: "HĐ nhà cung cấp — Bao bì", doi_tac: "Cty CP Bao Bì Việt", han: "2026-07-15", status: "needs_review" },
    { ten: "HĐ lao động — N.V.An", doi_tac: "—", han: "Vô thời hạn", status: "processing" },
  ];
  const cols = [
    { key: "ten", label: "Tài liệu" },
    { key: "doi_tac", label: "Đối tác" },
    { key: "han", label: "Ngày hết hạn" },
    { key: "status", label: "Trạng thái" },
  ];

  return (
    <div style={{ background: t.color.surfaceAlt, minHeight: "100vh", padding: t.space[8], fontFamily: t.font.family }}>
      {/* keyframes for spinner */}
      <style>{`@keyframes khe-spin{to{transform:rotate(360deg)}}`}</style>

      <header style={{ marginBottom: t.space[12] }}>
        <div style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.primary }}>Khế — Design System v0.1</div>
        <div style={{ fontSize: t.font.size.md, color: t.color.inkMuted, marginTop: t.space[2] }}>
          Mobile-first · 4px grid · tokens + 8 components · Phase 1 (issue #24, DEC-017). Đợi Kevin approve → unblock Frontend #30 / PWA #31.
        </div>
      </header>

      {/* TOKENS */}
      <Section title="Color" note="Semantic roles — production maps to Tailwind theme. KHÔNG dùng màu ad-hoc ngoài bảng này.">
        {colorRoles.map(([name, hex]) => <Swatch key={name} name={name} hex={hex} />)}
      </Section>

      <Section title="Typography" note={`Family: ${t.font.family}`}>
        <div style={{ width: "100%" }}>
          {Object.entries(t.font.size).reverse().map(([k, v]) => (
            <div key={k} style={{ fontSize: v, color: t.color.ink, lineHeight: t.font.lineHeight.normal, marginBottom: t.space[2] }}>
              <span style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginRight: t.space[3] }}>{k} · {v}px</span>
              Khế nhắc bạn trước khi hợp đồng hết hạn.
            </div>
          ))}
        </div>
      </Section>

      <Section title="Spacing (4px grid) · Radius">
        <div style={{ display: "flex", gap: t.space[4], flexWrap: "wrap" }}>
          {Object.entries(t.space).filter(([k]) => k !== "0").map(([k, v]) => (
            <div key={k} style={{ textAlign: "center" }}>
              <div style={{ width: v, height: v, background: t.color.primary, borderRadius: t.radius.sm }} />
              <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: t.space[1] }}>{k}·{v}</div>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: t.space[4], marginLeft: t.space[8] }}>
          {Object.entries(t.radius).map(([k, v]) => (
            <div key={k} style={{ textAlign: "center" }}>
              <div style={{ width: 56, height: 56, background: t.color.primarySoft, border: `1px solid ${t.color.primary}`, borderRadius: v }} />
              <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: t.space[1] }}>{k}</div>
            </div>
          ))}
        </div>
      </Section>

      {/* COMPONENTS */}
      <Section title="1 · Button" note="variants: primary / secondary / ghost / danger · sizes sm/md/lg · loading + disabled">
        <Button>Lưu tài liệu</Button>
        <Button variant="secondary">Hủy</Button>
        <Button variant="ghost">Bỏ qua</Button>
        <Button variant="danger">Thu hồi quyền</Button>
        <Button size="sm">Nhỏ</Button>
        <Button size="lg">Lớn</Button>
        <Button loading>Đang xử lý</Button>
        <Button disabled>Disabled</Button>
      </Section>

      <Section title="2 · Input" note="D-07: hover field bóc-tách → hiện nút ✎ Sửa (sửa → ghi Event). Hỗ trợ hint + error.">
        <div style={{ width: 280 }}><Input label="Tên đăng nhập" placeholder="vd: linh.ketoan" hint="Tài khoản do firm cấp" /></div>
        <div style={{ width: 280 }}><Input label="Ngày hết hạn (bóc tự động)" value="2026-09-30" editable onEdit={() => {}} /></div>
        <div style={{ width: 280 }}><Input label="Mật khẩu" type="password" value="123" error="Mật khẩu tối thiểu 8 ký tự" /></div>
      </Section>

      <Section title="3 · Card">
        <Card title="HĐ thuê mặt bằng Q7" subtitle="Cty TNHH Hải Đăng" footer={<Button size="sm" variant="secondary">Xem chi tiết</Button>} style={{ width: 320 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: t.font.size.sm }}>
            <span style={{ color: t.color.inkMuted }}>Ngày hết hạn</span>
            <strong>30/09/2026</strong>
          </div>
        </Card>
      </Section>

      <Section title="4 · Table" note="Status column dùng Badge. Cuộn ngang trên mobile.">
        <div style={{ width: "100%", maxWidth: 640 }}>
          <Table
            columns={cols} rows={docRows}
            renderCell={(key, row) => key === "status" ? <Badge kind={row.status}>{row.status}</Badge> : row[key]}
          />
        </div>
      </Section>

      <Section title="5 · Modal" note="Bottom-sheet trên mobile. Dùng cho consent NĐ 13/2023 + xác nhận destructive.">
        <Button onClick={() => setModal(true)}>Mở Modal</Button>
        <Modal
          open={modal} title="Đồng ý chia sẻ dữ liệu" onClose={() => setModal(false)}
          footer={<>
            <Button variant="ghost" onClick={() => setModal(false)}>Từ chối</Button>
            <Button onClick={() => setModal(false)}>Đồng ý</Button>
          </>}
        >
          Bạn đồng ý cho đại lý thuế của mình xem danh mục hợp đồng để được nhắc hạn chủ động? Bạn có thể thu hồi bất cứ lúc nào. (NĐ 13/2023)
        </Modal>
      </Section>

      <Section title="6 · Toast">
        <Toast kind="success">Đã lưu — ghi Event ✓</Toast>
        <Toast kind="error">Gửi nhắc thất bại</Toast>
        <Toast kind="info">Đang đọc tài liệu…</Toast>
      </Section>

      <Section title="7 · Badge + Confidence (FR-EX-05)" note="needs_review = warning · confidence = thanh tiến độ (<80% → cảnh báo).">
        <Badge kind="processing">đang xử lý</Badge>
        <Badge kind="extracted">đã bóc tách</Badge>
        <Badge kind="needs_review">⚠ cần kiểm tra</Badge>
        <Badge kind="due_soon">sắp hết hạn</Badge>
        <Badge kind="overdue">quá hạn</Badge>
        <Badge kind="done">hoàn thành</Badge>
        <ConfidenceMeter value={0.96} />
        <ConfidenceMeter value={0.62} />
      </Section>

      <Section title="8 · EmptyState" note="Generic + D-08 chat 'không tìm thấy' (không bịa).">
        <div style={{ width: 360, background: t.color.surface, borderRadius: t.radius.lg, border: `1px solid ${t.color.border}` }}>
          <EmptyState icon="📄" title="Chưa có tài liệu" description="Tải lên hợp đồng đầu tiên để Khế bắt đầu nhắc hạn." action={<Button>Tải tài liệu</Button>} />
        </div>
        <div style={{ width: 360, background: t.color.surface, borderRadius: t.radius.lg, border: `1px solid ${t.color.border}` }}>
          <EmptyState notFound />
        </div>
      </Section>
    </div>
  );
}
