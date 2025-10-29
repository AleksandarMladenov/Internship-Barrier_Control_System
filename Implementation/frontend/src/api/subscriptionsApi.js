// src/api/subscriptionsApi.js
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

async function jfetch(path, opts = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    let msg = "Request failed";
    try { const j = await res.json(); msg = j.detail || j.message || msg; } catch {}
    const err = new Error(msg); err.status = res.status; throw err;
  }
  if (res.status === 204) return null;
  const txt = await res.text();
  try { return txt ? JSON.parse(txt) : null; } catch { return txt; }
}

export function getSubscriptionPlans() {
  //  backend  returning plans with billing_period and stripe_price_id
  return jfetch(`/plans?type=subscription`);
}

export function startSubscriptionClaim(payload) {
  // { name, email, region_code, plate_text, plan_id }
  return jfetch(`/subscriptions/claim`, { method: "POST", body: payload });
}
