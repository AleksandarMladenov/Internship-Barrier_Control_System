import React, { useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import { acceptInvite } from "../../api/authApi";

export default function AcceptInviteForm({ token }) {
  const { refresh } = useAuth();
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    if (password !== confirm) {
      return setError("Passwords must match");
    }
    try {
      await acceptInvite(token, password, name || null);
      await refresh(); // load logged-in state
      window.location.href = "/dashboard";
    } catch (err) {
      setError("Failed to accept invite. Token may be expired.");
    }
  }

  return (
    <form className="invite-form" onSubmit={onSubmit}>
      {error && <p className="error">{error}</p>}

      <label>Name (optional)</label>
      <input
        type="text"
        placeholder="Your name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />

      <label>Password</label>
      <input
        type="password"
        placeholder="New password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />

      <label>Confirm Password</label>
      <input
        type="password"
        placeholder="Confirm password"
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
        required
      />

      <button type="submit">Activate Account</button>
    </form>
  );
}
