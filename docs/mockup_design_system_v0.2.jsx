/**
 * Khế — Design System v0.2  (mockup_design_system_v0.2.jsx)
 * KHE_Designer · minimalist revamp (Atlassian / Stripe-grade) · supersedes v0.1
 * ----------------------------------------------------------------------------
 * STATIC PROTOTYPE ONLY — scope docs/mockup_*.jsx. Self-contained: inline styles
 * driven by `tokens` so it renders with zero build. Production re-expresses these
 * as a Tailwind/CSS-vars theme.
 *
 * DESIGN PRINCIPLES (why this differs from v0.1)
 *   1. Neutral-dominant. One confident accent (khế-emerald) used sparingly.
 *      Calm surfaces, generous whitespace — content over chrome (Stripe).
 *   2. A precise 11-step neutral ramp (Atlassian N-scale style) so every
 *      text/border/surface choice is a token, never an ad-hoc hex.
 *   3. Soft, layered elevation (e0–e3) instead of one flat shadow. Borders do
 *      most of the separation; shadow only signals lift.
 *   4. Accessibility baked in: visible focus ring on every interactive element
 *      (WCAG 2.4.7), AA contrast on text roles, 40–44px touch targets.
 *   5. Type scale with tightened tracking on display sizes (industry standard
 *      for Inter), relaxed line-height on body for Vietnamese diacritics.
 *   6. Motion tokens (duration + standard easing) so transitions are uniform.
 *
 * MIGRATION: API surface is identical to v0.1 (same export names + token access
 *   keys: t.color.primary/ink/inkMuted/border/surface/surfaceAlt/primarySoft,
 *   t.color.{success,warning,danger,info}[_soft], t.font.*, t.space[*],
 *   t.radius.*, t.shadow.*, t.z.*). Existing screens upgrade by changing only
 *   the import path: "./mockup_design_system_v0.1.jsx" → "...v0.2.jsx".
 *   New, additive: t.color.neutral[*], t.color.ring, t.elevation.*, t.motion.*,
 *   Button variant "subtle", Badge `dot`, Skeleton, focusRing helper.
 *
 * ACCESSIBILITY — contrast VERIFIED (WCAG 2.1, measured not asserted):
 *   ink 15.0:1 · inkBody 10.8:1 · inkMuted 4.78:1 · primary 5.33:1 (white on
 *   primary 5.33:1) — all PASS AA normal on white. Semantic-on-tint: success
 *   4.51 · danger 5.70 · info 5.26 · warning 4.85 (was 4.34 FAIL → darkened to
 *   #8A6300). ALL PASS AA.
 *   ⚠️ `inkSubtle` (#94A3B8, 2.56:1) is BELOW AA by design — reserved ONLY for
 *      WCAG-exempt text (disabled controls, decorative, placeholder). Any
 *      meaningful text (hints, labels, timestamps) MUST use `inkMuted` (4.78:1).
 *   Touch targets: md/lg = 44/48px (≥44 touch min). `sm` (32px) is for dense
 *   DESKTOP/pointer surfaces only — do NOT use as a primary touch action.
 *   ⚠️ Vietnamese diacritics (ấ/ề/ỗ tone marks) need real-device QA on the PWA
 *      before prod — small Inter weights can look thin at low DPI. Mitigation
 *      here: small labels use weight 500+, body min 13px. Frontend owns device QA.
 *
 * SCOPE & SPEC-IMPACT: this is a VISUAL foundation refresh (tokens + generic
 *   components). It does NOT change BRD/SRS → no DOCS_INBOX for v0.2 itself.
 *   The activation-flow / journey primitives (ProgressBar, Stepper, Achievement
 *   card, locked-nav state, progressive-extraction PATTERN, 4-state EmptyState)
 *   belong to issue #198 and will be built ON this system once #198 is ratified;
 *   DOCS_INBOX will be filed then if they touch FR-CQ/FR-EX/FR-RM.
 *   This file is NOT a "complete" component library — it is the base layer.
 *
 * VERSIONING: v0.1 is FROZEN (no fixes — bugs fixed forward in v0.2). Migration
 *   to v0.2 is MANDATORY for all mockups; v0.1 imports removed once all screens
 *   migrate. Dark mode is out of MVP scope — the neutral-ramp + semantic token
 *   structure is theme-ready, but dark elevation tokens are deferred until a
 *   dark theme is actually scoped (Phase 2/3).
 */

