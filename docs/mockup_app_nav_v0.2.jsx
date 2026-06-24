/**
 * Khế — App Navigation v0.2 (responsive)  (mockup_app_nav_v0.2.jsx)
 * KHE_Designer · builds on Design System v0.2 · Kevin-ratified 2026-06-23 (layout-only)
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.2 only.
 *
 * DECISION: switch from horizontal top nav → RESPONSIVE:
 *   • Desktop  = vertical LEFT SIDEBAR, grouped by category → scales as features grow.
 *   • Mobile   = BOTTOM TAB BAR (thumb-reach) + top HEADER (account/settings reach).
 * Rationale: grouping + future expansion (the ask) without hurting mobile UX.
 *
 * SCOPE: this is a LAYOUT change only. Labels stay ENTITY-shaped (Tổng quan / Tài
 *   liệu / Nghĩa vụ / Hỏi-đáp) per Phase-1 ratified. Job-shaped IA ("Hôm nay cần lo /
 *   Sắp tới / Đã xong") is still deferred — // PHASE-2-IA-DEBT below.
 *
 * Behaviour kept from LockedNav: nav-lock ONLY on is_first_session (cleared at
 *   CONFIRMED — DEC-040 #238). Return visits = full nav. Supersedes `LockedNav` in journey
 *   primitives for the layout (the lock semantics are identical).
 *   → DEPRECATION: `LockedNav` (journey primitives, PR #200) is superseded by
 *     AppSidebar/AppBottomTabs. Migration tracked as a follow-up issue; the two
 *     coexist transitionally until journey mockups adopt these. Do not extend
 *     `LockedNav` — add to this file instead.
 *
 * REVIEW #204 FIXES (2026-06-23):
 *   #1 a11y  — all nav items are <button> (keyboard-reachable, focus ring, aria).
 *   #2 mobile — AppMobileHeader adds Settings + account/logout reach (was a hole).
 *   #3 lock  — first-session UNLOCKS `upload` (it IS the onboarding action) + home.
 *   #4 badge — mobile count badge uses the SAME warning-soft style as Badge due_soon.
 *   #5 dep   — LockedNav marked deprecated above + follow-up issue.
 */
import React, { useState } from "react";
import { tokens as t, Button, Badge } from "./mockup_design_system_v0.2.jsx";

/* ---- nav model: grouped sections (entity-shaped, Phase 1) ----
 * primary[] = the destinations that also appear in the mobile bottom bar. */
export const NAV_SECTIONS = [
  { group: "Theo dõi", items: [
    { key: "home", label: "Tổng quan", icon: "◎", primary: true },
    { key: "obligations", label: "Nghĩa vụ", icon: "⏰", primary: true, badge: 2 },
  ]},
  { group: "Tài liệu", items: [
    { key: "docs", label: "Kho tài liệu", icon: "▤", primary: true },
    { key: "upload", label: "Tải lên", icon: "↑", primary: true, action: true },
  ]},
  { group: "Trợ lý", items: [
    { key: "chat", label: "Hỏi-đáp", icon: "✦", primary: true },
  ]},
  // PHASE-2-IA-DEBT: entity-shaped sections; job-shaped candidate post-pilot.
  // Future: a "Đối tác / Firm" section drops in here without touching the rest.
];
const ALL = NAV_SECTIONS.flatMap((s) => s.items);
const SETTINGS = { key: "settings", label: "Cài đặt", icon: "⚙" };

/* #3 first-session lock: home + upload stay OPEN (upload IS the onboarding action;
 *   locking the prominent center "+" contradicts the onboarding goal). Only the
 *   read destinations (obligations / docs / chat) lock until reminders are on. */
const FIRST_SESSION_OPEN = ["home", "upload"];
const isLocked = (key, isFirstSession) => isFirstSession && !FIRST_SESSION_OPEN.includes(key);

/* tiny focus-visible ring hook (mirrors design-system internal; not exported there).
 * #1 a11y: every interactive nav element shows a visible focus ring on keyboard tab. */
