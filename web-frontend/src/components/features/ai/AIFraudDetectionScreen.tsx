import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle,
  Clock,
  Eye,
  Filter,
  RefreshCw,
  Shield,
  TrendingDown,
  TrendingUp,
  XCircle,
  Zap,
} from "lucide-react";
import React, { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  PieChart,
  Pie,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// ── Deterministic data helpers ──────────────────────────────────────────────

function seededRng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
}

function generateHourlyDetections() {
  const rng = seededRng(42);
  return Array.from({ length: 24 }, (_, h) => ({
    hour: `${String(h).padStart(2, "0")}:00`,
    blocked: Math.floor(rng() * 12 + 1),
    reviewed: Math.floor(rng() * 8 + 1),
    cleared: Math.floor(rng() * 40 + 20),
  }));
}

function generateDailyTrend() {
  const rng = seededRng(99);
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  return days.map((d) => ({
    day: d,
    fraudRate: parseFloat((rng() * 1.4 + 0.2).toFixed(2)),
    volume: Math.floor(rng() * 8000 + 2000),
  }));
}

function generateModelMetrics() {
  return [
    {
      model: "Random Forest",
      auc: 0.974,
      precision: 0.961,
      recall: 0.948,
      f1: 0.954,
      latency: 4,
    },
    {
      model: "XGBoost",
      auc: 0.981,
      precision: 0.967,
      recall: 0.953,
      f1: 0.96,
      latency: 3,
    },
    {
      model: "LightGBM",
      auc: 0.978,
      precision: 0.963,
      recall: 0.95,
      f1: 0.956,
      latency: 2,
    },
    {
      model: "Neural Network",
      auc: 0.969,
      precision: 0.944,
      recall: 0.937,
      f1: 0.94,
      latency: 18,
    },
    {
      model: "Ensemble",
      auc: 0.987,
      precision: 0.973,
      recall: 0.961,
      f1: 0.967,
      latency: 8,
    },
  ];
}

function generateRecentAlerts() {
  const rng = seededRng(77);
  const types = [
    "Velocity Spike",
    "Geo Anomaly",
    "Card Not Present",
    "Night-time Auth",
    "Device Change",
    "High-Value Transfer",
  ];
  const statuses = ["blocked", "reviewed", "cleared"] as const;
  const tickers = ["AAPL-4829", "VISA-3901", "MC-7812", "AMEX-6011"];
  return Array.from({ length: 12 }, (_, i) => ({
    id: `ALT-${String(i + 1).padStart(4, "0")}`,
    type: types[Math.floor(rng() * types.length)],
    amount: parseFloat((rng() * 4800 + 50).toFixed(2)),
    status: statuses[Math.floor(rng() * statuses.length)],
    riskScore: Math.floor(rng() * 35 + 65),
    card: tickers[Math.floor(rng() * tickers.length)],
    time: `${String(Math.floor(rng() * 23)).padStart(2, "0")}:${String(Math.floor(rng() * 59)).padStart(2, "0")}`,
  }));
}

function generateRiskRadar() {
  return [
    { subject: "Velocity", score: 72 },
    { subject: "Geo Risk", score: 38 },
    { subject: "Device Trust", score: 85 },
    { subject: "Behaviour", score: 61 },
    { subject: "Merchant Risk", score: 44 },
    { subject: "Time Pattern", score: 57 },
  ];
}

function generateConfusionMatrix() {
  return { tp: 2847, fp: 82, fn: 118, tn: 97953 };
}

// ── Sub-components ──────────────────────────────────────────────────────────

const STATUS_BADGE: Record<string, React.ReactElement> = {
  blocked: (
    <Badge className="bg-red-100 text-red-700 border-red-200">Blocked</Badge>
  ),
  reviewed: (
    <Badge className="bg-yellow-100 text-yellow-700 border-yellow-200">
      Review
    </Badge>
  ),
  cleared: (
    <Badge className="bg-green-100 text-green-700 border-green-200">
      Cleared
    </Badge>
  ),
};

