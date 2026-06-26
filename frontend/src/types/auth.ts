/**
 * Typed contract for auth endpoints
 * Mirrors backend Pydantic schema exactly to prevent 422 schema-vs-body drift.
 */
export interface LoginRequest {
  tenant_id: string;
  username: string;
  password: string;
}

export interface LoginOut {
  user: { username: string; role: string };
  tenant_id: string;
}

export interface UserOut {
  user_id: number;
  username: string;
  tenant_id: string;
  role: string;
}

export type User = UserOut;
