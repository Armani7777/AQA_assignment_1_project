const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function api(path, options = {}) {
  const access = localStorage.getItem("access");
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
  if (access) headers.Authorization = `Bearer ${access}`;
  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await res.json() : null;
  if (!res.ok) throw data || { detail: "Request failed" };
  return data;
}
