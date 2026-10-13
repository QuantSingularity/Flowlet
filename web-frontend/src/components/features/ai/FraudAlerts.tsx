import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Eye,
  Filter,
  RefreshCw,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { describeError, useAsyncData } from "@/hooks/useAsyncData";
import {
  mlService,
  type AlertStatus,
  type FraudAlertRecord,
  type RiskLevel,
} from "@/lib/api/mlService";

type SeverityKey = "high" | "medium" | "low";

const severityFor = (level: RiskLevel | null): SeverityKey => {
  if (level === "critical" || level === "high") return "high";
  if (level === "medium") return "medium";
  return "low";
};

const severityConfig: Record<
  SeverityKey,
  { label: string; className: string; dot: string; icon: typeof AlertTriangle }
> = {
  high: {
    label: "High Risk",
    className:
      "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400 border-red-200 dark:border-red-900",
    dot: "bg-red-500 animate-pulse",
    icon: ShieldAlert,
  },
  medium: {
    label: "Medium Risk",
    className:
      "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400 border-amber-200 dark:border-amber-900",
    dot: "bg-amber-500",
    icon: AlertTriangle,
  },
  low: {
    label: "Low Risk",
    className:
      "bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400 border-blue-200 dark:border-blue-900",
    dot: "bg-blue-500",
    icon: Eye,
  },
};

const statusConfig: Record<
  AlertStatus,
  { label: string; icon: typeof CheckCircle; className: string }
> = {
  pending: {
    label: "Pending Review",
    icon: Clock,
    className: "text-amber-600 dark:text-amber-400",
  },
  investigating: {
    label: "Investigating",
    icon: Eye,
    className: "text-blue-600 dark:text-blue-400",
  },
  reviewed: {
    label: "Under Review",
    icon: Eye,
    className: "text-blue-600 dark:text-blue-400",
  },
  confirmed: {
    label: "Confirmed Fraud",
    icon: ShieldAlert,
    className: "text-destructive",
  },
  false_positive: {
    label: "False Positive",
    icon: CheckCircle,
    className: "text-emerald-600 dark:text-emerald-400",
  },
  resolved: {
    label: "Resolved",
    icon: CheckCircle,
    className: "text-emerald-600 dark:text-emerald-400",
  },
  dismissed: {
    label: "Dismissed",
    icon: XCircle,
    className: "text-muted-foreground",
  },
};

const CLOSED: AlertStatus[] = [
  "resolved",
  "dismissed",
  "confirmed",
  "false_positive",
];

const titleFor = (alert: FraudAlertRecord) =>
  alert.alert_type
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

const formatTime = (value: string | null) =>
  value ? new Date(value).toLocaleString() : "";

