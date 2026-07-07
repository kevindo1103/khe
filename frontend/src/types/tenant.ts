/**
 * Tenant types
 * Mirrored from backend schemas exactly to prevent drift.
 */

export interface LegalNameIn {
  legal_name: string;
}

export interface LegalNameOut {
  ok: boolean;
  legal_name: string | null;
}

// #213 — tenant journey state (GET /tenants/me) + forward-only advance.
export interface TenantMeOut {
  id: string;
  name: string;
  plan: string;
  is_active: boolean;
  journey_stage: string;
  is_first_session: boolean;
}

export interface JourneyAdvanceIn {
  journey_stage: string;
}

export interface JourneyOut {
  journey_stage: string;
  is_first_session: boolean;
}

// #495 P2 — GET/PUT /tenants/me/compliance-profile
export interface ComplianceProfileOut {
  legal_form: string | null;
  has_employees: boolean | null;
  vat_period: string | null;        // "month" | "quarter"
  fiscal_year_start: string | null; // ISO date "YYYY-MM-DD"
}

export type ComplianceProfileIn = ComplianceProfileOut;
