import { useState, useEffect, useMemo, useCallback } from 'react';
import { Card, Badge } from '../../components';
import { apiFetch } from '../../lib/api';

interface MetricRow {
  document_id: number;
  tenant_slug: string;
  filename: string;
  doc_type: string | null;
  provider: string | null;
  model: string | null;
  cost_vnd: number | null;
  latency_ms: number | null;
  clause_count: number;
  party_count: number;
  obligation_count: number;
  field_count: number;
  low_confidence_count: number;
  warnings: string[];
  created_at: string | null;
}

interface MetricsResponse {
  items: MetricRow[];
  total: number;
  page: number;
  page_size: number;
}

interface MetricsSummary {
  total_docs: number;
  avg_cost_vnd: number | null;
  avg_latency_ms: number | null;
  total_cost_vnd: number;
  cost_by_provider: Record<string, number>;
  cost_by_tenant: Record<string, number>;
}

const QUALITY_THRESHOLDS = {
  clauses: 10,
  parties: 2,
  obligations: 1,
};

type SortKey = 'cost_vnd' | 'latency_ms' | 'clause_count' | 'party_count' | 'obligation_count' | 'created_at';

function passesAll(row: MetricRow): boolean {
  return (
    row.clause_count >= QUALITY_THRESHOLDS.clauses &&
    row.party_count >= QUALITY_THRESHOLDS.parties &&
    row.obligation_count >= QUALITY_THRESHOLDS.obligations
  );
}

function formatCost(vnd: number | null): string {
  if (vnd == null) return '—';
  return `${Math.round(vnd).toLocaleString('vi-VN')}đ`;
}

