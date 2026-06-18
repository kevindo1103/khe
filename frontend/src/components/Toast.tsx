import React from 'react';

export type ToastKind = 'success' | 'error' | 'info';

interface ToastProps {
  kind: ToastKind;
  children: React.ReactNode;
  className?: string;
}

const kindClasses: Record<ToastKind, string> = {
  success: 'bg-success-soft text-success border-success-soft',
  error: 'bg-danger-soft text-danger border-danger-soft',
  info: 'bg-info-soft text-info border-info-soft',
};

const iconMap: Record<ToastKind, string> = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
};

export function Toast({ kind, children, className = '' }: ToastProps) {
  return (
    <div
      className={`
        inline-flex items-center gap-2
        px-4 py-2 rounded-md border text-sm font-medium
        ${kindClasses[kind]}
        ${className}
      `}
    >
      <span className="font-bold">{iconMap[kind]}</span>
      {children}
    </div>
  );
}
