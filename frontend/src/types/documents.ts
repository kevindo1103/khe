/**
 * Document + Ingest types
 * Mirrored from backend schemas exactly to prevent drift.
 */

import type { ObligationOut } from './obligations';

export interface TermOut {
  id: number;
  field_name: string;
  field_value: string | null;
  confidence: number | null;
  needs_review: boolean;
}

export interface TermPatchIn {
  field_value: string;
}

export interface DocumentListItem {
  id: number;
  file_name: string;
  doc_type: string | null;
  status: string;
  needs_review: boolean;
  term_count: number;
  obligation_count: number;
  clause_count: number;
  confirmed_by_user_at: string | null;   // #238 — null = "Cần xác nhận"
  created_at: string | null;
  // #279 — new fields (optional until backend ships)
  primary_party?: string | null;
  next_due_date?: string | null;
  nghia_vu_count?: number;
  quyen_loi_count?: number;
  direction_null_count?: number;
  may_have_unextracted_obligations?: boolean | null;
  duplicate?: boolean;
}

export interface DocumentListOut {
  items: DocumentListItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface DocumentDetailOut {
  id: number;
  file_name: string;
  doc_type: string | null;
  status: string;
  created_at: string | null;
  file_url: string | null;
  terms: TermOut[];
  obligations: ObligationOut[];
  clause_count: number;
  confirmed_by_user_at: string | null;   // #238 — null = not yet user-confirmed
  failure_reason: string | null;
  parties?: { name: string; role_label: string | null }[];
}

// #238 — POST /documents/{id}/confirm (no body; self-party auto-derived from legal_name)
export interface ConfirmDocumentOut {
  doc_id: number;
  confirmed_at: string;
  directions_recomputed: number;
  journey_advanced: boolean;
  new_journey_stage: string | null;
}

// #262 (#258) — POST /documents/{id}/remap-type (text-only clause remap, no vision quota)
export interface RemapTypeOut {
  success: boolean;
  fields_remapped: number;
  fields_null: number;
  cost_vnd: number;
}

export interface UploadOut {
  doc_id: number;
  file_name: string;
  status: string;
}

export interface BulkUploadOut {
  count: number;
  documents: UploadOut[];
}

export interface SelfPartyConfirmIn {
  role_label: string;
}

export interface SelfPartyConfirmOut {
  ok: boolean;
  updated: number;
}
