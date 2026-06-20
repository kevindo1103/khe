import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button, Card, Badge, Input, ConfidenceMeter, Toast, EmptyState } from '../../components';
import { apiFetch } from '../../lib/api';
import type { DocumentDetailOut, TermOut, SelfPartyConfirmOut } from '../../types/documents';
import type { ObligationOut } from '../../types/obligations';
import type { ApiError } from '../../lib/api';
import {
  DOC_TYPE_GROUP_LABELS,
  OBLIGATION_TYPE_LABELS,
  DIRECTION_LABELS,
  CANONICAL_FIELDS,
  FIELD_LABELS,
  labelFor,
} from '../../lib/labels';

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const docId = Number(id);

  const [doc, setDoc] = useState<DocumentDetailOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [toastMsg, setToastMsg] = useState<string>('');
  const [editingTermId, setEditingTermId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [saving, setSaving] = useState(false);
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [confirming, setConfirming] = useState(false);

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

  useEffect(() => {
    load();
  }, [load]);

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
      // Optimistic update
      setDoc((prev) =>
        prev
          ? {
              ...prev,
              terms: prev.terms.map((t) =>
                t.id === termId
                  ? { ...t, field_value: editValue, needs_review: false }
                  : t
              ),
            }
          : prev
      );
      setToastMsg('Đã cập nhật — ghi Event ✓');
      setEditingTermId(null);
    } catch (err) {
      setError((err as ApiError).message || 'Lưu thất bại');
    } finally {
      setSaving(false);
    }
  };

  const STATUS_LABEL: Record<string, string> = {
    processing: 'Đang xử lý',
    extracted: 'Đã bóc tách',
    needs_review: 'Cần kiểm tra',
  };

  const STATUS_BADGE: Record<string, 'processing' | 'extracted' | 'needs_review'> = {
    processing: 'processing',
    extracted: 'extracted',
    needs_review: 'needs_review',
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
          {term.needs_review && (
            <Badge kind="needs_review">Cần kiểm tra</Badge>
          )}
        </div>
        {editingTermId === term.id ? (
          <div className="flex gap-2 items-center">
            <Input
              value={editValue}
              onChange={setEditValue}
              className="flex-1"
            />
            <Button
              size="sm"
              onClick={() => saveEdit(term.id)}
              loading={saving}
            >
              Lưu
            </Button>
            <Button size="sm" variant="ghost" onClick={cancelEdit}>
              Hủy
            </Button>
          </div>
        ) : (
          <div className="text-sm text-ink">
            {term.field_value || '—'}
          </div>
        )}
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {term.confidence !== null && (
          <ConfidenceMeter value={term.confidence} />
        )}
        {editingTermId !== term.id && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => startEdit(term)}
          >
            Sửa
          </Button>
        )}
      </div>
    </div>
  );

  const hasNullDirection = useMemo(() => {
    if (!doc) return false;
    return doc.obligations.some((ob) => ob.direction === null);
  }, [doc]);

  const showSelfPartyConfirm = useMemo(() => {
    if (!doc) return false;
    return (doc.parties?.length ?? 0) > 0 && hasNullDirection;
  }, [doc, hasNullDirection]);

  const confirmSelfParty = async () => {
    if (!docId || !selectedRole) return;
    setConfirming(true);
    setError('');
    try {
      const res = await apiFetch<SelfPartyConfirmOut>(
        `/documents/${docId}/confirm_self_party`,
        {
          method: 'POST',
          body: JSON.stringify({ role_label: selectedRole }),
        }
      );
      setToastMsg(
        `Đã xác nhận — ${res.updated} nghĩa vụ đã cập nhật hướng.`
      );
      setSelectedRole('');
      await load();
    } catch (err) {
      setError((err as ApiError).message || 'Xác nhận thất bại');
    } finally {
      setConfirming(false);
    }
  };

  if (loading && !doc) {
    return <div className="p-8 text-center text-ink-muted text-sm">Đang tải…</div>;
  }

  if (error && !doc) {
    return (
      <EmptyState
        icon="⚠️"
        title="Không tìm thấy tài liệu"
        description={error}
      />
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Link to="/admin/documents" className="text-sm text-ink-muted hover:text-primary">
          ← Tài liệu
        </Link>
      </div>

      {doc && (
        <>
          <div className="flex justify-between items-start flex-wrap gap-3 mb-4">
            <div>
              <h1 className="text-xl font-bold text-ink">{doc.file_name}</h1>
              <div className="flex gap-2 mt-1 text-sm text-ink-muted">
                <Badge kind={STATUS_BADGE[doc.status] || 'neutral'}>
                  {STATUS_LABEL[doc.status] || doc.status}
                </Badge>
                {doc.doc_type && <span>· {doc.doc_type}</span>}
                {docTypeGroupTerm?.field_value && (
                  <span>
                    ·{' '}
                    <Badge kind="neutral" className="text-2xs">
                      {labelFor(DOC_TYPE_GROUP_LABELS, docTypeGroupTerm.field_value)}
                    </Badge>
                  </span>
                )}
                {doc.created_at && (
                  <span>· {new Date(doc.created_at).toLocaleDateString('vi-VN')}</span>
                )}
                <span>· 📋 {doc.terms.length} thuộc tính</span>
                <span>· ⏰ {doc.obligations.length} nghĩa vụ</span>
                <span>· 📄 {doc.clause_count ?? 0} điều khoản</span>
              </div>
            </div>
            {doc.file_url && (
              <a
                href={`${import.meta.env.VITE_API_BASE_URL}${doc.file_url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline"
              >
                📥 Tải bản gốc
              </a>
            )}
          </div>

          {/* Terms — grouped */}
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
              {/* Thông tin chung */}
              {canonicalTerms.length > 0 && (
                <Card title="Thông tin chung" className="mb-4">
                  <div className="space-y-3">
                    {canonicalTerms.map((term) => renderTerm(term))}
                  </div>
                </Card>
              )}

              {/* Thông tin theo loại */}
              {typeSpecificTerms.length > 0 && (
                <Card title="Thông tin theo loại" className="mb-4">
                  <div className="space-y-3">
                    {typeSpecificTerms.map((term) => renderTerm(term))}
                  </div>
                </Card>
              )}
            </>
          )}

          {/* Self-party confirm */}
          {showSelfPartyConfirm && doc.parties && (
            <Card className="mb-4 border-warning/30 bg-warning-soft">
              <div className="text-sm font-medium text-ink mb-2">
                Bên nào trong hợp đồng này là bạn?
              </div>
              <p className="text-xs text-ink-muted mb-3">
                Chọn bên bạn đại diện để Khế phân loại nghĩa vụ (nghĩa_vụ / quyền_lợi).
                Chưa chọn → nghĩa vụ vẫn ở tab "Cần xác nhận".
              </p>
              <div className="flex gap-2 items-end">
                <div className="flex-1">
                  <select
                    value={selectedRole}
                    onChange={(e) => setSelectedRole(e.target.value)}
                    className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
                  >
                    <option value="">▼ Chọn bên...</option>
                    {doc.parties.map((p, i) => (
                      <option key={i} value={p.role_label || p.name}>
                        {p.name}{p.role_label ? ` (${p.role_label})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <Button
                  onClick={confirmSelfParty}
                  loading={confirming}
                  disabled={!selectedRole}
                >
                  Xác nhận
                </Button>
              </div>
            </Card>
          )}

          {/* Obligations */}
          {doc.obligations.length > 0 && (
            <Card title="Nghĩa vụ & hạn" className="mb-4">
              <div className="space-y-3">
                {doc.obligations.map((ob: ObligationOut) => (
                  <div
                    key={ob.id}
                    className="flex items-start justify-between gap-3 py-2 border-b border-border last:border-0"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-ink">
                        {ob.description}
                      </div>
                      <div className="text-xs text-ink-muted mt-1 flex gap-2 flex-wrap items-center">
                        <Badge kind="neutral" className="text-2xs">
                          {labelFor(OBLIGATION_TYPE_LABELS, ob.obligation_type)}
                        </Badge>
                        {ob.milestone_total && ob.milestone_total > 1 && ob.milestone_index != null && (
                          <span>· Đợt {ob.milestone_index}/{ob.milestone_total}</span>
                        )}
                        {ob.direction && (
                          <span>· {labelFor(DIRECTION_LABELS, ob.direction)}</span>
                        )}
                        {ob.due_date && (
                          <span>· hạn {new Date(ob.due_date).toLocaleDateString('vi-VN')}</span>
                        )}
                        {ob.status === 'waiting_trigger' && ob.trigger_condition && (
                          <span>· ⏳ Chờ: {ob.trigger_condition}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex-shrink-0">
                      {ob.status === 'done' ? (
                        <Badge kind="done">✓ hoàn thành</Badge>
                      ) : ob.status === 'cancelled' ? (
                        <Badge kind="neutral">đã hủy</Badge>
                      ) : (
                        <Link
                          to="/admin/obligations"
                          className="text-xs text-primary hover:underline"
                        >
                          Quản lý →
                        </Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
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