import React, { useState } from "react";

/* ===========================================================================
 * 1. TOKENS
 * ========================================================================= */

/* 1.1 — Neutral ramp (cool slate). The backbone of a minimalist system. */
const neutral = {
  0:   "#FFFFFF",
  25:  "#FBFCFD", // app background
  50:  "#F6F8FA", // subtle surface / hover fill
  100: "#EDF1F5", // pressed fill / track
  200: "#E2E8F0", // hairline border (default)
  300: "#CBD4E1", // strong border / divider on color
  400: "#94A3B8", // placeholder / disabled text
  500: "#647488", // muted / secondary text
  600: "#4A5567", // body secondary
  700: "#333E4F", // body strong
  800: "#1F2733", // headings
  900: "#0E141B", // max ink (never pure black)
};

export const tokens = {
  color: {
    /* --- expose the ramp (additive) --- */
    neutral,

    /* --- brand: one accent, used with restraint --- */
    primary:       "#0F7A56", // khế-emerald
    primaryHover:  "#0C6648",
    primaryActive: "#0A5740",
    primarySoft:   "#E8F4EF", // tinted surface (selected nav, info pill)
    primaryBorder: "#BFE0D1",

    /* --- semantic: muted, not loud (700-level fg on tinted bg) --- */
    success: "#15803D", success_soft: "#E9F6EE", successBorder: "#BBE3C7",
    warning: "#8A6300", warning_soft: "#FBF1DD", warningBorder: "#ECD7A6", // 4.85:1 on tint (AA)
    danger:  "#B42318", danger_soft:  "#FCEBEA", dangerBorder:  "#F2C5C1",
    info:    "#175CD3", info_soft:    "#E9F1FD", infoBorder:    "#C2D7F5",

    /* --- text roles (map onto ramp) --- */
    ink:       neutral[800], // headings / primary text
    inkBody:   neutral[700], // additive: body copy
    inkMuted:  neutral[500], // labels / secondary
    inkSubtle: neutral[400], // hints / disabled

    /* --- lines & surfaces --- */
    border:       neutral[200],
    borderStrong: neutral[300],
    surface:      neutral[0],
    surfaceAlt:   neutral[25],
    surfaceSunken:neutral[50], // additive

    /* --- misc --- */
    overlay: "rgba(14,20,27,0.40)",
    ring:    "rgba(15,122,86,0.32)", // focus ring (additive)
  },

  font: {
    family: "'Inter', 'Be Vietnam Pro', system-ui, -apple-system, 'Segoe UI', sans-serif",
    // refined scale (13 is the workhorse body in dense UIs; 16 for comfortable)
    size: { xs: 12, sm: 13, base: 14, md: 16, lg: 18, xl: 20, "2xl": 24, "3xl": 30, "4xl": 36 },
    weight: { regular: 400, medium: 500, semibold: 600, bold: 700 },
    lineHeight: { tight: 1.2, snug: 1.35, normal: 1.5, relaxed: 1.65 },
    // tighten tracking on large display text (Inter looks best slightly negative)
    tracking: { tight: "-0.02em", snug: "-0.01em", normal: "0", wide: "0.04em" },
  },

  /* strict 4px grid */
  space: { 0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 7: 32, 8: 40, 9: 48, 10: 64, 12: 80 },

  radius: { xs: 4, sm: 6, md: 8, lg: 12, xl: 16, "2xl": 20, pill: 999 },

  /* layered elevation — soft, low-spread (Stripe/Atlassian) */
  elevation: {
    e0: "none",
    e1: "0 1px 2px rgba(14,20,27,0.06), 0 1px 1px rgba(14,20,27,0.04)",
    e2: "0 2px 6px -1px rgba(14,20,27,0.08), 0 1px 3px rgba(14,20,27,0.05)",
    e3: "0 16px 32px -12px rgba(14,20,27,0.18), 0 6px 12px -4px rgba(14,20,27,0.08)",
  },

  motion: {
    fast: "120ms", base: "180ms", slow: "240ms",
    ease: "cubic-bezier(0.2, 0, 0, 1)", // standard easing
  },

  z: { base: 0, sticky: 100, overlay: 1000, modal: 1100, toast: 1200 },
};

/* back-compat alias: v0.1 used `shadow`; keep it pointing at elevation */
tokens.shadow = { sm: tokens.elevation.e1, md: tokens.elevation.e2, lg: tokens.elevation.e3 };

