'use client';

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { clearToken, getToken, login as apiLogin, setToken, apiFetch } from '@/lib/api';

interface AuthUser {
  id: string;
  username: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  role: string;
}

interface AuthContextType {
  user: AuthUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async () => {
    try {
      const me = await apiFetch<AuthUser>('/v1/users/me');
      setUser(me);
    } catch {
      // /v1/users/me not available (pre-migration) — fall back to token payload
      const token = getToken();
      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          setUser({
            id: payload.sub,
            username: payload.username ?? payload.sub,
            email: '',
            display_name: null,
            avatar_url: null,
            role: 'member',
          });
        } catch {
          clearToken();
          setUser(null);
        }
      }
    }
  }, []);

  useEffect(() => {
    const token = getToken();
    if (token) {
      fetchMe().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [fetchMe]);

  const login = useCallback(async (username: string, password: string) => {
    const res = await apiLogin(username, password);
    setToken(res.access_token);
    await fetchMe();
  }, [fetchMe]);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    window.location.href = '/login';
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser: fetchMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
