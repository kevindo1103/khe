import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { LoginRequest, User, UserOut } from '../types/auth';
import { apiFetch } from '../lib/api';

export interface AuthState {
  user: User | null;
  isLoading: boolean;
}

export function useAuth() {
  const navigate = useNavigate();
  const [state, setState] = useState<AuthState>({ user: null, isLoading: true });

  // One-time purge of stale localStorage token from old Bearer model
  useEffect(() => {
    localStorage.removeItem('khe_access_token');
  }, []);

  // On mount: check session via /auth/me
  useEffect(() => {
    let cancelled = false;
    apiFetch<UserOut>('/auth/me')
      .then((user) => {
        if (!cancelled) setState({ user, isLoading: false });
      })
      .catch(() => {
        if (!cancelled) setState({ user: null, isLoading: false });
      });
    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (payload: LoginRequest): Promise<void> => {
    setState(s => ({ ...s, isLoading: true }));
    try {
      await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      const user = await apiFetch<UserOut>('/auth/me');
      setState({ user, isLoading: false });
    } catch (err) {
      setState(s => ({ ...s, isLoading: false }));
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiFetch('/auth/logout', { method: 'POST' });
    } catch {
      // best-effort; cookie will expire naturally
    }
    setState({ user: null, isLoading: false });
    navigate('/admin/login');
  }, [navigate]);

  return {
    user: state.user,
    isLoading: state.isLoading,
    isAuthenticated: !!state.user,
    login,
    logout,
  };
}
