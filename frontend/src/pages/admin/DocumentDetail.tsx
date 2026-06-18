import { EmptyState } from '../../components';

export default function DocumentDetail() {
  return (
    <div>
      <h1 className="text-xl font-bold text-ink mb-4">Chi tiết tài liệu</h1>
      <EmptyState
        icon="📑"
        title="Chưa có chi tiết tài liệu"
        description="Màn hình này sẽ được triển khai ở Sprint tiếp theo khi API shape đã khóa."
      />
    </div>
  );
}
