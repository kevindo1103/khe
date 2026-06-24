import { Outlet } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useJourney } from '../../contexts/JourneyContext';
import { AppSidebar, AppMobileHeader, AppBottomTabs } from '../../components/AppNav';

/**
 * Responsive admin shell (#204/#227): left sidebar ≥760px, bottom-tabs + top
 * header <760px. First-session nav-lock reads server is_first_session (#213).
 */
export default function AdminShell() {
  const { user, logout } = useAuth();
  const { isFirstSession } = useJourney();
  const username = user?.username;

  return (
    <div className="min-h-screen bg-surface-alt nav:flex">
      <AppSidebar firstSession={isFirstSession} username={username} onLogout={logout} />

      <div className="flex-1 min-w-0 flex flex-col">
        <AppMobileHeader username={username} onLogout={logout} />
        <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6">
          <Outlet />
        </main>
        <AppBottomTabs firstSession={isFirstSession} />
      </div>
    </div>
  );
}