const t = tokens;
const ringStyle = { boxShadow: `0 0 0 3px ${t.color.ring}` };

/* ===========================================================================
 * 2. COMPONENTS
 * ========================================================================= */

/* tiny hook for focus-visible ring without external CSS */
function useFocusRing() {
  const [focus, setFocus] = useState(false);
  return {
    focus,
    bind: { onFocus: () => setFocus(true), onBlur: () => setFocus(false) },
  };
}

/* --- 2.1 Button ---------------------------------------------------------
 * variants: primary · secondary (hairline) · subtle (neutral fill) · ghost · danger
 * Flat + minimal: color does the work, hover darkens, focus shows ring. */
export function Button({
  children, variant = "primary", size = "md",
  loading = false, disabled = false, onClick, style, iconOnly = false,
}) {
  const { focus, bind } = useFocusRing();
  const [hover, setHover] = useState(false);

  const sizes = {
    sm: { height: 32, padding: iconOnly ? 0 : `0 ${t.space[3]}px`, width: iconOnly ? 32 : undefined, fontSize: t.font.size.sm },
    md: { height: 44, padding: iconOnly ? 0 : `0 ${t.space[4]}px`, width: iconOnly ? 44 : undefined, fontSize: t.font.size.base }, // 44 = touch min
    lg: { height: 48, padding: iconOnly ? 0 : `0 ${t.space[5]}px`, width: iconOnly ? 48 : undefined, fontSize: t.font.size.md },
  };
  const variants = {
    primary:   { bg: t.color.primary, bgHover: t.color.primaryHover, fg: "#fff", border: "transparent" },
    secondary: { bg: t.color.surface, bgHover: t.color.surfaceSunken, fg: t.color.inkBody, border: t.color.borderStrong },
    subtle:    { bg: t.color.surfaceSunken, bgHover: t.color.neutral[100], fg: t.color.inkBody, border: "transparent" },
    ghost:     { bg: "transparent", bgHover: t.color.surfaceSunken, fg: t.color.primary, border: "transparent" },
    danger:    { bg: t.color.danger, bgHover: "#9A1B12", fg: "#fff", border: "transparent" },
  };
  const v = variants[variant];
  const off = disabled || loading;

  return (
    <button
      {...bind}
      onClick={off ? undefined : onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      disabled={off}
      style={{
        ...sizes[size],
        display: "inline-flex", alignItems: "center", justifyContent: "center", gap: t.space[2],
        background: hover && !off ? v.bgHover : v.bg, color: v.fg,
        border: `1px solid ${v.border}`, borderRadius: t.radius.md,
        fontFamily: t.font.family, fontWeight: t.font.weight.semibold, letterSpacing: t.font.tracking.snug,
        cursor: off ? "not-allowed" : "pointer", opacity: off ? 0.5 : 1, whiteSpace: "nowrap",
        transition: `background ${t.motion.fast} ${t.motion.ease}, box-shadow ${t.motion.fast} ${t.motion.ease}`,
        ...(focus ? ringStyle : null),
        ...style,
      }}
    >
      {loading && <Spinner light={variant === "primary" || variant === "danger"} />}
      {children}
    </button>
  );
}

function Spinner({ size = 15, light = false }) {
  return (
    <span style={{
      width: size, height: size, borderRadius: "50%", display: "inline-block",
      border: `2px solid ${light ? "rgba(255,255,255,.45)" : t.color.neutral[300]}`,
      borderTopColor: light ? "#fff" : t.color.primary,
      animation: "khe-spin .6s linear infinite",
    }} />
  );
}

/* --- 2.2 Input  (D-07 edit affordance + focus ring + hint/error) -------- */
export function Input({
  label, value, onChange, placeholder, hint, error,
  editable = false, onEdit, type = "text", style, prefix,
}) {
  const { focus, bind } = useFocusRing();
  const [hover, setHover] = useState(false);
  const borderColor = error ? t.color.danger : focus ? t.color.primary : t.color.border;
  return (
    <label style={{ display: "block", fontFamily: t.font.family, ...style }}>
      {label && (
        <span style={{ display: "block", fontSize: t.font.size.sm, fontWeight: t.font.weight.medium, color: t.color.inkBody, marginBottom: t.space[1] }}>
          {label}
        </span>
      )}
      <div
        onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
        style={{
          display: "flex", alignItems: "center", gap: t.space[2],
          height: 44, padding: `0 ${t.space[3]}px`, background: t.color.surface,
          border: `1px solid ${borderColor}`, borderRadius: t.radius.md,
          transition: `border-color ${t.motion.fast} ${t.motion.ease}, box-shadow ${t.motion.fast} ${t.motion.ease}`,
          ...(focus ? ringStyle : null),
        }}
      >
        {prefix && <span style={{ color: t.color.inkSubtle, fontSize: t.font.size.base }}>{prefix}</span>}
        <input
          {...bind}
          type={type} value={value} placeholder={placeholder}
          onChange={(e) => onChange && onChange(e.target.value)}
          style={{
            flex: 1, minWidth: 0, border: "none", outline: "none", background: "transparent",
            fontSize: t.font.size.base, color: t.color.ink, fontFamily: t.font.family,
          }}
        />
        {editable && (hover || focus) && (
          // D-07: every extracted field is user-editable; edit → Event
          <button onClick={onEdit} title="Sửa (ghi Event)" style={{
            background: t.color.primarySoft, color: t.color.primary, border: "none",
            borderRadius: t.radius.sm, fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold,
            padding: `2px ${t.space[2]}px`, cursor: "pointer",
          }}>✎ Sửa</button>
        )}
      </div>
      {error ? (
        <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.danger, marginTop: t.space[1] }}>{error}</span>
      ) : hint ? (
        // hint is meaningful text → inkMuted (AA), not inkSubtle (below-AA, exempt-only)
        <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: t.space[1] }}>{hint}</span>
      ) : null}
    </label>
  );
}

