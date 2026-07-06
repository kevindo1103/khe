/**
 * Servanda — Design System v1.1 "Sổ cái"  (mockup_design_system_v1.1.jsx)
 * KHE_Designer · issue #470 · Kevin ratified 2026-07-03 (#467, #469)
 * STATIC PROTOTYPE ONLY — scope docs/mockup_*.jsx. Self-contained: inline styles
 * driven by `tokens` so it renders with zero build. Production re-expresses these
 * as a Tailwind/CSS-vars theme.
 * ----------------------------------------------------------------------------
 * PROVENANCE — this is NOT a v0.2 revision. It replaces v0.2 as the canonical
 *   system per Kevin's ratification on #469 (closed), after a confused PM relay
 *   history on #467 (v1.0 proposed → wrongly retracted as unratified → Kevin
 *   overrode the retraction and kept v1.0 → promoted to v1.1 by folding 3
 *   specific strengths OF v0.2 into it — see "WHAT WAS FOLDED FROM v0.2" below).
 *   Full token table + fold rationale: #467 comment (2026-07-03T04:45) and the
 *   #469 resolution comment (2026-07-03T04:45).
 *
 * ⚠️ DOES NOT INHERIT v0.2's COLOR/FONT/RADIUS TOKENS. Different primary
 *   (`#1E5C49` vs v0.2's `#0F7A56`), different ink/neutral ramp (warm paper vs
 *   cool slate), different font pairing (Be Vietnam Pro + Source Serif 4 vs
 *   Inter-only), different radius scale (6/10/pill vs xs–2xl). Do not mix files.
 *   v0.2 (`mockup_design_system_v0.2.jsx`) is SUPERSEDED for new mockups.
 *   NOT retroactive: PR #468 (#467) stays on v0.2 — grandfathered, already
 *   reviewed, not touched again for token reasons. Migrate-on-touch only.
 *
 * WHAT WAS FOLDED FROM v0.2 (the only 3 things kept, everything else is new):
 *   1. MEASURED CONTRAST, NOT ASSERTED — v0.2 pioneered "verify every token pair
 *      against WCAG 2.1, write the ratio in the comment." Auditing v1.0 this way
 *      surfaced a REAL gap: n-300 (1.46:1) / n-400 (2.08:1) fail 3:1, so they
 *      can't be used as a visible border for an input/button (WCAG 1.4.11).
 *      Fix: added `borderStrong` (#7E8983, 3.47:1) — the ONLY acceptable border
 *      for interactive components. n-200/n-300 remain, but decorative-only now.
 *   2. THE #206 A11Y HANDOFF CONTRACT, FOLDED WHOLESALE — semantic-element
 *      mandate (button/a, never div onClick), keyboard operability, LiveRegion
 *      for self-changing text, mandatory aria-label on icon-only controls.
 *      Ported 4 components verbatim in spirit: NavItem, IconButton, Dropzone,
 *      LiveRegion (+ VisuallyHidden helper).
 *   3. LAYERED ELEVATION WITH A RATIONALE — v1.0 had one flat shadow, which
 *      made a modal and a resting card read at the same visual "height." Now
 *      e0–e3, metaphor is "paper stacked in layers" (fits the Ledger
 *      philosophy — NOT borrowed from another app's glass/material metaphor).
 *
 * THE "SỔ CÁI" (LEDGER) PHILOSOPHY — 5 principles derived from D-rules:
 *   1. A ledger, not a startup dashboard. Warm paper ground, dark ink, no
 *      gradients, no glassmorphism. The product records facts; it doesn't sell.
 *   2. State never lies (D-08) — including "Chưa rõ hướng." An unknown state
 *      is shown as unknown, never guessed into a plausible-looking default.
 *   3. Urgency must be EARNED (Von Restorff). Red is a scarce resource — spend
 *      it only on genuinely overdue/destructive things, never decoratively.
 *   4. SERIF = the contract's own words. SANS = the software's words (D-06).
 *      Any verbatim clause quote renders in Source Serif 4; every UI chrome
 *      element (labels, buttons, nav) stays Be Vietnam Pro. This is a hard
 *      rule, not a style choice — it lets a user's eye tell instantly "this is
 *      what THEY signed" vs "this is what THE SOFTWARE is telling you."
 *   5. Confirmation is a ritual, not a click. Readback → decide → record
 *      (D-02). No dark patterns, no pre-ticked boxes, no auto-proceeding
 *      countdown (D-11 — never paywall or rush the safety-critical path).
 *
 * ICON RULE: absolute ban on icon/emoji for business/status meaning. State is
 *   ALWAYS a text badge (see the 13-entry vocabulary below), never a glyph.
 *   ONE exception: `IconButton` — a single functional control (not a status
 *   signal) in a tight space, and even then `label` (→ aria-label) is
 *   mandatory. If you reach for an icon to communicate "overdue" or "done,"
 *   you are using the wrong tool — use Badge.
 *
 * 13 CANONICAL STATUS BADGES (vocabulary — do not invent new labels outside
 *   this list without a PM ratification comment):
 *   Quá hạn N ngày (danger, solid) · Hôm nay / Còn N ngày (warn, solid) ·
 *   ngày tương lai (neutral, outline) · Chờ kích hoạt / Chờ xác nhận (info,
 *   solid) · Phạt (danger, OUTLINE — visually distinct from solid-fill
 *   overdue) · Đã hoàn thành / Đã thanh lý (done — quiet gray, solid, NEVER
 *   celebratory green) · Đã hủy (done, solid + line-through) · Chưa rõ hướng
 *   (neutral, outline — pairs with a Settings link, see Banner example below)
 *   · Đợt 07/14 (primary, solid) · Nhập tay / AI · đã duyệt (neutral,
 *   outline — 2-tier provenance per DEC-055).
 *
 * 8 HARD COLOR RULES:
 *   1. Danger is exclusive to overdue + destructive actions — never decorative.
 *   2. Max ONE red zone visible per screen at a time (Von Restorff — if
 *      everything is urgent, nothing is).
 *   3. Completion reads as quiet gray (`done` token), NEVER celebratory green.
 *      There is no `success` token in this system — that key does not exist,
 *      on purpose, to stop a v0.2 habit of reaching for green-means-good.
 *   4. Color is never the SOLE channel of meaning — every badge also differs
 *      by solid-vs-outline treatment or by text, so a colorblind reader still
 *      gets the signal.
 *   5. No gradients, anywhere.
 *   6. Elevation communicated via e0–e3 tokens only — never an ad-hoc shadow.
 *   7. `borderStrong` is the ONLY border for interactive components — n-200/
 *      n-300 are for decorative dividers/card edges, they fail 3:1 alone.
 *   8. One primary-filled button per visible viewport — every other action is
 *      secondary/ghost/outline (Tesler's Law: push the "what matters most"
 *      decision onto the designer, not the user scanning five loud buttons).
 *
 * VOICE: address the user as "bạn," the product refers to itself as
 *   "Servanda," never uses exclamation marks, states facts before framing,
 *   and every error explains WHAT went wrong + WHY + HOW to fix it (see the
 *   Input error example in the showcase).
 *
 * 11 UI/UX LAWS — used by QC as a verification checklist at gate step 3 for
 *   every mockup: Jakob's Law (familiar patterns unless there's a reason not
 *   to), Hick's Law (fewer choices decide faster — see Tabs/Button rules),
 *   Miller's Law (7±2 — bucket long obligation lists, don't dump them flat),
 *   Fitts's Law (primary actions large + reachable — 44px touch targets kept
 *   from v0.2), Von Restorff (color rule #2 above), Gestalt (proximity/
 *   grouping over borders where possible), Doherty Threshold (<400ms feedback
 *   — Toast/optimistic UI), Peak-End Rule (the confirmation ritual is the
 *   "peak" — make ReadbackModal feel deliberate, not rushed), Tesler's Law
 *   (complexity moved to the system, not the user — see color rule #8),
 *   Postel's Law (be liberal in what you accept — Input never blocks typing,
 *   only validates on blur/submit), Aesthetic-Usability Effect (a clean
 *   ledger is perceived as more trustworthy — this is why restraint matters
 *   here more than most products).
 */

