import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Input, Card } from '../../components';
import { useAuth } from '../../hooks/useAuth';
import type { LoginRequest } from '../../types/auth';
import type { ApiError } from '../../lib/api';

export default function Login() {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();

  const [form, setForm] = useState<LoginRequest>({
    tenant_id: '',
    username: '',
    password: '',
  });
  const [error, setError] = useState<string>('');

  const setField = (key: keyof LoginRequest) => (value: string) => {
    setForm((f) => ({ ...f, [key]: value }));
    if (error) setError('');
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!form.tenant_id.trim() || !form.username.trim() || !form.password.trim()) {
      setError('Vui lòng điền đầy đủ thông tin đăng nhập.');
      return;
    }

    try {
      await login(form);
      navigate('/admin');
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.status === 401) {
        setError('Thông tin đăng nhập không đúng. Vui lòng kiểm tra lại.');
      } else if (apiErr.status === 422) {
        setError('Dữ liệu không hợp lệ. Vui lòng kiểm tra lại các trường.');
      } else {
        setError(apiErr.message || 'Đã xảy ra lỗi. Vui lòng thử lại sau.');
      }
    }
  };

  return (
    <div className="min-h-screen bg-surface-alt flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <div className="text-2xl font-bold text-primary">Khế</div>
          <div className="text-sm text-ink-muted mt-1">
            Quản trị tài liệu — đăng nhập
          </div>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              label="Mã đơn vị (tenant)"
              value={form.tenant_id}
              onChange={setField('tenant_id')}
              placeholder="vd: sme-abc-restaurant"
              hint="Mã do firm/đại lý cấp khi onboard"
              testId="login-tenant-id"
            />
            <Input
              label="Tên đăng nhập"
              value={form.username}
              onChange={setField('username')}
              placeholder="vd: linh.ketoan"
              testId="login-username"
            />
            <Input
              label="Mật khẩu"
              type="password"
              value={form.password}
              onChange={setField('password')}
              placeholder="••••••••"
              testId="login-password"
            />

            {error && (
              <div
                data-testid="login-error"
                className="text-2xs text-danger bg-danger-soft px-3 py-2 rounded-md"
              >
                {error}
              </div>
            )}

            <Button type="submit" size="lg" loading={isLoading} className="w-full" testId="login-submit">
              Đăng nhập
            </Button>

            <div className="text-center text-2xs text-ink-subtle">
              Quên mật khẩu? Liên hệ đại lý/luật sư đã cấp tài khoản cho bạn.
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}
