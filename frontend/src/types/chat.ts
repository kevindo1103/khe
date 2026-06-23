/**
 * Chat types — mirrored from backend Pydantic schema to prevent drift.
 */

export interface ChatQueryIn {
  question: string;
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
}

export interface ChatMessage {
  role: 'user' | 'bot';
  text: string | null;
  source?: ChatSource | null;
  notFound?: boolean;
  isError?: boolean;
  loading?: boolean;
}
