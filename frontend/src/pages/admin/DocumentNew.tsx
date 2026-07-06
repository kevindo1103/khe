import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Input, Toast } from '../../components';
import { apiFetch } from '../../lib/api';
import type { ApiError } from '../../lib/api';
import type { ManualDocumentCreateIn, DocumentDetailOut } from '../../types/documents';
import type { ObligationCreateIn } from '../../types/obligations';

type Step = 'info' | 'obligations' | 'confirm';

const DOC_TYPE_OPTIONS = [
  { value: 'hop_dong_lao_dong', label: 'Hợp đồng lao động' },
  { value: 'hop_dong_dich_vu', label: 'Hợp đồng dịch vụ' },
  { value: 'hop_dong_thue', label: 'Hợp đồng thuê' },
  { value: 'hop_dong_mua_ban', label: 'Hợp đồng mua bán' },
  { value: 'manual', label: 'Khác' },
];

const DIRECTION_OPTIONS = [
  { value: 'nghĩa_vụ', label: 'Nghĩa vụ' },
  { value: 'quyền_lợi', label: 'Quyền lợi' },
];

const RECURRENCE_OPTIONS = [
  { value: 'once', label: 'Một lần' },
  { value: 'monthly', label: 'Hàng tháng' },
  { value: 'quarterly', label: 'Hàng quý' },
  { value: 'yearly', label: 'Hàng năm' },
];

const OBLIGATION_TYPE_OPTIONS = [
  { value: 'payment', label: 'Thanh toán' },
  { value: 'expiration', label: 'Hết hạn' },
  { value: 'renewal', label: 'Gia hạn' },
  { value: 'reporting', label: 'Báo cáo' },
  { value: 'other', label: 'Khác' },
];

interface InfoForm {
  title: string;
  partyA: string;
  partyB: string;
  signDate: string;
  effectiveDate: string;
  docType: string;
}

interface DraftObligation {
  id: string;
  description: string;
  direction: 'nghĩa_vụ' | 'quyền_lợi' | '';
  dueDate: string;
  recurrence: string;
  obligor: string;
  obligationType: string;
}

function makeObligationId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

function emptyObligation(): DraftObligation {
  return {
    id: makeObligationId(),
    description: '',
    direction: '',
    dueDate: '',
    recurrence: 'once',
    obligor: '',
    obligationType: 'other',
  };
}

