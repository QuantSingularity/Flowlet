import {
  AlertTriangle,
  CheckCircle,
  Key,
  Lock,
  Monitor,
  Shield,
  Smartphone,
  XCircle,
} from "lucide-react";
import React from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const SECURITY_CHECKS = [
  {
    id: "2fa",
    label: "Two-Factor Authentication",
    status: "enabled" as const,
    impact: "high",
  },
  {
    id: "email",
    label: "Email Verified",
    status: "enabled" as const,
    impact: "high",
  },
  {
    id: "phone",
    label: "Phone Verified",
    status: "disabled" as const,
    impact: "medium",
  },
  {
    id: "biometric",
    label: "Biometric Login",
    status: "disabled" as const,
    impact: "medium",
  },
  {
    id: "passkey",
    label: "Passkey / Hardware Key",
    status: "disabled" as const,
    impact: "high",
  },
];

const ACTIVE_SESSIONS = [
  {
    id: "1",
    device: "Chrome on macOS",
    location: "New York, US",
    lastActive: "Now",
    current: true,
  },
  {
    id: "2",
    device: "Safari on iPhone",
    location: "New York, US",
    lastActive: "2h ago",
    current: false,
  },
];

const RECENT_ACTIVITY = [
  {
    id: "1",
    event: "Successful login",
    device: "Chrome on macOS",
    time: "2 min ago",
    type: "success" as const,
  },
  {
    id: "2",
    event: "Password changed",
    device: "Chrome on macOS",
    time: "3 days ago",
    type: "info" as const,
  },
  {
    id: "3",
    event: "Failed login attempt",
    device: "Unknown",
    time: "5 days ago",
    type: "warning" as const,
  },
];

const scoreFromChecks = (checks: typeof SECURITY_CHECKS) => {
  const weights: Record<string, number> = { high: 3, medium: 2 };
  const total = checks.reduce((a, c) => a + (weights[c.impact] ?? 0), 0);
  const earned = checks
    .filter((c) => c.status === "enabled")
    .reduce((a, c) => a + (weights[c.impact] ?? 0), 0);
  return Math.round((earned / total) * 100);
};

const SecurityScreen: React.FC = () => {
  const navigate = useNavigate();
  const [checks, setChecks] = useState(SECURITY_CHECKS);
  const score = scoreFromChecks(checks);

  const toggle = (id: string) => {
    setChecks((prev) =>
      prev.map((c) =>
        c.id === id
          ? ({
              ...c,
              status: c.status === "enabled" ? "disabled" : "enabled",
            } as typeof c)
          : c,
      ),
    );
    toast.success("Security setting updated");
  };

  const scoreColor =
    score >= 80
      ? "text-emerald-600 dark:text-emerald-400"
      : score >= 50
        ? "text-amber-600 dark:text-amber-400"
        : "text-destructive";
  const scoreBg =
    score >= 80
      ? "bg-emerald-500"
      : score >= 50
        ? "bg-amber-500"
        : "bg-destructive";

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Security</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Monitor and strengthen your account security
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate("/security/advanced")}
        >
          Advanced Settings
        </Button>
      </div>

      {/* Security Score */}
      <Card
        className={cn(
          "border-2",
          score >= 80
            ? "border-emerald-500/30"
            : score >= 50
              ? "border-amber-500/30"
              : "border-destructive/30",
        )}
      >
        <CardContent className="p-6">
          <div className="flex items-center gap-6">
            <div className="relative w-20 h-20 shrink-0">
              <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                <circle
                  cx="40"
                  cy="40"
                  r="34"
                  fill="none"
                  stroke="hsl(var(--muted))"
                  strokeWidth="8"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="34"
                  fill="none"
                  stroke={
                    score >= 80
                      ? "#10b981"
                      : score >= 50
                        ? "#f59e0b"
                        : "#ef4444"
                  }
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 34}`}
                  strokeDashoffset={`${2 * Math.PI * 34 * (1 - score / 100)}`}
                  className="transition-all duration-1000"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span
                  className={cn("text-xl font-bold tabular-nums", scoreColor)}
                >
                  {score}
                </span>
              </div>
            </div>
            <div className="flex-1">
              <p className="font-semibold text-lg">Security Score</p>
              <p className={cn("text-sm font-medium", scoreColor)}>
                {score >= 80
                  ? "Excellent — well protected"
                  : score >= 50
                    ? "Good — room for improvement"
                    : "Weak — take action now"}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {checks.filter((c) => c.status === "disabled").length}{" "}
                recommendations remaining
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Security Checks */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Shield className="h-4 w-4 text-primary" />
              Protection Checks
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {checks.map((check) => (
              <div
                key={check.id}
                className="flex items-center justify-between py-1"
              >
                <div className="flex items-center gap-3">
                  {check.status === "enabled" ? (
                    <CheckCircle className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 text-muted-foreground shrink-0" />
                  )}
                  <div>
                    <p className="text-sm font-medium">{check.label}</p>
                    <Badge
                      variant="secondary"
                      className={cn(
                        "text-[10px] mt-0.5 border-0",
                        check.impact === "high"
                          ? "bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400"
                          : "bg-amber-50 text-amber-600 dark:bg-amber-950/30 dark:text-amber-400",
                      )}
                    >
                      {check.impact} impact
                    </Badge>
                  </div>
                </div>
                <Switch
                  checked={check.status === "enabled"}
                  onCheckedChange={() => toggle(check.id)}
                />
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-4">
          {/* Active Sessions */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Monitor className="h-4 w-4 text-primary" />
                  Active Sessions
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs h-7 px-2 text-destructive"
                >
                  Sign out all
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {ACTIVE_SESSIONS.map((session) => (
                <div
                  key={session.id}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center">
                      <Smartphone className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <p className="text-xs font-medium">{session.device}</p>
                        {session.current && (
                          <Badge
                            variant="secondary"
                            className="text-[10px] h-4 px-1.5 py-0 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400 border-0"
                          >
                            Current
                          </Badge>
                        )}
                      </div>
                      <p className="text-[11px] text-muted-foreground">
                        {session.location} · {session.lastActive}
                      </p>
                    </div>
                  </div>
                  {!session.current && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 text-xs text-destructive px-2"
                    >
                      Revoke
                    </Button>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Key className="h-4 w-4 text-primary" />
                Recent Activity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {RECENT_ACTIVITY.map((item) => (
                <div key={item.id} className="flex items-center gap-3">
                  <div
                    className={cn(
                      "w-7 h-7 rounded-full flex items-center justify-center shrink-0",
                      item.type === "success"
                        ? "bg-emerald-50 dark:bg-emerald-950/30"
                        : item.type === "warning"
                          ? "bg-amber-50 dark:bg-amber-950/30"
                          : "bg-blue-50 dark:bg-blue-950/30",
                    )}
                  >
                    {item.type === "success" ? (
                      <CheckCircle className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                    ) : item.type === "warning" ? (
                      <AlertTriangle className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                    ) : (
                      <Lock className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium">{item.event}</p>
                    <p className="text-[11px] text-muted-foreground truncate">
                      {item.device} · {item.time}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default SecurityScreen;