function useFocusRing() {
  const [focus, setFocus] = useState(false);
  return {
    focus,
    bind: { onFocus: () => setFocus(true), onBlur: () => setFocus(false) },
  };
}
const ringStyle = { boxShadow: `0 0 0 3px ${t.color.ring}`, outline: "none" };
// reset so <button> looks identical to the old <div> rows
const btnReset = { border: "none", background: "transparent", font: "inherit", textAlign: "left", width: "100%" };

/* =========================================================================
 * Desktop — vertical sidebar
 * ======================================================================= */
function SidebarItem({ it, active, isFirstSession }) {
  const locked = isLocked(it.key, isFirstSession);
  const on = active === it.key;
  const { focus, bind } = useFocusRing();
  return (
    <button
      {...bind}
      type="button"
      disabled={locked}
      aria-current={on ? "page" : undefined}
      aria-label={`${it.label}${locked ? " (khoá — mở sau khi bật nhắc)" : ""}`}
      title={locked ? "Mở khoá sau khi bật nhắc" : undefined}
      style={{
        ...btnReset,
        position: "relative", display: "flex", alignItems: "center", gap: t.space[2],
        padding: `${t.space[2]}px ${t.space[2]}px`, borderRadius: t.radius.md, marginBottom: 2,
        fontSize: t.font.size.base, fontWeight: on ? t.font.weight.semibold : t.font.weight.medium,
        background: on ? t.color.primarySoft : "transparent",
        color: locked ? t.color.inkSubtle : on ? t.color.primary : t.color.inkBody,
        opacity: locked ? 0.5 : 1, cursor: locked ? "not-allowed" : "pointer",
        ...(focus ? ringStyle : null),
      }}
    >
      {/* active left accent bar */}
      {on && <span aria-hidden="true" style={{ position: "absolute", left: -t.space[3] + 1, top: 6, bottom: 6, width: 3, borderRadius: t.radius.pill, background: t.color.primary }} />}
      <span aria-hidden="true" style={{ width: 20, textAlign: "center", fontSize: 15 }}>{it.icon}</span>
      <span style={{ flex: 1 }}>{it.label}</span>
      {locked && <span aria-hidden="true" style={{ fontSize: 10 }}>🔒</span>}
      {!locked && it.badge && <Badge kind="due_soon">{it.badge}</Badge>}
    </button>
  );
}

