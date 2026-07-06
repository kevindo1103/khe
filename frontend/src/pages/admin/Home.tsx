import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Badge, JourneyEmptyState } from '../../components';
import { apiFetch } from '../../lib/api';
import { useJourney } from '../../contexts/JourneyContext';
import type { ObligationSummaryOut } from '../../types/obligations';
import type { DocumentListOut, DocumentListItem } from '../../types/documents';
import type { ConsentEntry } from '../../types/consent';

// ── helpers ──

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

/** NEW — self-serve cold start: 3 CTAs (DEC-058). */
function StageNew({
  onUpload,
  onManual,
  onCompliance,
}: {
  onUpload: () => void;
  onManual: () => void;
  onCompliance: () => void;
}) {
  return (
    <div className="max-w-xl mx-auto">
      <div className="text-center py-6 px-2">
        <div className="text-xl font-bold text-ink">Chào mừng đến với Khế 👋</div>
        <p className="text-sm text-ink-muted mt-2 leading-relaxed">
          Bắt đầu theo dõi nghĩa vụ — tải hợp đồng, nhập tay, hoặc rà soát tuân thủ.
        </p>
      </div>
      <div className="space-y-3">
        <Card>
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div>
              <div className="text-sm font-semibold text-ink">Tải hợp đồng lên</div>
              <div className="text-2xs text-ink-muted mt-0.5">AI tự đọc và bóc tách nội dung.</div>
            </div>
            <Button size="sm" onClick={onUpload}>Tải lên →</Button>
          </div>
        </Card>
        <Card>
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div>
              <div className="text-sm font-semibold text-ink">Nhập tay hợp đồng</div>
              <div className="text-2xs text-ink-muted mt-0.5">Flow 2: tải lên → kiểm tra → xác nhận.</div>
            </div>
            <Button size="sm" variant="secondary" onClick={onManual}>Nhập tay →</Button>
          </div>
        </Card>
        <Card>
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div>
              <div className="text-sm font-semibold text-ink">Rà soát tuân thủ</div>
              <div className="text-2xs text-ink-muted mt-0.5">Flow 3: tạo nghĩa vụ từ gói luật (placeholder).</div>
            </div>
            <Button size="sm" variant="secondary" onClick={onCompliance}>Rà soát →</Button>
          </div>
        </Card>
      </div>
      <div className="text-2xs text-ink-subtle text-center mt-3">
        Các mục khác mở sau khi bạn hoàn tất bước đầu tiên.
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

// direction-card tone by server group key — labels themselves come from the server (#227)
const DIRECTION_TONE: Record<string, string> = {
  'nghĩa_vụ': 'text-ink',
  'quyền_lợi': 'text-info',
  'null': 'text-info',
};

/** STEADY/CONFIRMED — "Tôi có cần lo gì không?" dashboard (J-E). Reassurance only when legitimate. */
function StageDashboard({ docCount, unconfirmed, onUpload }: { docCount: number; unconfirmed: number; onUpload: () => void }) {
  // #253/#254 — consume the server aggregate; FE no longer derives direction counts.
  const [summary, setSummary] = useState<ObligationSummaryOut | null>(null);
  const [reminderOn, setReminderOn] = useState<boolean | null>(null);
  const navigate = useNavigate();
  const goSettings = () => navigate('/admin/settings');
  const goUnconfirmed = () => navigate('/admin/documents?confirm=pending');

  // MANDATORY persistent surface (#251): unconfirmed work stays visible after the gate unlock.
  const unconfirmedBlock = unconfirmed > 0 ? (
    <UnconfirmedCounter unconfirmed={unconfirmed} total={docCount} onView={goUnconfirmed} />
  ) : null;

  useEffect(() => {
    // default group_by=direction + active_only=true (#254) → counts match the active list
    apiFetch<ObligationSummaryOut>('/obligations/summary?group_by=direction')
      .then(setSummary)
      .catch(() => setSummary(null));
    apiFetch<ConsentEntry[]>('/consent')
      .then((res) => setReminderOn(res.find((c) => c.purpose === 'reminder_send')?.status === 'granted'))
      .catch(() => setReminderOn(true)); // fail-open: don't nag if consent unreadable
  }, []);

  if (summary === null || reminderOn === null) {
    return <div className="p-8 text-center text-ink-muted text-sm">Đang tải…</div>;
  }

  // MANDATORY (#238 / DEC-040): CONFIRMED-without-channel must surface the nudge + progress
  const reminderBlock = !reminderOn ? (
    <>
      <StepsChip reminderOn={reminderOn} />
      <ReminderNudge onEnable={goSettings} />
    </>
  ) : null;

  const { total, groups, status_breakdown: sb } = summary;
  // ── DASHBOARD CONSUMER RULE (#227 note 2) — two axes that do NOT add up ──
  // AXIS 1 direction = `groups` (sum to total). AXIS 2 status = `status_breakdown` (cross-cuts).
  const hasWork = sb.overdue + sb.due_soon > 0;
  // nearest upcoming across all direction groups (server gives per-group days_left)
  const nearestDays = groups
    .map((g) => g.nearest?.days_left)
    .filter((d): d is number => d != null)
    .sort((a, b) => a - b)[0];

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
              {hasWork ? `Có ${sb.overdue + sb.due_soon} việc cần chú ý.` : 'Mọi thứ trong tầm kiểm soát.'}
            </div>
            <div className="text-sm text-ink-body mt-0.5">
              {nearestDays != null
                ? `Hạn gần nhất còn ${nearestDays} ngày — Khế đang theo dõi ${total} nghĩa vụ.`
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

      {/* AXIS 1 — direction (server groups, labels verbatim): these sum to `total` */}
      <div>
        <div className="text-2xs font-semibold text-ink-subtle uppercase tracking-wide mb-2">Theo vai trò</div>
        <div className="flex gap-3 flex-wrap">
          {groups.map((g) => (
            <Stat key={g.key} n={g.count} label={g.label} tone={DIRECTION_TONE[g.key] ?? 'text-ink'} />
          ))}
        </div>
      </div>

      {/* AXIS 2 — status: cross-cuts direction → SEPARATE strip, not a direction card */}
      <div>
        <div className="text-2xs font-semibold text-ink-subtle uppercase tracking-wide mb-2">Theo tình trạng</div>
        <div className="flex gap-2 flex-wrap">
          <Badge kind="overdue">Quá hạn: {sb.overdue}</Badge>
          <Badge kind="due_soon">Sắp tới hạn: {sb.due_soon}</Badge>
          <Badge kind="needs_review">Chờ sự kiện: {sb.waiting_trigger}</Badge>
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
  const goManual = useCallback(() => navigate('/admin/documents/new'), [navigate]);
  const goCompliance = useCallback(() => navigate('/admin/obligations/ra-soat'), [navigate]);
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
      return <StageNew onUpload={goUpload} onManual={goManual} onCompliance={goCompliance} />;
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
