'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';

export default function Home() {
  useAuth();
  const router = useRouter();

  useEffect(() => {
    // Redirect to dashboard - this is now the main entry point
    router.push('/dashboard');
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-zinc-950/80 to-black flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
        <p className="text-zinc-300">Loading BioMLStudio...</p>
      </div>
    </div>
  );
}