export default function FraudAlerts() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [filter, setFilter] = useState<"all" | AlertStatus>("all");
  const [busyId, setBusyId] = useState<string | null>(null);

  const { data, loading, error, reload } = useAsyncData(
    () =>
      mlService.listAlerts({
        per_page: 100,
        status: filter === "all" ? undefined : filter,
      }),
    [filter],
  );

  const alerts = data?.alerts ?? [];
  const pending = alerts.filter((a) => a.status === "pending").length;

  const act = async (
    id: string,
    task: () => Promise<unknown>,
    done: string,
  ) => {
    setBusyId(id);
    try {
      await task();
      toast.success(done);
      await reload();
    } catch (err) {
      toast.error(describeError(err));
    } finally {
      setBusyId(null);
    }
  };

  const stats = [
    {
      label: "Total Alerts",
      value: data?.pagination.total ?? 0,
      color: "text-foreground",
    },
    {
      label: "Pending",
      value: pending,
      color: "text-amber-600 dark:text-amber-400",
    },
    {
      label: "High Risk",
      value: alerts.filter((a) => severityFor(a.risk_level) === "high").length,
      color: "text-destructive",
    },
    {
      label: "Closed",
      value: alerts.filter((a) => CLOSED.includes(a.status)).length,
      color: "text-emerald-600 dark:text-emerald-400",
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">Fraud Alerts</h1>
            {pending > 0 && (
              <Badge variant="destructive" className="text-xs px-2">
                {pending} pending
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm mt-1">
            Review and respond to suspicious activity
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5 self-start"
          onClick={() => void reload()}
          disabled={loading}
        >
          <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 stagger-children">
        {stats.map(({ label, value, color }) => (
          <Card key={label}>
            <CardContent className="p-4 text-center">
              <p className={cn("text-2xl font-bold tabular-nums", color)}>
                {value}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <Filter className="h-4 w-4 text-muted-foreground shrink-0" />
        <Select
          value={filter}
          onValueChange={(v) => setFilter(v as typeof filter)}
        >
          <SelectTrigger className="w-48 h-9 text-sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All alerts</SelectItem>
            <SelectItem value="pending">Pending Review</SelectItem>
            <SelectItem value="investigating">Investigating</SelectItem>
            <SelectItem value="reviewed">Under Review</SelectItem>
            <SelectItem value="confirmed">Confirmed Fraud</SelectItem>
            <SelectItem value="false_positive">False Positive</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
            <SelectItem value="dismissed">Dismissed</SelectItem>
          </SelectContent>
        </Select>
        <span className="text-xs text-muted-foreground">
          {alerts.length} result{alerts.length !== 1 ? "s" : ""}
        </span>
      </div>

      {error && (
        <Card>
          <CardContent className="py-6 text-center space-y-3">
            <p className="text-sm text-destructive">{error}</p>
            <Button size="sm" variant="outline" onClick={() => void reload()}>
              Try again
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3 stagger-children">
        {alerts.map((alert) => {
          const sev = severityConfig[severityFor(alert.risk_level)];
          const stat = statusConfig[alert.status] ?? statusConfig.pending;
          const SevIcon = sev.icon;
          const StatIcon = stat.icon;
          const closed = CLOSED.includes(alert.status);
          const busy = busyId === alert.id;
          const hits = alert.details?.rule_hits ?? [];

          return (
            <Card
              key={alert.id}
              className={cn(
                "transition-all duration-200",
                closed && "opacity-60",
              )}
            >
              <CardContent className="p-5">
                <div className="flex items-start gap-4">
                  <div
                    className={cn(
                      "w-10 h-10 rounded-xl border flex items-center justify-center shrink-0",
                      sev.className,
                    )}
                  >
                    <SevIcon className="h-5 w-5" />
                  </div>

                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="flex items-start justify-between gap-2 flex-wrap">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="font-semibold text-sm">
                            {titleFor(alert)}
                          </p>
                          <Badge
                            variant="outline"
                            className={cn("text-[10px] border", sev.className)}
                          >
                            <span
                              className={cn(
                                "w-1.5 h-1.5 rounded-full mr-1.5",
                                sev.dot,
                              )}
                            />
                            {sev.label}
                          </Badge>
                        </div>
                        {alert.description && (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {alert.description}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <StatIcon
                          className={cn("h-3.5 w-3.5", stat.className)}
                        />
                        <span
                          className={cn(
                            "text-[11px] font-medium",
                            stat.className,
                          )}
                        >
                          {stat.label}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                      <span className="font-medium text-foreground">
                        Risk score {Math.round(alert.risk_score)}
                      </span>
                      {alert.transaction_id && (
                        <span>Ref {alert.transaction_id.slice(0, 12)}</span>
                      )}
                      <span>{formatTime(alert.created_at)}</span>
                    </div>

                    {hits.length > 0 && (
                      <ul className="text-xs text-muted-foreground list-disc pl-4 space-y-0.5">
                        {hits.slice(0, 3).map((hit) => (
                          <li key={hit.name}>{hit.description}</li>
                        ))}
                      </ul>
                    )}

                    {!closed && !isAdmin && (
                      <div className="flex gap-2 pt-1">
                        <Button
                          size="sm"
                          className="h-7 text-xs gap-1 bg-emerald-600 hover:bg-emerald-700"
                          disabled={busy}
                          onClick={() =>
                            void act(
                              alert.id,
                              () =>
                                mlService.respondToAlert(
                                  alert.id,
                                  "recognized",
                                ),
                              "Thanks, we noted that you recognize this activity",
                            )
                          }
                        >
                          <CheckCircle className="h-3 w-3" />
                          This was me
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          className="h-7 text-xs gap-1"
                          disabled={busy}
                          onClick={() =>
                            void act(
                              alert.id,
                              () =>
                                mlService.respondToAlert(alert.id, "not_me"),
                              "Reported. Our team will investigate",
                            )
                          }
                        >
                          <ShieldAlert className="h-3 w-3" />
                          Not me
                        </Button>
                      </div>
                    )}

                    {!closed && isAdmin && (
                      <div className="flex gap-2 pt-1">
                        <Button
                          size="sm"
                          variant="destructive"
                          className="h-7 text-xs gap-1"
                          disabled={busy}
                          onClick={() =>
                            void act(
                              alert.id,
                              () =>
                                mlService.resolveAlert(alert.id, "confirmed"),
                              "Marked as confirmed fraud",
                            )
                          }
                        >
                          <ShieldAlert className="h-3 w-3" />
                          Confirm fraud
                        </Button>
                        <Button
                          size="sm"
                          className="h-7 text-xs gap-1 bg-emerald-600 hover:bg-emerald-700"
                          disabled={busy}
                          onClick={() =>
                            void act(
                              alert.id,
                              () =>
                                mlService.resolveAlert(
                                  alert.id,
                                  "false_positive",
                                ),
                              "Marked as false positive",
                            )
                          }
                        >
                          <CheckCircle className="h-3 w-3" />
                          False positive
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs gap-1 text-muted-foreground"
                          disabled={busy}
                          onClick={() =>
                            void act(
                              alert.id,
                              () =>
                                mlService.resolveAlert(alert.id, "dismissed"),
                              "Alert dismissed",
                            )
                          }
                        >
                          <XCircle className="h-3 w-3" />
                          Dismiss
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}

        {!loading && !error && alerts.length === 0 && (
          <Card>
            <CardContent className="py-16 text-center">
              <CheckCircle className="h-10 w-10 mx-auto mb-3 text-emerald-500 opacity-60" />
              <p className="font-semibold text-muted-foreground">
                No alerts in this category
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
