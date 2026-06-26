/**
 * Consent types — NĐ 13/2023 (DEC-010, D-10). Mirrors /consent endpoints.
 */
export type ConsentPurpose = 'vision_extraction' | 'reminder_send' | 'firm_partner_access';

export interface ConsentEntry {
  purpose: ConsentPurpose;
  status: 'granted' | 'none';
  consent_reference?: string;
  consent_text_version?: string;
  channel?: string | null;
  channel_target_ref?: string | null;
  at?: string;
}

export interface ConsentGrantIn {
  purpose: ConsentPurpose;
  channel?: string;
  channel_target_ref?: string;
  consent_text_version?: string;
}

export interface ConsentRevokeIn {
  purpose: ConsentPurpose;
}
