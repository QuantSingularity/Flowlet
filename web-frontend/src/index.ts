// ============================================================================
// Flowlet Web Frontend - Public Library Exports
// ============================================================================

// App
export { default as App } from "./App";

// Layout
export { default as ErrorBoundary } from "./components/layout/ErrorBoundary";
export { default as LoadingScreen } from "./components/layout/LoadingScreen";
export { default as OfflineIndicator } from "./components/layout/OfflineIndicator";
export { default as Header } from "./components/layout/Header";
export { default as Sidebar } from "./components/layout/Sidebar";
export { default as Layout } from "./components/layout/Layout";

// Auth
export { default as LoginScreen } from "./components/auth/LoginScreen";
export { default as RegisterScreen } from "./components/auth/RegisterScreen";
export { default as OnboardingFlow } from "./components/auth/OnboardingFlow";
export { default as ProtectedRoute } from "./components/auth/ProtectedRoute";
export { default as PublicRoute } from "./components/auth/PublicRoute";
export { default as BiometricAuth } from "./components/auth/BiometricAuth";
export { default as MFASetup } from "./components/auth/MFASetup";
export { default as SessionManager } from "./components/auth/SessionManager";
export { default as RoleBasedAccess } from "./components/auth/RoleBasedAccess";

// Feature - Dashboard
export { default as Dashboard } from "./components/features/dashboard/Dashboard";
export { default as TransactionList } from "./components/features/dashboard/TransactionList";

// Feature - Wallet
export { default as WalletScreen } from "./components/features/wallet/WalletScreen";

// Feature - Cards
export { default as CardsScreen } from "./components/features/cards/CardsScreen";
export { default as CardDetails } from "./components/features/cards/CardDetails";
export { default as IssueCard } from "./components/features/cards/IssueCard";

// Feature - Transactions
export { default as TransactionHistory } from "./components/features/transactions/TransactionHistory";
export { default as SendMoney } from "./components/features/transactions/SendMoney";
export { default as ReceiveMoney } from "./components/features/transactions/ReceiveMoney";

// Feature - Analytics & Budgeting
export { default as AnalyticsScreen } from "./components/features/analytics/AnalyticsScreen";
export { default as BudgetingScreen } from "./components/features/budgeting/BudgetingScreen";

// Feature - AI
export { default as ChatbotScreen } from "./components/features/ai/ChatbotScreen";
export { default as FraudAlerts } from "./components/features/ai/FraudAlerts";
export { default as AIFraudDetectionScreen } from "./components/features/ai/AIFraudDetectionScreen";

// Feature - Security
export { default as SecurityScreen } from "./components/features/security/SecurityScreen";
export { default as EnhancedSecurityScreen } from "./components/features/security/EnhancedSecurityScreen";

// Feature - Settings
export { default as SettingsScreen } from "./components/features/settings/SettingsScreen";

// Hooks
export { useAuth } from "./hooks/useAuth";
export { useAppDispatch, useAppSelector } from "./hooks/redux";
export {
  useResponsive,
  useOnlineStatus,
  useDebounce,
  useLocalStorage,
} from "./hooks/useResponsive";

// Store
export { store } from "./store";
export type { RootState, AppDispatch } from "./store";

// Utilities
export {
  cn,
  formatCurrency,
  formatDate,
  formatRelativeTime,
  formatNumber,
} from "./lib/utils";

// Types
export type * from "./types";
