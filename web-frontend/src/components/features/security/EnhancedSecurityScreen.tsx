import {
  Activity,
  AlertCircle,
  Bell,
  CheckCircle,
  Clock,
  Globe,
  Key,
  Lock,
  RefreshCw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Smartphone,
  Users,
  XCircle,
} from "lucide-react";
import React, { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
  Bar,
  Cell,
  LineChart,
  Line,
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
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// ── Deterministic data ───────────────────────────────────────────────────────

function seededRng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
}

function generateLoginHistory() {
  const rng = seededRng(13);
  const devices = [
    "Chrome · macOS",
    "Safari · iOS",
    "Firefox · Windows",
    "Chrome · Android",
  ];
  const locs = [
    "New York, US",
    "London, UK",
    "San Francisco, US",
    "Remote / VPN",
  ];
  return Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    device: devices[Math.floor(rng() * devices.length)],
    location: locs[Math.floor(rng() * locs.length)],
    ip: `${Math.floor(rng() * 200 + 50)}.${Math.floor(rng() * 255)}.${Math.floor(rng() * 255)}.${Math.floor(rng() * 255)}`,
    time: `${String(Math.floor(rng() * 23)).padStart(2, "0")}:${String(Math.floor(rng() * 59)).padStart(2, "0")} UTC`,
    status: rng() > 0.15 ? "success" : "failed",
    mfa: rng() > 0.3 ? "TOTP" : "SMS",
  }));
}

function generateAuthAttempts() {
  const rng = seededRng(55);
  return Array.from({ length: 14 }, (_, i) => ({
    day: `Day ${i + 1}`,
    success: Math.floor(rng() * 300 + 100),
    failed: Math.floor(rng() * 20),
    blocked: Math.floor(rng() * 8),
  }));
}

function generateActiveSessions() {
  return [
    {
      id: "S-001",
      device: "Chrome · macOS 14",
      location: "New York, US",
      ip: "203.0.113.42",
      since: "2h 14m",
      current: true,
    },
    {
      id: "S-002",
      device: "Safari · iOS 17",
      location: "London, UK",
      ip: "198.51.100.8",
      since: "5h 02m",
      current: false,
    },
    {
      id: "S-003",
      device: "Mobile App · Android 14",
      location: "San Francisco, US",
      ip: "192.0.2.17",
      since: "1d 3h",
      current: false,
    },
  ];
}

function generateComplianceChecks() {
  return [
    {
      label: "Multi-Factor Authentication",
      status: "pass",
      detail: "TOTP + SMS enabled",
    },
    {
      label: "Password Strength Policy",
      status: "pass",
      detail: "Min 12 chars, complexity enforced",
    },
    {
      label: "Session Timeout",
      status: "pass",
      detail: "30-min idle timeout active",
    },
    {
      label: "IP Allowlist",
      status: "warn",
      detail: "Not configured - consider enabling",
    },
    {
      label: "API Key Rotation",
      status: "pass",
      detail: "Last rotated 14 days ago",
    },
    {
      label: "Audit Log Retention",
      status: "pass",
      detail: "90-day retention active",
    },
    {
      label: "Encryption at Rest",
      status: "pass",
      detail: "AES-256 on all PII fields",
    },
    { label: "TLS Version", status: "pass", detail: "TLS 1.3 only" },
    { label: "Rate Limiting", status: "pass", detail: "100 req/min per IP" },
    {
      label: "Biometric Auth",
      status: "warn",
      detail: "Available but not enforced",
    },
  ];
}

// ── KPI card ─────────────────────────────────────────────────────────────────

