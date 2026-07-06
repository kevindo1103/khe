import type { ReactNode } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import { JourneyProvider } from './contexts/JourneyContext';
import Login from './pages/admin/Login';
import AdminShell from './pages/admin/AdminShell';
import Home from './pages/admin/Home';
import Upload from './pages/admin/Upload';
import DocumentList from './pages/admin/DocumentList';
import DocumentDetail from './pages/admin/DocumentDetail';
import DocumentNew from './pages/admin/DocumentNew';
import Obligations from './pages/admin/Obligations';
import ComplianceWizard from './pages/admin/ComplianceWizard';
import Chat from './pages/admin/Chat';
import Settings from './pages/admin/Settings';
import ExtractionMetrics from './pages/admin/ExtractionMetrics';

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
            <JourneyProvider>
              <AdminShell />
            </JourneyProvider>
          </ProtectedRoute>
        }
      >
        <Route index element={<Home />} />
        <Route path="upload" element={<Upload />} />
        <Route path="documents" element={<DocumentList />} />
        <Route path="documents/new" element={<DocumentNew />} />
        <Route path="documents/:id" element={<DocumentDetail />} />
        <Route path="obligations" element={<Obligations />} />
        <Route path="obligations/ra-soat" element={<ComplianceWizard />} />
        <Route path="chat" element={<Chat />} />
        <Route path="settings" element={<Settings />} />
        <Route path="extraction-metrics" element={<ExtractionMetrics />} />
      </Route>
      <Route path="*" element={<Navigate to="/admin/login" replace />} />
    </Routes>
  );
}