/* --- 2.3 Card ----------------------------------------------------------- */
export function Card({ title, subtitle, footer, children, style, interactive = false }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        background: t.color.surface, border: `1px solid ${t.color.border}`,
        borderRadius: t.radius.lg, overflow: "hidden", fontFamily: t.font.family,
        boxShadow: interactive && hover ? t.elevation.e2 : t.elevation.e1,
        transition: `box-shadow ${t.motion.base} ${t.motion.ease}`,
        ...style,
      }}
    >
      {(title || subtitle) && (
        <div style={{ padding: `${t.space[4]}px ${t.space[5]}px`, borderBottom: `1px solid ${t.color.border}` }}>
          {title && <div style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, color: t.color.ink, letterSpacing: t.font.tracking.snug }}>{title}</div>}
          {subtitle && <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>{subtitle}</div>}
        </div>
      )}
      <div style={{ padding: t.space[5] }}>{children}</div>
      {footer && (
        <div style={{ padding: `${t.space[3]}px ${t.space[5]}px`, borderTop: `1px solid ${t.color.border}`, background: t.color.surfaceAlt }}>{footer}</div>
      )}
    </div>
  );
}

/* --- 2.4 Table  (minimal: uppercase micro-header, hairline rows) -------- */
export function Table({ columns, rows, renderCell }) {
  const [hoverRow, setHoverRow] = useState(-1);
  return (
    <div style={{ overflowX: "auto", fontFamily: t.font.family }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: t.font.size.base }}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} style={{
                textAlign: "left", padding: `${t.space[2]}px ${t.space[3]}px`,
                color: t.color.inkMuted, fontWeight: t.font.weight.semibold,
                fontSize: t.font.size.xs, textTransform: "uppercase", letterSpacing: t.font.tracking.wide,
                borderBottom: `1px solid ${t.color.border}`, whiteSpace: "nowrap",
              }}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}
              onMouseEnter={() => setHoverRow(i)} onMouseLeave={() => setHoverRow(-1)}
              style={{ background: hoverRow === i ? t.color.surfaceAlt : "transparent", transition: `background ${t.motion.fast} ${t.motion.ease}` }}>
              {columns.map((c) => (
                <td key={c.key} style={{ padding: `${t.space[3]}px`, color: t.color.inkBody, borderBottom: `1px solid ${t.color.border}` }}>
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

/* --- 2.5 Modal  (centered, soft scrim, e3, scale-in) -------------------- */
export function Modal({ open, title, children, onClose, footer }) {
  if (!open) return null;
  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: t.color.overlay, zIndex: t.z.modal,
      display: "flex", alignItems: "center", justifyContent: "center", padding: t.space[4],
      animation: `khe-fade ${t.motion.base} ${t.motion.ease}`,
    }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: t.color.surface, borderRadius: t.radius.xl, boxShadow: t.elevation.e3,
        width: "100%", maxWidth: 440, fontFamily: t.font.family, border: `1px solid ${t.color.border}`,
        animation: `khe-pop ${t.motion.base} ${t.motion.ease}`,
      }}>
        <div style={{ padding: `${t.space[5]}px ${t.space[5]}px ${t.space[2]}px` }}>
          <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink, letterSpacing: t.font.tracking.snug }}>{title}</div>
        </div>
        <div style={{ padding: `0 ${t.space[5]}px`, color: t.color.inkBody, fontSize: t.font.size.base, lineHeight: t.font.lineHeight.relaxed }}>{children}</div>
        <div style={{ padding: t.space[5], display: "flex", gap: t.space[2], justifyContent: "flex-end" }}>{footer}</div>
      </div>
    </div>
  );
}

