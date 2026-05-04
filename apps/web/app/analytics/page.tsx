'use client';
import { useState } from 'react';

// Chart data
const freqBars = [3,5,2,7,4,6,8,3,5,9,4,6,7,2,5,8,6,4,7,3,6,9,5,7,4,8,6,3,7,5];
const weeklyHours = [8,12,9,15,11,14,18,10,13,16,12,17,14,9,16,19,15,11,18,12,16,21,13,18,11,19,14,10,17,13];
const participation = [
  { name: 'Abel', pct: 95 },
  { name: 'Sarah', pct: 87 },
  { name: 'John', pct: 73 },
  { name: 'Maria', pct: 68 },
];
const stacked = [
  { week: 'W1', done: 6, pending: 3 },
  { week: 'W2', done: 8, pending: 2 },
  { week: 'W3', done: 5, pending: 5 },
  { week: 'W4', done: 9, pending: 1 },
];
const sentimentPts = [55, 58, 52, 61, 65, 63, 70, 68, 72, 75, 71, 78, 80, 77, 83];

export default function Analytics() {
  const [range] = useState('Last 30 days');
  const maxFreq = Math.max(...freqBars);
  const maxHours = Math.max(...weeklyHours);
  const maxSentiment = Math.max(...sentimentPts);

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

        {/* Row 1 — Meeting Frequency + Hours */}
        <div className="charts-grid-top">
          <div className="card">
            <div className="card-header"><h3>Meeting Frequency</h3><span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Daily · 30 days</span></div>
            <div className="card-body">
              <div className="bar-chart">
                {freqBars.map((v, i) => (
                  <div key={i} className="bar" style={{ height: `${(v / maxFreq) * 100}%`, background: v >= 8 ? 'var(--accent)' : 'var(--primary)' }} title={`${v} meetings`} />
                ))}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
                <span>Oct 1</span><span>Oct 15</span><span>Oct 30</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h3>Hours Recorded per Week</h3><span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Area · 30 days</span></div>
            <div className="card-body">
              <div style={{ position: 'relative', height: 120 }}>
                <svg width="100%" height="120" viewBox={`0 0 ${weeklyHours.length * 20} 120`} preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.02" />
                    </linearGradient>
                  </defs>
                  <path
                    d={`M ${weeklyHours.map((v, i) => `${i * 20},${120 - (v / maxHours) * 110}`).join(' L ')} L ${(weeklyHours.length - 1) * 20},120 L 0,120 Z`}
                    fill="url(#areaGrad)"
                  />
                  <polyline
                    points={weeklyHours.map((v, i) => `${i * 20},${120 - (v / maxHours) * 110}`).join(' ')}
                    fill="none"
                    stroke="#0F766E"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: 11, color: 'var(--text-muted)' }}>
                <span>Oct 1</span><span>Oct 15</span><span>Oct 30</span>
              </div>
            </div>
          </div>
        </div>

        {/* Row 2 — Donut + Participation + Topics */}
        <div className="charts-grid-mid">
          <div className="card">
            <div className="card-header"><h3>Avg Meeting Duration</h3></div>
            <div className="card-body">
              <div className="donut-wrap">
                <svg width="100" height="100" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="var(--surface-2)" strokeWidth="12" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke="var(--primary)" strokeWidth="12"
                    strokeDasharray={`${0.75 * 251.2} ${251.2}`} strokeLinecap="round"
                    transform="rotate(-90 50 50)" />
                </svg>
                <div style={{ textAlign: 'center', marginTop: -90 }}>
                  <div className="donut-label">45m</div>
                  <div className="donut-sub">average</div>
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: 12 }}>
                {[['Min', '12m'], ['Avg', '45m'], ['Max', '2h 15m']].map(([l, v]) => (
                  <div key={l} style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--primary)' }}>{v}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{l}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h3>Participation Rate</h3></div>
            <div className="card-body">
              <div className="horiz-bars">
                {participation.map((p) => (
                  <div key={p.name} className="horiz-bar-row">
                    <div className="horiz-bar-label">
                      <span>{p.name}</span><span>{p.pct}%</span>
                    </div>
                    <div className="horiz-bar-track">
                      <div className="horiz-bar-fill" style={{ width: `${p.pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h3>Topics Distribution</h3></div>
            <div className="card-body">
              <div className="treemap">
                <div className="treemap-cell" style={{ gridRow: '1 / 3', background: 'var(--primary)' }}>Product</div>
                <div className="treemap-cell" style={{ background: '#0891B2' }}>Sales</div>
                <div className="treemap-cell" style={{ background: '#06B6D4' }}>Eng</div>
              </div>
              <div style={{ display: 'flex', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
                {['Product', 'Sales', 'Engineering', 'Finance'].map((t, i) => (
                  <span key={t} style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span style={{ width: 8, height: 8, borderRadius: 2, background: ['var(--primary)', '#0891B2', '#06B6D4', '#0E7490'][i], display: 'inline-block' }} />
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Row 3 — Stacked bars + Sentiment */}
        <div className="charts-grid-bot">
          <div className="card">
            <div className="card-header">
              <h3>Action Item Completion</h3>
              <div style={{ display: 'flex', gap: 12 }}>
                <span style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: 'var(--primary)', display: 'inline-block' }} /> Completed
                </span>
                <span style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: '#E5E7EB', display: 'inline-block' }} /> Pending
                </span>
              </div>
            </div>
            <div className="card-body">
              <div className="stacked-bars">
                {stacked.map((s) => {
                  const total = s.done + s.pending;
                  return (
                    <div key={s.week} className="stacked-bar-col">
                      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', width: '100%' }}>
                        <div style={{ height: `${(s.pending / total) * 80}px`, background: '#E5E7EB', borderRadius: '2px 2px 0 0', marginBottom: 2 }} />
                        <div style={{ height: `${(s.done / total) * 80}px`, background: 'var(--primary)', borderRadius: '2px 2px 0 0' }} />
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>{s.week}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h3>Meeting Sentiment</h3><span style={{ fontSize: 11, color: '#10B981', fontWeight: 600 }}>↑ Positive trend</span></div>
            <div className="card-body">
              <div style={{ position: 'relative', height: 120 }}>
                <svg width="100%" height="120" viewBox={`0 0 ${(sentimentPts.length - 1) * 30} 120`} preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="sentGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#0F766E" stopOpacity="0.2" />
                      <stop offset="100%" stopColor="#0F766E" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <path
                    d={`M ${sentimentPts.map((v, i) => `${i * 30},${120 - ((v - 40) / 60) * 100}`).join(' L ')} L ${(sentimentPts.length - 1) * 30},120 L 0,120 Z`}
                    fill="url(#sentGrad)"
                  />
                  <polyline
                    points={sentimentPts.map((v, i) => `${i * 30},${120 - ((v - 40) / 60) * 100}`).join(' ')}
                    fill="none" stroke="var(--primary)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                  />
                  {sentimentPts.map((v, i) => (
                    <circle key={i} cx={i * 30} cy={120 - ((v - 40) / 60) * 100} r="3" fill="var(--primary)" />
                  ))}
                </svg>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: 11, color: 'var(--text-muted)' }}>
                <span>Oct 1</span><span>Oct 15</span><span>Oct 30</span>
              </div>
            </div>
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
