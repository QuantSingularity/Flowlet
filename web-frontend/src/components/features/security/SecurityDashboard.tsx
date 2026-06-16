import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  Download,
  Eye,
  FileText,
  Flag,
  Globe,
  HardDrive,
  Key,
  MapPin,
  Monitor,
  Network,
  RefreshCw,
  Search,
  Server,
  Shield,
  TrendingDown,
  TrendingUp,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface SecurityMetric {
  id: string;
  name: string;
  value: number;
  unit: string;
  trend: "up" | "down" | "stable";
  trendPercentage: number;
  status: "normal" | "warning" | "critical";
  threshold: {
    warning: number;
    critical: number;
  };
  lastUpdated: string;
  category:
    | "authentication"
    | "authorization"
    | "data_protection"
    | "network"
    | "system"
    | "compliance";
}

interface SecurityEvent {
  id: string;
  timestamp: string;
  type:
    | "login_attempt"
    | "data_access"
    | "permission_change"
    | "system_alert"
    | "threat_detected"
    | "compliance_violation";
  severity: "low" | "medium" | "high" | "critical";
  source: string;
  target: string;
  userId?: string;
  userName?: string;
  ipAddress: string;
  userAgent: string;
  location?: {
    country: string;
    city: string;
    coordinates?: { lat: number; lng: number };
  };
  details: Record<string, any>;
  status: "new" | "investigating" | "resolved" | "false_positive";
  riskScore: number;
  actionsTaken: string[];
  correlatedEvents: string[];
}

interface ThreatIndicator {
  id: string;
  type:
    | "ip_address"
    | "domain"
    | "file_hash"
    | "user_behavior"
    | "network_pattern";
  value: string;
  severity: "low" | "medium" | "high" | "critical";
  confidence: number; // 0-100
  source: string;
  firstSeen: string;
  lastSeen: string;
  occurrences: number;
  description: string;
  mitigationActions: string[];
  isActive: boolean;
  tags: string[];
}

interface SystemHealth {
  id: string;
  component: string;
  status: "healthy" | "degraded" | "down" | "maintenance";
  uptime: number; // percentage
  responseTime: number; // milliseconds
  errorRate: number; // percentage
  throughput: number; // requests per second
  lastCheck: string;
  dependencies: string[];
  alerts: string[];
}

interface ComplianceStatus {
  framework: string;
  status: "compliant" | "non_compliant" | "partial" | "unknown";
  score: number; // 0-100
  requirements: {
    total: number;
    passed: number;
    failed: number;
    pending: number;
  };
  lastAssessment: string;
  nextAssessment: string;
  criticalFindings: string[];
}

interface SecurityDashboardProps {
  metrics?: SecurityMetric[];
  events?: SecurityEvent[];
  threats?: ThreatIndicator[];
  systemHealth?: SystemHealth[];
  complianceStatus?: ComplianceStatus[];
  onEventInvestigate?: (eventId: string) => Promise<void>;
  onThreatMitigate?: (threatId: string, action: string) => Promise<void>;
  onMetricRefresh?: (metricId: string) => Promise<void>;
  onExportReport?: (
    type: "security" | "compliance" | "threats",
    filters: any,
  ) => Promise<Blob>;
  realTimeUpdates?: boolean;
  refreshInterval?: number; // seconds
  className?: string;
}

interface ComponentState {
  activeTab: string;
  selectedEvent: SecurityEvent | null;
  selectedThreat: ThreatIndicator | null;
  timeRange: "1h" | "24h" | "7d" | "30d";
  searchTerm: string;
  filterSeverity: string;
  filterType: string;
  filterStatus: string;
  showEventDetails: boolean;
  showThreatDetails: boolean;
  isRefreshing: boolean;
  isExporting: boolean;
  error: string | null;
  success: string | null;
  lastRefresh: string;
}

