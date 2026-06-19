/**
 * Obligation types
 * Mirrored from backend schemas exactly to prevent drift.
 */

export interface ObligationOut {
  id: number;
  document_id: number;
  description: string;
  obligation_type: string;
  due_date: string | null;
  status: string;
  remind_before_days: number;
  source_doc_chain: string | null;
  resolution_method: string | null;
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
}
