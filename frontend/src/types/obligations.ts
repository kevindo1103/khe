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
  | 'waiting_trigger'
  | 'overdue'
  | 'awaiting_confirmation';

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
  // Fulfillment fields (Backend #302)
  fulfilled_at: string | null;
  fulfilled_by: string | null;
}

export interface ObligationListOut {
  items: ObligationOut[];
  page: number;
  page_size: number;
  total: number;
}

export interface ObligationPatchIn {
  status: string;
  fulfilled_at?: string | null;
  fulfilled_by?: string | null;
  evidence_doc_ids?: number[] | null;
}

export interface ObligationPatchOut {
  ok: boolean;
  obligation: ObligationOut;
  activated_count: number;
}

// GET /obligations/summary (#253/#254) — server-side dashboard aggregate.
// Default group_by=direction, active_only=true (excludes done/cancelled; overdue kept).
// Single source of truth shared with the #199 chat aggregate.
export interface ObligationSummaryGroup {
  key: string;            // 'nghĩa_vụ' | 'quyền_lợi' | 'null'
  label: string;          // server label — render verbatim (#227 consumer rule)
  count: number;
  nearest?: { title: string; days_left: number };
}

export interface ObligationStatusBreakdown {
  waiting_trigger: number;
  overdue: number;
  due_soon: number;
}

export interface ObligationSummaryOut {
  total: number;
  group_by: string;
  groups: ObligationSummaryGroup[];          // sorted by count desc
  status_breakdown: ObligationStatusBreakdown;
  source: { obligation_count: number; doc_count: number; label: string };
}
