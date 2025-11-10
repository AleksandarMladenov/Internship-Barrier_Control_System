const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

async function jfetch(path, opts = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });

  if (!res.ok) {
    let msg = "Request failed";
    try {
      const j = await res.json();
      msg = j.detail || j.message || msg;
    } catch {}
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }

  if (res.status === 204) return null;
  const txt = await res.text();
  try { return txt ? JSON.parse(txt) : null; } catch { return txt; }
}

// plans list for subscriptions
export function listSubscriptionPlans() {
  return jfetch(`/plans?type=subscription`);
}

// create subscription (admin-side)
export function createSubscription(payload) {

  return jfetch(`/subscriptions`, { method: "POST", body: payload });
}


export function createSubscriptionCheckout(subscriptionId) {
  return jfetch(`/subscriptions/${subscriptionId}/checkout`, { method: "POST" });
}

// revive last canceled sub for a vehicle (same sub id) and email checkout link to driver
export function reviveLastCanceledAndSendLink(vehicleId, body) {

  return jfetch(`/subscriptions/vehicles/${vehicleId}/revive-last-canceled`, {
    method: "POST",
    body,
  });
}

