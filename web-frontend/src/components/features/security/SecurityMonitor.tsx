import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  Eye,
  Globe,
  Lock,
  RefreshCw,
  Shield,
  TrendingUp,
  Wifi,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface SecurityEvent {
  id: string;
  type:
    | "login"
    | "logout"
    | "failed_login"
    | "permission_denied"
    | "data_access"
    | "security_violation";
  severity: "low" | "medium" | "high" | "critical";
  timestamp: string;
  description: string;
  userAgent?: string;
  ipAddress?: string;
  location?: string;
  metadata?: Record<string, any>;
}

interface SecurityMetrics {
  totalEvents: number;
  criticalEvents: number;
  highEvents: number;
  mediumEvents: number;
  lowEvents: number;
  successfulLogins: number;
  failedLogins: number;
  dataAccesses: number;
  securityViolations: number;
  lastUpdated: string;
}

interface ThreatLevel {
  level: "low" | "medium" | "high" | "critical";
  score: number;
  factors: string[];
  recommendations: string[];
}

interface SecurityMonitorProps {
  events?: SecurityEvent[];
  metrics?: SecurityMetrics;
  threatLevel?: ThreatLevel;
  onRefresh?: () => void;
  onExport?: () => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
  className?: string;
}

export function SecurityMonitor({
  events = [],
  metrics,
  threatLevel,
  onRefresh,
  onExport,
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
  className = "",
}: SecurityMonitorProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<SecurityEvent | null>(
    null,
  );
  const [filter, setFilter] = useState<
    "all" | "critical" | "high" | "medium" | "low"
  >("all");

  const handleRefresh = useCallback(async () => {
    if (!onRefresh) return;

    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  }, [onRefresh]);

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh && onRefresh) {
      const interval = setInterval(() => {
        handleRefresh();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, onRefresh, handleRefresh]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "text-red-600 bg-red-100 border-red-200";
      case "high":
        return "text-orange-600 bg-orange-100 border-orange-200";
      case "medium":
        return "text-yellow-600 bg-yellow-100 border-yellow-200";
      case "low":
        return "text-green-600 bg-green-100 border-green-200";
      default:
        return "text-gray-600 bg-gray-100 border-gray-200";
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <XCircle className="w-4 h-4" />;
      case "high":
        return <AlertTriangle className="w-4 h-4" />;
      case "medium":
        return <Activity className="w-4 h-4" />;
      case "low":
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const getThreatLevelColor = (level: string) => {
    switch (level) {
      case "critical":
        return "bg-red-500";
      case "high":
        return "bg-orange-500";
      case "medium":
        return "bg-yellow-500";
      case "low":
        return "bg-green-500";
      default:
        return "bg-gray-500";
    }
  };

  const filteredEvents = events.filter(
    (event) => filter === "all" || event.severity === filter,
  );

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const calculateThreatScore = () => {
    if (threatLevel) return threatLevel.score;
    if (!metrics) return 0;

    const { criticalEvents, highEvents, mediumEvents, totalEvents } = metrics;
    if (totalEvents === 0) return 0;

    const score =
      ((criticalEvents * 4 + highEvents * 3 + mediumEvents * 2) / totalEvents) *
      25;
    return Math.min(100, Math.round(score));
  };

  const getThreatLevelFromScore = (
    score: number,
  ): "low" | "medium" | "high" | "critical" => {
    if (score >= 75) return "critical";
    if (score >= 50) return "high";
    if (score >= 25) return "medium";
    return "low";
  };

  const currentThreatScore = calculateThreatScore();
  const currentThreatLevel =
    threatLevel?.level || getThreatLevelFromScore(currentThreatScore);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Shield className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">Security Monitor</h2>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={handleRefresh}
            disabled={isRefreshing}
            size="sm"
            variant="outline"
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          {onExport && (
            <Button onClick={onExport} size="sm" variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          )}
        </div>
      </div>

      {/* Threat Level Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Threat Level Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Current Threat Level</span>
              <Badge
                className={`${getSeverityColor(currentThreatLevel)} border`}
              >
                {getSeverityIcon(currentThreatLevel)}
                <span className="ml-1 capitalize">{currentThreatLevel}</span>
              </Badge>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Threat Score</span>
                <span>{currentThreatScore}/100</span>
              </div>
              <Progress
                value={currentThreatScore}
                className="h-2"
                style={{
                  background: `linear-gradient(to right, ${getThreatLevelColor(currentThreatLevel)} 0%, ${getThreatLevelColor(currentThreatLevel)} ${currentThreatScore}%, #e5e7eb ${currentThreatScore}%, #e5e7eb 100%)`,
                }}
              />
            </div>

            {threatLevel?.factors && threatLevel.factors.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2">
                  Contributing Factors:
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {threatLevel.factors.map((factor, index) => (
                    <li key={factor + index} className="flex items-center">
                      <AlertTriangle className="w-3 h-3 mr-2 text-amber-500" />
                      {factor}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {threatLevel?.recommendations &&
              threatLevel.recommendations.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Recommendations:</h4>
                  <ul className="text-sm text-blue-600 space-y-1">
                    {threatLevel.recommendations.map((rec, index) => (
                      <li key={rec + index} className="flex items-center">
                        <CheckCircle className="w-3 h-3 mr-2 text-blue-500" />
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
          </div>
        </CardContent>
      </Card>

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    Total Events
                  </p>
                  <p className="text-2xl font-bold">{metrics.totalEvents}</p>
                </div>
                <Activity className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    Critical Events
                  </p>
                  <p className="text-2xl font-bold text-red-600">
                    {metrics.criticalEvents}
                  </p>
                </div>
                <XCircle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    Failed Logins
                  </p>
                  <p className="text-2xl font-bold text-orange-600">
                    {metrics.failedLogins}
                  </p>
                </div>
                <Lock className="w-8 h-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    Data Accesses
                  </p>
                  <p className="text-2xl font-bold text-green-600">
                    {metrics.dataAccesses}
                  </p>
                </div>
                <Eye className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Events Timeline */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Security Events
            </CardTitle>
            <div className="flex space-x-2">
              {(
                ["all", "critical", "high", "medium", "low"] as Array<
                  "all" | "critical" | "high" | "medium" | "low"
                >
              ).map((severity) => (
                <Button
                  key={severity}
                  onClick={() => setFilter(severity)}
                  size="sm"
                  variant={filter === severity ? "default" : "outline"}
                  className="capitalize"
                >
                  {severity}
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {filteredEvents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Activity className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No security events found</p>
              </div>
            ) : (
              filteredEvents.map((event) => (
                <div
                  key={event.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors hover:bg-gray-50 ${
                    selectedEvent?.id === event.id ? "ring-2 ring-blue-500" : ""
                  }`}
                  onClick={() => setSelectedEvent(event)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <Badge
                        className={`${getSeverityColor(event.severity)} border`}
                      >
                        {getSeverityIcon(event.severity)}
                        <span className="ml-1 capitalize">
                          {event.severity}
                        </span>
                      </Badge>
                      <div>
                        <p className="font-medium text-sm">
                          {event.description}
                        </p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                          <span className="flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            {formatTimestamp(event.timestamp)}
                          </span>
                          {event.ipAddress && (
                            <span className="flex items-center">
                              <Globe className="w-3 h-3 mr-1" />
                              {event.ipAddress}
                            </span>
                          )}
                          {event.location && (
                            <span className="flex items-center">
                              <Wifi className="w-3 h-3 mr-1" />
                              {event.location}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Event Details Modal */}
      {selectedEvent && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Event Details</CardTitle>
              <Button
                onClick={() => setSelectedEvent(null)}
                size="sm"
                variant="outline"
              >
                Close
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">
                    Event ID
                  </label>
                  <p className="font-mono text-sm">{selectedEvent.id}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">
                    Type
                  </label>
                  <p className="capitalize">
                    {selectedEvent.type.replace("_", " ")}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">
                    Severity
                  </label>
                  <Badge
                    className={`${getSeverityColor(selectedEvent.severity)} border`}
                  >
                    {getSeverityIcon(selectedEvent.severity)}
                    <span className="ml-1 capitalize">
                      {selectedEvent.severity}
                    </span>
                  </Badge>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">
                    Timestamp
                  </label>
                  <p>{formatTimestamp(selectedEvent.timestamp)}</p>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-600">
                  Description
                </label>
                <p className="mt-1">{selectedEvent.description}</p>
              </div>

              {selectedEvent.userAgent && (
                <div>
                  <label className="text-sm font-medium text-gray-600">
                    User Agent
                  </label>
                  <p className="font-mono text-xs bg-gray-100 p-2 rounded mt-1">
                    {selectedEvent.userAgent}
                  </p>
                </div>
              )}

              {selectedEvent.metadata && (
                <div>
                  <label className="text-sm font-medium text-gray-600">
                    Metadata
                  </label>
                  <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
                    {JSON.stringify(selectedEvent.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Last Updated */}
      {metrics?.lastUpdated && (
        <div className="text-xs text-gray-500 text-center">
          Last updated: {formatTimestamp(metrics.lastUpdated)}
        </div>
      )}
    </div>
  );
}

export default SecurityMonitor;
