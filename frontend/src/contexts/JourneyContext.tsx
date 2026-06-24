import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { apiFetch } from '../lib/api';
import type { TenantMeOut } from '../types/tenant';

/**
 * Shared tenant journey state (#213/#238). One `GET /tenants/me` for the whole
 * admin shell — AdminShell (nav-lock), Home (stage routing) and DocumentDetail
 * (refetch after confirm) all read the same instance, so a doc-confirm that
 * advances NEEDS_REVIEW→CONFIRMED unlocks the sidebar atomically via refetch().
 * Replaces the per-component useJourneyStage hook (and folds #222 single-fetch).
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

interface JourneyState {
  stage: JourneyStage;
  isFirstSession: boolean;
  loading: boolean;
  error: string;
  refetch: () => Promise<void>;
}

const JourneyContext = createContext<JourneyState | null>(null);

export function JourneyProvider({ children }: { children: ReactNode }) {
  const [stage, setStage] = useState<JourneyStage>('NEW');
  const [isFirstSession, setIsFirstSession] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refetch = useCallback(async () => {
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
    refetch();
  }, [refetch]);

  return (
    <JourneyContext.Provider value={{ stage, isFirstSession, loading, error, refetch }}>
      {children}
    </JourneyContext.Provider>
  );
}

export function useJourney(): JourneyState {
  const ctx = useContext(JourneyContext);
  if (!ctx) throw new Error('useJourney must be used within JourneyProvider');
  return ctx;
}
