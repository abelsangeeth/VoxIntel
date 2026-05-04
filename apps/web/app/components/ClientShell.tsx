'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import Sidebar from './Sidebar';

// Routes that don't need auth or sidebar
const PUBLIC_ROUTES = ['/login', '/register'];

export default function ClientShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = PUBLIC_ROUTES.includes(pathname);

  useEffect(() => {
    if (!loading && !user && !isPublic) {
      router.replace('/login');
    }
  }, [loading, user, isPublic, router]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#0A1628' }}>
        <div style={{ textAlign: 'center', color: '#fff' }}>
          <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>VoxIntel</div>
          <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>Loading…</div>
        </div>
      </div>
    );
  }

  if (isPublic) return <>{children}</>;
  if (!user) return null; // redirecting

  return (
    <>
      <Sidebar />
      <div className="layout">{children}</div>
    </>
  );
}
