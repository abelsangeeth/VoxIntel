'use client';
import { useState } from 'react';
import useSWR from 'swr';
import { swrFetcher, type Session } from '@/lib/api';

function EmptyChart({ label }: { label: string }) {
  return (
    <div style={{ height: 120, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
      <div style={{ fontSize: 28, opacity: 0.2 }}>📊</div>
      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{label}</div>
    </div>
  );
}

export default function Analytics() {
  const [range] = useState('Last 30 days');

  const { data: sessions, isLoading } = useSWR<Session[]>('/v1/sessions?limit=100', swrFetcher);

  const totalSessions = sessions?.length ?? 0;
  const completed = sessions?.filter(s => s.status === 'ended').length ?? 0;
  const active = sessions?.filter(s => s.status === 'active').length ?? 0;
  const processing = sessions?.filter(s => s.status === 'processing').length ?? 0;

  // Build daily frequency over last 30 days from real sessions
  const freqMap: Record<string, number> = {};
  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    freqMap[d.toISOString().slice(0, 10)] = 0;
  }
  sessions?.forEach(s => {
    const day = s.created_at.slice(0, 10);
    if (day in freqMap) freqMap[day]++;
  });
  const freqBars = Object.values(freqMap);
  const maxFreq = Math.max(...freqBars, 1);
  const hasData = totalSessions > 0;

  const startLabel = Object.keys(freqMap)[0]?.slice(5).replace('-', '/') ?? '';
  const midLabel = Object.keys(freqMap)[14]?.slice(5).replace('-', '/') ?? '';
  const endLabel = Object.keys(freqMap)[29]?.slice(5).replace('-', '/') ?? '';

  return (
    <>
      <div className="topbar">
        <div>
          <div style={{ fontWeight: 700, fontSize: 18, letterSpacing: '-0.01em' }}>Analytics</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>Meeting insights and performance metrics</div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-secondary">⬇ Export Report</button>
          <button className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            📅 {range} ▾
          </button>
        </div>
      </div>

      <main className="main-content content-pb">

        {/* Summary stat cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 20 }}>
          {[
            { label: 'Total Sessions', value: isLoading ? '…' : totalSessions, sub: 'all time' },
            { label: 'Completed', value: isLoading ? '…' : completed, sub: 'processed', color: '#10B981' },
            { label: 'Active Now', value: isLoading ? '…' : active, sub: 'recording' },
            { label: 'Processing', value: isLoading ? '…' : processing, sub: 'in queue' },
          ].map(card => (
            <div key={card.label} className="card" style={{ padding: '20px 24px' }}>
              <div style={{ fontSize: 28, fontWeight: 700, color: card.color ?? 'var(--text-primary)' }}>{card.value}</div>
              <div style={{ fontSize: 13, fontWeight: 600, marginTop: 4 }}>{card.label}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{card.sub}</div>
            </div>
          ))}
        </div>

        {/* Row 1 — Meeting Frequency */}
        <div className="charts-grid-top">
          <div className="card">
            <div className="card-header"><h3>Meeting Frequency</h3><span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Daily · 30 days</span></div>
            <div className="card-body">
              {!hasData ? <EmptyChart label="No sessions yet — create your first meeting!" /> : (
                <>
                  <div className="bar-chart">
                    {freqBars.map((v, i) => (
                      <div key={i} className="bar" style={{ height: `${(v / maxFreq) * 100}%`, background: v >= 3 ? 'var(--accent)' : 'var(--primary)' }} title={`${v} meetings`} />
                    ))}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
                    <span>{startLabel}</span><span>{midLabel}</span><span>{endLabel}</span>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h3>Session Status Breakdown</h3><span style={{ fontSize: 12, color: 'var(--text-muted)' }}>All time</span></div>
            <div className="card-body">
              {!hasData ? <EmptyChart label="No sessions yet" /> : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {[
                    { label: 'Completed', count: completed, color: '#10B981' },
                    { label: 'Processing', count: processing, color: '#06B6D4' },
                    { label: 'Active', count: active, color: '#F59E0B' },
                    { label: 'Failed', count: sessions?.filter(s => s.status === 'failed').length ?? 0, color: '#EF4444' },
                  ].map(row => (
                    <div key={row.label} className="horiz-bar-row">
                      <div className="horiz-bar-label">
                        <span>{row.label}</span><span>{row.count}</span>
                      </div>
                      <div className="horiz-bar-track">
                        <div className="horiz-bar-fill" style={{ width: `${totalSessions ? (row.count / totalSessions) * 100 : 0}%`, background: row.color }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Row 2 — Recent activity */}
        <div className="card" style={{ marginTop: 20 }}>
          <div className="card-header"><h3>Recent Sessions</h3><span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{totalSessions} total</span></div>
          <div className="card-body">
            {isLoading ? (
              <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading…</div>
            ) : !hasData ? (
              <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)', fontSize: 13 }}>
                No sessions yet. <a href="/" style={{ color: 'var(--primary)' }}>Create your first meeting →</a>
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    {['Title', 'Source', 'Status', 'Created'].map(h => (
                      <th key={h} style={{ textAlign: 'left', padding: '6px 12px 10px', fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(sessions ?? []).slice(0, 8).map(s => (
                    <tr key={s.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '10px 12px', fontWeight: 500 }}>{s.title}</td>
                      <td style={{ padding: '10px 12px', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{s.source}</td>
                      <td style={{ padding: '10px 12px' }}>
                        <span className={`badge badge-${s.status === 'ended' ? 'green' : s.status === 'active' ? 'yellow' : s.status === 'processing' ? 'blue' : 'red'}`} style={{ textTransform: 'capitalize' }}>
                          {s.status}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>
                        {new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

      </main>

      <div className="rag-bar-wrap">
        <div className="rag-bar">
          <span className="rag-bar-icon">✦</span>
          <input type="text" placeholder="Ask anything about your meeting analytics..." />
          <button className="rag-bar-btn">Search</button>
        </div>
      </div>
    </>
  );
}