export default function DocumentNew() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('info');
  const [info, setInfo] = useState<InfoForm>({
    title: '',
    partyA: '',
    partyB: '',
    signDate: '',
    effectiveDate: '',
    docType: 'manual',
  });
  const [obligations, setObligations] = useState<DraftObligation[]>([]);
  const [confirmed, setConfirmed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const infoValid =
    info.title.trim().length > 0;

  const updateInfo = (patch: Partial<InfoForm>) => {
    setInfo((prev) => ({ ...prev, ...patch }));
  };

  const addObligation = () => {
    setObligations((prev) => [...prev, emptyObligation()]);
  };

  const updateObligation = (id: string, patch: Partial<DraftObligation>) => {
    setObligations((prev) => prev.map((o) => (o.id === id ? { ...o, ...patch } : o)));
  };

  const removeObligation = (id: string) => {
    setObligations((prev) => prev.filter((o) => o.id !== id));
  };

  const obligationsValid = obligations.every(
    (o) => o.description.trim().length > 0 && o.direction !== ''
  );

  const buildPayload = (): ManualDocumentCreateIn => {
    const terms: ManualDocumentCreateIn['terms'] = [];
    if (info.partyA.trim()) {
      terms.push({ field_name: 'Bên A', field_value: info.partyA.trim(), source: 'manual' });
    }
    if (info.partyB.trim()) {
      terms.push({ field_name: 'Bên B', field_value: info.partyB.trim(), source: 'manual' });
    }
    if (info.signDate) {
      terms.push({ field_name: 'Ngày ký', field_value: info.signDate, source: 'manual' });
    }
    if (info.effectiveDate) {
      terms.push({ field_name: 'Ngày hiệu lực', field_value: info.effectiveDate, source: 'manual' });
    }

    const embeddedObligations: ObligationCreateIn[] = obligations.map((o) => {
      const dueDate = o.dueDate || null;
      return {
        description: o.description.trim(),
        obligation_type: o.obligationType,
        direction: (o.direction as 'nghĩa_vụ' | 'quyền_lợi') || null,
        due_date: dueDate,
        recurrence: o.recurrence,
        obligor: o.obligor.trim() || null,
        remind_before_days: 7,
        document_id: null,
        source: 'user_manual',
        legal_basis: null,
        milestone_trigger: dueDate ? 'date' : 'event',
        trigger_condition: dueDate ? null : 'Chờ sự kiện kích hoạt',
        trigger_delay_days: null,
      };
    });

    return {
      title: info.title.trim(),
      doc_type: info.docType,
      counterparty: info.partyB.trim() || null,
      sign_date: info.signDate || null,
      effective_date: info.effectiveDate || null,
      terms,
      obligations: embeddedObligations,
    };
  };

  const submit = async () => {
    if (!infoValid) {
      setError('Vui lòng nhập tên hợp đồng.');
      return;
    }
    if (!obligationsValid) {
      setError('Mỗi nghĩa vụ cần có mô tả và chiều.');
      return;
    }
    if (!confirmed) {
      setError('Vui lòng xác nhận D-02 trước khi lưu.');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      // #494: manual document + embedded obligations (single transaction)
      const payload = buildPayload();
      const doc = await apiFetch<DocumentDetailOut>('/documents/', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      navigate(`/admin/documents/${doc.id}`);
    } catch (err) {
      setError((err as ApiError).message || 'Lưu hợp đồng thất bại. Vui lòng thử lại.');
    } finally {
      setSubmitting(false);
    }
  };

  const StepIndicator = () => (
    <div className="flex items-center gap-2 mb-6 text-sm">
      {(['info', 'obligations', 'confirm'] as Step[]).map((s, i) => (
        <span
          key={s}
          className={`px-3 py-1 rounded-full ${
            step === s
              ? 'bg-primary-soft text-primary font-semibold'
              : 'text-ink-muted'
          }`}
        >
          {i + 1}. {s === 'info' ? 'Thông tin' : s === 'obligations' ? 'Nghĩa vụ' : 'Xác nhận'}
        </span>
      ))}
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-ink mb-2">Nhập tay hợp đồng</h1>
      <p className="text-sm text-ink-muted mb-4">
        Ghi lại thông tin hợp đồng khi không có file PDF.
      </p>

      <StepIndicator />

      {error && (
        <div className="mb-4">
          <Toast kind="error">{error}</Toast>
        </div>
      )}

      {step === 'info' && (
        <Card>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-ink-muted uppercase mb-1">
                Tên hợp đồng *
              </label>
              <Input
                value={info.title}
                onChange={(v) => updateInfo({ title: v })}
                placeholder="vd: Hợp đồng dịch vụ kế toán"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-ink-muted uppercase mb-1">Bên A</label>
                <Input
                  value={info.partyA}
                  onChange={(v) => updateInfo({ partyA: v })}
                  placeholder="vd: Công ty ABC"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-muted uppercase mb-1">Bên B</label>
                <Input
                  value={info.partyB}
                  onChange={(v) => updateInfo({ partyB: v })}
                  placeholder="vd: Công ty XYZ"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-ink-muted uppercase mb-1">Ngày ký</label>
                <input
                  type="date"
                  value={info.signDate}
                  onChange={(e) => updateInfo({ signDate: e.target.value })}
                  className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-muted uppercase mb-1">Ngày hiệu lực</label>
                <input
                  type="date"
                  value={info.effectiveDate}
                  onChange={(e) => updateInfo({ effectiveDate: e.target.value })}
                  className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-ink-muted uppercase mb-1">Loại hợp đồng</label>
              <select
                value={info.docType}
                onChange={(e) => updateInfo({ docType: e.target.value })}
                className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                {DOC_TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex justify-end mt-6">
            <Button onClick={() => setStep('obligations')} disabled={!infoValid}>
              Tiếp theo
            </Button>
          </div>
        </Card>
      )}

      {step === 'obligations' && (
        <Card>
          <div className="space-y-4">
            {obligations.map((o, idx) => (
              <div key={o.id} className="border border-border rounded-md p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-ink">Nghĩa vụ #{idx + 1}</span>
                  <Button size="sm" variant="ghost" onClick={() => removeObligation(o.id)}>
                    Xóa
                  </Button>
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-muted uppercase mb-1">Mô tả *</label>
                  <Input
                    value={o.description}
                    onChange={(v) => updateObligation(o.id, { description: v })}
                    placeholder="vd: Thanh toán tiền thuê tháng 7"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-ink-muted uppercase mb-1">Chiều *</label>
                    <select
                      value={o.direction}
                      onChange={(e) => updateObligation(o.id, { direction: e.target.value as 'nghĩa_vụ' | 'quyền_lợi' | '' })}
                      className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
                    >
                      <option value="">Chọn</option>
                      {DIRECTION_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-ink-muted uppercase mb-1">Hạn</label>
                    <input
                      type="date"
                      value={o.dueDate}
                      onChange={(e) => updateObligation(o.id, { dueDate: e.target.value })}
                      className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-ink-muted uppercase mb-1">Lặp lại</label>
                    <select
                      value={o.recurrence}
                      onChange={(e) => updateObligation(o.id, { recurrence: e.target.value })}
                      className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
                    >
                      {RECURRENCE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-ink-muted uppercase mb-1">Bên phải thực hiện</label>
                    <Input
                      value={o.obligor}
                      onChange={(v) => updateObligation(o.id, { obligor: v })}
                      placeholder="vd: Công ty XYZ"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-muted uppercase mb-1">Loại nghĩa vụ</label>
                  <select
                    value={o.obligationType}
                    onChange={(e) => updateObligation(o.id, { obligationType: e.target.value })}
                    className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20"
                  >
                    {OBLIGATION_TYPE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            ))}
            <Button size="sm" variant="ghost" onClick={addObligation}>
              + Thêm nghĩa vụ
            </Button>
          </div>
          <div className="flex justify-between mt-6">
            <Button variant="ghost" onClick={() => setStep('info')}>
              Quay lại
            </Button>
            <Button onClick={() => setStep('confirm')} disabled={!obligationsValid}>
              Tiếp theo
            </Button>
          </div>
        </Card>
      )}

      {step === 'confirm' && (
        <Card>
          <div className="space-y-4">
            <div>
              <div className="text-sm font-semibold text-ink">{info.title || '(chưa có tên)'}</div>
              <div className="text-xs text-ink-muted mt-1">
                {info.partyA && `Bên A: ${info.partyA}`}
                {info.partyA && info.partyB && ' · '}
                {info.partyB && `Bên B: ${info.partyB}`}
              </div>
              <div className="text-xs text-ink-muted">
                {info.signDate && `Ngày ký: ${info.signDate}`}
                {info.signDate && info.effectiveDate && ' · '}
                {info.effectiveDate && `Hiệu lực: ${info.effectiveDate}`}
              </div>
            </div>

            {obligations.length > 0 ? (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-ink-muted uppercase">Nghĩa vụ đã nhập</div>
                {obligations.map((o, idx) => (
                  <div key={o.id} className="text-sm text-ink-body bg-surface-alt px-3 py-2 rounded-md">
                    <span className="font-medium">{idx + 1}.</span> {o.description}
                    {o.direction && <span className="text-ink-subtle"> · {o.direction === 'nghĩa_vụ' ? 'Nghĩa vụ' : 'Quyền lợi'}</span>}
                    {o.dueDate && <span className="text-ink-subtle"> · hạn {o.dueDate}</span>}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-ink-muted">Chưa có nghĩa vụ nào.</div>
            )}

            <label className="flex items-start gap-2 text-sm text-ink-body">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                className="mt-0.5"
              />
              <span>
                Tôi xác nhận thông tin trên là chính xác (D-02).
              </span>
            </label>
          </div>
          <div className="flex justify-between mt-6">
            <Button variant="ghost" onClick={() => setStep('obligations')}>
              Quay lại
            </Button>
            <Button onClick={submit} loading={submitting} disabled={!confirmed}>
              Lưu hợp đồng
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
