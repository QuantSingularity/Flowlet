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
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

type AlertStatus = "pending" | "reviewed" | "resolved" | "dismissed";
type AlertSeverity = "high" | "medium" | "low";

interface FraudAlert {
  id: string;
  severity: AlertSeverity;
  title: string;
  description: string;
  amount?: number;
  merchant?: string;
  location?: string;
  time: string;
  status: AlertStatus;
}

const ALERTS: FraudAlert[] = [
  {
    id: "1",
    severity: "high",
    title: "Unusual Transaction Pattern",
    description:
      "Multiple small transactions detected within 10 minutes - possible card testing",
    amount: 4.99,
    time: "2 hours ago",
    status: "pending",
    location: "Online",
  },
  {
    id: "2",
    severity: "high",
    title: "New Geographic Location",
    description: "Transaction detected 3,000 miles from your usual location",
    amount: 284.5,
    merchant: "Electronics Store",
    time: "5 hours ago",
    status: "pending",
    location: "Dubai, UAE",
  },
  {
    id: "3",
    severity: "medium",
    title: "Velocity Check Failed",
    description: "5 transactions in 3 minutes exceeds normal pattern",
    amount: 156.0,
    time: "1 day ago",
    status: "reviewed",
  },
  {
    id: "4",
    severity: "low",
    title: "Merchant Category Anomaly",
    description: "First transaction at this merchant type",
    amount: 89.99,
    merchant: "Crypto Exchange",
    time: "2 days ago",
    status: "resolved",
  },
  {
    id: "5",
    severity: "medium",
    title: "Large Transaction Alert",
    description: "Transaction 3x larger than your average",
    amount: 1200.0,
    merchant: "Jewelry Store",
    time: "3 days ago",
    status: "dismissed",
  },
];

const severityConfig: Record<
  AlertSeverity,
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
  reviewed: {
    label: "Under Review",
    icon: Eye,
    className: "text-blue-600 dark:text-blue-400",
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

export default function FraudAlerts() {
  const [alerts, setAlerts] = useState(ALERTS);
  const [filter, setFilter] = useState<"all" | AlertStatus>("all");

  const updateStatus = (id: string, status: AlertStatus) => {
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, status } : a)));
    toast.success(`Alert ${status}`);
  };

  const filtered =
    filter === "all" ? alerts : alerts.filter((a) => a.status === filter);
  const pending = alerts.filter((a) => a.status === "pending").length;

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
          onClick={() => toast.info("Refreshing alerts...")}
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 stagger-children">
        {[
          {
            label: "Total Alerts",
            value: alerts.length,
            color: "text-foreground",
          },
          {
            label: "Pending",
            value: alerts.filter((a) => a.status === "pending").length,
            color: "text-amber-600 dark:text-amber-400",
          },
          {
            label: "High Risk",
            value: alerts.filter((a) => a.severity === "high").length,
            color: "text-destructive",
          },
          {
            label: "Resolved",
            value: alerts.filter((a) => a.status === "resolved").length,
            color: "text-emerald-600 dark:text-emerald-400",
          },
        ].map(({ label, value, color }) => (
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

      {/* Filter */}
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
            <SelectItem value="reviewed">Under Review</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
            <SelectItem value="dismissed">Dismissed</SelectItem>
          </SelectContent>
        </Select>
        <span className="text-xs text-muted-foreground">
          {filtered.length} result{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Alerts list */}
      <div className="space-y-3 stagger-children">
        {filtered.map((alert) => {
          const sev = severityConfig[alert.severity];
          const stat = statusConfig[alert.status];
          const SevIcon = sev.icon;
          const StatIcon = stat.icon;

          return (
            <Card
              key={alert.id}
              className={cn(
                "transition-all duration-200",
                alert.status === "resolved" || alert.status === "dismissed"
                  ? "opacity-60"
                  : "",
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
                          <p className="font-semibold text-sm">{alert.title}</p>
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
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {alert.description}
                        </p>
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
                      {alert.amount && (
                        <span className="font-medium text-foreground">
                          ${alert.amount.toFixed(2)}
                        </span>
                      )}
                      {alert.merchant && <span>{alert.merchant}</span>}
                      {alert.location && <span>📍 {alert.location}</span>}
                      <span>{alert.time}</span>
                    </div>

                    {alert.status === "pending" && (
                      <div className="flex gap-2 pt-1">
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs gap-1"
                          onClick={() => updateStatus(alert.id, "reviewed")}
                        >
                          <Eye className="h-3 w-3" />
                          Review
                        </Button>
                        <Button
                          size="sm"
                          className="h-7 text-xs gap-1 bg-emerald-600 hover:bg-emerald-700"
                          onClick={() => updateStatus(alert.id, "resolved")}
                        >
                          <CheckCircle className="h-3 w-3" />
                          Resolve
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs gap-1 text-muted-foreground"
                          onClick={() => updateStatus(alert.id, "dismissed")}
                        >
                          <XCircle className="h-3 w-3" />
                          Dismiss
                        </Button>
                      </div>
                    )}
                    {alert.status === "reviewed" && (
                      <div className="flex gap-2 pt-1">
                        <Button
                          size="sm"
                          className="h-7 text-xs gap-1 bg-emerald-600 hover:bg-emerald-700"
                          onClick={() => updateStatus(alert.id, "resolved")}
                        >
                          <CheckCircle className="h-3 w-3" />
                          Mark Resolved
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs gap-1 text-muted-foreground"
                          onClick={() => updateStatus(alert.id, "dismissed")}
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

        {filtered.length === 0 && (
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
