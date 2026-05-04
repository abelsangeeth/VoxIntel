'use client';

export default function SearchPage() {
  return (
    <>
      <div className="topbar">
        <div style={{ fontWeight: 700, fontSize: 18 }}>Search</div>
      </div>
      <main className="main-content content-pb">
        <div style={{ maxWidth: 640, margin: '60px auto', textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 16 }}>✦</div>
          <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Ask VoxIntel Anything</div>
          <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 32 }}>
            Search across all your meetings using AI. Open a specific meeting to query its transcript directly.
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              placeholder="e.g. What were the action items from last week?"
              style={{
                flex: 1, padding: '12px 16px', border: '1px solid var(--border)', borderRadius: 8,
                fontSize: 14, fontFamily: 'inherit', outline: 'none',
                boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
              }}
            />
            <button className="btn-primary" style={{ padding: '12px 20px' }}>Search</button>
          </div>
          <div style={{ marginTop: 32, display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
            {['What were last week\'s action items?', 'Summarize the Q4 roadmap meeting', 'Who spoke most in product syncs?'].map(q => (
              <button key={q} className="btn-secondary" style={{ fontSize: 12 }}>{q}</button>
            ))}
          </div>
        </div>
      </main>
    </>
  );
}
