import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/auth-context';
import ClientShell from './components/ClientShell';

export const metadata: Metadata = {
  title: 'VoxIntel — AI Meeting Intelligence',
  description: 'Transcribe, summarize and search your meetings with AI.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ClientShell>{children}</ClientShell>
        </AuthProvider>
      </body>
    </html>
  );
}
