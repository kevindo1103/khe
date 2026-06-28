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
  processing_stage?: string | null;
  processing_progress?: number | null;
  title?: string | null;
  contract_number?: string | null;
  // #371 R8 — lifecycle status (optional until backend tenant_025 lands)
  contract_term?: string | null;
  lifecycle_status?: string | null;
}

export interface DocumentListOut {
  items: DocumentListItem[];
  page: number;
  page_size: number;
  total: number;
}

// #364 R2 — extended party details (all new fields optional until backend migration lands)
export interface PartyOut {
  id?: number;
  name: string;
  role_label: string | null;
  address?: string | null;
  contact?: string | null;
  representative?: string | null;
  tax_code?: string | null;
  is_self?: boolean;
  aliases?: string[] | null;
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
  parties?: PartyOut[];
  processing_stage?: string | null;
  processing_progress?: number | null;
  title?: string | null;
  contract_number?: string | null;
  // #371 R8 — lifecycle status (optional until backend tenant_025 lands)
  contract_term?: string | null;
  lifecycle_status?: string | null;
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

// Backend #284 — GET /documents/{id}/clauses
export interface ClauseOut {
  id: number;
  clause_num: string | null;
  title: string | null;
  page_num: number | null;
  content: string;
  // Phase 2 fields — populated after PATCH /clauses/{id} (Backend #325)
  edited_by_user?: string | null;
  edited_at?: string | null;
  original_content?: string | null;
  // #365 R3 — clause hierarchy (optional until backend migration tenant_023 lands)
  parent_id?: number | null;
  level?: number | null;
  clause_path?: string | null;
}

export interface ClauseListOut {
  document_id: number;
  clause_count: number;
  page_min: number | null;
  page_max: number | null;
  clauses: ClauseOut[];
}

// Backend #325 — PATCH /documents/{id}/clauses/{clause_id}
export interface ClausePatchOut {
  id: number;
  clause_num: string | null;
  title: string | null;
  page_num: number | null;
  content: string;
  edited_by_user: string | null;
  edited_at: string | null;
  original_content: string | null;
}

// #372 — GET /documents/{id}/definitions + PATCH /documents/{id}/definitions/{id}
export interface DefinitionOut {
  id: number;
  term: string;
  definition: string;
  source_clause_num: string | null;
  source_clause_id: number | null;
  edited_by_user: string | null;
  edited_at: string | null;
  original_definition: string | null;
  original_term: string | null;
}

export interface DefinitionListOut {
  document_id: number;
  definition_count: number;
  definitions: DefinitionOut[];
}

export interface DefinitionPatchOut {
  id: number;
  term: string;
  definition: string;
  edited_by_user: string | null;
  edited_at: string | null;
  original_definition: string | null;
  original_term: string | null;
}

// Backend #326 — POST /documents/{id}/reread
export interface ReReadDiff {
  action: 'add' | 'update' | 'remove';
  obligation_id: number | null;
  field: string | null;
  old_value: string | null;
  new_value: string | null;
  description: string | null;
  obligation_type: string | null;
  due_date: string | null;
  source_clause_num: string | null;
  protected: boolean;
}

export interface ReReadOut {
  document_id: number;
  clauses_checked: number;
  diffs: ReReadDiff[];
}
