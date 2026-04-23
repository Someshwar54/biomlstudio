import { ReactNode } from 'react';
import { Header } from './Header';

interface PageWrapperProps {
  children: ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '4xl' | '6xl' | '7xl';
  className?: string;
}

export function PageWrapper({ 
  children, 
  maxWidth = '7xl', 
  className = '' 
}: PageWrapperProps) {
  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '4xl': 'max-w-4xl',
    '6xl': 'max-w-6xl',
    '7xl': 'max-w-7xl',
  };

  return (
    <>
      <Header />
      <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-black via-zinc-950/90 to-black">
        <div className={`page-container ${maxWidthClasses[maxWidth]} mx-auto page-section ${className}`}>
          {children}
        </div>
      </div>
    </>
  );
}