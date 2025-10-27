import "./Login.css";
import LoginForm from "./LoginForm";
import { useAuth } from "../../hooks/useAuth";
import { useEffect, useState } from "react";

export default function LoginPage() {
  const { user, logout, loading } = useAuth();
  const [busy, setBusy] = useState(false);

  if (loading) return null; // still checking cookie

  async function handleLogout() {
    setBusy(true);
    try {
      await logout();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-left">
        <h1>Petroff Parking</h1>
      </div>

      <div className="login-right">
        <h2>{user ? "You are logged in!" : "Login"}</h2>

        {user ? (
          <>
            <p>{user.email}</p>
            <button onClick={handleLogout} disabled={busy}>
              {busy ? "Logging out…" : "Logout"}
            </button>
          </>
        ) : (
          <LoginForm />
        )}
      </div>
    </div>
  );
}
