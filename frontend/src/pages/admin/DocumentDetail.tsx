import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button, Card, Badge, Input, ConfidenceMeter, Toast, Modal, EmptyState } from '../../components';
import type { ToastKind } from '../../components/Toast';
import { apiFetch } from '../../lib/api';
import type {
  DocumentDetailOut,
  TermOut,
  SelfPartyConfirmOut,
  ConfirmDocumentOut,
  RemapTypeOut,
  ClauseOut,
  ClauseListOut,
  ClausePatchOut,
  ReReadDiff,
  ReReadOut,
} from '../../types/documents';
import type { ObligationOut, ObligationPatchOut } from '../../types/obligations';
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

type TabKey = 'overview' | 'obligations' | 'clauses';

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

// ── Direction badge ──────────────────────────────────────────────────────────
function DirectionBadge({ direction }: { direction: ObligationOut['direction'] }) {
  if (direction === 'nghĩa_vụ')
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-2xs font-medium bg-ink-muted/10 text-ink-muted">
        ↑ Phải làm
      </span>
    );
  if (direction === 'quyền_lợi')
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-2xs font-medium bg-primary/10 text-primary">
        ↓ Được hưởng
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-2xs font-medium bg-amber-100 text-amber-700">
      ? Chưa rõ — chọn bên
    </span>
  );
}

