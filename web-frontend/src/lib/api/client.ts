// ============================================================================
// Flowlet API Client — base HTTP client, ApiError, TokenManager
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export class TokenManager {
  private static accessToken: string | null = null;
  private static refreshToken: string | null = null;

  static setTokens(access: string, refresh?: string): void {
    TokenManager.accessToken = access;
    if (refresh) TokenManager.refreshToken = refresh;
    try {
      sessionStorage.setItem("flowlet_access_token", access);
      if (refresh) sessionStorage.setItem("flowlet_refresh_token", refresh);
    } catch {
      /* storage unavailable */
    }
  }

  /** Convenience setter for a single access token (alias for setTokens) */
  static setAccessToken(token: string): void {
    TokenManager.accessToken = token;
    try {
      sessionStorage.setItem("flowlet_access_token", token);
    } catch {
      /* storage unavailable */
    }
  }

  /** Convenience setter for a single refresh token */
  static setRefreshToken(token: string): void {
    TokenManager.refreshToken = token;
    try {
      sessionStorage.setItem("flowlet_refresh_token", token);
    } catch {
      /* storage unavailable */
    }
  }

  static getAccessToken(): string | null {
    if (TokenManager.accessToken) return TokenManager.accessToken;
    try {
      const stored = sessionStorage.getItem("flowlet_access_token");
      if (stored) TokenManager.accessToken = stored;
      return stored;
    } catch {
      return null;
    }
  }

  static getRefreshToken(): string | null {
    if (TokenManager.refreshToken) return TokenManager.refreshToken;
    try {
      const stored = sessionStorage.getItem("flowlet_refresh_token");
      if (stored) TokenManager.refreshToken = stored;
      return stored;
    } catch {
      return null;
    }
  }

  /** Store user data, stripping any password field */
  static setUser(user: Record<string, unknown>): void {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { password, ...safeUser } = user;
    try {
      sessionStorage.setItem("flowlet_user", JSON.stringify(safeUser));
    } catch {
      /* ignore */
    }
  }

  static getUser(): Record<string, unknown> | null {
    try {
      const raw = sessionStorage.getItem("flowlet_user");
      return raw ? (JSON.parse(raw) as Record<string, unknown>) : null;
    } catch {
      return null;
    }
  }

  static clearTokens(): void {
    TokenManager.accessToken = null;
    TokenManager.refreshToken = null;
    try {
      sessionStorage.removeItem("flowlet_access_token");
      sessionStorage.removeItem("flowlet_refresh_token");
      sessionStorage.removeItem("flowlet_user");
    } catch {
      /* ignore */
    }
  }

  static isTokenExpired(token: string): boolean {
    // Demo tokens are never expired
    if (token.startsWith("demo.")) return false;
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return Date.now() >= payload.exp * 1000;
    } catch {
      return true;
    }
  }
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: unknown;

  constructor(
    message: string,
    status: number,
    code = "API_ERROR",
    details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }

  get isUnauthorized() {
    return this.status === 401;
  }
  get isForbidden() {
    return this.status === 403;
  }
  get isNotFound() {
    return this.status === 404;
  }
  get isServerError() {
    return this.status >= 500;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  skipAuth?: boolean;
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, skipAuth = false, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((fetchOptions.headers ?? {}) as Record<string, string>),
  };

  if (!skipAuth) {
    const token = TokenManager.getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith("http")
    ? endpoint
    : `${API_BASE_URL}${endpoint}`;

  let response: Response;
  try {
    response = await fetch(url, {
      ...fetchOptions,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(
      "Network error — backend unreachable",
      0,
      "NETWORK_ERROR",
    );
  }

  if (!response.ok) {
    let errorData: { message?: string; error?: string; code?: string } = {};
    try {
      errorData = await response.json();
    } catch {
      /* non-JSON body */
    }
    const message =
      errorData.message || errorData.error || `HTTP ${response.status}`;
    throw new ApiError(
      message,
      response.status,
      errorData.code ?? "HTTP_ERROR",
    );
  }

  if (response.status === 204) return undefined as T;

  try {
    return await response.json();
  } catch {
    return undefined as T;
  }
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "GET" }),
  post: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "POST", body }),
  put: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "PUT", body }),
  patch: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "PATCH", body }),
  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "DELETE" }),
};

/**
 * apiFetch — convenience wrapper matching the signature used by authService
 * and walletService. Delegates to the internal `request` function.
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: {
    method?: string;
    body?: string;
    headers?: Record<string, string>;
  } = {},
): Promise<T> {
  return request<T>(path, {
    method: (options.method as RequestOptions["method"]) ?? "GET",
    body: options.body !== undefined ? JSON.parse(options.body) : undefined,
    skipAuth: false,
  });
}
