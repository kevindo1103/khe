import { useState, useEffect, useCallback } from 'react';
import { Button, Card, Input, Toast } from '../../components';
import { apiFetch } from '../../lib/api';
import type { LegalNameIn, LegalNameOut } from '../../types/tenant';
import type { ApiError } from '../../lib/api';

export default function Settings() {
  const [legalName, setLegalName] = useState('');
  const [savedName, setSavedName] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [toastMsg, setToastMsg] = useState('');

  const loadLegalName = useCallback(async () => {
    try {
      const res = await apiFetch<LegalNameOut>('/tenants/me/legal_name');
      setLegalName(res.legal_name || '');
      setSavedName(res.legal_name || '');
    } catch {
      // 404 or not set yet — leave empty
    }
  }, []);

  useEffect(() => {
    loadLegalName();
  }, [loadLegalName]);

  const handleSave = async () => {
    if (!legalName.trim()) return;
    setSaving(true);
    setError('');
    try {
      const res = await apiFetch<LegalNameOut>('/tenants/me/legal_name', {
        method: 'PATCH',
        body: JSON.stringify({ legal_name: legalName.trim() } as LegalNameIn),
      });
      setSavedName(res.legal_name);
      setToastMsg('Đã lưu tên pháp lý — tài liệu mới sẽ tự động đối chiếu.');
    } catch (err) {
      setError((err as ApiError).message || 'Lưu thất bại');
    } finally {
      setSaving(false);
    }
  };

  const hasChange = legalName.trim() !== savedName.trim();

  return (
    <div>
      <h1 className="text-xl font-bold text-ink mb-1">Cài đặt</h1>
      <p className="text-sm text-ink-muted mb-5">
        Thông tin doanh nghiệp để Khế tự động nhận diện bên bạn trong hợp đồng.
      </p>

      {error && <div className="mb-4 text-sm text-danger">{error}</div>}

      <Card title="Tên pháp lý doanh nghiệp" className="mb-4">
        <div className="space-y-3">
          <p className="text-sm text-ink-muted">
            Khi đặt, Khế sẽ tự động đối chiếu tên này với các bên trong hợp đồng mới —
            nghĩa vụ sẽ được phân loại nghĩa_vụ / quyền_lợi mà không cần xác nhận thủ công.
          </p>
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <Input
                value={legalName}
                onChange={setLegalName}
                placeholder="vd: Công ty Cổ phần ABC"
                className="mb-0"
              />
            </div>
            <Button
              onClick={handleSave}
              loading={saving}
              disabled={!hasChange}
            >
              Lưu
            </Button>
          </div>
          {savedName && !hasChange && (
            <p className="text-xs text-success">
              ✓ Đã đặt: {savedName}
            </p>
          )}
        </div>
      </Card>

      {toastMsg && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-toast">
          <Toast kind="success">{toastMsg}</Toast>
        </div>
      )}
    </div>
  );
}
