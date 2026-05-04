'use client';

import useSWR from 'swr';
import { swrFetcher, ragQuery, endSession, type Session, type Utterance, type Summary } from '@/lib/api';
import Link from 'next/link';
import { useState } from 'react';

const SPEAKER_COLORS = ['#0F766E', '#06B6D4', '#6366F1', '#EC4899', '#F59E0B', '#8B5CF6'];
const colorFor = (label: string) => SPEAKER_COLORS[Math.abs(label.charCodeAt(0)) % SPEAKER_COLORS.length];
const initials = (name: string) => name.slice(0, 2).toUpperCase();

function formatTime(s: number | undefined) {
  if (!s) return '0:00';
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

export default function MeetingDetails({ params }: { params: { id: string } }) {
  const { id } = params;

  const { data: session, error: sErr } = useSWR<Session>(`/v1/sessions/${id}`, swrFetcher);
  const { data: utterances, isLoading: uttLoading } = useSWR<Utterance[]>(
    `/v1/sessions/${id}/utterances?limit=200`, swrFetcher, { refreshInterval: session?.status === 'active' ? 5000 : 0 }
  );
  const { data: summary } = useSWR<Summary>(
    session?.status === 'ended' ? `/v1/sessions/${id}/summary` : null, swrFetcher
  );

  const [ragQ, setRagQ] = useState('');
  const [ragAnswer, setRagAnswer] = useState('');
  const [ragSources, setRagSources] = useState<{ text: string; score: number }[]>([]);
  const [ragLoading, setRagLoading] = useState(false);
  const [ending, setEnding] = useState(false);

  async function handleRag() {
    if (!ragQ.trim()) return;
    setRagLoading(true);
    try {
      const res = await ragQuery(id, ragQ);
      setRagAnswer(res.answer);
      setRagSources(res.sources ?? []);
    } catch (e: unknown) {
      setRagAnswer(e instanceof Error ? e.message : 'Error querying RAG');
    } finally { setRagLoading(false); }
  }

  async function handleEndSession() {
    setEnding(true);
    try { await endSession(id); } finally { setEnding(false); }
  }

  if (sErr) return <div style={{ padding: 32, color: '#EF4444' }}>Session not found.</div>;
  if (!session) return <div style={{ padding: 32, color: 'var(--text-muted)' }}>Loading session…</div>;

  // Deduplicate speakers
  const speakerMap: Record<string, string> = {};
  (utterances ?? []).forEach(u => {
    if (u.speaker_id && !speakerMap[u.speaker_id]) speakerMap[u.speaker_id] = u.speaker_id;
  });

  return (
    <>
      <div className="topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Link href="/" className="back-link">← Dashboard</Link>
          <div style={{ height: 20, width: 1, background: 'var(--border)' }} />
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>{session.title}</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
              {new Date(session.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
              {' · '}<span style={{ textTransform: 'capitalize' }}>{session.source}</span>
            </div>
          </div>
        </div>
        <div className="topbar-actions">
          <span className={`badge badge-${
            session.status === 'ended' ? 'green' : session.status === 'active' ? 'yellow' : session.status === 'processing' ? 'blue' : 'red'
          }`} style={{ textTransform: 'capitalize' }}>{session.status}</span>
          {session.status === 'active' && (
            <button className="btn-secondary" onClick={handleEndSession} disabled={ending} style={{ color: '#EF4444', borderColor: '#FECACA' }}>
              {ending ? 'Ending…' : '⏹ End Session'}
            </button>
          )}
          <Link href="/analytics" className="btn-secondary">📊 Analytics</Link>
        </div>
      </div>

      <main className="main-content content-pb">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 20, alignItems: 'start' }}>

          {/* Transcript */}
          <div className="card">
            <div className="card-header">
              <h3>Transcript {uttLoading && <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 400 }}>loading…</span>}</h3>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{utterances?.length ?? 0} utterances</span>
            </div>
            <div className="card-body" style={{ maxHeight: 580, overflowY: 'auto' }}>
              {!utterances || utterances.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)', fontSize: 13 }}>
                  {session.status === 'active' ? '🔴 Recording in progress…' : 'No transcript available yet.'}
                </div>
              ) : (
                utterances.map((u, i) => {
                  const spkLabel = u.speaker_id ?? 'Unknown';
                  return (
                    <div key={u.id} className="transcript-item">
                      <div className="transcript-avatar" style={{ background: colorFor(spkLabel) }}>
                        {initials(spkLabel)}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div className="transcript-meta">
                          <strong>{spkLabel}</strong> · {formatTime(u.start_time)}
                          {u.sentiment_label && (
                            <span style={{ marginLeft: 8, fontSize: 10, padding: '1px 6px', borderRadius: 4, background: u.sentiment_label === 'positive' ? '#D1FAE5' : u.sentiment_label === 'negative' ? '#FEE2E2' : '#F3F4F6', color: u.sentiment_label === 'positive' ? '#065F46' : u.sentiment_label === 'negative' ? '#991B1B' : '#6B7280' }}>
                              {u.sentiment_label}
                            </span>
                          )}
                        </div>
                        {i % 4 === 0 && u.text.length > 60 ? (
                          <div className="transcript-highlight">{u.text}</div>
                        ) : (
                          <div className="transcript-text">{u.text}</div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* AI Summary */}
            <div className="card">
              <div className="card-header"><h3>✦ AI Summary</h3></div>
              <div className="card-body">
                {!summary ? (
                  <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                    {session.status === 'ended' ? 'Generating summary…' : 'Summary available after session ends.'}
                  </div>
                ) : (
                  <>
                    <p style={{ fontSize: 13.5, lineHeight: 1.7, marginBottom: 12 }}>{summary.summary_text}</p>
                    {summary.top_intents?.length > 0 && (
                      <div className="topic-pills" style={{ marginTop: 8 }}>
                        {summary.top_intents.slice(0, 5).map((t: string) => (
                          <span key={t} className="topic-pill">{t}</span>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Action Items */}
            <div className="card">
              <div className="card-header">
                <h3>Action Items</h3>
                <span className="badge badge-blue">{summary?.action_items?.length ?? 0}</span>
              </div>
              <div className="card-body">
                {!summary?.action_items?.length ? (
                  <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>No action items extracted yet.</div>
                ) : (
                  summary.action_items.map((item: string, i: number) => (
                    <div key={i} className="action-item">
                      <div className="action-checkbox" />
                      <div className="action-text">{item}</div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* RAG Search */}
            <div className="card">
              <div className="card-header"><h3>✦ Ask about this Meeting</h3></div>
              <div className="card-body">
                <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                  <input
                    value={ragQ}
                    onChange={e => setRagQ(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleRag()}
                    placeholder="Ask a question…"
                    style={{ flex: 1, padding: '8px 12px', border: '1px solid var(--border)', borderRadius: 6, fontSize: 13, fontFamily: 'inherit', outline: 'none' }}
                  />
                  <button className="btn-primary" onClick={handleRag} disabled={ragLoading} style={{ padding: '8px 14px' }}>
                    {ragLoading ? '…' : '→'}
                  </button>
                </div>
                {ragAnswer && (
                  <div style={{ background: 'var(--surface-2)', borderRadius: 6, padding: '10px 12px', fontSize: 13, lineHeight: 1.6 }}>
                    <strong style={{ color: 'var(--primary)' }}>Answer: </strong>{ragAnswer}
                    {ragSources.length > 0 && (
                      <div style={{ marginTop: 8, fontSize: 11.5, color: 'var(--text-muted)' }}>
                        Sources: {ragSources.slice(0, 2).map((s, i) => <span key={i}>"{s.text.slice(0, 60)}…" </span>)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
