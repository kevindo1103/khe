import React, { useState } from 'react';

interface InputProps {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  hint?: string;
  error?: string;
  editable?: boolean;
  onEdit?: () => void;
  type?: 'text' | 'password';
  className?: string;
}

export function Input({
  label,
  value,
  onChange,
  placeholder,
  hint,
  error,
  editable = false,
  onEdit,
  type = 'text',
  className = '',
}: InputProps) {
  const [hover, setHover] = useState(false);

  return (
    <label className={`block ${className}`}>
      {label && (
        <span className="block text-xs font-medium text-ink-muted mb-1">
          {label}
        </span>
      )}
      <div
        className="relative flex items-center"
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
      >
        <input
          type={type}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          className={`
            w-full h-11 box-border px-3 text-sm text-ink bg-surface
            rounded-md outline-none transition-colors
            border
            ${error ? 'border-danger' : 'border-border'}
            focus:border-primary
          `}
        />
        {editable && hover && (
          <button
            type="button"
            onClick={onEdit}
            title="Sửa (ghi Event)"
            className="absolute right-2 bg-primary-soft text-primary text-2xs font-semibold px-2 py-1 rounded-sm cursor-pointer border-0"
          >
            Sửa
          </button>
        )}
      </div>
      {error ? (
        <span className="block text-2xs text-danger mt-1">{error}</span>
      ) : hint ? (
        <span className="block text-2xs text-ink-subtle mt-1">{hint}</span>
      ) : null}
    </label>
  );
}
