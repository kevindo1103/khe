import { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../lib/api';
import type { DocumentListOut, DocumentListItem } from '../types/documents';

/**
 * tenant_journey_stage — drives home routing + first-session nav-lock (#198).
 *
 * TODO(#219→#213): replace this client heuristic with the server-owned field
 * `GET /tenant/me { journey_stage, is_first_session }`. Backend #213 is the
 * canonical task; until it ships we approximate from the document list.
 *
 * Two PM constraints honored even in the mock (#198 PM ruling):
 *   1. MONOTONIC / forward-only — we persist the highest stage reached in
 *      localStorage and never report lower, so a new upload on a settled tenant
 *      can't regress the home (the real backend field is non-regressing too).
 *      When #213 lands the swap is clean (drop the persist + heuristic).
 *   2. is_first_session clears once the tenant first reaches the dashboard and
 *      never re-locks.
 */
export const JOURNEY_STAGES = [
  'NEW',
  'EXTRACTING',
  'NEEDS_REVIEW',
  'CONFIRMED',
  'ACTIVATED',
  'STEADY',
] as const;
export type JourneyStage = (typeof JOURNEY_STAGES)[number];

const STAGE_KEY = 'khe_journey_stage_max';     // monotonic floor (mock only)
const FIRST_SESSION_KEY = 'khe_first_session_done';

function ordinal(stage: JourneyStage): number {
  return JOURNEY_STAGES.indexOf(stage);
}

/**
 * Cheap first-session check from localStorage (no fetch) — for nav-lock in the
 * shell. TODO(#219→#213): replace with `is_first_session` from the server.
 */
export function isFirstSessionLocal(): boolean {
  return localStorage.getItem(FIRST_SESSION_KEY) !== 'true';
}

/** Derive a candidate stage from the document list (mock heuristic). */
function deriveFromDocs(docs: DocumentListItem[]): JourneyStage {
  if (docs.length === 0) return 'NEW';
  if (docs.some((d) => d.status === 'processing')) return 'EXTRACTING';
  if (docs.some((d) => d.needs_review || d.status === 'needs_review')) return 'NEEDS_REVIEW';
  // All extracted, nothing flagged → confirmed. ACTIVATED/STEADY distinction
  // needs the reminder-channel signal (backend #213) — not detectable client
  // side, so we report CONFIRMED and let Home show the steady dashboard.
  return 'CONFIRMED';
}

export interface JourneyState {
  stage: JourneyStage;
  isFirstSession: boolean;
  docs: DocumentListItem[];
  loading: boolean;
  error: string;
  refetch: () => void;
}

export function useJourneyStage(): JourneyState {
  const [stage, setStage] = useState<JourneyStage>('NEW');
  const [docs, setDocs] = useState<DocumentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isFirstSession, setIsFirstSession] = useState(
    () => localStorage.getItem(FIRST_SESSION_KEY) !== 'true'
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiFetch<DocumentListOut>('/documents/?page=1&page_size=100');
      setDocs(res.items);

      const candidate = deriveFromDocs(res.items);
      // monotonic floor — never report lower than the highest stage reached
      const persisted = localStorage.getItem(STAGE_KEY) as JourneyStage | null;
      const floor = persisted && JOURNEY_STAGES.includes(persisted) ? persisted : 'NEW';
      const next = ordinal(candidate) >= ordinal(floor) ? candidate : floor;
      if (next !== persisted) localStorage.setItem(STAGE_KEY, next);
      setStage(next);

      // first session clears once the tenant first reaches CONFIRMED+, never re-locks
      if (ordinal(next) >= ordinal('CONFIRMED') && localStorage.getItem(FIRST_SESSION_KEY) !== 'true') {
        localStorage.setItem(FIRST_SESSION_KEY, 'true');
        setIsFirstSession(false);
      }
    } catch (err) {
      setError((err as { message?: string }).message || 'Không thể tải trạng thái');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { stage, isFirstSession, docs, loading, error, refetch: load };
}
