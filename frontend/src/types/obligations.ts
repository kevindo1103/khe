/**
 * Obligation types
 * Mirrored from backend schemas exactly to prevent drift.
 */

export type ObligationDirection = 'nghĩa_vụ' | 'quyền_lợi' | null;

export type ObligationStatus =
  | 'pending'
  | 'in_progress'
  | 'partial'
  | 'done'
  | 'cancelled'
  | 'waiting_trigger';

export interface ObligationOut {
  id: number;
  document_id: number;
  description: string;
  obligation_type: string;
  recurrence: string;
  direction: ObligationDirection;
  obligor: string | null;
  due_date: string | null;
  status: ObligationStatus;
  remind_before_days: number;
  source_doc_chain: string | null;
  resolution_method: string | null;
  // DEC-030 Phase 2: series + event-chain
  milestone_series_id: string | null;
  milestone_index: number | null;
  milestone_total: number | null;
  milestone_trigger: string | null;
  trigger_condition: string | null;
  trigger_delay_days: number | null;
  trigger_obligation_id: number | null;
  amount_raw: string | null;
  created_at: string | null;
}

export interface ObligationListOut {
  items: ObligationOut[];
  page: number;
  page_size: number;
  total: number;
}

export interface ObligationPatchIn {
  status: string;
}

export interface ObligationPatchOut {
  ok: boolean;
  obligation: ObligationOut;
  activated_count: number;
}
