import React from 'react';

interface EmptyStateProps {
  icon?: string;
  title?: string;
  description?: string;
  action?: React.ReactNode;
  notFound?: boolean;
  className?: string;
}

export function EmptyState({
  icon = '📭',
  title,
  description,
  action,
  notFound = false,
  className = '',
}: EmptyStateProps) {
  const t = notFound
    ? 'Không tìm thấy thông tin này trong hồ sơ của bạn.'
    : title;
  const d = notFound
    ? 'Khế chỉ trả lời từ tài liệu bạn đã tải lên — không phỏng đoán. Hãy thử hỏi cách khác hoặc tải thêm tài liệu.'
    : description;

  return (
    <div className={`text-center px-5 py-10 text-ink-muted ${className}`}>
      <div className="text-4xl mb-3">{notFound ? '🔍' : icon}</div>
      {t && (
        <div className="text-lg font-semibold text-ink mb-2">{t}</div>
      )}
      {d && (
        <div className="text-sm max-w-sm mx-auto leading-relaxed">{d}</div>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
