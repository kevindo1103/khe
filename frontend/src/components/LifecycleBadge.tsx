const LIFECYCLE_MAP: Record<string, { label: string; cls: string }> = {
  // #485 Q1 (green-creep cleanup): active = normal neutral state, not celebratory green.
  active:    { label: 'Đang hiệu lực', cls: 'border border-border text-ink-muted' },
  expiring:  { label: 'Sắp hết hạn',  cls: 'bg-warning-soft text-warning' },
  expired:   { label: 'Hết hạn',      cls: 'bg-danger-soft text-danger' },
  settled:   { label: 'Đã thanh lý',  cls: 'bg-surface-alt text-ink-muted' },
  suspended: { label: 'Tạm dừng',     cls: 'bg-surface-alt text-ink-muted' },
};

export function LifecycleBadge({ status }: { status: string | null | undefined }) {
  if (!status) return null;
  const entry = LIFECYCLE_MAP[status];
  if (!entry) return null;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-2xs font-medium shrink-0 ${entry.cls}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70 shrink-0" />
      {entry.label}
    </span>
  );
}
