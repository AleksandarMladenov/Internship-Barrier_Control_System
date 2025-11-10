//  Base URL from .env
const BASE = import.meta.env.VITE_API_BASE_URL;

/**
 * Lightweight wrapper around fetch with:
 *  - automatic JSON body handling
 *  - credentials included
 *  - error extraction from FastAPI {detail, message}
 *  - optional timeout
 */
export async function http(path, options = {}, timeoutMs = 10000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const { body, ...rest } = options;
  const opts = {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    signal: controller.signal,
    ...rest,
  };

  if (body !== undefined) {
    opts.body = typeof body === "string" ? body : JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(`${BASE}${path}`, opts);
  } catch (err) {
    clearTimeout(timer);
    throw new Error(err.name === "AbortError" ? "Request timed out" : err.message);
  }
  clearTimeout(timer);

  if (!res.ok) {
    let msg = "";
    try {
      const data = await res.json();
      msg = data?.detail || data?.message || "";
    } catch {}
    throw new Error(msg || `${res.status} ${res.statusText}`);
  }

  return res.status === 204 ? null : res.json();
}

/* -------------------------------------------------------------------------- */
/*                              ADMIN  ENDPOINTS                              */
/* -------------------------------------------------------------------------- */

export const listAdmins = () => http("/admins");
export const inviteAdmin = (payload) =>
  http("/admins/invite", { method: "POST", body: payload });
export const resendInvite = (id) => http(`/admins/${id}/resend-invite`, { method: "POST" });
export const activateAdmin = (id) => http(`/admins/${id}/activate`, { method: "POST" });
export const deactivateAdmin = (id) => http(`/admins/${id}/deactivate`, { method: "POST" });
export const updateAdmin = (id, payload) =>
  http(`/admins/${id}`, { method: "PATCH", body: payload });

/* -------------------------------------------------------------------------- */
/*                          VEHICLE / ACCESS-LIST API                          */
/* -------------------------------------------------------------------------- */

export const fetchVehicles = ({ q = "", filter = "all", page = 1, pageSize = 20 }) => {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  params.set("page", String(page));
  params.set("page_size", String(pageSize));

  if (filter !== "all") params.set("filter", filter);

  // …and also send explicit flags most backends expect
  if (filter === "blacklisted") params.set("is_blacklisted", "true");
  if (filter === "whitelisted") params.set("is_blacklisted", "false");
  if (filter === "pending")     params.set("status", "pending");

  return http(`/vehicles?${params.toString()}`);
};


/** Blacklist vehicle */
export const blacklistVehicle = (vehicleId, { reason = null } = {}) =>
  http(`/admins/access/blacklist/${vehicleId}`, {
    method: "POST",
    body: reason ?? null,
  });

/** Delete a blacklisted vehicle */
export const deleteBlacklistedVehicle = (vehicleId, { reason = null } = {}) =>
  http(`/admins/access/blacklist/${vehicleId}`, {
    method: "DELETE",
    body: reason ?? null,
  });

  /** Whitelist vehicle  */
export const whitelistVehicle = (
  vehicleId,
  { reason = null, resumeSuspended = false } = {}
) => {

  const qs = new URLSearchParams();
  if (resumeSuspended) qs.set("resume_suspended", "true");

  return http(
    `/admins/access/whitelist/${vehicleId}${qs.toString() ? `?${qs}` : ""}`,
    {
      method: "POST",

      body: reason,
    }
  );
};