export function SecurityDashboard({
  metrics = [],
  events = [],
  threats = [],
  systemHealth = [],
  complianceStatus = [],
  onEventInvestigate,
  onThreatMitigate,
  onMetricRefresh,
  onExportReport,
  realTimeUpdates = true,
  refreshInterval = 30,
  className = "",
}: SecurityDashboardProps) {
  const [state, setState] = useState<ComponentState>({
    activeTab: "overview",
    selectedEvent: null,
    selectedThreat: null,
    timeRange: "24h",
    searchTerm: "",
    filterSeverity: "all",
    filterType: "all",
    filterStatus: "all",
    showEventDetails: false,
    showThreatDetails: false,
    isRefreshing: false,
    isExporting: false,
    error: null,
    success: null,
    lastRefresh: new Date().toISOString(),
  });

  // Auto-refresh functionality
  useEffect(() => {
    if (!realTimeUpdates) return;

    const interval = setInterval(() => {
      setState((prev) => ({ ...prev, lastRefresh: new Date().toISOString() }));
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [realTimeUpdates, refreshInterval]);

  // Calculate dashboard metrics
  const dashboardMetrics = useMemo(() => {
    const now = new Date();
    const timeRangeMs = {
      "1h": 60 * 60 * 1000,
      "24h": 24 * 60 * 60 * 1000,
      "7d": 7 * 24 * 60 * 60 * 1000,
      "30d": 30 * 24 * 60 * 60 * 1000,
    }[state.timeRange];

    const cutoffTime = new Date(now.getTime() - timeRangeMs);

    // Filter events by time range
    const recentEvents = events.filter(
      (event) => new Date(event.timestamp) > cutoffTime,
    );

    const totalEvents = recentEvents.length;
    const criticalEvents = recentEvents.filter(
      (e) => e.severity === "critical",
    ).length;
    const highSeverityEvents = recentEvents.filter(
      (e) => e.severity === "high",
    ).length;
    const newEvents = recentEvents.filter((e) => e.status === "new").length;

    const activeThreats = threats.filter((t) => t.isActive).length;
    const criticalThreats = threats.filter(
      (t) => t.severity === "critical" && t.isActive,
    ).length;

    const healthyComponents = systemHealth.filter(
      (s) => s.status === "healthy",
    ).length;
    const degradedComponents = systemHealth.filter(
      (s) => s.status === "degraded",
    ).length;
    const downComponents = systemHealth.filter(
      (s) => s.status === "down",
    ).length;

    const averageUptime =
      systemHealth.length > 0
        ? systemHealth.reduce((sum, s) => sum + s.uptime, 0) /
          systemHealth.length
        : 100;

    const averageResponseTime =
      systemHealth.length > 0
        ? systemHealth.reduce((sum, s) => sum + s.responseTime, 0) /
          systemHealth.length
        : 0;

    const eventsByType = recentEvents.reduce(
      (acc, event) => {
        acc[event.type] = (acc[event.type] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    const eventsBySeverity = recentEvents.reduce(
      (acc, event) => {
        acc[event.severity] = (acc[event.severity] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    const threatsByType = threats.reduce(
      (acc, threat) => {
        acc[threat.type] = (acc[threat.type] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    const complianceOverall =
      complianceStatus.length > 0
        ? complianceStatus.reduce((sum, c) => sum + c.score, 0) /
          complianceStatus.length
        : 100;

    return {
      totalEvents,
      criticalEvents,
      highSeverityEvents,
      newEvents,
      activeThreats,
      criticalThreats,
      healthyComponents,
      degradedComponents,
      downComponents,
      averageUptime,
      averageResponseTime,
      eventsByType,
      eventsBySeverity,
      threatsByType,
      complianceOverall,
      systemHealthScore:
        systemHealth.length > 0
          ? (healthyComponents / systemHealth.length) * 100
          : 100,
    };
  }, [events, threats, systemHealth, complianceStatus, state.timeRange]);

  // Filter events
  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      const matchesSearch =
        event.type.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
        event.source.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
        event.userName?.toLowerCase().includes(state.searchTerm.toLowerCase());

      const matchesSeverity =
        state.filterSeverity === "all" ||
        event.severity === state.filterSeverity;
      const matchesType =
        state.filterType === "all" || event.type === state.filterType;
      const matchesStatus =
        state.filterStatus === "all" || event.status === state.filterStatus;

      return matchesSearch && matchesSeverity && matchesType && matchesStatus;
    });
  }, [
    events,
    state.searchTerm,
    state.filterSeverity,
    state.filterType,
    state.filterStatus,
  ]);

  // Handle event investigation
  const handleEventInvestigate = useCallback(
    async (eventId: string) => {
      setState((prev) => ({ ...prev, isRefreshing: true, error: null }));

      try {
        if (onEventInvestigate) {
          await onEventInvestigate(eventId);
          setState((prev) => ({
            ...prev,
            success: "Event investigation initiated",
          }));
        }
      } catch (_error) {
        setState((prev) => ({
          ...prev,
          error: "Failed to initiate investigation",
        }));
      } finally {
        setState((prev) => ({ ...prev, isRefreshing: false }));
      }
    },
    [onEventInvestigate],
  );

  // Handle threat mitigation
  const handleThreatMitigate = useCallback(
    async (threatId: string, action: string) => {
      setState((prev) => ({ ...prev, isRefreshing: true, error: null }));

      try {
        if (onThreatMitigate) {
          await onThreatMitigate(threatId, action);
          setState((prev) => ({
            ...prev,
            success: "Threat mitigation initiated",
          }));
        }
      } catch (_error) {
        setState((prev) => ({ ...prev, error: "Failed to mitigate threat" }));
      } finally {
        setState((prev) => ({ ...prev, isRefreshing: false }));
      }
    },
    [onThreatMitigate],
  );

  // Handle metric refresh
  const handleMetricRefresh = useCallback(
    async (metricId?: string) => {
      setState((prev) => ({ ...prev, isRefreshing: true, error: null }));

      try {
        if (onMetricRefresh && metricId) {
          await onMetricRefresh(metricId);
        }
        setState((prev) => ({
          ...prev,
          success: "Metrics refreshed successfully",
          lastRefresh: new Date().toISOString(),
        }));
      } catch (_error) {
        setState((prev) => ({ ...prev, error: "Failed to refresh metrics" }));
      } finally {
        setState((prev) => ({ ...prev, isRefreshing: false }));
      }
    },
    [onMetricRefresh],
  );

  // Handle export
  const handleExport = useCallback(
    async (type: "security" | "compliance" | "threats") => {
      setState((prev) => ({ ...prev, isExporting: true, error: null }));

      try {
        if (onExportReport) {
          const filters = {
            timeRange: state.timeRange,
            severity: state.filterSeverity,
            type: state.filterType,
            status: state.filterStatus,
            search: state.searchTerm,
          };

          const blob = await onExportReport(type, filters);
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `${type}-report-${new Date().toISOString().split("T")[0]}.csv`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          setTimeout(() => URL.revokeObjectURL(url), 100);

          setState((prev) => ({
            ...prev,
            success: "Report exported successfully",
          }));
        }
      } catch (_error) {
        setState((prev) => ({ ...prev, error: "Failed to export report" }));
      } finally {
        setState((prev) => ({ ...prev, isExporting: false }));
      }
    },
    [
      onExportReport,
      state.timeRange,
      state.filterSeverity,
      state.filterType,
      state.filterStatus,
      state.searchTerm,
    ],
  );

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "low":
        return "bg-green-100 text-green-600";
      case "medium":
        return "bg-yellow-100 text-yellow-600";
      case "high":
        return "bg-orange-100 text-orange-600";
      case "critical":
        return "bg-red-100 text-red-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
      case "compliant":
      case "resolved":
        return "bg-green-100 text-green-600";
      case "degraded":
      case "partial":
      case "investigating":
        return "bg-yellow-100 text-yellow-600";
      case "down":
      case "non_compliant":
      case "new":
        return "bg-red-100 text-red-600";
      case "maintenance":
      case "unknown":
      case "false_positive":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const getMetricStatusColor = (metric: SecurityMetric) => {
    switch (metric.status) {
      case "normal":
        return "text-green-600";
      case "warning":
        return "text-yellow-600";
      case "critical":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  const getTrendIcon = (trend: string, percentage: number) => {
    if (trend === "up") {
      return (
        <TrendingUp
          className={`w-4 h-4 ${percentage > 0 ? "text-red-500" : "text-green-500"}`}
        />
      );
    } else if (trend === "down") {
      return (
        <TrendingDown
          className={`w-4 h-4 ${percentage > 0 ? "text-green-500" : "text-red-500"}`}
        />
      );
    }
    return <Activity className="w-4 h-4 text-gray-500" />;
  };

  const getEventTypeIcon = (type: string) => {
    switch (type) {
      case "login_attempt":
        return <Key className="w-4 h-4" />;
      case "data_access":
        return <Database className="w-4 h-4" />;
      case "permission_change":
        return <Shield className="w-4 h-4" />;
      case "system_alert":
        return <Monitor className="w-4 h-4" />;
      case "threat_detected":
        return <AlertTriangle className="w-4 h-4" />;
      case "compliance_violation":
        return <FileText className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const getSystemIcon = (component: string) => {
    if (component.toLowerCase().includes("database"))
      return <Database className="w-4 h-4" />;
    if (component.toLowerCase().includes("api"))
      return <Globe className="w-4 h-4" />;
    if (component.toLowerCase().includes("auth"))
      return <Key className="w-4 h-4" />;
    if (component.toLowerCase().includes("network"))
      return <Network className="w-4 h-4" />;
    if (component.toLowerCase().includes("storage"))
      return <HardDrive className="w-4 h-4" />;
    return <Server className="w-4 h-4" />;
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center">
              <Shield className="w-6 h-6 mr-3 text-blue-600" />
              Security Operations Center
            </div>
            <div className="flex items-center space-x-2">
              <Select
                value={state.timeRange}
                onValueChange={(value) =>
                  setState((prev) => ({
                    ...prev,
                    timeRange: value as "1h" | "24h" | "7d" | "30d",
                  }))
                }
              >
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1h">Last Hour</SelectItem>
                  <SelectItem value="24h">Last 24h</SelectItem>
                  <SelectItem value="7d">Last 7 days</SelectItem>
                  <SelectItem value="30d">Last 30 days</SelectItem>
                </SelectContent>
              </Select>
              <Button
                onClick={() => handleMetricRefresh()}
                disabled={state.isRefreshing}
                size="sm"
                variant="outline"
              >
                <RefreshCw
                  className={`w-4 h-4 mr-2 ${state.isRefreshing ? "animate-spin" : ""}`}
                />
                Refresh
              </Button>
              {realTimeUpdates && (
                <Badge className="bg-green-100 text-green-600">
                  <Activity className="w-3 h-3 mr-1" />
                  Live
                </Badge>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Real-time security monitoring and threat detection dashboard.
            </p>
            <p className="text-xs text-gray-500">
              Last updated: {new Date(state.lastRefresh).toLocaleTimeString()}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Alerts */}
      {state.error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {state.error}
          </AlertDescription>
        </Alert>
      )}

      {state.success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            {state.success}
          </AlertDescription>
        </Alert>
      )}

      {dashboardMetrics.criticalEvents > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <strong>Critical Alert:</strong> {dashboardMetrics.criticalEvents}{" "}
            critical security events detected.
          </AlertDescription>
        </Alert>
      )}

      {dashboardMetrics.criticalThreats > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <Flag className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <strong>Threat Alert:</strong> {dashboardMetrics.criticalThreats}{" "}
            critical threats require immediate attention.
          </AlertDescription>
        </Alert>
      )}

      {dashboardMetrics.downComponents > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <XCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <strong>System Alert:</strong> {dashboardMetrics.downComponents}{" "}
            system components are down.
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <Tabs
        value={state.activeTab}
        onValueChange={(value) =>
          setState((prev) => ({ ...prev, activeTab: value }))
        }
      >
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="events">Events</TabsTrigger>
          <TabsTrigger value="threats">Threats</TabsTrigger>
          <TabsTrigger value="systems">Systems</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        Security Events
                      </p>
                      <p className="text-2xl font-bold">
                        {dashboardMetrics.totalEvents}
                      </p>
                      <p className="text-xs text-gray-500">
                        {dashboardMetrics.criticalEvents} critical
                      </p>
                    </div>
                    <AlertTriangle className="w-8 h-8 text-orange-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        Active Threats
                      </p>
                      <p className="text-2xl font-bold text-red-600">
                        {dashboardMetrics.activeThreats}
                      </p>
                      <p className="text-xs text-gray-500">
                        {dashboardMetrics.criticalThreats} critical
                      </p>
                    </div>
                    <Flag className="w-8 h-8 text-red-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        System Health
                      </p>
                      <p className="text-2xl font-bold text-green-600">
                        {dashboardMetrics.systemHealthScore.toFixed(1)}%
                      </p>
                      <p className="text-xs text-gray-500">
                        {dashboardMetrics.healthyComponents}/
                        {systemHealth.length} healthy
                      </p>
                    </div>
                    <Monitor className="w-8 h-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        Compliance Score
                      </p>
                      <p className="text-2xl font-bold text-blue-600">
                        {dashboardMetrics.complianceOverall.toFixed(1)}%
                      </p>
                      <p className="text-xs text-gray-500">
                        {complianceStatus.length} frameworks
                      </p>
                    </div>
                    <CheckCircle className="w-8 h-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Charts and Distributions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Events by Type</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(dashboardMetrics.eventsByType).map(
                      ([type, count]) => (
                        <div
                          key={type}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded"
                        >
                          <div className="flex items-center space-x-2">
                            {getEventTypeIcon(type)}
                            <span className="font-medium capitalize">
                              {type.replace("_", " ")}
                            </span>
                          </div>
                          <Badge className="bg-blue-100 text-blue-600">
                            {count} events
                          </Badge>
                        </div>
                      ),
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Events by Severity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(dashboardMetrics.eventsBySeverity).map(
                      ([severity, count]) => (
                        <div
                          key={severity}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded"
                        >
                          <div className="flex items-center space-x-2">
                            <AlertTriangle className="w-4 h-4 text-gray-400" />
                            <span className="font-medium capitalize">
                              {severity}
                            </span>
                          </div>
                          <Badge className={getSeverityColor(severity)}>
                            {count} events
                          </Badge>
                        </div>
                      ),
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Critical Events */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Critical Events</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {filteredEvents
                    .filter(
                      (e) => e.severity === "critical" || e.severity === "high",
                    )
                    .slice(0, 5)
                    .map((event) => (
                      <div
                        key={event.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded"
                      >
                        <div className="flex items-center space-x-3">
                          {getEventTypeIcon(event.type)}
                          <div>
                            <p className="font-medium text-sm capitalize">
                              {event.type.replace("_", " ")}
                            </p>
                            <p className="text-xs text-gray-600">
                              {event.source} • {event.userName || "System"} •{" "}
                              {event.ipAddress}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge className={getSeverityColor(event.severity)}>
                            {event.severity}
                          </Badge>
                          <Badge className={getStatusColor(event.status)}>
                            {event.status.replace("_", " ")}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {new Date(event.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Events Tab */}
        <TabsContent value="events">
          <div className="space-y-4">
            {/* Search and Filters */}
            <Card>
              <CardContent className="p-4">
                <div className="flex space-x-4 mb-4">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                      <Input
                        placeholder="Search events by type, source, user..."
                        value={state.searchTerm}
                        onChange={(e) =>
                          setState((prev) => ({
                            ...prev,
                            searchTerm: e.target.value,
                          }))
                        }
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <Select
                    value={state.filterSeverity}
                    onValueChange={(value) =>
                      setState((prev) => ({ ...prev, filterSeverity: value }))
                    }
                  >
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="Severity" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Severity</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select
                    value={state.filterType}
                    onValueChange={(value) =>
                      setState((prev) => ({ ...prev, filterType: value }))
                    }
                  >
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder="Event Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="login_attempt">
                        Login Attempt
                      </SelectItem>
                      <SelectItem value="data_access">Data Access</SelectItem>
                      <SelectItem value="permission_change">
                        Permission Change
                      </SelectItem>
                      <SelectItem value="system_alert">System Alert</SelectItem>
                      <SelectItem value="threat_detected">
                        Threat Detected
                      </SelectItem>
                      <SelectItem value="compliance_violation">
                        Compliance Violation
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <Select
                    value={state.filterStatus}
                    onValueChange={(value) =>
                      setState((prev) => ({ ...prev, filterStatus: value }))
                    }
                  >
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="new">New</SelectItem>
                      <SelectItem value="investigating">
                        Investigating
                      </SelectItem>
                      <SelectItem value="resolved">Resolved</SelectItem>
                      <SelectItem value="false_positive">
                        False Positive
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex justify-between items-center">
                  <p className="text-sm text-gray-600">
                    Showing {filteredEvents.length} of {events.length} events
                  </p>
                  <Button
                    onClick={() => handleExport("security")}
                    disabled={state.isExporting}
                    size="sm"
                    variant="outline"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Events List */}
            <div className="grid gap-4">
              {filteredEvents.slice(0, 50).map((event) => (
                <Card
                  key={event.id}
                  className="hover:shadow-md transition-shadow"
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getEventTypeIcon(event.type)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium capitalize">
                              {event.type.replace("_", " ")}
                            </h4>
                            <Badge className={getSeverityColor(event.severity)}>
                              {event.severity}
                            </Badge>
                            <Badge className={getStatusColor(event.status)}>
                              {event.status.replace("_", " ")}
                            </Badge>
                            <Badge className="bg-purple-100 text-purple-600">
                              Risk: {event.riskScore}/100
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-500 mb-2">
                            <span>Source: {event.source}</span>
                            <span>Target: {event.target}</span>
                            <span>User: {event.userName || "System"}</span>
                            <span>IP: {event.ipAddress}</span>
                          </div>
                          <div className="flex items-center space-x-2 text-xs text-gray-600">
                            <Clock className="w-3 h-3" />
                            <span>
                              {new Date(event.timestamp).toLocaleString()}
                            </span>
                            {event.location && (
                              <>
                                <MapPin className="w-3 h-3 ml-2" />
                                <span>
                                  {event.location.city},{" "}
                                  {event.location.country}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          onClick={() =>
                            setState((prev) => ({
                              ...prev,
                              selectedEvent: event,
                              showEventDetails: true,
                            }))
                          }
                          size="sm"
                          variant="outline"
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          Details
                        </Button>
                        {event.status === "new" && (
                          <Button
                            onClick={() => handleEventInvestigate(event.id)}
                            disabled={state.isRefreshing}
                            size="sm"
                          >
                            <Search className="w-3 h-3 mr-1" />
                            Investigate
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {filteredEvents.length === 0 && (
              <Card>
                <CardContent className="p-6 text-center">
                  <Activity className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Events Found
                  </h3>
                  <p className="text-sm text-gray-600">
                    No security events match your current filters. Try adjusting
                    your search criteria.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Threats Tab */}
        <TabsContent value="threats">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">Threat Intelligence</h3>
              <Button
                onClick={() => handleExport("threats")}
                disabled={state.isExporting}
                size="sm"
                variant="outline"
              >
                <Download className="w-4 h-4 mr-2" />
                Export Threats
              </Button>
            </div>

            <div className="grid gap-4">
              {threats
                .filter((t) => t.isActive)
                .map((threat) => (
                  <Card
                    key={threat.id}
                    className="hover:shadow-md transition-shadow"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium">{threat.value}</h4>
                            <Badge
                              className={getSeverityColor(threat.severity)}
                            >
                              {threat.severity}
                            </Badge>
                            <Badge className="bg-blue-100 text-blue-600">
                              {threat.type.replace("_", " ")}
                            </Badge>
                            <Badge className="bg-purple-100 text-purple-600">
                              Confidence: {threat.confidence}%
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">
                            {threat.description}
                          </p>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-500 mb-2">
                            <span>Source: {threat.source}</span>
                            <span>Occurrences: {threat.occurrences}</span>
                            <span>
                              First Seen:{" "}
                              {new Date(threat.firstSeen).toLocaleDateString()}
                            </span>
                            <span>
                              Last Seen:{" "}
                              {new Date(threat.lastSeen).toLocaleDateString()}
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {threat.tags.map((tag) => (
                              <Badge
                                key={tag}
                                className="bg-gray-100 text-gray-600 text-xs"
                              >
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <Button
                            onClick={() =>
                              setState((prev) => ({
                                ...prev,
                                selectedThreat: threat,
                                showThreatDetails: true,
                              }))
                            }
                            size="sm"
                            variant="outline"
                          >
                            <Eye className="w-3 h-3 mr-1" />
                            Details
                          </Button>
                          <Button
                            onClick={() =>
                              handleThreatMitigate(threat.id, "block")
                            }
                            disabled={state.isRefreshing}
                            size="sm"
                            variant="destructive"
                          >
                            <Shield className="w-3 h-3 mr-1" />
                            Block
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
            </div>
          </div>
        </TabsContent>

        {/* Systems Tab */}
        <TabsContent value="systems">
          <div className="space-y-4">
            <h3 className="text-lg font-medium">System Health Monitoring</h3>

            <div className="grid gap-4">
              {systemHealth.map((system) => (
                <Card key={system.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getSystemIcon(system.component)}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium">{system.component}</h4>
                            <Badge className={getStatusColor(system.status)}>
                              {system.status}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-500 mb-3">
                            <span>Uptime: {system.uptime.toFixed(2)}%</span>
                            <span>Response: {system.responseTime}ms</span>
                            <span>
                              Error Rate: {system.errorRate.toFixed(2)}%
                            </span>
                            <span>Throughput: {system.throughput} req/s</span>
                          </div>
                          <div className="space-y-2">
                            <div>
                              <div className="flex justify-between text-sm mb-1">
                                <span>Uptime</span>
                                <span>{system.uptime.toFixed(1)}%</span>
                              </div>
                              <Progress value={system.uptime} className="h-2" />
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          onClick={() => handleMetricRefresh(system.id)}
                          disabled={state.isRefreshing}
                          size="sm"
                          variant="outline"
                        >
                          <RefreshCw className="w-3 h-3 mr-1" />
                          Refresh
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Compliance Tab */}
        <TabsContent value="compliance">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">Compliance Status</h3>
              <Button
                onClick={() => handleExport("compliance")}
                disabled={state.isExporting}
                size="sm"
                variant="outline"
              >
                <Download className="w-4 h-4 mr-2" />
                Export Report
              </Button>
            </div>

            <div className="grid gap-4">
              {complianceStatus.map((compliance) => (
                <Card key={compliance.framework}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium">
                            {compliance.framework}
                          </h4>
                          <Badge className={getStatusColor(compliance.status)}>
                            {compliance.status.replace("_", " ")}
                          </Badge>
                          <Badge className="bg-blue-100 text-blue-600">
                            Score: {compliance.score}%
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-500 mb-3">
                          <span>Total: {compliance.requirements.total}</span>
                          <span>Passed: {compliance.requirements.passed}</span>
                          <span>Failed: {compliance.requirements.failed}</span>
                          <span>
                            Pending: {compliance.requirements.pending}
                          </span>
                        </div>
                        <div className="space-y-2">
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span>Compliance Score</span>
                              <span>{compliance.score}%</span>
                            </div>
                            <Progress
                              value={compliance.score}
                              className="h-2"
                            />
                          </div>
                        </div>
                        {compliance.criticalFindings.length > 0 && (
                          <div className="mt-3">
                            <p className="text-sm font-medium text-red-600 mb-1">
                              Critical Findings:
                            </p>
                            <ul className="text-xs text-red-600 space-y-1">
                              {compliance.criticalFindings
                                .slice(0, 3)
                                .map((finding) => (
                                  <li key={finding}>• {finding}</li>
                                ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics">
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Security Metrics</h3>

            <div className="grid gap-4">
              {metrics.map((metric) => (
                <Card key={metric.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h4 className="font-medium">{metric.name}</h4>
                          <Badge className={getStatusColor(metric.status)}>
                            {metric.status}
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-4">
                          <span
                            className={`text-2xl font-bold ${getMetricStatusColor(metric)}`}
                          >
                            {metric.value} {metric.unit}
                          </span>
                          <div className="flex items-center space-x-1">
                            {getTrendIcon(metric.trend, metric.trendPercentage)}
                            <span className="text-sm text-gray-600">
                              {metric.trendPercentage.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          Last updated:{" "}
                          {new Date(metric.lastUpdated).toLocaleString()}
                        </p>
                      </div>
                      <Button
                        onClick={() => handleMetricRefresh(metric.id)}
                        disabled={state.isRefreshing}
                        size="sm"
                        variant="outline"
                      >
                        <RefreshCw className="w-3 h-3 mr-1" />
                        Refresh
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Event Details Modal */}
      {state.showEventDetails && state.selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Event Details</span>
                <Button
                  onClick={() =>
                    setState((prev) => ({
                      ...prev,
                      showEventDetails: false,
                      selectedEvent: null,
                    }))
                  }
                  variant="outline"
                  size="sm"
                >
                  ✕
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">
                    Event Information
                  </Label>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">ID:</span>
                      <span className="font-mono">
                        {state.selectedEvent.id}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Type:</span>
                      <span className="capitalize">
                        {state.selectedEvent.type.replace("_", " ")}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Severity:</span>
                      <Badge
                        className={getSeverityColor(
                          state.selectedEvent.severity,
                        )}
                      >
                        {state.selectedEvent.severity}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Status:</span>
                      <Badge
                        className={getStatusColor(state.selectedEvent.status)}
                      >
                        {state.selectedEvent.status.replace("_", " ")}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Risk Score:</span>
                      <span>{state.selectedEvent.riskScore}/100</span>
                    </div>
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium">
                    Source Information
                  </Label>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Source:</span>
                      <span>{state.selectedEvent.source}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Target:</span>
                      <span>{state.selectedEvent.target}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">User:</span>
                      <span>{state.selectedEvent.userName || "System"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">IP Address:</span>
                      <span className="font-mono">
                        {state.selectedEvent.ipAddress}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Timestamp:</span>
                      <span>
                        {new Date(
                          state.selectedEvent.timestamp,
                        ).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {state.selectedEvent.details && (
                <div>
                  <Label className="text-sm font-medium">Event Details</Label>
                  <pre className="mt-2 p-3 bg-gray-50 rounded text-xs overflow-x-auto">
                    {JSON.stringify(state.selectedEvent.details, null, 2)}
                  </pre>
                </div>
              )}

              {state.selectedEvent.actionsTaken.length > 0 && (
                <div>
                  <Label className="text-sm font-medium">Actions Taken</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {state.selectedEvent.actionsTaken.map((action) => (
                      <Badge key={action} className="bg-blue-100 text-blue-600">
                        {action}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex space-x-2">
                {state.selectedEvent.status === "new" && (
                  <Button
                    onClick={() => {
                      if (state.selectedEvent) {
                        handleEventInvestigate(state.selectedEvent.id);
                      }
                    }}
                    disabled={state.isRefreshing}
                    size="sm"
                  >
                    <Search className="w-4 h-4 mr-2" />
                    Start Investigation
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default SecurityDashboard;
