import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import ChatBubble from './ChatBubble'

// D-08 HARD: exact strings must never drift — one typo breaks NĐ compliance.
const D08_MAIN = 'Không tìm thấy thông tin này trong hồ sơ của bạn.'
const D08_SUB =
  'Khế chỉ trả lời từ tài liệu bạn đã tải lên — không phỏng đoán. Bạn có thể hỏi cách khác hoặc tải thêm tài liệu.'

describe('ChatBubble — D-08 not-found', () => {
  it('renders exact D-08 main string byte-for-byte when notFound:true', () => {
    render(<ChatBubble message={{ role: 'bot', notFound: true, text: null, source: null }} />)
    expect(screen.getByText(D08_MAIN)).toBeInTheDocument()
  })

  it('renders D-08 sub-text when notFound:true', () => {
    render(<ChatBubble message={{ role: 'bot', notFound: true, text: null, source: null }} />)
    expect(screen.getByText(D08_SUB)).toBeInTheDocument()
  })

  it('does NOT show D-08 string for a normal found response', () => {
    render(<ChatBubble message={{ role: 'bot', notFound: false, text: 'Có 1 hợp đồng.', source: null }} />)
    expect(screen.queryByText(D08_MAIN)).not.toBeInTheDocument()
  })

  it('does NOT show D-08 string for a user message', () => {
    render(<ChatBubble message={{ role: 'user', text: 'Hỏi gì đó', notFound: false, source: null }} />)
    expect(screen.queryByText(D08_MAIN)).not.toBeInTheDocument()
  })
})

describe('ChatBubble — source chip', () => {
  it('renders source chip with file_name when source is present', () => {
    render(<ChatBubble message={{ role: 'bot', notFound: false, text: 'Trả lời.', source: 'HĐ thuê Q7' }} />)
    expect(screen.getByText(/Nguồn: HĐ thuê Q7/)).toBeInTheDocument()
  })

  it('does not render source chip when source is null', () => {
    render(<ChatBubble message={{ role: 'bot', notFound: false, text: 'Trả lời.', source: null }} />)
    expect(screen.queryByText(/Nguồn:/)).not.toBeInTheDocument()
  })
})
