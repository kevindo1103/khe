import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Badge, JourneyEmptyState } from '../../components';
import { apiFetch } from '../../lib/api';
import { useJourney } from '../../contexts/JourneyContext';
import type { ObligationListOut, ObligationOut } from '../../types/obligations';
import type { DocumentListOut, DocumentListItem } from '../../types/documents';
import type { ConsentEntry } from '../../types/consent';

// ── helpers ──

function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(dateStr);
  due.setHours(0, 0, 0, 0);
  return Math.ceil((due.getTime() - today.getTime()) / 86_400_000);
}

// keep identical to DocList badge + filter so counter, badge and list agree (#251)
const isUnconfirmed = (d: DocumentListItem) =>
  (d.status === 'extracted' || d.status === 'needs_review') && !d.confirmed_by_user_at;

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

/**
 * MANDATORY at CONFIRMED-without-channel (#238 / DEC-040 / #198 cl.4): nav unlocks
 * at CONFIRMED, so a tenant can reach steady state with no reminder channel =
 * silent product failure. This nudge is the required UX bridge.
 */
function ReminderNudge({ onEnable }: { onEnable: () => void }) {
  return (
    <Card className="border-warning/30 bg-warning-soft">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-start gap-3">
          <span className="text-xl" aria-hidden="true">⏰</span>
          <div>
            <div className="text-sm font-medium text-ink">Bật nhắc để Khế không bỏ lỡ hạn nào</div>
            <div className="text-2xs text-ink-muted mt-0.5">
              Kết nối Telegram hoặc email — bước cuối để Khế nhắc bạn trước mỗi hạn.
            </div>
          </div>
        </div>
        <Button size="sm" onClick={onEnable}>Bật nhắc →</Button>
      </div>
    </Card>
  );
}

/** "X/3 bước" onboarding progress (doc reviewed · bật nhắc · ổn định). */
function StepsChip({ reminderOn }: { reminderOn: boolean }) {
  const steps = [
    { label: 'Đã duyệt tài liệu', done: true },
    { label: 'Bật nhắc Telegram', done: reminderOn },
    { label: 'Theo dõi tự động', done: reminderOn },
  ];
  const done = steps.filter((s) => s.done).length;
  return (
    <div
      role="group"
      aria-label={`Tiến độ thiết lập ${done}/${steps.length} bước`}
      className="inline-flex items-center gap-2 flex-wrap px-3 py-1 rounded-pill bg-surface-sunken border border-border text-2xs"
    >
      <span className="font-bold text-ink">{done}/{steps.length} bước</span>
      {steps.map((s, i) => (
        <span key={i} className={`inline-flex items-center gap-1 ${s.done ? 'text-success' : 'text-ink-muted'}`}>
          <span aria-hidden="true">{s.done ? '✅' : '⬜'}</span>
          {s.label}
        </span>
      ))}
    </div>
  );
}

/**
 * Persistent, non-dismissable unconfirmed-docs counter (#251 / DEC-040 amended #249).
 * Nav unlocks at FIRST confirm, so remaining unconfirmed docs must stay visible —
 * Khế is silent on them until confirmed (D-02). Disappears only at 0 unconfirmed.
 */
