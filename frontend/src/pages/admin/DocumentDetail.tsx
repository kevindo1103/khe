import { useState, useEffect, useCallback, useMemo } from 'react';
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
} from '../../types/documents';
import type { ObligationOut } from '../../types/obligations';
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

// ── Single obligation row ────────────────────────────────────────────────────
function ObligationRow({ ob }: { ob: ObligationOut }) {
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
          </div>
        </div>
        <div className="flex-shrink-0 mt-0.5">
          {ob.status === 'done' ? (
            <Badge kind="done">✓ hoàn thành</Badge>
          ) : ob.status === 'cancelled' ? (
            <Badge kind="neutral">đã hủy</Badge>
          ) : (
            <Link to="/admin/obligations" className="text-xs text-primary hover:underline">
              Quản lý →
            </Link>
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

// ── Clause accordion item ────────────────────────────────────────────────────
function ClauseItem({ clause, defaultOpen }: { clause: ClauseOut; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const title =
    clause.title ||
    (clause.clause_number ? `Điều ${clause.clause_number}` : `Điều khoản #${clause.id}`);
  return (
    <div className="border-b border-border last:border-0">
      <button
        className="w-full flex items-center justify-between py-3 text-left gap-2 hover:bg-surface-hover transition-colors"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="text-sm font-medium text-ink">{title}</span>
        <div className="flex items-center gap-2 flex-shrink-0">
          {clause.page_number != null && (
            <span className="text-2xs text-ink-muted">tr.{clause.page_number}</span>
          )}
          <span className="text-ink-muted text-xs">{open ? '▲' : '▼'}</span>
        </div>
      </button>
      {open && (
        <div className="pb-3 text-sm text-ink-muted leading-relaxed whitespace-pre-wrap">
          {clause.content}
        </div>
      )}
    </div>
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
}: {
  doc: DocumentDetailOut;
  selectedRole: string;
  confirming: boolean;
  onSelectRole: (v: string) => void;
  onConfirmSelfParty: () => void;
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
            <ObligationRow key={ob.id} ob={ob} />
          ))}
        </Card>
      )}

      {quyenLoi.length > 0 && (
        <Card title={`Được hưởng (${quyenLoi.length})`} className="mb-4">
          {quyenLoi.map((ob) => (
            <ObligationRow key={ob.id} ob={ob} />
          ))}
        </Card>
      )}

      {chuaRo.length > 0 && (
        <Card title={`Chưa rõ hướng (${chuaRo.length})`} className="mb-4">
          {chuaRo.map((ob) => (
            <ObligationRow key={ob.id} ob={ob} />
          ))}
        </Card>
      )}

      {reviewObs.length > 0 && (
        <Card title={`Review / kiểm tra định kỳ (${reviewObs.length})`} className="mb-4">
          {reviewObs.map((ob) => (
            <ObligationRow key={ob.id} ob={ob} />
          ))}
        </Card>
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
}: {
  clauses: ClauseOut[];
  loading: boolean;
  total: number;
  error: boolean;
  onRetry: () => void;
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
  const defaultOpen = clauses.length <= 8;
  return (
    <div>
      <div className="text-xs text-ink-muted mb-3">{total} điều khoản</div>
      <Card>
        {clauses.map((c) => (
          <ClauseItem key={c.id} clause={c} defaultOpen={defaultOpen} />
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
      setClauses(res.items);
      setClausesTotal(res.total);
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
                <h1 className="text-xl font-bold text-ink leading-tight">{derivedTitle}</h1>
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
            <TabObligations
              doc={doc}
              selectedRole={selectedRole}
              confirming={confirming}
              onSelectRole={setSelectedRole}
              onConfirmSelfParty={confirmSelfParty}
            />
          )}

          {activeTab === 'clauses' && (
            <TabClauses
              clauses={clauses}
              loading={clausesLoading}
              total={clausesTotal}
              error={clausesError}
              onRetry={() => { setClausesLoaded(false); setClausesError(false); }}
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
