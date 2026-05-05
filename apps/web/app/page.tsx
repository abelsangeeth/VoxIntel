'use client';

import useSWR from 'swr';
import { swrFetcher, createSession, type Session } from '@/lib/api';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { useState } from 'react';

const statusBadge = (status: string) => {
  const map: Record<string, string> = {
    ended: 'badge-green', processing: 'badge-blue', active: 'badge-yellow', failed: 'badge-red',
  };
  return map[status] || 'badge-blue';
};

const avatarColors = ['#0F766E', '#06B6D4', '#6366F1', '#EC4899', '#F59E0B'];

export default function Dashboard() {
  const { user, logout } = useAuth();
  const { data: sessions, error, isLoading, mutate } = useSWR<Session[]>(
    '/v1/sessions',
    swrFetcher,
    { refreshInterval: 30000 }
  );
  const { data: health } = useSWR<{ status: string }>('/v1/health', swrFetcher, { refreshInterval: 60000 });

  const [creating, setCreating] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [createError, setCreateError] = useState('');

  async function handleCreate() {
    if (!newTitle.trim()) return;
    setCreating(true);
    setCreateError('');
    try {
      await createSession({ title: newTitle, source: 'manual' });
      setNewTitle(''); setShowNew(false);
      mutate();
    } catch (e: unknown) {
      setCreateError(e instanceof Error ? e.message : 'Failed to create session');
    } finally { setCreating(false); }
  }

  const list = sessions ?? [];
  const ended = list.filter(s => s.status === 'ended').length;
  const active = list.filter(s => s.status === 'active').length;
  const processing = list.filter(s => s.status === 'processing').length;

  return (
    <>
      <div className="topbar">
        <div>
          <div className="topbar-greeting">
            Good morning, <span>{user?.username ?? 'Abel'}</span> 👋
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: health?.status === 'ok' ? '#10B981' : '#EF4444', display: 'inline-block' }} />
            API {health?.status === 'ok' ? 'Online' : error ? 'Offline' : '…'}
          </div>
        </div>
        <div className="topbar-actions">
          <button className="btn-secondary" onClick={logout}>⇥ Logout</button>
          <button className="btn-primary" onClick={() => setShowNew(true)}>＋ New Meeting</button>
        </div>
      </div>

      {/* New Meeting Modal */}
      {showNew && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 999, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="card" style={{ width: 420, padding: 24 }}>
            <h3 style={{ marginBottom: 16, fontSize: 16 }}>Create New Meeting Session</h3>
            <input
              value={newTitle}
              onChange={e => setNewTitle(e.target.value)}
              placeholder="Meeting title…"
              style={{ width: '100%', padding: '9px 12px', border: '1px solid var(--border)', borderRadius: 6, fontSize: 14, fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box', marginBottom: 16 }}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
              autoFocus
            />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn-secondary" onClick={() => { setShowNew(false); setCreateError(''); }}>Cancel</button>
              <button className="btn-primary" onClick={handleCreate} disabled={creating}>{creating ? 'Creating…' : 'Create'}</button>
            </div>
            {createError && <div style={{ color: '#EF4444', fontSize: 13, marginTop: 10, textAlign: 'right' }}>{createError}</div>}
          </div>
        </div>
      )}

      <main className="main-content content-pb">
        {/* Stats */}
        <div className="stats-grid">
          {[
            { label: 'Total Sessions', value: String(list.length), trend: '', dir: 'neutral', sub: 'all time' },
            { label: 'Completed', value: String(ended), trend: '', dir: 'up', sub: 'processed' },
            { label: 'Active Now', value: String(active), trend: '', dir: active > 0 ? 'up' : 'neutral', sub: 'recording' },
            { label: 'Processing', value: String(processing), trend: '', dir: 'neutral', sub: 'in queue' },
          ].map((s) => (
            <div key={s.label} className="stat-card">
              <div className="stat-label">{s.label}</div>
              <div className="stat-value">{isLoading ? '—' : s.value}</div>
              <div className={`stat-trend ${s.dir}`}>{s.sub}</div>
            </div>
          ))}
        </div>

        {/* Meetings Table */}
        <div className="card">
          <div className="card-header">
            <h3>Recent Sessions</h3>
            <Link href="/meetings" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px' }}>View All →</Link>
          </div>
          {isLoading ? (
            <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>Loading sessions…</div>
          ) : error ? (
            <div style={{ padding: 32, textAlign: 'center', color: '#EF4444', fontSize: 13 }}>
              Could not load sessions. Check API connectivity.
            </div>
          ) : list.length === 0 ? (
            <div style={{ padding: 48, textAlign: 'center' }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>🎙️</div>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>No sessions yet</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16 }}>Create your first session to get started.</div>
              <button className="btn-primary" onClick={() => setShowNew(true)}>＋ New Meeting</button>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Meeting Title</th>
                    <th>Source</th>
                    <th>Created</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {[...list].reverse().map((s, idx) => (
                    <tr key={s.id}>
                      <td style={{ fontWeight: 500 }}>{s.title}</td>
                      <td>
                        <span className="badge badge-blue" style={{ textTransform: 'capitalize' }}>{s.source}</span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
                        {new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td><span className={`badge ${statusBadge(s.status)}`} style={{ textTransform: 'capitalize' }}>{s.status}</span></td>
                      <td>
                        <Link href={`/meetings/${s.id}`} style={{ color: 'var(--primary)', fontSize: 12, textDecoration: 'none', fontWeight: 500 }}>View →</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* RAG Bar */}
      <RagBar />
    </>
  );
}

function RagBar() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSearch() {
    if (!query.trim()) return;
    setLoading(true);
    setAnswer('Global search works per-meeting. Open a meeting and ask questions there.');
    setLoading(false);
  }

  return (
    <div className="rag-bar-wrap">
      {answer && (
        <div style={{
          background: '#fff', border: '1px solid var(--border)', borderRadius: 8,
          padding: '12px 16px', marginBottom: 10, fontSize: 13, color: 'var(--text-primary)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        }}>
          <strong style={{ color: 'var(--primary)' }}>✦ VoxIntel:</strong> {answer}
          <button onClick={() => setAnswer('')} style={{ float: 'right', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 13 }}>✕</button>
        </div>
      )}
      <div className="rag-bar">
        <span className="rag-bar-icon">✦</span>
        <input
          type="text"
          placeholder="Ask anything about your meetings…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
        />
        <button className="rag-bar-btn" onClick={handleSearch} disabled={loading}>
          {loading ? '…' : 'Search'}
        </button>
      </div>
    </div>
  );
}