// ── Due date display ─────────────────────────────────────────────────────────
function ObligationDue({ ob }: { ob: ObligationOut }) {
  if (ob.status === 'waiting_trigger') {
    return (
      <span className="text-xs text-ink-muted">
        ⏳ Chờ mốc: {ob.trigger_condition || ob.milestone_trigger || '—'}
      </span>
    );
  }
  if (!ob.due_date) {
    return <span className="text-xs text-ink-muted italic">Cam kết đang hiệu lực</span>;
  }
  const diff = Math.ceil((new Date(ob.due_date).getTime() - Date.now()) / 86400000);
  const dateStr = new Date(ob.due_date).toLocaleDateString('vi-VN');
  if (diff < 0)
    return <span className="text-xs font-medium text-red-600">Quá hạn {-diff} ngày · {dateStr}</span>;
  if (diff === 0)
    return <span className="text-xs font-medium text-orange-600">Hôm nay · {dateStr}</span>;
  if (diff <= 7)
    return <span className="text-xs font-medium text-orange-500">Còn {diff} ngày · {dateStr}</span>;
  return <span className="text-xs text-ink-muted">Hạn: {dateStr}</span>;
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

// ── Single obligation row ────────────────────────────────────────────────────
function ObligationRow({
  ob,
  onFulfill,
}: {
  ob: ObligationOut;
  onFulfill: (ob: ObligationOut) => void;
}) {
  const canFulfill = ['pending', 'in_progress', 'partial'].includes(ob.status);
  return (
    <div className="py-3 border-b border-border last:border-0">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <DirectionBadge direction={ob.direction} />
            <Badge kind="neutral" className="text-2xs">
              {labelFor(OBLIGATION_TYPE_LABELS, ob.obligation_type)}
            </Badge>
            {ob.milestone_total && ob.milestone_total > 1 && ob.milestone_index != null && (
              <span className="text-2xs text-ink-muted">
                Đợt {ob.milestone_index}/{ob.milestone_total}
              </span>
            )}
          </div>
          <div className="text-sm text-ink leading-snug">{ob.description}</div>
          <div className="mt-1 flex items-center gap-3 flex-wrap">
            <ObligationDue ob={ob} />
            {ob.amount_raw && (
              <span className="text-xs text-ink-muted">💰 {ob.amount_raw}</span>
            )}
            {ob.fulfilled_at && (
              <span className="text-xs text-ink-muted">
                ✓ {new Date(ob.fulfilled_at).toLocaleDateString('vi-VN')}
                {ob.fulfilled_by && ` · ${ob.fulfilled_by}`}
              </span>
            )}
          </div>
        </div>
        <div className="flex-shrink-0 mt-0.5 flex items-center gap-2">
          {ob.status === 'done' ? (
            <Badge kind="done">✓ hoàn thành</Badge>
          ) : ob.status === 'cancelled' ? (
            <Badge kind="neutral">đã hủy</Badge>
          ) : (
            <>
              {canFulfill && (
                <Button size="sm" variant="ghost" onClick={() => onFulfill(ob)}>
                  Hoàn thành →
                </Button>
              )}
              {!canFulfill && (
                <Link to="/admin/obligations" className="text-xs text-primary hover:underline">
                  Quản lý →
                </Link>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Self-party gate (blocking prompt when direction=null) ────────────────────
function SelfPartyGate({
  parties,
  selectedRole,
  onSelect,
  onConfirm,
  confirming,
}: {
  parties: { name: string; role_label: string | null }[];
  selectedRole: string;
  onSelect: (v: string) => void;
  onConfirm: () => void;
  confirming: boolean;
}) {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 mb-6">
      <div className="flex items-start gap-3">
        <span className="text-xl" aria-hidden="true">⚠️</span>
        <div className="flex-1">
          <div className="text-sm font-semibold text-ink mb-1">
            Bên nào trong hợp đồng này là bạn?
          </div>
          <p className="text-xs text-ink-muted mb-3">
            Chọn bên bạn đại diện để Khế phân loại nghĩa vụ (phải làm / được hưởng).
            Chưa chọn → tất cả nghĩa vụ hiển thị "Chưa rõ".
          </p>
          <div className="flex gap-2 items-end flex-wrap">
            <select
              value={selectedRole}
              onChange={(e) => onSelect(e.target.value)}
              className="flex-1 min-w-[180px] px-3 py-2 rounded-md border border-border bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">▼ Chọn bên...</option>
              {parties.map((p, i) => (
                <option key={i} value={p.role_label || p.name}>
                  {p.name}{p.role_label ? ` (${p.role_label})` : ''}
                </option>
              ))}
            </select>
            <Button onClick={onConfirm} loading={confirming} disabled={!selectedRole}>
              Xác nhận bên
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Self-party confirmed chip ────────────────────────────────────────────────
function SelfPartyConfirmed({ confirmedAt }: { confirmedAt: string }) {
  return (
    <div className="flex items-center gap-2 text-xs text-ink-muted mb-4">
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
        ✓ Đã chọn bên
      </span>
      <span>{new Date(confirmedAt).toLocaleDateString('vi-VN')}</span>
    </div>
  );
}

// ── Completeness banner ──────────────────────────────────────────────────────
function CompletenessBanner({ doc }: { doc: DocumentDetailOut }) {
  const nullDirs = doc.obligations.filter((o) => o.direction === null).length;
  const confirmed = !!doc.confirmed_by_user_at;
  const mayHaveMore = (doc as DocumentDetailOut & { may_have_unextracted_obligations?: boolean | null })
    .may_have_unextracted_obligations;

  if (confirmed && nullDirs === 0 && !mayHaveMore) {
    return (
      <div className="flex items-center gap-2 text-xs text-success font-medium mb-4">
        <span>✅</span>
        <span>Nghĩa vụ đầy đủ — Khế đang theo dõi</span>
      </div>
    );
  }
  if (nullDirs > 0) {
    return (
      <div className="flex items-center gap-2 text-xs text-amber-700 mb-4">
        <span>⚠️</span>
        <span>{nullDirs} nghĩa vụ chưa rõ hướng — hãy chọn bên để Khế phân loại.</span>
      </div>
    );
  }
  if (mayHaveMore) {
    return (
      <div className="flex items-center gap-2 text-xs text-ink-muted mb-4">
        <span>ℹ️</span>
        <span>Có thể còn nghĩa vụ chưa bóc — xem nội dung điều khoản để xác nhận.</span>
      </div>
    );
  }
  return null;
}

// ── Clause accordion item (Phase 2 — inline edit, D-07) ─────────────────────
function ClauseItem({
  clause,
  defaultOpen,
  docId,
  onSaved,
}: {
  clause: ClauseOut;
  defaultOpen: boolean;
  docId: number;
  onSaved: (updated: ClauseOut) => void;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string>('');
  const [showOriginal, setShowOriginal] = useState(false);

  const title =
    clause.title ||
    (clause.clause_num ? `Điều ${clause.clause_num}` : `Điều khoản #${clause.id}`);

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

  return (
    <div className="border-b border-border last:border-0">
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
              <p className="text-sm text-ink-muted leading-relaxed whitespace-pre-wrap">
                {displayContent}
              </p>
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
                  ✎ Sửa nội dung
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
        <span>🔄</span>
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
    <div className="flex items-center gap-3 p-3 mb-4 rounded-lg bg-amber-50 border border-amber-200 text-sm">
      <span>⚠️</span>
      <span className="text-amber-700 flex-1">
        Có điều khoản đã sửa — nghĩa vụ có thể chưa phản ánh nội dung mới.
      </span>
      <button className="text-2xs text-amber-700 underline" onClick={onGoToClauses}>
        Xem điều khoản →
      </button>
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
    if (action === 'update') return '✏ Cập nhật';
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
                    selected ? 'border-red-200 bg-red-50' : 'border-border bg-surface-muted'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="text-xs font-medium text-red-600">
                          {actionLabel(diff.action)}
                        </span>
                        {diff.protected && (
                          <span className="text-2xs px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 font-medium">
                            🔒 Thủ công
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
                            ? 'border-red-300 text-red-600 bg-red-50'
                            : 'border-border text-ink-muted'
                        }`}
                        onClick={() => toggleCancel(id)}
                        disabled={submitting}
                      >
                        {selected ? 'Hủy ✓' : 'Giữ lại'}
                      </button>
                    )}
                    {diff.protected && (
                      <span className="flex-shrink-0 text-xs px-2 py-1 text-ink-muted">
                        Giữ của bạn ✓
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
                    <span className="text-red-500 line-through">{diff.old_value}</span>
                    <span>→</span>
                    <span className="text-green-600">{diff.new_value}</span>
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
          <span className="text-xs font-medium text-ink-muted uppercase">
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

      {doc.terms.length === 0 ? (
        <Card title="Thông tin trích xuất">
          <EmptyState
            icon="📭"
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

// ── Tab: Nghĩa vụ & Quyền lợi ────────────────────────────────────────────────
function TabObligations({
  doc,
  selectedRole,
  confirming,
  onSelectRole,
  onConfirmSelfParty,
  onFulfill,
}: {
  doc: DocumentDetailOut;
  selectedRole: string;
  confirming: boolean;
  onSelectRole: (v: string) => void;
  onConfirmSelfParty: () => void;
  onFulfill: (ob: ObligationOut) => void;
}) {
  const hasNullDirection = doc.obligations.some((o) => o.direction === null);

  const nghiaVu = doc.obligations.filter(
    (o) => o.direction === 'nghĩa_vụ' && o.obligation_type !== 'review'
  );
  const quyenLoi = doc.obligations.filter(
    (o) => o.direction === 'quyền_lợi' && o.obligation_type !== 'review'
  );
  const chuaRo = doc.obligations.filter((o) => o.direction === null);
  const reviewObs = doc.obligations.filter((o) => o.obligation_type === 'review');

  if (doc.obligations.length === 0) {
    return (
      <EmptyState
        icon="📋"
        title="Chưa có nghĩa vụ nào"
        description="Tài liệu chưa có nghĩa vụ được bóc tách."
      />
    );
  }

  return (
    <div>
      <CompletenessBanner doc={doc} />

      {hasNullDirection && doc.parties && doc.parties.length > 0 && (
        <SelfPartyGate
          parties={doc.parties}
          selectedRole={selectedRole}
          onSelect={onSelectRole}
          onConfirm={onConfirmSelfParty}
          confirming={confirming}
        />
      )}

      {!hasNullDirection && doc.confirmed_by_user_at && (
        <SelfPartyConfirmed confirmedAt={doc.confirmed_by_user_at} />
      )}

      {nghiaVu.length > 0 && (
        <Card title={`Phải làm (${nghiaVu.length})`} className="mb-4">
          {nghiaVu.map((ob) => (
            <ObligationRow key={ob.id} ob={ob} onFulfill={onFulfill} />
          ))}
        </Card>
      )}

      {quyenLoi.length > 0 && (
        <Card title={`Được hưởng (${quyenLoi.length})`} className="mb-4">
          {quyenLoi.map((ob) => (
            <ObligationRow key={ob.id} ob={ob} onFulfill={onFulfill} />
          ))}
        </Card>
      )}

      {chuaRo.length > 0 && (
        <Card title={`Chưa rõ hướng (${chuaRo.length})`} className="mb-4">
          {chuaRo.map((ob) => (
            <ObligationRow key={ob.id} ob={ob} onFulfill={onFulfill} />
          ))}
        </Card>
      )}

      {reviewObs.length > 0 && (
        <Card title={`Review / kiểm tra định kỳ (${reviewObs.length})`} className="mb-4">
          {reviewObs.map((ob) => (
            <ObligationRow key={ob.id} ob={ob} onFulfill={onFulfill} />
          ))}
        </Card>
      )}
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
}: {
  node: ClauseNode;
  depth: number;
  docId: number;
  onSaved: (updated: ClauseOut) => void;
}) {
  const [expanded, setExpanded] = useState(depth === 0);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [showOriginal, setShowOriginal] = useState(false);

  const isStub = node.content === '(tổng hợp từ mục con)';
  const hasChildren = node.children.length > 0;
  const title = node.title || node.clause_num || `Điều khoản #${node.id}`;

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

  return (
    <div className={depth > 0 ? 'border-l border-border ml-3' : ''}>
      <div style={{ paddingLeft: depth * 24 }}>
        <button
          className="w-full flex items-center justify-between py-2 px-1 text-left gap-2 hover:bg-surface-alt transition-colors"
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
          <div className="pb-2 px-1">
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
                <p className="text-sm text-ink-muted leading-relaxed whitespace-pre-wrap">{displayContent}</p>
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
                    ✎ Sửa nội dung
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
              />
            ))}
          </div>
        )}
      </div>
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
}) {
  if (loading) {
    return (
      <div className="py-12 text-center text-sm text-ink-muted">Đang tải điều khoản…</div>
    );
  }
  if (error) {
    return (
      <EmptyState
        icon="⚠️"
        title="Không tải được điều khoản"
        description="Đã xảy ra lỗi khi tải nội dung điều khoản."
        action={<Button size="sm" variant="ghost" onClick={onRetry}>Thử lại</Button>}
      />
    );
  }
  if (clauses.length === 0) {
    return (
      <EmptyState
        icon="📄"
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
        <div className="text-xs text-ink-muted mb-3">{total} điều khoản</div>
        <Card>
          {roots.map((root) => (
            <ClauseTreeItem
              key={root.id}
              node={root}
              depth={0}
              docId={docId}
              onSaved={onClauseSaved}
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
      <div className="text-xs text-ink-muted mb-3">{total} điều khoản</div>
      <Card>
        {clauses.map((c) => (
          <ClauseItem
            key={c.id}
            clause={c}
            defaultOpen={defaultOpen}
            docId={docId}
            onSaved={onClauseSaved}
          />
        ))}
      </Card>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const docId = Number(id);

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
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [confirming, setConfirming] = useState(false);
  const [confirmingDoc, setConfirmingDoc] = useState(false);
  const [clauses, setClauses] = useState<ClauseOut[]>([]);
  const [clausesLoading, setClausesLoading] = useState(false);
  const [clausesLoaded, setClausesLoaded] = useState(false);
  const [clausesTotal, setClausesTotal] = useState(0);
  const [clausesError, setClausesError] = useState(false);
  const [fulfillTarget, setFulfillTarget] = useState<ObligationOut | null>(null);
  const [fulfilling, setFulfilling] = useState(false);
  const [reReading, setReReading] = useState(false);
  const [reReadDiffs, setReReadDiffs] = useState<ReReadDiff[] | null>(null);
  const [applyingDiffs, setApplyingDiffs] = useState(false);
  const { refetch: refetchJourney } = useJourney();

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
    }
  }, [activeTab, loadClauses]);

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
      showToast('Đã cập nhật — ghi Event ✓');
      setEditingTermId(null);
    } catch (err) {
      setError((err as ApiError).message || 'Lưu thất bại');
    } finally {
      setSaving(false);
    }
  };

  const confirmSelfParty = async () => {
    if (!docId || !selectedRole) return;
    setConfirming(true);
    setError('');
    try {
      const res = await apiFetch<SelfPartyConfirmOut>(
        `/documents/${docId}/confirm_self_party`,
        { method: 'POST', body: JSON.stringify({ role_label: selectedRole }) }
      );
      showToast(
        res.updated > 0
          ? `Đã ghi nhận bên bạn — ${res.updated} nghĩa vụ đã cập nhật hướng.`
          : 'Đã ghi nhận bên bạn — chưa có nghĩa vụ nào khớp để suy ra hướng.'
      );
      setSelectedRole('');
      await load();
    } catch (err) {
      setError((err as ApiError).message || 'Xác nhận thất bại');
    } finally {
      setConfirming(false);
    }
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
          ? 'Đã xác nhận tài liệu ✓ — hoàn tất kiểm tra, đã mở khoá đầy đủ.'
          : `Đã xác nhận tài liệu ✓${res.directions_recomputed > 0 ? ` — ${res.directions_recomputed} nghĩa vụ cập nhật hướng` : ''}`
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
      showToast(`Đã đánh dấu hoàn thành ✓${chainMsg}`);
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
      showToast('Đã sửa điều khoản ✓ — D-07 ghi nhận.');
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
            ? `Đã hủy ${toCancel.length} nghĩa vụ theo nội dung mới ✓`
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
  ];

  if (loading && !doc) {
    return <div className="p-8 text-center text-ink-muted text-sm">Đang tải…</div>;
  }

  if (error && !doc) {
    return <EmptyState icon="⚠️" title="Không tìm thấy tài liệu" description={error} />;
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
                  📥 Tải bản gốc
                </a>
              )}
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
                  <span className="text-xl" aria-hidden="true">⚠️</span>
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
                selectedRole={selectedRole}
                confirming={confirming}
                onSelectRole={setSelectedRole}
                onConfirmSelfParty={confirmSelfParty}
                onFulfill={setFulfillTarget}
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
            />
          )}

          {/* Footer: D-02 confirm gate */}
          {doc.terms.length > 0 && (
            <div className="mt-6">
              {doc.confirmed_by_user_at ? (
                <div className="flex items-center gap-2 text-sm text-ink-body">
                  <Badge kind="done">đã xác nhận</Badge>
                  <span>✅ Bạn đã xác nhận tài liệu này. Khế dùng để nhắc hạn.</span>
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
                <Card className="border-amber-200 bg-amber-50">
                  <div className="text-sm text-amber-700">
                    ⚠️ Hãy chọn bên trong tab "Nghĩa vụ & Quyền lợi" trước khi xác nhận tài liệu.
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

      {/* Toast */}
      {toastMsg && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-toast">
          <Toast kind={toastKind}>{toastMsg}</Toast>
        </div>
      )}
    </div>
  );
}
