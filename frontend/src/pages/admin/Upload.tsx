import { EmptyState } from '../../components';

export default function Upload() {
  return (
    <div>
      <h1 className="text-xl font-bold text-ink mb-4">Tải lên tài liệu</h1>
      <EmptyState
        icon="📤"
        title="Chưa có chức năng tải lên"
        description="Màn hình này sẽ được triển khai ở Sprint tiếp theo khi API shape đã khóa."
      />
    </div>
  );
}
