import React, { createContext, useContext, useEffect, useState } from "react";
import { me, login as apiLogin, logout as apiLogout } from "../api/authApi";

const Ctx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      const u = await me();
      setUser(u);
    } catch {
      setUser(null);
    }
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    await apiLogin(email, password);
    await refresh();
  }
  async function logout() {
    await apiLogout();
    setUser(null);
  }

  return (
    <Ctx.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
