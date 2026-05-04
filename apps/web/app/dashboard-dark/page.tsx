import Link from 'next/link';

const meetings = [
  { name: 'Weekly Product Sync', date: 'Oct 24, 2023', duration: '45m 12s', participants: ['AB', 'SR', 'JK'], colors: ['#0F766E', '#06B6D4', '#6366F1'], status: 'Processed', badge: 'badge-green' },
  { name: 'Design System Architecture', date: 'Oct 23, 2023', duration: '1h 15m', participants: ['AB', 'MR'], colors: ['#0F766E', '#8B5CF6'], status: 'Processing', badge: 'badge-blue' },
  { name: 'Q4 Roadmap Planning', date: 'Oct 22, 2023', duration: '2h 15m', participants: ['AB', 'SR', 'JK', 'MR'], colors: ['#0F766E', '#06B6D4', '#6366F1', '#EC4899'], status: 'Processed', badge: 'badge-green' },
  { name: 'Investor Pitch Prep', date: 'Oct 22, 2023', duration: '18m 4s', participants: ['AB'], colors: ['#0F766E'], status: 'Failed', badge: 'badge-red' },
];

const stats = [
  { label: 'Total Meetings', value: '48', trend: '+12%', dir: 'up', sub: 'this month' },
  { label: 'Hours Recorded', value: '124h', trend: '+8%', dir: 'up', sub: 'last month' },
  { label: 'Action Items', value: '23', trend: '-5%', dir: 'down', sub: 'pending total' },
  { label: 'Team Members', value: '6', trend: '', dir: 'neutral', sub: 'active now' },
];

export default function DarkDashboard() {
  return (
    <div className="dark" style={{ minHeight: '100vh', background: 'var(--dark-bg)' }}>
      {/* Topbar */}
      <div className="topbar" style={{ background: 'rgba(13,17,23,0.9)', borderBottomColor: 'var(--dark-border)' }}>
        <div>
          <div className="topbar-greeting" style={{ color: 'var(--dark-text-primary)' }}>
            Good morning, <span style={{ color: 'var(--dark-text-secondary)' }}>Abel</span> 👋
          </div>
        </div>
        <div className="topbar-actions">
          <button className="btn-secondary" style={{ borderColor: '#30363D', color: '#8B949E' }}>⛭ Filter</button>
          <Link href="#" className="btn-primary">＋ New Meeting</Link>
        </div>
      </div>

      <main className="main-content content-pb">
        {/* Stats */}
        <div className="stats-grid">
          {stats.map((s) => (
            <div key={s.label} className="stat-card" style={{ background: '#161B22', borderColor: '#30363D' }}>
              <div className="stat-label" style={{ color: '#6E7681' }}>{s.label}</div>
              <div className="stat-value" style={{ color: '#06B6D4' }}>{s.value}</div>
              <div className={`stat-trend ${s.dir}`}>
                {s.dir === 'up' && '↑'}{s.dir === 'down' && '↓'} {s.trend}{' '}
                <span style={{ fontWeight: 400, color: '#6E7681' }}>{s.sub}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Meetings */}
        <div className="card" style={{ background: '#161B22', borderColor: '#30363D' }}>
          <div className="card-header" style={{ borderBottomColor: '#30363D' }}>
            <h3 style={{ color: '#E6EDF3' }}>Recent Meetings</h3>
            <Link href="/meetings" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', borderColor: '#30363D', color: '#8B949E' }}>View All →</Link>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {['Meeting Name', 'Date', 'Duration', 'Participants', 'Status'].map(h => (
                    <th key={h} style={{ color: '#6E7681', borderBottomColor: '#30363D' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {meetings.map((m, idx) => (
                  <tr key={m.name} style={{ borderBottomColor: '#21262D', background: idx % 2 === 1 ? '#1C2128' : 'transparent' }}>
                    <td style={{ color: '#E6EDF3', fontWeight: 500 }}>{m.name}</td>
                    <td style={{ color: '#8B949E' }}>{m.date}</td>
                    <td style={{ color: '#8B949E', fontVariantNumeric: 'tabular-nums' }}>{m.duration}</td>
                    <td>
                      <div className="avatar-group">
                        {m.participants.map((p, i) => (
                          <div key={i} className="avatar" style={{ background: m.colors[i], borderColor: '#161B22' }}>{p}</div>
                        ))}
                      </div>
                    </td>
                    <td><span className={`badge ${m.badge}`}>{m.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Glassmorphism RAG Bar */}
      <div className="rag-bar-wrap">
        <div className="rag-bar" style={{ background: 'rgba(22,27,34,0.85)', backdropFilter: 'blur(12px)', borderColor: '#30363D', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}>
          <span className="rag-bar-icon">✦</span>
          <input type="text" placeholder="Ask anything about your meetings..." style={{ color: '#E6EDF3' }} />
          <button className="rag-bar-btn">Search</button>
        </div>
      </div>
    </div>
  );
}
