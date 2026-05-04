'use client';

import useSWR from 'swr';
import { swrFetcher, type Session, type Utterance } from '@/lib/api';
import Link from 'next/link';
import { useState } from 'react';

export default function TranscriptsPage() {
  const { data: sessions } = useSWR<Session[]>('/v1/sessions', swrFetcher);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: utterances, isLoading } = useSWR<Utterance[]>(
    selectedId ? `/v1/sessions/${selectedId}/utterances?limit=500` : null, swrFetcher
  );
  const [search, setSearch] = useState('');

  const endedSessions = (sessions ?? []).filter(s => s.status === 'ended' || s.status === 'processing');
  const filtered = (utterances ?? []).filter(u => !search || u.text.toLowerCase().includes(search.toLowerCase()));

  function formatTime(s: number | undefined) {
    if (!s) return '0:00';
    return `${Math.floor(s / 60)}:${Math.floor(s % 60).toString().padStart(2, '0')}`;
  }

  return (
    <>
      <div className="topbar">
        <div>
          <div style={{ fontWeight: 700, fontSize: 18 }}>Transcripts</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>Full meeting transcripts with speaker labels</div>
        </div>
      </div>
      <main className="main-content content-pb">
        <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 16, alignItems: 'start' }}>
          {/* Session list */}
          <div className="card">
            <div className="card-header"><h3>Sessions</h3></div>
            <div style={{ maxHeight: 600, overflowY: 'auto' }}>
              {endedSessions.length === 0 ? (
                <div style={{ padding: 16, fontSize: 13, color: 'var(--text-muted)' }}>No sessions with transcripts yet.</div>
              ) : endedSessions.map(s => (
                <button key={s.id} onClick={() => setSelectedId(s.id)} style={{
                  width: '100%', textAlign: 'left', padding: '10px 14px',
                  background: selectedId === s.id ? 'var(--primary-light)' : 'transparent',
                  borderLeft: `3px solid ${selectedId === s.id ? 'var(--primary)' : 'transparent'}`,
                  border: 'none', borderBottom: '1px solid var(--border)',
                  cursor: 'pointer', fontFamily: 'inherit',
                }}>
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 3, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {s.title}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {new Date(s.created_at).toLocaleDateString()}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Transcript viewer */}
          <div className="card">
            {!selectedId ? (
              <div style={{ padding: 60, textAlign: 'center', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: 32, marginBottom: 12 }}>≡</div>
                <div>Select a session to view its transcript</div>
              </div>
            ) : (
              <>
                <div className="card-header">
                  <h3>Transcript</h3>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <input
                      value={search}
                      onChange={e => setSearch(e.target.value)}
                      placeholder="Search transcript…"
                      style={{ padding: '5px 10px', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12, fontFamily: 'inherit', outline: 'none', width: 180 }}
                    />
                    <Link href={`/meetings/${selectedId}`} className="btn-secondary" style={{ fontSize: 12 }}>Full View →</Link>
                  </div>
                </div>
                <div style={{ maxHeight: 580, overflowY: 'auto', padding: '0 20px' }}>
                  {isLoading ? (
                    <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>Loading transcript…</div>
                  ) : filtered.length === 0 ? (
                    <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
                      {search ? 'No matches found.' : 'No utterances in this session.'}
                    </div>
                  ) : filtered.map(u => (
                    <div key={u.id} className="transcript-item">
                      <div className="transcript-avatar" style={{ background: '#0F766E', fontSize: 10 }}>
                        {(u.speaker_id ?? 'UK').slice(0, 2).toUpperCase()}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div className="transcript-meta">
                          <strong>{u.speaker_id ?? 'Unknown'}</strong> · {formatTime(u.start_time)}
                          {u.sentiment_label && <span style={{ marginLeft: 6, fontSize: 10, color: u.sentiment_label === 'positive' ? '#10B981' : u.sentiment_label === 'negative' ? '#EF4444' : 'var(--text-muted)' }}>● {u.sentiment_label}</span>}
                        </div>
                        <div className="transcript-text">{u.text}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
