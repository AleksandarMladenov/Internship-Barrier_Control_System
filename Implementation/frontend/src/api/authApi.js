const BASE = import.meta.env.VITE_API_BASE_URL;

async function http(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    credentials: "include", // ✅ sends cookie to FastAPI
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
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
