import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

/**
 * App navigation v0.2 (#204, responsive) — desktop left sidebar (≥760px) +
 * mobile bottom-tab bar & top header (<760px). Supersedes the journey-primitive
 * LockedNav for the production shell (same lock semantics).
 *
 * a11y (#206): every nav target is a real <Link> (navigation) or <button>
 * (action/logout); locked items are <button disabled> (not focusable); glyph
 * icons are decorative (aria-hidden) with a text label always present.
 * Labels stay entity-shaped (Phase 1). // PHASE-2-IA-DEBT: job-shaped post-pilot.
 */
export interface NavItem {
  key: string;
  label: string;
  icon: string;
  to: string;
  primary?: boolean;
  action?: boolean;
}
export interface NavSection {
  group: string;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  {
    group: 'Theo dõi',
    items: [
      { key: 'home', label: 'Tổng quan', icon: '◎', to: '/admin', primary: true },
      { key: 'obligations', label: 'Nghĩa vụ', icon: '⏰', to: '/admin/obligations', primary: true },
    ],
  },
  {
    group: 'Tài liệu',
    items: [
      { key: 'docs', label: 'Kho tài liệu', icon: '▤', to: '/admin/documents', primary: true },
      { key: 'upload', label: 'Tải lên', icon: '↑', to: '/admin/upload', primary: true, action: true },
    ],
  },
  {
    group: 'Trợ lý',
    items: [{ key: 'chat', label: 'Hỏi-đáp', icon: '✦', to: '/admin/chat', primary: true }],
  },
];
const ALL_ITEMS = NAV_SECTIONS.flatMap((s) => s.items);
export const SETTINGS_ITEM: NavItem = { key: 'settings', label: 'Cài đặt', icon: '⚙', to: '/admin/settings' };

// first session keeps home + upload OPEN; read destinations lock until activated
const FIRST_SESSION_OPEN = ['home', 'upload'];
const isLocked = (key: string, firstSession: boolean) =>
  firstSession && !FIRST_SESSION_OPEN.includes(key);

function useActiveKey(): string {
  const { pathname } = useLocation();
  if (pathname === '/admin') return 'home';
  if (pathname.startsWith('/admin/obligations')) return 'obligations';
  if (pathname.startsWith('/admin/documents')) return 'docs';
  if (pathname.startsWith('/admin/upload')) return 'upload';
  if (pathname.startsWith('/admin/chat')) return 'chat';
  if (pathname.startsWith('/admin/settings')) return 'settings';
  return 'home';
}

const lockTitle = 'Mở khoá sau khi bạn tải & xác nhận hợp đồng đầu tiên';

// ── Desktop sidebar ──

function SidebarItem({ it, activeKey, firstSession }: { it: NavItem; activeKey: string; firstSession: boolean }) {
  const locked = isLocked(it.key, firstSession);
  const on = activeKey === it.key;
  const base =
    'relative flex items-center gap-2 px-2 py-2 rounded-md mb-0.5 text-sm transition-colors focus-visible:shadow-ring focus-visible:outline-none';
  if (locked) {
    return (
      <button
        type="button"
        disabled
        title={lockTitle}
        aria-label={`${it.label} (khoá — mở sau khi bật nhắc)`}
        className={`${base} w-full text-left font-medium text-ink-subtle opacity-50 cursor-not-allowed`}
      >
        <span aria-hidden="true" className="w-5 text-center text-[15px]">{it.icon}</span>
        <span className="flex-1">{it.label}</span>
        <span aria-hidden="true" className="text-[10px]">🔒</span>
      </button>
    );
  }
  return (
    <Link
      to={it.to}
      aria-current={on ? 'page' : undefined}
      className={`${base} ${on ? 'bg-primary-soft text-primary font-semibold' : 'text-ink-body font-medium hover:bg-surface-alt'}`}
    >
      {on && <span aria-hidden="true" className="absolute -left-2 top-1.5 bottom-1.5 w-0.5 rounded-pill bg-primary" />}
      <span aria-hidden="true" className="w-5 text-center text-[15px]">{it.icon}</span>
      <span className="flex-1">{it.label}</span>
    </Link>
  );
}

export function AppSidebar({ firstSession, username, onLogout }: { firstSession: boolean; username?: string; onLogout: () => void }) {
  const activeKey = useActiveKey();
  return (
    <aside className="hidden nav:flex w-60 shrink-0 flex-col bg-surface border-r border-border min-h-screen sticky top-0 self-start">
      <div className="px-5 py-4 flex items-center gap-2">
        <span className="w-7 h-7 rounded-md bg-primary text-white flex items-center justify-center font-bold">K</span>
        <span className="text-lg font-bold text-ink">Khế</span>
      </div>
      <nav aria-label="Điều hướng chính" className="flex-1 overflow-y-auto px-3 py-2">
        {NAV_SECTIONS.map((sec) => (
          <div key={sec.group} role="group" aria-label={sec.group} className="mb-4">
            <div className="text-2xs font-semibold text-ink-subtle uppercase tracking-wide px-2 py-1">{sec.group}</div>
            {sec.items.map((it) => (
              <SidebarItem key={it.key} it={it} activeKey={activeKey} firstSession={firstSession} />
            ))}
          </div>
        ))}
      </nav>
      <div className="border-t border-border p-3">
        <Link
          to={SETTINGS_ITEM.to}
          aria-current={activeKey === 'settings' ? 'page' : undefined}
          className={`flex items-center gap-2 px-2 py-2 rounded-md text-sm focus-visible:shadow-ring focus-visible:outline-none ${activeKey === 'settings' ? 'bg-primary-soft text-primary' : 'text-ink-body hover:bg-surface-alt'}`}
        >
          <span aria-hidden="true" className="w-5 text-center">{SETTINGS_ITEM.icon}</span>
          {SETTINGS_ITEM.label}
        </Link>
        <div className="flex items-center gap-2 mt-1 px-2 py-2">
          <span aria-hidden="true" className="w-7 h-7 rounded-full bg-surface-sunken border border-border flex items-center justify-center text-sm text-ink-muted">
            {(username || 'D').charAt(0).toUpperCase()}
          </span>
          <span className="min-w-0 flex-1 text-sm text-ink font-medium truncate">{username || 'Tài khoản'}</span>
          <button
            type="button"
            onClick={onLogout}
            className="text-2xs font-medium text-danger hover:underline focus-visible:shadow-ring focus-visible:outline-none rounded px-1"
          >
            Đăng xuất
          </button>
        </div>
      </div>
    </aside>
  );
}

