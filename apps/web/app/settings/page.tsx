'use client';

import { useAuth } from '@/lib/auth-context';
import { useState } from 'react';
import useSWR from 'swr';
import { swrFetcher } from '@/lib/api';

type Section = 'profile' | 'integrations' | 'api' | 'notifications';

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { data: health } = useSWR('/v1/health', swrFetcher);
  const [activeSection, setActiveSection] = useState<Section>('profile');
  const [saved, setSaved] = useState(false);

  function save() {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
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
            {activeSection === 'profile' && (
              <>
                <div className="card">
                  <div className="card-header"><h3>Profile</h3></div>
                  <div className="card-body">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
                      <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 20, fontWeight: 700 }}>
                        {user?.username?.slice(0, 1).toUpperCase()}
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 15 }}>{user?.display_name || user?.username}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : 'Member'}</div>
                      </div>
                    </div>
                    <div style={{ display: 'grid', gap: 14 }}>
                      {[['Display Name', user?.display_name || user?.username], ['Email', user?.email], ['Role', user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : 'Member']].map(([label, val]) => (
                        <div key={label}>
                          <label style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</label>
                          <input defaultValue={val ?? ''} style={{ width: '100%', padding: '9px 12px', border: '1px solid var(--border)', borderRadius: 6, fontSize: 14, fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box' }} />
                        </div>
                      ))}
                    </div>
                    <button className="btn-primary" onClick={save} style={{ marginTop: 16 }}>{saved ? '✓ Saved' : 'Save Changes'}</button>
                  </div>
                </div>
              </>
            )}

            {activeSection === 'integrations' && (
              <div className="card">
                <div className="card-header"><h3>Integrations</h3></div>
                <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  {[
                    {
                      name: 'Zoom', icon: '📹', desc: 'Auto-capture Zoom meetings via webhook',
                      url: 'https://voxintel-production.up.railway.app/v1/integrations/zoom/webhook',
                      status: 'Configure',
                    },
                    {
                      name: 'Slack', icon: '💬', desc: 'Post meeting summaries to Slack channels',
                      url: 'https://voxintel-production.up.railway.app/v1/integrations/slack/webhook',
                      status: 'Configure',
                    },
                  ].map(int => (
                    <div key={int.name} style={{ display: 'flex', alignItems: 'flex-start', gap: 16, padding: 16, border: '1px solid var(--border)', borderRadius: 8 }}>
                      <span style={{ fontSize: 24 }}>{int.icon}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600, marginBottom: 4 }}>{int.name}</div>
                        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 10 }}>{int.desc}</div>
                        <div style={{ background: 'var(--surface-2)', borderRadius: 6, padding: '7px 12px', fontSize: 12, fontFamily: 'monospace', color: 'var(--text-primary)', wordBreak: 'break-all', marginBottom: 10 }}>
                          {int.url}
                        </div>
                        <button className="btn-secondary" onClick={() => navigator.clipboard.writeText(int.url)} style={{ fontSize: 12 }}>⎘ Copy Webhook URL</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeSection === 'api' && (
              <div className="card">
                <div className="card-header"><h3>API & Keys</h3></div>
                <div className="card-body">
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>
                      Your API base URL for integration:
                    </div>
                    <div style={{ background: 'var(--surface-2)', borderRadius: 6, padding: '10px 14px', fontSize: 13, fontFamily: 'monospace', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>https://voxintel-production.up.railway.app</span>
                      <button className="btn-secondary" style={{ fontSize: 12 }} onClick={() => navigator.clipboard.writeText('https://voxintel-production.up.railway.app')}>⎘ Copy</button>
                    </div>
                  </div>
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>Demo credentials (read-only sandbox):</div>
                    <div style={{ background: 'var(--surface-2)', borderRadius: 6, padding: '10px 14px', fontSize: 13, fontFamily: 'monospace' }}>
                      Username: <strong>demo</strong> · Password: <strong>voxintel-demo</strong>
                    </div>
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                    Full API docs at{' '}
                    <a href="https://voxintel-production.up.railway.app/docs" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary)' }}>
                      /docs
                    </a>
                    {' '}(Swagger UI)
                  </div>
                </div>
              </div>
            )}

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
                  <button className="btn-primary" onClick={save} style={{ marginTop: 16 }}>{saved ? '✓ Saved' : 'Save Preferences'}</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