/* --- 2.6 Toast ---------------------------------------------------------- */
export function Toast({ kind = "success", children }) {
  const map = {
    success: { fg: t.color.success, bd: t.color.successBorder, icon: "✓" },
    error:   { fg: t.color.danger,  bd: t.color.dangerBorder,  icon: "✕" },
    info:    { fg: t.color.info,    bd: t.color.infoBorder,    icon: "ⓘ" },
  };
  const s = map[kind];
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: t.space[2],
      background: t.color.surface, color: t.color.inkBody, fontFamily: t.font.family,
      padding: `${t.space[2]}px ${t.space[4]}px`, borderRadius: t.radius.md,
      border: `1px solid ${t.color.border}`, boxShadow: t.elevation.e2,
      fontSize: t.font.size.base, fontWeight: t.font.weight.medium,
    }}>
      <span aria-hidden style={{ color: s.fg, fontWeight: t.font.weight.bold }}>{s.icon}</span>
      {children}
    </div>
  );
}

/* --- 2.7 Badge  (subtle tint pills + optional dot) ---------------------- */
export function Badge({ kind = "neutral", dot = false, children }) {
  const map = {
    neutral:      { bg: t.color.surfaceSunken, fg: t.color.inkMuted,  bd: t.color.border },
    processing:   { bg: t.color.info_soft,     fg: t.color.info,      bd: t.color.infoBorder },
    extracted:    { bg: t.color.success_soft,  fg: t.color.success,   bd: t.color.successBorder },
    needs_review: { bg: t.color.warning_soft,  fg: t.color.warning,   bd: t.color.warningBorder },
    overdue:      { bg: t.color.danger_soft,   fg: t.color.danger,    bd: t.color.dangerBorder },
    due_soon:     { bg: t.color.warning_soft,  fg: t.color.warning,   bd: t.color.warningBorder },
    done:         { bg: t.color.success_soft,  fg: t.color.success,   bd: t.color.successBorder },
    brand:        { bg: t.color.primarySoft,   fg: t.color.primary,   bd: t.color.primaryBorder },
  };
  const s = map[kind] || map.neutral;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: t.space[1],
      background: s.bg, color: s.fg, border: `1px solid ${s.bd}`, fontFamily: t.font.family,
      padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill,
      fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, lineHeight: 1.4,
    }}>
      {dot && <span style={{ width: 6, height: 6, borderRadius: "50%", background: s.fg }} />}
      {children}
    </span>
  );
}

/* Confidence meter (FR-EX-05) — thin, refined. <80% reads as needs_review. */
export function ConfidenceMeter({ value = 0 }) {
  const pct = Math.round(value * 100);
  const low = value < 0.8;
  const fg = low ? t.color.warning : t.color.success;
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: t.space[2], fontFamily: t.font.family }}>
      <div style={{ width: 56, height: 4, borderRadius: t.radius.pill, background: t.color.neutral[200], overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: fg, transition: `width ${t.motion.slow} ${t.motion.ease}` }} />
      </div>
      <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: fg, fontVariantNumeric: "tabular-nums" }}>{pct}%</span>
    </div>
  );
}

