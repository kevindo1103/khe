/**
 * Tenant types
 * Mirrored from backend schemas exactly to prevent drift.
 */

export interface LegalNameIn {
  legal_name: string;
}

export interface LegalNameOut {
  ok: boolean;
  legal_name: string;
}
