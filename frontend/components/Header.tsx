import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { LogOut, Dna } from 'lucide-react';

export function Header() {
  const router = useRouter();

  const handleLogout = () => {
    api.clearToken();
    router.push('/login');
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="max-w-7xl mx-auto px-4 flex h-16 items-center">
        <div className="mr-4 hidden md:flex">
          <button 
            onClick={() => router.push('/dashboard')}
            className="mr-6 flex items-center space-x-2 hover:opacity-80 transition-opacity"
          >
            <Dna className="h-6 w-6" />
            <span className="hidden font-bold sm:inline-block">
              BioMLStudio
            </span>
          </button>
          <nav className="flex items-center space-x-6 text-sm font-medium">
            <button
              onClick={() => router.push('/dashboard')}
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Dashboard
            </button>
            <button
              onClick={() => router.push('/datasets')}
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Datasets
            </button>
            <button
              onClick={() => router.push('/automl')}
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              AutoML
            </button>
            <button
              onClick={() => router.push('/dna-discovery')}
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              DNA Discovery
            </button>
          </nav>
        </div>
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <div className="w-full flex-1 md:w-auto md:flex-none">
            <Button variant="outline" onClick={() => router.push('/upload')} size="sm">
              Upload Dataset
            </Button>
          </div>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline-block ml-2">Logout</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
