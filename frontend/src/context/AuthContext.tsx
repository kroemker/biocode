import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { auth as authApi, clearToken, setToken } from "@/api/client";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, loading: true });

  // Restore session from stored token on mount
  useEffect(() => {
    authApi
      .me()
      .then((user) => setState({ user, loading: false }))
      .catch(() => setState({ user: null, loading: false }));
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const { access_token } = await authApi.login(username, password);
    setToken(access_token);
    const user = await authApi.me();
    setState({ user, loading: false });
  }, []);

  const register = useCallback(async (username: string, email: string, password: string) => {
    await authApi.register(username, email, password);
    await login(username, password);
  }, [login]);

  const logout = useCallback(() => {
    clearToken();
    setState({ user: null, loading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
