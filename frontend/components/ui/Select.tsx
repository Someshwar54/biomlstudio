import { SelectHTMLAttributes, ReactNode } from 'react';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  children: ReactNode;
}

export function Select({ label, children, className = '', ...props }: SelectProps) {
  return (
    <div className="flex flex-col gap-3">
      {label && (
        <label className="text-sm font-semibold text-zinc-200 tracking-wide">
          {label}
        </label>
      )}
      <select
        className={`bg-gradient-to-br from-zinc-900/90 to-zinc-950/90 border border-zinc-800/60 rounded-xl px-5 py-4 text-white focus:outline-none focus:ring-2 focus:ring-zinc-500/20 focus:border-zinc-600/60 hover:border-zinc-700/60 transition-all duration-200 backdrop-blur-sm shadow-lg hover:shadow-xl min-h-[52px] ${className}`}
        {...props}
      >
        {children}
      </select>
    </div>
  );
}
