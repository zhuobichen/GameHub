const BASE = "http://localhost:8000/api/v1"

function token(): string | null {
  return localStorage.getItem("token")
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  }
  const t = token()
  if (t) headers["Authorization"] = `Bearer ${t}`

  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || "Request failed")
  }
  return res.json()
}

export const apiGet = <T>(path: string) => api<T>(path)

export const apiPost = <T>(path: string, body: any) =>
  api<T>(path, { method: "POST", body: JSON.stringify(body) })

export const apiPut = <T>(path: string, body: any) =>
  api<T>(path, { method: "PUT", body: JSON.stringify(body) })

export const apiDelete = (path: string) =>
  api(path, { method: "DELETE" })
