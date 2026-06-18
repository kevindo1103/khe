import React from 'react';

export type BadgeKind =
  | 'processing'
  | 'extracted'
  | 'needs_review'
  | 'due_soon'
  | 'overdue'
  | 'done';

interface BadgeProps {
  kind: BadgeKind;
  children: React.ReactNode;
  className?: string;
}

const kindClasses: Record<BadgeKind, string> = {
  processing: 'bg-info-soft text-info',
  extracted: 'bg-success-soft text-success',
  needs_review: 'bg-warning-soft text-warning',
  due_soon: 'bg-warning-soft text-warning',
  overdue: 'bg-danger-soft text-danger',
  done: 'bg-success-soft text-success',
};

export function Badge({ kind, children, className = '' }: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1
        px-2 py-0.5 rounded-md text-2xs font-medium
        ${kindClasses[kind]}
        ${className}
      `}
    >
      {kind === 'needs_review' && <span>⚠</span>}
      {children}
    </span>
  );
}
