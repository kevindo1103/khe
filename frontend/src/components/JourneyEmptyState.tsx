import type { ReactNode } from 'react';
import { EmptyState } from './EmptyState';
import { Button } from './Button';

/**
 * The 4-STATE EMPTY MATRIX (#198 anti-pattern fix) — CLOSED contract.
 *
 * State 1 (cold_start) must NEVER borrow state 3 (all_clear)'s "Khế sẽ nhắc khi
 * có hạn" reassurance — that was the original false-reassurance bug. `state` MUST
 * be one of EMPTY_STATES; an unknown value dev-warns + renders nothing so a wrong
 * string can't silently regress to false reassurance. Use this on EVERY list
 * surface instead of an ad-hoc empty <div>.
 *
 * Mirrors mockup_journey_primitives_v0.1.jsx §2.
 */
export const EMPTY_STATES = ['cold_start', 'processing', 'all_clear', 'no_match'] as const;
export type EmptyStateKind = (typeof EMPTY_STATES)[number];

interface JourneyEmptyStateProps {
  state: EmptyStateKind;
  docCount?: number;
  onUpload?: () => void;
  onRetry?: () => void;
}

export function JourneyEmptyState({ state, docCount = 0, onUpload, onRetry }: JourneyEmptyStateProps) {
  if (!EMPTY_STATES.includes(state)) {
    if (typeof console !== 'undefined') {
      console.warn(`[JourneyEmptyState] unknown state "${state}" — use one of ${EMPTY_STATES.join('|')}`);
    }
    return null;
  }

  switch (state) {
    case 'cold_start': // 0 documents — honest: nothing here yet, drive the 1 CTA
      return (
        <EmptyState
          icon="＋"
          title="Chưa có tài liệu"
          description="Tải hợp đồng lên để Khế tự bóc hạn và nhắc bạn."
          action={
            onUpload ? (
              <Button size="lg" onClick={onUpload} testId="journey-cold-upload">
                Tải hợp đồng
              </Button>
            ) : undefined
          }
        />
      );

    case 'processing': // docs exist, extraction pending — show motion, no CTA
      return (
        <div className="text-center px-5 py-10" data-testid="journey-processing">
          <div className="text-2xl mb-3" aria-hidden="true">⏳</div>
          <div className="text-md font-semibold text-ink" aria-live="polite">
            Đang bóc tách {docCount} tài liệu…
          </div>
          <div className="w-52 h-1 mx-auto mt-4 bg-neutral-200 rounded-pill overflow-hidden">
            <div className="w-1/2 h-full bg-primary" />
          </div>
          <div className="text-sm text-ink-muted mt-3">Khoảng ~30 giây mỗi tài liệu.</div>
        </div>
      );

    case 'all_clear': // extracted, genuinely 0 dated obligations — LEGITIMATE reassurance
      return (
        <EmptyState
          icon="✓"
          title="Đã quét — bạn không có hạn nào"
          description="Khế đã đọc tài liệu của bạn và không tìm thấy nghĩa vụ có ngày tháng nào. Sẽ báo ngay khi có."
        />
      );

    case 'no_match': // a specific query found nothing — D-08 integrity + an exit
      return (
        <EmptyState
          notFound
          action={
            <div className="flex gap-2 justify-center flex-wrap">
              {onRetry && (
                <Button variant="secondary" onClick={onRetry}>
                  Thử cách khác
                </Button>
              )}
              {onUpload && (
                <Button variant="ghost" onClick={onUpload}>
                  Tải thêm tài liệu
                </Button>
              )}
            </div>
          }
        />
      );

    default:
      return null as ReactNode;
  }
}
