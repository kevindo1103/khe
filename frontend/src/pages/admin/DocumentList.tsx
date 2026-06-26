import { useState, useEffect, useCallback, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../../components';
import { apiFetch } from '../../lib/api';
import type { DocumentListOut, DocumentListItem } from '../../types/documents';
import type { ApiError } from '../../lib/api';
import { DOC_TYPE_LABELS } from '../../lib/labels';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const docTypeLabel = (docType: string | null): string =>
  docType ? (DOC_TYPE_LABELS[docType] ?? docType) : 'Chưa phân loại';

type ActiveFilter =
  | 'all' | 'due7' | 'overdue' | 'pending' | 'rights'
  | 'processing' | 'extracted' | 'needs_review';

const PIPELINE_FILTERS: { key: ActiveFilter; label: string }[] = [
  { key: 'processing',   label: 'Đang xử lý' },
  { key: 'extracted',    label: 'Đã bóc tách' },
  { key: 'needs_review', label: 'Cần kiểm tra' },
];

function sortDocs(docs: DocumentListItem[]): DocumentListItem[] {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return [...docs].sort((a, b) => {
    const overdueA = a.next_due_date ? new Date(a.next_due_date) < today : false;
    const overdueB = b.next_due_date ? new Date(b.next_due_date) < today : false;
    const actionA = (overdueA || (!a.confirmed_by_user_at && a.status !== 'processing')) ? 0 : 1;
    const actionB = (overdueB || (!b.confirmed_by_user_at && b.status !== 'processing')) ? 0 : 1;
    if (actionA !== actionB) return actionA - actionB;
    const dateA = a.next_due_date ? new Date(a.next_due_date).getTime() : Infinity;
    const dateB = b.next_due_date ? new Date(b.next_due_date).getTime() : Infinity;
    return dateA - dateB;
  });
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function DirectionCell({ doc }: { doc: DocumentListItem }) {
  if (doc.obligation_count === 0) {
    return <span className="text-ink-subtle text-2xs">—</span>;
  }
  // #279 fields not yet available — show total with ? until backend ships
  if (doc.nghia_vu_count === undefined) {
    return (
      <span className="text-2xs text-ink-muted" title="Chưa xác định nghĩa vụ hay quyền lợi">
        {doc.obligation_count}?
      </span>
    );
  }
  const nv = doc.nghia_vu_count ?? 0;
  const ql = doc.quyen_loi_count ?? 0;
  const nu = doc.direction_null_count ?? 0;
  const parts: React.ReactNode[] = [];
  if (nv > 0) parts.push(
    <span key="nv" className="text-ink">{nv}<span className="text-ink-subtle">↑</span> NV</span>
  );
  if (ql > 0) parts.push(
    <span key="ql" className="text-ink">{ql}<span className="text-ink-subtle">↓</span> QL</span>
  );
  if (nu > 0) parts.push(
    <span key="nu" className="text-ink-muted" title="Chưa xác định nghĩa vụ hay quyền lợi">{nu}?</span>
  );
  return (
    <span className="text-2xs flex items-center gap-1 flex-wrap">
      {parts.map((p, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && <span className="text-ink-subtle">·</span>}
          {p}
        </span>
      ))}
    </span>
  );
}

function DueCell({ doc }: { doc: DocumentListItem }) {
  if (doc.next_due_date) {
    const d = new Date(doc.next_due_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diff = Math.round((d.getTime() - today.getTime()) / 86400000);
    const dm = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
    let label: string;
    let labelClass: string;
    if (diff < 0) {
      label = `quá hạn ${-diff} ngày`;
      labelClass = 'text-danger font-semibold';
    } else if (diff === 0) {
      label = 'hôm nay';
      labelClass = 'text-warning font-semibold';
    } else if (diff <= 7) {
      label = `còn ${diff} ngày`;
      labelClass = 'text-warning';
    } else {
      label = `còn ${diff} ngày`;
      labelClass = 'text-ink-muted';
    }
    return (
      <span className="text-2xs text-ink">
        {dm} <span className="text-ink-subtle">·</span>{' '}
        <span className={labelClass}>{label}</span>
      </span>
    );
  }
  // N3 — standing obligation: ink weight + "Liên tục" pill (not muted italic)
  if (doc.obligation_count > 0) {
    return (
      <span className="text-2xs flex items-center gap-1.5">
        <span className="text-ink font-medium">Cam kết đang hiệu lực</span>
        <span className="inline-flex items-center px-1.5 py-0.5 rounded-pill bg-surface-alt text-ink-muted text-[10px] font-medium border border-border leading-none">
          Liên tục
        </span>
      </span>
    );
  }
  return <span className="text-ink-subtle text-2xs">—</span>;
}

function CompletenessIcon({ value }: { value: boolean | null | undefined }) {
  if (value === false || value === undefined) return null;
  return (
    <span
      className={`ml-1 text-2xs font-bold leading-none ${value === true ? 'text-warning' : 'text-ink-muted'}`}
      title={
        value === true
          ? 'Có thể còn nghĩa vụ chưa bóc — xem chi tiết điều khoản'
          : 'Chưa kiểm tra toàn bộ điều khoản'
      }
    >
      {value === true ? '⚠' : '?'}
    </span>
  );
}

function StatusPill({ doc }: { doc: DocumentListItem }) {
  let label: string;
  let pillClass: string;
  if (doc.status === 'processing') {
    label = 'Đang xử lý';
    pillClass = 'bg-surface-alt text-ink-muted';
  } else if (!doc.confirmed_by_user_at) {
    label = 'Cần xác nhận';
    pillClass = 'bg-warning-soft text-warning';
  } else {
    label = 'Đã xác nhận';
    pillClass = 'bg-primary-soft text-primary';
  }
  return (
    <span className="inline-flex items-center">
      <span className={`inline-flex items-center px-2 py-0.5 rounded-pill text-2xs font-semibold whitespace-nowrap ${pillClass}`}>
        {label}
      </span>
      <CompletenessIcon value={doc.may_have_unextracted_obligations} />
    </span>
  );
}

function FilterChip({
  label, count, active, muted, onClick,
}: {
  label: string;
  count?: number;
  active: boolean;
  muted?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1 px-3 py-1 rounded-pill text-2xs font-medium border transition-colors focus-visible:shadow-ring focus-visible:outline-none
        ${active
          ? 'bg-primary border-primary text-white'
          : muted
            ? 'bg-surface border-border text-ink-muted hover:text-ink'
            : 'bg-surface border-border text-ink hover:bg-surface-alt'
        }`}
    >
      {label}
      {count !== undefined && (
        <span className={`font-semibold ${active ? 'text-white/70' : 'text-ink-subtle'}`}>
          {count}
        </span>
      )}
    </button>
  );
}

function CounterChip({
  children, tone, onClick,
}: {
  children: React.ReactNode;
  tone: 'amber' | 'red' | 'muted';
  onClick?: () => void;
}) {
  const cls =
    tone === 'amber' ? 'border-warning bg-warning-soft text-warning' :
    tone === 'red'   ? 'border-danger bg-danger-soft text-danger' :
                       'border-border bg-surface text-ink-muted';
  return (
    <button
      type="button"
      onClick={onClick}
      className={`border px-3 py-1 rounded-pill text-2xs font-medium focus-visible:shadow-ring focus-visible:outline-none ${cls}`}
    >
      {children}
    </button>
  );
}

// ─── Empty state — zero docs (cold start, DEC-034) ────────────────────────────

function DocListEmpty({ onUpload }: { onUpload: () => void }) {
  return (
    <>
      <div className="flex justify-between items-start gap-4 flex-wrap mb-4">
        <div>
          <h1 className="text-xl font-bold text-ink">Hồ sơ hợp đồng</h1>
          <p className="text-xs text-ink-muted mt-1">
            Chưa có hợp đồng nào — tải lên để Khế bắt đầu theo dõi nghĩa vụ &amp; quyền lợi.
          </p>
        </div>
        <Button onClick={onUpload}>+ Tải hợp đồng</Button>
      </div>

      <div className="border border-dashed border-border-strong rounded-lg bg-surface px-6 py-16 text-center">
        <div className="text-5xl leading-none" aria-hidden="true">📄</div>
        <div className="text-lg font-bold text-ink mt-4">Tải hợp đồng đầu tiên</div>
        <p className="text-xs text-ink-muted max-w-md mx-auto mt-3 leading-relaxed">
          Khế đọc hợp đồng, bóc tách nghĩa vụ (mình phải làm) và quyền lợi (mình được nhận),
          rồi nhắc bạn trước khi tới hạn. Bắt đầu chỉ với một file PDF hoặc ảnh chụp.
        </p>
        <div className="flex gap-3 justify-center mt-6 flex-wrap">
          <Button onClick={onUpload}>+ Tải hợp đồng</Button>
          <Button variant="secondary" onClick={onUpload}>Tải nhiều file (≤20)</Button>
        </div>
        <p className="text-2xs text-ink-subtle mt-6">
          Được onboard theo diện concierge? Đại lý/luật sư của bạn có thể số hóa giúp tận nơi.
        </p>
      </div>
    </>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function DocumentList() {
  const navigate = useNavigate();
  const [data, setData] = useState<DocumentListOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [q, setQ] = useState('');
  const [filter, setFilter] = useState<ActiveFilter>('all');
  const [showPipeline, setShowPipeline] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({ page: '1', page_size: '200' });
      const res = await apiFetch<DocumentListOut>(`/documents/?${params}`);
      setData(res);
      setHydrated(true);
    } catch (err) {
      setError((err as ApiError).message || 'Không thể tải danh sách');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const today = useMemo(() => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d;
  }, []);

  const isOverdue = useCallback(
    (doc: DocumentListItem) =>
      !!doc.next_due_date && new Date(doc.next_due_date) < today,
    [today],
  );

  const isDueSoon = useCallback(
    (doc: DocumentListItem) => {
      if (!doc.next_due_date) return false;
      const diff = Math.round((new Date(doc.next_due_date).getTime() - today.getTime()) / 86400000);
      return diff >= 0 && diff <= 7;
    },
    [today],
  );

  const matchesFilter = useCallback(
    (doc: DocumentListItem): boolean => {
      if (q) {
        const search = q.toLowerCase();
        const haystack = [doc.file_name, doc.primary_party ?? '', docTypeLabel(doc.doc_type)]
          .join(' ')
          .toLowerCase();
        if (!haystack.includes(search)) return false;
      }
      switch (filter) {
        case 'all':          return true;
        case 'due7':         return isDueSoon(doc);
        case 'overdue':      return isOverdue(doc);
        case 'pending':      return !doc.confirmed_by_user_at && doc.status !== 'processing';
        case 'rights':       return (doc.quyen_loi_count ?? 0) > 0;
        case 'processing':   return doc.status === 'processing';
        case 'extracted':    return doc.status === 'extracted';
        case 'needs_review': return doc.status === 'needs_review' || doc.may_have_unextracted_obligations === true;
        default:             return true;
      }
    },
    [q, filter, isDueSoon, isOverdue],
  );

  const counts = useMemo(() => {
    const items = data?.items ?? [];
    return {
      total: data?.total ?? 0,
      pending: items.filter(d => !d.confirmed_by_user_at && d.status !== 'processing').length,
      dueSoon: items.filter(isDueSoon).length,
      overdue: items.filter(isOverdue).length,
      rights:  items.filter(d => (d.quyen_loi_count ?? 0) > 0).length,
    };
  }, [data, isDueSoon, isOverdue]);

  const commitmentFilters = useMemo(() => [
    { key: 'all'     as const, label: 'Tất cả',           count: counts.total   },
    { key: 'due7'    as const, label: 'Tới hạn 7 ngày',   count: counts.dueSoon },
    { key: 'overdue' as const, label: 'Quá hạn',           count: counts.overdue },
    { key: 'pending' as const, label: 'Cần xác nhận',      count: counts.pending },
    { key: 'rights'  as const, label: 'Quyền lợi cần thu', count: counts.rights  },
  ], [counts]);

  const rows = useMemo(
    () => sortDocs((data?.items ?? []).filter(matchesFilter)),
    [data, matchesFilter],
  );

  if (loading && !data) {
    return <div className="py-16 text-center text-xs text-ink-muted">Đang tải…</div>;
  }

  if (error && !data) {
    return <div className="py-16 text-center text-xs text-danger">{error}</div>;
  }

  // Cold start — zero docs, no active filter/search
  if (data && data.total === 0 && !q && filter === 'all') {
    return <DocListEmpty onUpload={() => navigate('/admin/upload')} />;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-start gap-4 flex-wrap mb-4">
        <div>
          <h1 className="text-xl font-bold text-ink">Hồ sơ hợp đồng</h1>
          <p
            className="text-xs text-ink-muted mt-1 transition-opacity duration-fast"
            style={{ opacity: hydrated ? 1 : 0 }}
          >
            {counts.pending} cần xác nhận · {counts.dueSoon} nghĩa vụ tới hạn · {counts.total} hợp đồng
          </p>
        </div>
        <Link to="/admin/upload">
          <Button size="sm">+ Tải hợp đồng</Button>
        </Link>
      </div>

      {/* Counter chips — F2: opacity-0 until hydrated to prevent flash */}
      <div
        className="flex gap-2 flex-wrap mb-5 transition-opacity duration-fast"
        style={{ opacity: hydrated ? 1 : 0 }}
        aria-live="polite"
        aria-label="Tóm tắt danh mục"
      >
        <CounterChip tone="amber" onClick={() => setFilter('pending')}>
          {counts.pending}/{counts.total} cần xác nhận
        </CounterChip>
        <CounterChip
          tone={counts.overdue > 0 ? 'red' : 'muted'}
          onClick={() => setFilter(counts.overdue > 0 ? 'overdue' : 'due7')}
        >
          {counts.dueSoon} NV tới hạn 7 ngày
          {counts.overdue > 0 ? ` · ${counts.overdue} quá hạn` : ''}
        </CounterChip>
        <CounterChip tone="muted">
          {counts.total} hợp đồng
        </CounterChip>
      </div>

      {/* Search */}
      <div className="mb-3">
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="🔍  Tìm theo tên hoặc đối tác..."
          aria-label="Tìm kiếm hợp đồng"
          className="w-full max-w-sm h-10 px-3 text-xs border border-border rounded-md bg-surface text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
      </div>

      {/* Filter row 1 — commitment (always visible) */}
      <div className="flex gap-2 flex-wrap mb-2" role="group" aria-label="Lọc theo cam kết">
        {commitmentFilters.map(f => (
          <FilterChip
            key={f.key}
            label={f.label}
            count={f.count}
            active={filter === f.key}
            onClick={() => setFilter(f.key)}
          />
        ))}
        <button
          type="button"
          onClick={() => setShowPipeline(s => !s)}
          className="text-2xs text-ink-muted hover:text-ink px-2 py-1 focus-visible:shadow-ring focus-visible:outline-none rounded"
        >
          {showPipeline ? 'Ẩn trạng thái xử lý ▴' : 'Trạng thái xử lý ▾'}
        </button>
      </div>

      {/* Filter row 2 — pipeline (collapsible) — F1: 3 chips */}
      {showPipeline && (
        <div className="flex gap-2 flex-wrap mb-2" role="group" aria-label="Lọc theo trạng thái xử lý">
          {PIPELINE_FILTERS.map(f => (
            <FilterChip
              key={f.key}
              label={f.label}
              active={filter === f.key}
              muted
              onClick={() => setFilter(f.key)}
            />
          ))}
        </div>
      )}

      {/* Glyph legend (G7) */}
      <p className="text-2xs text-ink-muted mb-3 mt-1">
        <strong className="text-ink font-semibold">↑ NV</strong> = nghĩa vụ (mình phải làm) ·{' '}
        <strong className="text-ink font-semibold">↓ QL</strong> = quyền lợi (mình được nhận) ·{' '}
        <strong className="text-ink font-semibold">?</strong> = chưa xác định
      </p>

      {error && <div className="mb-3 text-xs text-danger">{error}</div>}

      {/* 5-column table */}
      <div className="border border-border rounded-lg overflow-hidden">
        <table className="w-full border-collapse">
          <colgroup>
            <col style={{ width: '34%' }} />
            <col style={{ width: '12%' }} />
            <col style={{ width: '18%' }} />
            <col style={{ width: '18%' }} />
            <col style={{ width: '18%' }} />
          </colgroup>
          <thead>
            <tr>
              {(['Hợp đồng', 'Loại', 'Nghĩa vụ · Quyền lợi', 'Hạn gần nhất', 'Trạng thái'] as const).map(col => (
                <th
                  key={col}
                  className="text-left px-3 py-2 text-2xs font-semibold text-ink-muted uppercase tracking-wide border-b border-border bg-surface whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-3 py-10 text-center text-xs text-ink-muted">
                  Không có hợp đồng phù hợp bộ lọc.
                </td>
              </tr>
            ) : rows.map(doc => (
              <tr
                key={doc.id}
                onClick={() => navigate(`/admin/documents/${doc.id}`)}
                className="cursor-pointer hover:bg-surface-alt transition-colors border-b border-border last:border-0 group"
              >
                {/* Col 1 — Hợp đồng */}
                <td className="px-3 py-3 align-middle">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="text-xs font-medium text-ink group-hover:underline truncate">
                      HĐ {docTypeLabel(doc.doc_type)} với {doc.primary_party ?? doc.file_name}
                    </span>
                    {doc.duplicate && (
                      <span
                        className="shrink-0 text-warning font-bold text-xs cursor-help"
                        title="Tệp trùng — kiểm tra"
                        aria-label="Cảnh báo: tệp trùng"
                      >
                        !
                      </span>
                    )}
                  </div>
                  <div className="text-2xs text-ink-muted mt-0.5 truncate max-w-xs">
                    {doc.file_name}
                  </div>
                </td>
                {/* Col 2 — Loại */}
                <td className="px-3 py-3 align-middle text-2xs text-ink-muted">
                  {docTypeLabel(doc.doc_type)}
                </td>
                {/* Col 3 — Nghĩa vụ · Quyền lợi */}
                <td className="px-3 py-3 align-middle">
                  <DirectionCell doc={doc} />
                </td>
                {/* Col 4 — Hạn gần nhất */}
                <td className="px-3 py-3 align-middle">
                  <DueCell doc={doc} />
                </td>
                {/* Col 5 — Trạng thái */}
                <td className="px-3 py-3 align-middle">
                  <StatusPill doc={doc} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
