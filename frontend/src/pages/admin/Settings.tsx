import { useState, useEffect, useCallback } from 'react';
import { Button, Card, Input, Badge, Toast } from '../../components';
import { apiFetch } from '../../lib/api';
import type { LegalNameIn, LegalNameOut } from '../../types/tenant';
import type { ConsentEntry, ConsentGrantIn, ConsentRevokeIn } from '../../types/consent';
import type { ApiError } from '../../lib/api';

// NĐ13 purposes shown as privacy toggles (reminder_send handled in its own section)
const PRIVACY_PURPOSES: { purpose: ConsentEntry['purpose']; title: string; desc: string }[] = [
  {
    purpose: 'vision_extraction',
    title: 'Trích xuất bằng AI',
    desc: 'Cho phép Khế dùng AI đọc và bóc tách thông tin từ hợp đồng bạn tải lên.',
  },
  {
    purpose: 'firm_partner_access',
    title: 'Chia sẻ với đại lý / luật sư',
    desc: 'Cho phép đơn vị đối tác xem dữ liệu của bạn để hỗ trợ. Có thể thu hồi bất cứ lúc nào.',
  },
];

type Channel = 'telegram' | 'email';

export default function Settings() {
  const [legalName, setLegalName] = useState('');
  const [savedName, setSavedName] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [toastMsg, setToastMsg] = useState('');

  const [consents, setConsents] = useState<ConsentEntry[]>([]);
  const [busyPurpose, setBusyPurpose] = useState<string>('');
  const [channel, setChannel] = useState<Channel>('telegram');
  const [channelTarget, setChannelTarget] = useState('');

  const loadLegalName = useCallback(async () => {
    try {
      const res = await apiFetch<LegalNameOut>('/tenants/me/legal_name');
      setLegalName(res.legal_name || '');
      setSavedName(res.legal_name || '');
    } catch {
      // not set yet — leave empty
    }
  }, []);

  const loadConsents = useCallback(async () => {
    try {
      const res = await apiFetch<ConsentEntry[]>('/consent');
      setConsents(res);
      const reminder = res.find((c) => c.purpose === 'reminder_send');
      if (reminder?.channel === 'email' || reminder?.channel === 'telegram') {
        setChannel(reminder.channel);
      }
      if (reminder?.channel_target_ref) setChannelTarget(reminder.channel_target_ref);
    } catch {
      // best-effort
    }
  }, []);

  useEffect(() => {
    loadLegalName();
    loadConsents();
  }, [loadLegalName, loadConsents]);

  const statusOf = (purpose: string): 'granted' | 'none' =>
    consents.find((c) => c.purpose === purpose)?.status ?? 'none';

  const handleSaveLegalName = async () => {
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

  const grant = async (purpose: ConsentEntry['purpose'], extra?: Partial<ConsentGrantIn>) => {
    setBusyPurpose(purpose);
    setError('');
    try {
      await apiFetch('/consent', {
        method: 'POST',
        body: JSON.stringify({ purpose, ...extra } as ConsentGrantIn),
      });
      await loadConsents();
      setToastMsg('Đã ghi nhận đồng ý.');
    } catch (err) {
      setError((err as ApiError).message || 'Không ghi nhận được đồng ý');
    } finally {
      setBusyPurpose('');
    }
  };

  const revoke = async (purpose: ConsentEntry['purpose']) => {
    setBusyPurpose(purpose);
    setError('');
    try {
      await apiFetch('/consent/revoke', {
        method: 'POST',
        body: JSON.stringify({ purpose } as ConsentRevokeIn),
      });
      await loadConsents();
      setToastMsg('Đã thu hồi đồng ý.');
    } catch (err) {
      setError((err as ApiError).message || 'Thu hồi thất bại');
    } finally {
      setBusyPurpose('');
    }
  };

  const enableReminder = async () => {
    if (!channelTarget.trim()) return;
    await grant('reminder_send', { channel, channel_target_ref: channelTarget.trim() });
  };

  const hasNameChange = legalName.trim() !== savedName.trim();
  const reminderOn = statusOf('reminder_send') === 'granted';

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-bold text-ink mb-1">Cài đặt</h1>
      <p className="text-sm text-ink-muted mb-5">
        Thông tin doanh nghiệp, nhắc hạn và quyền riêng tư.
      </p>

      {error && <div className="mb-4 text-sm text-danger">{error}</div>}

      {/* Legal name */}
      <Card title="Tên pháp lý doanh nghiệp" className="mb-4">
        <div className="space-y-3">
          <p className="text-sm text-ink-muted">
            Khi đặt, Khế tự đối chiếu tên này với các bên trong hợp đồng — nghĩa vụ được phân loại
            nghĩa_vụ / quyền_lợi mà không cần xác nhận thủ công.
          </p>
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <Input value={legalName} onChange={setLegalName} placeholder="vd: Công ty Cổ phần ABC" className="mb-0" />
            </div>
            <Button onClick={handleSaveLegalName} loading={saving} disabled={!hasNameChange}>Lưu</Button>
          </div>
          {savedName && !hasNameChange && <p className="text-xs text-success">✓ Đã đặt: {savedName}</p>}
        </div>
      </Card>

      {/* Reminder channel (DEC-006) — windows NOT hardcoded (DEC-020 pending) */}
      <Card title="Nhắc hạn" className="mb-4">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <p className="text-sm text-ink-muted flex-1">
              Chọn kênh để Khế nhắc bạn trước mỗi hạn.
            </p>
            {reminderOn && <Badge kind="extracted">Đang bật</Badge>}
          </div>
          <div className="flex gap-2">
            {(['telegram', 'email'] as Channel[]).map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setChannel(c)}
                className={`px-3 py-1.5 rounded-pill text-xs font-medium border transition-colors ${
                  channel === c ? 'bg-primary-soft text-primary border-primary' : 'bg-surface text-ink-muted border-border hover:text-ink'
                }`}
              >
                {c === 'telegram' ? 'Telegram' : 'Email'}
              </button>
            ))}
          </div>
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <Input
                value={channelTarget}
                onChange={setChannelTarget}
                placeholder={channel === 'telegram' ? 'Telegram chat ID' : 'địa chỉ email'}
                className="mb-0"
              />
            </div>
            <Button onClick={enableReminder} loading={busyPurpose === 'reminder_send'} disabled={!channelTarget.trim()}>
              {reminderOn ? 'Cập nhật' : 'Bật nhắc'}
            </Button>
          </div>
          {reminderOn && (
            <button
              type="button"
              onClick={() => revoke('reminder_send')}
              className="text-2xs text-danger hover:underline"
            >
              Tắt nhắc hạn
            </button>
          )}
        </div>
      </Card>

      {/* NĐ13 privacy consents (D-10) */}
      <Card title="Quyền riêng tư (NĐ 13/2023)" className="mb-4">
        <div className="space-y-4">
          {PRIVACY_PURPOSES.map((p) => {
            const granted = statusOf(p.purpose) === 'granted';
            return (
              <div key={p.purpose} className="flex items-start justify-between gap-3 border-b border-border last:border-0 pb-3 last:pb-0">
                <div className="flex-1">
                  <div className="text-sm font-medium text-ink flex items-center gap-2">
                    {p.title}
                    {granted ? <Badge kind="extracted">Đã đồng ý</Badge> : <Badge kind="neutral">Chưa</Badge>}
                  </div>
                  <p className="text-2xs text-ink-muted mt-0.5">{p.desc}</p>
                </div>
                {granted ? (
                  <Button variant="ghost" size="sm" loading={busyPurpose === p.purpose} onClick={() => revoke(p.purpose)}>
                    Thu hồi
                  </Button>
                ) : (
                  <Button size="sm" loading={busyPurpose === p.purpose} onClick={() => grant(p.purpose)}>
                    Đồng ý
                  </Button>
                )}
              </div>
            );
          })}
          <p className="text-2xs text-ink-subtle">
            Bạn có thể thu hồi đồng ý bất cứ lúc nào (D-10). Mọi thay đổi được ghi vào sổ sự kiện.
          </p>
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
