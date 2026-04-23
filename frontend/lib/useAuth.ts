import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export function useAuth() {
  const router = useRouter();

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      router.push('/login');
    }
  }, [router]);

  return { isAuthenticated: !!api.getToken() };
}
