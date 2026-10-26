/**
 * TypeScript mirrors of backend Pydantic API contracts.
 * Source of truth: backend/app/api/schemas/ and app/common/exceptions.py
 */

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  name: string;
  tier: string;
  created_at: string;
}
