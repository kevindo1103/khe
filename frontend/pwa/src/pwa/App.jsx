import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { getMe } from './api'
import { theme } from './theme'
import Login from './pages/Login'
import ConsentFlow from './pages/ConsentFlow'
import Chat from './pages/Chat'

const t = theme

function hasConsent() {
  return localStorage.getItem('khe_consent_given') === 'true'
}

// Calls GET /auth/me on mount. 200 = cookie valid; 401 = not authenticated.
function AuthGate({ children }) {
  const [status, setStatus] = useState('loading') // 'loading' | 'auth' | 'unauth'

  useEffect(() => {
    getMe()
      .then(() => setStatus('auth'))
      .catch(() => setStatus('unauth'))
  }, [])

  if (status === 'loading') {
    return (
      <div style={{
        minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: t.colors.surfaceAlt, fontFamily: t.font,
      }}>
        <div style={{ fontSize: 14, color: t.colors.inkMuted }}>Đang tải…</div>
      </div>
    )
  }

  if (status === 'unauth') return <Navigate to="/login" replace />

  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/consent"
          element={
            <AuthGate>
              <ConsentFlow />
            </AuthGate>
          }
        />
        {/* /chat intentionally allows no-consent: Chat renders read-only mode when consent deferred ("Để sau" flow) */}
        <Route
          path="/chat"
          element={
            <AuthGate>
              <Chat />
            </AuthGate>
          }
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
