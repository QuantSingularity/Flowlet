import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  CreditCard,
  Plus,
  Send,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { useAppDispatch, useAppSelector } from "@/hooks/redux";
import {
  fetchDashboardSummary,
  fetchAccounts,
  fetchCards,
  fetchTransactions,
} from "@/store/walletSlice";
import TransactionList from "./TransactionList";

// ── Skeleton loader ──────────────────────────────────────────────────────────
const StatSkeleton = () => (
  <Card>
    <CardContent className="p-6">
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <Skeleton className="h-3.5 w-24" />
          <Skeleton className="h-7 w-36" />
          <Skeleton className="h-3 w-28" />
        </div>
        <Skeleton className="h-10 w-10 rounded-xl" />
      </div>
    </CardContent>
  </Card>
);

// ── Stat card ────────────────────────────────────────────────────────────────
interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  trend?: "up" | "down" | "neutral";
  icon: React.ElementType;
  iconClass: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  trend,
  icon: Icon,
  iconClass,
}) => (
  <Card className="card-hover overflow-hidden">
    <CardContent className="p-6">
      <div className="flex items-start justify-between">
        <div className="space-y-1.5 min-w-0 pr-3">
          <p className="text-sm font-medium text-muted-foreground truncate">
            {title}
          </p>
          <p className="text-2xl font-bold tabular-nums tracking-tight">
            {value}
          </p>
          {change && (
            <div className="flex items-center gap-1">
              {trend === "up" ? (
                <TrendingUp className="h-3 w-3 text-emerald-500 shrink-0" />
              ) : trend === "down" ? (
                <TrendingDown className="h-3 w-3 text-red-500 shrink-0" />
              ) : null}
              <span
                className={`text-xs font-medium ${trend === "up" ? "text-emerald-600 dark:text-emerald-400" : trend === "down" ? "text-red-600 dark:text-red-400" : "text-muted-foreground"}`}
              >
                {change}
              </span>
            </div>
          )}
        </div>
        <div
          className={`h-11 w-11 rounded-2xl flex items-center justify-center shrink-0 ${iconClass}`}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </CardContent>
  </Card>
);

