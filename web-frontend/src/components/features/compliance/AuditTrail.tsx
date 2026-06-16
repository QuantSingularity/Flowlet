import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  Download,
  Edit,
  Eye,
  FileText,
  Filter,
  Globe,
  Key,
  Monitor,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Shield,
  Smartphone,
  User,
  XCircle,
} from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DatePicker } from "@/components/ui/date-picker";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface AuditEvent {
  id: string;
  timestamp: string;
  eventType:
    | "authentication"
    | "authorization"
    | "data_access"
    | "data_modification"
    | "system_access"
    | "configuration_change"
    | "security_event"
    | "compliance_event";
  action: string;
  resource: string;
  userId: string;
  userName: string;
  userRole: string;
  sourceIp: string;
  userAgent: string;
  location?: {
    country: string;
    city: string;
    coordinates?: { lat: number; lng: number };
  };
  deviceInfo?: {
    type: "desktop" | "mobile" | "tablet" | "api";
    browser?: string;
    os?: string;
  };
  outcome: "success" | "failure" | "warning" | "info";
  riskLevel: "low" | "medium" | "high" | "critical";
  details: Record<string, any>;
  metadata?: {
    sessionId?: string;
    requestId?: string;
    correlationId?: string;
    tags?: string[];
  };
  complianceRelevant: boolean;
  retentionPeriod: number; // in days
}

interface AuditFilter {
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
  eventTypes: string[];
  outcomes: string[];
  riskLevels: string[];
  users: string[];
  resources: string[];
  searchTerm: string;
  complianceOnly: boolean;
}

interface AuditReport {
  id: string;
  name: string;
  description: string;
  generatedAt: string;
  period: {
    start: string;
    end: string;
  };
  filters: AuditFilter;
  totalEvents: number;
  criticalEvents: number;
  failureRate: number;
  topUsers: Array<{ userId: string; userName: string; eventCount: number }>;
  topResources: Array<{ resource: string; eventCount: number }>;
  complianceEvents: number;
  status: "generating" | "completed" | "failed";
}

interface AuditTrailProps {
  events?: AuditEvent[];
  reports?: AuditReport[];
  onEventSearch?: (filters: AuditFilter) => Promise<AuditEvent[]>;
  onEventExport?: (
    filters: AuditFilter,
    format: "csv" | "json" | "pdf",
  ) => Promise<Blob>;
  onReportGenerate?: (config: Partial<AuditReport>) => Promise<void>;
  onReportExport?: (reportId: string) => Promise<Blob>;
  onEventDetails?: (eventId: string) => Promise<AuditEvent>;
  realTimeEnabled?: boolean;
  retentionPolicyDays?: number;
  className?: string;
}

interface ComponentState {
  activeTab: string;
  selectedEvent: AuditEvent | null;
  selectedReport: AuditReport | null;
  filters: AuditFilter;
  isSearching: boolean;
  isExporting: boolean;
  isGenerating: boolean;
  error: string | null;
  success: string | null;
  showAdvancedFilters: boolean;
  showEventDetails: boolean;
  showReportConfig: boolean;
  newReportName: string;
  newReportDescription: string;
}

