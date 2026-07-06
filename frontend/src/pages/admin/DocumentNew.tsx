import { useState, useRef, type ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Toast } from '../../components';
import { apiFetch, apiFetchMultipart } from '../../lib/api';
import type { ApiError } from '../../lib/api';
import type { DocumentDetailOut, UploadOut } from '../../types/documents';
import type { ConfirmDocumentOut } from '../../types/documents';

type Step = 'upload' | 'review' | 'confirm';

export default function DocumentNew() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [doc, setDoc] = useState<DocumentDetailOut | null>(null);
  const [uploading, setUploading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected && selected.type === 'application/pdf') {
      setFile(selected);
      setError('');
    } else if (selected) {
      setError('Chỉ chấp nhận file PDF.');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type === 'application/pdf') {
      setFile(dropped);
      setError('');
    } else {
      setError('Chỉ chấp nhận file PDF.');
    }
  };

  const upload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await apiFetchMultipart<UploadOut>('/ingest/upload', fd);
      const detail = await apiFetch<DocumentDetailOut>(`/documents/${res.doc_id}`);
      setDoc(detail);
      setStep('review');
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.status === 403) {
        setError('Chưa ghi nhận đồng ý trích xuất AI. Vui lòng liên hệ đại lý/luật sư để kích hoạt.');
      } else if (apiErr.status === 429) {
        setError('Đã đạt giới hạn số tài liệu trong tháng. Liên hệ đại lý/luật sư để nâng hạn mức.');
      } else if (apiErr.status === 422) {
        setError('File không hợp lệ. Chỉ chấp nhận PDF.');
      } else {
        setError(apiErr.message || 'Tải lên thất bại. Vui lòng thử lại.');
      }
    } finally {
      setUploading(false);
    }
  };

  const confirmDoc = async () => {
    if (!doc) return;
    setConfirming(true);
    setError('');
    try {
      const res = await apiFetch<ConfirmDocumentOut>(`/documents/${doc.id}/confirm`, { method: 'POST' });
      if (res.confirmed_at) {
        setStep('confirm');
      } else {
        setError('Xác nhận tài liệu thất bại.');
      }
    } catch (err) {
      setError((err as ApiError).message || 'Xác nhận tài liệu thất bại.');
    } finally {
      setConfirming(false);
    }
  };

  const reset = () => {
    setFile(null);
    setDoc(null);
    setStep('upload');
    setError('');
    if (inputRef.current) inputRef.current.value = '';
  };

  const StepIndicator = () => (
    <div className="flex items-center gap-2 mb-6 text-sm">
      {(['upload', 'review', 'confirm'] as Step[]).map((s, i) => (
        <span
          key={s}
          className={`px-3 py-1 rounded-full ${
            step === s
              ? 'bg-primary-soft text-primary font-semibold'
              : step === 'confirm' || (step === 'review' && s === 'upload')
              ? 'text-ink-muted'
              : 'text-ink-muted'
          }`}
        >
          {i + 1}. {s === 'upload' ? 'Tải lên' : s === 'review' ? 'Kiểm tra' : 'Xác nhận'}
        </span>
      ))}
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-ink mb-2">Nhập tay hợp đồng</h1>
      <p className="text-sm text-ink-muted mb-4">Flow 2: Tải lên → Kiểm tra → Xác nhận trong một trang.</p>

      <StepIndicator />

      {error && (
        <div className="mb-4">
          <Toast kind="error">{error}</Toast>
        </div>
      )}

      {step === 'upload' && (
        <Card>
          <div
            role="button"
            tabIndex={0}
            aria-label="Tải lên file PDF"
            className="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-primary transition-colors focus-visible:shadow-ring focus-visible:outline-none"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
          >
            <div className="text-3xl mb-2">📁</div>
            <div className="text-sm text-ink-muted">Kéo thả file PDF hoặc click để chọn</div>
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={handleSelect}
            />
          </div>

          {file && (
            <div className="mt-4 flex items-center gap-2 text-sm text-ink-muted bg-surface-alt px-3 py-2 rounded-md">
              <span>📄</span>
              <span className="truncate">{file.name}</span>
              <span className="text-2xs text-ink-subtle">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
          )}

          {file && (
            <div className="flex gap-2 mt-4">
              <Button onClick={upload} loading={uploading}>
                Tải lên
              </Button>
              <Button variant="ghost" onClick={reset} disabled={uploading}>
                Xóa
              </Button>
            </div>
          )}
        </Card>
      )}

      {step === 'review' && doc && (
        <Card>
          <div className="text-sm font-semibold text-ink mb-2">{doc.file_name}</div>
          <div className="text-xs text-ink-muted mb-4">
            Trạng thái: {doc.status} · {doc.terms.length} trường · {doc.obligations.length} nghĩa vụ
          </div>
          <div className="text-sm text-ink-body leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto bg-surface-alt p-3 rounded-md">
            {doc.terms.slice(0, 5).map((t) => `${t.field_name}: ${t.field_value || '(chưa có)'}`).join('\n')}
            {doc.terms.length > 5 && '\n...'}
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={confirmDoc} loading={confirming}>
              Xác nhận tài liệu
            </Button>
            <Button variant="ghost" onClick={reset}>
              Tải lên khác
            </Button>
          </div>
        </Card>
      )}

      {step === 'confirm' && doc && (
        <Card>
          <div className="text-lg font-semibold text-success mb-2">Đã xác nhận thành công ✓</div>
          <p className="text-sm text-ink-body mb-4">
            {doc.file_name} đã được xác nhận. Khế sẽ tự động theo dõi các nghĩa vụ và quyền lợi.
          </p>
          <div className="flex gap-2">
            <Button onClick={() => navigate(`/admin/documents/${doc.id}`)}>Xem tài liệu</Button>
            <Button variant="ghost" onClick={reset}>
              Nhập thêm
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
