import { createContext, useContext, useEffect, useState } from "react";
import { authApi } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function bootstrap() {
      if (authApi.hasSession()) {
        try {
          const me = await authApi.me();
          if (active) setUser(me);
        } catch {
          authApi.logout();
        }
      }
      if (active) setLoading(false);
    }
    bootstrap();

    const onLogout = () => setUser(null);
    window.addEventListener("tc:logout", onLogout);
    return () => {
      active = false;
      window.removeEventListener("tc:logout", onLogout);
    };
  }, []);

  async function login(username, password) {
    await authApi.login({ username, password });
    const me = await authApi.me();
    setUser(me);
    return me;
  }

  async function register(username, email, password) {
    await authApi.register({ username, email, password });
    return login(username, password);
  }

  function logout() {
    authApi.logout();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, isAuthenticated: !!user }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
}
