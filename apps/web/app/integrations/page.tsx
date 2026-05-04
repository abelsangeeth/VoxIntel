'use client';

export default function IntegrationsPage() {
  const endpoints = [
    {
      name: 'Zoom Webhook',
      icon: '📹',
      url: 'https://voxintel-production.up.railway.app/v1/integrations/zoom/webhook',
      method: 'POST',
      desc: 'Set this URL in your Zoom App → Event Subscriptions. Supports: meeting.started, meeting.ended',
      steps: [
        'Go to marketplace.zoom.us → My Apps',
        'Create or edit your Zoom App',
        'Under "Feature" → "Event Subscriptions" → "Add new event subscription"',
        'Set Event notification URL to the webhook URL above',
        'Subscribe to: meeting.started, meeting.ended',
        'Save and validate',
      ],
    },
    {
      name: 'Slack Events API',
      icon: '💬',
      url: 'https://voxintel-production.up.railway.app/v1/integrations/slack/webhook',
      method: 'POST',
      desc: 'Set this URL in your Slack App → Event Subscriptions. Handles: url_verification, app_mention',
      steps: [
        'Go to api.slack.com/apps → Your App',
        'Under "Event Subscriptions" → Enable Events',
        'Set "Request URL" to the webhook URL above',
        'Subscribe to bot events: app_mention',
        'Add OAuth scope: chat:write',
        'Reinstall app to workspace',
      ],
    },
  ];

  return (
    <>
      <div className="topbar">
        <div>
          <div style={{ fontWeight: 700, fontSize: 18 }}>Integrations</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>Connect Zoom and Slack to auto-capture meetings</div>
        </div>
      </div>
      <main className="main-content content-pb">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 760 }}>
          {endpoints.map(int => (
            <div key={int.name} className="card">
              <div className="card-header">
                <h3>{int.icon} {int.name}</h3>
                <span className="badge badge-green">Active</span>
              </div>
              <div className="card-body">
                <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', marginBottom: 16 }}>{int.desc}</p>

                {/* Endpoint */}
                <div style={{ marginBottom: 20 }}>
                  <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>Webhook URL</div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span style={{ background: 'var(--primary)', color: '#fff', padding: '3px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700, fontFamily: 'monospace', flexShrink: 0 }}>
                      {int.method}
                    </span>
                    <div style={{ flex: 1, background: 'var(--surface-2)', borderRadius: 6, padding: '8px 12px', fontSize: 12.5, fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {int.url}
                    </div>
                    <button className="btn-secondary" style={{ fontSize: 12, flexShrink: 0 }} onClick={() => navigator.clipboard.writeText(int.url)}>
                      ⎘ Copy
                    </button>
                  </div>
                </div>

                {/* Setup Steps */}
                <div>
                  <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>Setup Steps</div>
                  <ol style={{ paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {int.steps.map((step, i) => (
                      <li key={i} style={{ fontSize: 13.5, color: 'var(--text-primary)', lineHeight: 1.6 }}>{step}</li>
                    ))}
                  </ol>
                </div>
              </div>
            </div>
          ))}

          {/* API Docs link */}
          <div className="card" style={{ padding: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>📖 Full API Reference</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Interactive Swagger docs with all endpoints</div>
            </div>
            <a href="https://voxintel-production.up.railway.app/docs" target="_blank" rel="noopener noreferrer" className="btn-primary">
              Open Docs →
            </a>
          </div>
        </div>
      </main>
    </>
  );
}
