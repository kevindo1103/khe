import { useState, useEffect, useCallback, useMemo, useRef, type MouseEvent } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Button, Card, Badge, Input, ConfidenceMeter, Toast, Modal, EmptyState, LifecycleBadge } from '../../components';
import type { ToastKind } from '../../components/Toast';
import { apiFetch } from '../../lib/api';
import type {
  DocumentDetailOut,
  PartyOut,
  TermOut,
  ConfirmDocumentOut,
  RemapTypeOut,
  ClauseOut,
  ClauseListOut,
  ClausePatchOut,
  ReReadDiff,
  ReReadOut,
  DefinitionOut,
  DefinitionListOut,
  DefinitionPatchOut,
  CrossRefOut,
  CrossRefListOut,
  CrossRefResolveOut,
} from '../../types/documents';
import type { EventOut, EventListOut } from '../../types/events';
import type { ObligationOut, ObligationPatchOut, BulkCompleteIn, BulkCompleteOut } from '../../types/obligations';
import type { ApiError } from '../../lib/api';
import { useJourney } from '../../contexts/JourneyContext';
import {
  DOC_TYPE_LABELS,
  DOC_TYPE_GROUP_LABELS,
  OBLIGATION_TYPE_LABELS,
  CANONICAL_FIELDS,
  FIELD_LABELS,
  labelFor,
} from '../../lib/labels';

type TabKey = 'overview' | 'obligations' | 'clauses' | 'parties';

const DOC_TYPE_GROUPS = Object.keys(DOC_TYPE_GROUP_LABELS);

const STATUS_BADGE: Record<string, 'processing' | 'extracted' | 'needs_review'> = {
  processing: 'processing',
  extracted: 'extracted',
  needs_review: 'needs_review',
};

const STATUS_LABEL: Record<string, string> = {
  processing: 'Đang xử lý',
  extracted: 'Đã bóc tách',
  needs_review: 'Cần kiểm tra',
};


const STAGE_LABELS: Record<string, string> = {
  queued: 'Đang chờ xử lý…',
  ocr: 'Đang nhận dạng văn bản…',
  llm: 'Đang phân tích hợp đồng…',
  saving: 'Đang lưu kết quả…',
  done: 'Hoàn tất',
  failed: 'Lỗi xử lý',
};

function ExtractionProgress({ stage, progress }: { stage: string | null | undefined; progress: number | null | undefined }) {
  const pct = progress ?? 0;
  const label = (stage && STAGE_LABELS[stage]) || STAGE_LABELS.queued;
  const failed = stage === 'failed';

  return (
    <div className="mb-5">
      <div className="flex items-center justify-between mb-1.5">
        <span className={`text-xs font-medium ${failed ? 'text-danger' : 'text-ink-muted'}`}>{label}</span>
        <span className="text-2xs text-ink-subtle">{pct}%</span>
      </div>
      <div className="w-full h-2 bg-surface-sunken rounded-pill overflow-hidden">
        <div
          className={`h-full rounded-pill transition-all duration-[1200ms] ease-out ${failed ? 'bg-danger' : 'bg-primary'}`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  );
}

// ── #472 R472: obligation tab helpers — temporal bucket + currency format ────
function daysDiff(dateStr: string): number | null {
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return null;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return Math.round((d.getTime() - now.getTime()) / 86400000);
}

function temporalBucket(ob: ObligationOut): 'overdue' | 'this_week' | 'upcoming' | 'waiting' | 'done' {
  if (ob.status === 'waiting_trigger') return 'waiting';
  if (ob.status === 'done' || ob.status === 'cancelled') return 'done';
  if (!ob.due_date) return 'upcoming';
  const days = daysDiff(ob.due_date);
  if (days === null) return 'upcoming';
  if (days < 0) return 'overdue';
  if (days <= 7) return 'this_week';
  return 'upcoming';
}

function overdueLabel(dateStr: string): string {
  const days = daysDiff(dateStr);
  if (days === null) return 'Không thời hạn';
  const dateFmt = new Date(dateStr).toLocaleDateString('vi-VN');
  if (Math.abs(days) === 0) return `Hôm nay · ${dateFmt}`;
  return `Quá hạn ${Math.abs(days)} ngày · ${dateFmt}`;
}

function dueLabel(dateStr: string): string {
  const days = daysDiff(dateStr);
  if (days === null) return 'Không thời hạn';
  const dateFmt = new Date(dateStr).toLocaleDateString('vi-VN');
  if (days === 0) return `Hôm nay · ${dateFmt}`;
  if (days === 1) return `Ngày mai · ${dateFmt}`;
  if (days <= 7) return `Còn ${days} ngày · ${dateFmt}`;
  return `Hạn: ${dateFmt}`;
}

function formatCurrency(raw: string | null): string | null {
  if (!raw) return null;
  if (/%/.test(raw)) return null;
  const cleaned = raw.replace(/[^\d.,]/g, '').replace(/\./g, '').replace(',', '.');
  const num = parseFloat(cleaned);
  if (isNaN(num) || num <= 0) return null;
  return num.toLocaleString('vi-VN') + ' đ';
}

const RECURRENCE_LABEL: Record<string, string> = { open_ended_review: 'Rà soát định kỳ' };

// ── #472: text+color badge atom (Q7 — no icon/emoji, DEC-055) ────────────────
function TextBadge({ className, children }: { className?: string; children: React.ReactNode }) {
  // Tone classes are always passed as a complete bg-*/text-*/border-* set —
  // never combined with the default, since Tailwind resolves same-specificity
  // utility conflicts by stylesheet source order, not by className order.
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-semibold whitespace-nowrap ${className || 'bg-surface-sunken text-ink-muted'}`}
    >
      {children}
    </span>
  );
}

function StatusBadge({ status }: { status: ObligationOut['status'] }) {
  const MAP: Record<string, { label: string; className: string }> = {
    done: { label: 'Hoàn thành', className: 'bg-done-soft text-done' },
    pending: { label: 'Chưa làm', className: 'bg-surface-sunken text-ink-muted' },
    in_progress: { label: 'Đang làm', className: 'bg-info-soft text-info' },
    partial: { label: 'Một phần', className: 'bg-info-soft text-info' },
    cancelled: { label: 'Đã hủy', className: 'bg-surface-sunken text-ink-subtle' },
    waiting_trigger: { label: 'Chờ kích hoạt', className: 'bg-warning-soft text-warning' },
  };
  const s = MAP[status] || MAP.pending;
  return <TextBadge className={s.className}>{s.label}</TextBadge>;
}

function CategoryChip({ obligationType }: { obligationType: string }) {
  const label = labelFor(OBLIGATION_TYPE_LABELS, obligationType);
  // Penalty: outline treatment (border-danger, transparent bg) — distinct from
  // the solid-fill "Quá hạn" badge (DS v1.1 penalty kind, PR #474 follow-up).
  if (obligationType === 'penalty') {
    return <TextBadge className="bg-transparent border border-danger text-danger">{label}</TextBadge>;
  }
  return <TextBadge>{label}</TextBadge>;
}

function AmountDisplay({ raw }: { raw: string | null }) {
  const formatted = formatCurrency(raw);
  if (!formatted) return null;
  // #485 Q1 (green-creep cleanup): amount is data, not a status — plain text,
  // no badge, no green.
  return <span className="text-xs text-ink font-medium">{formatted}</span>;
}

function SourceClauseLink({
  clauseNum,
  onJump,
}: {
  clauseNum: string | null;
  onJump: (clauseNum: string) => void;
}) {
  if (!clauseNum) return null;
  return (
    <button
      type="button"
      onClick={() => onJump(clauseNum)}
      className="text-2xs font-medium text-primary underline hover:text-primary-hover"
      title={`Nhảy đến ${clauseNum} trong tab Nội dung hợp đồng`}
    >
      {clauseNum}
    </button>
  );
}

// ── #472 Q2: checkbox + floating action bar (multi-select bulk complete) ─────
function ObligationCheckbox({
  checked,
  onChange,
  disabled,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      disabled={disabled}
      onClick={(e) => { e.stopPropagation(); onChange(!checked); }}
      className={`w-[18px] h-[18px] rounded-xs shrink-0 flex items-center justify-center border-2
        ${checked ? 'border-primary bg-primary' : 'border-border-strong bg-surface'}
        ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}
    >
      {checked && <span className="text-white text-[11px] font-bold leading-none">✓</span>}
    </button>
  );
}

function ObligationActionBar({
  count,
  completing,
  onComplete,
  onCancel,
}: {
  count: number;
  completing: boolean;
  onComplete: () => void;
  onCancel: () => void;
}) {
  if (count === 0) return null;
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-ink text-surface rounded-lg px-5 py-3 flex items-center gap-4 shadow-lg z-toast min-w-80">
      <span className="text-sm font-medium">{count} mục đã chọn</span>
      <div className="flex-1" />
      <button
        type="button"
        onClick={onComplete}
        disabled={completing}
        className="bg-primary text-white px-4 py-2 rounded-md text-sm font-semibold disabled:opacity-60"
      >
        {completing ? 'Đang xử lý…' : `Hoàn thành đã chọn (${count})`}
      </button>
      <button
        type="button"
        onClick={onCancel}
        disabled={completing}
        className="border border-ink-muted text-ink-muted px-3 py-2 rounded-md text-sm"
      >
        Bỏ chọn
      </button>
    </div>
  );
}

// ── #368 R5b: Signature presence badge ───────────────────────────────────────
function SignatureBadge({ hasSig, pages }: { hasSig?: boolean | null; pages?: number[] | null }) {
  if (hasSig == null) return null;
  if (hasSig) {
    const pageText = pages && pages.length > 0 ? `trang ${pages.join(', ')}` : '';
    // #485 Q1 (green-creep cleanup): "done" state = quiet gray, not celebratory green.
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-done-soft text-done">
        Đã ký{pageText && <span className="text-2xs opacity-75"> ({pageText})</span>}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-warning-soft text-warning">
      Chưa ký
    </span>
  );
}

// ── Fulfillment modal ────────────────────────────────────────────────────────
function FulfillModal({
  ob,
  open,
  onClose,
  onSubmit,
  submitting,
}: {
  ob: ObligationOut | null;
  open: boolean;
  onClose: () => void;
  onSubmit: (fulfilledAt: string, fulfilledBy: string) => void;
  submitting: boolean;
}) {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [actor, setActor] = useState('');
  useEffect(() => {
    if (open) {
      setDate(new Date().toISOString().slice(0, 10));
      setActor('');
    }
  }, [open]);
  if (!ob) return null;
  return (
    <Modal
      open={open}
      title="Đánh dấu hoàn thành"
      onClose={onClose}
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={submitting}>
            Hủy
          </Button>
          <Button
            onClick={() => onSubmit(date, actor)}
            loading={submitting}
            disabled={!date}
            testId="fulfill-confirm-btn"
          >
            Xác nhận hoàn thành
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <p className="text-sm text-ink-muted">{ob.description}</p>
        <div>
          <label className="block text-xs font-medium text-ink-muted uppercase mb-1">
            Ngày thực hiện *
          </label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-ink-muted uppercase mb-1">
            Người thực hiện (tùy chọn)
          </label>
          <Input
            value={actor}
            onChange={setActor}
            placeholder="Tên hoặc email người thực hiện"
          />
        </div>
      </div>
    </Modal>
  );
}

