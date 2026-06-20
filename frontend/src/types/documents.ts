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
  created_at: string | null;
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
  failure_reason: string | null;
  parties?: { name: string; role_label: string | null }[];
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
