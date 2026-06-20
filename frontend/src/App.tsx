import type { ReactNode } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import Login from './pages/admin/Login';
import AdminShell from './pages/admin/AdminShell';
import Upload from './pages/admin/Upload';
import DocumentList from './pages/admin/DocumentList';
import DocumentDetail from './pages/admin/DocumentDetail';
import Obligations from './pages/admin/Obligations';
import Chat from './pages/admin/Chat';

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-ink-muted text-sm">
        Đang kiểm tra phiên…
      </div>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/admin/login" element={<Login />} />
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <AdminShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Upload />} />
        <Route path="upload" element={<Upload />} />
        <Route path="documents" element={<DocumentList />} />
        <Route path="documents/:id" element={<DocumentDetail />} />
        <Route path="obligations" element={<Obligations />} />
        <Route path="chat" element={<Chat />} />
      </Route>
      <Route path="*" element={<Navigate to="/admin/login" replace />} />
    </Routes>
  );
}
