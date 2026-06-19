// Option A (DEC-#43 LOCKED): HttpOnly cookie auth.
// Backend sets Set-Cookie: khe_session=...; HttpOnly; Secure; SameSite=Strict on login.
// PWA never touches the token — credentials: 'include' sends cookie automatically.
// No localStorage token, no Authorization header.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const MOCK = import.meta.env.VITE_MOCK_API === 'true'

// Mock session state (in-memory only — simulates HttpOnly cookie presence)
let _mockSession = null

function mockDelay(ms = 600) {
  return new Promise((r) => setTimeout(r, ms))
}

export async function login({ tenant_id, username, password }) {
  if (MOCK) {
    await mockDelay()
    if (!tenant_id || !username || !password) throw new Error('Thiếu thông tin đăng nhập')
    _mockSession = { user_id: 1, username, tenant_id, role: 'owner' }
    return { user: { username, role: 'owner' }, tenant_id }
  }
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tenant_id, username, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Đăng nhập thất bại')
  }
  return res.json()
}

// TODO(backend): GET /auth/me — returns {sub, tenant_id, role} from HttpOnly session cookie.
// 200 = authenticated; 401 = not authenticated (redirect to /login).
export async function getMe() {
  if (MOCK) {
    await mockDelay(200)
    if (!_mockSession) throw new Error('Not authenticated')
    return _mockSession
  }
  const res = await fetch(`${BASE_URL}/auth/me`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Not authenticated')
  return res.json()
}

export async function logout() {
  if (MOCK) {
    await mockDelay(300)
    _mockSession = null
    return
  }
  // TODO(backend): POST /auth/logout — clears HttpOnly cookie server-side.
  await fetch(`${BASE_URL}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  })
}

// Backend returns {answer, found, sources[]} — found:false means D-08 not-found path.
// sources[] items: {file_name, document_id, ...}
export async function chatQuery({ question }) {
  if (MOCK) {
    await mockDelay(800)
    const q = question.toLowerCase()
    if (q.includes('hết hạn') || q.includes('sắp')) {
      return {
        answer: 'Có 1 hợp đồng sắp hết hạn trong quý này:\n• HĐ thuê mặt bằng Q7 — hết hạn 30/09/2026 (còn 104 ngày).',
        found: true,
        sources: [{ file_name: 'HĐ thuê mặt bằng Q7', document_id: 1 }],
      }
    }
    return { answer: 'Không tìm thấy thông tin này trong hồ sơ của bạn.', found: false, sources: [] }
  }
  const res = await fetch(`${BASE_URL}/chat/query`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Lỗi hỏi-đáp')
  }
  return res.json()
}

// TODO(#22): POST /consent not yet implemented on backend — consent gate enforced server-side when shipped
export async function postConsent({ purpose = 'vision_extraction', consent_text_version = 'nd13-v1' }) {
  if (MOCK) {
    await mockDelay()
    return { ok: true, purpose, consent_text_version }
  }
  const res = await fetch(`${BASE_URL}/consent`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ purpose, consent_text_version }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Lỗi ghi consent')
  }
  return res.json()
}
