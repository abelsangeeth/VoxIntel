/**
 * VoxIntel API Client
 * Wraps all calls to the production backend at voxintel-production.up.railway.app
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://voxintel-production.up.railway.app';

// ── Token storage (localStorage for SPA) ──────────────────────────────────────
export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('voxintel_token');
};

export const setToken = (token: string) => {
  localStorage.setItem('voxintel_token', token);
};

export const clearToken = () => {
  localStorage.removeItem('voxintel_token');
};

// ── Base fetch wrapper ────────────────────────────────────────────────────────
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API error');
  }
  // 204 No Content
  if (res.status === 204) return {} as T;
  return res.json();
}

// ── SWR fetcher (used by useSWR hooks) ────────────────────────────────────────
export const swrFetcher = (url: string) => apiFetch(url);

// ── Auth ──────────────────────────────────────────────────────────────────────
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${BASE_URL}/v1/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed');
  }
  return res.json();
}

// ── Sessions / Meetings ───────────────────────────────────────────────────────
export interface Session {
  id: string;
  title: string;
  source: string;
  external_id?: string;
  status: 'active' | 'processing' | 'ended' | 'failed';
  created_at: string;
  ended_at?: string;
  metadata_?: Record<string, unknown>;
}

export interface SessionCreate {
  title: string;
  source?: string;
  external_id?: string;
  metadata?: Record<string, unknown>;
}

export const createSession = (data: SessionCreate) =>
  apiFetch<Session>('/v1/sessions', { method: 'POST', body: JSON.stringify(data) });

export const getSession = (id: string) =>
  apiFetch<Session>(`/v1/sessions/${id}`);

export const endSession = (id: string) =>
  apiFetch(`/v1/sessions/${id}/end`, { method: 'POST' });

// ── Transcript ────────────────────────────────────────────────────────────────
export interface Utterance {
  id: string;
  conversation_id: string;
  sequence_number: number;
  speaker_id?: string;
  text: string;
  start_time?: number;
  end_time?: number;
  sentiment_label?: string;
  intent?: string;
}

export const getUtterances = (sessionId: string, offset = 0, limit = 100) =>
  apiFetch<Utterance[]>(`/v1/sessions/${sessionId}/utterances?offset=${offset}&limit=${limit}`);

// ── Summary ───────────────────────────────────────────────────────────────────
export interface Summary {
  id: string;
  conversation_id: string;
  summary_text: string;
  action_items: string[];
  top_intents: string[];
  sentiment_arc: number[];
  webhook_sent: boolean;
  created_at: string;
}

export const getSummary = (sessionId: string) =>
  apiFetch<Summary>(`/v1/sessions/${sessionId}/summary`);

// ── RAG Query ─────────────────────────────────────────────────────────────────
export interface RagResponse {
  conversation_id: string;
  answer: string;
  sources: { text: string; score: number }[];
}

export const ragQuery = (sessionId: string, question: string) =>
  apiFetch<RagResponse>(`/v1/sessions/${sessionId}/rag?question=${encodeURIComponent(question)}`, {
    method: 'POST',
  });

// ── Global RAG (no session) — search across all meetings ─────────────────────
export const globalRagQuery = async (question: string): Promise<RagResponse> => {
  // Falls back gracefully if no session context
  return {
    conversation_id: 'global',
    answer: 'Global search is available per-meeting via the meeting detail page.',
    sources: [],
  };
};

// ── Health ────────────────────────────────────────────────────────────────────
export const getHealth = () =>
  apiFetch<{ status: string }>('/v1/health');
