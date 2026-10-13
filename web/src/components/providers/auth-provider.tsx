"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { getAuthStatus, logout as apiLogout, type AuthStatus } from "@/lib/api";

type AuthContextValue = {
  /** 첫 조회가 끝나기 전에는 화면을 그리지 않는다 — 로그인 화면이 깜빡이는 걸 막기 위함. */
  loading: boolean;
  status: AuthStatus | null;
  refresh: () => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setStatus(await getAuthStatus());
    } catch {
      // 백엔드가 꺼져 있어도 로그인 화면은 떠야 한다.
      setStatus({ authenticated: false });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const signOut = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      setStatus({ authenticated: false });
    }
  }, []);

  return (
    <AuthContext.Provider value={{ loading, status, refresh, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth 는 AuthProvider 안에서만 쓸 수 있어요");
  return ctx;
}
