import { useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import SocialLoginButtons from "./SocialLoginButtons";
import { useNavigate } from "react-router-dom";

export default function LoginForm() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate("/admins", { replace: true }); // ✅ redirect to dashboard
    } catch (e) {
      setErr(e.message || "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="login-form">
      <label>Email address</label>
      <input type="email" value={email} onChange={(e)=>setEmail(e.target.value)}
             placeholder="you@example.com" required />
      <label>Password</label>
      <input type="password" value={password} onChange={(e)=>setPassword(e.target.value)}
             placeholder="••••••••" required />
      <div className="forgot">Forgot password?</div>
      <button type="submit" disabled={busy}>
        {busy ? "Logging in…" : "Log In"}
      </button>
      {err && <p className="error">{err}</p>}
      <div className="or">— Or continue with —</div>
      <SocialLoginButtons />
    </form>
  );
}
