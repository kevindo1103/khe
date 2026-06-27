import { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Button, Card, Badge, Toast, EmptyState } from '../../components';
import { apiFetch } from '../../lib/api';
import type { ObligationListOut, ObligationOut, ObligationPatchOut, ObligationStatus } from '../../types/obligations';
import type { ApiError } from '../../lib/api';
import type { BadgeKind } from '../../components/Badge';
import { OBLIGATION_TYPE_LABELS, labelFor } from '../../lib/labels';

type DirectionTab = 'nghĩa_vụ' | 'quyền_lợi' | null;
type BucketKey = 'overdue' | 'due_soon' | 'upcoming' | 'waiting' | 'open_ended';

interface BucketDef {
  key: BucketKey;
  label: string;
  badge: BadgeKind;
}

const TABS: { key: DirectionTab; label: string }[] = [
  { key: 'nghĩa_vụ', label: 'Nghĩa vụ' },
  { key: 'quyền_lợi', label: 'Quyền lợi' },
  { key: null, label: 'Cần xác nhận' },
];

const BUCKET_DEFS: BucketDef[] = [
  { key: 'overdue', label: 'Quá hạn', badge: 'overdue' },
  { key: 'due_soon', label: 'Sắp tới hạn (≤30 ngày)', badge: 'due_soon' },
  { key: 'waiting', label: 'Chờ sự kiện', badge: 'needs_review' },
  { key: 'open_ended', label: 'Vô thời hạn', badge: 'neutral' },
  { key: 'upcoming', label: 'Sắp tới', badge: 'neutral' },
];

function classifyDueDate(dueDate: string | null): 'overdue' | 'due_soon' | 'upcoming' {
  if (!dueDate) return 'upcoming';
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(dueDate);
  due.setHours(0, 0, 0, 0);
  const diffMs = due.getTime() - today.getTime();
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return 'overdue';
  if (diffDays <= 30) return 'due_soon';
  return 'upcoming';
}

function classifyObligation(ob: ObligationOut): BucketKey {
  if (ob.status === 'waiting_trigger') return 'waiting';
  if (!ob.due_date) return 'open_ended';
  return classifyDueDate(ob.due_date);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'vô thời hạn';
  try {
    return new Date(dateStr).toLocaleDateString('vi-VN');
  } catch {
    return dateStr;
  }
}

function statusBadgeKind(status: ObligationStatus): BadgeKind {
  switch (status) {
    case 'pending':
      return 'needs_review';
    case 'in_progress':
      return 'processing';
    case 'partial':
      return 'due_soon';
    case 'done':
      return 'done';
    case 'cancelled':
      return 'neutral';
    case 'waiting_trigger':
      return 'needs_review';
    default:
      return 'neutral';
  }
}

function statusLabel(status: ObligationStatus): string {
  switch (status) {
    case 'pending':
      return 'chờ';
    case 'in_progress':
      return 'đang làm';
    case 'partial':
      return 'một phần';
    case 'done':
      return 'hoàn thành';
    case 'cancelled':
      return 'đã hủy';
    case 'waiting_trigger':
      return 'chờ sự kiện';
    case 'overdue':
      return 'quá hạn';
    case 'awaiting_confirmation':
      return 'chờ xác nhận';
  }
}

