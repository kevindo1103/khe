import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button, Card, Badge, Input, ConfidenceMeter, Toast, EmptyState } from '../../components';
import { apiFetch } from '../../lib/api';
import type { DocumentDetailOut, TermOut } from '../../types/documents';
import type { ApiError } from '../../lib/api';

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

          {/* Terms */}
          <Card title="Thông tin trích xuất">
            {doc.terms.length === 0 ? (
              <EmptyState
                icon="📭"
                title="Chưa có thông tin"
                description="Tài liệu đang được xử lý. Quay lại sau vài phút."
              />
            ) : (
              <div className="space-y-3">
                {doc.terms.map((term) => (
                  <div
                    key={term.id}
                    className="flex items-start justify-between gap-3 py-2 border-b border-border last:border-0"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-ink-muted uppercase">
                          {term.field_name}
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
                ))}
              </div>
            )}
          </Card>
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
