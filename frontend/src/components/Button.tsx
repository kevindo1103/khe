import type { ReactNode } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit';
  className?: string;
  testId?: string;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-white border-transparent hover:bg-primary-hover',
  secondary: 'bg-surface text-primary border-border-strong hover:bg-surface-alt',
  ghost: 'bg-transparent text-primary border-transparent hover:bg-primary-soft',
  danger: 'bg-danger text-white border-transparent hover:opacity-90',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-3 py-1 text-xs h-8',
  md: 'px-4 py-2 text-sm h-10',
  lg: 'px-6 py-3 text-md h-12',
};

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  onClick,
  type = 'button',
  className = '',
  testId,
}: ButtonProps) {
  const isOff = disabled || loading;
  return (
    <button
      type={type}
      onClick={isOff ? undefined : onClick}
      disabled={isOff}
      data-testid={testId}
      className={`
        inline-flex items-center justify-center gap-2
        rounded-md font-semibold whitespace-nowrap
        transition-colors duration-150
        disabled:opacity-55 disabled:cursor-not-allowed
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${className}
      `}
    >
      {loading && <Spinner />}
      {children}
    </button>
  );
}

function Spinner({ size = 16 }: { size?: number }) {
  return (
    <span
      className="inline-block rounded-full"
      style={{
        width: size,
        height: size,
        border: '2px solid rgba(255,255,255,.5)',
        borderTopColor: '#fff',
        animation: 'khe-spin .7s linear infinite',
      }}
    />
  );
}