// ── Mobile top header ──

export function AppMobileHeader({ username, onLogout }: { username?: string; onLogout: () => void }) {
  const [menu, setMenu] = useState(false);
  return (
    <header className="nav:hidden relative flex items-center justify-between px-4 py-3 border-b border-border bg-surface sticky top-0 z-sticky">
      <span className="font-bold text-primary">Khế</span>
      <div className="flex items-center gap-1">
        <Link
          to={SETTINGS_ITEM.to}
          aria-label="Cài đặt"
          className="w-9 h-9 rounded-md flex items-center justify-center text-ink-body hover:bg-surface-alt focus-visible:shadow-ring focus-visible:outline-none"
        >
          <span aria-hidden="true">{SETTINGS_ITEM.icon}</span>
        </Link>
        <button
          type="button"
          aria-label="Tài khoản"
          aria-haspopup="menu"
          aria-expanded={menu}
          onClick={() => setMenu((m) => !m)}
          className="w-9 h-9 rounded-full flex items-center justify-center bg-surface-sunken border border-border text-sm text-ink-muted focus-visible:shadow-ring focus-visible:outline-none"
        >
          <span aria-hidden="true">{(username || 'D').charAt(0).toUpperCase()}</span>
        </button>
        {menu && (
          <div role="menu" className="absolute top-[52px] right-4 min-w-[180px] bg-surface border border-border rounded-lg shadow-e2 p-2 z-overlay">
            <div className="px-2 py-1 text-sm text-ink font-medium border-b border-border mb-1">{username || 'Tài khoản'}</div>
            <button
              type="button"
              role="menuitem"
              onClick={onLogout}
              className="block w-full text-left px-2 py-2 rounded-md text-sm text-danger hover:bg-surface-alt focus-visible:shadow-ring focus-visible:outline-none"
            >
              Đăng xuất
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

// ── Mobile bottom tab bar ──

function BottomTab({ it, activeKey, firstSession }: { it: NavItem; activeKey: string; firstSession: boolean }) {
  const locked = isLocked(it.key, firstSession);
  const on = activeKey === it.key;

  if (it.action) {
    // center elevated upload action — never locked first session (it IS onboarding)
    return (
      <div className="flex-1 flex justify-center items-center">
        {locked ? (
          <button type="button" disabled aria-label={`${it.label} (khoá)`} className="w-12 h-12 rounded-full -mt-4 bg-neutral-300 text-white text-xl shadow-e2 cursor-not-allowed">
            <span aria-hidden="true">＋</span>
          </button>
        ) : (
          <Link to={it.to} aria-label={it.label} className="w-12 h-12 rounded-full -mt-4 bg-primary text-white text-xl shadow-e2 flex items-center justify-center focus-visible:shadow-ring focus-visible:outline-none">
            <span aria-hidden="true">＋</span>
          </Link>
        )}
      </div>
    );
  }

  const inner = (
    <>
      <span aria-hidden="true" className="text-lg">{it.icon}</span>
      <span className={`text-[10px] ${on ? 'font-semibold' : 'font-medium'}`}>{it.label}</span>
    </>
  );
  if (locked) {
    return (
      <button type="button" disabled aria-label={`${it.label} (khoá)`} title={lockTitle} className="flex-1 flex flex-col items-center gap-0.5 py-2 text-ink-subtle opacity-50 cursor-not-allowed">
        {inner}
      </button>
    );
  }
  return (
    <Link
      to={it.to}
      aria-current={on ? 'page' : undefined}
      className={`flex-1 flex flex-col items-center gap-0.5 py-2 focus-visible:shadow-ring focus-visible:outline-none ${on ? 'text-primary' : 'text-ink-muted'}`}
    >
      {inner}
    </Link>
  );
}

export function AppBottomTabs({ firstSession }: { firstSession: boolean }) {
  const activeKey = useActiveKey();
  const tabs = ALL_ITEMS.filter((i) => i.primary);
  return (
    <nav aria-label="Điều hướng chính" className="nav:hidden flex items-stretch border-t border-border bg-surface pb-1 sticky bottom-0 z-sticky">
      {tabs.map((it) => (
        <BottomTab key={it.key} it={it} activeKey={activeKey} firstSession={firstSession} />
      ))}
    </nav>
  );
}