import React, { useState } from "react";

/* ===========================================================================
 * 1. TOKENS
 * ========================================================================= */

export const tokens = {
  color: {
    /* --- ground --- */
    paper: "#FBFAF7",   // app background — warm, not pure white (Ledger ground)
    surface: "#FFFFFF", // cards / raised surfaces sit on paper

    /* --- ink (text) --- */
    ink: "#1C2420",       // 15.21:1 on paper — headings, primary text
    inkMuted: "#5A6660",  // 5.74:1 on paper — labels, secondary text, body copy
    inkFaint: "#8B948F",  // 2.99:1 on paper — INTENTIONALLY sub-AA. Placeholder/
                           // disabled text ONLY. Never meaningful copy.

    /* --- borders --- */
    borderStrong: "#7E8983", // 3.47:1 on paper (WCAG 1.4.11 pass). The ONLY
                              // border for interactive components: input,
                              // button, checkbox, select. Do not use n200/n300.
    n200: "#E6E5DE", // decorative divider / card edge ONLY — fails 3:1 alone
    n300: "#D2D2C9", // decorative divider (slightly stronger) — same caveat

    /* --- brand: "Lục Khế" (Khế Green) --- */
    primary: "#1E5C49",      // 7.5:1 on paper
    primaryHover: "#174A3B",
    primarySoft: "#EAF1EC",  // tint surface (selected nav, series badge fill)

    /* --- semantic (each has exactly one job, each has a tint) --- */
    danger: "#A6372B", danger_soft: "#F7ECEA",  // overdue + destructive ONLY
    warning: "#8A5800", warning_soft: "#F9F1DF", // due today / due soon / attention
    info: "#33597E", info_soft: "#EBF0F5",       // waiting on something external
    done: "#5A6660", done_soft: "#F0F0EB",       // completion — quiet, not green
                                                   // (there is deliberately no
                                                   // `success` token in v1.1)

    /* --- misc --- */
    overlay: "rgba(28,36,32,0.42)",
    ring: "rgba(30,92,73,0.35)", // focus ring, tuned to new primary
  },

  font: {
    /* UI chrome — Be Vietnam Pro. Self-host the Vietnamese subset in prod. */
    family: "'Be Vietnam Pro', system-ui, -apple-system, 'Segoe UI', sans-serif",
    /* Contract verbatim text ONLY (D-06) — never for UI chrome, labels, or nav. */
    familySerif: "'Source Serif 4', Georgia, 'Times New Roman', serif",
    /* 6-step scale, exactly as ratified: 28/22/16/15/13.5/12.5 + 11 uppercase label */
    size: { label: 11, xs: 12.5, sm: 13.5, base: 15, lg: 16, xl: 22, display: 28 },
    /* only 3 weights, on purpose — a 4th weight is a design-review flag */
    weight: { regular: 400, medium: 500, semibold: 600 },
    lineHeight: { tight: 1.2, snug: 1.35, normal: 1.5, relaxed: 1.65, serif: 1.7 },
    tracking: { tight: "-0.01em", normal: "0", label: "0.06em" }, // label = uppercase tracking
  },

  /* 4px rhythm, exactly as ratified: 4/8/12/16/24/32/48/64 */
  space: { 0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32, 7: 48, 8: 64 },

  radius: { control: 6, card: 10, pill: 999 },

  /* "paper stacked in layers" — NOT a borrowed glass/material metaphor */
  elevation: {
    e0: "none",
    e1: "0 1px 2px rgba(28,36,32,0.06)",
    e2: "0 2px 6px rgba(28,36,32,0.09)",
    e3: "0 16px 32px rgba(28,36,32,0.20)",
  },

  motion: { fast: "120ms", base: "180ms", ease: "cubic-bezier(0.2, 0, 0, 1)" },

  z: { base: 0, sticky: 100, overlay: 1000, modal: 1100, toast: 1200 },

  layout: { maxWidth: 880 }, // content column cap, ratified
};

const t = tokens;
const ringStyle = { boxShadow: `0 0 0 3px ${t.color.ring}` };

/* tone → tint lookup, used by Badge's solid variant */
const TONE_TINT = {
  [t.color.danger]: t.color.danger_soft,
  [t.color.warning]: t.color.warning_soft,
  [t.color.info]: t.color.info_soft,
  [t.color.done]: t.color.done_soft,
  [t.color.primary]: t.color.primarySoft,
};

/* ===========================================================================
 * 2. COMPONENTS
 * ========================================================================= */

function useFocusRing() {
  const [focus, setFocus] = useState(false);
  return { focus, bind: { onFocus: () => setFocus(true), onBlur: () => setFocus(false) } };
}

