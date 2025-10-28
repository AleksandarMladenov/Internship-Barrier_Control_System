import React, { useState } from "react";

export default function InviteModal({ canInviteOwner, onClose, onSubmit }) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState("admin");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null); // { invite_url, ... }

  async function submit(e) {
    e.preventDefault();
    if (busy) return;
    setErr("");
    try {
      setBusy(true);
      const res = await onSubmit({ email, name: name || null, role });
      setResult(res);
    } catch (e2) {
      setErr(e2.message || "Failed to send invite");
    } finally {
      setBusy(false);
    }
  }

  function copy(text) {
    navigator.clipboard.writeText(text).then(() => {
      alert("Invite link copied!");
    });
  }

  return (
    <div className="rm-modal-backdrop" onClick={onClose}>
      <div className="rm-modal" onClick={(e) => e.stopPropagation()}>
        {!result ? (
          <>
            <h3>Invite Admin</h3>
            {err && <div className="rm-error">{err}</div>}
            <form onSubmit={submit}>
              <label>Email</label>
              <input
                type="email"
                required
                placeholder="person@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />

              <label>Name (optional)</label>
              <input
                type="text"
                placeholder="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />

              <label>Role</label>
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="viewer">Viewer</option>
                <option value="admin">Admin</option>
                {canInviteOwner && <option value="owner">Owner</option>}
              </select>

              <div className="rm-modal-actions">
                <button type="button" className="rm-btn" onClick={onClose}>
                  Cancel
                </button>
                <button type="submit" className="rm-btn primary" disabled={busy}>
                  {busy ? "Sending…" : "Send Invite"}
                </button>
              </div>
            </form>
          </>
        ) : (
          <>
            <h3>Invite Sent</h3>
            <p>
              Share this link with <strong>{email}</strong> so they can set a password and join:
            </p>
            <div className="rm-invite-link">
              <code>{result.invite_url || "(email sending enabled: link sent)"}</code>
            </div>
            {result.invite_url && (
              <div className="rm-modal-actions">
                <a className="rm-btn" href={result.invite_url} target="_blank" rel="noreferrer">Open Link</a>
                <button className="rm-btn primary" onClick={() => copy(result.invite_url)}>Copy Link</button>
                <button className="rm-btn" onClick={onClose}>Done</button>
              </div>
            )}
            {!result.invite_url && (
              <div className="rm-modal-actions">
                <button className="rm-btn" onClick={onClose}>Close</button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