function formatLatency(ms: number | null): string {
  if (ms == null) return '—';
  return `${(ms / 1000).toFixed(0)}s`;
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function truncate(s: string, max: number): string {
  return s.length > max ? s.slice(0, max) + '…' : s;
}

function QualityCell({ value, threshold }: { value: number; threshold: number }) {
  const pass = value >= threshold;
  return (
    <span className={pass ? 'text-success font-medium' : 'text-danger font-medium'}>
      {value} {pass ? '✅' : '❌'}
    </span>
  );
}

function SortableHeader({
  label,
  sortKey: key,
  currentKey,
  asc,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  currentKey: SortKey;
  asc: boolean;
  onSort: (k: SortKey) => void;
}) {
  const active = currentKey === key;
  return (
    <button
      type="button"
      onClick={() => onSort(key)}
      className={`inline-flex items-center gap-0.5 hover:text-ink transition-colors ${active ? 'text-ink font-bold' : ''}`}
    >
      {label}
      {active && <span className="text-2xs">{asc ? '↑' : '↓'}</span>}
    </button>
  );
}

function providerBadgeKind(provider: string | null): 'extracted' | 'needs_review' | 'neutral' {
  if (provider === 'claude_haiku') return 'needs_review';
  if (provider === 'gemini_flash' || provider === 'hybrid_ocr') return 'extracted';
  return 'neutral';
}

function buildQueryString(params: Record<string, string | undefined>): string {
  const entries = Object.entries(params).filter(
    (pair): pair is [string, string] => pair[1] != null && pair[1] !== '',
  );
  return entries.length > 0 ? '?' + new URLSearchParams(entries).toString() : '';
}

export default function ExtractionMetrics() {
  const [rows, setRows] = useState<MetricRow[]>([]);
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [tenantFilter, setTenantFilter] = useState('');
  const [providerFilter, setProviderFilter] = useState('');
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('created_at');
  const [sortAsc, setSortAsc] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError('');
    const qs = buildQueryString({
      tenant: tenantFilter || undefined,
      provider: providerFilter || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      page_size: '200',
    });
    const summaryQs = buildQueryString({
      tenant: tenantFilter || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    });
    try {
      const [metricsRes, summaryRes] = await Promise.all([
        apiFetch<MetricsResponse>(`/admin/extraction-metrics${qs}`),
        apiFetch<MetricsSummary>(`/admin/extraction-metrics/summary${summaryQs}`),
      ]);
      setRows(metricsRes.items);
      setSummary(summaryRes);
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'message' in err
        ? (err as { message: string }).message
        : 'Không tải được dữ liệu';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [tenantFilter, providerFilter, dateFrom, dateTo]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const tenants = useMemo(() => [...new Set(rows.map((r) => r.tenant_slug))], [rows]);
  const providers = useMemo(() => [...new Set(rows.map((r) => r.provider).filter(Boolean) as string[])], [rows]);

  const filtered = useMemo(() => {
    let result = rows;
    if (search) {
      const q = search.toLowerCase();
      result = result.filter((r) => r.filename.toLowerCase().includes(q));
    }
    return [...result].sort((a, b) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      if (av < bv) return sortAsc ? -1 : 1;
      if (av > bv) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [rows, search, sortKey, sortAsc]);

  const passRate = filtered.length > 0
    ? (filtered.filter(passesAll).length / filtered.length) * 100
    : 0;

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  const selectClass = 'text-xs border border-border rounded-md px-2 py-1.5 bg-surface text-ink focus-visible:shadow-ring focus-visible:outline-none';
  const thClass = 'text-left px-3 py-2 text-ink-muted font-semibold border-b border-border-strong whitespace-nowrap';

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-ink">Extraction Metrics</h1>
        {error && <p className="text-sm text-danger mt-1">{error}</p>}
      </div>

      <div className="grid grid-cols-2 gap-3 nav:grid-cols-4">
        <Card>
          <div className="text-2xl font-bold text-ink">{summary?.total_docs ?? '—'}</div>
          <div className="text-xs text-ink-muted mt-1">Documents</div>
        </Card>
        <Card>
          <div className="text-2xl font-bold text-ink">{formatCost(summary?.avg_cost_vnd ?? null)}</div>
          <div className="text-xs text-ink-muted mt-1">Avg cost</div>
        </Card>
        <Card>
          <div className="text-2xl font-bold text-ink">{formatLatency(summary?.avg_latency_ms ?? null)}</div>
          <div className="text-xs text-ink-muted mt-1">Avg latency</div>
        </Card>
        <Card>
          <div className={`text-2xl font-bold ${passRate >= 80 ? 'text-success' : passRate >= 50 ? 'text-warning' : 'text-danger'}`}>
            {filtered.length > 0 ? `${passRate.toFixed(0)}%` : '—'}
          </div>
          <div className="text-xs text-ink-muted mt-1">Pass rate</div>
        </Card>
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        <select value={tenantFilter} onChange={(e) => setTenantFilter(e.target.value)} className={selectClass}>
          <option value="">All tenants</option>
          {tenants.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={providerFilter} onChange={(e) => setProviderFilter(e.target.value)} className={selectClass}>
          <option value="">All providers</option>
          {providers.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className={selectClass}
          aria-label="From date"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className={selectClass}
          aria-label="To date"
        />
        <input
          type="text"
          placeholder="Tìm filename…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={`${selectClass} min-w-[180px]`}
        />
      </div>

      {loading ? (
        <div className="text-sm text-ink-muted py-8 text-center">Đang tải…</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                <th className={thClass}>Tenant</th>
                <th className={thClass}>Document</th>
                <th className={thClass}>Loại</th>
                <th className={thClass}>Provider</th>
                <th className={thClass}>
                  <SortableHeader label="Chi phí" sortKey="cost_vnd" currentKey={sortKey} asc={sortAsc} onSort={handleSort} />
                </th>
                <th className={thClass}>
                  <SortableHeader label="Latency" sortKey="latency_ms" currentKey={sortKey} asc={sortAsc} onSort={handleSort} />
                </th>
                <th className={thClass}>
                  <SortableHeader label="Clauses" sortKey="clause_count" currentKey={sortKey} asc={sortAsc} onSort={handleSort} />
                </th>
                <th className={thClass}>
                  <SortableHeader label="Parties" sortKey="party_count" currentKey={sortKey} asc={sortAsc} onSort={handleSort} />
                </th>
                <th className={thClass}>
                  <SortableHeader label="Obligations" sortKey="obligation_count" currentKey={sortKey} asc={sortAsc} onSort={handleSort} />
                </th>
                <th className={thClass}>Low conf.</th>
                <th className={thClass}>
                  <SortableHeader label="Ngày" sortKey="created_at" currentKey={sortKey} asc={sortAsc} onSort={handleSort} />
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr key={`${row.tenant_slug}-${row.document_id}`} className="border-b border-border hover:bg-surface-alt transition-colors">
                  <td className="px-3 py-2 text-ink-muted">{row.tenant_slug}</td>
                  <td className="px-3 py-2" title={row.filename}>
                    <span className="text-ink-muted text-2xs">#{row.document_id}</span>{' '}
                    {truncate(row.filename, 28)}
                  </td>
                  <td className="px-3 py-2 text-ink-muted">{row.doc_type ?? '—'}</td>
                  <td className="px-3 py-2">
                    <Badge kind={providerBadgeKind(row.provider)}>{row.provider ?? '—'}</Badge>
                  </td>
                  <td className="px-3 py-2">{formatCost(row.cost_vnd)}</td>
                  <td className="px-3 py-2">{formatLatency(row.latency_ms)}</td>
                  <td className="px-3 py-2">
                    <QualityCell value={row.clause_count} threshold={QUALITY_THRESHOLDS.clauses} />
                  </td>
                  <td className="px-3 py-2">
                    <QualityCell value={row.party_count} threshold={QUALITY_THRESHOLDS.parties} />
                  </td>
                  <td className="px-3 py-2">
                    <QualityCell value={row.obligation_count} threshold={QUALITY_THRESHOLDS.obligations} />
                  </td>
                  <td className="px-3 py-2">
                    {row.low_confidence_count > 0
                      ? <span className="text-warning font-medium">{row.low_confidence_count}</span>
                      : <span className="text-ink-muted">0</span>}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">{formatDate(row.created_at)}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={11} className="px-3 py-8 text-center text-ink-muted">
                    Không tìm thấy kết quả phù hợp.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {filtered.some((r) => r.warnings.length > 0) && (
        <div className="space-y-1">
          <div className="text-xs font-semibold text-ink-muted">Warnings</div>
          {filtered
            .filter((r) => r.warnings.length > 0)
            .map((r) => (
              <div key={`${r.tenant_slug}-${r.document_id}-warn`} className="text-2xs text-warning bg-warning-soft border border-warning-border rounded-md px-3 py-1.5">
                #{r.document_id} {truncate(r.filename, 20)}: {r.warnings.join('; ')}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