// ── #472: single obligation row — checkbox + no-emoji badges ─────────────────
function ObligationRow({
  ob,
  checked,
  onCheck,
  onFulfill,
  onJumpToClause,
  dim,
}: {
  ob: ObligationOut;
  checked: boolean;
  onCheck: (v: boolean) => void;
  onFulfill: (ob: ObligationOut) => void;
  onJumpToClause: (clauseNum: string) => void;
  dim?: boolean;
}) {
  const isDone = ob.status === 'done' || ob.status === 'cancelled';
  const isOverdue = temporalBucket(ob) === 'overdue';
  const canCheck = !isDone && ob.status !== 'waiting_trigger';
  const canFulfill = !isDone && ob.status !== 'waiting_trigger';
  const hasRecurrence = !!ob.recurrence && ob.recurrence !== 'once';

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 border-b border-border last:border-0
        ${dim || isDone ? 'opacity-55' : ''} ${checked ? 'bg-primary-soft/40' : ''}`}
    >
      <div className="pt-0.5">
        <ObligationCheckbox checked={checked} onChange={onCheck} disabled={!canCheck} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-sm font-medium text-ink ${isDone ? 'line-through' : ''}`}>
            {ob.description}
          </span>
          {isOverdue && ob.due_date && (
            <TextBadge className="bg-danger-soft text-danger">{overdueLabel(ob.due_date)}</TextBadge>
          )}
          {isDone && <StatusBadge status={ob.status} />}
        </div>
        <div className="flex items-center gap-2 flex-wrap mt-1">
          <CategoryChip obligationType={ob.obligation_type} />
          {ob.milestone_total && ob.milestone_total > 1 && ob.milestone_index != null && (
            <TextBadge>Đợt {ob.milestone_index}/{ob.milestone_total}</TextBadge>
          )}
          {ob.due_date && !isOverdue && !isDone && <TextBadge>{dueLabel(ob.due_date)}</TextBadge>}
          {!ob.due_date && hasRecurrence && (
            <TextBadge>{RECURRENCE_LABEL[ob.recurrence] || ob.recurrence}</TextBadge>
          )}
          {!ob.due_date && !hasRecurrence && !isDone && ob.status !== 'waiting_trigger' && (
            <TextBadge>Không thời hạn</TextBadge>
          )}
          <AmountDisplay raw={ob.amount_raw} />
          {ob.fulfilled_at && (
            <TextBadge className="bg-done-soft text-done">
              Hoàn thành {new Date(ob.fulfilled_at).toLocaleDateString('vi-VN')}
              {ob.fulfilled_by ? ` · ${ob.fulfilled_by}` : ''}
            </TextBadge>
          )}
          <SourceClauseLink clauseNum={ob.source_clause_num} onJump={onJumpToClause} />
        </div>
      </div>
      {canFulfill && (
        <div className="shrink-0">
          <button
            type="button"
            onClick={() => onFulfill(ob)}
            className="border border-border-strong bg-surface text-ink-body px-3 py-1 rounded-md text-2xs font-semibold hover:bg-surface-alt"
          >
            Hoàn thành
          </button>
        </div>
      )}
    </div>
  );
}

// ── #472 Q3: series card — collapsible, progress bar, next installment ───────
function SeriesCard({
  items,
  selected,
  onCheck,
  onFulfill,
  onJumpToClause,
}: {
  items: ObligationOut[];
  selected: Set<number>;
  onCheck: (id: number, v: boolean) => void;
  onFulfill: (ob: ObligationOut) => void;
  onJumpToClause: (clauseNum: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const total = items[0].milestone_total || items.length;
  const doneCount = items.filter((o) => o.status === 'done').length;
  const pct = total > 0 ? Math.round((doneCount / total) * 100) : 0;
  const sorted = [...items].sort((a, b) => (a.milestone_index || 0) - (b.milestone_index || 0));
  const nextItem = sorted.find((o) => o.status !== 'done' && o.status !== 'cancelled');
  const nextOverdue = !!nextItem && temporalBucket(nextItem) === 'overdue';
  const nextAmount = nextItem ? formatCurrency(nextItem.amount_raw) : null;

  return (
    <div className="border border-border rounded-lg mb-3 overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 bg-surface-alt text-left"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-ink">
              {labelFor(OBLIGATION_TYPE_LABELS, items[0].obligation_type)}
            </span>
            <TextBadge className="bg-primary-soft text-primary">{doneCount}/{total} hoàn thành</TextBadge>
            {nextOverdue && <TextBadge className="bg-danger-soft text-danger">Có đợt quá hạn</TextBadge>}
          </div>
          <div className="mt-2 h-1 rounded-full bg-surface-sunken overflow-hidden max-w-[200px]">
            <div
              className={`h-full rounded-full transition-all duration-base ${nextOverdue ? 'bg-danger' : 'bg-primary'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          {nextItem && (
            <div className="mt-2 text-sm text-ink-muted">
              Kế tiếp: Đợt {nextItem.milestone_index} — {nextItem.due_date ? new Date(nextItem.due_date).toLocaleDateString('vi-VN') : 'chưa có hạn'}
              {nextAmount && <span className="text-ink font-medium"> · {nextAmount}</span>}
            </div>
          )}
        </div>
        <span className="text-sm text-ink-muted shrink-0">{expanded ? 'Thu gọn' : 'Xem chi tiết'}</span>
      </button>
      {expanded && (
        <div>
          {sorted.map((ob) => (
            <ObligationRow
              key={ob.id}
              ob={ob}
              checked={selected.has(ob.id)}
              onCheck={(v) => onCheck(ob.id, v)}
              onFulfill={onFulfill}
              onJumpToClause={onJumpToClause}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── #472 Q4: "Chờ kích hoạt" row — waiting_trigger, separate from today's work ──
function WaitingTriggerRow({
  ob,
  onJumpToClause,
}: {
  ob: ObligationOut;
  onJumpToClause: (clauseNum: string) => void;
}) {
  const amount = formatCurrency(ob.amount_raw);
  return (
    <div className="flex items-start gap-3 px-4 py-3 border-b border-border last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-ink">{ob.description}</span>
        </div>
        <div className="text-sm text-ink-muted mt-1">
          Nếu &quot;{ob.trigger_condition || ob.milestone_trigger || '—'}&quot;
          {ob.trigger_delay_days != null && <span> — trong {ob.trigger_delay_days} ngày</span>}
        </div>
        <div className="flex items-center gap-2 mt-1 flex-wrap">
          <CategoryChip obligationType={ob.obligation_type} />
          {amount && <AmountDisplay raw={ob.amount_raw} />}
          {ob.obligor && <TextBadge>{ob.obligor}</TextBadge>}
          <SourceClauseLink clauseNum={ob.source_clause_num} onJump={onJumpToClause} />
        </div>
      </div>
      <button
        type="button"
        disabled
        title="Chưa hỗ trợ — cần API xác nhận sự kiện kích hoạt (Backend kickoff riêng)"
        className="border border-border-strong bg-surface text-ink-body px-3 py-1 rounded-md text-2xs font-semibold shrink-0 opacity-50 cursor-not-allowed"
      >
        Sự kiện đã xảy ra
      </button>
    </div>
  );
}

// ── #472 Q1: Settings nudge — replaces per-doc SelfPartyGate dropdown ─────────
function SettingsNudge({ hasLegalName }: { hasLegalName: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 flex-wrap p-4 rounded-lg bg-warning-soft border border-warning/20 mb-4">
      <div>
        <div className="text-sm font-semibold text-ink">
          {hasLegalName
            ? 'Xác nhận tài liệu để áp dụng chiều nghĩa vụ'
            : 'Chưa xác định được chiều nghĩa vụ'}
        </div>
        <div className="text-xs text-ink-muted mt-0.5">
          {hasLegalName
            ? 'Pháp nhân đã được đặt — nhấn "Xác nhận tài liệu này" ở cuối trang để phân biệt nghĩa vụ và quyền lợi.'
            : 'Servanda cần biết tên pháp nhân của bạn để tự phân biệt nghĩa vụ và quyền lợi.'}
        </div>
      </div>
      <Link
        to="/admin/settings"
        className="px-4 py-2 rounded-md text-sm font-semibold text-primary bg-surface border border-border-strong hover:bg-surface-alt shrink-0"
      >
        {hasLegalName ? 'Kiểm tra pháp nhân' : 'Sửa pháp nhân trong Cài đặt'}
      </Link>
    </div>
  );
}

// ── #472: collapsible section header ──────────────────────────────────────────
function SectionHeader({
  title,
  subtitle,
  count,
  dotClassName,
  badgeClassName,
  collapsed,
  onToggle,
}: {
  title: string;
  subtitle?: string;
  count?: number;
  dotClassName?: string;
  badgeClassName?: string;
  collapsed?: boolean;
  onToggle?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={!onToggle}
      className="w-full flex items-center gap-2 py-3 bg-transparent text-left disabled:cursor-default"
    >
      {dotClassName && <span className={`w-2 h-2 rounded-full shrink-0 ${dotClassName}`} />}
      <span className="text-lg font-semibold text-ink">{title}</span>
      {count !== undefined && <TextBadge className={badgeClassName}>{count}</TextBadge>}
      {subtitle && <span className="text-sm text-ink-muted font-normal">{subtitle}</span>}
      {onToggle && (
        <span className="ml-auto text-sm text-ink-muted">{collapsed ? 'Mở rộng' : 'Thu gọn'}</span>
      )}
    </button>
  );
}

// ── #472: temporal sub-header (Quá hạn / Tuần này / Sắp tới) ─────────────────
function BucketHeader({ bucket, count }: { bucket: 'overdue' | 'this_week' | 'upcoming'; count: number }) {
  const MAP: Record<string, { label: string; dot: string; text: string }> = {
    overdue: { label: 'Quá hạn', dot: 'bg-danger', text: 'text-danger' },
    this_week: { label: 'Tuần này', dot: 'bg-warning', text: 'text-warning' },
    upcoming: { label: 'Sắp tới', dot: 'bg-info', text: 'text-info' },
  };
  const b = MAP[bucket];
  if (!b || count === 0) return null;
  return (
    <div className="flex items-center gap-2 px-4 py-2 border-b border-border">
      <span className={`w-1.5 h-1.5 rounded-full ${b.dot}`} />
      <span className={`text-sm font-semibold ${b.text}`}>{b.label}</span>
      <span className="text-xs text-ink-muted">{count}</span>
    </div>
  );
}

// ── #373 R10: Cross-ref inline rendering ─────────────────────────────────────

function renderClauseContent(
  content: string,
  clauseRefs: CrossRefOut[],
  onNavigateDoc?: (docId: number) => void,
): React.ReactNode {
  if (clauseRefs.length === 0) return content;

  type Segment = { text: string; ref?: CrossRefOut };
  const segments: Segment[] = [];
  let remaining = content;

  const sortedRefs = [...clauseRefs].sort((a, b) => {
    const posA = content.indexOf(a.ref_text);
    const posB = content.indexOf(b.ref_text);
    return (posA === -1 ? Infinity : posA) - (posB === -1 ? Infinity : posB);
  });

  for (const ref of sortedRefs) {
    const idx = remaining.indexOf(ref.ref_text);
    if (idx === -1) continue;
    if (idx > 0) segments.push({ text: remaining.slice(0, idx) });
    segments.push({ text: ref.ref_text, ref });
    remaining = remaining.slice(idx + ref.ref_text.length);
  }
  if (remaining) segments.push({ text: remaining });

  return (
    <>
      {segments.map((seg, i) => {
        if (!seg.ref) return <span key={i}>{seg.text}</span>;
        if (seg.ref.is_orphan) {
          return (
            <span
              key={i}
              className="text-danger font-medium underline decoration-wavy cursor-default"
              title={`Tham chiếu không tìm thấy: ${seg.ref.ref_text}`}
            >
              {seg.text}
            </span>
          );
        }
        if (seg.ref.ref_type === 'appendix' && seg.ref.target_doc_id != null) {
          return (
            <button
              key={i}
              type="button"
              className="text-primary font-medium underline cursor-pointer hover:text-primary-hover"
              onClick={() => onNavigateDoc?.(seg.ref!.target_doc_id!)}
              title={`Mở phụ lục (tài liệu #${seg.ref.target_doc_id})`}
            >
              {seg.text}
            </button>
          );
        }
        return (
          <button
            key={i}
            type="button"
            className="text-primary font-medium underline cursor-pointer hover:text-primary-hover"
            onClick={() => {
              const el = document.getElementById(`clause-${seg.ref!.target_clause_id}`);
              if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }
            }}
          >
            {seg.text}
          </button>
        );
      })}
    </>
  );
}