function Kpi({
  title,
  value,
  sub,
  icon: Icon,
  color = "text-gray-900",
}: {
  title: string;
  value: string;
  sub: string;
  icon: React.ElementType;
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
        <p className="text-xs text-muted-foreground mt-1">{sub}</p>
      </CardContent>
    </Card>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────

export default function EnhancedSecurityScreen() {
  const [settings, setSettings] = useState({
    mfa: true,
    biometric: false,
    sessionAlerts: true,
    ipAllowlist: false,
    apiKeyRotation: true,
    auditLog: true,
  });

  const logins = useMemo(() => generateLoginHistory(), []);
  const attempts = useMemo(() => generateAuthAttempts(), []);
  const sessions = useMemo(() => generateActiveSessions(), []);
  const compliance = useMemo(() => generateComplianceChecks(), []);

  const toggle = (key: keyof typeof settings) =>
    setSettings((p) => ({ ...p, [key]: !p[key] }));

  const passCount = compliance.filter((c) => c.status === "pass").length;
  const warnCount = compliance.filter((c) => c.status === "warn").length;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Advanced Security</h1>
          <p className="text-muted-foreground mt-1">
            Enterprise-grade security monitoring, sessions, and compliance
          </p>
        </div>
        <Button variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-1" /> Refresh
        </Button>
      </div>

      {/* KPIs */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Kpi
          title="Threat Level"
          value="Low"
          sub="No active incidents"
          icon={Shield}
          color="text-green-700"
        />
        <Kpi
          title="Active Sessions"
          value={String(sessions.length)}
          sub="Across 3 devices"
          icon={Activity}
        />
        <Kpi
          title="Failed Auth (24h)"
          value="12"
          sub="+3 from yesterday"
          icon={Lock}
          color="text-orange-600"
        />
        <Kpi
          title="Compliance Score"
          value={`${passCount}/${compliance.length}`}
          sub={`${warnCount} warning${warnCount !== 1 ? "s" : ""}`}
          icon={ShieldCheck}
          color="text-blue-700"
        />
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sessions">Sessions</TabsTrigger>
          <TabsTrigger value="policies">Policies</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
        </TabsList>

        {/* ── Overview ── */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                  Authentication Attempts (14 days)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={attempts}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" tick={{ fontSize: 9 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar
                      dataKey="success"
                      name="Success"
                      stackId="a"
                      fill="#10b981"
                      radius={[0, 0, 0, 0]}
                    />
                    <Bar
                      dataKey="failed"
                      name="Failed"
                      stackId="a"
                      fill="#f59e0b"
                    />
                    <Bar
                      dataKey="blocked"
                      name="Blocked"
                      stackId="a"
                      fill="#ef4444"
                      radius={[3, 3, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                  Recent Login History
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {logins.map((l) => (
                    <div
                      key={l.id}
                      className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
                    >
                      <div className="flex items-center gap-3">
                        {l.status === "success" ? (
                          <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
                        )}
                        <div>
                          <p className="text-xs font-medium">{l.device}</p>
                          <p className="text-xs text-gray-400">
                            {l.location} · {l.ip}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">{l.time}</p>
                        <Badge className="text-xs mt-0.5 bg-blue-50 text-blue-700">
                          {l.mfa}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── Sessions ── */}
        <TabsContent value="sessions">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                  Active Sessions
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-red-600 border-red-200 hover:bg-red-50"
                >
                  Revoke All Others
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {sessions.map((s) => (
                  <div
                    key={s.id}
                    className={`flex items-center justify-between p-4 rounded-lg border ${s.current ? "border-blue-200 bg-blue-50" : "border-gray-200"}`}
                  >
                    <div className="flex items-center gap-4">
                      <Smartphone className="h-5 w-5 text-gray-500" />
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium">{s.device}</p>
                          {s.current && (
                            <Badge className="bg-green-100 text-green-700 text-xs">
                              Current
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5">
                          <Globe className="h-3 w-3 inline mr-1" />
                          {s.location} · {s.ip}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p className="text-xs text-gray-500">Active for</p>
                        <p className="text-sm font-medium">{s.since}</p>
                      </div>
                      {!s.current && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-500 hover:text-red-700 text-xs"
                        >
                          Revoke
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Policies ── */}
        <TabsContent value="policies">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                Security Policy Configuration
              </CardTitle>
              <CardDescription>
                Toggle enterprise security features
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {[
                {
                  key: "mfa" as const,
                  label: "Multi-Factor Authentication",
                  sub: "Require TOTP or SMS for every login",
                  icon: Key,
                },
                {
                  key: "biometric" as const,
                  label: "Biometric Authentication",
                  sub: "Allow fingerprint / Face ID on mobile",
                  icon: Smartphone,
                },
                {
                  key: "sessionAlerts" as const,
                  label: "New Session Alerts",
                  sub: "Email notification on each new login",
                  icon: Bell,
                },
                {
                  key: "ipAllowlist" as const,
                  label: "IP Allowlist",
                  sub: "Restrict access to specific IP ranges",
                  icon: Globe,
                },
                {
                  key: "apiKeyRotation" as const,
                  label: "Automatic API Key Rotation",
                  sub: "Rotate API keys every 30 days",
                  icon: RefreshCw,
                },
                {
                  key: "auditLog" as const,
                  label: "Extended Audit Logging",
                  sub: "90-day retention of all security events",
                  icon: Activity,
                },
              ].map(({ key, label, sub, icon: Icon }) => (
                <div
                  key={key}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <Icon className="h-5 w-5 text-gray-500" />
                    <div>
                      <Label className="text-sm font-medium cursor-pointer">
                        {label}
                      </Label>
                      <p className="text-xs text-gray-400">{sub}</p>
                    </div>
                  </div>
                  <Switch
                    checked={settings[key]}
                    onCheckedChange={() => toggle(key)}
                  />
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Compliance ── */}
        <TabsContent value="compliance">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                    Security Compliance Checklist
                  </CardTitle>
                  <CardDescription>
                    {passCount} passed · {warnCount} warnings · 0 failures
                  </CardDescription>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-blue-700">
                    {Math.round((passCount / compliance.length) * 100)}%
                  </p>
                  <p className="text-xs text-gray-400">compliance score</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {compliance.map((c) => (
                  <div
                    key={c.label}
                    className={`flex items-center justify-between p-3 rounded-lg border ${c.status === "pass" ? "border-green-100 bg-green-50" : "border-yellow-100 bg-yellow-50"}`}
                  >
                    <div className="flex items-center gap-3">
                      {c.status === "pass" ? (
                        <ShieldCheck className="h-4 w-4 text-green-600 flex-shrink-0" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-600 flex-shrink-0" />
                      )}
                      <div>
                        <p className="text-sm font-medium">{c.label}</p>
                        <p className="text-xs text-gray-500">{c.detail}</p>
                      </div>
                    </div>
                    <Badge
                      className={
                        c.status === "pass"
                          ? "bg-green-100 text-green-700"
                          : "bg-yellow-100 text-yellow-700"
                      }
                    >
                      {c.status === "pass" ? "Pass" : "Warning"}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