export default function Obligations() {
  const [data, setData] = useState<ObligationListOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [toastMsg, setToastMsg] = useState<string>('');
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<DirectionTab>('nghĩa_vụ');
  const [collapsedSeries, setCollapsedSeries] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiFetch<ObligationListOut>('/obligations/?page=1&page_size=100');
      setData(res);
    } catch (err) {
      setError((err as ApiError).message || 'Không thể tải danh sách');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filteredItems = useMemo(() => {
    return (data?.items || []).filter((ob) => ob.direction === activeTab);
  }, [data, activeTab]);

  const { seriesGroups, standalone } = useMemo(() => {
    const groups = new Map<string, ObligationOut[]>();
    const standaloneList: ObligationOut[] = [];
    for (const ob of filteredItems) {
      if (ob.milestone_series_id) {
        const arr = groups.get(ob.milestone_series_id) || [];
        arr.push(ob);
        groups.set(ob.milestone_series_id, arr);
      } else {
        standaloneList.push(ob);
      }
    }
    return { seriesGroups: groups, standalone: standaloneList };
  }, [filteredItems]);

  const bucketed = useMemo(() => {
    const map: Record<BucketKey, ObligationOut[]> = {
      overdue: [],
      due_soon: [],
      upcoming: [],
      waiting: [],
      open_ended: [],
    };
    for (const ob of standalone) {
      const bucket = classifyObligation(ob);
      map[bucket].push(ob);
    }
    return map;
  }, [standalone]);

  const counts = useMemo(() => {
    const all = filteredItems;
    const overdue = all.filter((o) => classifyObligation(o) === 'overdue' && o.status === 'pending').length;
    const dueSoon = all.filter((o) => classifyObligation(o) === 'due_soon' && o.status === 'pending').length;
    const done = all.filter((o) => o.status === 'done').length;
    return { overdue, dueSoon, done };
  }, [filteredItems]);

  const toggleSeries = (seriesId: string) => {
    setCollapsedSeries((prev) => {
      const next = new Set(prev);
      if (next.has(seriesId)) next.delete(seriesId);
      else next.add(seriesId);
      return next;
    });
  };

  const markStatus = async (id: number, newStatus: ObligationStatus) => {
    setUpdatingId(id);
    try {
      const patchRes = await apiFetch<ObligationPatchOut>(`/obligations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      });
      setData((prev) =>
        prev
          ? {
              ...prev,
              items: prev.items.map((o) =>
                o.id === id ? patchRes.obligation : o
              ),
            }
          : prev
      );
      if (newStatus === 'done') {
        const msg =
          patchRes.activated_count > 0
            ? `Hoàn thành ✅ — ${patchRes.activated_count} nghĩa vụ tiếp theo đã kích hoạt`
            : 'Hoàn thành ✅ — ghi Event';
        setToastMsg(msg);
      } else {
        setToastMsg(`Cập nhật: ${statusLabel(newStatus)}`);
      }
    } catch (err) {
      setError((err as ApiError).message || 'Cập nhật thất bại');
    } finally {
      setUpdatingId(null);
    }
  };

  const isUpdating = (id: number) => updatingId === id;

  const renderChips = (ob: ObligationOut) => {
    const chips: string[] = [];
    if (ob.milestone_total && ob.milestone_total > 1 && ob.milestone_index != null) {
      chips.push(`Đợt ${ob.milestone_index}/${ob.milestone_total}`);
    }
    if (ob.obligor) chips.push(`${ob.obligor} phải làm`);
    if (ob.status === 'waiting_trigger' && ob.trigger_condition) {
      chips.push(`⏳ Chờ: ${ob.trigger_condition}`);
    }
    if (ob.amount_raw) chips.push(ob.amount_raw);
    return chips;
  };

  const renderRow = (ob: ObligationOut) => {
    const isDone = ob.status === 'done';
    const isCancelled = ob.status === 'cancelled';
    const chips = renderChips(ob);
    return (
      <div
        key={ob.id}
        className={`flex items-start justify-between gap-3 py-3 border-b border-border last:border-0 ${
          isDone || isCancelled ? 'opacity-60' : ''
        }`}
      >
        <div className="min-w-0 flex-1">
          <div className={`text-sm font-medium ${isDone ? 'line-through' : 'text-ink'}`}>
            {ob.description}
          </div>
          <div className="text-xs text-ink-muted mt-1 flex gap-2 flex-wrap items-center">
            <Badge kind="neutral" className="text-2xs">{labelFor(OBLIGATION_TYPE_LABELS, ob.obligation_type)}</Badge>
            <span>
              📄{' '}
              <Link
                to={`/admin/documents/${ob.document_id}`}
                className="text-primary hover:underline"
              >
                #{ob.document_id}
              </Link>
            </span>
            <span>·</span>
            <span>
              {ob.status === 'waiting_trigger'
                ? 'chờ sự kiện'
                : `hạn ${formatDate(ob.due_date)}`}
            </span>
            {chips.map((c) => (
              <span key={c} className="text-ink-subtle">
                · {c}
              </span>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {isDone || isCancelled ? (
            <Badge kind={statusBadgeKind(ob.status)}>
              {statusLabel(ob.status)}
            </Badge>
          ) : ob.status === 'pending' ? (
            <>
              <Button size="sm" onClick={() => markStatus(ob.id, 'done')} loading={isUpdating(ob.id)}>
                Hoàn thành
              </Button>
              <Button size="sm" variant="ghost" onClick={() => markStatus(ob.id, 'in_progress')} disabled={isUpdating(ob.id)}>
                Đang làm
              </Button>
              <Button size="sm" variant="ghost" onClick={() => markStatus(ob.id, 'cancelled')} disabled={isUpdating(ob.id)}>
                Hủy
              </Button>
            </>
          ) : ob.status === 'in_progress' ? (
            <>
              <Button size="sm" onClick={() => markStatus(ob.id, 'done')} loading={isUpdating(ob.id)}>
                Hoàn thành
              </Button>
              <Button size="sm" variant="ghost" onClick={() => markStatus(ob.id, 'cancelled')} disabled={isUpdating(ob.id)}>
                Hủy
              </Button>
            </>
          ) : ob.status === 'waiting_trigger' ? (
            <Button size="sm" onClick={() => markStatus(ob.id, 'done')} loading={isUpdating(ob.id)}>
              Đánh dấu sự kiện đã xảy ra
            </Button>
          ) : (
            <Badge kind={statusBadgeKind(ob.status)}>{statusLabel(ob.status)}</Badge>
          )}
        </div>
      </div>
    );
  };

  const renderSeriesGroup = (seriesId: string, items: ObligationOut[]) => {
    const sorted = [...items].sort((a, b) => (a.milestone_index ?? 0) - (b.milestone_index ?? 0));
    const first = sorted[0];
    const doneCount = sorted.filter((o) => o.status === 'done').length;
    const total = sorted.length;
    const isCollapsed = collapsedSeries.has(seriesId);
    const label = `${labelFor(OBLIGATION_TYPE_LABELS, first.obligation_type)}${first.source_doc_chain ? ` (${first.source_doc_chain})` : ''}`;
    return (
      <Card key={seriesId} className="mb-4">
        <button
          type="button"
          onClick={() => toggleSeries(seriesId)}
          className="w-full text-left px-5 py-3 flex items-center justify-between border-b border-border bg-surface-alt cursor-pointer"
        >
          <div>
            <div className="text-sm font-semibold text-ink">{label}</div>
            <div className="text-xs text-ink-muted mt-0.5">
              {doneCount}/{total} hoàn thành
            </div>
          </div>
          <div className="text-ink-muted text-sm">{isCollapsed ? '▶' : '▼'}</div>
        </button>
        {!isCollapsed && <div className="px-5">{sorted.map(renderRow)}</div>}
      </Card>
    );
  };

  return (
    <div>
      <h1 className="text-xl font-bold text-ink mb-1">Nghĩa vụ & hạn</h1>
      <p className="text-sm text-ink-muted mb-5">
        Danh sách tất định từ kho — không phải AI đoán.
      </p>

      {error && <div className="mb-4 text-sm text-danger">{error}</div>}

      {/* Direction tabs */}
      <div className="flex gap-1 mb-5 border-b border-border">
        {TABS.map((t) => {
          const active = activeTab === t.key;
          return (
            <button
              key={t.label}
              type="button"
              onClick={() => setActiveTab(t.key)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                active
                  ? 'border-primary text-primary'
                  : 'border-transparent text-ink-muted hover:text-ink'
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Summary */}
      <div className="flex gap-3 mb-5 flex-wrap">
        <Card className="flex-1 min-w-[140px]">
          <div className="text-2xl font-bold text-danger">{counts.overdue}</div>
          <div className="text-sm text-ink-muted">Quá hạn</div>
        </Card>
        <Card className="flex-1 min-w-[140px]">
          <div className="text-2xl font-bold text-warning">{counts.dueSoon}</div>
          <div className="text-sm text-ink-muted">Sắp tới hạn</div>
        </Card>
        <Card className="flex-1 min-w-[140px]">
          <div className="text-2xl font-bold text-success">{counts.done}</div>
          <div className="text-sm text-ink-muted">Hoàn thành</div>
        </Card>
      </div>

      {/* Cần xác nhận — CTA to document detail */}
      {activeTab === null && filteredItems.length > 0 && (
        <Card className="mb-4 border-info/30 bg-info-soft">
          <div className="text-sm font-medium text-ink mb-2">
            Các nghĩa vụ này chưa xác định vai trò
          </div>
          <p className="text-xs text-ink-muted mb-3">
            Mở tài liệu gốc để xác nhận bên bạn đại diện → Khế sẽ tự phân loại nghĩa_vụ / quyền_lợi.
          </p>
          <div className="flex flex-wrap gap-2">
            {Array.from(new Set(filteredItems.map((ob) => ob.document_id))).map((docId) => (
              <Link
                key={docId}
                to={`/admin/documents/${docId}`}
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-surface border border-border rounded-md text-xs font-medium text-primary hover:bg-primary-soft transition-colors"
              >
                📄 Tài liệu #{docId} →
              </Link>
            ))}
          </div>
        </Card>
      )}

      {/* Series groups */}
      {Array.from(seriesGroups.entries()).map(([seriesId, items]) =>
        renderSeriesGroup(seriesId, items)
      )}

      {/* Standalone buckets */}
      {loading && !data ? (
        <div className="p-8 text-center text-ink-muted text-sm">Đang tải…</div>
      ) : (
        BUCKET_DEFS.map((b) => {
          const items = bucketed[b.key];
          if (items.length === 0) return null;
          return (
            <Card key={b.key} title={b.label} className="mb-4">
              {items.map(renderRow)}
            </Card>
          );
        })
      )}

      {data && filteredItems.length === 0 && !loading && (
        <EmptyState
          icon="✅"
          title="Không có nghĩa vụ nào"
          description="Khế sẽ nhắc bạn khi có hạn mới."
        />
      )}

      {/* Toast */}
      {toastMsg && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-toast">
          <Toast kind="success">{toastMsg}</Toast>
        </div>
      )}
    </div>
  );
}
