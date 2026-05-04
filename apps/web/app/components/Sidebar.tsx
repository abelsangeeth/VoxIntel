'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

const nav = [
  { href: '/', label: 'Dashboard', icon: '◈' },
  { href: '/meetings', label: 'Meetings', icon: '◷' },
  { href: '/transcripts', label: 'Transcripts', icon: '≡' },
  { href: '/search', label: 'Search', icon: '⌕' },
  { href: '/analytics', label: 'Analytics', icon: '◎' },
  { href: '/integrations', label: 'Integrations', icon: '⟐' },
  { href: '/settings', label: 'Settings', icon: '⚙' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>VoxIntel</h1>
        <span>AI Meeting Intelligence</span>
      </div>
      <nav className="sidebar-nav">
        {nav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href)) ? 'active' : ''}
          >
            <span style={{ fontSize: 15, width: 18, textAlign: 'center' }}>{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)', padding: '4px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 22, height: 22, borderRadius: '50%', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, color: '#fff' }}>
            {user?.username?.slice(0, 1).toUpperCase()}
          </div>
          {user?.username}
        </div>
        <button onClick={logout} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.35)', fontSize: 12, textAlign: 'left', padding: '6px 0', fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 6, transition: 'color 0.15s' }}
          onMouseOver={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.7)')}
          onMouseOut={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.35)')}>
          ⇥ Sign Out
        </button>
      </div>
    </aside>
  );
}
