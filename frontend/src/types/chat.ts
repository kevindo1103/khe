/**
 * Chat types — mirrored from backend Pydantic schema to prevent drift.
 */

export interface ChatQueryIn {
  question: string;
  // DEC-031 v2 (#201): per-device/tab UUID from FE localStorage. Optional —
  // absent → stateless (cold) chat, fully backward compatible.
  session_id?: string;
}

export interface ChatSource {
  file_name: string;
  document_id: number;
  clause_num?: string | null;
  // obligation-source enrichment (backend #177):
  type?: string | null;
  field_name?: string | null;
  value?: string | null;
  status?: string | null;
  clause_title?: string | null;
  description?: string | null;
  direction?: 'nghĩa_vụ' | 'quyền_lợi' | null;
  obligor?: string | null;
  obligation_type?: string | null;
  amount_raw?: string | null;
  milestone_series_id?: string | null;
  milestone_index?: number | null;
  milestone_total?: number | null;
  trigger_condition?: string | null;
}

export interface ChatQueryOut {
  answer: string;
  found: boolean;
  sources: ChatSource[];
  // DEC-031 v2 (#201): ID-only working-set chip label ("HĐ #12" / "3 tài liệu");
  // null when cold (0 docs) or working set over-cap. Plus the echoed session_id.
  context_label: string | null;
  session_id: string | null;
}

export interface ChatSessionResetIn {
  session_id: string;
}

export interface ChatSessionResetOut {
  ok: boolean;
  deleted: number;
}

export interface ChatMessage {
  role: 'user' | 'bot';
  text: string | null;
  source?: ChatSource | null;
  notFound?: boolean;
  isError?: boolean;
  loading?: boolean;
  // Over-cap signal: backend surfaces a `truncation_hint` source carrying VN
  // text ("Tổng số: N kết quả, hiển thị 10 mới nhất."). NOT a D-08 string.
  truncationHint?: string | null;
}
