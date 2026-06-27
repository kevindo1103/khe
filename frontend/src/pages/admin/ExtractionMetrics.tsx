import { useState, useMemo } from 'react';
import { Card, Badge } from '../../components';

interface MetricRow {
  document_id: number;
  tenant_slug: string;
  filename: string;
  doc_type: string | null;
  provider: string | null;
  cost_vnd: number | null;
  latency_ms: number | null;
  clause_count: number;
  party_count: number;
  obligation_count: number;
  low_confidence_count: number;
  warnings: string[];
  created_at: string;
}

const QUALITY_THRESHOLDS = {
  clauses: 10,
  parties: 2,
  obligations: 1,
};

const MOCK_DATA: MetricRow[] = [
  {
    document_id: 1, tenant_slug: 'uat-demo', filename: 'hop-dong-thue-mat-bang-quan1.pdf',
    doc_type: 'hd_thue_mat_bang', provider: 'hybrid_ocr', cost_vnd: 966,
    latency_ms: 105000, clause_count: 14, party_count: 2, obligation_count: 16,
    low_confidence_count: 0, warnings: [], created_at: '2026-06-27T10:30:00',
  },
  {
    document_id: 2, tenant_slug: 'uat-demo', filename: 'hop-dong-lao-dong-nv01.pdf',
    doc_type: 'hd_lao_dong', provider: 'hybrid_ocr', cost_vnd: 1191,
    latency_ms: 105000, clause_count: 11, party_count: 2, obligation_count: 15,
    low_confidence_count: 1, warnings: ['hybrid:docai_ocr | OCR 381d + LLM 810d'],
    created_at: '2026-06-26T14:20:00',
  },
  {
    document_id: 3, tenant_slug: 'uat-demo', filename: 'hop-dong-mua-ban-thiet-bi.pdf',
    doc_type: 'hd_mua_ban', provider: 'gemini_flash', cost_vnd: 500,
    latency_ms: 40000, clause_count: 8, party_count: 1, obligation_count: 8,
    low_confidence_count: 3, warnings: [], created_at: '2026-06-25T09:15:00',
  },
  {
    document_id: 4, tenant_slug: 'pilot-firm-a', filename: 'hd-dich-vu-ke-toan-2026.pdf',
    doc_type: 'hd_dich_vu', provider: 'gemini_flash', cost_vnd: 585,
    latency_ms: 52000, clause_count: 12, party_count: 2, obligation_count: 10,
    low_confidence_count: 0, warnings: [], created_at: '2026-06-24T16:45:00',
  },
  {
    document_id: 5, tenant_slug: 'pilot-firm-a', filename: 'phu-luc-hop-dong-thue.pdf',
    doc_type: 'phu_luc', provider: 'claude_haiku', cost_vnd: 560,
    latency_ms: 38000, clause_count: 5, party_count: 2, obligation_count: 3,
    low_confidence_count: 2, warnings: ['fallback:claude_haiku — gemini quota exceeded'],
    created_at: '2026-06-23T11:00:00',
  },
  {
    document_id: 6, tenant_slug: 'uat-demo', filename: 'bien-ban-giao-mat-bang.pdf',
    doc_type: 'bien_ban', provider: 'hybrid_ocr', cost_vnd: 780,
    latency_ms: 88000, clause_count: 6, party_count: 2, obligation_count: 4,
    low_confidence_count: 1, warnings: [], created_at: '2026-06-22T08:30:00',
  },
];

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

function formatDate(iso: string): string {
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

export default function ExtractionMetrics() {
  const [tenantFilter, setTenantFilter] = useState('');
  const [providerFilter, setProviderFilter] = useState('');
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('created_at');
  const [sortAsc, setSortAsc] = useState(false);

  const tenants = useMemo(() => [...new Set(MOCK_DATA.map((r) => r.tenant_slug))], []);
  const providers = useMemo(() => [...new Set(MOCK_DATA.map((r) => r.provider).filter(Boolean) as string[])], []);

  const filtered = useMemo(() => {
    let rows = MOCK_DATA;
    if (tenantFilter) rows = rows.filter((r) => r.tenant_slug === tenantFilter);
    if (providerFilter) rows = rows.filter((r) => r.provider === providerFilter);
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((r) => r.filename.toLowerCase().includes(q));
    }
    if (dateFrom) rows = rows.filter((r) => r.created_at >= dateFrom);
    if (dateTo) rows = rows.filter((r) => r.created_at <= dateTo + 'T23:59:59');
    return [...rows].sort((a, b) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      if (av < bv) return sortAsc ? -1 : 1;
      if (av > bv) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [tenantFilter, providerFilter, search, dateFrom, dateTo, sortKey, sortAsc]);

  const totalDocs = filtered.length;
  const avgCost = totalDocs > 0 ? filtered.reduce((s, r) => s + (r.cost_vnd ?? 0), 0) / totalDocs : 0;
  const avgLatency = totalDocs > 0 ? filtered.reduce((s, r) => s + (r.latency_ms ?? 0), 0) / totalDocs : 0;
  const passRate = totalDocs > 0 ? (filtered.filter(passesAll).length / totalDocs) * 100 : 0;

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
        <p className="text-2xs text-ink-muted mt-1">Mock data — API: #346 (chưa merge)</p>
      </div>

      <div className="grid grid-cols-2 gap-3 nav:grid-cols-4">
        <Card>
          <div className="text-2xl font-bold text-ink">{totalDocs}</div>
          <div className="text-xs text-ink-muted mt-1">Documents</div>
        </Card>
        <Card>
          <div className="text-2xl font-bold text-ink">{formatCost(avgCost)}</div>
          <div className="text-xs text-ink-muted mt-1">Avg cost</div>
        </Card>
        <Card>
          <div className="text-2xl font-bold text-ink">{formatLatency(avgLatency)}</div>
          <div className="text-xs text-ink-muted mt-1">Avg latency</div>
        </Card>
        <Card>
          <div className={`text-2xl font-bold ${passRate >= 80 ? 'text-success' : passRate >= 50 ? 'text-warning' : 'text-danger'}`}>
            {passRate.toFixed(0)}%
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
