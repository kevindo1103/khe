import { EmptyState } from '../../components';

export default function Obligations() {
  return (
    <div>
      <h1 className="text-xl font-bold text-ink mb-4">Nghĩa vụ & hạn</h1>
      <EmptyState
        icon="📋"
        title="Chưa có danh sách nghĩa vụ"
        description="Màn hình này sẽ được triển khai ở Sprint tiếp theo khi API shape đã khóa."
      />
    </div>
  );
}
