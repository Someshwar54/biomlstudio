interface MetricCardProps {
  label: string;
  value: string | number;
  good?: boolean;
}

export function MetricCard({ label, value, good }: MetricCardProps) {
  return (
    <div className="bg-gradient-to-br from-zinc-900/90 to-zinc-950/90 border border-zinc-800/60 rounded-xl p-5 sm:p-6 shadow-lg hover:shadow-xl hover:border-zinc-700/60 transition-all duration-300 backdrop-blur-sm">
      <div className="text-sm font-medium text-zinc-400 mb-3 tracking-wide uppercase">
        {label}
      </div>
      <div className={`text-2xl sm:text-3xl font-bold tracking-tight ${
        good === true 
          ? 'text-green-400' 
          : good === false 
            ? 'text-red-400' 
            : 'text-white'
      }`}>
        {typeof value === 'number' ? value.toFixed(3) : value}
      </div>
    </div>
  );
}
