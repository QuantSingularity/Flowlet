import React from "react";
import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";
import { Toaster } from "sonner";

import LoginScreen from "@/components/auth/LoginScreen";
import RegisterScreen from "@/components/auth/RegisterScreen";
import OnboardingFlow from "@/components/auth/OnboardingFlow";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import PublicRoute from "@/components/auth/PublicRoute";
import Layout from "@/components/layout/Layout";
import LoadingScreen from "@/components/layout/LoadingScreen";
import OfflineIndicator from "@/components/layout/OfflineIndicator";
import ForgotPasswordScreen from "@/components/pages/public/ForgotPasswordScreen";
import HomePage from "@/components/pages/public/HomePage";
import PaymentsPage from "@/components/pages/public/PaymentsPage";
import CompliancePage from "@/components/pages/public/CompliancePage";
import DeveloperPortalPage from "@/components/pages/public/DeveloperPortalPage";
import ProfilePage from "@/components/pages/ProfilePage";
import NotificationsPage from "@/components/pages/NotificationsPage";
import NotFoundPage from "@/components/pages/NotFoundPage";

import Dashboard from "@/components/features/dashboard/Dashboard";
import WalletScreen from "@/components/features/wallet/WalletScreen";
import CardsScreen from "@/components/features/cards/CardsScreen";
import CardDetails from "@/components/features/cards/CardDetails";
import IssueCard from "@/components/features/cards/IssueCard";
import TransactionHistory from "@/components/features/transactions/TransactionHistory";
import SendMoney from "@/components/features/transactions/SendMoney";
import ReceiveMoney from "@/components/features/transactions/ReceiveMoney";
import AnalyticsScreen from "@/components/features/analytics/AnalyticsScreen";
import BudgetingScreen from "@/components/features/budgeting/BudgetingScreen";
import ChatbotScreen from "@/components/features/ai/ChatbotScreen";
import FraudAlerts from "@/components/features/ai/FraudAlerts";
import AIFraudDetectionScreen from "@/components/features/ai/AIFraudDetectionScreen";
import SecurityScreen from "@/components/features/security/SecurityScreen";
import EnhancedSecurityScreen from "@/components/features/security/EnhancedSecurityScreen";
import SettingsScreen from "@/components/features/settings/SettingsScreen";
import WorkflowMain from "@/components/features/workflow/WorkflowMain";

import { useOnlineStatus, useResponsive } from "@/hooks";
import { useAuth } from "@/hooks/useAuth";

const AppInner: React.FC = () => {
  const { isLoading } = useAuth();
  const isOnline = useOnlineStatus();
  const { isMobile } = useResponsive();

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Router>
        {!isOnline && <OfflineIndicator />}

        <Routes>
          {/* Root: redirect to public homepage */}
          <Route path="/" element={<Navigate to="/home" replace />} />

          {/* Public marketing pages */}
          <Route path="/home" element={<HomePage />} />
          <Route path="/payments" element={<PaymentsPage />} />
          <Route path="/compliance" element={<CompliancePage />} />
          <Route path="/developer" element={<DeveloperPortalPage />} />

          {/* Auth routes - redirect to /dashboard if already logged in */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <LoginScreen />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <RegisterScreen />
              </PublicRoute>
            }
          />
          <Route
            path="/onboarding"
            element={
              <PublicRoute>
                <OnboardingFlow />
              </PublicRoute>
            }
          />
          <Route
            path="/forgot-password"
            element={
              <PublicRoute>
                <ForgotPasswordScreen />
              </PublicRoute>
            }
          />

          {/*
           * Protected app routes via a pathless layout route.
           */}
          <Route
            element={
              <ProtectedRoute>
                <Layout isMobile={isMobile} />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<Dashboard />} />

            <Route path="/wallet" element={<WalletScreen />} />
            <Route
              path="/wallet/transactions"
              element={<TransactionHistory />}
            />
            <Route path="/wallet/send" element={<SendMoney />} />
            <Route path="/wallet/receive" element={<ReceiveMoney />} />

            <Route path="/cards" element={<CardsScreen />} />
            <Route path="/cards/issue" element={<IssueCard />} />
            <Route path="/cards/:cardId" element={<CardDetails />} />

            <Route path="/analytics" element={<AnalyticsScreen />} />
            <Route path="/financial-planning" element={<BudgetingScreen />} />
            <Route path="/budgeting" element={<BudgetingScreen />} />

            <Route path="/chat" element={<ChatbotScreen />} />
            <Route path="/alerts" element={<FraudAlerts />} />
            <Route
              path="/fraud-detection"
              element={<AIFraudDetectionScreen />}
            />

            <Route path="/security" element={<SecurityScreen />} />
            <Route
              path="/security/advanced"
              element={<EnhancedSecurityScreen />}
            />
            <Route path="/workflows" element={<WorkflowMain />} />
            <Route path="/settings" element={<SettingsScreen />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
          </Route>

          <Route path="*" element={<NotFoundPage />} />
        </Routes>

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: "hsl(var(--background))",
              color: "hsl(var(--foreground))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "0.75rem",
              fontSize: "13px",
            },
          }}
        />
      </Router>
    </div>
  );
};

export default AppInner;
