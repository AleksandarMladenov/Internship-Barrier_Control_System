import React, { createContext, useContext, useEffect, useState } from "react";
import { me, login as apiLogin, logout as apiLogout } from "../api/authApi";

const Ctx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    me().then(setUser).catch(() => setUser(null)).finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    await apiLogin(email, password);
    const u = await me();
    setUser(u);
  }

  async function logout() {
    await apiLogout();
    setUser(null);
  }

  return (
    <Ctx.Provider value={{ user, loading, login, logout }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
