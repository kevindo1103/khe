import type { ReactNode } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import Login from './pages/admin/Login';
import AdminShell from './pages/admin/AdminShell';
import Upload from './pages/admin/Upload';
import DocumentList from './pages/admin/DocumentList';
import DocumentDetail from './pages/admin/DocumentDetail';
import Obligations from './pages/admin/Obligations';

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
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
      </Route>
      <Route path="*" element={<Navigate to="/admin/login" replace />} />
    </Routes>
  );
}