/* --- 2.1 Button — 4 tiers. Rule: ONE primary per visible viewport (color rule #8). */
export function Button({
  children, variant = "primary", size = "md",
  loading = false, disabled = false, onClick, style, iconOnly = false,
}) {
  const { focus, bind } = useFocusRing();
  const [hover, setHover] = useState(false);

  const sizes = {
    sm: { height: 32, padding: iconOnly ? 0 : `0 ${t.space[3]}px`, width: iconOnly ? 32 : undefined, fontSize: t.font.size.sm },
    md: { height: 44, padding: iconOnly ? 0 : `0 ${t.space[4]}px`, width: iconOnly ? 44 : undefined, fontSize: t.font.size.base },
    lg: { height: 48, padding: iconOnly ? 0 : `0 ${t.space[5]}px`, width: iconOnly ? 48 : undefined, fontSize: t.font.size.lg },
  };
  const variants = {
    primary:   { bg: t.color.primary, bgHover: t.color.primaryHover, fg: "#fff", border: "transparent" },
    secondary: { bg: t.color.surface, bgHover: t.color.paper, fg: t.color.ink, border: t.color.borderStrong },
    subtle:    { bg: t.color.done_soft, bgHover: t.color.n200, fg: t.color.ink, border: "transparent" },
    ghost:     { bg: "transparent", bgHover: t.color.paper, fg: t.color.primary, border: "transparent" },
    danger:    { bg: t.color.danger, bgHover: "#8A2E24", fg: "#fff", border: "transparent" },
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
        border: `1px solid ${v.border}`, borderRadius: t.radius.control,
        fontFamily: t.font.family, fontWeight: t.font.weight.semibold, letterSpacing: t.font.tracking.normal,
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
      border: `2px solid ${light ? "rgba(255,255,255,.45)" : t.color.n300}`,
      borderTopColor: light ? "#fff" : t.color.primary,
      animation: "servanda-spin .6s linear infinite",
    }} />
  );
}

/* --- 2.2 Input — label-above, error says what+why+how-to-fix (voice rule). */
export function Input({
  label, value, onChange, placeholder, hint, error,
  editable = false, onEdit, type = "text", style, prefix,
}) {
  const { focus, bind } = useFocusRing();
  const [hover, setHover] = useState(false);
  const borderColor = error ? t.color.danger : focus ? t.color.primary : t.color.borderStrong;
  return (
    <label style={{ display: "block", fontFamily: t.font.family, ...style }}>
      {label && (
        <span style={{ display: "block", fontSize: t.font.size.sm, fontWeight: t.font.weight.medium, color: t.color.ink, marginBottom: t.space[1] }}>
          {label}
        </span>
      )}
      <div
        onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
        style={{
          display: "flex", alignItems: "center", gap: t.space[2],
          height: 44, padding: `0 ${t.space[3]}px`, background: t.color.surface,
          border: `1px solid ${borderColor}`, borderRadius: t.radius.control,
          transition: `border-color ${t.motion.fast} ${t.motion.ease}, box-shadow ${t.motion.fast} ${t.motion.ease}`,
          ...(focus ? ringStyle : null),
        }}
      >
        {prefix && <span style={{ color: t.color.inkFaint, fontSize: t.font.size.base }}>{prefix}</span>}
        <input
          {...bind}
          type={type} value={value} placeholder={placeholder}
          onChange={(e) => onChange && onChange(e.target.value)}
          style={{
            flex: 1, minWidth: 0, border: "none", outline: "none", background: "transparent",
            fontSize: t.font.size.base, color: t.color.ink, fontFamily: t.font.family,
            fontVariantNumeric: "tabular-nums",
          }}
        />
        {editable && (hover || focus) && (
          <button onClick={onEdit} title="Sửa (ghi Event)" style={{
            background: t.color.primarySoft, color: t.color.primary, border: "none",
            borderRadius: t.radius.control, fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold,
            padding: `2px ${t.space[2]}px`, cursor: "pointer",
          }}>Sửa</button>
        )}
      </div>
      {error ? (
        <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.danger, marginTop: t.space[1], lineHeight: t.font.lineHeight.snug }}>{error}</span>
      ) : hint ? (
        <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: t.space[1] }}>{hint}</span>
      ) : null}
    </label>
  );
}

/* --- 2.3 Card ------------------------------------------------------------ */
export function Card({ title, subtitle, footer, children, style, interactive = false }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        background: t.color.surface, border: `1px solid ${t.color.n200}`,
        borderRadius: t.radius.card, overflow: "hidden", fontFamily: t.font.family,
        boxShadow: interactive && hover ? t.elevation.e2 : t.elevation.e1,
        transition: `box-shadow ${t.motion.base} ${t.motion.ease}`,
        ...style,
      }}
    >
      {(title || subtitle) && (
        <div style={{ padding: `${t.space[4]}px ${t.space[5]}px`, borderBottom: `1px solid ${t.color.n200}` }}>
          {title && <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{title}</div>}
          {subtitle && <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>{subtitle}</div>}
        </div>
      )}
      <div style={{ padding: t.space[5] }}>{children}</div>
      {footer && (
        <div style={{ padding: `${t.space[3]}px ${t.space[5]}px`, borderTop: `1px solid ${t.color.n200}`, background: t.color.paper }}>{footer}</div>
      )}
    </div>
  );
}

/* --- 2.4 Table ------------------------------------------------------------ */
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
                fontSize: t.font.size.label, textTransform: "uppercase", letterSpacing: t.font.tracking.label,
                borderBottom: `1px solid ${t.color.n200}`, whiteSpace: "nowrap",
              }}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}
              onMouseEnter={() => setHoverRow(i)} onMouseLeave={() => setHoverRow(-1)}
              style={{ background: hoverRow === i ? t.color.paper : "transparent", transition: `background ${t.motion.fast} ${t.motion.ease}` }}>
              {columns.map((c) => (
                <td key={c.key} style={{ padding: `${t.space[3]}px`, color: t.color.ink, borderBottom: `1px solid ${t.color.n200}`, fontVariantNumeric: "tabular-nums" }}>
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

/* --- 2.5 Modal ------------------------------------------------------------ */
export function Modal({ open, title, children, onClose, footer }) {
  if (!open) return null;
  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: t.color.overlay, zIndex: t.z.modal,
      display: "flex", alignItems: "center", justifyContent: "center", padding: t.space[4],
      animation: `servanda-fade ${t.motion.base} ${t.motion.ease}`,
    }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: t.color.surface, borderRadius: t.radius.card, boxShadow: t.elevation.e3,
        width: "100%", maxWidth: 440, fontFamily: t.font.family, border: `1px solid ${t.color.n200}`,
        animation: `servanda-pop ${t.motion.base} ${t.motion.ease}`,
      }}>
        <div style={{ padding: `${t.space[5]}px ${t.space[5]}px ${t.space[2]}px` }}>
          <div style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{title}</div>
        </div>
        <div style={{ padding: `0 ${t.space[5]}px`, color: t.color.ink, fontSize: t.font.size.base, lineHeight: t.font.lineHeight.relaxed }}>{children}</div>
        <div style={{ padding: t.space[5], display: "flex", gap: t.space[2], justifyContent: "flex-end" }}>{footer}</div>
      </div>
    </div>
  );
}

/* --- 2.5b ContractQuote — D-06: serif = the contract's own words. -------- */
export function ContractQuote({ children, source }) {
  return (
    <div style={{
      borderLeft: `3px solid ${t.color.n300}`, paddingLeft: t.space[4],
      fontFamily: t.font.familySerif, fontSize: t.font.size.base,
      lineHeight: t.font.lineHeight.serif, color: t.color.ink, fontStyle: "normal",
    }}>
      <div>{children}</div>
      {source && (
        <div style={{
          marginTop: t.space[2], fontFamily: t.font.family, fontSize: t.font.size.label,
          fontWeight: t.font.weight.medium, color: t.color.inkMuted, textTransform: "uppercase",
          letterSpacing: t.font.tracking.label,
        }}>{source}</div>
      )}
    </div>
  );
}

