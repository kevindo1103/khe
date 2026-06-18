import React from 'react';

interface CardProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function Card({ title, subtitle, footer, children, className = '' }: CardProps) {
  return (
    <div className={`bg-surface border border-border rounded-lg shadow-sm overflow-hidden ${className}`}>
      {(title || subtitle) && (
        <div className="px-5 py-4 border-b border-border">
          {title && <div className="text-lg font-semibold text-ink">{title}</div>}
          {subtitle && <div className="text-sm text-ink-muted mt-1">{subtitle}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
      {footer && (
        <div className="px-5 py-3 border-t border-border bg-surface-alt">
          {footer}
        </div>
      )}
    </div>
  );
}
