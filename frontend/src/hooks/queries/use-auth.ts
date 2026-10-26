"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import { apiFetch, ApiClientError } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import type { TokenResponse, UserResponse } from "@/types/api";

/** Machine-readable reason an auth attempt failed. */
export type AuthErrorKind =
  | "email_taken"
  | "invalid_credentials"
  | "validation"
  | "network";

export class AuthError extends Error {
  readonly kind: AuthErrorKind;

  constructor(kind: AuthErrorKind, message: string) {
    super(message);
    this.name = "AuthError";
    this.kind = kind;
  }
}

const MESSAGES: Record<AuthErrorKind, string> = {
  email_taken: "An account with this email already exists.",
  invalid_credentials: "Invalid email or password.",
  network: "Could not reach the server. Is the backend running?",
  validation: "Check your input and try again.",
};

export function toAuthError(error: unknown): AuthError {
  if (error instanceof ApiClientError) {
    if (error.code === "CONFLICT") {
      return new AuthError("email_taken", MESSAGES.email_taken);
    }
    if (error.status === 401 || error.status === 403) {
      return new AuthError("invalid_credentials", MESSAGES.invalid_credentials);
    }
  }
  if (error instanceof TypeError) {
    return new AuthError("network", MESSAGES.network);
  }
  return new AuthError("validation", MESSAGES.validation);
}

/** Store the access token after a token-issuing call (user loads via /me). */
function persistSession(tokens: TokenResponse) {
  useAuthStore.getState().setAuth(tokens.access_token, null);
}

/** Register — one request; backend returns tokens and sets the cookie. */
export function useRegister() {
  return useMutation({
    mutationFn: async (input: {
      name: string;
      email: string;
      password: string;
    }) => {
      try {
        const tokens = await apiFetch<TokenResponse>("/api/v1/auth/register", {
          method: "POST",
          body: JSON.stringify(input),
        });
        persistSession(tokens);
        return tokens;
      } catch (error) {
        throw toAuthError(error);
      }
    },
  });
}

/** Login — stores the access token; refresh token arrives as a cookie. */
export function useLogin() {
  return useMutation({
    mutationFn: async (input: { email: string; password: string }) => {
      try {
        const tokens = await apiFetch<TokenResponse>("/api/v1/auth/login", {
          method: "POST",
          body: JSON.stringify(input),
        });
        persistSession(tokens);
        return tokens;
      } catch (error) {
        throw toAuthError(error);
      }
    },
  });
}

/** Logout — revokes the refresh token server-side and clears local state. */
export function useLogout() {
  const clearAuth = useAuthStore((s) => s.clearAuth);

  return useMutation({
    mutationFn: async () => {
      try {
        await apiFetch<void>("/api/v1/auth/logout", { method: "POST" });
      } catch {
        // Cookie may already be gone — local logout must succeed regardless.
      }
      clearAuth();
    },
  });
}

/**
 * Profile of the logged-in user. Runs whenever a token exists, so the
 * user is restored on reload and after login (storage keeps user=null).
 * On a failed refresh the api-client clears auth, which disables this.
 */
export function useCurrentUser() {
  const token = useAuthStore((s) => s.token);

  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => apiFetch<UserResponse>("/api/v1/auth/me"),
    enabled: Boolean(token),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}