/* --- 2.5c ReadbackModal — D-02 ritual: readback → decide → record. ------- */
export function ReadbackModal({ open, quote, source, statement, onConfirm, onCancel, confirmLabel = "Xác nhận", cancelLabel = "Huỷ" }) {
  if (!open) return null;
  return (
    <Modal open={open} title="Xác nhận trước khi ghi nhận" onClose={onCancel} footer={
      <>
        <Button variant="ghost" onClick={onCancel}>{cancelLabel}</Button>
        <Button onClick={onConfirm}>{confirmLabel}</Button>
      </>
    }>
      <div style={{ marginBottom: t.space[4] }}>
        <ContractQuote source={source}>{quote}</ContractQuote>
      </div>
      <div style={{ fontSize: t.font.size.base, color: t.color.ink }}>{statement}</div>
    </Modal>
  );
}

/* --- 2.6 Toast — including event-chain narration. -------------------------*/
export function Toast({ kind = "info", children }) {
  const map = {
    done: { fg: t.color.done, label: "Đã ghi" },
    error: { fg: t.color.danger, label: "Lỗi" },
    info: { fg: t.color.info, label: "Thông tin" },
  };
  const s = map[kind] || map.info;
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: t.space[2],
      background: t.color.surface, color: t.color.ink, fontFamily: t.font.family,
      padding: `${t.space[2]}px ${t.space[4]}px`, borderRadius: t.radius.control,
      border: `1px solid ${t.color.n200}`, boxShadow: t.elevation.e2,
      fontSize: t.font.size.base, fontWeight: t.font.weight.medium,
    }}>
      <span style={{
        fontSize: t.font.size.label, fontWeight: t.font.weight.semibold, color: s.fg,
        textTransform: "uppercase", letterSpacing: t.font.tracking.label,
      }}>{s.label}</span>
      {children}
    </div>
  );
}

/* --- 2.7 Badge — the 13-entry status vocabulary. NO icons, ever. --------- */
const BADGE_KINDS = {
  overdue:    { tone: t.color.danger,  variant: "solid" },   // "Quá hạn N ngày"
  dueSoon:    { tone: t.color.warning, variant: "solid" },   // "Hôm nay" / "Còn N ngày"
  future:     { tone: t.color.inkMuted, variant: "outline" },// future date
  waiting:    { tone: t.color.info,    variant: "solid" },   // "Chờ kích hoạt" / "Chờ xác nhận"
  penalty:    { tone: t.color.danger,  variant: "outline" }, // "Phạt" — distinct from solid overdue
  done:       { tone: t.color.done,    variant: "solid" },   // "Đã hoàn thành" / "Đã thanh lý"
  cancelled:  { tone: t.color.done,    variant: "solid", strike: true }, // "Đã hủy"
  unclear:    { tone: t.color.inkMuted, variant: "outline" },// "Chưa rõ hướng" — pairs with a link
  series:     { tone: t.color.primary, variant: "solid" },   // "Đợt 07/14"
  manual:     { tone: t.color.inkMuted, variant: "outline" },// "Nhập tay"
  aiVerified: { tone: t.color.inkMuted, variant: "outline" },// "AI · đã duyệt"
};
export function Badge({ kind = "future", children }) {
  const k = BADGE_KINDS[kind] || BADGE_KINDS.future;
  const solid = k.variant === "solid";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      fontFamily: t.font.family, fontSize: t.font.size.xs, fontWeight: t.font.weight.medium,
      padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill,
      background: solid ? (TONE_TINT[k.tone] || t.color.done_soft) : "transparent",
      color: k.tone, border: solid ? "none" : `1px solid ${k.tone}`,
      textDecoration: k.strike ? "line-through" : "none",
      fontVariantNumeric: "tabular-nums", lineHeight: 1.4,
    }}>
      {children}
    </span>
  );
}

/* --- 2.7b Banner — 3-level, BOLD LABEL replaces icon. Worked example below
 * replaces the old SelfPartyGate emoji dropdown (⚠️) with this pattern. ---- */
const BANNER_LEVELS = {
  info:   { tone: t.color.info,    tint: t.color.info_soft,    label: "Ghi chú" },
  warn:   { tone: t.color.warning, tint: t.color.warning_soft, label: "Cần chú ý" },
  danger: { tone: t.color.danger,  tint: t.color.danger_soft,  label: "Khẩn" },
};
export function Banner({ level = "info", title, description, action }) {
  const l = BANNER_LEVELS[level] || BANNER_LEVELS.info;
  return (
    <div style={{
      display: "flex", gap: t.space[3], alignItems: "center", flexWrap: "wrap",
      padding: `${t.space[3]}px ${t.space[4]}px`, borderRadius: t.radius.control,
      background: l.tint, borderLeft: `3px solid ${l.tone}`, fontFamily: t.font.family,
    }}>
      <div style={{ flex: 1, minWidth: 200 }}>
        <div style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
          <span style={{
            fontSize: t.font.size.label, fontWeight: t.font.weight.semibold, color: l.tone,
            textTransform: "uppercase", letterSpacing: t.font.tracking.label,
          }}>{l.label}</span>
          <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{title}</span>
        </div>
        {description && <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>{description}</div>}
      </div>
      {action}
    </div>
  );
}

/* --- 2.7c ActionBar — bulk selection, inverted-ink background. ----------- */
export function ActionBar({ count, primaryLabel, onPrimary, onCancel, cancelLabel = "Bỏ chọn" }) {
  if (!count) return null;
  return (
    <div style={{
      position: "fixed", bottom: t.space[6], left: "50%", transform: "translateX(-50%)",
      background: t.color.ink, color: t.color.paper, borderRadius: t.radius.card,
      padding: `${t.space[3]}px ${t.space[5]}px`, display: "flex", alignItems: "center", gap: t.space[4],
      boxShadow: t.elevation.e3, zIndex: t.z.toast, fontFamily: t.font.family, minWidth: 320,
    }}>
      <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.medium, fontVariantNumeric: "tabular-nums" }}>{count} mục đã chọn</span>
      <div style={{ flex: 1 }} />
      <button onClick={onPrimary} style={{
        border: "none", background: t.color.primary, color: "#fff", padding: `${t.space[2]}px ${t.space[4]}px`,
        borderRadius: t.radius.control, fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, cursor: "pointer",
        fontFamily: t.font.family,
      }}>{primaryLabel}</button>
      <button onClick={onCancel} style={{
        border: `1px solid ${t.color.inkMuted}`, background: "transparent", color: t.color.n200,
        padding: `${t.space[2]}px ${t.space[3]}px`, borderRadius: t.radius.control, fontSize: t.font.size.sm,
        cursor: "pointer", fontFamily: t.font.family,
      }}>{cancelLabel}</button>
    </div>
  );
}

