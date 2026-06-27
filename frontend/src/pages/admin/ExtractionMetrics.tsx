import { useState, useMemo } from 'react';
import { Card, Table, Badge } from '../../components';

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

const QUALITY_THRESHOLDS = {
  clauses: 10,
  parties: 2,
  obligations: 1,
};

const MOCK_DATA: MetricRow[] = [
  {
    document_id: 1, tenant_slug: 'uat-demo', filename: 'hop-dong-thue-mat-bang-quan1.pdf',
    doc_type: 'hd_thue_mat_bang', provider: 'hybrid_ocr', model: 'gemini-2.5-flash',
    cost_vnd: 966.1, latency_ms: 105000, clause_count: 14, party_count: 2,
    obligation_count: 16, field_count: 12, low_confidence_count: 0, warnings: [], created_at: '2026-06-27T10:30:00',
  },
  {
    document_id: 2, tenant_slug: 'uat-demo', filename: 'hop-dong-lao-dong-nv01.pdf',
    doc_type: 'hd_lao_dong', provider: 'hybrid_ocr', model: 'gemini-2.5-flash',
    cost_vnd: 1191, latency_ms: 105000, clause_count: 11, party_count: 2,
    obligation_count: 15, field_count: 14, low_confidence_count: 1, warnings: ['hybrid:docai_ocr | OCR 381d + LLM 810d'], created_at: '2026-06-26T14:20:00',
  },
  {
    document_id: 3, tenant_slug: 'uat-demo', filename: 'hop-dong-mua-ban-thiet-bi.pdf',
    doc_type: 'hd_mua_ban', provider: 'gemini_flash', model: 'gemini-2.5-flash',
    cost_vnd: 500, latency_ms: 40000, clause_count: 8, party_count: 1,
    obligation_count: 8, field_count: 10, low_confidence_count: 3, warnings: [], created_at: '2026-06-25T09:15:00',
  },
  {
    document_id: 4, tenant_slug: 'pilot-firm-a', filename: 'hd-dich-vu-ke-toan-2026.pdf',
    doc_type: 'hd_dich_vu', provider: 'gemini_flash', model: 'gemini-2.5-flash',
    cost_vnd: 585, latency_ms: 52000, clause_count: 12, party_count: 2,
    obligation_count: 10, field_count: 11, low_confidence_count: 0, warnings: [], created_at: '2026-06-24T16:45:00',
  },
  {
    document_id: 5, tenant_slug: 'pilot-firm-a', filename: 'phu-luc-hop-dong-thue.pdf',
    doc_type: 'phu_luc', provider: 'claude_haiku', model: 'claude-haiku-4.5',
    cost_vnd: 560, latency_ms: 38000, clause_count: 5, party_count: 2,
    obligation_count: 3, field_count: 8, low_confidence_count: 2, warnings: ['fallback:claude_haiku — gemini quota exceeded'], created_at: '2026-06-23T11:00:00',
  },
  {
    document_id: 6, tenant_slug: 'uat-demo', filename: 'bien-ban-giao-mat-bang.pdf',
    doc_type: 'bien_ban', provider: 'hybrid_ocr', model: 'gemini-2.5-flash',
    cost_vnd: 780, latency_ms: 88000, clause_count: 6, party_count: 2,
    obligation_count: 4, field_count: 9, low_confidence_count: 1, warnings: [], created_at: '2026-06-22T08:30:00',
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

function QualityIndicator({ value, threshold }: { value: number; threshold: number }) {
  const pass = value >= threshold;
  return (
    <span className={pass ? 'text-success font-medium' : 'text-danger font-medium'}>
      {value} {pass ? '✅' : '❌'}
    </span>
  );
}

function formatCost(vnd: number | null): string {
  if (vnd == null) return '—';
  return `${Math.round(vnd).toLocaleString('vi-VN')}d`;
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
  return s.length > max ? s.slice(0, max) + '...' : s;
}

export default function ExtractionMetrics() {
  const [tenantFilter, setTenantFilter] = useState('');
  const [providerFilter, setProviderFilter] = useState('');
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('created_at');
  const [sortAsc, setSortAsc] = useState(false);

  const tenants = useMemo(() => [...new Set(MOCK_DATA.map((r) => r.tenant_slug))], []);
  const providers = useMemo(() => [...new Set(MOCK_DATA.map((r) => r.provider).filter(Boolean))], []);

  const filtered = useMemo(() => {
    let rows = MOCK_DATA;
    if (tenantFilter) rows = rows.filter((r) => r.tenant_slug === tenantFilter);
    if (providerFilter) rows = rows.filter((r) => r.provider === providerFilter);
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((r) => r.filename.toLowerCase().includes(q));
    }
    const sorted = [...rows].sort((a, b) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      if (av < bv) return sortAsc ? -1 : 1;
      if (av > bv) return sortAsc ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [tenantFilter, providerFilter, search, sortKey, sortAsc]);

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

  const sortArrow = (key: SortKey) => (sortKey === key ? (sortAsc ? ' ↑' : ' ↓') : '');

  const columns = [
    { key: 'tenant_slug', label: 'Tenant' },
    { key: 'document', label: 'Document' },
    { key: 'doc_type', label: 'Loai' },
    { key: 'provider', label: 'Provider' },
    { key: 'cost_vnd', label: `Chi phi${sortArrow('cost_vnd')}` },
    { key: 'latency_ms', label: `Latency${sortArrow('latency_ms')}` },
    { key: 'clause_count', label: `Clauses${sortArrow('clause_count')}` },
    { key: 'party_count', label: `Parties${sortArrow('party_count')}` },
    { key: 'obligation_count', label: `Obligations${sortArrow('obligation_count')}` },
    { key: 'low_confidence', label: 'Low conf.' },
    { key: 'created_at', label: `Ngay${sortArrow('created_at')}` },
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-ink">Extraction Metrics</h1>
      <p className="text-sm text-ink-muted">Mock data — API dependency: #346</p>

      {/* Summary cards */}
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

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={tenantFilter}
          onChange={(e) => setTenantFilter(e.target.value)}
          className="text-xs border border-border rounded-md px-2 py-1.5 bg-surface text-ink"
        >
          <option value="">All tenants</option>
          {tenants.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        <select
          value={providerFilter}
          onChange={(e) => setProviderFilter(e.target.value)}
          className="text-xs border border-border rounded-md px-2 py-1.5 bg-surface text-ink"
        >
          <option value="">All providers</option>
          {providers.map((p) => (
            <option key={p} value={p!}>{p}</option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Search filename..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="text-xs border border-border rounded-md px-2 py-1.5 bg-surface text-ink min-w-[180px]"
        />
      </div>

      {/* Table */}
      <Table<MetricRow>
        columns={columns}
        rows={filtered}
        renderCell={(key, row) => {
          switch (key) {
            case 'tenant_slug':
              return <span className="text-ink-muted">{row.tenant_slug}</span>;
            case 'document':
              return (
                <span title={row.filename}>
                  <span className="text-ink-muted text-2xs">#{row.document_id}</span>{' '}
                  {truncate(row.filename, 28)}
                </span>
              );
            case 'doc_type':
              return <span className="text-ink-muted">{row.doc_type ?? '—'}</span>;
            case 'provider':
              return <Badge kind={row.provider === 'claude_haiku' ? 'needs_review' : 'extracted'}>{row.provider ?? '—'}</Badge>;
            case 'cost_vnd':
              return (
                <button type="button" className="hover:underline" onClick={() => handleSort('cost_vnd')}>
                  {formatCost(row.cost_vnd)}
                </button>
              );
            case 'latency_ms':
              return (
                <button type="button" className="hover:underline" onClick={() => handleSort('latency_ms')}>
                  {formatLatency(row.latency_ms)}
                </button>
              );
            case 'clause_count':
              return (
                <button type="button" className="hover:underline" onClick={() => handleSort('clause_count')}>
                  <QualityIndicator value={row.clause_count} threshold={QUALITY_THRESHOLDS.clauses} />
                </button>
              );
            case 'party_count':
              return (
                <button type="button" className="hover:underline" onClick={() => handleSort('party_count')}>
                  <QualityIndicator value={row.party_count} threshold={QUALITY_THRESHOLDS.parties} />
                </button>
              );
            case 'obligation_count':
              return (
                <button type="button" className="hover:underline" onClick={() => handleSort('obligation_count')}>
                  <QualityIndicator value={row.obligation_count} threshold={QUALITY_THRESHOLDS.obligations} />
                </button>
              );
            case 'low_confidence':
              return row.low_confidence_count > 0
                ? <span className="text-warning font-medium">{row.low_confidence_count}</span>
                : <span className="text-ink-muted">0</span>;
            case 'created_at':
              return (
                <button type="button" className="hover:underline" onClick={() => handleSort('created_at')}>
                  {formatDate(row.created_at)}
                </button>
              );
            default:
              return String((row as unknown as Record<string, unknown>)[key] ?? '');
          }
        }}
      />
    </div>
  );
}
