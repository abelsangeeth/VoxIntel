'use client';

import useSWR from 'swr';
import { swrFetcher, type Session } from '@/lib/api';
import Link from 'next/link';

const statusBadge = (s: string) => ({
  ended: 'badge-green', processing: 'badge-blue', active: 'badge-yellow', failed: 'badge-red'
}[s] ?? 'badge-blue');

export default function MeetingsPage() {
  const { data: sessions, isLoading, error } = useSWR<Session[]>('/v1/sessions', swrFetcher, { refreshInterval: 15000 });
  const list = [...(sessions ?? [])].reverse();

  return (
    <>
      <div className="topbar">
        <div>
          <div style={{ fontWeight: 700, fontSize: 18 }}>All Meetings</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{list.length} sessions total</div>
        </div>
        <div className="topbar-actions">
          <Link href="/" className="btn-secondary">← Dashboard</Link>
        </div>
      </div>
      <main className="main-content content-pb">
        <div className="card">
          <div className="card-header"><h3>All Sessions</h3></div>
          {isLoading ? (
            <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>Loading…</div>
          ) : error ? (
            <div style={{ padding: 32, textAlign: 'center', color: '#EF4444' }}>Failed to load sessions.</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr>
                  <th>Title</th><th>Source</th><th>Created</th><th>Ended</th><th>Status</th><th></th>
                </tr></thead>
                <tbody>
                  {list.map(s => (
                    <tr key={s.id}>
                      <td style={{ fontWeight: 500, maxWidth: 280 }}>{s.title}</td>
                      <td><span className="badge badge-blue" style={{ textTransform: 'capitalize' }}>{s.source}</span></td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{new Date(s.created_at).toLocaleDateString()}</td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{s.ended_at ? new Date(s.ended_at).toLocaleDateString() : '—'}</td>
                      <td><span className={`badge ${statusBadge(s.status)}`} style={{ textTransform: 'capitalize' }}>{s.status}</span></td>
                      <td><Link href={`/meetings/${s.id}`} style={{ color: 'var(--primary)', fontSize: 12, textDecoration: 'none', fontWeight: 600 }}>Open →</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </>
  );
}
