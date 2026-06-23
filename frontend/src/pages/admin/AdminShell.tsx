import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useJourneyStage } from '../../hooks/useJourneyStage';
import { Button } from '../../components';

// First session keeps home + upload OPEN (upload IS the onboarding action);
// the rest lock until the tenant activates (#198 clarification 2, #208 §3).
const navItems = [
  { to: '/admin', label: 'Tổng quan', firstSessionOpen: true },
  { to: '/admin/upload', label: 'Tải lên', firstSessionOpen: true },
  { to: '/admin/documents', label: 'Tài liệu', firstSessionOpen: false },
  { to: '/admin/obligations', label: 'Nghĩa vụ', firstSessionOpen: false },
  { to: '/admin/chat', label: 'Hỏi-đáp', firstSessionOpen: false },
  { to: '/admin/settings', label: 'Cài đặt', firstSessionOpen: false },
];

export default function AdminShell() {
  const { user, logout } = useAuth();
  const location = useLocation();
  // server-owned is_first_session (#213); cleared atomically at ACTIVATED+
  const { isFirstSession: firstSession } = useJourneyStage();

  return (
    <div className="min-h-screen bg-surface-alt">
      {/* Top nav */}
      <header className="bg-surface border-b border-border sticky top-0 z-sticky">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/admin" className="text-lg font-bold text-primary">
              Khế
            </Link>
            <nav className="hidden sm:flex items-center gap-1">
              {navItems.map((item) => {
                const active = location.pathname === item.to;
                const locked = firstSession && !item.firstSessionOpen;
                if (locked) {
                  return (
                    <span
                      key={item.to}
                      title="Mở khoá sau khi bạn tải & xác nhận hợp đồng đầu tiên"
                      aria-disabled="true"
                      className="px-3 py-1.5 rounded-md text-sm font-medium text-ink-subtle opacity-50 cursor-not-allowed inline-flex items-center gap-1"
                    >
                      <span aria-hidden="true">🔒</span>
                      {item.label}
                    </span>
                  );
                }
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`
                      px-3 py-1.5 rounded-md text-sm font-medium transition-colors
                      ${active ? 'bg-primary-soft text-primary' : 'text-ink-muted hover:text-ink hover:bg-surface-alt'}
                    `}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            {user && (
              <span className="text-xs text-ink-muted hidden sm:inline">
                {user.username}
              </span>
            )}
            <Button size="sm" variant="ghost" onClick={logout}>
              Đăng xuất
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
