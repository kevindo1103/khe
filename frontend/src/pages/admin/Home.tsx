import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Badge, JourneyEmptyState } from '../../components';
import { apiFetch } from '../../lib/api';
import { useJourneyStage } from '../../hooks/useJourneyStage';
import type { ObligationListOut, ObligationOut } from '../../types/obligations';

// ── helpers ──

function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(dateStr);
  due.setHours(0, 0, 0, 0);
  return Math.ceil((due.getTime() - today.getTime()) / 86_400_000);
}

// ── small presentational pieces (mirror journey primitives v0.1) ──

function ScopeCard({ contractCount, onAddMore }: { contractCount: number; onAddMore: () => void }) {
  // Per-contract scope + hint loop (#198 clarification 3) — NEVER "đã được bảo vệ toàn kho".
  return (
    <Card className="border-primary-border bg-primary-soft">
      <div className="flex gap-3 items-start">
        <span className="text-xl" aria-hidden="true">🔔</span>
        <div className="flex-1">
          <div className="text-sm text-ink leading-relaxed">
            Khế đang nhắc bạn về <strong>{contractCount} hợp đồng</strong>.
          </div>
          <div className="text-2xs text-ink-muted mt-0.5">
            Tải thêm hợp đồng để Khế nhắc trọn vẹn hơn.
          </div>
          <div className="mt-3">
            <Button size="sm" onClick={onAddMore}>Tải hợp đồng tiếp theo →</Button>
          </div>
        </div>
      </div>
    </Card>
  );
}

function Stat({ n, label, tone }: { n: number; label: string; tone: string }) {
  return (
    <Card className="flex-1 min-w-[140px]">
      <div className={`text-2xl font-bold tabular-nums ${tone}`}>{n}</div>
      <div className="text-sm text-ink-muted">{label}</div>
    </Card>
  );
}

// ── stage views ──

/** NEW — self-serve cold start: one focused CTA (Hick's law). */
function StageNew({ onUpload }: { onUpload: () => void }) {
  return (
    <div className="max-w-xl mx-auto">
      <div className="text-center py-6 px-2">
        <div className="text-xl font-bold text-ink">Chào mừng đến với Khế 👋</div>
        <p className="text-sm text-ink-muted mt-2 leading-relaxed">
          Tải hợp đồng đầu tiên lên — Khế tự đọc, bóc hạn và nhắc bạn trước khi tới hạn.
        </p>
      </div>
      <Card>
        <JourneyEmptyState state="cold_start" onUpload={onUpload} />
      </Card>
      <div className="text-2xs text-ink-subtle text-center mt-3">
        Các mục khác mở sau khi bạn tải hợp đồng đầu tiên.
      </div>
    </div>
  );
}

/** NEEDS_REVIEW — data exists (incl. concierge pre-fill), user must self-confirm (D-02). */
function StageReview({ docCount, onReview }: { docCount: number; onReview: () => void }) {
  return (
    <div className="max-w-xl mx-auto">
      <Card>
        <div className="text-lg font-semibold text-ink">Cần bạn kiểm tra & xác nhận</div>
        <p className="text-sm text-ink-body leading-relaxed mt-2">
          Khế đã đọc <strong>{docCount} tài liệu</strong> và bóc tách thông tin. Hãy kiểm tra lại
          lần cuối và xác nhận — Khế chỉ bắt đầu nhắc sau khi bạn đồng ý.
        </p>
        <div className="mt-4 flex gap-2 items-center">
          <Button onClick={onReview}>Kiểm tra & xác nhận</Button>
          {/* D-02: the user is always the final author */}
          <Badge kind="needs_review">Cần bạn xác nhận</Badge>
        </div>
      </Card>
      <div className="text-2xs text-ink-subtle text-center mt-3">
        D-02: thông tin chỉ được chuẩn bị sẵn — bạn là người xác nhận cuối.
      </div>
    </div>
  );
}

