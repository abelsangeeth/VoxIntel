'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { apiFetch } from '@/lib/api';

export default function RegisterPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ email: '', username: '', password: '', display_name: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await apiFetch('/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify(form),
      });
      // Auto-login after register
      await login(form.username, form.password);
      router.replace('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  }

  const inputStyle = {
    width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.3)',
    border: '1px solid rgba(255,255,255,0.12)', borderRadius: 6,
    color: '#fff', fontSize: 14, fontFamily: 'inherit', outline: 'none',
    boxSizing: 'border-box' as const,
  };
  const labelStyle = {
    display: 'block', fontSize: 12, fontWeight: 600 as const,
    color: 'rgba(255,255,255,0.5)', marginBottom: 6,
    letterSpacing: '0.04em', textTransform: 'uppercase' as const,
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #0A1628 0%, #0F2744 50%, #0A1628 100%)',
      fontFamily: "'Inter', sans-serif",
    }}>
      <div style={{
        width: 420, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 12, padding: 40, backdropFilter: 'blur(12px)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ fontSize: 26, fontWeight: 800, color: '#fff', letterSpacing: '-0.02em' }}>VoxIntel</div>
          <div style={{ fontSize: 12, color: '#06B6D4', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 4 }}>
            Create Account
          </div>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[
            { key: 'display_name', label: 'Full Name', placeholder: 'Abel Sangeeth', type: 'text' },
            { key: 'email', label: 'Email', placeholder: 'you@company.com', type: 'email' },
            { key: 'username', label: 'Username', placeholder: 'abelsangeeth', type: 'text' },
            { key: 'password', label: 'Password', placeholder: 'Min. 8 characters', type: 'password' },
          ].map(field => (
            <div key={field.key}>
              <label style={labelStyle}>{field.label}</label>
              <input
                type={field.type}
                value={form[field.key as keyof typeof form]}
                onChange={set(field.key)}
                placeholder={field.placeholder}
                required={field.key !== 'display_name'}
                style={inputStyle}
              />
            </div>
          ))}

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
            {loading ? 'Creating account…' : 'Create Account →'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'rgba(255,255,255,0.4)' }}>
          Already have an account?{' '}
          <Link href="/login" style={{ color: '#06B6D4', textDecoration: 'none', fontWeight: 500 }}>Sign in</Link>
        </div>
      </div>
    </div>
  );
}
