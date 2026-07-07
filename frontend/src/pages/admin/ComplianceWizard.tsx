import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Card, Toast } from '../../components';
import { apiFetch } from '../../lib/api';
import type { ApiError } from '../../lib/api';
import type { ComplianceProfileIn, ComplianceProfileOut } from '../../types/tenant';

const LEGAL_FORM_OPTIONS = [
  { value: 'Hộ kinh doanh', label: 'Hộ kinh doanh' },
  { value: 'Doanh nghiệp tư nhân', label: 'Doanh nghiệp tư nhân' },
  { value: 'Công ty TNHH', label: 'Công ty TNHH' },
  { value: 'Công ty cổ phần', label: 'Công ty cổ phần' },
];

const EMPTY_PROFILE: ComplianceProfileOut = {
  legal_form: null,
  has_employees: null,
  vat_period: null,
  fiscal_year_start: null,
};

/**
 * Compliance wizard (Flow 3) — Step 1: compliance profile form.
 * Steps 2-5 (rule-matching, activation, D-02 confirm) remain placeholder —
 * rule-pack engine on hold pending firm pilot content (see #495).
 */
export default function ComplianceWizard() {
  const [profile, setProfile] = useState<ComplianceProfileOut>(EMPTY_PROFILE);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [toastMsg, setToastMsg] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch<ComplianceProfileOut>('/tenants/me/compliance-profile');
      setProfile(res);
    } catch {
      // 404 = profile chưa tồn tại (chưa từng đặt tên pháp lý) — hiển thị form trống
      setProfile(EMPTY_PROFILE);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      const res = await apiFetch<ComplianceProfileOut>('/tenants/me/compliance-profile', {
        method: 'PUT',
        body: JSON.stringify(profile satisfies ComplianceProfileIn),
      });
      setProfile(res);
      setToastMsg('Đã lưu hồ sơ doanh nghiệp.');
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.status === 404) {
        setError(
          'Chưa có hồ sơ doanh nghiệp — hãy đặt tên pháp lý trong Cài đặt trước, sau đó quay lại đây.'
        );
      } else {
        setError(apiErr.message || 'Lưu thất bại');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-ink mb-1">Rà soát tuân thủ</h1>
      <p className="text-sm text-ink-muted mb-4">Bước 1/5 — Hồ sơ doanh nghiệp</p>

      {error && (
        <div className="mb-4">
          <Toast kind="error">{error}</Toast>
        </div>
      )}

      <Card>
        {loading ? (
          <p className="text-sm text-ink-muted">Đang tải…</p>
        ) : (
          <div className="space-y-5">
            <div>
              <label className="block text-xs font-medium text-ink-muted uppercase mb-1">
                Loại hình doanh nghiệp
              </label>
              <select
                value={profile.legal_form ?? ''}
                onChange={(e) =>
                  setProfile((p) => ({ ...p, legal_form: e.target.value || null }))
                }
                className="w-full px-3 py-2 rounded-md border border-border-strong bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">Chọn loại hình</option>
                {LEGAL_FORM_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-muted uppercase mb-2">
                Doanh nghiệp có nhân viên không?
              </label>
              <div className="flex gap-4">
                {[{ value: true, label: 'Có' }, { value: false, label: 'Không' }].map((opt) => (
                  <label key={String(opt.value)} className="flex items-center gap-2 text-sm text-ink cursor-pointer">
                    <input
                      type="radio"
                      name="has_employees"
                      checked={profile.has_employees === opt.value}
                      onChange={() => setProfile((p) => ({ ...p, has_employees: opt.value }))}
                      className="accent-primary"
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-muted uppercase mb-2">
                Kỳ kê khai thuế GTGT
              </label>
              <div className="flex gap-4">
                {[{ value: 'month', label: 'Theo tháng' }, { value: 'quarter', label: 'Theo quý' }].map((opt) => (
                  <label key={opt.value} className="flex items-center gap-2 text-sm text-ink cursor-pointer">
                    <input
                      type="radio"
                      name="vat_period"
                      checked={profile.vat_period === opt.value}
                      onChange={() => setProfile((p) => ({ ...p, vat_period: opt.value }))}
                      className="accent-primary"
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-muted uppercase mb-1">
                Ngày bắt đầu năm tài chính
              </label>
              <input
                type="date"
                value={profile.fiscal_year_start ?? '2026-01-01'}
                onChange={(e) =>
                  setProfile((p) => ({ ...p, fiscal_year_start: e.target.value || null }))
                }
                className="w-full px-3 py-2 rounded-md border border-border-strong bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>

            <div className="flex justify-end">
              <Button onClick={handleSave} loading={saving}>
                Lưu hồ sơ
              </Button>
            </div>
          </div>
        )}
      </Card>

      <Card className="mt-4 opacity-60">
        <p className="text-sm text-ink-body">
          Bước 2-5 đang phát triển — cần gói quy tắc để tạo nghĩa vụ tự động.
        </p>
        <p className="text-xs text-ink-muted mt-1">
          Chưa đặt tên pháp lý? <Link to="/admin/settings" className="text-primary underline">Vào Cài đặt</Link>.
        </p>
      </Card>

      {toastMsg && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-toast">
          <Toast kind="success">{toastMsg}</Toast>
        </div>
      )}
    </div>
  );
}
