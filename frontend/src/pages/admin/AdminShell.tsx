import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Button } from '../../components';

const navItems = [
  { to: '/admin', label: 'Tổng quan' },
  { to: '/admin/upload', label: 'Tải lên' },
  { to: '/admin/documents', label: 'Tài liệu' },
  { to: '/admin/obligations', label: 'Nghĩa vụ' },
];

export default function AdminShell() {
  const { user, logout } = useAuth();
  const location = useLocation();

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