// ── #373 R10: Orphan reference warning panel ──────────────────────────────────
function OrphanRefPanel({
  orphanRefs,
  clauses,
  onResolve,
  resolving,
}: {
  orphanRefs: CrossRefOut[];
  clauses: ClauseOut[];
  onResolve: () => void;
  resolving: boolean;
}) {
  const [showAll, setShowAll] = useState(false);
  if (orphanRefs.length === 0) return null;
  const clauseMap = new Map(clauses.map((c) => [c.id, c]));
  const visible = showAll ? orphanRefs : orphanRefs.slice(0, 5);
  const hasMore = orphanRefs.length > 5;
  return (
    <div className="mb-4 rounded-lg bg-danger-soft border border-danger/30 p-4">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-ink mb-2">
            {orphanRefs.length} tham chiếu không tìm thấy
          </div>
          <div className={`space-y-1 ${!showAll && hasMore ? 'max-h-40 overflow-hidden' : ''}`}>
            {visible.map((ref) => {
              const srcClause = clauseMap.get(ref.source_clause_id);
              const srcLabel = srcClause
                ? (srcClause.clause_num && srcClause.title
                    ? `${srcClause.clause_num}. ${srcClause.title}`
                    : srcClause.title || srcClause.clause_num || `#${srcClause.id}`)
                : `#${ref.source_clause_id}`;
              return (
                <div key={ref.id} className="flex items-center gap-2 flex-wrap text-xs">
                  <span className="text-danger font-medium">{ref.ref_text}</span>
                  <span className="text-ink-muted">trong {srcLabel}</span>
                  <span className="text-ink-subtle">— có thể phụ lục chưa được tải lên hoặc không tồn tại</span>
                </div>
              );
            })}
          </div>
          {hasMore && (
            <button
              type="button"
              className="mt-2 text-2xs text-danger hover:underline"
              onClick={() => setShowAll((v) => !v)}
            >
              {showAll ? 'Thu gọn' : `Xem tất cả (${orphanRefs.length})`}
            </button>
          )}
          <button
            type="button"
            className="mt-3 text-2xs text-danger hover:underline disabled:opacity-50"
            onClick={onResolve}
            disabled={resolving}
          >
            {resolving ? 'Đang phân giải lại…' : 'Thử phân giải lại →'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── #368 R5: Clause content renderer — markdown tables + plain text fallback ──
const REMARK_PLUGINS = [remarkGfm];
const REHYPE_PLUGINS = [rehypeSanitize];
const MD_TABLE_SEP = /\|[\s-:]+\|/;

const MD_COMPONENTS = {
  table: ({ children }: { children?: React.ReactNode }) => (
    <table className="w-full border-collapse text-sm my-3 border border-border">{children}</table>
  ),
  th: ({ children }: { children?: React.ReactNode }) => (
    <th className="text-left p-2 font-semibold bg-surface-alt text-ink border-b border-border">{children}</th>
  ),
  td: ({ children }: { children?: React.ReactNode }) => (
    <td className="p-2 text-ink border-b border-border">{children}</td>
  ),
  p: ({ children }: { children?: React.ReactNode }) => (
    <p className="whitespace-pre-wrap mb-2">{children}</p>
  ),
};

function ClauseContent({
  content,
  crossRefs,
  onNavigateDoc,
}: {
  content: string;
  crossRefs?: CrossRefOut[];
  onNavigateDoc?: (docId: number) => void;
}) {
  const hasTable = content.includes('|') && MD_TABLE_SEP.test(content);
  if (hasTable) {
    return (
      <div className="text-sm text-ink leading-relaxed whitespace-pre-wrap font-serif">
        <ReactMarkdown
          remarkPlugins={REMARK_PLUGINS}
          rehypePlugins={REHYPE_PLUGINS}
          components={MD_COMPONENTS}
        >
          {content}
        </ReactMarkdown>
      </div>
    );
  }
  const clauseRefs = crossRefs ?? [];
  if (clauseRefs.length > 0) {
    return (
      <p className="text-sm text-ink leading-relaxed whitespace-pre-wrap font-serif">
        {renderClauseContent(content, clauseRefs, onNavigateDoc)}
      </p>
    );
  }
  return (
    <p className="text-sm text-ink leading-relaxed whitespace-pre-wrap font-serif">{content}</p>
  );
}

// ── Clause accordion item (Phase 2 — inline edit, D-07) ─────────────────────
function ClauseItem({
  clause,
  defaultOpen,
  docId,
  onSaved,
  crossRefs,
  onNavigateDoc,
}: {
  clause: ClauseOut;
  defaultOpen: boolean;
  docId: number;
  onSaved: (updated: ClauseOut) => void;
  crossRefs?: CrossRefOut[];
  onNavigateDoc?: (docId: number) => void;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string>('');
  const [showOriginal, setShowOriginal] = useState(false);

  const title = clause.clause_num && clause.title
    ? `${clause.clause_num}. ${clause.title}`
    : clause.title || clause.clause_num || `Điều khoản #${clause.id}`;

  const startEdit = () => {
    setDraft(clause.content);
    setEditing(true);
    setOpen(true);
  };

  const cancelEdit = () => {
    setEditing(false);
    setDraft('');
  };

  const saveEdit = async () => {
    setSaving(true);
    setSaveError('');
    try {
      const res = await apiFetch<ClausePatchOut>(
        `/documents/${docId}/clauses/${clause.id}`,
        { method: 'PATCH', body: JSON.stringify({ content: draft }) }
      );
      onSaved({ ...clause, ...res });
      setEditing(false);
      setDraft('');
      setShowOriginal(false);
    } catch (err) {
      setSaveError((err as ApiError).message || 'Lưu điều khoản thất bại');
    } finally {
      setSaving(false);
    }
  };

  const displayContent =
    showOriginal && clause.original_content ? clause.original_content : clause.content;
  const clauseRefs = (crossRefs ?? []).filter((r) => r.source_clause_id === clause.id);

  return (
    <div id={`clause-${clause.id}`} className="border-b border-border last:border-0">
      <button
        className="w-full flex items-center justify-between py-3 text-left gap-2 hover:bg-surface-hover transition-colors"
        onClick={() => !editing && setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="text-sm font-medium text-ink">{title}</span>
        <div className="flex items-center gap-2 flex-shrink-0">
          {clause.edited_by_user && (
            <span className="text-2xs px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium">
              đã sửa
            </span>
          )}
          {clause.page_num != null && (
            <span className="text-2xs text-ink-muted">tr.{clause.page_num}</span>
          )}
          <span className="text-ink-muted text-xs">{open ? '▲' : '▼'}</span>
        </div>
      </button>
      {open && (
        <div className="pb-3">
          {editing ? (
            <div className="flex flex-col gap-2">
              <textarea
                className="w-full text-sm border border-border rounded p-2 leading-relaxed resize-y min-h-[8rem] focus:outline-none focus:ring-1 focus:ring-primary"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                autoFocus
              />
              {saveError && (
                <p className="text-xs text-danger">{saveError}</p>
              )}
              <div className="flex items-center gap-2">
                <Button size="sm" onClick={saveEdit} loading={saving}>
                  Lưu
                </Button>
                <Button size="sm" variant="ghost" onClick={cancelEdit} disabled={saving}>
                  Hủy
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-1">
              <ClauseContent content={displayContent} crossRefs={clauseRefs} onNavigateDoc={onNavigateDoc} />
              <div className="flex items-center gap-3 pt-1 flex-wrap">
                {clause.original_content && (
                  <button
                    className="text-2xs text-primary hover:underline"
                    onClick={() => setShowOriginal((v) => !v)}
                  >
                    {showOriginal ? 'Xem bản đã sửa' : 'Xem bản gốc (AI)'}
                  </button>
                )}
                {clause.edited_by_user && clause.edited_at && (
                  <span className="text-2xs text-ink-muted">
                    Sửa bởi {clause.edited_by_user} ·{' '}
                    {new Date(clause.edited_at).toLocaleDateString('vi-VN')}
                  </span>
                )}
                <button
                  className="text-2xs text-ink-muted hover:text-primary ml-auto"
                  onClick={startEdit}
                >
                  Sửa nội dung
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Phase 3: Re-read banner ──────────────────────────────────────────────────
function ReReadBanner({ onReRead, reReading }: { onReRead: () => void; reReading: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 p-3 mb-4 rounded-lg bg-primary/5 border border-primary/20 text-sm">
      <div className="flex items-center gap-2">
        <span className="text-ink">
          Bạn đã sửa điều khoản — Khế có thể bóc lại nghĩa vụ từ nội dung mới.
        </span>
      </div>
      <Button size="sm" onClick={onReRead} loading={reReading}>
        Bóc lại
      </Button>
    </div>
  );
}

// ── Phase 3: Stale-edit warning on obligations tab ───────────────────────────
function StaleEditBanner({ onGoToClauses }: { onGoToClauses: () => void }) {
  return (
    <div className="flex items-center gap-3 p-3 mb-4 rounded-lg bg-warning-soft border border-warning-border text-sm">
      <span className="text-warning flex-1">
        Có điều khoản đã sửa — nghĩa vụ có thể chưa phản ánh nội dung mới.
      </span>
      <button className="text-2xs text-warning underline" onClick={onGoToClauses}>
        Xem điều khoản →
      </button>
    </div>
  );
}

// ── #312 D-07 audit drawer: slide-in event history ───────────────────────────

const EVENT_LABELS: Record<string, string> = {
  'document:document_uploaded': 'Tải lên tài liệu',
  'document:document_field_edited': 'Sửa trường tài liệu',
  'document:clause_edited': 'Sửa điều khoản',
  'document:self_party_confirmed': 'Xác nhận bên mình',
  'document:document_confirmed_by_user': 'Xác nhận tài liệu',
  'document:doc_type_corrected': 'Sửa loại hợp đồng',
  'document:clause_re_derived': 'Đọc lại điều khoản',
  'document:extraction_retriggered': 'Trích xuất lại',
  'document:re_read_triggered': 'Kích hoạt đọc lại',
  'document:extraction_performed': 'Trích xuất hoàn tất',
  'document:extraction_failed': 'Trích xuất lỗi',
  'document:extraction_two_pass_completed': 'Trích xuất 2 lượt hoàn tất',
  'document:definition_edited': 'Sửa định nghĩa',
  'document:definition_deleted': 'Xóa định nghĩa',
  'obligation:updated': 'Cập nhật nghĩa vụ',
  'obligation:evidence_attached': 'Đính kèm minh chứng',
  'obligation:reminder_snoozed': 'Hoãn nhắc',
};

function eventLabel(ev: EventOut): string {
  const key = `${ev.entity_type}:${ev.event_type}`;
  if (ev.entity_type === 'obligation' && ev.event_type === 'updated') {
    return describeObligationUpdate(ev.payload);
  }
  return EVENT_LABELS[key] || `${ev.entity_type}:${ev.event_type}`;
}

function describeObligationUpdate(payload: Record<string, unknown> | null): string {
  if (!payload) return 'Cập nhật nghĩa vụ';
  const newStatus = payload.new_status as string | undefined;
  const oldStatus = payload.old_status as string | undefined;
  if (newStatus === 'done' && payload.fulfilled_at) return 'Hoàn thành nghĩa vụ';
  if (oldStatus === 'done' && newStatus !== 'done') return 'Hoàn tác hoàn thành';
  if (newStatus) return `Đổi trạng thái → ${newStatus}`;
  return 'Cập nhật nghĩa vụ';
}

function formatEventTime(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function PayloadDiff({ payload }: { payload: Record<string, unknown> | null }) {
  if (!payload || typeof payload !== 'object') return null;
  const entries = Object.entries(payload);
  const oldNew = entries.find(([k]) => k === 'old_value' || k === 'old_content');
  const newVal = entries.find(([k]) => k === 'new_value' || k === 'new_content');
  if (oldNew && newVal) {
    return (
      <div className="text-xs mt-1">
        <span className="text-danger line-through">{String(oldNew[1] ?? '')}</span>
        <span className="text-ink-muted mx-1">→</span>
        <span className="text-done">{String(newVal[1] ?? '')}</span>
      </div>
    );
  }
  return (
    <div className="text-xs text-ink-muted mt-1">
      {entries.map(([k, v]) => (
        <div key={k}>
          <span className="font-medium">{k}:</span> {String(v ?? '')}
        </div>
      ))}
    </div>
  );
}

function AuditDrawer({ docId, open, onClose }: { docId: number; open: boolean; onClose: () => void }) {
  const [items, setItems] = useState<EventOut[]>([]);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const limit = 50;

  const load = useCallback(async () => {
    if (!open || !docId) return;
    setLoading(true);
    setError('');
    try {
      const res = await apiFetch<EventListOut>(`/documents/${docId}/events?limit=${limit}&offset=${offset}`);
      setItems((prev) => (offset === 0 ? res.items : [...prev, ...res.items]));
      setTotal(res.total);
    } catch (err) {
      setError((err as ApiError).message || 'Không thể tải lịch sử chỉnh sửa');
    } finally {
      setLoading(false);
    }
  }, [open, docId, offset]);

  useEffect(() => {
    if (!open) return;
    setOffset(0);
  }, [open]);

  useEffect(() => {
    if (open) load();
  }, [open, offset, load]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const hasMore = items.length < total;
  const loadMore = () => setOffset((prev) => prev + limit);

  const handleBackdropClick = (e: MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div
      className={`fixed inset-0 z-modal transition-opacity duration-200 ${open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
      onClick={handleBackdropClick}
      aria-hidden={!open}
    >
      <div className="absolute inset-0 bg-black/50" />
      <div
        className={`absolute top-0 right-0 h-full w-[420px] max-w-full bg-surface shadow-xl border-l border-border flex flex-col transition-transform duration-200 ease-out ${open ? 'translate-x-0' : 'translate-x-full'}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="audit-drawer-title"
      >
        <div className="flex items-center justify-between gap-3 p-4 border-b border-border">
          <div>
            <h2 id="audit-drawer-title" className="text-lg font-semibold text-ink">Lịch sử chỉnh sửa</h2>
            <p className="text-2xs text-ink-muted">{total} sự kiện</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-md text-sm font-semibold text-ink-body border border-border-strong hover:bg-surface-alt"
          >
            Đóng
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {error && <Toast kind="error" className="mb-4">{error}</Toast>}

          {items.length === 0 && !loading && !error && (
            <div className="text-sm text-ink-muted text-center py-8">Chưa có sự kiện nào</div>
          )}

          <div className="space-y-3">
            {items.map((ev) => (
              <div key={ev.id} className="rounded-lg border border-border p-3">
                <div className="flex items-start justify-between gap-2 flex-wrap">
                  <span className="text-sm font-semibold text-ink">{eventLabel(ev)}</span>
                  <span className="text-2xs text-ink-muted shrink-0">{formatEventTime(ev.created_at)}</span>
                </div>
                <div className="text-2xs text-ink-muted mt-1">
                  Bởi {ev.actor === 'system' ? 'Hệ thống' : (ev.actor ?? 'không rõ')}
                </div>
                <PayloadDiff payload={ev.payload} />
              </div>
            ))}
          </div>

          {hasMore && (
            <div className="mt-4 text-center">
              <button
                type="button"
                onClick={loadMore}
                disabled={loading}
                className="px-4 py-2 rounded-md text-sm font-semibold border border-border-strong text-ink-body hover:bg-surface-alt disabled:opacity-50"
              >
                {loading ? 'Đang tải…' : 'Tải thêm'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Phase 3: Diff confirm modal (D-02) ───────────────────────────────────────
function DiffConfirmModal({
  open,
  diffs,
  onClose,
  onConfirm,
  submitting,
}: {
  open: boolean;
  diffs: ReReadDiff[];
  onClose: () => void;
  onConfirm: (toApply: number[]) => Promise<void>;
  submitting: boolean;
}) {
  const removeDiffs = diffs.filter((d) => d.action === 'remove');
  const infoDiffs = diffs.filter((d) => d.action !== 'remove');

  // Default: cancel non-protected removes; keep protected removes
  const [cancelSet, setCancelSet] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!open) return;
    const defaultCancel = new Set(
      removeDiffs
        .map((d, i) => ({ d, i }))
        .filter(({ d }) => !d.protected && d.obligation_id != null)
        .map(({ d }) => d.obligation_id as number)
    );
    setCancelSet(defaultCancel);
  }, [open, diffs]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleCancel = (obligationId: number) => {
    setCancelSet((prev) => {
      const next = new Set(prev);
      if (next.has(obligationId)) next.delete(obligationId);
      else next.add(obligationId);
      return next;
    });
  };

  const actionLabel = (action: string) => {
    if (action === 'add') return '+ Thêm mới';
    if (action === 'update') return 'Cập nhật';
    if (action === 'remove') return '− Xóa';
    return action;
  };

  const handleConfirm = async () => {
    await onConfirm(Array.from(cancelSet));
  };

  return (
    <Modal
      open={open}
      title={`Khế phát hiện ${diffs.length} thay đổi nghĩa vụ`}
      onClose={() => !submitting && onClose()}
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={submitting}>
            Bỏ qua
          </Button>
          <Button onClick={handleConfirm} loading={submitting}>
            Xác nhận ({cancelSet.size} hủy)
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-3 max-h-[60vh] overflow-y-auto">
        {removeDiffs.length > 0 && (
          <div>
            <p className="text-xs font-medium text-ink-muted uppercase mb-2">Xóa nghĩa vụ</p>
            {removeDiffs.map((diff) => {
              const id = diff.obligation_id!;
              const selected = cancelSet.has(id);
              return (
                <div
                  key={`remove-${id}`}
                  className={`p-3 rounded-lg border mb-2 transition-colors ${
                    selected ? 'border-danger/30 bg-danger-soft' : 'border-border bg-surface-muted'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="text-xs font-medium text-danger">
                          {actionLabel(diff.action)}
                        </span>
                        {diff.protected && (
                          <span className="text-2xs px-1.5 py-0.5 rounded bg-warning-soft text-warning font-medium">
                            Thủ công
                          </span>
                        )}
                        {diff.source_clause_num && (
                          <span className="text-2xs text-ink-muted">
                            Điều {diff.source_clause_num}
                          </span>
                        )}
                      </div>
                      {diff.description && (
                        <p className="text-sm text-ink leading-snug">{diff.description}</p>
                      )}
                      {diff.due_date && (
                        <p className="text-2xs text-ink-muted mt-1">
                          Hạn: {new Date(diff.due_date).toLocaleDateString('vi-VN')}
                        </p>
                      )}
                    </div>
                    {!diff.protected && (
                      <button
                        className={`flex-shrink-0 text-xs px-2 py-1 rounded border transition-colors ${
                          selected
                            ? 'border-danger/30 text-danger bg-danger-soft'
                            : 'border-border text-ink-muted'
                        }`}
                        onClick={() => toggleCancel(id)}
                        disabled={submitting}
                      >
                        {selected ? 'Hủy' : 'Giữ lại'}
                      </button>
                    )}
                    {diff.protected && (
                      <span className="flex-shrink-0 text-xs px-2 py-1 text-ink-muted">
                        Giữ của bạn
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
        {infoDiffs.length > 0 && (
          <div>
            <p className="text-xs font-medium text-ink-muted uppercase mb-2">
              Thay đổi khác (cần cập nhật thủ công)
            </p>
            {infoDiffs.map((diff, i) => (
              <div key={`info-${i}`} className="p-3 rounded-lg border border-border mb-2">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="text-xs font-medium text-ink">{actionLabel(diff.action)}</span>
                  {diff.obligation_type && (
                    <span className="text-2xs text-ink-muted">
                      {labelFor(OBLIGATION_TYPE_LABELS, diff.obligation_type)}
                    </span>
                  )}
                  {diff.source_clause_num && (
                    <span className="text-2xs text-ink-muted">Điều {diff.source_clause_num}</span>
                  )}
                </div>
                {diff.description && (
                  <p className="text-sm text-ink leading-snug">{diff.description}</p>
                )}
                {diff.old_value && diff.new_value && (
                  <div className="mt-1 flex gap-2 text-2xs flex-wrap">
                    <span className="text-danger line-through">{diff.old_value}</span>
                    <span>→</span>
                    <span className="text-done">{diff.new_value}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}

// ── Tab: Tổng quan ───────────────────────────────────────────────────────────
function TabOverview({
  doc,
  docTypeGroupTerm,
  canonicalTerms,
  typeSpecificTerms,
  editingTermId,
  editValue,
  saving,
  remapping,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onSetEditValue,
  onSetPendingType,
}: {
  doc: DocumentDetailOut;
  docTypeGroupTerm: TermOut | null;
  canonicalTerms: TermOut[];
  typeSpecificTerms: TermOut[];
  editingTermId: number | null;
  editValue: string;
  saving: boolean;
  remapping: boolean;
  onStartEdit: (t: TermOut) => void;
  onCancelEdit: () => void;
  onSaveEdit: (id: number) => void;
  onSetEditValue: (v: string) => void;
  onSetPendingType: (v: string | null) => void;
}) {
  const renderTerm = (term: TermOut) => (
    <div
      key={term.id}
      className="flex items-start justify-between gap-3 py-2 border-b border-border last:border-0"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-semibold text-ink">
            {labelFor(FIELD_LABELS, term.field_name)}
          </span>
          {term.needs_review && <Badge kind="needs_review">Cần kiểm tra</Badge>}
        </div>
        {editingTermId === term.id ? (
          <div className="flex gap-2 items-center">
            <Input value={editValue} onChange={onSetEditValue} className="flex-1" />
            <Button size="sm" onClick={() => onSaveEdit(term.id)} loading={saving}>
              Lưu
            </Button>
            <Button size="sm" variant="ghost" onClick={onCancelEdit}>
              Hủy
            </Button>
          </div>
        ) : (
          <div className="text-sm text-ink">{term.field_value || '—'}</div>
        )}
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {term.confidence !== null && <ConfidenceMeter value={term.confidence} />}
        {editingTermId !== term.id && (
          <Button size="sm" variant="ghost" onClick={() => onStartEdit(term)}>
            Sửa
          </Button>
        )}
      </div>
    </div>
  );

  return (
    <div>
      {docTypeGroupTerm && doc.terms.length > 0 && (
        <Card title="Loại hợp đồng" className="mb-4">
          <div className="flex items-end gap-3 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <label
                htmlFor="doc-type-group-select"
                className="text-xs font-medium text-ink-muted uppercase mb-1 block"
              >
                Loại hợp đồng
              </label>
              <select
                id="doc-type-group-select"
                data-testid="doc-type-group-select"
                value={docTypeGroupTerm.field_value || ''}
                disabled={doc.clause_count === 0 || remapping || editingTermId !== null}
                title={
                  doc.clause_count === 0
                    ? 'Chưa có clause text — không thể map lại loại tài liệu này'
                    : undefined
                }
                onChange={(e) => {
                  const v = e.target.value;
                  if (v && v !== docTypeGroupTerm.field_value) onSetPendingType(v);
                }}
                className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm text-ink disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                {DOC_TYPE_GROUPS.map((t) => (
                  <option key={t} value={t}>
                    {labelFor(DOC_TYPE_GROUP_LABELS, t)}
                  </option>
                ))}
              </select>
            </div>
            {remapping && (
              <span className="text-xs text-ink-muted pb-2">Đang map lại…</span>
            )}
          </div>
          <p className="text-2xs text-ink-muted mt-2">
            {doc.clause_count === 0
              ? 'Tài liệu chưa có nội dung điều khoản (clause) nên không thể map lại loại.'
              : 'Chọn lại nếu phân loại sai — Khế map lại các trường từ nội dung điều khoản, không tính thêm quota.'}
          </p>
        </Card>
      )}

      {doc.contract_term && (
        <Card className="mb-4">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div>
              <p className="text-2xs text-ink-muted uppercase tracking-wide font-medium mb-1">
                Thời hạn hợp đồng
              </p>
              <p className="text-sm text-ink">{doc.contract_term}</p>
            </div>
            <LifecycleBadge status={doc.lifecycle_status} />
          </div>
        </Card>
      )}

      {doc.terms.length === 0 ? (
        <Card title="Thông tin trích xuất">
          <EmptyState
            title="Chưa có thông tin"
            description="Tài liệu đang được xử lý. Quay lại sau vài phút."
          />
        </Card>
      ) : (
        <>
          {canonicalTerms.length > 0 && (
            <Card title="Thông tin chung" className="mb-4">
              <div className="space-y-3">{canonicalTerms.map(renderTerm)}</div>
            </Card>
          )}
          {typeSpecificTerms.length > 0 && (
            <Card title="Thông tin theo loại" className="mb-4">
              <div className="space-y-3">{typeSpecificTerms.map(renderTerm)}</div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

// ── Tab: Nghĩa vụ & Quyền lợi (#472 R472 — 3-axis IA: direction × temporal × series) ──
function TabObligations({
  doc,
  onFulfill,
  onBulkComplete,
  bulkCompleting,
  onJumpToClause,
  hasLegalName,
}: {
  doc: DocumentDetailOut;
  onFulfill: (ob: ObligationOut) => void;
  onBulkComplete: (ids: number[]) => Promise<void>;
  bulkCompleting: boolean;
  onJumpToClause: (clauseNum: string) => void;
  hasLegalName: boolean;
}) {
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [showDone, setShowDone] = useState(false);
  const [showWaiting, setShowWaiting] = useState(true);
  const [showNull, setShowNull] = useState(true);

  const toggleCheck = (id: number, val: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (val) next.add(id); else next.delete(id);
      return next;
    });
  };

  if (doc.obligations.length === 0) {
    return (
      <EmptyState
        title="Chưa có nghĩa vụ nào"
        description="Tài liệu chưa có nghĩa vụ được bóc tách."
      />
    );
  }

  const obligations = doc.obligations;
  const nghiaVu = obligations.filter(
    (o) => o.direction === 'nghĩa_vụ' && o.status !== 'waiting_trigger' && o.status !== 'done' && o.status !== 'cancelled'
  );
  const quyenLoi = obligations.filter(
    (o) => o.direction === 'quyền_lợi' && o.status !== 'waiting_trigger' && o.status !== 'done' && o.status !== 'cancelled'
  );
  const waiting = obligations.filter((o) => o.status === 'waiting_trigger');
  const done = obligations.filter((o) => o.status === 'done' || o.status === 'cancelled');
  const nullDir = obligations.filter(
    (o) => o.direction === null && o.status !== 'waiting_trigger' && o.status !== 'done' && o.status !== 'cancelled'
  );

  const BUCKETS: Array<'overdue' | 'this_week' | 'upcoming'> = ['overdue', 'this_week', 'upcoming'];

  // Series render ONCE, positioned by its next actionable item's temporal bucket
  // (a 14-installment series can have members across all 3 buckets).
  function renderDirectionSection(items: ObligationOut[], title: string, subtitle: string) {
    if (items.length === 0) return null;

    const seriesIds = [...new Set(items.filter((o) => o.milestone_series_id).map((o) => o.milestone_series_id as string))];
    const standaloneItems = items.filter((o) => !o.milestone_series_id);

    const seriesByBucket: Record<string, string[]> = { overdue: [], this_week: [], upcoming: [] };
    seriesIds.forEach((sid) => {
      const allSeriesItems = obligations.filter((o) => o.milestone_series_id === sid);
      const sorted = [...allSeriesItems].sort((a, b) => (a.milestone_index || 0) - (b.milestone_index || 0));
      const next = sorted.find((o) => o.status !== 'done' && o.status !== 'cancelled');
      const bucket = next ? temporalBucket(next) : 'upcoming';
      seriesByBucket[BUCKETS.includes(bucket as 'overdue' | 'this_week' | 'upcoming') ? bucket : 'upcoming'].push(sid);
    });

    const standaloneByBucket: Record<string, ObligationOut[]> = {};
    BUCKETS.forEach((b) => { standaloneByBucket[b] = standaloneItems.filter((o) => temporalBucket(o) === b); });

    return (
      <div className="mb-6">
        <SectionHeader title={title} subtitle={subtitle} count={items.length} />
        <div className="border border-border rounded-lg overflow-hidden">
          {BUCKETS.map((bk) => {
            const seriesInBucket = seriesByBucket[bk];
            const standalone = standaloneByBucket[bk];
            const visibleCount = seriesInBucket.length + standalone.length;
            if (visibleCount === 0) return null;
            return (
              <div key={bk}>
                <BucketHeader bucket={bk} count={visibleCount} />
                {seriesInBucket.map((sid) => (
                  <div key={sid} className="px-3 py-2">
                    <SeriesCard
                      items={obligations.filter((o) => o.milestone_series_id === sid)}
                      selected={selected}
                      onCheck={toggleCheck}
                      onFulfill={onFulfill}
                      onJumpToClause={onJumpToClause}
                    />
                  </div>
                ))}
                {standalone.map((ob) => (
                  <ObligationRow
                    key={ob.id}
                    ob={ob}
                    checked={selected.has(ob.id)}
                    onCheck={(v) => toggleCheck(ob.id, v)}
                    onFulfill={onFulfill}
                    onJumpToClause={onJumpToClause}
                  />
                ))}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div>
      {nullDir.length > 0 && (
        <div className="mb-5">
          <SettingsNudge hasLegalName={hasLegalName} />
          <SectionHeader
            title="Cần xác nhận chiều"
            count={nullDir.length}
            dotClassName="bg-warning"
            badgeClassName="bg-warning-soft text-warning"
            collapsed={!showNull}
            onToggle={() => setShowNull((v) => !v)}
          />
          {showNull && (
            <div className="border border-border rounded-lg overflow-hidden">
              {nullDir.map((ob) => (
                <ObligationRow
                  key={ob.id}
                  ob={ob}
                  checked={selected.has(ob.id)}
                  onCheck={(v) => toggleCheck(ob.id, v)}
                  onFulfill={onFulfill}
                  onJumpToClause={onJumpToClause}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {renderDirectionSection(nghiaVu, 'Nghĩa vụ của bạn', 'phải làm')}
      {renderDirectionSection(quyenLoi, 'Quyền lợi của bạn', 'được hưởng')}

      {waiting.length > 0 && (
        <div className="mb-6">
          <SectionHeader
            title="Chờ kích hoạt"
            subtitle="khi điều kiện xảy ra"
            count={waiting.length}
            dotClassName="bg-warning"
            badgeClassName="bg-warning-soft text-warning"
            collapsed={!showWaiting}
            onToggle={() => setShowWaiting((v) => !v)}
          />
          {showWaiting && (
            <div className="border border-border rounded-lg overflow-hidden">
              {waiting.map((ob) => (
                <WaitingTriggerRow key={ob.id} ob={ob} onJumpToClause={onJumpToClause} />
              ))}
            </div>
          )}
        </div>
      )}

      {done.length > 0 && (
        <div className="mb-6">
          <SectionHeader
            title="Đã hoàn thành"
            count={done.length}
            dotClassName="bg-done"
            badgeClassName="bg-done-soft text-done"
            collapsed={!showDone}
            onToggle={() => setShowDone((v) => !v)}
          />
          {showDone && (
            <div className="border border-border rounded-lg overflow-hidden">
              {done.map((ob) => (
                <ObligationRow
                  key={ob.id}
                  ob={ob}
                  checked={false}
                  onCheck={() => {}}
                  onFulfill={onFulfill}
                  onJumpToClause={onJumpToClause}
                  dim
                />
              ))}
            </div>
          )}
        </div>
      )}

      <ObligationActionBar
        count={selected.size}
        completing={bulkCompleting}
        onComplete={async () => {
          // Keep selection (and the action bar) visible through the request so
          // the "Đang xử lý…" state is reachable — only clear on completion.
          await onBulkComplete([...selected]);
          setSelected(new Set());
        }}
        onCancel={() => setSelected(new Set())}
      />
    </div>
  );
}

// ── Clause hierarchy tree (#365 R3) ─────────────────────────────────────────
interface ClauseNode extends ClauseOut {
  children: ClauseNode[];
}

function buildClauseTree(clauses: ClauseOut[]): ClauseNode[] {
  const map = new Map<number, ClauseNode>();
  const roots: ClauseNode[] = [];
  for (const c of clauses) map.set(c.id, { ...c, children: [] });
  for (const c of clauses) {
    const node = map.get(c.id)!;
    if (c.parent_id != null && map.has(c.parent_id)) {
      map.get(c.parent_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  }
  const sortByPath = (nodes: ClauseNode[]) => {
    nodes.sort((a, b) =>
      (a.clause_path ?? '').localeCompare(b.clause_path ?? '', undefined, { numeric: true })
    );
    nodes.forEach(n => sortByPath(n.children));
  };
  sortByPath(roots);
  return roots;
}

function ClauseTreeItem({
  node,
  depth,
  docId,
  onSaved,
  crossRefs,
  onNavigateDoc,
}: {
  node: ClauseNode;
  depth: number;
  docId: number;
  onSaved: (updated: ClauseOut) => void;
  crossRefs?: CrossRefOut[];
  onNavigateDoc?: (docId: number) => void;
}) {
  const [expanded, setExpanded] = useState(depth === 0);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [showOriginal, setShowOriginal] = useState(false);

  const isStub = node.content === '(tổng hợp từ mục con)';
  const hasChildren = node.children.length > 0;
  const title = node.clause_num && node.title
    ? `${node.clause_num}. ${node.title}`
    : node.title || node.clause_num || `Điều khoản #${node.id}`;

  const startEdit = () => { setDraft(node.content); setEditing(true); setExpanded(true); };
  const cancelEdit = () => { setEditing(false); setDraft(''); };

  const saveEdit = async () => {
    setSaving(true);
    setSaveError('');
    try {
      const res = await apiFetch<ClausePatchOut>(
        `/documents/${docId}/clauses/${node.id}`,
        { method: 'PATCH', body: JSON.stringify({ content: draft }) }
      );
      onSaved({ ...node, ...res });
      setEditing(false);
      setDraft('');
      setShowOriginal(false);
    } catch (err) {
      setSaveError((err as ApiError).message || 'Lưu điều khoản thất bại');
    } finally {
      setSaving(false);
    }
  };

  const displayContent = showOriginal && node.original_content ? node.original_content : node.content;
  const nodeRefs = (crossRefs ?? []).filter((r) => r.source_clause_id === node.id);

  const itemCls = 'border-b border-border last:border-0';

  return (
    <div id={`clause-${node.id}`} className={itemCls}>
      <div style={{ paddingLeft: depth * 24 }}>
        <button
          className="w-full flex items-center justify-between py-3 px-4 text-left gap-2 hover:bg-surface-alt transition-colors"
          onClick={() => !editing && setExpanded((v) => !v)}
          aria-expanded={expanded}
        >
          <div className="flex items-center gap-2 min-w-0">
            {depth > 0 && <span className="text-ink-subtle text-xs shrink-0">└</span>}
            <span className={`text-sm ${hasChildren ? 'font-semibold' : 'font-medium'} text-ink truncate`}>
              {title}
            </span>
            {node.edited_by_user && (
              <span className="shrink-0 text-2xs px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium">
                đã sửa
              </span>
            )}
            {hasChildren && (
              <Badge kind="neutral" className="shrink-0">{node.children.length}</Badge>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {node.page_num != null && (
              <span className="text-2xs text-ink-muted">tr.{node.page_num}</span>
            )}
            <span className="text-ink-muted text-xs">{expanded ? '▲' : '▼'}</span>
          </div>
        </button>

        {expanded && !isStub && (
          <div className="pb-3 px-4">
            {editing ? (
              <div className="flex flex-col gap-2">
                <textarea
                  className="w-full text-sm border border-border rounded p-2 leading-relaxed resize-y min-h-[8rem] focus:outline-none focus:ring-1 focus:ring-primary"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  autoFocus
                />
                {saveError && <p className="text-xs text-danger">{saveError}</p>}
                <div className="flex items-center gap-2">
                  <Button size="sm" onClick={saveEdit} loading={saving}>Lưu</Button>
                  <Button size="sm" variant="ghost" onClick={cancelEdit} disabled={saving}>Hủy</Button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-1">
                <ClauseContent content={displayContent} crossRefs={nodeRefs} onNavigateDoc={onNavigateDoc} />
                <div className="flex items-center gap-3 pt-1 flex-wrap">
                  {node.original_content && (
                    <button
                      className="text-2xs text-primary hover:underline"
                      onClick={() => setShowOriginal((v) => !v)}
                    >
                      {showOriginal ? 'Xem bản đã sửa' : 'Xem bản gốc (AI)'}
                    </button>
                  )}
                  {node.edited_by_user && node.edited_at && (
                    <span className="text-2xs text-ink-muted">
                      Sửa bởi {node.edited_by_user} · {new Date(node.edited_at).toLocaleDateString('vi-VN')}
                    </span>
                  )}
                  <button
                    className="text-2xs text-ink-muted hover:text-primary ml-auto"
                    onClick={startEdit}
                  >
                    Sửa nội dung
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {expanded && hasChildren && (
          <div className="mb-1">
            {node.children.map((child) => (
              <ClauseTreeItem
                key={child.id}
                node={child}
                depth={depth + 1}
                docId={docId}
                onSaved={onSaved}
                crossRefs={crossRefs}
                onNavigateDoc={onNavigateDoc}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── #372 Definition row (D-07 inline edit) ───────────────────────────────────
function DefinitionRow({
  def,
  docId,
  onSaved,
}: {
  def: DefinitionOut;
  docId: number;
  onSaved: (updated: DefinitionOut) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [showOriginal, setShowOriginal] = useState(false);

  const startEdit = () => { setDraft(def.definition); setEditing(true); };
  const cancelEdit = () => { setEditing(false); setDraft(''); };

  const saveEdit = async () => {
    setSaving(true);
    setSaveError('');
    try {
      const res = await apiFetch<DefinitionPatchOut>(
        `/documents/${docId}/definitions/${def.id}`,
        { method: 'PATCH', body: JSON.stringify({ definition: draft }) }
      );
      onSaved({ ...def, ...res });
      setEditing(false);
      setDraft('');
      setShowOriginal(false);
    } catch (err) {
      setSaveError((err as ApiError).message || 'Lưu định nghĩa thất bại');
    } finally {
      setSaving(false);
    }
  };

  const displayDef = showOriginal && def.original_definition ? def.original_definition : def.definition;

  return (
    <div className="py-3 border-b border-border last:border-0">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-sm font-semibold text-primary">{def.term}</span>
            {def.edited_by_user && (
              <span className="text-2xs px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium">
                đã sửa
              </span>
            )}
            {def.source_clause_num && (
              <span className="text-2xs text-ink-muted">{def.source_clause_num}</span>
            )}
          </div>
          {editing ? (
            <div className="flex flex-col gap-2">
              <textarea
                className="w-full text-sm border border-border rounded p-2 leading-relaxed resize-y min-h-[5rem] focus:outline-none focus:ring-1 focus:ring-primary"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                autoFocus
              />
              {saveError && <p className="text-xs text-danger">{saveError}</p>}
              <div className="flex items-center gap-2">
                <Button size="sm" onClick={saveEdit} loading={saving}>Lưu</Button>
                <Button size="sm" variant="ghost" onClick={cancelEdit} disabled={saving}>Hủy</Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-1">
              <p className="text-sm text-ink leading-relaxed">{displayDef}</p>
              <div className="flex items-center gap-3 pt-1 flex-wrap">
                {def.original_definition && (
                  <button
                    className="text-2xs text-primary hover:underline"
                    onClick={() => setShowOriginal((v) => !v)}
                  >
                    {showOriginal ? 'Xem bản đã sửa' : 'Xem bản gốc (AI)'}
                  </button>
                )}
                {def.edited_by_user && def.edited_at && (
                  <span className="text-2xs text-ink-muted">
                    Sửa bởi {def.edited_by_user} · {new Date(def.edited_at).toLocaleDateString('vi-VN')}
                  </span>
                )}
                <button
                  className="text-2xs text-ink-muted hover:text-primary ml-auto"
                  onClick={startEdit}
                >
                  Sửa định nghĩa
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function GlossarySection({
  definitions,
  docId,
  onSaved,
}: {
  definitions: DefinitionOut[];
  docId: number;
  onSaved: (updated: DefinitionOut) => void;
}) {
  const [open, setOpen] = useState(false);
  if (definitions.length === 0) return null;
  return (
    <div className="mb-4 rounded-lg border border-border overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-4 py-3 bg-surface-alt text-left hover:bg-surface-sunken transition-colors"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="text-sm font-semibold text-ink">
          Định nghĩa ({definitions.length})
        </span>
        <span className="text-ink-muted text-xs">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="px-4 bg-surface">
          {definitions.map((def) => (
            <DefinitionRow key={def.id} def={def} docId={docId} onSaved={onSaved} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Tab: Nội dung hợp đồng ───────────────────────────────────────────────────
function TabClauses({
  clauses,
  loading,
  total,
  error,
  onRetry,
  docId,
  onClauseSaved,
  hasEdited,
  reReading,
  onReRead,
  definitions,
  onDefinitionSaved,
  crossRefs,
  orphanRefs,
  onResolveRefs,
  resolvingRefs,
  onNavigateDoc,
}: {
  clauses: ClauseOut[];
  loading: boolean;
  total: number;
  error: boolean;
  onRetry: () => void;
  docId: number;
  onClauseSaved: (updated: ClauseOut) => void;
  hasEdited: boolean;
  reReading: boolean;
  onReRead: () => void;
  definitions: DefinitionOut[];
  onDefinitionSaved: (updated: DefinitionOut) => void;
  crossRefs: CrossRefOut[];
  orphanRefs: CrossRefOut[];
  onResolveRefs: () => void;
  resolvingRefs: boolean;
  onNavigateDoc: (docId: number) => void;
}) {
  if (loading) {
    return (
      <div className="py-12 text-center text-sm text-ink-muted">Đang tải điều khoản…</div>
    );
  }
  if (error) {
    return (
      <EmptyState
        title="Không tải được điều khoản"
        description="Đã xảy ra lỗi khi tải nội dung điều khoản."
        action={<Button size="sm" variant="ghost" onClick={onRetry}>Thử lại</Button>}
      />
    );
  }
  if (clauses.length === 0) {
    return (
      <EmptyState
        title="Chưa có nội dung điều khoản"
        description="Tài liệu này chưa được bóc tách nội dung điều khoản."
      />
    );
  }
  const isHierarchical = clauses.some((c) => c.parent_id != null);
  if (isHierarchical) {
    const roots = buildClauseTree(clauses);
    return (
      <div>
        {hasEdited && <ReReadBanner onReRead={onReRead} reReading={reReading} />}
        <OrphanRefPanel
          orphanRefs={orphanRefs}
          clauses={clauses}
          onResolve={onResolveRefs}
          resolving={resolvingRefs}
        />
        <GlossarySection definitions={definitions} docId={docId} onSaved={onDefinitionSaved} />
        <div className="text-xs text-ink-muted mb-3">{total} điều khoản</div>
        <Card className="p-0">
          {roots.map((root) => (
            <ClauseTreeItem
              key={root.id}
              node={root}
              depth={0}
              docId={docId}
              onSaved={onClauseSaved}
              crossRefs={crossRefs}
              onNavigateDoc={onNavigateDoc}
            />
          ))}
        </Card>
      </div>
    );
  }

  const defaultOpen = clauses.length <= 8;
  return (
    <div>
      {hasEdited && <ReReadBanner onReRead={onReRead} reReading={reReading} />}
      <OrphanRefPanel
        orphanRefs={orphanRefs}
        clauses={clauses}
        onResolve={onResolveRefs}
        resolving={resolvingRefs}
      />
      <GlossarySection definitions={definitions} docId={docId} onSaved={onDefinitionSaved} />
      <div className="text-xs text-ink-muted mb-3">{total} điều khoản</div>
      <Card>
        {clauses.map((c) => (
          <ClauseItem
            key={c.id}
            clause={c}
            defaultOpen={defaultOpen}
            docId={docId}
            onSaved={onClauseSaved}
            crossRefs={crossRefs}
            onNavigateDoc={onNavigateDoc}
          />
        ))}
      </Card>
    </div>
  );
}

// ── Tab: Bên ký kết ───────────────────────────────────────────────────────────
function PartyCard({ party, isSelf }: { party: PartyOut; isSelf: boolean }) {
  const fields: { label: string; value: string | null | undefined }[] = [
    { label: 'Địa chỉ', value: party.address },
    { label: 'Liên hệ', value: party.contact },
    { label: 'Người đại diện', value: party.representative },
    { label: 'Mã số thuế', value: party.tax_code },
  ];
  const presentFields = fields.filter((f) => f.value);
  return (
    <Card className={isSelf ? 'border-primary-border bg-primary-soft' : ''}>
      <div className="flex items-center gap-2 flex-wrap mb-3">
        <span className="text-sm font-semibold text-ink">{party.name}</span>
        {party.role_label && <Badge kind="neutral">{party.role_label}</Badge>}
        {isSelf && <Badge kind="extracted">Bên mình</Badge>}
      </div>
      {presentFields.length > 0 && (
        <dl className="grid grid-cols-1 nav:grid-cols-2 gap-x-6 gap-y-2">
          {presentFields.map(({ label, value }) => (
            <div key={label}>
              <dt className="text-2xs text-ink-muted uppercase font-medium">{label}</dt>
              <dd className="text-xs text-ink mt-0.5">{value}</dd>
            </div>
          ))}
        </dl>
      )}
      {party.aliases && party.aliases.length > 0 && (
        <div className="mt-2">
          <span className="text-2xs text-ink-muted uppercase font-medium">Viết tắt / bí danh</span>
          <p className="text-xs text-ink mt-0.5">{party.aliases.join(', ')}</p>
        </div>
      )}
    </Card>
  );
}

function TabParties({ parties }: { parties?: PartyOut[] }) {
  if (!parties || parties.length === 0) {
    return (
      <EmptyState
        title="Chưa có dữ liệu bên ký kết"
        description="Bên ký kết sẽ xuất hiện sau khi tài liệu được bóc tách."
      />
    );
  }
  const selfParties = parties.filter((p) => p.is_self);
  const counterparties = parties.filter((p) => !p.is_self);
  return (
    <div className="space-y-4">
      {selfParties.map((p, i) => (
        <PartyCard key={p.id ?? `self-${i}`} party={p} isSelf />
      ))}
      {counterparties.map((p, i) => (
        <PartyCard key={p.id ?? `cp-${i}`} party={p} isSelf={false} />
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const docId = Number(id);
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [doc, setDoc] = useState<DocumentDetailOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [toastMsg, setToastMsg] = useState<string>('');
  const [toastKind, setToastKind] = useState<ToastKind>('success');
  const [pendingType, setPendingType] = useState<string | null>(null);
  const [remapping, setRemapping] = useState(false);
  const [editingTermId, setEditingTermId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [saving, setSaving] = useState(false);
  const [confirmingDoc, setConfirmingDoc] = useState(false);
  const [pendingClauseJump, setPendingClauseJump] = useState<string | null>(null);
  const [bulkCompleting, setBulkCompleting] = useState(false);
  const [clauses, setClauses] = useState<ClauseOut[]>([]);
  const [clausesLoading, setClausesLoading] = useState(false);
  const [clausesLoaded, setClausesLoaded] = useState(false);
  const [clausesTotal, setClausesTotal] = useState(0);
  const [clausesError, setClausesError] = useState(false);
  const [definitions, setDefinitions] = useState<DefinitionOut[]>([]);
  const [definitionsLoaded, setDefinitionsLoaded] = useState(false);
  const [crossRefs, setCrossRefs] = useState<CrossRefOut[]>([]);
  const [crossRefsLoaded, setCrossRefsLoaded] = useState(false);
  const [resolvingRefs, setResolvingRefs] = useState(false);
  const [fulfillTarget, setFulfillTarget] = useState<ObligationOut | null>(null);
  const [fulfilling, setFulfilling] = useState(false);
  const [reReading, setReReading] = useState(false);
  const [reReadDiffs, setReReadDiffs] = useState<ReReadDiff[] | null>(null);
  const [applyingDiffs, setApplyingDiffs] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { legalName, refetch: refetchJourney } = useJourney();

  const showToast = (msg: string, kind: ToastKind = 'success') => {
    setToastKind(kind);
    setToastMsg(msg);
  };

  const load = useCallback(async () => {
    if (!docId) return;
    setLoading(true);
    setError('');
    try {
      const res = await apiFetch<DocumentDetailOut>(`/documents/${docId}`);
      setDoc(res);
    } catch (err) {
      setError((err as ApiError).message || 'Không thể tải chi tiết');
    } finally {
      setLoading(false);
    }
  }, [docId]);

  const loadClauses = useCallback(async () => {
    if (!docId || clausesLoaded) return;
    setClausesLoading(true);
    setClausesError(false);
    try {
      const res = await apiFetch<ClauseListOut>(`/documents/${docId}/clauses`);
      setClauses(res.clauses);
      setClausesTotal(res.clause_count);
      setClausesLoaded(true);
    } catch {
      setClausesError(true);
    } finally {
      setClausesLoading(false);
    }
  }, [docId, clausesLoaded]);

  const loadDefinitions = useCallback(async () => {
    if (!docId || definitionsLoaded) return;
    try {
      const res = await apiFetch<DefinitionListOut>(`/documents/${docId}/definitions`);
      setDefinitions(res.definitions);
      setDefinitionsLoaded(true);
    } catch (err: unknown) {
      const status = (err as ApiError)?.status;
      if (status !== 404) console.warn('Failed to load definitions', err);
    }
  }, [docId, definitionsLoaded]);

  const loadCrossRefs = useCallback(async () => {
    if (!docId || crossRefsLoaded) return;
    try {
      const res = await apiFetch<CrossRefListOut>(`/documents/${docId}/cross-refs`);
      setCrossRefs(res.refs);
      setCrossRefsLoaded(true);
    } catch { /* graceful — no cross-refs = empty */ }
  }, [docId, crossRefsLoaded]);

  const resolveRefs = useCallback(async () => {
    if (!docId) return;
    setResolvingRefs(true);
    try {
      await apiFetch<CrossRefResolveOut>(`/documents/${docId}/cross-refs/resolve`, { method: 'POST' });
      const res = await apiFetch<CrossRefListOut>(`/documents/${docId}/cross-refs`);
      setCrossRefs(res.refs);
    } catch (err) {
      showToast((err as ApiError).message || 'Phân giải lại thất bại', 'error');
    } finally {
      setResolvingRefs(false);
    }
  }, [docId]);

  useEffect(() => {
    load();
  }, [load]);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    if (doc?.status === 'processing') {
      pollRef.current = setInterval(async () => {
        try {
          const res = await apiFetch<DocumentDetailOut>(`/documents/${docId}`);
          setDoc(res);
          if (res.status !== 'processing') {
            if (pollRef.current) clearInterval(pollRef.current);
          }
        } catch { /* ignore poll errors */ }
      }, 3000);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [doc?.status, docId]);

  useEffect(() => {
    if (activeTab === 'clauses') {
      loadClauses();
      loadDefinitions();
      loadCrossRefs();
    }
  }, [activeTab, loadClauses, loadDefinitions, loadCrossRefs]);

  // #472: obligation "Điều X" link jumps to clauses tab + scrolls to target
  // once clauses finish loading (source_clause_num is a clause_num string like
  // "4.1", not the numeric clause id used in the clause-{id} DOM anchor).
  useEffect(() => {
    if (activeTab !== 'clauses' || !pendingClauseJump || !clausesLoaded) return;
    const match = clauses.find((c) => c.clause_num === pendingClauseJump);
    if (match) {
      document.getElementById(`clause-${match.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    setPendingClauseJump(null);
  }, [activeTab, pendingClauseJump, clausesLoaded, clauses]);

  const startEdit = (term: TermOut) => {
    setEditingTermId(term.id);
    setEditValue(term.field_value || '');
  };

  const cancelEdit = () => {
    setEditingTermId(null);
    setEditValue('');
  };

  const saveEdit = async (termId: number) => {
    if (!docId) return;
    setSaving(true);
    try {
      await apiFetch(`/documents/${docId}/terms/${termId}`, {
        method: 'PATCH',
        body: JSON.stringify({ field_value: editValue }),
      });
      setDoc((prev) =>
        prev
          ? {
              ...prev,
              terms: prev.terms.map((t) =>
                t.id === termId ? { ...t, field_value: editValue, needs_review: false } : t
              ),
            }
          : prev
      );
      showToast('Đã cập nhật — ghi Event');
      setEditingTermId(null);
    } catch (err) {
      setError((err as ApiError).message || 'Lưu thất bại');
    } finally {
      setSaving(false);
    }
  };

  // #472 Q1: per-doc self-party dropdown removed — direction now fixed via
  // tenant-level legal_name in Settings (SettingsNudge links there).

  const jumpToClause = (clauseNum: string) => {
    setActiveTab('clauses');
    setPendingClauseJump(clauseNum);
  };

  const bulkCompleteObligations = async (ids: number[]) => {
    if (ids.length === 0) return;
    setBulkCompleting(true);
    try {
      const res = await apiFetch<BulkCompleteOut>('/obligations/bulk', {
        method: 'PATCH',
        body: JSON.stringify({
          ids,
          status: 'done',
          fulfilled_at: new Date().toISOString(),
        } as BulkCompleteIn),
      });
      showToast(
        res.skipped === 0
          ? `Đã đánh dấu hoàn thành ${res.updated} mục.`
          : `Hoàn thành ${res.updated}/${ids.length} mục — ${res.skipped} mục lỗi.`,
        res.skipped === 0 ? 'success' : 'error'
      );
    } catch (err) {
      showToast((err as ApiError).message || 'Hoàn thành hàng loạt thất bại', 'error');
    } finally {
      setBulkCompleting(false);
    }
    await load();
  };

  const confirmDocument = async () => {
    if (!docId) return;
    setConfirmingDoc(true);
    setError('');
    try {
      const res = await apiFetch<ConfirmDocumentOut>(`/documents/${docId}/confirm`, {
        method: 'POST',
      });
      showToast(
        res.journey_advanced
          ? 'Đã xác nhận tài liệu — hoàn tất kiểm tra, đã mở khoá đầy đủ.'
          : `Đã xác nhận tài liệu${res.directions_recomputed > 0 ? ` — ${res.directions_recomputed} nghĩa vụ cập nhật hướng` : ''}`
      );
      await load();
      if (res.journey_advanced) await refetchJourney();
    } catch (err) {
      setError((err as ApiError).message || 'Xác nhận tài liệu thất bại');
    } finally {
      setConfirmingDoc(false);
    }
  };

  const fulfillObligation = async (fulfilledAt: string, fulfilledBy: string) => {
    if (!fulfillTarget) return;
    setFulfilling(true);
    try {
      const res = await apiFetch<ObligationPatchOut>(
        `/obligations/${fulfillTarget.id}`,
        {
          method: 'PATCH',
          body: JSON.stringify({
            status: 'done',
            fulfilled_at: `${fulfilledAt}T00:00:00`,
            fulfilled_by: fulfilledBy || undefined,
          }),
        }
      );
      setFulfillTarget(null);
      const chainMsg = res.activated_count > 0
        ? ` · ${res.activated_count} nghĩa vụ tiếp theo đã kích hoạt`
        : '';
      showToast(`Đã đánh dấu hoàn thành${chainMsg}`);
      await load();
    } catch (err) {
      showToast((err as ApiError).message || 'Đánh dấu hoàn thành thất bại', 'error');
    } finally {
      setFulfilling(false);
    }
  };

  const saveClause = useCallback(
    (updated: ClauseOut) => {
      setClauses((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      showToast('Đã sửa điều khoản — D-07 ghi nhận.');
    },
    []
  );

  const saveDefinition = useCallback(
    (updated: DefinitionOut) => {
      setDefinitions((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      showToast('Đã sửa định nghĩa — D-07 ghi nhận.');
    },
    []
  );

  const hasEditedClauses = useMemo(
    () => clauses.some((c) => c.edited_by_user != null),
    [clauses]
  );

  const triggerReRead = useCallback(async () => {
    if (!docId) return;
    setReReading(true);
    try {
      const res = await apiFetch<ReReadOut>(`/documents/${docId}/reread`, { method: 'POST' });
      if (res.diffs.length === 0) {
        showToast(`Đã kiểm tra ${res.clauses_checked} điều khoản — không có thay đổi mới.`);
      } else {
        setReReadDiffs(res.diffs);
      }
    } catch (err) {
      showToast((err as ApiError).message || 'Bóc lại thất bại', 'error');
    } finally {
      setReReading(false);
    }
  }, [docId]);

  const applyReReadDiffs = useCallback(
    async (toCancel: number[]) => {
      setApplyingDiffs(true);
      try {
        await Promise.all(
          toCancel.map((id) =>
            apiFetch(`/obligations/${id}`, {
              method: 'PATCH',
              body: JSON.stringify({ status: 'cancelled' }),
            })
          )
        );
        setReReadDiffs(null);
        const msg =
          toCancel.length > 0
            ? `Đã hủy ${toCancel.length} nghĩa vụ theo nội dung mới`
            : 'Đã đóng — không áp dụng thay đổi.';
        showToast(msg);
        await load();
      } catch (err) {
        showToast((err as ApiError).message || 'Áp dụng thất bại', 'error');
      } finally {
        setApplyingDiffs(false);
      }
    },
    [load]
  );

  const handleRemap = async (newType: string) => {
    if (!docId) return;
    setRemapping(true);
    setError('');
    try {
      const res = await apiFetch<RemapTypeOut>(`/documents/${docId}/remap-type`, {
        method: 'POST',
        body: JSON.stringify({ doc_type_group: newType }),
      });
      setPendingType(null);
      await load();
      let msg = `Đã map lại ${res.fields_remapped} trường`;
      if (res.fields_null > 0) {
        msg += ` · ${res.fields_null} trường không tìm thấy trong điều khoản`;
      }
      showToast(msg, 'success');
    } catch (err) {
      const e = err as ApiError;
      setPendingType(null);
      showToast(
        e.status === 409
          ? 'Chưa có clause text — không thể map lại loại tài liệu này'
          : 'Map lại thất bại',
        'error'
      );
    } finally {
      setRemapping(false);
    }
  };

  const { docTypeGroupTerm, canonicalTerms, typeSpecificTerms } = useMemo(() => {
    if (!doc) return { docTypeGroupTerm: null, canonicalTerms: [], typeSpecificTerms: [] };
    let dtgTerm: TermOut | null = null;
    const canonical: TermOut[] = [];
    const typeSpecific: TermOut[] = [];
    for (const term of doc.terms) {
      if (term.field_name === 'doc_type_group') {
        dtgTerm = term;
      } else if (CANONICAL_FIELDS.includes(term.field_name)) {
        canonical.push(term);
      } else {
        typeSpecific.push(term);
      }
    }
    return { docTypeGroupTerm: dtgTerm, canonicalTerms: canonical, typeSpecificTerms: typeSpecific };
  }, [doc]);

  // Derived document title (DEC-043 — obligation-centric IA)
  const derivedTitle = useMemo(() => {
    if (!doc) return '';
    const typeLabel = doc.doc_type ? (DOC_TYPE_LABELS[doc.doc_type] ?? null) : null;
    const primaryParty = doc.parties?.find((p) => p.role_label === null)?.name ?? null;
    if (typeLabel && primaryParty) return `Hợp đồng ${typeLabel} với ${primaryParty}`;
    if (typeLabel) return `Hợp đồng ${typeLabel}`;
    if (primaryParty) return `Hợp đồng với ${primaryParty}`;
    return doc.file_name;
  }, [doc]);

  // Self-party is set when no obligations have null direction
  const selfPartySet = useMemo(() => {
    if (!doc || doc.obligations.length === 0) return true;
    return !doc.obligations.some((o) => o.direction === null);
  }, [doc]);

  const tabs: { key: TabKey; label: string; count?: number }[] = [
    { key: 'overview', label: 'Tổng quan' },
    {
      key: 'obligations',
      label: 'Nghĩa vụ & Quyền lợi',
      count: doc?.obligations.length ?? 0,
    },
    {
      key: 'clauses',
      label: 'Nội dung hợp đồng',
      count: doc?.clause_count ?? 0,
    },
    {
      key: 'parties',
      label: 'Bên ký kết',
      count: doc?.parties?.length ?? 0,
    },
  ];

  if (loading && !doc) {
    return <div className="p-8 text-center text-ink-muted text-sm">Đang tải…</div>;
  }

  if (error && !doc) {
    return <EmptyState title="Không tìm thấy tài liệu" description={error} />;
  }

  return (
    <div>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-4">
        <Link to="/admin/documents" className="text-sm text-ink-muted hover:text-primary">
          ← Tài liệu
        </Link>
      </div>

      {doc && (
        <>
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-xl font-bold text-ink leading-tight">
                    {doc.title || derivedTitle}
                  </h1>
                  {doc.contract_number && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-medium bg-surface-alt text-ink-muted border border-border">
                      #{doc.contract_number}
                    </span>
                  )}
                </div>
                <div className="text-xs text-ink-muted mt-1">
                  Tệp gốc: {doc.file_name}
                  {doc.created_at && (
                    <> · {new Date(doc.created_at).toLocaleDateString('vi-VN')}</>
                  )}
                </div>
                <div className="flex gap-2 mt-2 flex-wrap items-center">
                  <Badge kind={STATUS_BADGE[doc.status] || 'neutral'}>
                    {STATUS_LABEL[doc.status] || doc.status}
                  </Badge>
                  <LifecycleBadge status={doc.lifecycle_status} />
                  <SignatureBadge hasSig={doc.has_signature} pages={doc.signature_pages} />
                  {doc.doc_type && (
                    <span className="text-xs text-ink-muted">
                      {DOC_TYPE_LABELS[doc.doc_type] ?? doc.doc_type}
                    </span>
                  )}
                </div>
              </div>
              {doc.file_url && (
                <a
                  href={`${import.meta.env.VITE_API_BASE_URL}${doc.file_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline flex-shrink-0"
                >
                  Tải bản gốc
                </a>
              )}
              <button
                type="button"
                onClick={() => setDrawerOpen(true)}
                className="text-sm text-primary hover:underline flex-shrink-0"
              >
                Lịch sử chỉnh sửa
              </button>
            </div>
          </div>

          {/* Extraction progress bar */}
          {(doc.status === 'processing' || doc.processing_stage === 'failed') && (
            <ExtractionProgress stage={doc.processing_stage} progress={doc.processing_progress} />
          )}

          {/* Unconfirmed warning banner */}
          {doc.terms.length > 0 && !doc.confirmed_by_user_at && (
            <Card className="mb-4 border-warning-border bg-warning-soft" testId="doc-unconfirmed-warning">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex items-start gap-3">
                  <div>
                    <div className="text-sm font-medium text-ink">
                      Khế chưa nhắc nội dung tài liệu này vì bạn chưa xác nhận.
                    </div>
                    <div className="text-2xs text-ink-muted mt-0.5">
                      Hãy kiểm tra các trường và xác nhận để Khế bắt đầu nhắc.
                    </div>
                  </div>
                </div>
                <Button
                  size="sm"
                  onClick={confirmDocument}
                  loading={confirmingDoc}
                  disabled={editingTermId !== null}
                  testId="doc-unconfirmed-warning-cta"
                >
                  Xác nhận tài liệu này →
                </Button>
              </div>
            </Card>
          )}

          {/* Tab bar */}
          <div className="flex border-b border-border mb-6">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-primary text-primary'
                    : 'border-transparent text-ink-muted hover:text-ink'
                }`}
              >
                {tab.label}
                {tab.count !== undefined && tab.count > 0 && (
                  <span className="ml-1.5 px-1.5 py-0.5 text-2xs rounded-full bg-surface-muted text-ink-muted">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {activeTab === 'overview' && (
            <TabOverview
              doc={doc}
              docTypeGroupTerm={docTypeGroupTerm}
              canonicalTerms={canonicalTerms}
              typeSpecificTerms={typeSpecificTerms}
              editingTermId={editingTermId}
              editValue={editValue}
              saving={saving}
              remapping={remapping}
              onStartEdit={startEdit}
              onCancelEdit={cancelEdit}
              onSaveEdit={saveEdit}
              onSetEditValue={setEditValue}
              onSetPendingType={setPendingType}
            />
          )}

          {activeTab === 'obligations' && (
            <>
              {hasEditedClauses && (
                <StaleEditBanner onGoToClauses={() => setActiveTab('clauses')} />
              )}
              <TabObligations
                doc={doc}
                onFulfill={setFulfillTarget}
                onBulkComplete={bulkCompleteObligations}
                bulkCompleting={bulkCompleting}
                onJumpToClause={jumpToClause}
                hasLegalName={!!legalName}
              />
            </>
          )}

          {activeTab === 'clauses' && (
            <TabClauses
              clauses={clauses}
              loading={clausesLoading}
              total={clausesTotal}
              error={clausesError}
              onRetry={() => { setClausesLoaded(false); setClausesError(false); }}
              docId={docId}
              onClauseSaved={saveClause}
              hasEdited={hasEditedClauses}
              reReading={reReading}
              onReRead={triggerReRead}
              definitions={definitions}
              onDefinitionSaved={saveDefinition}
              crossRefs={crossRefs}
              orphanRefs={crossRefs.filter((r) => r.is_orphan)}
              onResolveRefs={resolveRefs}
              resolvingRefs={resolvingRefs}
              onNavigateDoc={(targetDocId) => navigate(`/documents/${targetDocId}`)}
            />
          )}

          {activeTab === 'parties' && (
            <TabParties parties={doc.parties} />
          )}

          {/* Footer: D-02 confirm gate */}
          {doc.terms.length > 0 && (
            <div className="mt-6">
              {doc.confirmed_by_user_at ? (
                <div className="flex items-center gap-2 text-sm text-ink-body">
                  <Badge kind="done">đã xác nhận</Badge>
                  <span>Bạn đã xác nhận tài liệu này. Khế dùng để nhắc hạn.</span>
                </div>
              ) : selfPartySet ? (
                <Card>
                  <div className="flex items-center justify-between gap-3 flex-wrap">
                    <span className="text-sm text-ink-body">
                      {editingTermId !== null
                        ? 'Lưu hoặc huỷ trường đang sửa trước khi xác nhận.'
                        : 'Đã kiểm tra xong các trường? Xác nhận để Khế chốt và bắt đầu nhắc hạn.'}
                    </span>
                    <Button
                      onClick={confirmDocument}
                      loading={confirmingDoc}
                      disabled={editingTermId !== null}
                    >
                      Xác nhận tài liệu này
                    </Button>
                  </div>
                </Card>
              ) : (
                <Card className="border-warning-border bg-warning-soft">
                  <div className="text-sm text-warning">
                    Hãy chọn bên trong tab "Nghĩa vụ & Quyền lợi" trước khi xác nhận tài liệu.
                  </div>
                </Card>
              )}
            </div>
          )}
        </>
      )}

      {/* Fulfillment modal */}
      <FulfillModal
        ob={fulfillTarget}
        open={fulfillTarget !== null}
        onClose={() => setFulfillTarget(null)}
        onSubmit={fulfillObligation}
        submitting={fulfilling}
      />

      {/* Re-read diff confirm modal (Phase 3 — D-02) */}
      {reReadDiffs !== null && (
        <DiffConfirmModal
          open={reReadDiffs !== null}
          diffs={reReadDiffs}
          onClose={() => setReReadDiffs(null)}
          onConfirm={applyReReadDiffs}
          submitting={applyingDiffs}
        />
      )}

      {/* Remap confirm modal */}
      <Modal
        open={pendingType !== null}
        title="Map lại loại hợp đồng?"
        onClose={() => !remapping && setPendingType(null)}
        footer={
          <>
            <Button variant="ghost" onClick={() => setPendingType(null)} disabled={remapping}>
              Hủy
            </Button>
            <Button
              onClick={() => pendingType && handleRemap(pendingType)}
              loading={remapping}
              testId="remap-confirm-btn"
            >
              Map lại
            </Button>
          </>
        }
      >
        Hệ thống sẽ tự động map lại các trường cho loại hợp đồng{' '}
        <span className="font-medium text-ink">
          {pendingType ? labelFor(DOC_TYPE_GROUP_LABELS, pendingType) : ''}
        </span>
        . Các trường theo loại cũ sẽ bị thay thế. Tiếp tục?
      </Modal>

      {/* D-07 audit drawer */}
      {docId > 0 && (
        <AuditDrawer
          docId={docId}
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
        />
      )}

      {/* Toast */}
      {toastMsg && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-toast">
          <Toast kind={toastKind}>{toastMsg}</Toast>
        </div>
      )}
    </div>
  );
}
