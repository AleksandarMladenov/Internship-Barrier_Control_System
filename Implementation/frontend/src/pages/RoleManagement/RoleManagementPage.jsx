import React, { useEffect, useMemo, useState } from "react";
import "./RoleManagement.css";
import AdminLayout from "../../layouts/AdminLayout";
import { useAuth } from "../../hooks/useAuth";
import {
  listAdmins, inviteAdmin, resendInvite, activateAdmin,
  deactivateAdmin, updateAdmin,
} from "../../api/adminApi";
import InviteModal from "./components/InviteModal";
import RoleRow from "./components/RoleRow";

export default function RoleManagementPage() {
  const { user } = useAuth(); // { id, email, role }
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

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    if (filter === "all") return admins;
    return admins.filter(a => a.status === filter);
  }, [admins, filter]);

  const actions = {
    async onResend(id)       { await resendInvite(id); await load(); alert("Invite resent."); },
    async onActivate(id)     { await activateAdmin(id); await load(); },
    async onDeactivate(id)   { await deactivateAdmin(id); await load(); },
    async onChangeRole(id,r) { await updateAdmin(id, { role: r }); await load(); },
  };

  return (
    <AdminLayout
      title={
        <span data-cy="role-management-title">
          Role Management
        </span>
      }
      actions={
        <div className="rm-actions" data-cy="role-management-actions">
          <select
            value={filter}
            onChange={(e)=>setFilter(e.target.value)}
            className="rm-select"
            data-cy="role-filter"
          >
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="invited">Invited</option>
            <option value="disabled">Disabled</option>
          </select>

          {canInvite && (
            <button
              className="rm-btn primary"
              onClick={() => setShowInvite(true)}
              data-cy="invite-admin-button"
            >
              +Invite
            </button>
          )}
        </div>
      }
    >
      {err && (
        <div className="rm-error" data-cy="role-management-error">
          {err}
        </div>
      )}

      {loading ? (
        <div className="rm-empty" data-cy="role-management-loading">
          Loading…
        </div>
      ) : filtered.length === 0 ? (
        <div className="rm-empty" data-cy="role-management-empty">
          No admins match this filter.
        </div>
      ) : (
        <div className="rm-card">
          <table className="rm-table" data-cy="admins-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th style={{ width:220 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a,i)=>(
                <RoleRow
                  key={a.id}
                  index={i+1}
                  me={user}
                  admin={a}
                  canEditRoles={canEditRoles}
                  onResend={actions.onResend}
                  onActivate={actions.onActivate}
                  onDeactivate={actions.onDeactivate}
                  onChangeRole={actions.onChangeRole}
                  dataCy={`admin-row-${a.email}`}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showInvite && (
        <div data-cy="invite-modal">
          <InviteModal
            canInviteOwner={user?.role === "owner"}
            onClose={()=>setShowInvite(false)}
            onSubmit={async payload => {
              const res = await inviteAdmin(payload);
              await load();
              return res;
            }}
          />
        </div>
      )}
    </AdminLayout>
  );
}
