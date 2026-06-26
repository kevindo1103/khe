import { useCallback } from 'react';
import { apiFetch } from '../lib/api';
import type { ChatSessionResetIn, ChatSessionResetOut } from '../types/chat';

/**
 * Stage 6 chat session state (DEC-031 v2, #201/#208).
 *
 * Holds a per-device/tab UUID in localStorage so the backend can seed a soft
 * working-set prior across queries. Layout-agnostic on purpose: the Admin chat
 * and the PWA chat share this logic, not the layout (PM split rule on #208).
 *
 * The session_id is a pointer key only — never PII — so persisting it client
 * side is safe; the server stores ID pointers, not message content.
 */
const STORAGE_KEY = 'khe_chat_session_id';

function freshId(): string {
  const id =
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  localStorage.setItem(STORAGE_KEY, id);
  return id;
}

export function useChatSession() {
  /** Return the persisted session id, lazily generating one on first use. */
  const getSessionId = useCallback((): string => {
    return localStorage.getItem(STORAGE_KEY) || freshId();
  }, []);

  /**
   * "🔄 Hỏi mới" — reset the server-side working set for this device/tab, then
   * clear + regenerate the local UUID so subsequent queries start cold but
   * stay stateful. Best-effort: the server row TTL-expires regardless.
   */
  const resetSession = useCallback(async (): Promise<void> => {
    const id = localStorage.getItem(STORAGE_KEY);
    if (id) {
      try {
        await apiFetch<ChatSessionResetOut>('/chat/sessions/reset', {
          method: 'POST',
          body: JSON.stringify({ session_id: id } as ChatSessionResetIn),
        });
      } catch {
        // best-effort — server session will expire on its own TTL
      }
    }
    localStorage.removeItem(STORAGE_KEY);
    freshId();
  }, []);

  return { getSessionId, resetSession };
}
