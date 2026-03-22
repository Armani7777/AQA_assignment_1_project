import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/client";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const refreshMe = async () => {
    try { setUser(await api("/api/auth/me/")); } catch { setUser(null); }
  };

  useEffect(() => { if (localStorage.getItem("access")) refreshMe(); }, []);

  const login = async (email, password) => {
    const data = await api("/api/auth/login/", { method: "POST", body: JSON.stringify({ email, password }) });
    localStorage.setItem("access", data.access);
    localStorage.setItem("refresh", data.refresh);
    await refreshMe();
  };

  const register = async (payload) => {
    await api("/api/auth/register/", { method: "POST", body: JSON.stringify(payload) });
    await login(payload.email, payload.password);
  };

  const logout = async () => {
    const refresh = localStorage.getItem("refresh");
    if (refresh) {
      try { await api("/api/auth/logout/", { method: "POST", body: JSON.stringify({ refresh }) }); } catch {}
    }
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, login, register, logout, refreshMe }}>{children}</AuthContext.Provider>;
}
