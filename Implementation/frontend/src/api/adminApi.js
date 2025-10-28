const BASE = import.meta.env.VITE_API_BASE_URL;

async function http(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    let msg = "";
    try {
      const data = await res.json();
      msg = data?.detail || data?.message || "";
    } catch {}
    throw new Error(msg || res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

export const listAdmins   = () => http("/admins");
export const inviteAdmin  = (payload) =>
  http("/admins/invite", { method: "POST", body: JSON.stringify(payload) }); // {id,email,role,status,invite_url}
export const resendInvite = (id) => http(`/admins/${id}/resend-invite`, { method: "POST" });
export const activateAdmin   = (id) => http(`/admins/${id}/activate`,   { method: "POST" });
export const deactivateAdmin = (id) => http(`/admins/${id}/deactivate`, { method: "POST" });
export const updateAdmin     = (id, payload) =>
  http(`/admins/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