function KpiCard({
  title,
  value,
  sub,
  icon: Icon,
  trend,
  color = "text-gray-900",
}: {
  title: string;
  value: string;
  sub: string;
  icon: React.ElementType;
  trend?: "up" | "down" | "neutral";
  color?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-500">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${color}`}>{value}</div>
        <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
          {trend === "up" && <TrendingUp className="h-3 w-3 text-green-500" />}
          {trend === "down" && (
            <TrendingDown className="h-3 w-3 text-red-500" />
          )}
          {sub}
        </p>
      </CardContent>
    </Card>
  );
}

// ── Main component ──────────────────────────────────────────────────────────

export default function AIFraudDetectionScreen() {
  const [timeRange, setTimeRange] = useState("24h");
  const [modelFilter, setModelFilter] = useState("ensemble");

  const hourly = useMemo(() => generateHourlyDetections(), []);
  const daily = useMemo(() => generateDailyTrend(), []);
  const models = useMemo(() => generateModelMetrics(), []);
  const alerts = useMemo(() => generateRecentAlerts(), []);
  const radar = useMemo(() => generateRiskRadar(), []);
  const cm = useMemo(() => generateConfusionMatrix(), []);

  const precision = ((cm.tp / (cm.tp + cm.fp)) * 100).toFixed(1);
  const recall = ((cm.tp / (cm.tp + cm.fn)) * 100).toFixed(1);
  const f1 = (((2 * cm.tp) / (2 * cm.tp + cm.fp + cm.fn)) * 100).toFixed(1);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">AI Fraud Detection</h1>
          <p className="text-muted-foreground mt-1">
            Real-time ML-powered transaction monitoring · Ensemble model active
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-28">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">Last 1h</SelectItem>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7d</SelectItem>
              <SelectItem value="30d">Last 30d</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh
          </Button>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <KpiCard
          title="Threats Blocked"
          value="159"
          sub="+12% vs yesterday"
          icon={Shield}
          trend="up"
          color="text-red-600"
        />
        <KpiCard
          title="Under Review"
          value="47"
          sub="Avg resolution 4.2 min"
          icon={Eye}
          trend="neutral"
          color="text-yellow-600"
        />
        <KpiCard
          title="Transactions Analysed"
          value="98,234"
          sub="+8% volume"
          icon={Activity}
          trend="up"
        />
        <KpiCard
          title="Detection Accuracy"
          value="98.7%"
          sub="Ensemble model (F1 = 0.967)"
          icon={TrendingUp}
          trend="up"
          color="text-green-700"
        />
        <KpiCard
          title="Avg Latency"
          value="8 ms"
          sub="p99 = 22 ms"
          icon={Zap}
        />
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="models">ML Models</TabsTrigger>
          <TabsTrigger value="alerts">Alert Log</TabsTrigger>
          <TabsTrigger value="risk">Risk Radar</TabsTrigger>
        </TabsList>

        {/* ── Overview ── */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Hourly detections */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                  Hourly Decision Breakdown
                </CardTitle>
                <CardDescription>
                  Blocked · Under review · Cleared
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={hourly}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" tick={{ fontSize: 9 }} interval={3} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Bar
                      dataKey="blocked"
                      name="Blocked"
                      stackId="a"
                      fill="#ef4444"
                      radius={[0, 0, 0, 0]}
                    />
                    <Bar
                      dataKey="reviewed"
                      name="Reviewed"
                      stackId="a"
                      fill="#f59e0b"
                    />
                    <Bar
                      dataKey="cleared"
                      name="Cleared"
                      stackId="a"
                      fill="#10b981"
                      radius={[3, 3, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Daily fraud rate trend */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                  Daily Fraud Rate (%)
                </CardTitle>
                <CardDescription>vs. transaction volume</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={daily}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                    <YAxis
                      yAxisId="left"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) => `${v}%`}
                    />
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                    />
                    <Tooltip />
                    <Legend />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="fraudRate"
                      name="Fraud Rate %"
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                    <Bar
                      yAxisId="right"
                      dataKey="volume"
                      name="Volume"
                      fill="#e0e7ff"
                      radius={[2, 2, 0, 0]}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Confusion matrix */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                Confusion Matrix - Ensemble Model (last 100k transactions)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
                {[
                  {
                    label: "True Positives",
                    value: cm.tp.toLocaleString(),
                    color: "bg-green-50 border-green-200 text-green-800",
                    sub: "Fraud correctly caught",
                  },
                  {
                    label: "False Positives",
                    value: cm.fp.toLocaleString(),
                    color: "bg-orange-50 border-orange-200 text-orange-800",
                    sub: "Legit flagged as fraud",
                  },
                  {
                    label: "False Negatives",
                    value: cm.fn.toLocaleString(),
                    color: "bg-red-50 border-red-200 text-red-800",
                    sub: "Fraud missed",
                  },
                  {
                    label: "True Negatives",
                    value: cm.tn.toLocaleString(),
                    color: "bg-blue-50 border-blue-200 text-blue-800",
                    sub: "Legit correctly passed",
                  },
                ].map((c) => (
                  <div
                    key={c.label}
                    className={`rounded-lg border p-4 text-center ${c.color}`}
                  >
                    <p className="text-xs font-medium">{c.label}</p>
                    <p className="text-2xl font-bold mt-1">{c.value}</p>
                    <p className="text-xs mt-1 opacity-70">{c.sub}</p>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-4">
                {[
                  {
                    label: "Precision",
                    value: `${precision}%`,
                    hint: "TP / (TP + FP)",
                  },
                  {
                    label: "Recall",
                    value: `${recall}%`,
                    hint: "TP / (TP + FN)",
                  },
                  {
                    label: "F1 Score",
                    value: `${f1}%`,
                    hint: "Harmonic mean of P & R",
                  },
                ].map((m) => (
                  <div
                    key={m.label}
                    className="bg-gray-50 rounded-lg p-3 text-center"
                  >
                    <p className="text-xs text-gray-500">{m.label}</p>
                    <p className="text-xl font-bold text-blue-700">{m.value}</p>
                    <p className="text-xs text-gray-400">{m.hint}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── ML Models ── */}
        <TabsContent value="models" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                Model Performance Comparison
              </CardTitle>
              <CardDescription>
                AUC-ROC, Precision, Recall, F1, and inference latency
              </CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50">
                    {[
                      "Model",
                      "AUC-ROC",
                      "Precision",
                      "Recall",
                      "F1",
                      "Latency (ms)",
                      "Status",
                    ].map((h) => (
                      <th
                        key={h}
                        className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {models.map((m) => (
                    <tr
                      key={m.model}
                      className={`hover:bg-gray-50 ${m.model === "Ensemble" ? "font-semibold bg-blue-50" : ""}`}
                    >
                      <td className="px-4 py-3">{m.model}</td>
                      <td className="px-4 py-3 text-blue-700">
                        {m.auc.toFixed(3)}
                      </td>
                      <td className="px-4 py-3">
                        {(m.precision * 100).toFixed(1)}%
                      </td>
                      <td className="px-4 py-3">
                        {(m.recall * 100).toFixed(1)}%
                      </td>
                      <td className="px-4 py-3">{(m.f1 * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3">{m.latency} ms</td>
                      <td className="px-4 py-3">
                        <Badge
                          className={
                            m.model === "Ensemble"
                              ? "bg-green-100 text-green-700"
                              : "bg-gray-100 text-gray-600"
                          }
                        >
                          {m.model === "Ensemble" ? "Active" : "Standby"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                AUC-ROC Comparison
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={models} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis
                    type="number"
                    domain={[0.95, 1.0]}
                    tickFormatter={(v) => v.toFixed(3)}
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis
                    type="category"
                    dataKey="model"
                    width={120}
                    tick={{ fontSize: 11 }}
                  />
                  <Tooltip
                    formatter={(v) => [Number(v).toFixed(3), "AUC-ROC"]}
                  />
                  <Bar dataKey="auc" radius={[0, 4, 4, 0]}>
                    {models.map((m, i) => (
                      <Cell
                        key={i}
                        fill={m.model === "Ensemble" ? "#2563eb" : "#93c5fd"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { label: "Detection Rules Active", value: "247", icon: Filter },
              { label: "Models in Production", value: "5", icon: BarChart3 },
              { label: "Last Retrain", value: "6 hrs ago", icon: Clock },
            ].map((s) => (
              <Card key={s.label}>
                <CardContent className="pt-6 flex items-center gap-4">
                  <s.icon className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className="text-xs text-gray-500">{s.label}</p>
                    <p className="text-xl font-bold">{s.value}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* ── Alert Log ── */}
        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                  Recent Fraud Alerts
                </CardTitle>
                <Button variant="outline" size="sm">
                  <Filter className="h-3 w-3 mr-1" /> Filter
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm divide-y divide-gray-100">
                  <thead className="bg-gray-50">
                    <tr>
                      {[
                        "Alert ID",
                        "Type",
                        "Card",
                        "Amount",
                        "Risk Score",
                        "Time",
                        "Status",
                        "Action",
                      ].map((h) => (
                        <th
                          key={h}
                          className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-100">
                    {alerts.map((a) => (
                      <tr key={a.id} className="hover:bg-gray-50">
                        <td className="px-4 py-2.5 font-mono text-xs text-gray-500">
                          {a.id}
                        </td>
                        <td className="px-4 py-2.5 font-medium">{a.type}</td>
                        <td className="px-4 py-2.5 font-mono text-xs">
                          {a.card}
                        </td>
                        <td className="px-4 py-2.5">${a.amount.toFixed(2)}</td>
                        <td className="px-4 py-2.5">
                          <span
                            className={`font-semibold ${a.riskScore >= 85 ? "text-red-600" : a.riskScore >= 70 ? "text-yellow-600" : "text-gray-700"}`}
                          >
                            {a.riskScore}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-gray-500">{a.time}</td>
                        <td className="px-4 py-2.5">
                          {STATUS_BADGE[a.status]}
                        </td>
                        <td className="px-4 py-2.5">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs h-7"
                          >
                            View
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Risk Radar ── */}
        <TabsContent value="risk" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                  Risk Dimension Radar
                </CardTitle>
                <CardDescription>
                  Current risk scores across 6 signal dimensions (0–100)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radar}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
                    <PolarRadiusAxis
                      angle={90}
                      domain={[0, 100]}
                      tick={false}
                    />
                    <Radar
                      name="Risk Score"
                      dataKey="score"
                      stroke="#2563eb"
                      fill="#2563eb"
                      fillOpacity={0.25}
                    />
                    <Tooltip formatter={(v) => [`${v}/100`, "Risk Score"]} />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                  Risk Factor Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {radar.map((r) => (
                    <div key={r.subject}>
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span className="font-medium">{r.subject}</span>
                        <span
                          className={
                            r.score >= 70
                              ? "text-red-600 font-semibold"
                              : r.score >= 50
                                ? "text-yellow-600"
                                : "text-green-600"
                          }
                        >
                          {r.score}/100
                        </span>
                      </div>
                      <div className="h-2.5 w-full bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${r.score}%`,
                            background:
                              r.score >= 70
                                ? "#ef4444"
                                : r.score >= 50
                                  ? "#f59e0b"
                                  : "#10b981",
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-400 mt-4">
                  🟢 Low (&lt;50) · 🟡 Medium (50–70) · 🔴 High (&gt;70). Scores
                  updated in real-time by the ensemble model.
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
