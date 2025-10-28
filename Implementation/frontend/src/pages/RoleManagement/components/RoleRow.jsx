import React, { useState } from "react";

export default function RoleRow({
  index,
  me,
  admin,
  canEditRoles,             // true only if current user is owner
  onResend,
  onActivate,
  onDeactivate,
  onChangeRole,
}) {
  const isMe = me?.id === admin.id;
  const targetIsOwner = admin.role === "owner";
  const actorIsOwner = me?.role === "owner";

  // You can manage this row if:
  // - you're not editing yourself
  // - you're owner (can manage anyone) OR you're admin managing a non-owner
  const actorIsAdmin = me?.role === "admin";
  const canManageThis = !isMe && (actorIsOwner || (actorIsAdmin && !targetIsOwner));

  const [role, setRole] = useState(admin.role);
  const [busy, setBusy] = useState(false);

  const roleDisabled = !canEditRoles || isMe; // only owners can change roles, never on themselves

  async function handleRoleChange(next) {
    if (roleDisabled || next === role) return;
    const prev = role;
    setRole(next);
    setBusy(true);
    try {
      await onChangeRole(admin.id, next);
    } catch (e) {
      setRole(prev); // revert
      alert(e?.message || "Failed to change role.");
    } finally {
      setBusy(false);
    }
  }

  const statusBadge = (
    <span
      className={`rm-badge ${
        admin.status === "active" ? "ok" :
        admin.status === "invited" ? "info" : "warn"
      }`}
    >
      {admin.status}
    </span>
  );

  return (
    <tr>
      <td>#{index}</td>
      <td>{admin.name}</td>
      <td><a href={`mailto:${admin.email}`} className="rm-link">{admin.email}</a></td>

      <td>
        <select
          value={role}
          onChange={(e) => handleRoleChange(e.target.value)}
          disabled={roleDisabled || busy}
        >
          <option value="viewer">Viewer</option>
          <option value="admin">Admin</option>
          <option value="owner">Owner</option>
        </select>
      </td>

      <td>{statusBadge}</td>

      <td className="rm-actions-cell">
        {admin.status === "invited" ? (
          <>
            <button className="rm-btn" onClick={() => onResend(admin.id)} disabled={!canManageThis || busy}>
              Resend
            </button>
            <button className="rm-btn danger" onClick={() => onDeactivate(admin.id)} disabled={!canManageThis || busy}>
              Cancel
            </button>
          </>
        ) : admin.status === "active" ? (
          <button className="rm-btn danger" onClick={() => onDeactivate(admin.id)} disabled={!canManageThis || busy}>
            Deactivate
          </button>
        ) : (
          <button className="rm-btn" onClick={() => onActivate(admin.id)} disabled={!canManageThis || busy}>
            Activate
          </button>
        )}
      </td>
    </tr>
  );
}
