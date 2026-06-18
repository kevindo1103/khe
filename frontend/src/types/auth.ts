/**
 * Typed contract for POST /auth/login
 * Mirrors backend Pydantic schema exactly to prevent 422 schema-vs-body drift.
 */
export interface LoginRequest {
  tenant_id: string;
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface JwtPayload {
  sub: string;
  tenant_id: string;
  role: string;
  exp: number;
}

export interface User {
  username: string;
  tenant_id: string;
  role: string;
}
