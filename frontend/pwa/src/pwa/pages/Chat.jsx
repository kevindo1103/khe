import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { chatQuery, logout } from '../api'
import { theme } from '../theme'
import ChatBubble from '../components/ChatBubble'

const t = theme

const SUGGESTION_CHIPS = [
  'Cái gì sắp hết hạn?',
  'Tìm HĐ với Hải Đăng',
  'HĐ thuê Q7 còn hạn bao lâu?',
]

function hasConsent() {
  return localStorage.getItem('khe_consent_given') === 'true'
}

export default function Chat() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const consentOk = hasConsent()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (question) => {
    if (!question.trim() || !consentOk || loading) return
    const userMsg = { role: 'user', text: question }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)

    try {
      const data = await chatQuery({ question })
      // Backend shape: {answer, found, sources[{file_name, document_id}]}
      // found:false = D-08 not-found path; sources[] may be empty
      const isNotFound = !data.found
      setMessages((m) => [
        ...m,
        {
          role: 'bot',
          text: data.answer || null,
          source: data.sources?.[0]?.file_name || null,
          notFound: isNotFound,
        },
      ])
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'bot', text: `Lỗi: ${err.message}`, source: null, notFound: false, isError: true },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(input)
  }

  const handleChip = (chip) => {
    setInput(chip)
    sendMessage(chip)
  }

  const handleLogout = async () => {
    localStorage.removeItem('khe_consent_given') // non-secret UI hint only
    await logout() // clears HttpOnly cookie server-side
    navigate('/login', { replace: true })
  }

  const s = {
    page: {
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: t.colors.surfaceAlt,
      maxWidth: 480,
      margin: '0 auto',
    },
    header: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: `${t.space[4]}px ${t.space[4]}px`,
      background: t.colors.surface,
      borderBottom: `1px solid ${t.colors.border}`,
      boxShadow: t.shadow.md,
      flexShrink: 0,
    },
    headerLeft: {},
    headerTitle: {
      fontSize: 22,
      fontWeight: 700,
      color: t.colors.primary,
      letterSpacing: '-0.3px',
    },
    headerSub: {
      fontSize: 12,
      color: t.colors.inkMuted,
      marginTop: 1,
    },
    logoutBtn: {
      background: 'none',
      border: 'none',
      color: t.colors.inkSubtle,
      fontSize: 13,
      cursor: 'pointer',
      padding: `${t.space[1]}px ${t.space[2]}px`,
    },
    consentBanner: {
      background: t.colors.warningSoft,
      borderBottom: `1px solid #E8C87A`,
      padding: `${t.space[3]}px ${t.space[4]}px`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexShrink: 0,
    },
    consentBannerText: {
      fontSize: 13,
      color: t.colors.warning,
      flex: 1,
    },
    consentBannerLink: {
      fontSize: 13,
      color: t.colors.primary,
      fontWeight: 600,
      cursor: 'pointer',
      marginLeft: `${t.space[3]}px`,
      background: 'none',
      border: 'none',
      padding: 0,
    },
    messageList: {
      flex: 1,
      overflowY: 'auto',
      padding: `${t.space[4]}px`,
      display: 'flex',
      flexDirection: 'column',
      gap: `${t.space[3]}px`,
    },
    emptyState: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: `${t.space[3]}px`,
      padding: `${t.space[6]}px ${t.space[4]}px`,
    },
    emptyIcon: {
      fontSize: 48,
    },
    emptyTitle: {
      fontSize: 18,
      fontWeight: 600,
      color: t.colors.ink,
      textAlign: 'center',
    },
    emptyDesc: {
      fontSize: 14,
      color: t.colors.inkMuted,
      textAlign: 'center',
      lineHeight: 1.55,
    },
    chipsWrapper: {
      padding: `${t.space[2]}px ${t.space[4]}px`,
      flexShrink: 0,
    },
    chipsScroll: {
      display: 'flex',
      gap: `${t.space[2]}px`,
      overflowX: 'auto',
      paddingBottom: `${t.space[1]}px`,
      scrollbarWidth: 'none',
    },
    chip: {
      whiteSpace: 'nowrap',
      padding: `${t.space[2]}px ${t.space[3]}px`,
      background: t.colors.primarySoft,
      color: t.colors.primary,
      border: `1px solid #B4D5C9`,
      borderRadius: t.radius.pill,
      fontSize: 13,
      fontWeight: 500,
      cursor: 'pointer',
      flexShrink: 0,
    },
    inputArea: {
      padding: `${t.space[3]}px ${t.space[4]}px ${t.space[4]}px`,
      background: t.colors.surface,
      borderTop: `1px solid ${t.colors.border}`,
      flexShrink: 0,
    },
    inputRow: {
      display: 'flex',
      gap: `${t.space[2]}px`,
      alignItems: 'center',
      background: t.colors.surfaceAlt,
      borderRadius: t.radius.pill,
      padding: `${t.space[2]}px ${t.space[2]}px ${t.space[2]}px ${t.space[4]}px`,
      border: `1.5px solid ${t.colors.border}`,
    },
    textInput: {
      flex: 1,
      border: 'none',
      background: 'transparent',
      fontSize: 15,
      color: t.colors.ink,
      outline: 'none',
    },
    sendBtn: {
      width: 36,
      height: 36,
      borderRadius: '50%',
      background: consentOk ? t.colors.primary : t.colors.border,
      border: 'none',
      color: '#fff',
      fontSize: 16,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: consentOk ? 'pointer' : 'not-allowed',
      flexShrink: 0,
    },
  }

  const showEmpty = messages.length === 0 && !loading

  return (
    <div style={s.page}>
      <div style={s.header}>
        <div style={s.headerLeft}>
          <div style={s.headerTitle}>Khế</div>
          <div style={s.headerSub}>Hỏi-đáp hồ sơ</div>
        </div>
        <button style={s.logoutBtn} onClick={handleLogout}>Đăng xuất</button>
      </div>

      {!consentOk && (
        <div style={s.consentBanner}>
          <span style={s.consentBannerText}>
            Bạn chưa đồng ý để Khế đọc tài liệu. Tính năng hỏi-đáp tạm thời bị tắt.
          </span>
          <button style={s.consentBannerLink} onClick={() => navigate('/consent')}>
            Đồng ý ngay
          </button>
        </div>
      )}

      {showEmpty ? (
        <div style={s.emptyState}>
          <div style={s.emptyIcon}>💬</div>
          <div style={s.emptyTitle}>Hỏi Khế về hợp đồng của bạn</div>
          <div style={s.emptyDesc}>
            Khế tìm thông tin từ tài liệu bạn đã tải lên và nhắc bạn trước khi hợp đồng hết hạn.
          </div>
        </div>
      ) : (
        <div style={s.messageList}>
          {messages.map((msg, i) => (
            <ChatBubble key={i} message={msg} />
          ))}
          {loading && <ChatBubble message={{ role: 'bot', text: 'Đang tìm...', loading: true }} />}
          <div ref={bottomRef} />
        </div>
      )}

      {showEmpty && (
        <div style={s.chipsWrapper}>
          <div style={s.chipsScroll}>
            {SUGGESTION_CHIPS.map((chip) => (
              <button key={chip} style={s.chip} onClick={() => handleChip(chip)}>
                {chip}
              </button>
            ))}
          </div>
        </div>
      )}

      <div style={s.inputArea}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: `${t.space[2]}px` }}>
          {messages.length > 0 && (
            <div style={{ ...s.chipsScroll, marginBottom: `${t.space[1]}px` }}>
              {SUGGESTION_CHIPS.map((chip) => (
                <button
                  key={chip}
                  type="button"
                  style={s.chip}
                  onClick={() => handleChip(chip)}
                >
                  {chip}
                </button>
              ))}
            </div>
          )}
          <div style={s.inputRow}>
            <input
              type="text"
              style={s.textInput}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={consentOk ? 'Hỏi về hợp đồng của bạn...' : 'Chưa bật hỏi-đáp'}
              disabled={!consentOk || loading}
            />
            <button type="submit" style={s.sendBtn} disabled={!consentOk || loading || !input.trim()}>
              ➤
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
