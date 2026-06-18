import { EmptyState } from '../../components';

export default function DocumentList() {
  return (
    <div>
      <h1 className="text-xl font-bold text-ink mb-4">Danh sách tài liệu</h1>
      <EmptyState
        icon="📄"
        title="Chưa có danh sách tài liệu"
        description="Màn hình này sẽ được triển khai ở Sprint tiếp theo khi API shape đã khóa."
      />
    </div>
  );
}
