import type { ReactNode } from 'react';

interface ModalProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}

export function Modal({ open, title, onClose, children, footer, className = '' }: ModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-modal flex items-end sm:items-center justify-center">
      {/* scrim */}
      <div
        className="absolute inset-0 bg-black/45"
        onClick={onClose}
      />
      {/* content */}
      <div
        className={`
          relative z-10 w-full sm:w-auto sm:max-w-lg
          bg-surface rounded-t-xl sm:rounded-xl
          shadow-lg
          ${className}
        `}
      >
        <div className="px-5 py-4 border-b border-border flex items-center justify-between">
          <h3 className="text-lg font-semibold text-ink">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-ink-subtle hover:text-ink text-xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="px-5 py-4 text-sm text-ink-muted">{children}</div>
        {footer && (
          <div className="px-5 py-3 border-t border-border flex justify-end gap-2">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