/* --- 2.8 EmptyState  (generous whitespace + D-08 chat variant) ---------- */
export function EmptyState({ icon = "○", title, description, action, notFound = false }) {
  const ttl = notFound ? "Không tìm thấy thông tin này trong hồ sơ của bạn." : title;
  const desc = notFound
    ? "Khế chỉ trả lời từ tài liệu bạn đã tải lên — không phỏng đoán. Hãy thử hỏi cách khác hoặc tải thêm tài liệu."
    : description;
  return (
    <div style={{ textAlign: "center", padding: `${t.space[9]}px ${t.space[5]}px`, fontFamily: t.font.family, color: t.color.inkMuted }}>
      <div style={{
        width: 48, height: 48, margin: "0 auto", marginBottom: t.space[3], borderRadius: t.radius.pill,
        background: t.color.surfaceSunken, border: `1px solid ${t.color.border}`,
        display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22, color: t.color.inkSubtle,
      }}>{notFound ? "?" : icon}</div>
      <div style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[1] }}>{ttl}</div>
      {desc && <div style={{ fontSize: t.font.size.sm, maxWidth: 360, margin: "0 auto", lineHeight: t.font.lineHeight.relaxed }}>{desc}</div>}
      {action && <div style={{ marginTop: t.space[5] }}>{action}</div>}
    </div>
  );
}

/* --- 2.9 Skeleton (additive) — minimalist loading placeholder ----------- */
export function Skeleton({ w = "100%", h = 12, style }) {
  return (
    <span style={{
      display: "block", width: w, height: h, borderRadius: t.radius.sm,
      background: `linear-gradient(90deg, ${t.color.neutral[100]} 25%, ${t.color.neutral[50]} 37%, ${t.color.neutral[100]} 63%)`,
      backgroundSize: "400% 100%", animation: "khe-shimmer 1.4s ease infinite", ...style,
    }} />
  );
}

/* ===========================================================================
 * 3. SHOWCASE
 * ========================================================================= */
function Section({ title, note, children }) {
  return (
    <section style={{ marginBottom: t.space[10] }}>
      <h2 style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.semibold, color: t.color.ink, margin: 0, letterSpacing: t.font.tracking.snug }}>{title}</h2>
      {note && <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1], maxWidth: 620, lineHeight: t.font.lineHeight.relaxed }}>{note}</p>}
      <div style={{ marginTop: t.space[5], display: "flex", flexWrap: "wrap", gap: t.space[4], alignItems: "flex-start" }}>{children}</div>
    </section>
  );
}

function Swatch({ name, hex, ink }) {
  return (
    <div style={{ width: 104, fontFamily: t.font.family }}>
      <div style={{ height: 52, borderRadius: t.radius.md, background: hex, border: `1px solid ${t.color.border}` }} />
      <div style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, marginTop: 6, color: t.color.ink }}>{name}</div>
      <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, fontVariantNumeric: "tabular-nums" }}>{hex}</div>
    </div>
  );
}

