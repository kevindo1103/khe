import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Button, Input, Card, Table, EmptyState, JourneyEmptyState } from '../../components';
import { Badge } from '../../components/Badge';
import { apiFetch } from '../../lib/api';
import type { DocumentListOut, DocumentListItem } from '../../types/documents';
import type { ApiError } from '../../lib/api';

// Cross-cuts the status axis: an unconfirmed doc can be `extracted` OR `needs_review`.
// Backend GET /documents/ has no `confirmed` param yet → filtered client-side below.
// TODO(#251): switch to server `?confirmed=false` when Backend adds it (drops the 100-cap).
const NEEDS_CONFIRM = '__needsconfirm';

// keep this gate identical to the DocList badge + Home counter so all three agree
const isUnconfirmed = (d: DocumentListItem) =>
  (d.status === 'extracted' || d.status === 'needs_review') && !d.confirmed_by_user_at;

const FILTERS = [
  { key: '', label: 'Tất cả' },
  { key: NEEDS_CONFIRM, label: 'Cần xác nhận' },
  { key: 'processing', label: 'Đang xử lý' },
  { key: 'extracted', label: 'Đã bóc tách' },
  { key: 'needs_review', label: 'Cần kiểm tra' },
];

export default function DocumentList() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  // Deep-link from the dashboard counter (#251 §1): /admin/documents?confirm=pending
  const [filter, setFilter] = useState<string>(
    searchParams.get('confirm') === 'pending' ? NEEDS_CONFIRM : ''
  );
  const [q, setQ] = useState<string>('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<DocumentListOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    const needsConfirm = filter === NEEDS_CONFIRM;
    try {
      const params = new URLSearchParams();
      if (filter && !needsConfirm) params.set('status', filter);
      if (q) params.set('q', q);
      // No server-side `confirmed` filter yet → pull a wide page and filter client-side.
      params.set('page', String(needsConfirm ? 1 : page));
      params.set('page_size', needsConfirm ? '100' : '20');
      const res = await apiFetch<DocumentListOut>(`/documents/?${params.toString()}`);
      if (needsConfirm) {
        const items = res.items.filter(isUnconfirmed);
        setData({ ...res, items, total: items.length, page: 1, page_size: 100 });
      } else {
        setData(res);
      }
    } catch (err) {
      setError((err as ApiError).message || 'Không thể tải danh sách');
    } finally {
      setLoading(false);
    }
  }, [filter, q, page]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSearch = () => {
    setPage(1);
    load();
  };

  return (
    <div>
      <div className="flex justify-between items-end flex-wrap gap-3 mb-4">
        <div>
          <h1 className="text-xl font-bold text-ink">Kho tài liệu</h1>
          {data && (
            <p className="text-sm text-ink-muted mt-0.5">
              {data.total} tài liệu đang theo dõi
            </p>
          )}
        </div>
        <Link to="/admin/upload">
          <Button size="sm">+ Tải tài liệu</Button>
        </Link>
      </div>

      {/* Filters + search */}
      <div className="flex gap-3 items-center flex-wrap mb-4">
        <div className="w-full sm:w-72 flex items-center gap-2">
          <span aria-hidden="true" className="text-ink-subtle text-sm">🔍</span>
          <Input
            value={q}
            onChange={setQ}
            placeholder="Tìm theo tên / đối tác…"
            className="mb-0 flex-1"
          />
        </div>
        <Button size="sm" onClick={handleSearch}>
          Tìm
        </Button>
        <div className="flex gap-2 flex-wrap" role="group" aria-label="Lọc theo trạng thái">
          {FILTERS.map((f) => (
            <button
              key={f.key || 'all'}
              type="button"
              aria-pressed={filter === f.key}
              onClick={() => { setFilter(f.key); setPage(1); }}
              className={`px-3 py-1.5 rounded-pill text-xs font-medium transition-colors border focus-visible:shadow-ring focus-visible:outline-none ${
                filter === f.key
                  ? 'bg-primary-soft text-primary border-primary'
                  : 'bg-surface text-ink-muted border-border hover:text-ink'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-4 text-sm text-danger">{error}</div>
      )}

      <Card>
        {loading && !data ? (
          <div className="p-8 text-center text-ink-muted text-sm">Đang tải…</div>
        ) : data && data.items.length === 0 ? (
          // 4-state matrix spirit: truly-zero (cold tenant) ≠ all-confirmed ≠ no-match
          !filter && !q ? (
            <JourneyEmptyState state="cold_start" onUpload={() => navigate('/admin/upload')} />
          ) : filter === NEEDS_CONFIRM ? (
            <EmptyState
              icon="🎉"
              title="Tất cả tài liệu đã được xác nhận"
              description="Không còn tài liệu nào cần bạn kiểm tra. Khế đang nhắc đầy đủ."
            />
          ) : (
            <EmptyState
              notFound
              title="Không có tài liệu phù hợp"
              description="Thử bỏ bộ lọc hoặc đổi từ khoá tìm."
            />
          )
        ) : (
          <>
            <Table<DocumentListItem>
              columns={[
                { key: 'file_name', label: 'Tài liệu' },
                { key: 'doc_type', label: 'Loại' },
                { key: 'status', label: 'Trạng thái' },
                { key: 'term_count', label: 'Thuộc tính' },
                { key: 'obligation_count', label: 'Nghĩa vụ' },
                { key: 'clause_count', label: 'Điều khoản' },
                { key: 'created_at', label: 'Ngày tạo' },
              ]}
              rows={data?.items || []}
              rowTestId={(row) => `doc-row-${row.status}`}
              rowDataAttrs={(row) => ({ 'data-status': row.status })}
              renderCell={(key, row) => {
                if (key === 'file_name') {
                  return (
                    <Link
                      to={`/admin/documents/${row.id}`}
                      className="text-primary font-medium hover:underline"
                    >
                      {row.file_name}
                    </Link>
                  );
                }
                if (key === 'status') {
                  const badgeMap: Record<string, 'processing' | 'extracted' | 'needs_review' | 'neutral'> = {
                    processing: 'processing',
                    extracted: 'extracted',
                    needs_review: 'needs_review',
                  };
                  const labelMap: Record<string, string> = {
                    processing: 'Đang xử lý',
                    extracted: 'Đã bóc tách',
                    needs_review: '⚠ Cần kiểm tra',
                  };
                  // #238 — surface unconfirmed docs once successfully extracted.
                  // Gate on extracted/needs_review only: a 'failed' doc has no terms,
                  // so its confirm card never renders → the badge would be unclearable.
                  const needsConfirm =
                    (row.status === 'extracted' || row.status === 'needs_review') &&
                    !row.confirmed_by_user_at;
                  return (
                    <div className="flex gap-1.5 items-center flex-wrap">
                      <Badge kind={badgeMap[row.status] || 'neutral'} testId={`doc-status-${row.id}`}>
                        {labelMap[row.status] || row.status}
                      </Badge>
                      {needsConfirm && (
                        <Badge kind="needs_review" testId={`doc-needsconfirm-${row.id}`}>
                          Cần xác nhận
                        </Badge>
                      )}
                    </div>
                  );
                }
                if (key === 'doc_type') {
                  return row.doc_type || '—';
                }
                if (key === 'created_at') {
                  return row.created_at
                    ? new Date(row.created_at).toLocaleDateString('vi-VN')
                    : '—';
                }
                return String(((row as unknown) as Record<string, unknown>)[key] ?? '');
              }}
            />

            {/* Pagination */}
            {data && data.total > data.page_size && (
              <div className="flex items-center justify-between px-3 py-3 border-t border-border text-xs text-ink-muted">
                <span>
                  {data.total} tài liệu · Trang {data.page}
                </span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => p - 1)}
                  >
                    ← Trước
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={page * data.page_size >= data.total}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Sau →
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
