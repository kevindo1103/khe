import { useState, useRef, type ChangeEvent } from 'react';
import { Button, Card, Badge, Toast, EmptyState } from '../../components';
import { apiFetchMultipart } from '../../lib/api';
import type { UploadOut, BulkUploadOut } from '../../types/documents';
import type { ApiError } from '../../lib/api';

type Tab = 'single' | 'bulk';

export default function Upload() {
  const [tab, setTab] = useState<Tab>('single');
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<UploadOut[] | null>(null);
  const [error, setError] = useState<string>('');
  const [toastMsg, setToastMsg] = useState<string>('');
  const singleInputRef = useRef<HTMLInputElement>(null);
  const bulkInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>, multiple: boolean) => {
    const selected = Array.from(e.target.files || []);
    if (multiple && selected.length > 20) {
      setError('Tối đa 20 file mỗi lần tải lên hàng loạt.');
      return;
    }
    setFiles(selected.filter((f) => f.type === 'application/pdf'));
    setError('');
    setResults(null);
  };

  const handleDrop = (e: React.DragEvent, multiple: boolean) => {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer.files).filter((f) => f.type === 'application/pdf');
    if (multiple && dropped.length > 20) {
      setError('Tối đa 20 file mỗi lần tải lên hàng loạt.');
      return;
    }
    if (dropped.length === 0) {
      setError('Chỉ chấp nhận file PDF.');
      return;
    }
    setFiles(dropped);
    setError('');
    setResults(null);
  };

  const upload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setError('');
    setResults(null);

    try {
      if (tab === 'single' && files.length === 1) {
        const fd = new FormData();
        fd.append('file', files[0]);
        const res = await apiFetchMultipart<UploadOut>('/ingest/upload', fd);
        setResults([res]);
        setToastMsg('Tải lên thành công ✓');
      } else {
        const fd = new FormData();
        files.forEach((f) => fd.append('files', f));
        const res = await apiFetchMultipart<BulkUploadOut>('/ingest/bulk', fd);
        setResults(res.documents);
        setToastMsg(`Đã tải ${res.count} tài liệu ✓`);
      }
      setFiles([]);
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.status === 403) {
        setError('Chưa ghi nhận đồng ý trích xuất AI. Vui lòng liên hệ đại lý/luật sư để kích hoạt.');
      } else if (apiErr.status === 422) {
        setError('File không hợp lệ. Chỉ chấp nhận PDF.');
      } else {
        setError(apiErr.message || 'Tải lên thất bại. Vui lòng thử lại.');
      }
    } finally {
      setUploading(false);
    }
  };

  const clear = () => {
    setFiles([]);
    setResults(null);
    setError('');
    if (singleInputRef.current) singleInputRef.current.value = '';
    if (bulkInputRef.current) bulkInputRef.current.value = '';
  };

  return (
    <div>
      <h1 className="text-xl font-bold text-ink mb-4">Tải lên tài liệu</h1>

      {/* Tabs */}
      <div className="flex gap-1 mb-4">
        {([
          { key: 'single', label: 'Tải lên đơn' },
          { key: 'bulk', label: 'Tải lên hàng loạt' },
        ] as { key: Tab; label: string }[]).map((t) => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); clear(); }}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-primary-soft text-primary'
                : 'text-ink-muted hover:text-ink hover:bg-surface-alt'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <Card>
        {/* Drop zone */}
        <div
          className="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-primary transition-colors"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => handleDrop(e, tab === 'bulk')}
          onClick={() => (tab === 'single' ? singleInputRef.current?.click() : bulkInputRef.current?.click())}
        >
          <div className="text-3xl mb-2">📁</div>
          <div className="text-sm text-ink-muted">
            {tab === 'single'
              ? 'Kéo thả file PDF hoặc click để chọn'
              : 'Kéo thả tối đa 20 file PDF hoặc click để chọn'}
          </div>
          <input
            ref={singleInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => handleFileSelect(e, false)}
          />
          <input
            ref={bulkInputRef}
            type="file"
            accept="application/pdf"
            multiple
            className="hidden"
            onChange={(e) => handleFileSelect(e, true)}
          />
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="text-sm font-medium text-ink">File đã chọn:</div>
            {files.map((f, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-ink-muted bg-surface-alt px-3 py-2 rounded-md">
                <span>📄</span>
                <span className="truncate">{f.name}</span>
                <span className="text-2xs text-ink-subtle">({(f.size / 1024).toFixed(1)} KB)</span>
              </div>
            ))}
          </div>
        )}

        {/* Actions */}
        {files.length > 0 && (
          <div className="flex gap-2 mt-4">
            <Button onClick={upload} loading={uploading}>
              {tab === 'single' ? 'Tải lên' : `Tải lên ${files.length} file`}
            </Button>
            <Button variant="ghost" onClick={clear} disabled={uploading}>
              Xóa
            </Button>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4">
            <Toast kind="error">{error}</Toast>
          </div>
        )}

        {/* Results */}
        {results && results.length > 0 && (
          <div className="mt-4">
            <div className="text-sm font-medium text-ink mb-2">Kết quả:</div>
            <div className="space-y-2">
              {results.map((r) => (
                <div key={r.doc_id} className="flex items-center justify-between text-sm bg-success-soft px-3 py-2 rounded-md">
                  <span className="truncate">{r.file_name}</span>
                  <Badge kind={r.status === 'processing' ? 'processing' : 'extracted'}>
                    {r.status === 'processing' ? 'Đang xử lý' : 'Đã bóc tách'}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {results && results.length === 0 && (
          <div className="mt-4">
            <EmptyState icon="📭" title="Không có file nào được tải lên" />
          </div>
        )}
      </Card>

      {/* Toast */}
      {toastMsg && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-toast">
          <Toast kind="success">{toastMsg}</Toast>
        </div>
      )}
    </div>
  );
}