export function AppSidebar({ active = "home", isFirstSession = false, width = 248 }) {
  const settingsFocus = useFocusRing();
  const acctFocus = useFocusRing();
  return (
    <aside style={{
      width, minHeight: 560, background: t.color.surface, borderRight: `1px solid ${t.color.border}`,
      display: "flex", flexDirection: "column", fontFamily: t.font.family, flexShrink: 0,
    }}>
      {/* brand */}
      <div style={{ padding: `${t.space[4]}px ${t.space[5]}px`, display: "flex", alignItems: "center", gap: t.space[2] }}>
        <span style={{ width: 28, height: 28, borderRadius: t.radius.md, background: t.color.primary, color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: t.font.weight.bold }}>K</span>
        <span style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.snug }}>Khế</span>
      </div>

      <nav aria-label="Điều hướng chính" style={{ flex: 1, overflowY: "auto", padding: `${t.space[2]}px ${t.space[3]}px` }}>
        {NAV_SECTIONS.map((sec) => (
          <div key={sec.group} role="group" aria-label={sec.group} style={{ marginBottom: t.space[4] }}>
            <div style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.inkSubtle, textTransform: "uppercase", letterSpacing: t.font.tracking.wide, padding: `${t.space[1]}px ${t.space[2]}px` }}>
              {sec.group}
            </div>
            {sec.items.map((it) => (
              <SidebarItem key={it.key} it={it} active={active} isFirstSession={isFirstSession} />
            ))}
          </div>
        ))}
      </nav>

      {/* footer: settings + account (both keyboard-accessible buttons) */}
      <div style={{ borderTop: `1px solid ${t.color.border}`, padding: t.space[3] }}>
        <button
          {...settingsFocus.bind}
          type="button"
          aria-current={active === "settings" ? "page" : undefined}
          style={{
            ...btnReset, display: "flex", alignItems: "center", gap: t.space[2], padding: t.space[2],
            borderRadius: t.radius.md, color: active === "settings" ? t.color.primary : t.color.inkBody,
            background: active === "settings" ? t.color.primarySoft : "transparent",
            fontSize: t.font.size.base, cursor: "pointer", ...(settingsFocus.focus ? ringStyle : null),
          }}
        >
          <span aria-hidden="true" style={{ width: 20, textAlign: "center" }}>{SETTINGS.icon}</span>{SETTINGS.label}
        </button>
        <button
          {...acctFocus.bind}
          type="button"
          aria-label="Tài khoản Anh Dũng — Quán Cơm Tấm ABC"
          style={{
            ...btnReset, display: "flex", alignItems: "center", gap: t.space[2], padding: t.space[2],
            marginTop: 2, borderRadius: t.radius.md, cursor: "pointer", ...(acctFocus.focus ? ringStyle : null),
          }}
        >
          <span aria-hidden="true" style={{ width: 28, height: 28, borderRadius: "50%", background: t.color.surfaceSunken, border: `1px solid ${t.color.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: t.font.size.sm, color: t.color.inkMuted }}>D</span>
          <span style={{ minWidth: 0 }}>
            <span style={{ display: "block", fontSize: t.font.size.sm, color: t.color.ink, fontWeight: t.font.weight.medium }}>Anh Dũng</span>
            <span style={{ display: "block", fontSize: t.font.size.xs, color: t.color.inkSubtle, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Quán Cơm Tấm ABC</span>
          </span>
        </button>
      </div>
    </aside>
  );
}

/* =========================================================================
 * Mobile — top header (brand + settings + account/logout) so Settings and
 * logout are reachable on the primary persona's device (#2 fix). The bottom
 * bar stays 5 primary destinations; account-level actions live in the header.
 * ======================================================================= */
export function AppMobileHeader({ onNavigate }) {
  const [menu, setMenu] = useState(false);
  const settingsFocus = useFocusRing();
  const acctFocus = useFocusRing();
  return (
    <header style={{ position: "relative", display: "flex", alignItems: "center", justifyContent: "space-between", padding: `${t.space[3]}px ${t.space[4]}px`, borderBottom: `1px solid ${t.color.border}`, background: t.color.surface, fontFamily: t.font.family }}>
      <span style={{ fontWeight: t.font.weight.bold, color: t.color.primary }}>Khế</span>
      <div style={{ display: "flex", alignItems: "center", gap: t.space[1] }}>
        <button
          {...settingsFocus.bind}
          type="button"
          aria-label="Cài đặt"
          onClick={() => onNavigate && onNavigate("settings")}
          style={{ ...btnReset, width: 36, height: 36, borderRadius: t.radius.md, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: t.color.inkBody, fontSize: 16, ...(settingsFocus.focus ? ringStyle : null) }}
        >
          <span aria-hidden="true">{SETTINGS.icon}</span>
        </button>
        <button
          {...acctFocus.bind}
          type="button"
          aria-label="Tài khoản"
          aria-haspopup="menu"
          aria-expanded={menu}
          onClick={() => setMenu((m) => !m)}
          style={{ ...btnReset, width: 36, height: 36, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", background: t.color.surfaceSunken, border: `1px solid ${t.color.border}`, color: t.color.inkMuted, fontSize: t.font.size.sm, ...(acctFocus.focus ? ringStyle : null) }}
        >
          <span aria-hidden="true">D</span>
        </button>
        {menu && (
          <div role="menu" style={{ position: "absolute", top: 52, right: t.space[4], minWidth: 180, background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, boxShadow: t.elevation.e2, padding: t.space[2], zIndex: 10 }}>
            <div style={{ padding: `${t.space[1]}px ${t.space[2]}px`, fontSize: t.font.size.sm, color: t.color.ink, fontWeight: t.font.weight.medium }}>Anh Dũng</div>
            <div style={{ padding: `0 ${t.space[2]}px ${t.space[2]}px`, fontSize: t.font.size.xs, color: t.color.inkSubtle, borderBottom: `1px solid ${t.color.border}`, marginBottom: t.space[1] }}>Quán Cơm Tấm ABC</div>
            <button type="button" role="menuitem" onClick={() => { setMenu(false); onNavigate && onNavigate("settings"); }} style={{ ...btnReset, display: "block", padding: `${t.space[2]}px ${t.space[2]}px`, borderRadius: t.radius.md, fontSize: t.font.size.base, color: t.color.inkBody, cursor: "pointer" }}>Cài đặt</button>
            <button type="button" role="menuitem" style={{ ...btnReset, display: "block", padding: `${t.space[2]}px ${t.space[2]}px`, borderRadius: t.radius.md, fontSize: t.font.size.base, color: t.color.danger, cursor: "pointer" }}>Đăng xuất</button>
          </div>
        )}
      </div>
    </header>
  );
}

/* =========================================================================
 * Mobile — bottom tab bar (primary destinations; center = upload action)
 * ======================================================================= */
function BottomTab({ it, active, isFirstSession }) {
  const locked = isLocked(it.key, isFirstSession);
  const on = active === it.key;
  const { focus, bind } = useFocusRing();
  if (it.action) {
    // center elevated upload action — NOT locked first-session (it's the onboarding action, #3)
    return (
      <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center" }}>
        <button
          {...bind}
          type="button"
          disabled={locked}
          aria-label={`${it.label}${locked ? " (khoá)" : ""}`}
          title={locked ? "Mở khoá sau khi bật nhắc" : it.label}
          style={{
            width: 48, height: 48, borderRadius: "50%", marginTop: -16, border: "none",
            background: locked ? t.color.neutral[300] : t.color.primary, color: "#fff", fontSize: 22,
            boxShadow: t.elevation.e2, cursor: locked ? "not-allowed" : "pointer",
            ...(focus ? ringStyle : null),
          }}
        >
          <span aria-hidden="true">＋</span>
        </button>
      </div>
    );
  }
  return (
    <button
      {...bind}
      type="button"
      disabled={locked}
      aria-current={on ? "page" : undefined}
      aria-label={`${it.label}${locked ? " (khoá — mở sau khi bật nhắc)" : ""}`}
      title={locked ? "Mở khoá sau khi bật nhắc" : undefined}
      style={{
        flex: 1, background: "transparent", border: "none", cursor: locked ? "not-allowed" : "pointer",
        display: "flex", flexDirection: "column", alignItems: "center", gap: 2, padding: `${t.space[2]}px 0`,
        color: locked ? t.color.inkSubtle : on ? t.color.primary : t.color.inkMuted, opacity: locked ? 0.5 : 1,
        ...(focus ? ringStyle : null),
      }}
    >
      <span aria-hidden="true" style={{ fontSize: 18, position: "relative" }}>
        {it.icon}
        {/* #4 unify: same warning-soft style as <Badge kind="due_soon"> in the sidebar */}
        {!locked && it.badge && <span style={{ position: "absolute", top: -4, right: -8, background: t.color.warning_soft, color: t.color.warning, border: `1px solid ${t.color.warningBorder}`, fontSize: 9, borderRadius: t.radius.pill, padding: "0 4px", fontWeight: t.font.weight.bold }}>{it.badge}</span>}
      </span>
      <span style={{ fontSize: 10, fontWeight: on ? t.font.weight.semibold : t.font.weight.medium }}>{it.label}</span>
    </button>
  );
}

export function AppBottomTabs({ active = "home", isFirstSession = false }) {
  const tabs = ALL.filter((i) => i.primary); // home, obligations, upload(action), docs, chat
  return (
    <nav aria-label="Điều hướng chính" style={{
      display: "flex", alignItems: "stretch", borderTop: `1px solid ${t.color.border}`,
      background: t.color.surface, fontFamily: t.font.family, paddingBottom: 4,
    }}>
      {tabs.map((it) => (
        <BottomTab key={it.key} it={it} active={active} isFirstSession={isFirstSession} />
      ))}
    </nav>
  );
}

/* =========================================================================
 * SHOWCASE — desktop sidebar vs mobile bottom-tab, return vs first-session
 * ======================================================================= */
function ContentStub({ title }) {
  return (
    <div style={{ flex: 1, padding: t.space[6], fontFamily: t.font.family }}>
      <div style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight }}>{title}</div>
      <div style={{ marginTop: t.space[4], height: 120, background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg }} />
    </div>
  );
}

export default function AppNavShowcase() {
  const [active, setActive] = useState("obligations");
  const [first, setFirst] = useState(false);
  const titleFor = (key) => key === "settings" ? "Cài đặt" : (ALL.find((i) => i.key === key) || { label: "Tổng quan" }).label;
  return (
    <div style={{ background: t.color.surfaceAlt, minHeight: "100vh", padding: t.space[8], fontFamily: t.font.family }}>
      <header style={{ marginBottom: t.space[7], maxWidth: 760 }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Navigation v0.2 · responsive</span>
        <div style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, marginTop: t.space[1] }}>Sidebar (desktop) + Bottom-tab (mobile)</div>
        <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, marginTop: t.space[2], lineHeight: t.font.lineHeight.relaxed }}>
          Group theo category, scale khi thêm feature; mobile dùng bottom-tab thumb-reach + header cho Cài đặt/đăng xuất. Layout-only — nhãn vẫn entity-shaped (Phase 1), job-shaped để post-pilot. Tab phím để thấy focus ring.
        </p>
        <div style={{ display: "flex", gap: t.space[2], marginTop: t.space[4] }}>
          <Button size="sm" variant={first ? "secondary" : "primary"} onClick={() => setFirst(false)}>Return visit</Button>
          <Button size="sm" variant={first ? "primary" : "secondary"} onClick={() => setFirst(true)}>First session (locked)</Button>
        </div>
      </header>

      {/* desktop */}
      <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.inkMuted, marginBottom: t.space[2] }}>Desktop</div>
      <div style={{ display: "flex", background: t.color.surfaceAlt, border: `1px solid ${t.color.border}`, borderRadius: t.radius.xl, overflow: "hidden", boxShadow: t.elevation.e1, maxWidth: 980 }}>
        <AppSidebar active={active} isFirstSession={first} />
        <ContentStub title={titleFor(active)} />
      </div>

      {/* mobile */}
      <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.inkMuted, margin: `${t.space[7]}px 0 ${t.space[2]}px` }}>Mobile</div>
      <div style={{ width: 390, height: 600, border: `1px solid ${t.color.border}`, borderRadius: t.radius.xl, overflow: "hidden", background: t.color.surface, boxShadow: t.elevation.e2, display: "flex", flexDirection: "column" }}>
        <AppMobileHeader onNavigate={setActive} />
        <div style={{ flex: 1, overflow: "auto" }}><ContentStub title={titleFor(active)} /></div>
        <AppBottomTabs active={active} isFirstSession={first} />
      </div>

      {/* quick switcher to preview active state */}
      <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginTop: t.space[5] }}>
        {[...ALL.filter((i) => !i.action), SETTINGS].map((i) => (
          <button key={i.key} onClick={() => setActive(i.key)} style={{ padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, cursor: "pointer", fontFamily: t.font.family, fontSize: t.font.size.sm, border: `1px solid ${active === i.key ? t.color.primary : t.color.border}`, background: active === i.key ? t.color.primarySoft : t.color.surface, color: active === i.key ? t.color.primary : t.color.inkMuted }}>{i.icon} {i.label}</button>
        ))}
      </div>
    </div>
  );
}
