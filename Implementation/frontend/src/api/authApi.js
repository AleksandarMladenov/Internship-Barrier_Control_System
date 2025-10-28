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

export async function login(email, password) {
  await http("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function me() {
  return http("/auth/me");
}

export async function logout() {
  return http("/auth/logout", { method: "POST" });
}

export async function acceptInvite(token, password, name) {
  return http("/auth/accept-invite", {
    method: "POST",
    body: JSON.stringify({ token, password, name }),
  });
}
