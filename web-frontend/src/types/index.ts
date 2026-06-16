// Improved TypeScript type definitions for Flowlet web-frontend

// ============================================================================
// Core Types
// ============================================================================

export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// ============================================================================
// User & Authentication Types
// ============================================================================

export interface User extends BaseEntity {
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  phoneNumber?: string;
  dateOfBirth?: string;
  address?: Address;
  profilePicture?: string;
  role: UserRole;
  permissions: Permission[];
  isEmailVerified: boolean;
  isPhoneVerified: boolean;
  kycStatus: KYCStatus;
  mfaEnabled: boolean;
  lastLoginAt?: string;
  status: UserStatus;
}

export type UserRole = "customer" | "admin" | "support" | "compliance";

export type UserStatus =
  | "active"
  | "inactive"
  | "suspended"
  | "pending_verification";

export type KYCStatus =
  | "not_started"
  | "in_progress"
  | "completed"
  | "rejected"
  | "expired";

export interface Permission {
  id: string;
  name: string;
  resource: string;
  action: string;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  phoneNumber?: string;
  // NOTE: the registration form does not currently collect consent. These are
  // optional until a terms/privacy checkbox is added to RegisterScreen. See
  // FIXES.md (frontend) for the flagged product gap.
  acceptTerms?: boolean;
  acceptPrivacy?: boolean;
}

export interface MFASetupData {
  secret: string;
  qrCode: string;
  backupCodes: string[];
}

export interface BiometricAuthData {
  publicKey: string;
  credentialId: string;
  deviceName: string;
}

// ============================================================================
// Financial Types
// ============================================================================

export interface Account extends BaseEntity {
  accountNumber: string;
  accountType: AccountType;
  balance: Money;
  availableBalance: Money;
  currency: Currency;
  status: AccountStatus;
  userId: string;
  bankName: string;
  routingNumber?: string;
  swiftCode?: string;
  iban?: string;
}

export type AccountType =
  | "checking"
  | "savings"
  | "credit"
  | "investment"
  | "business";

export type AccountStatus = "active" | "inactive" | "frozen" | "closed";

export interface Money {
  amount: number;
  currency: Currency;
  formatted: string;
}

export type Currency = "USD" | "EUR" | "GBP" | "CAD" | "JPY" | "AUD" | "CHF";

export interface Transaction extends BaseEntity {
  transactionId: string;
  accountId: string;
  amount: Money;
  type: TransactionType;
  status: TransactionStatus;
  category: TransactionCategory;
  description: string;
  merchantName?: string;
  merchantCategory?: string;
  reference?: string;
  fromAccount?: string;
  toAccount?: string;
  fee?: Money;
  exchangeRate?: number;
  location?: TransactionLocation;
  metadata?: Record<string, any>;
  processedAt?: string;
  settledAt?: string;
}

export type TransactionType =
  | "debit"
  | "credit"
  | "transfer"
  | "payment"
  | "refund"
  | "fee"
  | "interest";

export type TransactionStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled"
  | "reversed";

export type TransactionCategory =
  | "food_dining"
  | "transportation"
  | "shopping"
  | "entertainment"
  | "healthcare"
  | "utilities"
  | "income"
  | "transfer"
  | "fees"
  | "other";

export interface TransactionLocation {
  latitude: number;
  longitude: number;
  address?: string;
  city?: string;
  country?: string;
}

export interface TransferRequest {
  fromAccountId: string;
  toAccountId?: string;
  recipientEmail?: string;
  recipientPhone?: string;
  amount: number;
  currency: Currency;
  description?: string;
  scheduledAt?: string;
  recurring?: RecurringTransferConfig;
}

export interface RecurringTransferConfig {
  frequency: "daily" | "weekly" | "monthly" | "yearly";
  interval: number;
  endDate?: string;
  maxOccurrences?: number;
}

// ============================================================================
// Card Types
// ============================================================================

export interface Card extends BaseEntity {
  cardNumber: string; // Masked: **** **** **** 1234
  cardType: CardType;
  cardBrand: CardBrand;
  expiryMonth: number;
  expiryYear: number;
  holderName: string;
  status: CardStatus;
  accountId: string;
  isVirtual: boolean;
  spendingLimits: SpendingLimits;
  features: CardFeature[];
  lastUsedAt?: string;
}

export type CardType = "debit" | "credit" | "prepaid" | "virtual";

export type CardBrand = "visa" | "mastercard" | "amex" | "discover";

export type CardStatus =
  | "active"
  | "inactive"
  | "blocked"
  | "expired"
  | "lost"
  | "stolen";

export interface SpendingLimits {
  daily: Money;
  weekly: Money;
  monthly: Money;
  perTransaction: Money;
  atmDaily: Money;
}

export type CardFeature =
  | "contactless"
  | "chip"
  | "magnetic_stripe"
  | "virtual_numbers"
  | "freeze_unfreeze";

export interface CardTransaction extends Transaction {
  cardId: string;
  authorizationCode?: string;
  merchantId?: string;
  isContactless: boolean;
  isOnline: boolean;
}

// ============================================================================
// Security & Compliance Types
// ============================================================================

export interface SecurityEvent extends BaseEntity {
  userId: string;
  eventType: SecurityEventType;
  severity: SecuritySeverity;
  description: string;
  ipAddress: string;
  userAgent: string;
  location?: string;
  resolved: boolean;
  resolvedAt?: string;
  resolvedBy?: string;
}

