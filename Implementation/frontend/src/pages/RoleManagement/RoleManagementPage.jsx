import React, { useEffect, useMemo, useState } from "react";
import "./RoleManagement.css";
import { useAuth } from "../../hooks/useAuth";
import {
  listAdmins,
  inviteAdmin,
  resendInvite,
  activateAdmin,
  deactivateAdmin,
  updateAdmin,
} from "../../api/adminApi";
import InviteModal from "./components/InviteModal";
import RoleRow from "./components/RoleRow";

export default function RoleManagementPage() {
  const { user } = useAuth(); // { id, email, role, ... }
  const [admins, setAdmins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [filter, setFilter] = useState("all");
  const [showInvite, setShowInvite] = useState(false);

  const canInvite = user?.role === "owner" || user?.role === "admin";
  const canEditRoles = user?.role === "owner";

  async function load() {
    setErr("");
    setLoading(true);
    try {
      const data = await listAdmins();
      setAdmins(data);
    } catch (e) {
      setErr(e.message || "Failed to load admins");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    if (filter === "all") return admins;
    if (filter === "active") return admins.filter((a) => a.status === "active");
    if (filter === "invited") return admins.filter((a) => a.status === "invited");
    if (filter === "disabled") return admins.filter((a) => a.status === "disabled");
    return admins;
  }, [admins, filter]);

  // actions handed down to rows
  const actions = {
    async onResend(id) {
      await resendInvite(id);
      await load();
      alert("Invite resent.");
    },
    async onActivate(id) {
      await activateAdmin(id);
      await load();
    },
    async onDeactivate(id) {
      await deactivateAdmin(id);
      await load();
    },
    async onChangeRole(id, nextRole) {
      await updateAdmin(id, { role: nextRole });
      await load();
    },
  };

  return (
    <div className="rm-wrapper">
      <div className="rm-header">
        <h1>Role Management</h1>

        <div className="rm-actions">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="rm-select"
          >
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="invited">Invited</option>
            <option value="disabled">Disabled</option>
          </select>

          {canInvite && (
            <button className="rm-btn primary" onClick={() => setShowInvite(true)}>
              + Invite
            </button>
          )}
        </div>
      </div>

      {err && <div className="rm-error">{err}</div>}
      {loading ? (
        <div className="rm-empty">Loading…</div>
      ) : filtered.length === 0 ? (
        <div className="rm-empty">No admins match this filter.</div>
      ) : (
        <div className="rm-card">
          <table className="rm-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th style={{ width: 220 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a, i) => (
                <RoleRow
                  key={a.id}
                  index={i + 1}
                  me={user}
                  admin={a}
                  canEditRoles={canEditRoles}
                  onResend={actions.onResend}
                  onActivate={actions.onActivate}
                  onDeactivate={actions.onDeactivate}
                  onChangeRole={actions.onChangeRole}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

     {showInvite && (
  <InviteModal
    canInviteOwner={user?.role === "owner"}
    onClose={() => setShowInvite(false)}
    onSubmit={async (payload) => {
      const res = await inviteAdmin(payload); // <— capture response
      await load();
      return res; // <— so the modal can show invite_url + copy buttons
    }}
  />
)}

    </div>
  );
}
