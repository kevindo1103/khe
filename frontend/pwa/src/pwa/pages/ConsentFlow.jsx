import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { postConsent, getMe } from '../api'
import { theme } from '../theme'

const t = theme

const TELEGRAM_BOT_USERNAME = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || 'KheBot'

export default function ConsentFlow() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [tenantId, setTenantId] = useState('')

  useEffect(() => {
    // tenant_id for Telegram deep-link — from HttpOnly session via /auth/me
    getMe().then((u) => setTenantId(u.tenant_id || u.username || '')).catch(() => {})
  }, [])

  const handleAgree = async () => {
    setLoading(true)
    setError('')
    try {
      await postConsent({ purpose: 'vision_extraction', consent_text_version: 'nd13-v1' })
      localStorage.setItem('khe_consent_given', 'true')
      navigate('/chat', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleLater = () => {
    navigate('/chat', { replace: true })
  }

  const handleTelegram = async () => {
    // Record reminder_send intent before opening bot link.
    // channel_target_ref is null — Telegram chat_id is captured when user sends /start to the bot.
    try {
      await postConsent({ purpose: 'reminder_send', channel: 'telegram', channel_target_ref: null })
    } catch {
      // Non-blocking: open the deep-link regardless; backend captures chat_id on /start.
    }
    window.open(`https://t.me/${TELEGRAM_BOT_USERNAME}?start=${tenantId}`, '_blank', 'noopener')
  }

  const s = {
    page: {
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: t.colors.surfaceAlt,
    },
    scroll: {
      flex: 1,
      overflowY: 'auto',
      padding: `${t.space[4]}px`,
      maxWidth: 480,
      width: '100%',
      margin: '0 auto',
    },
    header: {
      textAlign: 'center',
      marginBottom: `${t.space[6]}px`,
      paddingTop: `${t.space[5]}px`,
    },
    headerIcon: {
      fontSize: 40,
      marginBottom: `${t.space[2]}px`,
    },
    title: {
      fontSize: 20,
      fontWeight: 700,
      color: t.colors.ink,
      lineHeight: 1.35,
    },
    card: {
      background: t.colors.surface,
      borderRadius: t.radius.lg,
      padding: `${t.space[5]}px`,
      boxShadow: t.shadow.md,
      marginBottom: `${t.space[4]}px`,
    },
    bullet: {
      display: 'flex',
      gap: `${t.space[3]}px`,
      marginBottom: `${t.space[4]}px`,
      alignItems: 'flex-start',
    },
    bulletIcon: {
      fontSize: 18,
      flexShrink: 0,
      marginTop: 1,
    },
    bulletText: {
      fontSize: 14,
      color: t.colors.ink,
      lineHeight: 1.55,
    },
    bulletBold: {
      fontWeight: 700,
    },
    footerNote: {
      fontSize: 12,
      color: t.colors.inkMuted,
      textAlign: 'center',
      padding: `${t.space[3]}px`,
      borderTop: `1px solid ${t.colors.border}`,
      marginTop: `${t.space[3]}px`,
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
    btnPrimary: {
      width: '100%',
      padding: `${t.space[4]}px`,
      background: loading ? t.colors.primaryHover : t.colors.primary,
      color: '#fff',
      border: 'none',
      borderRadius: t.radius.md,
      fontSize: 15,
      fontWeight: 600,
      cursor: loading ? 'not-allowed' : 'pointer',
      marginBottom: `${t.space[3]}px`,
    },
    btnGhost: {
      width: '100%',
      padding: `${t.space[3]}px`,
      background: 'transparent',
      color: t.colors.inkMuted,
      border: `1.5px solid ${t.colors.border}`,
      borderRadius: t.radius.md,
      fontSize: 14,
      fontWeight: 500,
      cursor: 'pointer',
    },
    laterNote: {
      fontSize: 12,
      color: t.colors.inkSubtle,
      textAlign: 'center',
      marginTop: `${t.space[2]}px`,
    },
    separator: {
      display: 'flex',
      alignItems: 'center',
      gap: `${t.space[3]}px`,
      margin: `${t.space[5]}px 0`,
      color: t.colors.inkSubtle,
      fontSize: 12,
    },
    separatorLine: {
      flex: 1,
      height: 1,
      background: t.colors.border,
    },
    telegramSection: {
      textAlign: 'center',
    },
    telegramTitle: {
      fontSize: 14,
      fontWeight: 600,
      color: t.colors.ink,
      marginBottom: `${t.space[3]}px`,
    },
    btnTelegram: {
      padding: `${t.space[3]}px ${t.space[5]}px`,
      background: '#2AABEE',
      color: '#fff',
      border: 'none',
      borderRadius: t.radius.md,
      fontSize: 14,
      fontWeight: 600,
      cursor: 'pointer',
      marginBottom: `${t.space[2]}px`,
    },
    telegramNote: {
      fontSize: 12,
      color: t.colors.inkSubtle,
    },
  }

  return (
    <div style={s.page}>
      <div style={s.scroll}>
        <div style={s.header}>
          <div style={s.headerIcon}>📄</div>
          <div style={s.title}>Đồng ý để Khế đọc tài liệu của bạn</div>
        </div>

        <div style={s.card}>
          <div style={s.bullet}>
            <span style={s.bulletIcon}>📖</span>
            <span style={s.bulletText}>
              <span style={s.bulletBold}>Mục đích:</span> chỉ để ĐỌC và bóc tách thông tin — Khế KHÔNG soạn, KHÔNG sửa, KHÔNG ký nội dung pháp lý của bạn.
            </span>
          </div>

          <div style={s.bullet}>
            <span style={s.bulletIcon}>🌐</span>
            <span style={s.bulletText}>
              <span style={s.bulletBold}>Nơi xử lý:</span> tài liệu được gửi tới dịch vụ AI tại Hoa Kỳ (Google và Anthropic) để đọc.
            </span>
          </div>

          <div style={{ ...s.bullet, marginBottom: 0 }}>
            <span style={s.bulletIcon}>🔐</span>
            <span style={s.bulletText}>
              <span style={s.bulletBold}>Quyền của bạn:</span> bạn có thể THU HỒI đồng ý này bất cứ lúc nào trong phần Cài đặt.
            </span>
          </div>

          <div style={s.footerNote}>
            Bạn có quyền yêu cầu xem, sửa, hoặc xóa dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP.
          </div>
        </div>

        {error && <div style={s.error}>{error}</div>}

        <button style={s.btnPrimary} onClick={handleAgree} disabled={loading}>
          {loading ? 'Đang ghi nhận...' : 'Đồng ý cho Khế đọc tài liệu của tôi'}
        </button>

        <button style={s.btnGhost} onClick={handleLater}>
          Để sau
        </button>

        <div style={s.laterNote}>
          Chọn "Để sau": bạn vẫn dùng được Khế ở chế độ chỉ-xem, nhưng chưa bóc tách tài liệu.
        </div>

        <div style={s.separator}>
          <div style={s.separatorLine} />
          <span>hoặc</span>
          <div style={s.separatorLine} />
        </div>

        <div style={s.telegramSection}>
          <div style={s.telegramTitle}>📱 Nhận nhắc hạn qua Telegram</div>
          <div>
            <button style={s.btnTelegram} onClick={handleTelegram}>
              Kết nối Telegram
            </button>
          </div>
          <div style={s.telegramNote}>
            Sau khi nhắn /start cho bot, Khế sẽ nhắc bạn trước khi hợp đồng hết hạn.
          </div>
        </div>
      </div>
    </div>
  )
}