function UnconfirmedCounter({ unconfirmed, total, onView }: { unconfirmed: number; total: number; onView: () => void }) {
  return (
    <Card className="border-info-border bg-info-soft" testId="dashboard-unconfirmed-counter">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-start gap-3">
          <span className="text-xl" aria-hidden="true">📄</span>
          <div>
            <div className="text-sm font-medium text-ink">
              {unconfirmed}/{total} tài liệu cần xác nhận
            </div>
            <div className="text-2xs text-ink-muted mt-0.5">
              Khế chỉ nhắc nội dung tài liệu sau khi bạn xác nhận — hãy xử lý dần các tài liệu còn lại.
            </div>
          </div>
        </div>
        <Button size="sm" variant="ghost" onClick={onView}>Xem danh sách →</Button>
      </div>
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
function StageReview({ docs, onReviewDoc }: { docs: DocumentListItem[]; onReviewDoc: (id: number) => void }) {
  const total = docs.length;
  const confirmed = docs.filter((d) => d.confirmed_by_user_at).length;
  const next = docs.find((d) => !d.confirmed_by_user_at) ?? docs[0];
  return (
    <div className="max-w-xl mx-auto">
      <Card>
        <div className="text-lg font-semibold text-ink">Cần bạn kiểm tra & xác nhận</div>
        <p className="text-sm text-ink-body leading-relaxed mt-2">
          Khế đã đọc <strong>{total} tài liệu</strong> và bóc tách thông tin. Hãy kiểm tra lại
          lần cuối và xác nhận — Khế chỉ bắt đầu nhắc sau khi bạn đồng ý.
        </p>
        <div className="mt-4 flex gap-2 items-center flex-wrap">
          <Button onClick={() => next && onReviewDoc(next.id)} disabled={!next}>
            Kiểm tra & xác nhận
          </Button>
          {/* D-02: the user is always the final author */}
          <Badge kind="needs_review">{confirmed}/{total} đã xác nhận</Badge>
        </div>
      </Card>
      <div className="text-2xs text-ink-subtle text-center mt-3">
        D-02: thông tin chỉ được chuẩn bị sẵn — bạn là người xác nhận cuối.
      </div>
    </div>
  );
}

/** STEADY/CONFIRMED — "Tôi có cần lo gì không?" dashboard (J-E). Reassurance only when legitimate. */
function StageDashboard({ docCount, unconfirmed, onUpload }: { docCount: number; unconfirmed: number; onUpload: () => void }) {
  const [obligations, setObligations] = useState<ObligationOut[] | null>(null);
  const [reminderOn, setReminderOn] = useState<boolean | null>(null);
  const navigate = useNavigate();
  const goSettings = () => navigate('/admin/settings');
  const goUnconfirmed = () => navigate('/admin/documents?confirm=pending');

  // MANDATORY persistent surface (#251): unconfirmed work stays visible after the gate unlock.
  const unconfirmedBlock = unconfirmed > 0 ? (
    <UnconfirmedCounter unconfirmed={unconfirmed} total={docCount} onView={goUnconfirmed} />
  ) : null;

  useEffect(() => {
    apiFetch<ObligationListOut>('/obligations/?page=1&page_size=100')
      .then((res) => setObligations(res.items))
      .catch(() => setObligations([]));
    apiFetch<ConsentEntry[]>('/consent')
      .then((res) => setReminderOn(res.find((c) => c.purpose === 'reminder_send')?.status === 'granted'))
      .catch(() => setReminderOn(true)); // fail-open: don't nag if consent unreadable
  }, []);

  if (obligations === null || reminderOn === null) {
    return <div className="p-8 text-center text-ink-muted text-sm">Đang tải…</div>;
  }

  // MANDATORY (#238 / DEC-040): CONFIRMED-without-channel must surface the nudge + progress
  const reminderBlock = !reminderOn ? (
    <>
      <StepsChip reminderOn={reminderOn} />
      <ReminderNudge onEnable={goSettings} />
    </>
  ) : null;

  // active = non-terminal obligations (the dashboard "total")
  const active = obligations.filter((o) => o.status !== 'done' && o.status !== 'cancelled');
  const total = active.length;

  // ── DASHBOARD CONSUMER RULE (#227 note 2) — two axes that do NOT add up ──
  // Direction (groups) → sum to total → rendered as direction cards.
  const ngVu = active.filter((o) => o.direction === 'nghĩa_vụ').length;
  const qLoi = active.filter((o) => o.direction === 'quyền_lợi').length;
  const canXacNhan = total - ngVu - qLoi; // direction null/unset
  // Status (status_breakdown) → CROSS-CUTS direction → separate strip, never a 4th direction card.
  const waiting = active.filter((o) => o.status === 'waiting_trigger').length;
  const dated = active
    .filter((o) => o.status !== 'waiting_trigger')
    .map((o) => daysUntil(o.due_date))
    .filter((d): d is number => d !== null);
  const overdue = dated.filter((d) => d < 0).length;
  const dueSoon = dated.filter((d) => d >= 0 && d <= 30).length;
  const nearest = dated.filter((d) => d >= 0).sort((a, b) => a - b)[0];
  const hasWork = overdue + dueSoon > 0;

  // genuinely 0 active obligations → legitimate all-clear (state 3, not false reassurance)
  if (total === 0) {
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        <h1 className="text-xl font-bold text-ink">Tổng quan</h1>
        {unconfirmedBlock}
        {reminderBlock}
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

      {unconfirmedBlock}
      {reminderBlock}

      {/* the single answer to "tôi có cần lo gì không?" — copy uses the group/total numbers */}
      <Card className={hasWork ? 'border-warning/30 bg-warning-soft' : 'border-success/30 bg-success-soft'}>
        <div className="flex items-center gap-3">
          <span className="text-3xl" aria-hidden="true">{hasWork ? '👀' : '🌿'}</span>
          <div>
            <div className="text-lg font-semibold text-ink" aria-live="polite">
              {hasWork ? `Có ${overdue + dueSoon} việc cần chú ý.` : 'Mọi thứ trong tầm kiểm soát.'}
            </div>
            <div className="text-sm text-ink-body mt-0.5">
              {nearest != null
                ? `Hạn gần nhất còn ${nearest} ngày — Khế đang theo dõi ${total} nghĩa vụ.`
                : `Khế đang theo dõi ${total} nghĩa vụ và sẽ nhắc bạn trước mỗi hạn.`}
            </div>
          </div>
        </div>
        {hasWork && (
          <div className="mt-4">
            <Button onClick={() => navigate('/admin/obligations')}>Xem việc cần làm</Button>
          </div>
        )}
      </Card>

      {/* AXIS 1 — direction (groups): these sum to `total` */}
      <div>
        <div className="text-2xs font-semibold text-ink-subtle uppercase tracking-wide mb-2">Theo vai trò</div>
        <div className="flex gap-3 flex-wrap">
          <Stat n={ngVu} label="Nghĩa vụ" tone="text-ink" />
          <Stat n={qLoi} label="Quyền lợi" tone="text-info" />
          <Stat n={canXacNhan} label="Cần xác nhận" tone="text-info" />
        </div>
      </div>

      {/* AXIS 2 — status: cross-cuts direction → SEPARATE strip, not a direction card */}
      <div>
        <div className="text-2xs font-semibold text-ink-subtle uppercase tracking-wide mb-2">Theo tình trạng</div>
        <div className="flex gap-2 flex-wrap">
          <Badge kind="overdue">Quá hạn: {overdue}</Badge>
          <Badge kind="due_soon">Sắp tới hạn: {dueSoon}</Badge>
          <Badge kind="needs_review">Chờ sự kiện: {waiting}</Badge>
        </div>
      </div>

      <ScopeCard contractCount={docCount} onAddMore={onUpload} />
    </div>
  );
}

// ── routed home ──

export default function Home() {
  const { stage, loading, error } = useJourney();
  const [docs, setDocs] = useState<DocumentListItem[] | null>(null);
  const navigate = useNavigate();

  const goUpload = useCallback(() => navigate('/admin/upload'), [navigate]);
  const goReviewDoc = useCallback((id: number) => navigate(`/admin/documents/${id}`), [navigate]);

  // doc list powers the counts shown in several stage views (server owns the stage)
  useEffect(() => {
    apiFetch<DocumentListOut>('/documents/?page=1&page_size=100')
      .then((res) => setDocs(res.items))
      .catch(() => setDocs([]));
  }, []);

  if (loading || docs === null) {
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
      return <StageReview docs={docs} onReviewDoc={goReviewDoc} />;
    // CONFIRMED / ACTIVATED / STEADY → steady-state dashboard
    default:
      return (
        <StageDashboard
          docCount={docs.length}
          unconfirmed={docs.filter(isUnconfirmed).length}
          onUpload={goUpload}
        />
      );
  }
}
