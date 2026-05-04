'use client';
import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState('demo');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      router.replace('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #0A1628 0%, #0F2744 50%, #0A1628 100%)',
      fontFamily: "'Inter', sans-serif",
    }}>
      <div style={{
        width: 400, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 12, padding: 40, backdropFilter: 'blur(12px)',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 26, fontWeight: 800, color: '#fff', letterSpacing: '-0.02em' }}>VoxIntel</div>
          <div style={{ fontSize: 12, color: '#06B6D4', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 4 }}>
            AI Meeting Intelligence
          </div>
        </div>

        <div style={{ fontSize: 18, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Sign in</div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', marginBottom: 28 }}>
          Use <code style={{ background: 'rgba(255,255,255,0.1)', padding: '1px 6px', borderRadius: 4, color: '#06B6D4' }}>demo</code> / <code style={{ background: 'rgba(255,255,255,0.1)', padding: '1px 6px', borderRadius: 4, color: '#06B6D4' }}>voxintel-demo</code>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.5)', marginBottom: 6, letterSpacing: '0.04em', textTransform: 'uppercase' }}>Username</label>
            <input
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              style={{
                width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(255,255,255,0.12)', borderRadius: 6,
                color: '#fff', fontSize: 14, fontFamily: 'inherit', outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.5)', marginBottom: 6, letterSpacing: '0.04em', textTransform: 'uppercase' }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              placeholder="voxintel-demo"
              style={{
                width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(255,255,255,0.12)', borderRadius: 6,
                color: '#fff', fontSize: 14, fontFamily: 'inherit', outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {error && (
            <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 6, padding: '10px 14px', color: '#F87171', fontSize: 13 }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              background: loading ? '#0d6660' : '#0F766E', color: '#fff', border: 'none',
              borderRadius: 6, padding: '11px 0', fontSize: 14, fontWeight: 600,
              fontFamily: 'inherit', cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: 4, transition: 'background 0.15s',
            }}
          >
            {loading ? 'Signing in…' : 'Sign In →'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'rgba(255,255,255,0.4)' }}>
          Don't have an account?{' '}
          <a href="/register" style={{ color: '#06B6D4', textDecoration: 'none', fontWeight: 500 }}>Create one →</a>
        </div>

        <div style={{ textAlign: 'center', marginTop: 12, fontSize: 12, color: 'rgba(255,255,255,0.2)' }}>
          VoxIntel v0.1.0 · Production
        </div>
      </div>
    </div>
  );
}
