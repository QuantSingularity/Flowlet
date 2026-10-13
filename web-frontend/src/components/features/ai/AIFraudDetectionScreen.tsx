import {
  Activity,
  AlertTriangle,
  RefreshCw,
  Shield,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";
import React, { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { describeError, useAsyncData } from "@/hooks/useAsyncData";
import {
  mlService,
  type FraudAnalysis,
  type RiskLevel,
} from "@/lib/api/mlService";

const LEVEL_COLORS: Record<RiskLevel, string> = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#f97316",
  critical: "#ef4444",
};

const CATEGORY_OPTIONS = [
  "grocery",
  "restaurant",
  "retail",
  "travel",
  "utilities",
  "gambling",
  "cryptocurrency",
  "wire_transfer",
  "cash_advance",
];

const money = (value: number) =>
  value.toLocaleString(undefined, { style: "currency", currency: "USD" });

const label = (key: string) => key.replace(/_/g, " ");

function KpiCard({
  title,
  value,
  hint,
  icon: Icon,
  trend,
}: {
  title: string;
  value: string;
  hint?: string;
  icon: React.ElementType;
  trend?: "up" | "down";
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold tabular-nums">{value}</p>
        {hint && (
          <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
            {trend === "up" && (
              <TrendingUp className="h-3 w-3 text-amber-500" />
            )}
            {trend === "down" && (
              <TrendingDown className="h-3 w-3 text-emerald-500" />
            )}
            {hint}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function ErrorPanel({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <Card>
      <CardContent className="py-8 text-center space-y-3">
        <p className="text-sm text-destructive">{message}</p>
        <Button size="sm" variant="outline" onClick={onRetry}>
          Try again
        </Button>
      </CardContent>
    </Card>
  );
}

function Loading() {
  return (
    <p className="text-sm text-muted-foreground py-8 text-center">Loading...</p>
  );
}

function ScreeningPanel() {
  const [amount, setAmount] = useState("250");
  const [category, setCategory] = useState("retail");
  const [country, setCountry] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<FraudAnalysis | null>(null);

  const submit = async () => {
    const parsed = Number(amount);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      toast.error("Enter a positive amount");
      return;
    }
    setBusy(true);
    try {
      const analysis = await mlService.screenTransaction({
        amount: parsed,
        merchant_info: {
          category,
          location: country.trim().toUpperCase() || undefined,
        },
      });
      setResult(analysis);
    } catch (err) {
      toast.error(describeError(err));
    } finally {
      setBusy(false);
    }
  };

  const outcome = result?.fraud_analysis;
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Screen a transaction</CardTitle>
          <CardDescription>
            Scores the transaction against your history. Flagged results are
            logged as alerts.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium" htmlFor="screen-amount">
              Amount (USD)
            </label>
            <Input
              id="screen-amount"
              inputMode="decimal"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium">Merchant category</label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CATEGORY_OPTIONS.map((option) => (
                  <SelectItem key={option} value={option}>
                    {label(option)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium" htmlFor="screen-country">
              Country code (optional)
            </label>
            <Input
              id="screen-country"
              maxLength={2}
              placeholder="US"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
            />
          </div>
          <Button
            onClick={() => void submit()}
            disabled={busy}
            className="w-full gap-2"
          >
            <Zap className="h-4 w-4" />
            {busy ? "Scoring..." : "Run fraud check"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Result</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!outcome && (
            <p className="text-sm text-muted-foreground">
              Run a check to see the decision.
            </p>
          )}
          {outcome && result && (
            <>
              <div className="flex items-center gap-3">
                <p className="text-3xl font-bold tabular-nums">
                  {Math.round(outcome.risk_score)}
                </p>
                <Badge
                  style={{
                    backgroundColor: LEVEL_COLORS[outcome.risk_level],
                    color: "white",
                  }}
                >
                  {outcome.risk_level}
                </Badge>
                <Badge variant="outline">
                  {label(outcome.recommended_action)}
                </Badge>
              </div>
              <p className="text-sm">{outcome.explanation.summary}</p>
              {outcome.explanation.rule_hits.length > 0 && (
                <div>
                  <p className="text-xs font-semibold mb-1">Rules triggered</p>
                  <ul className="text-xs text-muted-foreground list-disc pl-4 space-y-0.5">
                    {outcome.explanation.rule_hits.map((hit) => (
                      <li key={hit.name}>{hit.description}</li>
                    ))}
                  </ul>
                </div>
              )}
              {outcome.explanation.primary_risk_factors.length > 0 && (
                <div>
                  <p className="text-xs font-semibold mb-1">Model factors</p>
                  <ul className="text-xs text-muted-foreground list-disc pl-4 space-y-0.5">
                    {outcome.explanation.primary_risk_factors.map((factor) => (
                      <li key={factor.feature}>{factor.description}</li>
                    ))}
                  </ul>
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                Confidence {Math.round(outcome.confidence)}% - mode{" "}
                {result.mode === "model" ? "ML ensemble" : "rules only"}
                {result.alert_created ? " - alert logged" : ""}
              </p>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function RiskPanel() {
  const { data, loading, error, reload } = useAsyncData(
    () => mlService.assessRisk(),
    [],
  );
  if (loading && !data) return <Loading />;
  if (error)
    return <ErrorPanel message={error} onRetry={() => void reload()} />;
  const assessment = data?.assessment;
  if (!assessment) return null;
  const radar = Object.entries(assessment.category_scores).map(
    ([name, score]) => ({
      category: label(name.replace("_risk", "")),
      score: Math.round(score * 100),
    }),
  );
  const factors = [...assessment.risk_factors]
    .sort((a, b) => b.score - a.score)
    .slice(0, 6);

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Risk profile</CardTitle>
          <CardDescription>
            Overall {Math.round(assessment.overall_risk_score * 100)} (
            {label(assessment.overall_risk_level)}), confidence{" "}
            {Math.round(assessment.confidence_score * 100)}%
          </CardDescription>
        </CardHeader>
        <CardContent className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radar}>
              <PolarGrid />
              <PolarAngleAxis dataKey="category" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Radar
                dataKey="score"
                stroke="#6366f1"
                fill="#6366f1"
                fillOpacity={0.35}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top factors</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {factors.map((factor) => (
              <div key={factor.factor_name}>
                <div className="flex justify-between text-xs">
                  <span className="font-medium">
                    {label(factor.factor_name)}
                  </span>
                  <span className="tabular-nums">
                    {Math.round(factor.score * 100)}
                  </span>
                </div>
                <div className="h-1.5 rounded bg-muted mt-1">
                  <div
                    className="h-1.5 rounded bg-primary"
                    style={{ width: `${Math.round(factor.score * 100)}%` }}
                  />
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  {factor.description}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="text-sm list-disc pl-4 space-y-1">
              {assessment.recommendations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            {assessment.monitoring_alerts.length > 0 && (
              <div className="mt-3 flex items-start gap-2 text-xs text-amber-600">
                <AlertTriangle className="h-3.5 w-3.5 mt-0.5" />
                <span>{assessment.monitoring_alerts.join("; ")}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function SpendingPanel() {
  const { data, loading, error, reload } = useAsyncData(
    () => mlService.spendingAnalysis(90),
    [],
  );
  if (loading && !data) return <Loading />;
  if (error)
    return <ErrorPanel message={error} onRetry={() => void reload()} />;
  const analysis = data?.analysis;
  if (!analysis) return null;
  const categories = Object.entries(analysis.category_totals).map(
    ([name, value]) => ({
      name: label(name),
      value: Math.round(value * 100) / 100,
    }),
  );

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Spent (90 days)"
          value={money(analysis.total_spent)}
          icon={Activity}
        />
        <KpiCard
          title="Income"
          value={money(analysis.total_income)}
          icon={TrendingUp}
        />
        <KpiCard
          title="Net cash flow"
          value={money(analysis.net_cash_flow)}
          icon={Shield}
          trend={analysis.net_cash_flow < 0 ? "up" : "down"}
          hint={
            analysis.net_cash_flow < 0
              ? "Spending exceeds income"
              : "Positive cash flow"
          }
        />
        <KpiCard
          title="30 day forecast"
          value={
            analysis.forecast.projected_spend === null
              ? "Not enough data"
              : money(analysis.forecast.projected_spend)
          }
          icon={Zap}
          hint={`Pattern: ${analysis.pattern}`}
        />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Spending by category</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            {categories.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No spending in this period.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={categories}
                  layout="vertical"
                  margin={{ left: 40 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis
                    dataKey="name"
                    type="category"
                    tick={{ fontSize: 11 }}
                    width={90}
                  />
                  <Tooltip formatter={(v: number) => money(v)} />
                  <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Insights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <ul className="text-sm list-disc pl-4 space-y-1">
              {analysis.insights.map((item) => (
                <li key={item}>{item}</li>
              ))}
              {analysis.insights.length === 0 && (
                <li className="list-none text-muted-foreground">
                  No insights yet.
                </li>
              )}
            </ul>
            {analysis.recurring.length > 0 && (
              <div>
                <p className="text-xs font-semibold mb-1">Recurring payments</p>
                <ul className="text-xs text-muted-foreground space-y-0.5">
                  {analysis.recurring.slice(0, 5).map((item) => (
                    <li key={item.merchant}>
                      {item.merchant}: {money(item.average_amount)} every{" "}
                      {item.period_days} days
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {analysis.alerts.map((alert) => (
              <p
                key={alert}
                className="text-xs text-amber-600 flex items-center gap-1.5"
              >
                <AlertTriangle className="h-3.5 w-3.5" />
                {alert}
              </p>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function OperationsPanel() {
  const { data, loading, error, reload } = useAsyncData(
    () => mlService.fraudStatistics(24),
    [],
  );
  if (loading && !data) return <Loading />;
  if (error)
    return <ErrorPanel message={error} onRetry={() => void reload()} />;
  const stats = data?.statistics;
  if (!stats) return null;
  const distribution = (Object.keys(LEVEL_COLORS) as RiskLevel[]).map(
    (level) => ({
      name: level,
      value: stats.risk_distribution[level] ?? 0,
    }),
  );

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <KpiCard
          title="Scored (24h)"
          value={String(stats.total_transactions)}
          icon={Activity}
        />
        <KpiCard
          title="Flagged"
          value={String(stats.fraud_detected)}
          icon={AlertTriangle}
        />
        <KpiCard
          title="Average risk score"
          value={`${Math.round(stats.average_risk_score * 100)}`}
          icon={Shield}
          hint={`Flag rate ${(stats.fraud_rate * 100).toFixed(1)}%`}
        />
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Risk distribution</CardTitle>
        </CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={distribution}
                dataKey="value"
                nameKey="name"
                outerRadius={90}
                label
              >
                {distribution.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={LEVEL_COLORS[entry.name as RiskLevel]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}

export default function AIFraudDetectionScreen() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const health = useAsyncData(() => mlService.health(), []);
  const mode = health.data?.fraud_detection?.mode;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            AI Fraud Detection
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Live risk scoring, spending intelligence and account risk
          </p>
        </div>
        <div className="flex items-center gap-2">
          {mode && (
            <Badge variant={mode === "model" ? "default" : "secondary"}>
              {mode === "model" ? "ML ensemble active" : "Rules only"}
            </Badge>
          )}
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => void health.reload()}
          >
            <RefreshCw
              className={cn("h-4 w-4", health.loading && "animate-spin")}
            />
            Refresh
          </Button>
        </div>
      </div>

      <Tabs defaultValue="screening">
        <TabsList>
          <TabsTrigger value="screening">Screening</TabsTrigger>
          <TabsTrigger value="spending">Spending</TabsTrigger>
          <TabsTrigger value="risk">Risk Profile</TabsTrigger>
          {isAdmin && <TabsTrigger value="operations">Operations</TabsTrigger>}
        </TabsList>
        <TabsContent value="screening" className="mt-4">
          <ScreeningPanel />
        </TabsContent>
        <TabsContent value="spending" className="mt-4">
          <SpendingPanel />
        </TabsContent>
        <TabsContent value="risk" className="mt-4">
          <RiskPanel />
        </TabsContent>
        {isAdmin && (
          <TabsContent value="operations" className="mt-4">
            <OperationsPanel />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
