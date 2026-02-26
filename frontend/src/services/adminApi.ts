import type {
  AdminStats,
  AdminHealth,
  AdminFeedbackLog,
  AdminExperimentDetail,
} from './types';

const API_BASE = '/api/v1';

// Token stored in memory only — cleared on page refresh (intentional for demo security)
let _token: string | null = null;

export function setToken(token: string) {
  _token = token;
  window.dispatchEvent(new Event('admin-auth-change'));
}

export function clearToken() {
  _token = null;
  window.dispatchEvent(new Event('admin-auth-change'));
}

export function isLoggedIn(): boolean {
  return _token !== null;
}

async function adminFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(_token ? { Authorization: `Bearer ${_token}` } : {}),
    },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { error?: string }).error ?? `${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// Log in and store the token. Throws on bad credentials.
export async function adminLogin(username: string, password: string): Promise<void> {
  const data = await adminFetch<{ status: string; access_token: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  setToken(data.access_token);
}

// Verify the stored token is still valid (useful after page re-login).
export async function verifyToken(): Promise<{ username: string }> {
  return adminFetch<{ status: string; username: string }>('/auth/verify');
}

export async function getAdminStats(): Promise<AdminStats> {
  return adminFetch<AdminStats>('/admin/stats');
}

export async function getAdminHealth(): Promise<AdminHealth> {
  return adminFetch<AdminHealth>('/admin/health');
}

export async function getAdminFeedback(
  limit = 50,
  feedbackType?: string,
): Promise<AdminFeedbackLog> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (feedbackType) params.set('feedback_type', feedbackType);
  return adminFetch<AdminFeedbackLog>(`/admin/feedback?${params}`);
}

export async function getExperimentDetail(name: string): Promise<AdminExperimentDetail> {
  return adminFetch<AdminExperimentDetail>(`/admin/experiments/${encodeURIComponent(name)}`);
}

// Public endpoint — no auth required
export async function listExperiments(): Promise<{ name: string; status: string }[]> {
  const data = await fetch(`${API_BASE}/experiments`);
  if (!data.ok) return [];
  const json = (await data.json()) as { experiments?: { name: string; status: string }[] };
  return json.experiments ?? [];
}