/* --- 2.7d Tabs — counted, Hick's Law (few options, decide fast). --------- */
export function Tabs({ items, active, onChange }) {
  return (
    <div style={{ display: "flex", gap: t.space[2], borderBottom: `1px solid ${t.color.n200}`, fontFamily: t.font.family }}>
      {items.map((it) => {
        const isActive = it.key === active;
        return (
          <button key={it.key} onClick={() => onChange(it.key)} style={{
            padding: `${t.space[2]}px ${t.space[3]}px`, background: "transparent", border: "none",
            borderBottom: `2px solid ${isActive ? t.color.primary : "transparent"}`, cursor: "pointer",
            fontFamily: t.font.family, fontSize: t.font.size.base,
            fontWeight: isActive ? t.font.weight.semibold : t.font.weight.medium,
            color: isActive ? t.color.primary : t.color.inkMuted,
            display: "flex", alignItems: "center", gap: t.space[2],
          }}>
            {it.label}
            {it.count !== undefined && (
              <span style={{
                fontSize: t.font.size.xs, fontVariantNumeric: "tabular-nums",
                background: isActive ? t.color.primarySoft : t.color.done_soft,
                color: isActive ? t.color.primary : t.color.inkMuted,
                borderRadius: t.radius.pill, padding: `0 ${t.space[2]}px`,
              }}>{it.count}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/* --- 2.8 EmptyState — D-08 honest, never fabricated reassurance. --------- */
export function EmptyState({ title, description, action, notFound = false }) {
  const ttl = notFound ? "Không tìm thấy thông tin này trong hồ sơ của bạn." : title;
  const desc = notFound
    ? "Servanda chỉ trả lời từ tài liệu bạn đã tải lên — không phỏng đoán. Hãy thử hỏi cách khác hoặc tải thêm tài liệu."
    : description;
  return (
    <div style={{ textAlign: "center", padding: `${t.space[7]}px ${t.space[5]}px`, fontFamily: t.font.family, color: t.color.inkMuted }}>
      <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[1] }}>{ttl}</div>
      {desc && <div style={{ fontSize: t.font.size.sm, maxWidth: 360, margin: "0 auto", lineHeight: t.font.lineHeight.relaxed }}>{desc}</div>}
      {action && <div style={{ marginTop: t.space[5] }}>{action}</div>}
    </div>
  );
}

/* --- 2.9 Skeleton ---------------------------------------------------------*/
export function Skeleton({ w = "100%", h = 12, style }) {
  return (
    <span style={{
      display: "block", width: w, height: h, borderRadius: t.radius.control,
      background: `linear-gradient(90deg, ${t.color.n200} 25%, ${t.color.paper} 37%, ${t.color.n200} 63%)`,
      backgroundSize: "400% 100%", animation: "servanda-shimmer 1.4s ease infinite", ...style,
    }} />
  );
}

/* ===========================================================================
 * 2b. A11Y-CORRECT PRIMITIVES — folded wholesale from #206 / v0.2 (fold #2)
 * ---------------------------------------------------------------------------
 * Same contract as v0.2: nav → <a>, action → <button>, locked → <button
 * disabled>, icon glyphs → aria-hidden + visible/aria label, self-changing
 * text → LiveRegion. Re-themed to v1.1 tokens; behavior identical.
 * ========================================================================= */

export function VisuallyHidden({ children, as: As = "span" }) {
  return (
    <As style={{
      position: "absolute", width: 1, height: 1, padding: 0, margin: -1,
      overflow: "hidden", clip: "rect(0 0 0 0)", whiteSpace: "nowrap", border: 0,
    }}>{children}</As>
  );
}

export function LiveRegion({ children, assertive = false, atomic = true, style }) {
  return (
    <div role="status" aria-live={assertive ? "assertive" : "polite"} aria-atomic={atomic}
      style={{ fontFamily: t.font.family, ...style }}>
      {children}
    </div>
  );
}

/* IconButton — the ONE exception to the icon ban. A single functional glyph,
 * never a status signal, `label` is mandatory (becomes aria-label). */
export function IconButton({ icon, label, onClick, disabled = false, size = 44, style }) {
  const { focus, bind } = useFocusRing();
  const [hover, setHover] = useState(false);
  if (!label) console.warn("IconButton: `label` is required (becomes aria-label) — an icon glyph alone is not accessible, and this component must never be used for business/status state (use Badge).");
  return (
    <button
      {...bind} type="button" onClick={disabled ? undefined : onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      disabled={disabled} aria-label={label} title={label}
      style={{
        width: size, height: size, display: "inline-flex", alignItems: "center", justifyContent: "center",
        border: "none", borderRadius: t.radius.control, background: hover && !disabled ? t.color.paper : "transparent",
        color: t.color.ink, fontSize: 16, cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.5 : 1,
        transition: `background ${t.motion.fast} ${t.motion.ease}, box-shadow ${t.motion.fast} ${t.motion.ease}`,
        ...(focus ? ringStyle : null), ...style,
      }}
    >
      <span aria-hidden="true">{icon}</span>
    </button>
  );
}

export function NavItem({
  icon, label, active = false, locked = false, lockedHint = "Chưa mở khoá",
  badgeCount, href, onClick, orientation = "vertical", style,
}) {
  const { focus, bind } = useFocusRing();
  const [hover, setHover] = useState(false);
  const isLink = !locked && !!href;
  const El = isLink ? "a" : "button";
  const horizontal = orientation === "horizontal";

  const elProps = locked
    ? { type: "button", disabled: true, "aria-disabled": true, title: lockedHint }
    : isLink ? { href, onClick } : { type: "button", onClick };

  return (
    <El
      {...bind} {...elProps}
      aria-current={active ? "page" : undefined}
      aria-label={locked ? `${label} (${lockedHint})` : undefined}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        position: "relative", display: "flex", alignItems: "center", gap: t.space[2],
        flexDirection: horizontal ? "column" : "row", justifyContent: horizontal ? "center" : "flex-start",
        width: horizontal ? undefined : "100%", textAlign: "left", textDecoration: "none",
        padding: horizontal ? `${t.space[2]}px ${t.space[3]}px` : `${t.space[2]}px`,
        border: "none", borderRadius: t.radius.control, font: "inherit",
        fontSize: horizontal ? t.font.size.sm : t.font.size.base,
        fontWeight: active ? t.font.weight.semibold : t.font.weight.medium,
        background: active ? t.color.primarySoft : hover && !locked ? t.color.paper : "transparent",
        color: locked ? t.color.inkFaint : active ? t.color.primary : t.color.ink,
        opacity: locked ? 0.6 : 1, cursor: locked ? "not-allowed" : "pointer",
        transition: `background ${t.motion.fast} ${t.motion.ease}, box-shadow ${t.motion.fast} ${t.motion.ease}`,
        ...(focus ? ringStyle : null), ...style,
      }}
    >
      {active && !horizontal && <span aria-hidden="true" style={{ position: "absolute", left: -t.space[2], top: 6, bottom: 6, width: 3, borderRadius: t.radius.pill, background: t.color.primary }} />}
      <span aria-hidden="true" style={{ width: horizontal ? "auto" : 20, textAlign: "center", fontSize: horizontal ? 18 : 15 }}>{icon}</span>
      <span style={{ flex: horizontal ? undefined : 1 }}>{label}</span>
      {locked && <VisuallyHidden>({lockedHint})</VisuallyHidden>}
      {!locked && badgeCount != null && <Badge kind="dueSoon">{badgeCount}</Badge>}
    </El>
  );
}

export function Dropzone({
  label = "Kéo thả tệp vào đây", hint, onActivate, onFiles,
  disabled = false, dragging = false, style,
}) {
  const { focus, bind } = useFocusRing();
  const [over, setOver] = useState(false);
  const active = over || dragging;
  const fire = () => { if (!disabled && onActivate) onActivate(); };
  return (
    <div
      {...bind} role="button" tabIndex={disabled ? -1 : 0} aria-label={label} aria-disabled={disabled || undefined}
      onClick={fire}
      onKeyDown={(e) => { if (!disabled && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); fire(); } }}
      onDragOver={(e) => { e.preventDefault(); if (!disabled) setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); if (!disabled && onFiles) onFiles(e.dataTransfer?.files); }}
      style={{
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: t.space[2],
        padding: `${t.space[7]}px ${t.space[5]}px`, textAlign: "center", fontFamily: t.font.family,
        border: `2px dashed ${active ? t.color.primary : t.color.borderStrong}`, borderRadius: t.radius.card,
        background: active ? t.color.primarySoft : t.color.surface,
        color: t.color.ink, cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.5 : 1,
        transition: `border-color ${t.motion.fast} ${t.motion.ease}, background ${t.motion.fast} ${t.motion.ease}, box-shadow ${t.motion.fast} ${t.motion.ease}`,
        ...(focus ? ringStyle : null), ...style,
      }}
    >
      <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.medium }}>{label}</span>
      {hint && <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>{hint}</span>}
    </div>
  );
}

/* ===========================================================================
 * 3. SHOWCASE
 * ========================================================================= */
function Section({ title, note, children }) {
  return (
    <section style={{ marginBottom: t.space[8] }}>
      <h2 style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.semibold, color: t.color.ink, margin: 0 }}>{title}</h2>
      {note && <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1], maxWidth: 620, lineHeight: t.font.lineHeight.relaxed }}>{note}</p>}
      <div style={{ marginTop: t.space[4], display: "flex", flexWrap: "wrap", gap: t.space[4], alignItems: "flex-start" }}>{children}</div>
    </section>
  );
}