/** STEADY/CONFIRMED — "Tôi có cần lo gì không?" dashboard (J-E). Reassurance only when legitimate. */
function StageDashboard({ docCount, onUpload }: { docCount: number; onUpload: () => void }) {
  const [obligations, setObligations] = useState<ObligationOut[] | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    apiFetch<ObligationListOut>('/obligations/?page=1&page_size=100')
      .then((res) => setObligations(res.items))
      .catch(() => setObligations([]));
  }, []);

  if (obligations === null) {
    return <div className="p-8 text-center text-ink-muted text-sm">Đang tải…</div>;
  }

  const pending = obligations.filter((o) => o.status === 'pending');
  const withDays = pending
    .map((o) => daysUntil(o.due_date))
    .filter((d): d is number => d !== null);
  const overdue = withDays.filter((d) => d < 0).length;
  const dueSoon = withDays.filter((d) => d >= 0 && d <= 30).length;
  const quyenLoi = pending.filter((o) => o.direction === 'quyền_lợi').length;
  const nearest = withDays.filter((d) => d >= 0).sort((a, b) => a - b)[0];
  const hasWork = overdue + dueSoon > 0;

  // genuinely 0 dated obligations → legitimate all-clear (state 3, not false reassurance)
  if (withDays.length === 0) {
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        <h1 className="text-xl font-bold text-ink">Tổng quan</h1>
        <Card>
          <JourneyEmptyState state="all_clear" />
        </Card>
        <ScopeCard contractCount={docCount} onAddMore={onUpload} />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <h1 className="text-xl font-bold text-ink">Tổng quan</h1>

      {/* the single answer to "tôi có cần lo gì không?" */}
      <Card className={hasWork ? 'border-warning/30 bg-warning-soft' : 'border-success/30 bg-success-soft'}>
        <div className="flex items-center gap-3">
          <span className="text-3xl" aria-hidden="true">{hasWork ? '👀' : '🌿'}</span>
          <div>
            <div className="text-lg font-semibold text-ink" aria-live="polite">
              {hasWork ? `Có ${overdue + dueSoon} việc cần chú ý.` : 'Mọi thứ trong tầm kiểm soát.'}
            </div>
            <div className="text-sm text-ink-body mt-0.5">
              {nearest != null
                ? `Hạn gần nhất còn ${nearest} ngày — Khế sẽ nhắc trước.`
                : 'Khế sẽ nhắc bạn trước mỗi hạn.'}
            </div>
          </div>
        </div>
        {hasWork && (
          <div className="mt-4">
            <Button onClick={() => navigate('/admin/obligations')}>Xem việc cần làm</Button>
          </div>
        )}
      </Card>

      {/* legitimate-reassurance footing: real counts, scoped */}
      <div className="flex gap-3 flex-wrap">
        <Stat n={overdue + dueSoon} label="Sắp tới hạn" tone={hasWork ? 'text-warning' : 'text-success'} />
        <Stat n={quyenLoi} label="Quyền lợi cần đòi" tone="text-info" />
        <Stat n={docCount} label="Hợp đồng đang theo dõi" tone="text-ink" />
      </div>

      <ScopeCard contractCount={docCount} onAddMore={onUpload} />
    </div>
  );
}

// ── routed home ──

export default function Home() {
  const { stage, docs, loading, error } = useJourneyStage();
  const navigate = useNavigate();

  const goUpload = useCallback(() => navigate('/admin/upload'), [navigate]);
  const goDocuments = useCallback(() => navigate('/admin/documents'), [navigate]);

  if (loading) {
    return <div className="p-8 text-center text-ink-muted text-sm">Đang tải…</div>;
  }
  if (error) {
    return <div className="p-8 text-center text-danger text-sm">{error}</div>;
  }

  switch (stage) {
    case 'NEW':
      return <StageNew onUpload={goUpload} />;
    case 'EXTRACTING':
      return (
        <div className="max-w-xl mx-auto">
          <Card>
            <JourneyEmptyState
              state="processing"
              docCount={docs.filter((d) => d.status === 'processing').length}
            />
          </Card>
        </div>
      );
    case 'NEEDS_REVIEW':
      return <StageReview docCount={docs.length} onReview={goDocuments} />;
    // CONFIRMED / ACTIVATED / STEADY → steady-state dashboard
    default:
      return <StageDashboard docCount={docs.length} onUpload={goUpload} />;
  }
}
