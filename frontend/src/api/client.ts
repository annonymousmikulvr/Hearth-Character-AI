const BASE = "/api";

function friendlyError(status: number, detail: string): string {
  if (status === 0 || detail.includes("Failed to fetch")) {
    return "Cannot reach the Hearth backend. Is the API window running?";
  }
  if (status === 404) return detail || "Not found.";
  if (status >= 500) return detail || "Server error — check the backend console for details.";
  return detail || `Request failed (${status})`;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch {
    throw new Error(friendlyError(0, "Failed to fetch"));
  }
  if (!res.ok) {
    const body = await res.text();
    let detail = body;
    try {
      const j = JSON.parse(body);
      detail = typeof j.detail === "string" ? j.detail : j.message || body;
      if (Array.isArray(j.detail)) {
        detail = j.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join("; ");
      }
    } catch {
      /* keep raw */
    }
    throw new Error(friendlyError(res.status, String(detail)));
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
