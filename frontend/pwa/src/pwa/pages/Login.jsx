import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api'
import { theme } from '../theme'

const t = theme

export default function Login() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ tenant_id: '', username: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form)
      // Cookie set by backend (HttpOnly) — no token in JS. khe_consent_given is a non-secret UI hint.
      const hasConsent = localStorage.getItem('khe_consent_given') === 'true'
      navigate(hasConsent ? '/chat' : '/consent', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const styles = {
    container: {
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: `${t.space[4]}px`,
      background: t.colors.surfaceAlt,
    },
    card: {
      width: '100%',
      maxWidth: 375,
      background: t.colors.surface,
      borderRadius: t.radius.xl,
      padding: `${t.space[6]}px`,
      boxShadow: t.shadow.md,
    },
    logo: {
      textAlign: 'center',
      marginBottom: `${t.space[6]}px`,
    },
    logoText: {
      fontSize: 32,
      fontWeight: 700,
      color: t.colors.primary,
      letterSpacing: '-0.5px',
    },
    logoSub: {
      fontSize: 13,
      color: t.colors.inkMuted,
      marginTop: 4,
    },
    label: {
      display: 'block',
      fontSize: 13,
      fontWeight: 600,
      color: t.colors.ink,
      marginBottom: `${t.space[1]}px`,
    },
    input: {
      width: '100%',
      padding: `${t.space[3]}px ${t.space[4]}px`,
      border: `1.5px solid ${t.colors.border}`,
      borderRadius: t.radius.md,
      fontSize: 15,
      color: t.colors.ink,
      background: t.colors.surface,
      outline: 'none',
      marginBottom: `${t.space[4]}px`,
      transition: 'border-color 0.15s',
    },
    button: {
      width: '100%',
      padding: `${t.space[3]}px`,
      background: loading ? t.colors.primaryHover : t.colors.primary,
      color: '#fff',
      border: 'none',
      borderRadius: t.radius.md,
      fontSize: 15,
      fontWeight: 600,
      cursor: loading ? 'not-allowed' : 'pointer',
      marginTop: `${t.space[2]}px`,
    },
    error: {
      background: t.colors.dangerSoft,
      color: t.colors.danger,
      borderRadius: t.radius.md,
      padding: `${t.space[3]}px`,
      fontSize: 13,
      marginBottom: `${t.space[4]}px`,
      textAlign: 'center',
    },
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logo}>
          <div style={styles.logoText}>Khế</div>
          <div style={styles.logoSub}>Hỏi-đáp hợp đồng · Nhắc đúng hạn</div>
        </div>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <label style={styles.label} htmlFor="tenant_id">Mã doanh nghiệp</label>
          <input
            id="tenant_id"
            name="tenant_id"
            type="text"
            style={styles.input}
            value={form.tenant_id}
            onChange={handleChange}
            placeholder="vd: sme-abc-restaurant"
            autoComplete="organization"
            required
          />

          <label style={styles.label} htmlFor="username">Tên đăng nhập</label>
          <input
            id="username"
            name="username"
            type="text"
            style={styles.input}
            value={form.username}
            onChange={handleChange}
            placeholder="username"
            autoComplete="username"
            required
          />

          <label style={styles.label} htmlFor="password">Mật khẩu</label>
          <input
            id="password"
            name="password"
            type="password"
            style={styles.input}
            value={form.password}
            onChange={handleChange}
            placeholder="••••••••"
            autoComplete="current-password"
            required
          />

          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
        </form>
      </div>
    </div>
  )
}