export function AuditTrail({
  events = [],
  reports = [],
  onEventSearch,
  onEventExport,
  onReportGenerate,
  onReportExport,
  onEventDetails,
  realTimeEnabled = true,
  retentionPolicyDays = 2555, // 7 years default for financial compliance
  className = "",
}: AuditTrailProps) {
  const [state, setState] = useState<ComponentState>({
    activeTab: "events",
    selectedEvent: null,
    selectedReport: null,
    filters: {
      dateRange: {
        start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // Last 7 days
        end: new Date(),
      },
      eventTypes: [],
      outcomes: [],
      riskLevels: [],
      users: [],
      resources: [],
      searchTerm: "",
      complianceOnly: false,
    },
    isSearching: false,
    isExporting: false,
    isGenerating: false,
    error: null,
    success: null,
    showAdvancedFilters: false,
    showEventDetails: false,
    showReportConfig: false,
    newReportName: "",
    newReportDescription: "",
  });

  // Calculate audit metrics
  const auditMetrics = useMemo(() => {
    const totalEvents = events.length;
    const criticalEvents = events.filter(
      (e) => e.riskLevel === "critical",
    ).length;
    const failedEvents = events.filter((e) => e.outcome === "failure").length;
    const complianceEvents = events.filter((e) => e.complianceRelevant).length;

    const eventsByType = events.reduce(
      (acc, event) => {
        acc[event.eventType] = (acc[event.eventType] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    const eventsByUser = events.reduce(
      (acc, event) => {
        const key = `${event.userId}:${event.userName}`;
        acc[key] = (acc[key] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    const eventsByHour = events.reduce(
      (acc, event) => {
        const hour = new Date(event.timestamp).getHours();
        acc[hour] = (acc[hour] || 0) + 1;
        return acc;
      },
      {} as Record<number, number>,
    );

    return {
      totalEvents,
      criticalEvents,
      failedEvents,
      complianceEvents,
      failureRate: totalEvents > 0 ? (failedEvents / totalEvents) * 100 : 0,
      eventsByType,
      eventsByUser,
      eventsByHour,
      topUsers: Object.entries(eventsByUser)
        .map(([key, count]) => {
          const [userId, userName] = key.split(":");
          return { userId, userName, eventCount: count };
        })
        .sort((a, b) => b.eventCount - a.eventCount)
        .slice(0, 10),
      topEventTypes: Object.entries(eventsByType)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5),
    };
  }, [events]);

  // Filter events based on current filters
  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      // Date range filter
      if (
        state.filters.dateRange.start &&
        new Date(event.timestamp) < state.filters.dateRange.start
      ) {
        return false;
      }
      if (
        state.filters.dateRange.end &&
        new Date(event.timestamp) > state.filters.dateRange.end
      ) {
        return false;
      }

      // Event type filter
      if (
        state.filters.eventTypes.length > 0 &&
        !state.filters.eventTypes.includes(event.eventType)
      ) {
        return false;
      }

      // Outcome filter
      if (
        state.filters.outcomes.length > 0 &&
        !state.filters.outcomes.includes(event.outcome)
      ) {
        return false;
      }

      // Risk level filter
      if (
        state.filters.riskLevels.length > 0 &&
        !state.filters.riskLevels.includes(event.riskLevel)
      ) {
        return false;
      }

      // User filter
      if (
        state.filters.users.length > 0 &&
        !state.filters.users.includes(event.userId)
      ) {
        return false;
      }

      // Resource filter
      if (
        state.filters.resources.length > 0 &&
        !state.filters.resources.some((r) => event.resource.includes(r))
      ) {
        return false;
      }

      // Search term filter
      if (state.filters.searchTerm) {
        const searchLower = state.filters.searchTerm.toLowerCase();
        const searchableText =
          `${event.action} ${event.resource} ${event.userName} ${event.details}`.toLowerCase();
        if (!searchableText.includes(searchLower)) {
          return false;
        }
      }

      // Compliance filter
      if (state.filters.complianceOnly && !event.complianceRelevant) {
        return false;
      }

      return true;
    });
  }, [events, state.filters]);

  // Handle search
  const handleSearch = useCallback(async () => {
    setState((prev) => ({ ...prev, isSearching: true, error: null }));

    try {
      if (onEventSearch) {
        const results = await onEventSearch(state.filters);
        setState((prev) => ({
          ...prev,
          success: `Found ${results.length} events`,
        }));
      }
    } catch (_error) {
      setState((prev) => ({ ...prev, error: "Failed to search events" }));
    } finally {
      setState((prev) => ({ ...prev, isSearching: false }));
    }
  }, [onEventSearch, state.filters]);

  // Handle export
  const handleExport = useCallback(
    async (format: "csv" | "json" | "pdf") => {
      setState((prev) => ({ ...prev, isExporting: true, error: null }));

      try {
        if (onEventExport) {
          const blob = await onEventExport(state.filters, format);
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `audit-trail-${new Date().toISOString().split("T")[0]}.${format}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          setTimeout(() => URL.revokeObjectURL(url), 100);

          setState((prev) => ({
            ...prev,
            success: "Export completed successfully",
          }));
        }
      } catch (_error) {
        setState((prev) => ({ ...prev, error: "Failed to export events" }));
      } finally {
        setState((prev) => ({ ...prev, isExporting: false }));
      }
    },
    [onEventExport, state.filters],
  );

  // Handle report generation
  const handleReportGenerate = useCallback(async () => {
    if (!state.newReportName.trim()) {
      setState((prev) => ({ ...prev, error: "Report name is required" }));
      return;
    }

    setState((prev) => ({ ...prev, isGenerating: true, error: null }));

    try {
      if (onReportGenerate) {
        await onReportGenerate({
          name: state.newReportName,
          description: state.newReportDescription,
          filters: state.filters,
          period: {
            start: state.filters.dateRange.start?.toISOString() || "",
            end: state.filters.dateRange.end?.toISOString() || "",
          },
        });

        setState((prev) => ({
          ...prev,
          success: "Report generation started",
          showReportConfig: false,
          newReportName: "",
          newReportDescription: "",
        }));
      }
    } catch (_error) {
      setState((prev) => ({ ...prev, error: "Failed to generate report" }));
    } finally {
      setState((prev) => ({ ...prev, isGenerating: false }));
    }
  }, [
    onReportGenerate,
    state.filters,
    state.newReportName,
    state.newReportDescription,
  ]);

  // Handle event details
  const handleEventDetails = useCallback(
    async (eventId: string) => {
      try {
        if (onEventDetails) {
          const event = await onEventDetails(eventId);
          setState((prev) => ({
            ...prev,
            selectedEvent: event,
            showEventDetails: true,
          }));
        } else {
          const event = events.find((e) => e.id === eventId);
          if (event) {
            setState((prev) => ({
              ...prev,
              selectedEvent: event,
              showEventDetails: true,
            }));
          }
        }
      } catch (_error) {
        setState((prev) => ({
          ...prev,
          error: "Failed to load event details",
        }));
      }
    },
    [onEventDetails, events],
  );

  const getEventTypeIcon = (type: string) => {
    switch (type) {
      case "authentication":
        return <Key className="w-4 h-4" />;
      case "authorization":
        return <Shield className="w-4 h-4" />;
      case "data_access":
        return <Eye className="w-4 h-4" />;
      case "data_modification":
        return <Edit className="w-4 h-4" />;
      case "system_access":
        return <Monitor className="w-4 h-4" />;
      case "configuration_change":
        return <Settings className="w-4 h-4" />;
      case "security_event":
        return <AlertTriangle className="w-4 h-4" />;
      case "compliance_event":
        return <FileText className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const getOutcomeColor = (outcome: string) => {
    switch (outcome) {
      case "success":
        return "bg-green-100 text-green-600";
      case "failure":
        return "bg-red-100 text-red-600";
      case "warning":
        return "bg-yellow-100 text-yellow-600";
      case "info":
        return "bg-blue-100 text-blue-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case "critical":
        return "bg-red-100 text-red-600";
      case "high":
        return "bg-orange-100 text-orange-600";
      case "medium":
        return "bg-yellow-100 text-yellow-600";
      case "low":
        return "bg-green-100 text-green-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const getDeviceIcon = (type?: string) => {
    switch (type) {
      case "mobile":
        return <Smartphone className="w-4 h-4" />;
      case "tablet":
        return <Monitor className="w-4 h-4" />;
      case "api":
        return <Database className="w-4 h-4" />;
      default:
        return <Monitor className="w-4 h-4" />;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center">
              <FileText className="w-6 h-6 mr-3 text-blue-600" />
              Audit Trail Management
            </div>
            <div className="flex items-center space-x-2">
              <Badge className="bg-blue-100 text-blue-600">
                <Clock className="w-3 h-3 mr-1" />
                {filteredEvents.length} Events
              </Badge>
              {realTimeEnabled && (
                <Badge className="bg-green-100 text-green-600">
                  <RefreshCw className="w-3 h-3 mr-1" />
                  Real-time
                </Badge>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">
            Comprehensive audit logging and monitoring for compliance and
            security analysis. Retention period: {retentionPolicyDays} days.
          </p>
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

      {auditMetrics.criticalEvents > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <strong>Critical Alert:</strong> {auditMetrics.criticalEvents}{" "}
            critical security events detected.
          </AlertDescription>
        </Alert>
      )}

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="space-y-4">
            <div className="flex space-x-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Search events, actions, resources, users..."
                    value={state.filters.searchTerm}
                    onChange={(e) =>
                      setState((prev) => ({
                        ...prev,
                        filters: {
                          ...prev.filters,
                          searchTerm: e.target.value,
                        },
                      }))
                    }
                    className="pl-10"
                  />
                </div>
              </div>
              <Button
                onClick={() =>
                  setState((prev) => ({
                    ...prev,
                    showAdvancedFilters: !prev.showAdvancedFilters,
                  }))
                }
                variant="outline"
              >
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </Button>
              <Button onClick={handleSearch} disabled={state.isSearching}>
                <Search
                  className={`w-4 h-4 mr-2 ${state.isSearching ? "animate-spin" : ""}`}
                />
                Search
              </Button>
            </div>

            {state.showAdvancedFilters && (
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <Label className="text-sm">Start Date</Label>
                  <DatePicker
                    date={state.filters.dateRange.start ?? undefined}
                    onDateChange={(date) =>
                      setState((prev) => ({
                        ...prev,
                        filters: {
                          ...prev.filters,
                          dateRange: {
                            ...prev.filters.dateRange,
                            start: date ?? null,
                          },
                        },
                      }))
                    }
                  />
                </div>
                <div>
                  <Label className="text-sm">End Date</Label>
                  <DatePicker
                    date={state.filters.dateRange.end ?? undefined}
                    onDateChange={(date) =>
                      setState((prev) => ({
                        ...prev,
                        filters: {
                          ...prev.filters,
                          dateRange: {
                            ...prev.filters.dateRange,
                            end: date ?? null,
                          },
                        },
                      }))
                    }
                  />
                </div>
                <div>
                  <Label className="text-sm">Event Type</Label>
                  <Select
                    value={state.filters.eventTypes[0] || "all"}
                    onValueChange={(value) =>
                      setState((prev) => ({
                        ...prev,
                        filters: {
                          ...prev.filters,
                          eventTypes: value === "all" ? [] : [value],
                        },
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="authentication">
                        Authentication
                      </SelectItem>
                      <SelectItem value="authorization">
                        Authorization
                      </SelectItem>
                      <SelectItem value="data_access">Data Access</SelectItem>
                      <SelectItem value="data_modification">
                        Data Modification
                      </SelectItem>
                      <SelectItem value="system_access">
                        System Access
                      </SelectItem>
                      <SelectItem value="configuration_change">
                        Configuration
                      </SelectItem>
                      <SelectItem value="security_event">
                        Security Event
                      </SelectItem>
                      <SelectItem value="compliance_event">
                        Compliance
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-sm">Outcome</Label>
                  <Select
                    value={state.filters.outcomes[0] || "all"}
                    onValueChange={(value) =>
                      setState((prev) => ({
                        ...prev,
                        filters: {
                          ...prev.filters,
                          outcomes: value === "all" ? [] : [value],
                        },
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All outcomes" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Outcomes</SelectItem>
                      <SelectItem value="success">Success</SelectItem>
                      <SelectItem value="failure">Failure</SelectItem>
                      <SelectItem value="warning">Warning</SelectItem>
                      <SelectItem value="info">Info</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-sm">Risk Level</Label>
                  <Select
                    value={state.filters.riskLevels[0] || "all"}
                    onValueChange={(value) =>
                      setState((prev) => ({
                        ...prev,
                        filters: {
                          ...prev.filters,
                          riskLevels: value === "all" ? [] : [value],
                        },
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All levels" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Levels</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <Tabs
        value={state.activeTab}
        onValueChange={(value) =>
          setState((prev) => ({ ...prev, activeTab: value }))
        }
      >
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="events">Events</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Events Tab */}
        <TabsContent value="events">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">
                Audit Events ({filteredEvents.length})
              </h3>
              <div className="flex space-x-2">
                <Button
                  onClick={() => handleExport("csv")}
                  disabled={state.isExporting}
                  size="sm"
                  variant="outline"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export CSV
                </Button>
                <Button
                  onClick={() => handleExport("json")}
                  disabled={state.isExporting}
                  size="sm"
                  variant="outline"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export JSON
                </Button>
              </div>
            </div>

            <div className="grid gap-2">
              {filteredEvents.slice(0, 100).map((event) => (
                <Card
                  key={event.id}
                  className="hover:shadow-md transition-shadow"
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getEventTypeIcon(event.eventType)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <h4 className="font-medium truncate">
                              {event.action}
                            </h4>
                            <Badge className={getOutcomeColor(event.outcome)}>
                              {event.outcome}
                            </Badge>
                            <Badge
                              className={getRiskLevelColor(event.riskLevel)}
                            >
                              {event.riskLevel}
                            </Badge>
                            {event.complianceRelevant && (
                              <Badge className="bg-purple-100 text-purple-600">
                                Compliance
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-1">
                            <span className="flex items-center">
                              <User className="w-3 h-3 mr-1" />
                              {event.userName}
                            </span>
                            <span className="flex items-center">
                              <Database className="w-3 h-3 mr-1" />
                              {event.resource}
                            </span>
                            <span className="flex items-center">
                              <Globe className="w-3 h-3 mr-1" />
                              {event.sourceIp}
                            </span>
                            {event.deviceInfo && (
                              <span className="flex items-center">
                                {getDeviceIcon(event.deviceInfo.type)}
                                <span className="ml-1">
                                  {event.deviceInfo.type}
                                </span>
                              </span>
                            )}
                          </div>
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <Clock className="w-3 h-3" />
                            <span>
                              {new Date(event.timestamp).toLocaleString()}
                            </span>
                            {event.location && (
                              <>
                                <span>•</span>
                                <span>
                                  {event.location.city},{" "}
                                  {event.location.country}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                      <Button
                        onClick={() => handleEventDetails(event.id)}
                        size="sm"
                        variant="outline"
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        Details
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {filteredEvents.length === 0 && (
              <Card>
                <CardContent className="p-6 text-center">
                  <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Events Found
                  </h3>
                  <p className="text-sm text-gray-600">
                    No audit events match your current filters. Try adjusting
                    your search criteria.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        Total Events
                      </p>
                      <p className="text-2xl font-bold">
                        {auditMetrics.totalEvents}
                      </p>
                    </div>
                    <FileText className="w-8 h-8 text-blue-500" />
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
                        {auditMetrics.criticalEvents}
                      </p>
                    </div>
                    <AlertTriangle className="w-8 h-8 text-red-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        Failure Rate
                      </p>
                      <p className="text-2xl font-bold text-orange-600">
                        {auditMetrics.failureRate.toFixed(1)}%
                      </p>
                    </div>
                    <XCircle className="w-8 h-8 text-orange-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        Compliance Events
                      </p>
                      <p className="text-2xl font-bold text-purple-600">
                        {auditMetrics.complianceEvents}
                      </p>
                    </div>
                    <Shield className="w-8 h-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Top Users */}
            <Card>
              <CardHeader>
                <CardTitle>Top Active Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {auditMetrics.topUsers.slice(0, 10).map((user, index) => (
                    <div
                      key={user.userId}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium">
                          #{index + 1}
                        </span>
                        <User className="w-4 h-4 text-gray-400" />
                        <span className="text-sm">{user.userName}</span>
                      </div>
                      <Badge className="bg-blue-100 text-blue-600">
                        {user.eventCount} events
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Event Types Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Event Types Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {auditMetrics.topEventTypes.map(([type, count]) => (
                    <div
                      key={type}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded"
                    >
                      <div className="flex items-center space-x-2">
                        {getEventTypeIcon(type)}
                        <span className="text-sm capitalize">
                          {type.replace("_", " ")}
                        </span>
                      </div>
                      <Badge className="bg-green-100 text-green-600">
                        {count} events
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Reports Tab */}
        <TabsContent value="reports">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">Audit Reports</h3>
              <Button
                onClick={() =>
                  setState((prev) => ({ ...prev, showReportConfig: true }))
                }
                size="sm"
              >
                <Plus className="w-4 h-4 mr-2" />
                Generate Report
              </Button>
            </div>

            <div className="grid gap-4">
              {reports.map((report) => (
                <Card key={report.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{report.name}</h4>
                        <p className="text-sm text-gray-600 mb-2">
                          {report.description}
                        </p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span>
                            Generated:{" "}
                            {new Date(report.generatedAt).toLocaleDateString()}
                          </span>
                          <span>
                            Period:{" "}
                            {new Date(report.period.start).toLocaleDateString()}{" "}
                            - {new Date(report.period.end).toLocaleDateString()}
                          </span>
                          <span>Events: {report.totalEvents}</span>
                          <span>Critical: {report.criticalEvents}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge
                          className={
                            report.status === "completed"
                              ? "bg-green-100 text-green-600"
                              : report.status === "generating"
                                ? "bg-yellow-100 text-yellow-600"
                                : "bg-red-100 text-red-600"
                          }
                        >
                          {report.status}
                        </Badge>
                        {report.status === "completed" && (
                          <Button
                            onClick={() => {
                              if (onReportExport) {
                                onReportExport(report.id);
                              }
                            }}
                            size="sm"
                            variant="outline"
                          >
                            <Download className="w-3 h-3 mr-1" />
                            Export
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Audit Trail Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium">
                      Retention Policy
                    </Label>
                    <p className="text-xs text-gray-600 mb-2">
                      How long audit events are stored
                    </p>
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl font-bold">
                        {retentionPolicyDays}
                      </span>
                      <span className="text-sm text-gray-600">days</span>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">
                      Real-time Monitoring
                    </Label>
                    <p className="text-xs text-gray-600 mb-2">
                      Enable real-time event streaming
                    </p>
                    <Badge
                      className={
                        realTimeEnabled
                          ? "bg-green-100 text-green-600"
                          : "bg-gray-100 text-gray-600"
                      }
                    >
                      {realTimeEnabled ? "Enabled" : "Disabled"}
                    </Badge>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium">
                      Event Categories
                    </Label>
                    <p className="text-xs text-gray-600 mb-2">
                      Types of events being logged
                    </p>
                    <div className="space-y-1">
                      {[
                        "Authentication",
                        "Authorization",
                        "Data Access",
                        "System Access",
                        "Security Events",
                        "Compliance",
                      ].map((category) => (
                        <div
                          key={category}
                          className="flex items-center justify-between"
                        >
                          <span className="text-sm">{category}</span>
                          <Badge className="bg-green-100 text-green-600">
                            Active
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
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
                      <span className="text-gray-600">Timestamp:</span>
                      <span>
                        {new Date(
                          state.selectedEvent.timestamp,
                        ).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Type:</span>
                      <span className="capitalize">
                        {state.selectedEvent.eventType.replace("_", " ")}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Action:</span>
                      <span>{state.selectedEvent.action}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Resource:</span>
                      <span>{state.selectedEvent.resource}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium">
                    User Information
                  </Label>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">User ID:</span>
                      <span>{state.selectedEvent.userId}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Name:</span>
                      <span>{state.selectedEvent.userName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Role:</span>
                      <span>{state.selectedEvent.userRole}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">IP Address:</span>
                      <span className="font-mono">
                        {state.selectedEvent.sourceIp}
                      </span>
                    </div>
                    {state.selectedEvent.location && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Location:</span>
                        <span>
                          {state.selectedEvent.location.city},{" "}
                          {state.selectedEvent.location.country}
                        </span>
                      </div>
                    )}
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

              {state.selectedEvent.metadata && (
                <div>
                  <Label className="text-sm font-medium">Metadata</Label>
                  <pre className="mt-2 p-3 bg-gray-50 rounded text-xs overflow-x-auto">
                    {JSON.stringify(state.selectedEvent.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Report Configuration Modal */}
      {state.showReportConfig && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Generate Audit Report</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Report Name</Label>
                <Input
                  value={state.newReportName}
                  onChange={(e) =>
                    setState((prev) => ({
                      ...prev,
                      newReportName: e.target.value,
                    }))
                  }
                  placeholder="Enter report name"
                />
              </div>
              <div>
                <Label>Description</Label>
                <Input
                  value={state.newReportDescription}
                  onChange={(e) =>
                    setState((prev) => ({
                      ...prev,
                      newReportDescription: e.target.value,
                    }))
                  }
                  placeholder="Enter report description"
                />
              </div>
              <div className="flex space-x-2">
                <Button
                  onClick={handleReportGenerate}
                  disabled={state.isGenerating || !state.newReportName.trim()}
                >
                  {state.isGenerating ? "Generating..." : "Generate Report"}
                </Button>
                <Button
                  onClick={() =>
                    setState((prev) => ({
                      ...prev,
                      showReportConfig: false,
                      newReportName: "",
                      newReportDescription: "",
                    }))
                  }
                  variant="outline"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default AuditTrail;
