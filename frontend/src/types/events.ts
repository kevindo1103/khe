/**
 * Event / audit trail types (#281, D-07)
 * Mirrored from backend schemas/documents.py
 */

export interface EventOut {
  id: number;
  event_type: string;
  entity_type: string;
  entity_id: number;
  actor: string | null;
  created_at: string | null;
  payload: Record<string, unknown> | null;
}

export interface EventListOut {
  document_id: number;
  total: number;
  limit: number;
  offset: number;
  items: EventOut[];
}
