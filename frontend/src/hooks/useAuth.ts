import { useState, useCallback, useEffect } from 'react';
import type { LoginRequest, TokenResponse, User, JwtPayload } from '../types/auth';
import { apiFetch } from '../lib/api';

const TOKEN_KEY = 'khe_access_token';

function decodeJwt(token: string): JwtPayload | null {
  try {
    const base64 = token.split('.')[1];
    const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(json) as JwtPayload;
  } catch {
    return null;
  }
}

function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function buildUserFromToken(token: string): User | null {
  const payload = decodeJwt(token);
  if (!payload) return null;
  return {
    username: payload.sub,
    tenant_id: payload.tenant_id,
    role: payload.role,
  };
}

export interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>(() => {
    const token = getStoredToken();
    const user = token ? buildUserFromToken(token) : null;
    return { token, user, isLoading: false };
  });

  const login = useCallback(async (payload: LoginRequest): Promise<void> => {
    setState(s => ({ ...s, isLoading: true }));
    try {
      const data = await apiFetch<TokenResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      localStorage.setItem(TOKEN_KEY, data.access_token);
      const user = buildUserFromToken(data.access_token);
      setState({ token: data.access_token, user, isLoading: false });
    } catch (err) {
      setState(s => ({ ...s, isLoading: false }));
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setState({ token: null, user: null, isLoading: false });
  }, []);

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === TOKEN_KEY) {
        const token = e.newValue;
        const user = token ? buildUserFromToken(token) : null;
        setState({ token, user, isLoading: false });
      }
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  return {
    token: state.token,
    user: state.user,
    isLoading: state.isLoading,
    isAuthenticated: !!state.token,
    login,
    logout,
  };
}
