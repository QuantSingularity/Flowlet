// ============================================================================
// authService — integrates with Flowlet Flask backend
// Falls back to demo mode when backend is unreachable
// ============================================================================
import { apiClient, TokenManager } from "./client";
import type { LoginCredentials, RegisterData, User } from "@/types";

const DEMO_USER: User = {
  id: "demo-user-001",
  email: "demo@flowlet.com",
  firstName: "Demo",
  lastName: "User",
  fullName: "Demo User",
  role: "customer",
  permissions: [],
  isEmailVerified: true,
  isPhoneVerified: false,
  kycStatus: "completed",
  mfaEnabled: false,
  status: "active",
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token?: string;
}

function mapBackendUser(data: Record<string, unknown>): User {
  return {
    id: String(data.id ?? data.user_id ?? ""),
    email: String(data.email ?? ""),
    firstName: String(data.first_name ?? data.firstName ?? ""),
    lastName: String(data.last_name ?? data.lastName ?? ""),
    fullName: String(
      data.full_name ??
        data.fullName ??
        `${data.first_name ?? ""} ${data.last_name ?? ""}`.trim(),
    ),
    role: (data.role as User["role"]) ?? "customer",
    permissions: (data.permissions as User["permissions"]) ?? [],
    isEmailVerified: Boolean(
      data.is_email_verified ?? data.isEmailVerified ?? false,
    ),
    isPhoneVerified: Boolean(
      data.is_phone_verified ?? data.isPhoneVerified ?? false,
    ),
    kycStatus: (data.kyc_status ??
      data.kycStatus ??
      "not_started") as User["kycStatus"],
    mfaEnabled: Boolean(data.mfa_enabled ?? data.mfaEnabled ?? false),
    status: (data.status as User["status"]) ?? "active",
    phoneNumber: data.phone_number as string | undefined,
    createdAt: String(
      data.created_at ?? data.createdAt ?? new Date().toISOString(),
    ),
    updatedAt: String(
      data.updated_at ?? data.updatedAt ?? new Date().toISOString(),
    ),
  };
}

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Demo mode
    if (
      credentials.email === "demo@flowlet.com" &&
      credentials.password === "demo123"
    ) {
      const token = "demo.token." + Date.now();
      TokenManager.setTokens(token);
      this._storeUser(DEMO_USER);
      return { user: DEMO_USER, access_token: token };
    }

    try {
      const data = await apiClient.post<Record<string, unknown>>(
        "/auth/login",
        credentials,
        { skipAuth: true },
      );
      const access = String(data.access_token ?? data.token ?? "");
      const refresh = data.refresh_token
        ? String(data.refresh_token)
        : undefined;
      TokenManager.setTokens(access, refresh);
      // The login endpoint returns only tokens, not the user. Fetch the
      // authenticated user separately now that the token is set.
      let user: User;
      if (data.user) {
        user = mapBackendUser(data.user as Record<string, unknown>);
      } else {
        const status =
          await apiClient.get<Record<string, unknown>>("/auth/status");
        user = mapBackendUser(
          (status.user as Record<string, unknown>) ?? status,
        );
      }
      this._storeUser(user);
      return { user, access_token: access, refresh_token: refresh };
    } catch (err) {
      throw err;
    }
  }

  async register(userData: RegisterData): Promise<AuthResponse> {
    const payload = {
      email: userData.email,
      password: userData.password,
      first_name: userData.firstName,
      last_name: userData.lastName,
      phone_number: userData.phoneNumber,
    };
    // The register endpoint creates the account but does not return tokens
    // (it returns a verification token). Log in immediately afterwards to
    // obtain the access/refresh tokens and the authenticated user.
    await apiClient.post<Record<string, unknown>>("/auth/register", payload, {
      skipAuth: true,
    });
    return this.login({
      email: userData.email,
      password: userData.password,
    });
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      /* ignore server errors on logout */
    } finally {
      TokenManager.clearTokens();
      this._clearUser();
    }
  }

  async getCurrentUser(): Promise<User> {
    const stored = this.getCurrentUserFromStorage();
    if (stored) return stored;

    const data = await apiClient.get<Record<string, unknown>>("/auth/status");
    const user = mapBackendUser((data.user as Record<string, unknown>) ?? data);
    this._storeUser(user);
    return user;
  }

  async refreshToken(): Promise<string> {
    const refresh = TokenManager.getRefreshToken();
    if (!refresh) throw new Error("No refresh token");

    const data = await apiClient.post<Record<string, unknown>>(
      "/auth/refresh",
      { refresh_token: refresh },
      { skipAuth: true },
    );
    const newAccess = String(data.access_token ?? data.token ?? "");
    TokenManager.setTokens(newAccess);
    return newAccess;
  }

  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.post(
      "/auth/password/reset/request",
      { email },
      { skipAuth: true },
    );
  }

  async confirmPasswordReset(
    token: string,
    newPassword: string,
  ): Promise<void> {
    await apiClient.post(
      "/auth/password/reset/confirm",
      { token, new_password: newPassword },
      { skipAuth: true },
    );
  }

  isAuthenticated(): boolean {
    const token = TokenManager.getAccessToken();
    if (!token) return false;
    if (token.startsWith("demo.")) return true;
    return !TokenManager.isTokenExpired(token);
  }

  getCurrentUserFromStorage(): User | null {
    try {
      const raw = sessionStorage.getItem("flowlet_user");
      if (!raw) return null;
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  }

  private _storeUser(user: User): void {
    try {
      sessionStorage.setItem("flowlet_user", JSON.stringify(user));
    } catch {
      /* ignore */
    }
  }

  private _clearUser(): void {
    try {
      sessionStorage.removeItem("flowlet_user");
    } catch {
      /* ignore */
    }
  }
}

export const authService = new AuthService();
