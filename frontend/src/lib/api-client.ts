import { useAuthStore } from "@/stores/auth-store";
import type { ApiErrorBody, TokenResponse } from "@/types/api";

/**
 * Fetch wrapper for the FastAPI backend.
 * - Injects the JWT Authorization header from the auth store.
 * - On 401, refreshes once via the HttpOnly cookie, then retries.
 * - Parses structured backend errors ({ error: { code, message } }).
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: Record<string, unknown>;

  constructor(
    status: number,
    code: string,
    message: string,
    details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

interface ApiFetchOptions extends Omit<RequestInit, "headers"> {
  headers?: Record<string, string>;
}

async function parseErrorResponse(response: Response): Promise<ApiClientError> {
  let code = "UNKNOWN_ERROR";
  let message = `Request failed with status ${response.status}`;
  let details: Record<string, unknown> | undefined;
  try {
    const body = (await response.json()) as {
      error?: Partial<ApiErrorBody["error"]>;
      detail?: unknown;
    };
    if (body?.error) {
      code = body.error.code ?? code;
      message = body.error.message ?? message;
      details = body.error.details;
    } else if (typeof body?.detail === "string") {
      // FastAPI HTTPException shape: { detail: "..." }
      message = body.detail;
    } else if (Array.isArray(body?.detail)) {
      // FastAPI RequestValidationError: { detail: [{ loc, msg, type }, ...] }
      const problems = body.detail
        .filter(
          (item): item is { msg: string } =>
            typeof item === "object" &&
            item !== null &&
            typeof (item as { msg?: unknown }).msg === "string",
        )
        .map((item) => item.msg);
      if (problems.length > 0) {
        code = "VALIDATION_ERROR";
        message = problems.join("; ");
      }
    }
  } catch {
    // Non-JSON error body — keep defaults
  }
  return new ApiClientError(response.status, code, message, details);
}

async function refreshAccessToken(): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (!response.ok) return null;
    const body = (await response.json()) as TokenResponse;
    return body.access_token;
  } catch {
    return null;
  }
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const token = useAuthStore.getState().token;

  const execute = (authToken: string | null): Promise<Response> => {
    const headers: Record<string, string> = { ...options.headers };
    // FormData must keep its auto-generated multipart boundary — forcing
    // application/json here makes the backend fail to parse the body (422).
    const isFormData = options.body instanceof FormData;
    if (options.body && !isFormData && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }
    if (authToken) {
      headers.Authorization = `Bearer ${authToken}`;
    }
    return fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
      // Needed so the backend can set/read the HttpOnly refresh cookie
      credentials: "include",
    });
  };

  let response = await execute(token);

  // Auto-refresh once on 401, then retry the original request
  if (response.status === 401 && token) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      useAuthStore.getState().setAuth(newToken, useAuthStore.getState().user);
      response = await execute(newToken);
    } else {
      useAuthStore.getState().clearAuth();
    }
  }

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  return (await response.json()) as T;
}
