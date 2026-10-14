import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { api, getToken, setToken, setUnauthorizedHandler } from '../api/client';
import type { Me, Perfil } from '../api/types';

interface AuthState {
  user: Me | null;
  carregando: boolean;
  login: (email: string, senha: string) => Promise<void>;
  logout: () => void;
  pode: (...perfis: Perfil[]) => boolean;
}

const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [carregando, setCarregando] = useState(true);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    if (!getToken()) {
      setCarregando(false);
      return;
    }
    api<Me>('/auth/me')
      .then(setUser)
      .catch(() => logout())
      .finally(() => setCarregando(false));
  }, [logout]);

  const login = useCallback(async (email: string, senha: string) => {
    const { access_token } = await api<{ access_token: string }>('/auth/login', {
      body: { email, password: senha },
      auth: false,
    });
    setToken(access_token);
    setUser(await api<Me>('/auth/me'));
  }, []);

  const pode = useCallback(
    (...perfis: Perfil[]) => !!user && (user.perfil === 'admin' || perfis.includes(user.perfil)),
    [user],
  );

  return <Ctx.Provider value={{ user, carregando, login, logout, pode }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useAuth fora do AuthProvider');
  return ctx;
}