function Swatch({ name, hex }) {
  return (
    <div style={{ width: 104, fontFamily: t.font.family }}>
      <div style={{ height: 52, borderRadius: t.radius.control, background: hex, border: `1px solid ${t.color.n200}` }} />
      <div style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, marginTop: 6, color: t.color.ink }}>{name}</div>
      <div style={{ fontSize: t.font.size.xs, color: t.color.inkFaint, fontVariantNumeric: "tabular-nums" }}>{hex}</div>
    </div>
  );
}

export default function DesignSystemShowcaseV1_1() {
  const [modal, setModal] = useState(false);
  const [readback, setReadback] = useState(false);
  const [tab, setTab] = useState("nghia_vu");
  const [selected, setSelected] = useState(2);

  const docRows = [
    { ten: "HĐ thuê mặt bằng Q7", doi_tac: "Cty TNHH Hải Đăng", han: "30/09/2026" },
    { ten: "HĐ cung cấp bao bì", doi_tac: "Cty CP Bao Bì Việt", han: "15/07/2026" },
    { ten: "HĐ lao động — N.V.An", doi_tac: "—", han: "Vô thời hạn" },
  ];
  const cols = [{ key: "ten", label: "Tài liệu" }, { key: "doi_tac", label: "Đối tác" }, { key: "han", label: "Ngày hết hạn" }];

  return (
    <div style={{ background: t.color.paper, minHeight: "100vh", padding: t.space[6], fontFamily: t.font.family }}>
      <style>{`
        @keyframes servanda-spin{to{transform:rotate(360deg)}}
        @keyframes servanda-fade{from{opacity:0}to{opacity:1}}
        @keyframes servanda-pop{from{opacity:0;transform:translateY(8px) scale(.98)}to{opacity:1;transform:none}}
        @keyframes servanda-shimmer{0%{background-position:100% 0}100%{background-position:0 0}}
      `}</style>

      <header style={{ marginBottom: t.space[7], maxWidth: t.layout.maxWidth }}>
        <span style={{ fontSize: t.font.size.label, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.label }}>Design System</span>
        <div style={{ fontSize: t.font.size.display, fontWeight: t.font.weight.semibold, color: t.color.ink, marginTop: t.space[2], letterSpacing: t.font.tracking.tight }}>Servanda v1.1 — Sổ cái</div>
        <p style={{ fontSize: t.font.size.lg, color: t.color.inkMuted, marginTop: t.space[2], lineHeight: t.font.lineHeight.relaxed, maxWidth: 620 }}>
          Nền giấy ấm, mực sẫm, không gradient. Đỏ là tài nguyên khan hiếm. Nguyên văn hợp đồng luôn serif;
          phần mềm luôn sans. Xác nhận là nghi thức, không phải cú click. Canonical từ 2026-07-03 — thay thế DS v0.2.
        </p>
      </header>

      <Section title="Ground & ink" note="Nền giấy ấm (không trắng tinh), mực gần đen (không đen tuyền). border-strong (mới v1.1) là biên DUY NHẤT cho component tương tác — n200/n300 chỉ để viền trang trí.">
        <Swatch name="paper" hex={t.color.paper} />
        <Swatch name="surface" hex={t.color.surface} />
        <Swatch name="ink" hex={t.color.ink} />
        <Swatch name="inkMuted" hex={t.color.inkMuted} />
        <Swatch name="inkFaint" hex={t.color.inkFaint} />
        <Swatch name="borderStrong" hex={t.color.borderStrong} />
        <Swatch name="n200" hex={t.color.n200} />
        <Swatch name="n300" hex={t.color.n300} />
      </Section>

      <Section title="Brand & semantic" note="Lục Khế (primary). 4 màu nghĩa, mỗi màu một phận sự — không có token `success` (hoàn thành = xám lặng, không xanh ăn mừng, xem 8 luật màu trong header file).">
        <Swatch name="primary" hex={t.color.primary} />
        <Swatch name="primaryHover" hex={t.color.primaryHover} />
        <Swatch name="danger" hex={t.color.danger} />
        <Swatch name="warning" hex={t.color.warning} />
        <Swatch name="info" hex={t.color.info} />
        <Swatch name="done" hex={t.color.done} />
      </Section>

      <Section title="Typography" note="Be Vietnam Pro (UI) + Source Serif 4 (nguyên văn hợp đồng — xem ContractQuote bên dưới). Thang 6 bậc, 3 weight.">
        <div style={{ width: "100%" }}>
          {[["display","Servanda — sổ cái hợp đồng của bạn",t.font.weight.semibold],
            ["xl","Nghĩa vụ & Quyền lợi",t.font.weight.semibold],
            ["lg","Hợp đồng thuê mặt bằng Q7",t.font.weight.medium],
            ["base","Servanda chỉ trả lời từ tài liệu bạn đã tải lên — không phỏng đoán.",t.font.weight.regular],
            ["sm","Nhãn phụ / chú thích",t.font.weight.medium],
            ["label","NHÃN VIẾT HOA",t.font.weight.semibold]].map(([sz,txt,w]) => (
            <div key={sz} style={{ display: "flex", alignItems: "baseline", gap: t.space[4], marginBottom: t.space[3] }}>
              <span style={{ width: 76, flexShrink: 0, fontSize: t.font.size.xs, color: t.color.inkFaint, fontVariantNumeric: "tabular-nums" }}>{sz} · {t.font.size[sz]}px</span>
              <span style={{
                fontSize: t.font.size[sz], fontWeight: w, color: t.color.ink,
                textTransform: sz === "label" ? "uppercase" : "none",
                letterSpacing: sz === "label" ? t.font.tracking.label : t.font.tracking.normal,
              }}>{txt}</span>
            </div>
          ))}
          <div style={{ marginTop: t.space[4] }}>
            <ContractQuote source="Điều 4.1 — Thanh toán">
              Bên B có nghĩa vụ thanh toán cho Bên A số tiền 130.000.000 đồng mỗi tháng, chậm nhất vào ngày 15,
              trong suốt thời hạn 14 tháng kể từ ngày ký.
            </ContractQuote>
          </div>
        </div>
      </Section>

      <Section title="Spacing · Radius · Elevation" note="Nhịp 4px. Radius 6/10/pill. Elevation e0–e3 — ẩn dụ giấy xếp lớp, không phải 1 bóng phẳng.">
        <div style={{ display: "flex", gap: t.space[3], flexWrap: "wrap", alignItems: "flex-end" }}>
          {Object.entries(t.space).filter(([k]) => k !== "0").map(([k, v]) => (
            <div key={k} style={{ textAlign: "center" }}>
              <div style={{ width: v, height: v, background: t.color.primary, borderRadius: t.radius.control / 2 }} />
              <div style={{ fontSize: t.font.size.xs, color: t.color.inkFaint, marginTop: 4 }}>{k}</div>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: t.space[3], marginLeft: t.space[5] }}>
          {Object.entries(t.radius).map(([k, v]) => (
            <div key={k} style={{ textAlign: "center" }}>
              <div style={{ width: 48, height: 48, background: t.color.surface, border: `1px solid ${t.color.borderStrong}`, borderRadius: v }} />
              <div style={{ fontSize: t.font.size.xs, color: t.color.inkFaint, marginTop: 4 }}>{k}</div>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: t.space[5], marginLeft: t.space[5] }}>
          {["e0","e1","e2","e3"].map((e) => (
            <div key={e} style={{ textAlign: "center" }}>
              <div style={{ width: 72, height: 48, background: t.color.surface, borderRadius: t.radius.control, boxShadow: t.elevation[e], border: `1px solid ${t.color.n200}` }} />
              <div style={{ fontSize: t.font.size.xs, color: t.color.inkFaint, marginTop: 6 }}>{e}</div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Button" note="4 cấp — MỘT nút primary mỗi màn hình nhìn thấy (luật màu #8).">
        <Button>Lưu tài liệu</Button>
        <Button variant="secondary">Hủy</Button>
        <Button variant="subtle">Bỏ qua</Button>
        <Button variant="ghost">Xem thêm</Button>
        <Button variant="danger">Thu hồi quyền</Button>
        <Button loading>Đang xử lý</Button>
        <Button disabled>Disabled</Button>
      </Section>

      <Section title="Input" note="Lỗi nói gì+vì sao+cách sửa (giọng Servanda), không chỉ 'Trường bắt buộc'.">
        <div style={{ width: 300 }}><Input label="Tên đăng nhập" placeholder="vd: linh.ketoan" hint="Tài khoản do firm cấp" /></div>
        <div style={{ width: 300 }}><Input label="Ngày hết hạn (bóc tự động)" value="30/09/2026" editable onEdit={() => {}} /></div>
        <div style={{ width: 300 }}>
          <Input label="Mã số thuế" value="12345" error="Mã số thuế cần đủ 10 hoặc 13 số để đối chiếu — hiện chỉ có 5 số. Kiểm tra lại trên giấy đăng ký kinh doanh." />
        </div>
      </Section>

      <Section title="Card · Table">
        <Card title="HĐ thuê mặt bằng Q7" subtitle="Cty TNHH Hải Đăng" interactive footer={<Button size="sm" variant="secondary">Xem chi tiết</Button>} style={{ width: 320 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: t.font.size.base }}>
            <span style={{ color: t.color.inkMuted }}>Ngày hết hạn</span>
            <strong style={{ color: t.color.ink, fontVariantNumeric: "tabular-nums" }}>30/09/2026</strong>
          </div>
        </Card>
        <div style={{ width: "100%", maxWidth: 480, background: t.color.surface, border: `1px solid ${t.color.n200}`, borderRadius: t.radius.card, padding: t.space[2] }}>
          <Table columns={cols} rows={docRows} />
        </div>
      </Section>

      <Section title="Modal · ReadbackModal (D-02)" note="Nghi thức xác nhận: đọc lại nguyên văn (serif) → quyết định → ghi nhận. Không dark pattern, không auto-proceed (D-11).">
        <Button onClick={() => setModal(true)}>Mở Modal thường</Button>
        <Button variant="secondary" onClick={() => setReadback(true)}>Mở ReadbackModal</Button>
        <Modal open={modal} title="Đồng ý chia sẻ dữ liệu" onClose={() => setModal(false)}
          footer={<>
            <Button variant="ghost" onClick={() => setModal(false)}>Từ chối</Button>
            <Button onClick={() => setModal(false)}>Đồng ý</Button>
          </>}>
          Bạn đồng ý cho đại lý thuế xem danh mục hợp đồng để được nhắc hạn chủ động? Có thể thu hồi bất cứ lúc nào. (NĐ 13/2023)
        </Modal>
        <ReadbackModal
          open={readback} onCancel={() => setReadback(false)} onConfirm={() => setReadback(false)}
          quote="Bên B có nghĩa vụ thanh toán cho Bên A số tiền 130.000.000 đồng mỗi tháng, chậm nhất vào ngày 15."
          source="Điều 4.1 — Thanh toán"
          statement="Bạn xác nhận đã hoàn thành đợt thanh toán này? Servanda sẽ ghi nhận và kích hoạt đợt kế tiếp."
        />
      </Section>

      <Section title="Toast · ActionBar · Banner" note="Toast tường thuật event-chain. ActionBar nền mực đảo cho hành động hàng loạt. Banner 3 mức nhãn-đậm-thay-icon.">
        <Toast kind="done">Đã ghi nhận — 1 nghĩa vụ tiếp theo được kích hoạt</Toast>
        <Toast kind="error">Gửi nhắc thất bại — thử lại sau 5 phút</Toast>
        <Toast kind="info">Đang đọc hợp đồng…</Toast>
        <div style={{ width: "100%" }}>
          <Banner level="warn" title="Chưa rõ hướng nghĩa vụ trong hợp đồng này"
            description="Servanda cần biết tên pháp nhân của bạn để tự phân biệt nghĩa vụ và quyền lợi."
            action={<Button variant="secondary" size="sm">Sửa pháp nhân trong Cài đặt</Button>} />
        </div>
        <div style={{ width: "100%" }}>
          <Banner level="danger" title="3 nghĩa vụ quá hạn" description="Kiểm tra ngay để tránh phạt vi phạm." action={<Button variant="danger" size="sm">Xem ngay</Button>} />
        </div>
      </Section>

      <Section title="Tabs · bulk select" note="Tabs đếm số (Hick's Law — ít lựa chọn, quyết nhanh). Chọn ≥1 hàng bên dưới để xem ActionBar nổi.">
        <div style={{ width: "100%" }}>
          <Tabs active={tab} onChange={setTab} items={[
            { key: "nghia_vu", label: "Nghĩa vụ", count: 5 },
            { key: "quyen_loi", label: "Quyền lợi", count: 2 },
            { key: "cho_kich_hoat", label: "Chờ kích hoạt", count: 3 },
          ]} />
          <div style={{ marginTop: t.space[3], display: "flex", flexDirection: "column", gap: t.space[2] }}>
            {[1,2,3].map((i) => (
              <label key={i} style={{ display: "flex", alignItems: "center", gap: t.space[2], fontSize: t.font.size.base, color: t.color.ink }}>
                <input type="checkbox" checked={selected === i} onChange={() => setSelected(selected === i ? 0 : i)} />
                Thanh toán đợt {i} — 130.000.000 đ
              </label>
            ))}
          </div>
        </div>
        <ActionBar count={selected ? 1 : 0} primaryLabel="Hoàn thành đã chọn (1)" onPrimary={() => setSelected(0)} onCancel={() => setSelected(0)} />
      </Section>

      <Section title="Badge — 13 canonical status labels" note="Solid = trạng thái có sức nặng nghiệp vụ. Outline = thông tin phụ / provenance. Phạt dùng outline đỏ để phân biệt với Quá hạn (solid đỏ) — không bao giờ trộn lẫn.">
        <Badge kind="overdue">Quá hạn 3 ngày</Badge>
        <Badge kind="dueSoon">Hôm nay</Badge>
        <Badge kind="dueSoon">Còn 5 ngày</Badge>
        <Badge kind="future">15/08/2026</Badge>
        <Badge kind="waiting">Chờ kích hoạt</Badge>
        <Badge kind="waiting">Chờ xác nhận</Badge>
        <Badge kind="penalty">Phạt</Badge>
        <Badge kind="done">Đã hoàn thành</Badge>
        <Badge kind="done">Đã thanh lý</Badge>
        <Badge kind="cancelled">Đã hủy</Badge>
        <Badge kind="unclear">Chưa rõ hướng</Badge>
        <Badge kind="series">Đợt 07/14</Badge>
        <Badge kind="manual">Nhập tay</Badge>
        <Badge kind="aiVerified">AI · đã duyệt</Badge>
      </Section>

      <Section title="EmptyState · Skeleton">
        <div style={{ width: 340, background: t.color.surface, borderRadius: t.radius.card, border: `1px solid ${t.color.n200}` }}>
          <EmptyState title="Chưa có tài liệu" description="Tải lên hợp đồng đầu tiên để Servanda bắt đầu nhắc hạn." action={<Button>Tải tài liệu</Button>} />
        </div>
        <div style={{ width: 340, background: t.color.surface, borderRadius: t.radius.card, border: `1px solid ${t.color.n200}` }}>
          <EmptyState notFound />
        </div>
        <div style={{ width: 280, background: t.color.surface, borderRadius: t.radius.card, border: `1px solid ${t.color.n200}`, padding: t.space[5], display: "flex", flexDirection: "column", gap: t.space[3] }}>
          <Skeleton w="60%" h={14} /><Skeleton /><Skeleton w="80%" /><Skeleton w="40%" />
        </div>
      </Section>

      {/* A11Y PRIMITIVES — fold #2 from #206/v0.2 */}
      <Section title="A11y primitives (folded from #206)" note="NavItem = <a>/<button> (locked → disabled). Dropzone = role+keyboard. IconButton = aria-label bắt buộc (NGOẠI LỆ DUY NHẤT của luật không-icon — không dùng cho trạng thái nghiệp vụ). LiveRegion = aria-live. Tab phím qua tất cả để thấy focus ring.">
        <div style={{ width: 240, background: t.color.surface, borderRadius: t.radius.card, border: `1px solid ${t.color.n200}`, padding: t.space[3], display: "flex", flexDirection: "column", gap: 2 }}>
          <NavItem icon="—" label="Tổng quan" href="#" active />
          <NavItem icon="—" label="Nghĩa vụ" href="#" badgeCount={2} />
          <NavItem icon="—" label="Hỏi-đáp" href="#" />
          <NavItem icon="—" label="Kho tài liệu" locked lockedHint="Mở khoá sau khi bật nhắc" />
        </div>
        <div style={{ width: 300 }}>
          <Dropzone label="Kéo thả hợp đồng vào đây" hint="hoặc bấm / Enter để chọn tệp · PDF, ảnh" />
        </div>
        <div style={{ width: 240, background: t.color.surface, borderRadius: t.radius.card, border: `1px solid ${t.color.n200}`, padding: t.space[4], display: "flex", flexDirection: "column", gap: t.space[3] }}>
          <div style={{ display: "flex", gap: t.space[1] }}>
            <IconButton icon="⚙" label="Cài đặt" />
            <IconButton icon="↑" label="Tải lên" />
          </div>
          <LiveRegion style={{ fontSize: t.font.size.sm, color: t.color.ink }}>
            Đang đọc hợp đồng… đã lấy 3/7 trường.
          </LiveRegion>
        </div>
      </Section>
    </div>
  );
}
