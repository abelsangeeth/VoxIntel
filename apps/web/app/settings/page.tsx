'use client';

import { useAuth } from '@/lib/auth-context';
import { apiFetch } from '@/lib/api';
import { useState } from 'react';
import useSWR from 'swr';
import { swrFetcher } from '@/lib/api';

type Section = 'profile' | 'integrations' | 'api' | 'notifications';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://voxintel-production.up.railway.app';

export default function SettingsPage() {
  const { user, logout, refreshUser } = useAuth();
  const { data: health } = useSWR('/v1/health', swrFetcher);
  const [activeSection, setActiveSection] = useState<Section>('profile');
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [displayName, setDisplayName] = useState(user?.display_name || user?.username || '');
  const [copied, setCopied] = useState<string | null>(null);

  const zoomConnectUrl = `${API_BASE}/v1/integrations/zoom/connect`;
  const slackWebhook = `${API_BASE}/v1/integrations/slack/webhook`;

  // Live Zoom connection status for current user
  const { data: zoomStatus, mutate: refetchZoom } = useSWR<{
    provider: string; connected: boolean; provider_email?: string; connected_at?: string;
  }>('/v1/integrations/zoom/status', swrFetcher);

  async function disconnectZoom() {
    await apiFetch('/v1/integrations/zoom/disconnect', { method: 'DELETE' });
    refetchZoom();
  }

  function copyToClipboard(text: string, key: string) {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  }

  async function saveProfile() {
    setSaving(true);
    setSaveError('');
    try {
      await apiFetch('/v1/users/me', {
        method: 'PATCH',
        body: JSON.stringify({ display_name: displayName }),
      });
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  const sideItems: { key: Section; label: string; icon: string }[] = [
    { key: 'profile', label: 'Profile', icon: '◉' },
    { key: 'integrations', label: 'Integrations', icon: '⟐' },
    { key: 'api', label: 'API & Keys', icon: '⚿' },
    { key: 'notifications', label: 'Notifications', icon: '◎' },
  ];

  return (
    <>
      <div className="topbar">
        <div>
          <div style={{ fontWeight: 700, fontSize: 18 }}>Settings</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>Manage your account and integrations</div>
        </div>
        <div className="topbar-actions">
          <div style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)' }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: health?.status === 'ok' ? '#10B981' : '#6B7280', display: 'inline-block' }} />
            API {health?.status === 'ok' ? 'Online' : 'Checking…'}
          </div>
        </div>
      </div>

      <main className="main-content content-pb">
        <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 20, alignItems: 'start' }}>
          {/* Settings nav */}
          <div className="card">
            <div style={{ padding: '8px 0' }}>
              {sideItems.map(item => (
                <button key={item.key} onClick={() => setActiveSection(item.key)} style={{
                  width: '100%', textAlign: 'left', padding: '9px 16px',
                  background: activeSection === item.key ? 'var(--primary-light)' : 'transparent',
                  border: 'none', borderLeft: `3px solid ${activeSection === item.key ? 'var(--primary)' : 'transparent'}`,
                  color: activeSection === item.key ? 'var(--primary)' : 'var(--text-secondary)',
                  fontSize: 13.5, fontWeight: activeSection === item.key ? 600 : 400,
                  fontFamily: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
                  transition: 'all 0.15s',
                }}>
                  <span>{item.icon}</span> {item.label}
                </button>
              ))}
              <div style={{ margin: '8px 16px', borderTop: '1px solid var(--border)', paddingTop: 8 }}>
                <button onClick={logout} style={{
                  width: '100%', textAlign: 'left', padding: '9px 0',
                  background: 'none', border: 'none', color: '#EF4444',
                  fontSize: 13, fontFamily: 'inherit', cursor: 'pointer',
                }}>⇥ Sign Out</button>
              </div>
            </div>
          </div>

          {/* Content */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* ── Profile ── */}
            {activeSection === 'profile' && (
              <div className="card">
                <div className="card-header"><h3>Profile</h3></div>
                <div className="card-body">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
                    <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 20, fontWeight: 700 }}>
                      {(user?.display_name || user?.username || '?').slice(0, 1).toUpperCase()}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 15 }}>{user?.display_name || user?.username}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{user?.role || 'member'}</div>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gap: 14 }}>
                    <div>
                      <label style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Display Name</label>
                      <input
                        value={displayName}
                        onChange={e => setDisplayName(e.target.value)}
                        style={{ width: '100%', padding: '9px 12px', border: '1px solid var(--border)', borderRadius: 6, fontSize: 14, fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Email</label>
                      <input readOnly value={user?.email || ''} style={{ width: '100%', padding: '9px 12px', border: '1px solid var(--border)', borderRadius: 6, fontSize: 14, fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box', opacity: 0.7 }} />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Username</label>
                      <input readOnly value={user?.username || ''} style={{ width: '100%', padding: '9px 12px', border: '1px solid var(--border)', borderRadius: 6, fontSize: 14, fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box', opacity: 0.7 }} />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Role</label>
                      <input readOnly value={user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : 'Member'} style={{ width: '100%', padding: '9px 12px', border: '1px solid var(--border)', borderRadius: 6, fontSize: 14, fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box', opacity: 0.7 }} />
                    </div>
                  </div>
                  {saveError && <div style={{ color: '#EF4444', fontSize: 13, marginTop: 12 }}>{saveError}</div>}
                  <button className="btn-primary" onClick={saveProfile} disabled={saving} style={{ marginTop: 16 }}>
                    {saving ? 'Saving…' : saved ? '✓ Saved' : 'Save Changes'}
                  </button>
                </div>
                         {/* ── Integrations ── */}
            {activeSection === 'integrations' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

                {/* Zoom */}
                <div className="card">
                  <div className="card-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: 22 }}>📹</span>
                      <div>
                        <div style={{ fontWeight: 600 }}>Zoom</div>
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Automatically capture your Zoom meetings in VoxIntel</div>
                      </div>
                    </div>
                    {/* Live status badge */}
                    {zoomStatus?.connected ? (
                      <span className="badge badge-green">● Connected</span>
                    ) : (
                      <span className="badge" style={{ background: 'var(--surface-2)', color: 'var(--text-muted)' }}>Not connected</span>
                    )}
                  </div>
                  <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    {zoomStatus?.connected ? (
                      <>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px', background: 'var(--surface-2)', borderRadius: 8, border: '1px solid var(--border)' }}>
                          <span style={{ fontSize: 20 }}>✅</span>
                          <div>
                            <div style={{ fontWeight: 600, fontSize: 13.5 }}>Connected as {zoomStatus.provider_email}</div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                              Your Zoom meetings will automatically appear in VoxIntel when they start.
                            </div>
                          </div>
                        </div>
                        <button
                          className="btn-secondary"
                          onClick={disconnectZoom}
                          style={{ color: '#EF4444', borderColor: '#FECACA', alignSelf: 'flex-start' }}
                        >
                          Disconnect Zoom
                        </button>
                      </>
                    ) : (
                      <>
                        <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                          Connect your Zoom account so VoxIntel can automatically capture your meetings, generate transcripts, and create AI summaries — without any manual steps.
                        </div>
                        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                          <a
                            href={zoomConnectUrl}
                            className="btn-primary"
                            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, textDecoration: 'none' }}
                          >
                            <span>📹</span> Connect Zoom Account
                          </a>
                          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>You'll be redirected to Zoom to authorize</span>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '10px 12px', background: 'var(--surface-2)', borderRadius: 6, lineHeight: 1.6 }}>
                          <strong>Note:</strong> Make sure your Zoom App type is set to <strong>OAuth</strong> (not Webhook Only) in the <a href="https://marketplace.zoom.us" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary)' }}>Zoom Marketplace</a>.
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Slack */}
                <div className="card">
                  <div className="card-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: 22 }}>💬</span>
                      <div>
                        <div style={{ fontWeight: 600 }}>Slack</div>
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Post meeting summaries and action items to your Slack channels</div>
                      </div>
                    </div>
                  </div>
                  <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                      Set up Slack to receive automatic meeting summaries after each session ends.
                    </div>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Slack Webhook URL</div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <code style={{ flex: 1, background: 'var(--surface-2)', borderRadius: 6, padding: '9px 12px', fontSize: 12.5, wordBreak: 'break-all', color: 'var(--text-primary)', border: '1px solid var(--border)' }}>
                          {slackWebhook}
                        </code>
                        <button className="btn-secondary" style={{ whiteSpace: 'nowrap', fontSize: 12 }} onClick={() => copyToClipboard(slackWebhook, 'slack')}>
                          {copied === 'slack' ? '✓ Copied' : '⎘ Copy'}
                        </button>
                      </div>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                      Add <code>SLACK_BOT_TOKEN</code> and <code>SLACK_SIGNING_SECRET</code> to your environment to enable Slack posting.
                    </div>
                  </div>
                </div>
              </div>
            )}          </div>
              </div>
            )}

            {/* ── API & Keys ── */}
            {activeSection === 'api' && (
              <div className="card">
                <div className="card-header"><h3>API & Keys</h3></div>
                <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>API Base URL</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <code style={{ flex: 1, background: 'var(--surface-2)', borderRadius: 6, padding: '9px 12px', fontSize: 13, color: 'var(--text-primary)', border: '1px solid var(--border)' }}>
                        {API_BASE}
                      </code>
                      <button className="btn-secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }} onClick={() => copyToClipboard(API_BASE, 'base')}>
                        {copied === 'base' ? '✓ Copied' : '⎘ Copy'}
                      </button>
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Interactive API Docs</div>
                    <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer" className="btn-secondary" style={{ fontSize: 13, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                      Open Swagger UI ↗
                    </a>
                  </div>
                  <div style={{ padding: '12px 14px', background: 'var(--surface-2)', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    <strong style={{ color: 'var(--text-primary)' }}>Authentication:</strong> All API requests require a Bearer token. Use <code>POST /v1/auth/token</code> to obtain a token, then include it as <code>Authorization: Bearer &lt;token&gt;</code> in subsequent requests.
                  </div>
                </div>
              </div>
            )}

            {/* ── Notifications ── */}
            {activeSection === 'notifications' && (
              <div className="card">
                <div className="card-header"><h3>Notifications</h3></div>
                <div className="card-body">
                  {[
                    ['Session completed', 'Notify when a meeting session finishes processing', true],
                    ['Action items extracted', 'Alert when new action items are detected', true],
                    ['Failed transcription', 'Alert on transcription failure', false],
                    ['Weekly digest', 'Weekly summary of all meetings', false],
                  ].map(([title, desc, def]) => (
                    <div key={title as string} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
                      <div>
                        <div style={{ fontWeight: 500, fontSize: 13.5 }}>{title as string}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{desc as string}</div>
                      </div>
                      <label style={{ position: 'relative', display: 'inline-block', width: 36, height: 20, cursor: 'pointer' }}>
                        <input type="checkbox" defaultChecked={def as boolean} style={{ opacity: 0, width: 0, height: 0, position: 'absolute' }} />
                        <span style={{ position: 'absolute', inset: 0, background: def ? 'var(--primary)' : 'var(--border)', borderRadius: 20, transition: '0.2s' }} />
                      </label>
                    </div>
                  ))}
                  <button className="btn-primary" onClick={() => { setSaved(true); setTimeout(() => setSaved(false), 2000); }} style={{ marginTop: 16 }}>
                    {saved ? '✓ Saved' : 'Save Preferences'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