export type SecurityEventType =
  | "login_attempt"
  | "login_success"
  | "login_failure"
  | "password_change"
  | "mfa_enabled"
  | "mfa_disabled"
  | "suspicious_activity"
  | "account_locked"
  | "data_breach_attempt";

export type SecuritySeverity = "low" | "medium" | "high" | "critical";

export interface AuditLog extends BaseEntity {
  userId: string;
  action: string;
  resource: string;
  resourceId: string;
  changes?: Record<string, { from: any; to: any }>;
  ipAddress: string;
  userAgent: string;
  timestamp: string;
}

export interface ComplianceCheck extends BaseEntity {
  userId: string;
  checkType: ComplianceCheckType;
  status: ComplianceStatus;
  result: Record<string, any>;
  riskScore: number;
  flags: string[];
  reviewedBy?: string;
  reviewedAt?: string;
  notes?: string;
}

export type ComplianceCheckType = "kyc" | "aml" | "sanctions" | "pep" | "fraud";

export type ComplianceStatus = "pass" | "fail" | "review_required" | "pending";

// ============================================================================
// Analytics & Reporting Types
// ============================================================================

export interface SpendingAnalytics {
  period: "daily" | "weekly" | "monthly" | "yearly";
  totalSpent: Money;
  totalIncome: Money;
  netFlow: Money;
  categoryBreakdown: CategorySpending[];
  trends: SpendingTrend[];
  budgetComparison?: BudgetComparison;
}

export interface CategorySpending {
  category: TransactionCategory;
  amount: Money;
  percentage: number;
  transactionCount: number;
  averageAmount: Money;
}

export interface SpendingTrend {
  date: string;
  amount: Money;
  category?: TransactionCategory;
}

export interface BudgetComparison {
  budgeted: Money;
  spent: Money;
  remaining: Money;
  percentageUsed: number;
  isOverBudget: boolean;
}

export interface Budget extends BaseEntity {
  userId: string;
  name: string;
  category: TransactionCategory;
  amount: Money;
  period: "monthly" | "weekly" | "yearly";
  startDate: string;
  endDate?: string;
  isActive: boolean;
  alerts: BudgetAlert[];
}

export interface BudgetAlert {
  threshold: number; // Percentage
  isEnabled: boolean;
  lastTriggered?: string;
}

// ============================================================================
// UI & Component Types
// ============================================================================

export interface Theme {
  mode: "light" | "dark" | "system";
  primaryColor: string;
  accentColor: string;
  fontSize: "small" | "medium" | "large";
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
  inApp: boolean;
  categories: {
    transactions: boolean;
    security: boolean;
    marketing: boolean;
    updates: boolean;
  };
}

export interface AppSettings {
  theme: Theme;
  notifications: NotificationPreferences;
  language: string;
  currency: Currency;
  timezone: string;
  biometricEnabled: boolean;
  autoLockTimeout: number; // minutes
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  errors?: Record<string, string[]>;
  meta?: {
    timestamp: string;
    requestId: string;
    version: string;
  };
}

export interface PaginatedApiResponse<T> extends ApiResponse<T[]> {
  pagination: PaginationMeta;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
  field?: string;
}

// ============================================================================
// Form Types
// ============================================================================

export interface FormField {
  name: string;
  label: string;
  type:
    | "text"
    | "email"
    | "password"
    | "number"
    | "select"
    | "textarea"
    | "checkbox"
    | "radio";
  required: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    custom?: (value: any) => string | undefined;
  };
}

export interface FormState {
  values: Record<string, any>;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
  isSubmitting: boolean;
  isValid: boolean;
}

// ============================================================================
// Utility Types
// ============================================================================

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type ValueOf<T> = T[keyof T];

export type NonEmptyArray<T> = [T, ...T[]];

// ============================================================================
// Event Types
// ============================================================================

export interface AppEvent {
  type: string;
  payload?: any;
  timestamp: string;
}

export interface TransactionEvent extends AppEvent {
  type: "transaction:created" | "transaction:updated" | "transaction:failed";
  payload: {
    transactionId: string;
    userId: string;
    amount: Money;
    status: TransactionStatus;
  };
}

export interface SecurityEvent extends AppEvent {
  type: "security:login" | "security:logout" | "security:suspicious_activity";
  payload: {
    userId: string;
    ipAddress: string;
    userAgent: string;
    severity?: SecuritySeverity;
  };
}

// ============================================================================
// Export all types
// ============================================================================

// export * from './api'; // Removed non-existent module export
// export * from './components'; // Removed non-existent module export
// export * from './hooks'; // Removed non-existent module export

// ============================================================================
// Auth State (used by store/authSlice)
// ============================================================================

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// ============================================================================
// Wallet (used by store/api)
// ============================================================================

export interface Wallet extends BaseEntity {
  userId: string;
  balance: number;
  currency: Currency;
  type: "checking" | "savings" | "investment";
  isActive: boolean;
  accountNumber?: string;
  routingNumber?: string;
}

// ============================================================================
// Analytics (used by store/api)
// ============================================================================

export interface AnalyticsData {
  totalRevenue: number;
  totalExpenses: number;
  netIncome: number;
  transactionCount: number;
  categoryBreakdown: CategorySpending[];
  trends: SpendingTrend[];
  period: string;
}

// ============================================================================
// Notification (used by store/uiSlice)
// ============================================================================
export type NotificationType =
  | "transaction"
  | "security"
  | "alert"
  | "info"
  | "promotion";

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  read: boolean;
  createdAt: string;
  updatedAt: string;
}

// ============================================================================
// PaginatedResponse (alias used by store/api and walletService)
// ============================================================================
export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
  message?: string;
}