export default function DesignSystemShowcaseV2() {
  const [modal, setModal] = useState(false);

  const docRows = [
    { ten: "HĐ thuê mặt bằng Q7", doi_tac: "Cty TNHH Hải Đăng", han: "30/09/2026", status: "extracted" },
    { ten: "HĐ cung cấp bao bì", doi_tac: "Cty CP Bao Bì Việt", han: "15/07/2026", status: "needs_review" },
    { ten: "HĐ lao động — N.V.An", doi_tac: "—", han: "Vô thời hạn", status: "processing" },
  ];
  const cols = [
    { key: "ten", label: "Tài liệu" }, { key: "doi_tac", label: "Đối tác" },
    { key: "han", label: "Ngày hết hạn" }, { key: "status", label: "Trạng thái" },
  ];

  return (
    <div style={{ background: t.color.surfaceAlt, minHeight: "100vh", padding: t.space[8], fontFamily: t.font.family }}>
      <style>{`
        @keyframes khe-spin{to{transform:rotate(360deg)}}
        @keyframes khe-fade{from{opacity:0}to{opacity:1}}
        @keyframes khe-pop{from{opacity:0;transform:translateY(8px) scale(.98)}to{opacity:1;transform:none}}
        @keyframes khe-shimmer{0%{background-position:100% 0}100%{background-position:0 0}}
      `}</style>

      <header style={{ marginBottom: t.space[10], maxWidth: 720 }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Design System</span>
        <div style={{ fontSize: t.font.size["4xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, marginTop: t.space[2] }}>Khế v0.2</div>
        <p style={{ fontSize: t.font.size.md, color: t.color.inkMuted, marginTop: t.space[2], lineHeight: t.font.lineHeight.relaxed }}>
          Minimalist revamp — neutral-dominant, one confident accent, soft layered elevation, focus rings & AA contrast.
          Cùng API với v0.1: các mockup khác nâng cấp chỉ bằng cách đổi đường dẫn import.
        </p>
      </header>

      {/* TOKENS */}
      <Section title="Neutral ramp" note="11 bậc slate — nền tảng của hệ minimalist. Mọi text/border/surface là một bậc, không hex tuỳ ý.">
        {Object.entries(neutral).map(([k, v]) => <Swatch key={k} name={`neutral.${k}`} hex={v} />)}
      </Section>

      <Section title="Brand & semantic" note="Một accent (khế-emerald) dùng tiết chế. Semantic ở mức 700 — đủ rõ, không chói.">
        <Swatch name="primary" hex={t.color.primary} />
        <Swatch name="primaryHover" hex={t.color.primaryHover} />
        <Swatch name="primarySoft" hex={t.color.primarySoft} />
        <Swatch name="success" hex={t.color.success} />
        <Swatch name="warning" hex={t.color.warning} />
        <Swatch name="danger" hex={t.color.danger} />
        <Swatch name="info" hex={t.color.info} />
      </Section>

      <Section title="Typography" note="Inter / Be Vietnam Pro. Display sizes tracking âm nhẹ; body line-height thoáng cho dấu tiếng Việt.">
        <div style={{ width: "100%" }}>
          {[["4xl","Khế — nhắc đúng hạn",t.font.weight.bold,t.font.tracking.tight],
            ["2xl","Nghĩa vụ & hạn",t.font.weight.semibold,t.font.tracking.snug],
            ["lg","Hợp đồng thuê mặt bằng Q7",t.font.weight.semibold,t.font.tracking.snug],
            ["base","Khế chỉ trả lời từ tài liệu bạn đã tải lên — không phỏng đoán.",t.font.weight.regular,t.font.tracking.normal],
            ["sm","Nhãn phụ / chú thích",t.font.weight.medium,t.font.tracking.normal]].map(([sz,txt,w,tr]) => (
            <div key={sz} style={{ display: "flex", alignItems: "baseline", gap: t.space[4], marginBottom: t.space[3] }}>
              <span style={{ width: 64, flexShrink: 0, fontSize: t.font.size.xs, color: t.color.inkSubtle, fontVariantNumeric: "tabular-nums" }}>{sz} · {t.font.size[sz]}px</span>
              <span style={{ fontSize: t.font.size[sz], fontWeight: w, letterSpacing: tr, color: t.color.ink, lineHeight: t.font.lineHeight.snug }}>{txt}</span>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Spacing · Radius · Elevation">
        <div style={{ display: "flex", gap: t.space[3], flexWrap: "wrap", alignItems: "flex-end" }}>
          {Object.entries(t.space).filter(([k]) => k !== "0").map(([k, v]) => (
            <div key={k} style={{ textAlign: "center" }}>
              <div style={{ width: v, height: v, background: t.color.primary, borderRadius: t.radius.xs }} />
              <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: 4 }}>{k}</div>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: t.space[3], marginLeft: t.space[6] }}>
          {Object.entries(t.radius).map(([k, v]) => (
            <div key={k} style={{ textAlign: "center" }}>
              <div style={{ width: 48, height: 48, background: t.color.surface, border: `1px solid ${t.color.borderStrong}`, borderRadius: v }} />
              <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: 4 }}>{k}</div>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: t.space[5], marginLeft: t.space[6] }}>
          {["e1","e2","e3"].map((e) => (
            <div key={e} style={{ textAlign: "center" }}>
              <div style={{ width: 72, height: 48, background: t.color.surface, borderRadius: t.radius.md, boxShadow: t.elevation[e], border: `1px solid ${t.color.border}` }} />
              <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: 6 }}>{e}</div>
            </div>
          ))}
        </div>
      </Section>

      {/* COMPONENTS */}
      <Section title="Button" note="primary · secondary · subtle · ghost · danger — flat, hover darkens, focus hiện ring. (Tab để thấy focus ring.)">
        <Button>Lưu tài liệu</Button>
        <Button variant="secondary">Hủy</Button>
        <Button variant="subtle">Bỏ qua</Button>
        <Button variant="ghost">Xem thêm</Button>
        <Button variant="danger">Thu hồi quyền</Button>
        <Button loading>Đang xử lý</Button>
        <Button disabled>Disabled</Button>
        <Button iconOnly aria-label="add">＋</Button>
      </Section>

      <Section title="Input" note="Focus ring + border đổi màu accent. D-07: hover field bóc-tách → nút ✎ Sửa.">
        <div style={{ width: 280 }}><Input label="Tên đăng nhập" placeholder="vd: linh.ketoan" hint="Tài khoản do firm cấp" /></div>
        <div style={{ width: 280 }}><Input label="Ngày hết hạn (bóc tự động)" value="30/09/2026" editable onEdit={() => {}} /></div>
        <div style={{ width: 280 }}><Input label="Mật khẩu" type="password" value="123" error="Tối thiểu 8 ký tự" /></div>
      </Section>

      <Section title="Card" note="Hairline border + elevation e1; interactive → nhấc lên e2 khi hover.">
        <Card title="HĐ thuê mặt bằng Q7" subtitle="Cty TNHH Hải Đăng" interactive footer={<Button size="sm" variant="secondary">Xem chi tiết</Button>} style={{ width: 320 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: t.font.size.base }}>
            <span style={{ color: t.color.inkMuted }}>Ngày hết hạn</span>
            <strong style={{ color: t.color.ink, fontVariantNumeric: "tabular-nums" }}>30/09/2026</strong>
          </div>
        </Card>
      </Section>

      <Section title="Table" note="Micro-header chữ hoa, hàng hairline, hover nền nhạt.">
        <div style={{ width: "100%", maxWidth: 660, background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, padding: t.space[2] }}>
          <Table columns={cols} rows={docRows}
            renderCell={(key, row) => key === "status"
              ? <Badge kind={row.status} dot>{({processing:"đang xử lý",extracted:"đã bóc tách",needs_review:"cần kiểm tra"})[row.status]}</Badge>
              : row[key]} />
        </div>
      </Section>

      <Section title="Modal" note="Centered, scrim mềm, e3, scale-in. Dùng cho consent NĐ 13 + xác nhận destructive.">
        <Button onClick={() => setModal(true)}>Mở Modal</Button>
        <Modal open={modal} title="Đồng ý chia sẻ dữ liệu" onClose={() => setModal(false)}
          footer={<>
            <Button variant="ghost" onClick={() => setModal(false)}>Từ chối</Button>
            <Button onClick={() => setModal(false)}>Đồng ý</Button>
          </>}>
          Bạn đồng ý cho đại lý thuế xem danh mục hợp đồng để được nhắc hạn chủ động? Có thể thu hồi bất cứ lúc nào. (NĐ 13/2023)
        </Modal>
      </Section>

      <Section title="Toast">
        <Toast kind="success">Đã lưu — ghi Event</Toast>
        <Toast kind="error">Gửi nhắc thất bại</Toast>
        <Toast kind="info">Đang đọc tài liệu…</Toast>
      </Section>

      <Section title="Badge · Confidence (FR-EX-05)" note="Pill tint nhạt + viền; dot tuỳ chọn. Confidence <80% → cảnh báo.">
        <Badge kind="processing" dot>đang xử lý</Badge>
        <Badge kind="extracted" dot>đã bóc tách</Badge>
        <Badge kind="needs_review" dot>cần kiểm tra</Badge>
        <Badge kind="due_soon">sắp hết hạn</Badge>
        <Badge kind="overdue">quá hạn</Badge>
        <Badge kind="done">hoàn thành</Badge>
        <Badge kind="brand">Đợt 2/3</Badge>
        <ConfidenceMeter value={0.96} />
        <ConfidenceMeter value={0.62} />
      </Section>

      <Section title="EmptyState · Skeleton" note="Nhiều khoảng trắng, icon nhạt. D-08 chat 'không tìm thấy'.">
        <div style={{ width: 340, background: t.color.surface, borderRadius: t.radius.lg, border: `1px solid ${t.color.border}` }}>
          <EmptyState icon="＋" title="Chưa có tài liệu" description="Tải lên hợp đồng đầu tiên để Khế bắt đầu nhắc hạn." action={<Button>Tải tài liệu</Button>} />
        </div>
        <div style={{ width: 340, background: t.color.surface, borderRadius: t.radius.lg, border: `1px solid ${t.color.border}` }}>
          <EmptyState notFound />
        </div>
        <div style={{ width: 280, background: t.color.surface, borderRadius: t.radius.lg, border: `1px solid ${t.color.border}`, padding: t.space[5], display: "flex", flexDirection: "column", gap: t.space[3] }}>
          <Skeleton w="60%" h={14} /><Skeleton /><Skeleton w="80%" /><Skeleton w="40%" />
        </div>
      </Section>
    </div>
  );
}
