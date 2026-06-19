import React from 'react'
import { theme } from '../theme'

const t = theme

const D08_MAIN = 'Không tìm thấy thông tin này trong hồ sơ của bạn.'
const D08_SUB = 'Khế chỉ trả lời từ tài liệu bạn đã tải lên — không phỏng đoán. Bạn có thể hỏi cách khác hoặc tải thêm tài liệu.'

export default function ChatBubble({ message }) {
  const { role, text, source, notFound, loading: isLoading, isError } = message

  const isUser = role === 'user'

  if (isUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <div
          style={{
            maxWidth: '78%',
            background: t.colors.primary,
            color: '#fff',
            borderRadius: `${t.radius.lg}px ${t.radius.lg}px ${t.radius.sm}px ${t.radius.lg}px`,
            padding: `${t.space[3]}px ${t.space[4]}px`,
            fontSize: 14,
            lineHeight: 1.55,
            boxShadow: t.shadow.md,
          }}
        >
          {text}
        </div>
      </div>
    )
  }

  if (notFound) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-start', flexDirection: 'column', gap: 4, maxWidth: '88%' }}>
        <div
          style={{
            background: t.colors.warningSoft,
            borderRadius: `${t.radius.sm}px ${t.radius.lg}px ${t.radius.lg}px ${t.radius.lg}px`,
            padding: `${t.space[3]}px ${t.space[4]}px`,
            fontSize: 14,
            lineHeight: 1.6,
            border: `1px solid #E8C87A`,
          }}
        >
          <div style={{ color: t.colors.warning, fontWeight: 600, marginBottom: `${t.space[1]}px` }}>
            {D08_MAIN}
          </div>
          <div style={{ color: t.colors.warning, fontSize: 13, opacity: 0.9 }}>
            {D08_SUB}
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
        <div
          style={{
            background: t.colors.surface,
            border: `1px solid ${t.colors.border}`,
            borderRadius: `${t.radius.sm}px ${t.radius.lg}px ${t.radius.lg}px ${t.radius.lg}px`,
            padding: `${t.space[3]}px ${t.space[4]}px`,
            fontSize: 14,
            color: t.colors.inkMuted,
            boxShadow: t.shadow.md,
            fontStyle: 'italic',
          }}
        >
          Đang tìm...
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-start', maxWidth: '88%' }}>
      <div
        style={{
          background: isError ? t.colors.dangerSoft : t.colors.surface,
          border: `1px solid ${isError ? '#F5B7B1' : t.colors.border}`,
          borderRadius: `${t.radius.sm}px ${t.radius.lg}px ${t.radius.lg}px ${t.radius.lg}px`,
          padding: `${t.space[3]}px ${t.space[4]}px`,
          fontSize: 14,
          lineHeight: 1.6,
          color: isError ? t.colors.danger : t.colors.ink,
          boxShadow: t.shadow.md,
        }}
      >
        {text}
      </div>
      {source && (
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: `${t.space[1]}px`,
            background: t.colors.primarySoft,
            color: t.colors.primary,
            borderRadius: t.radius.pill,
            padding: `${t.space[1]}px ${t.space[3]}px`,
            fontSize: 12,
            fontWeight: 500,
            border: `1px solid #B4D5C9`,
          }}
        >
          📄 Nguồn: {source}
        </div>
      )}
    </div>
  )
}
