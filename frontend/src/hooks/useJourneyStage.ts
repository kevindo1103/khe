import { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../lib/api';
import type { TenantMeOut } from '../types/tenant';

/**
 * tenant_journey_stage — drives home routing + first-session nav-lock (#198/#213).
 *
 * Server-owned (backend #213): reads `GET /tenants/me`. The backend auto-advances
 * the stage on real events (upload→EXTRACTING, extraction→NEEDS_REVIEW/CONFIRMED,
 * reminder channel→ACTIVATED) and clears `is_first_session` atomically at
 * ACTIVATED+. Monotonic/forward-only is enforced server-side, so the FE only
 * reads — no client heuristic, no localStorage floor.
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

function coerceStage(s: string): JourneyStage {
  return (JOURNEY_STAGES as readonly string[]).includes(s) ? (s as JourneyStage) : 'NEW';
}

export interface JourneyState {
  stage: JourneyStage;
  isFirstSession: boolean;
  loading: boolean;
  error: string;
  refetch: () => void;
}

export function useJourneyStage(): JourneyState {
  const [stage, setStage] = useState<JourneyStage>('NEW');
  // default unlocked until known — never flash-lock the nav for a returning user
  const [isFirstSession, setIsFirstSession] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const me = await apiFetch<TenantMeOut>('/tenants/me');
      setStage(coerceStage(me.journey_stage));
      setIsFirstSession(me.is_first_session);
    } catch (err) {
      setError((err as { message?: string }).message || 'Không thể tải trạng thái');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { stage, isFirstSession, loading, error, refetch: load };
}