// ── Quick actions ────────────────────────────────────────────────────────────
const QuickActions: React.FC = () => {
  const navigate = useNavigate();
  const actions = [
    {
      label: "Send Money",
      icon: Send,
      path: "/wallet",
      iconClass: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
    },
    {
      label: "Receive",
      icon: ArrowDownRight,
      path: "/wallet",
      iconClass: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    },
    {
      label: "Cards",
      icon: CreditCard,
      path: "/cards",
      iconClass: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
    },
    {
      label: "Add Funds",
      icon: Plus,
      path: "/wallet",
      iconClass: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
    },
  ];
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2.5">
          {actions.map((a) => {
            const Icon = a.icon;
            return (
              <button
                key={a.label}
                onClick={() => navigate(a.path)}
                className="group flex flex-col items-center gap-2.5 rounded-2xl border border-border p-4 transition-all hover:border-primary/30 hover:bg-accent/40"
              >
                <div
                  className={`h-10 w-10 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110 ${a.iconClass}`}
                >
                  <Icon className="h-4.5 w-4.5" />
                </div>
                <span className="text-xs font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                  {a.label}
                </span>
              </button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

// ── Security card ────────────────────────────────────────────────────────────
const SecurityCard: React.FC = () => {
  const navigate = useNavigate();
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <p className="text-sm font-medium">Security Status</p>
          </div>
          <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border-0 text-xs">
            Secure
          </Badge>
        </div>
        <div className="space-y-2.5">
          {[
            { label: "2FA Authentication", value: "Enabled" },
            { label: "Last login", value: "Just now" },
            { label: "Active sessions", value: "1 device" },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                {item.label}
              </span>
              <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
                {item.value}
              </span>
            </div>
          ))}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full mt-4 h-8 text-xs"
          onClick={() => navigate("/security")}
        >
          Security Settings <ArrowRight className="h-3 w-3 ml-1" />
        </Button>
      </CardContent>
    </Card>
  );
};

// ── Main Dashboard ────────────────────────────────────────────────────────────
const Dashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { accounts, cards, dashboardSummary, transactions, isLoading } =
    useAppSelector((s) => s.wallet);

  useEffect(() => {
    dispatch(fetchDashboardSummary());
    dispatch(fetchAccounts());
    dispatch(fetchCards());
  }, [dispatch]);

  useEffect(() => {
    if (accounts.length > 0) {
      dispatch(
        fetchTransactions({
          accountId: accounts[0].id,
          filters: { per_page: 10 },
        }),
      );
    }
  }, [dispatch, accounts]);

  const totalBalance =
    dashboardSummary?.total_balance ??
    accounts.reduce((s, a) => s + a.balance, 0);
  const monthlyIncome = dashboardSummary?.monthly_income ?? 0;
  const monthlySpend = dashboardSummary?.monthly_spending ?? 0;
  const savingsRate =
    monthlyIncome > 0
      ? (((monthlyIncome - monthlySpend) / monthlyIncome) * 100).toFixed(1)
      : "-";

  const fmt = (n: number) =>
    n.toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    });

  const stats: StatCardProps[] = [
    {
      title: "Total Balance",
      value: fmt(totalBalance),
      change: "Across all accounts",
      trend: "neutral",
      icon: Wallet,
      iconClass: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
    },
    {
      title: "Monthly Income",
      value: fmt(monthlyIncome),
      change: monthlyIncome > 0 ? "This month" : "No data yet",
      trend: "up",
      icon: TrendingUp,
      iconClass: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    },
    {
      title: "Monthly Expenses",
      value: fmt(monthlySpend),
      change: monthlySpend > 0 ? "This month" : "No data yet",
      trend: "down",
      icon: TrendingDown,
      iconClass: "bg-red-500/10 text-red-600 dark:text-red-400",
    },
    {
      title: "Savings Rate",
      value:
        typeof savingsRate === "string" && savingsRate !== "-"
          ? `${savingsRate}%`
          : savingsRate,
      change: `${cards.length} active card${cards.length !== 1 ? "s" : ""}`,
      trend: "up",
      icon: BarChart3,
      iconClass: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
    },
  ];

  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const firstName = user?.firstName ?? "there";

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Page header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {greeting}, {firstName} 👋
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Here's what's happening with your account today.
          </p>
        </div>
        <div className="flex gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate("/wallet")}
          >
            <ArrowDownRight className="h-4 w-4 mr-1.5" /> Receive
          </Button>
          <Button
            size="sm"
            className="bg-gradient-brand hover:opacity-90"
            onClick={() => navigate("/wallet")}
          >
            <Send className="h-4 w-4 mr-1.5" /> Send
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {isLoading && accounts.length === 0
          ? Array.from({ length: 4 }).map((_, i) => <StatSkeleton key={i} />)
          : stats.map((s) => <StatCard key={s.title} {...s} />)}
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Transactions - takes 2 cols */}
        <div className="lg:col-span-2">
          <TransactionList
            transactions={transactions.map((t) => ({
              id: parseInt(t.id.replace(/\D/g, "").slice(0, 9) || "0", 10),
              description: t.description ?? t.type,
              amount: t.type === "deposit" ? t.amount : -Math.abs(t.amount),
              date: t.created_at.slice(0, 10),
              category: t.type,
            }))}
          />
        </div>

        {/* Sidebar cards */}
        <div className="space-y-4">
          <QuickActions />
          <SecurityCard />

          {/* Account summary mini card */}
          {accounts.length > 0 && (
            <Card className="card-hover">
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm font-medium">Accounts</p>
                  <Badge variant="secondary" className="text-xs">
                    {accounts.length}
                  </Badge>
                </div>
                <div className="space-y-3">
                  {accounts.slice(0, 3).map((acc) => (
                    <div
                      key={acc.id}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2.5">
                        <div className="h-7 w-7 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Wallet className="h-3.5 w-3.5 text-primary" />
                        </div>
                        <div>
                          <p className="text-xs font-medium capitalize">
                            {acc.account_type}
                          </p>
                          <p className="text-[10px] text-muted-foreground">
                            {acc.currency}
                          </p>
                        </div>
                      </div>
                      <p className="text-xs font-semibold tabular-nums">
                        {fmt(acc.balance)}
                      </p>
                    </div>
                  ))}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mt-3 h-8 text-xs"
                  onClick={() => navigate("/wallet")}
                >
                  View all accounts <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
