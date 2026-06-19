import { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Button, Card, Badge, Toast, EmptyState } from '../../components';
import { apiFetch } from '../../lib/api';
import type { ObligationListOut, ObligationOut } from '../../types/obligations';
import type { ApiError } from '../../lib/api';

type BucketKey = 'overdue' | 'due_soon' | 'upcoming';

interface BucketDef {
  key: BucketKey;
  label: string;
  badge: 'overdue' | 'due_soon' | 'neutral';
}

const BUCKETS: BucketDef[] = [
  { key: 'overdue', label: 'Quá hạn', badge: 'overdue' },
  { key: 'due_soon', label: 'Sắp tới hạn (≤30 ngày)', badge: 'due_soon' },
  { key: 'upcoming', label: 'Sắp tới', badge: 'neutral' },
];

function classifyDueDate(dueDate: string | null): BucketKey {
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

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'vô thời hạn';
  try {
    return new Date(dateStr).toLocaleDateString('vi-VN');
  } catch {
    return dateStr;
  }
}

export default function Obligations() {
  const [data, setData] = useState<ObligationListOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [toastMsg, setToastMsg] = useState<string>('');
  const [updatingId, setUpdatingId] = useState<number | null>(null);

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

  const bucketed = useMemo(() => {
    const map: Record<BucketKey, ObligationOut[]> = { overdue: [], due_soon: [], upcoming: [] };
    const items = data?.items || [];
    for (const ob of items) {
      const bucket = classifyDueDate(ob.due_date);
      map[bucket].push(ob);
    }
    return map;
  }, [data]);

  const counts = useMemo(() => {
    const overdue = bucketed.overdue.filter((o) => o.status === 'pending').length;
    const dueSoon = bucketed.due_soon.filter((o) => o.status === 'pending').length;
    const done = (data?.items || []).filter((o) => o.status === 'done').length;
    return { overdue, dueSoon, done };
  }, [bucketed, data]);

  const markDone = async (id: number) => {
    setUpdatingId(id);
    try {
      await apiFetch(`/obligations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: 'done' }),
      });
      // Optimistic update
      setData((prev) =>
        prev
          ? {
              ...prev,
              items: prev.items.map((o) =>
                o.id === id ? { ...o, status: 'done' } : o
              ),
            }
          : prev
      );
      setToastMsg('Đã đánh dấu hoàn thành — ghi Event ✓');
    } catch (err) {
      setError((err as ApiError).message || 'Cập nhật thất bại');
    } finally {
      setUpdatingId(null);
    }
  };

  const renderRow = (ob: ObligationOut) => {
    const isDone = ob.status === 'done';
    return (
      <div
        key={ob.id}
        className={`flex items-center justify-between gap-3 py-3 border-b border-border last:border-0 ${
          isDone ? 'opacity-60' : ''
        }`}
      >
        <div className="min-w-0 flex-1">
          <div className={`text-sm font-medium ${isDone ? 'line-through' : 'text-ink'}`}>
            {ob.description}
          </div>
          <div className="text-xs text-ink-muted mt-1 flex gap-2 flex-wrap">
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
            <span>hạn {formatDate(ob.due_date)}</span>
            <span>·</span>
            <span>{ob.obligation_type}</span>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {isDone ? (
            <Badge kind="done">✓ hoàn thành</Badge>
          ) : (
            <>
              <Button
                size="sm"
                onClick={() => markDone(ob.id)}
                loading={updatingId === ob.id}
              >
                Hoàn thành
              </Button>
              <Button size="sm" variant="ghost" disabled>
                Hủy
              </Button>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div>
      <h1 className="text-xl font-bold text-ink mb-1">Nghĩa vụ & hạn</h1>
      <p className="text-sm text-ink-muted mb-5">
        Danh sách tất định từ kho — không phải AI đoán.
      </p>

      {error && <div className="mb-4 text-sm text-danger">{error}</div>}

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

      {/* Buckets */}
      {loading && !data ? (
        <div className="p-8 text-center text-ink-muted text-sm">Đang tải…</div>
      ) : (
        BUCKETS.map((b) => {
          const items = bucketed[b.key];
          if (items.length === 0) return null;
          return (
            <Card key={b.key} title={b.label} className="mb-4">
              {items.map(renderRow)}
            </Card>
          );
        })
      )}

      {data && data.items.length === 0 && (
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
