'use client';

/**
 * AuthContext — client-side auth state management.
 *
 * Provides: user, token, isPremium, isLoading, login(), register(), logout()
 * On mount, checks /api/auth/me to restore session from httpOnly cookie.
 */
import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';

// ─── Types ──────────────────────────────────────────────────────────

interface User {
  id: number;
  email: string;
  name: string | null;
  subscription: 'free' | 'mentorado' | 'admin';
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isPremium: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ error?: string }>;
  register: (email: string, password: string, name?: string) => Promise<{ error?: string }>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ─── Hook ───────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
}

// ─── Provider ───────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isPremium = user?.subscription === 'mentorado' || user?.subscription === 'admin';

  // Restore session on mount (cookie-based)
  useEffect(() => {
    let cancelled = false;

    fetch('/api/auth/me', { signal: AbortSignal.timeout(5000) })
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json();
          if (!cancelled && data.user) {
            setUser(data.user);
          }
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        return { error: data.error || 'Login failed' };
      }

      setToken(data.token);
      setUser(data.user);
      return {};
    } catch (e: any) {
      return { error: e.message || 'Network error' };
    }
  }, []);

  const register = useCallback(async (email: string, password: string, name?: string) => {
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name }),
      });

      const data = await res.json();

      if (!res.ok) {
        return { error: data.error || 'Registration failed' };
      }

      setToken(data.token);
      setUser(data.user);
      return {};
    } catch (e: any) {
      return { error: e.message || 'Network error' };
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch { /* ignore */ }
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isPremium, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
