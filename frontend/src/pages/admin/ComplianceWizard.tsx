import { Card } from '../../components';

/**
 * Compliance wizard placeholder (Flow 3).
 *
 * Full 5-step implementation deferred until backend ships the compliance-profile
 * API (GET/PUT /tenants/me/compliance-profile). See issue #495 PR 2.
 */
export default function ComplianceWizard() {
  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-ink mb-2">Rà soát tuân thủ</h1>
      <p className="text-sm text-ink-muted mb-4">
        Flow 3: trả lời 5 câu hỏi về doanh nghiệp để Khế tạo nghĩa vụ từ gói luật
        (thuế GTGT + BHXH).
      </p>
      <Card>
        <div className="text-sm text-ink-body">
          <p className="mb-2">
            Tính năng đang được hoàn thiện — cần API <code>/tenants/me/compliance-profile</code>.
          </p>
          <p className="text-ink-muted">Vui lòng quay lại sau khi backend deploy.</p>
        </div>
      </Card>
    </div>
  );
}
