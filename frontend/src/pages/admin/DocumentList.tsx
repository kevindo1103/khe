import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Button, Input, Card, Table, EmptyState } from '../../components';
import { Badge } from '../../components/Badge';
import { apiFetch } from '../../lib/api';
import type { DocumentListOut, DocumentListItem } from '../../types/documents';
import type { ApiError } from '../../lib/api';

const FILTERS = [
  { key: '', label: 'Tất cả' },
  { key: 'processing', label: 'Đang xử lý' },
  { key: 'extracted', label: 'Đã bóc tách' },
  { key: 'needs_review', label: 'Cần kiểm tra' },
];

export default function DocumentList() {
  const [filter, setFilter] = useState<string>('');
  const [q, setQ] = useState<string>('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<DocumentListOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (filter) params.set('status', filter);
      if (q) params.set('q', q);
      params.set('page', String(page));
      params.set('page_size', '20');
      const res = await apiFetch<DocumentListOut>(`/documents/?${params.toString()}`);
      setData(res);
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
      <div className="flex justify-between items-center flex-wrap gap-3 mb-4">
        <h1 className="text-xl font-bold text-ink">Tài liệu</h1>
        <Link to="/admin/upload">
          <Button size="sm">+ Tải tài liệu</Button>
        </Link>
      </div>

      {/* Filters + search */}
      <div className="flex gap-3 items-center flex-wrap mb-4">
        <div className="w-full sm:w-64">
          <Input
            value={q}
            onChange={setQ}
            placeholder="Tìm theo tên tài liệu…"
          />
        </div>
        <Button size="sm" onClick={handleSearch}>
          Tìm
        </Button>
        <div className="flex gap-2 flex-wrap">
          {FILTERS.map((f) => (
            <button
              key={f.key || 'all'}
              onClick={() => { setFilter(f.key); setPage(1); }}
              className={`px-3 py-1.5 rounded-pill text-xs font-medium transition-colors border ${
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
          <EmptyState
            icon="🗂️"
            title="Không có tài liệu"
            description="Thử bỏ bộ lọc hoặc tải tài liệu mới."
          />
        ) : (
          <>
            <Table<DocumentListItem>
              columns={[
                { key: 'file_name', label: 'Tài liệu' },
                { key: 'doc_type', label: 'Loại' },
                { key: 'status', label: 'Trạng thái' },
                { key: 'term_count', label: 'Thuộc tính' },
                { key: 'obligation_count', label: 'Nghĩa vụ' },
                { key: 'created_at', label: 'Ngày tạo' },
              ]}
              rows={data?.items || []}
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
                  return (
                    <Badge kind={badgeMap[row.status] || 'neutral'}>
                      {labelMap[row.status] || row.status}
                    </Badge>
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
