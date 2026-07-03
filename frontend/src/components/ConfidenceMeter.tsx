interface ConfidenceMeterProps {
  value: number; // 0.0 - 1.0
  className?: string;
}

export function ConfidenceMeter({ value, className = '' }: ConfidenceMeterProps) {
  const pct = Math.round(value * 100);
  const isLow = value < 0.8;

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="w-20 h-2 bg-border rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${isLow ? 'bg-warning' : 'bg-done'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-2xs font-medium ${isLow ? 'text-warning' : 'text-done'}`}>
        {pct}%
      </span>
    </div>
  );
}
