import {
  Activity,
  AlertTriangle,
  BarChart3,
  Brain,
  CheckCircle,
  Clock,
  Database,
  Download,
  Edit,
  Eye,
  Flag,
  Mail,
  Network,
  Play,
  Plus,
  Radar,
  Search,
  Settings,
  Shield,
  StopCircle,
  Target,
  Trash2,
  Users,
  Zap,
} from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
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

interface ThreatSignature {
  id: string;
  name: string;
  description: string;
  category:
    | "malware"
    | "phishing"
    | "ddos"
    | "intrusion"
    | "data_exfiltration"
    | "insider_threat"
    | "apt"
    | "custom";
  severity: "low" | "medium" | "high" | "critical";
  confidence: number; // 0-100
  patterns: ThreatPattern[];
  indicators: ThreatIndicator[];
  mitreTactics: string[];
  mitreAttackIds: string[];
  killChainPhases: string[];
  createdBy: string;
  createdAt: string;
  lastUpdated: string;
  version: string;
  isActive: boolean;
  falsePositiveRate: number;
  detectionCount: number;
  lastDetection?: string;
}

interface ThreatPattern {
  id: string;
  type: "network" | "file" | "registry" | "process" | "behavior" | "anomaly";
  pattern: string;
  weight: number; // 0-1
  description: string;
  regex?: string;
  conditions?: Record<string, any>;
}

interface ThreatIndicator {
  id: string;
  type:
    | "ip"
    | "domain"
    | "url"
    | "hash"
    | "email"
    | "file_path"
    | "registry_key"
    | "process_name";
  value: string;
  context: string;
  confidence: number;
  source: string;
  tags: string[];
}

interface ThreatDetection {
  id: string;
  signatureId: string;
  signatureName: string;
  timestamp: string;
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;
  status:
    "active" | "investigating" | "contained" | "resolved" | "false_positive";
  source: {
    type: "network" | "endpoint" | "email" | "web" | "database" | "application";
    identifier: string;
    location: string;
  };
  target: {
    type: "user" | "system" | "application" | "data";
    identifier: string;
    criticality: "low" | "medium" | "high" | "critical";
  };
  matchedPatterns: string[];
  matchedIndicators: string[];
  riskScore: number; // 0-100
  businessImpact: "none" | "low" | "medium" | "high" | "critical";
  attackVector: string;
  killChainPhase: string;
  mitreTactic: string;
  mitreAttackId: string;
  evidence: ThreatEvidence[];
  timeline: ThreatTimelineEvent[];
  response: ThreatResponse;
  correlatedDetections: string[];
}

interface ThreatEvidence {
  id: string;
  type:
    | "network_traffic"
    | "file_activity"
    | "process_execution"
    | "registry_change"
    | "user_behavior";
  timestamp: string;
  description: string;
  data: Record<string, any>;
  hash: string;
  preserved: boolean;
}

interface ThreatTimelineEvent {
  id: string;
  timestamp: string;
  event: string;
  actor: string;
  details: string;
  severity: "info" | "warning" | "critical";
}

interface ThreatResponse {
  id: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  actions: ThreatResponseAction[];
  assignedTo?: string;
  startedAt?: string;
  completedAt?: string;
  notes: string[];
  escalated: boolean;
  containmentLevel: "none" | "partial" | "full";
}

interface ThreatResponseAction {
  id: string;
  type:
    | "isolate"
    | "block"
    | "quarantine"
    | "monitor"
    | "alert"
    | "investigate"
    | "remediate";
  target: string;
  status: "pending" | "executing" | "completed" | "failed";
  timestamp: string;
  result?: string;
  automated: boolean;
}

interface ThreatHunt {
  id: string;
  name: string;
  description: string;
  hypothesis: string;
  status: "planning" | "active" | "completed" | "cancelled";
  priority: "low" | "medium" | "high" | "critical";
  huntType: "proactive" | "reactive" | "intelligence_driven";
  scope: {
    timeRange: { start: string; end: string };
    systems: string[];
    dataTypes: string[];
    indicators: string[];
  };
  queries: ThreatHuntQuery[];
  findings: ThreatHuntFinding[];
  createdBy: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  progress: number; // 0-100
}

interface ThreatHuntQuery {
  id: string;
  name: string;
  query: string;
  platform: "siem" | "edr" | "network" | "cloud" | "custom";
  status: "pending" | "running" | "completed" | "failed";
  results?: any[];
  executedAt?: string;
}

interface ThreatHuntFinding {
  id: string;
  title: string;
  description: string;
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;
  evidence: string[];
  recommendations: string[];
  createdAt: string;
}

interface ThreatDetectionProps {
  signatures?: ThreatSignature[];
  detections?: ThreatDetection[];
  hunts?: ThreatHunt[];
  onSignatureCreate?: (
    signature: Omit<ThreatSignature, "id" | "createdAt" | "detectionCount">,
  ) => Promise<void>;
  onSignatureUpdate?: (
    signatureId: string,
    updates: Partial<ThreatSignature>,
  ) => Promise<void>;
  onSignatureDelete?: (signatureId: string) => Promise<void>;
  onDetectionInvestigate?: (detectionId: string) => Promise<void>;
  onDetectionRespond?: (
    detectionId: string,
    actions: ThreatResponseAction[],
  ) => Promise<void>;
  onHuntCreate?: (
    hunt: Omit<ThreatHunt, "id" | "createdAt" | "progress">,
  ) => Promise<void>;
  onHuntStart?: (huntId: string) => Promise<void>;
  onHuntStop?: (huntId: string) => Promise<void>;
  onExportReport?: (
    type: "detections" | "signatures" | "hunts",
    filters: any,
  ) => Promise<Blob>;
  realTimeDetection?: boolean;
  className?: string;
}

interface ComponentState {
  activeTab: string;
  selectedSignature: ThreatSignature | null;
  selectedDetection: ThreatDetection | null;
  selectedHunt: ThreatHunt | null;
  searchTerm: string;
  filterSeverity: string;
  filterStatus: string;
  filterCategory: string;
  timeRange: "1h" | "24h" | "7d" | "30d";
  showSignatureEditor: boolean;
  showDetectionDetails: boolean;
  showHuntEditor: boolean;
  showResponseDialog: boolean;
  isCreating: boolean;
  isInvestigating: boolean;
  isResponding: boolean;
  isExporting: boolean;
  error: string | null;
  success: string | null;
  newSignature: Partial<ThreatSignature>;
  newHunt: Partial<ThreatHunt>;
  responseActions: ThreatResponseAction[];
}

export function ThreatDetection({
  signatures = [],
  detections = [],
  hunts = [],
  onSignatureCreate,
  onSignatureUpdate,
  onSignatureDelete,
  onDetectionInvestigate,
  onDetectionRespond,
  onHuntCreate,
  onHuntStart,
  onHuntStop,
  onExportReport,
  realTimeDetection = true,
  className = "",
}: ThreatDetectionProps) {
  const [state, setState] = useState<ComponentState>({
    activeTab: "overview",
    selectedSignature: null,
    selectedDetection: null,
    selectedHunt: null,
    searchTerm: "",
    filterSeverity: "all",
    filterStatus: "all",
    filterCategory: "all",
    timeRange: "24h",
    showSignatureEditor: false,
    showDetectionDetails: false,
    showHuntEditor: false,
    showResponseDialog: false,
    isCreating: false,
    isInvestigating: false,
    isResponding: false,
    isExporting: false,
    error: null,
    success: null,
    newSignature: {
      name: "",
      description: "",
      category: "malware",
      severity: "medium",
      confidence: 80,
      patterns: [],
      indicators: [],
      mitreTactics: [],
      mitreAttackIds: [],
      killChainPhases: [],
      createdBy: "current-user",
      version: "1.0",
      isActive: true,
      falsePositiveRate: 0,
    },
    newHunt: {
      name: "",
      description: "",
      hypothesis: "",
      status: "planning",
      priority: "medium",
      huntType: "proactive",
      scope: {
        timeRange: { start: "", end: "" },
        systems: [],
        dataTypes: [],
        indicators: [],
      },
      queries: [],
      findings: [],
      createdBy: "current-user",
    },
    responseActions: [],
  });

  // Calculate threat metrics
  const threatMetrics = useMemo(() => {
    const now = new Date();
    const timeRangeMs = {
      "1h": 60 * 60 * 1000,
      "24h": 24 * 60 * 60 * 1000,
      "7d": 7 * 24 * 60 * 60 * 1000,
      "30d": 30 * 24 * 60 * 60 * 1000,
    }[state.timeRange];

    const cutoffTime = new Date(now.getTime() - timeRangeMs);
    const recentDetections = detections.filter(
      (d) => new Date(d.timestamp) > cutoffTime,
    );

    const totalDetections = recentDetections.length;
    const criticalDetections = recentDetections.filter(
      (d) => d.severity === "critical",
    ).length;
    const activeDetections = recentDetections.filter(
      (d) => d.status === "active",
    ).length;
    const containedDetections = recentDetections.filter(
      (d) => d.status === "contained",
    ).length;

    const activeSignatures = signatures.filter((s) => s.isActive).length;
    const activeHunts = hunts.filter((h) => h.status === "active").length;

    const detectionsByCategory = recentDetections.reduce(
      (acc, detection) => {
        const signature = signatures.find(
          (s) => s.id === detection.signatureId,
        );
        if (signature) {
          acc[signature.category] = (acc[signature.category] || 0) + 1;
        }
        return acc;
      },
      {} as Record<string, number>,
    );

    const detectionsBySeverity = recentDetections.reduce(
      (acc, detection) => {
        acc[detection.severity] = (acc[detection.severity] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    const detectionsByKillChain = recentDetections.reduce(
      (acc, detection) => {
        acc[detection.killChainPhase] =
          (acc[detection.killChainPhase] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    const averageRiskScore =
      recentDetections.length > 0
        ? recentDetections.reduce((sum, d) => sum + d.riskScore, 0) /
          recentDetections.length
        : 0;

    const averageConfidence =
      recentDetections.length > 0
        ? recentDetections.reduce((sum, d) => sum + d.confidence, 0) /
          recentDetections.length
        : 0;

    const containmentRate =
      totalDetections > 0 ? (containedDetections / totalDetections) * 100 : 0;

    return {
      totalDetections,
      criticalDetections,
      activeDetections,
      containedDetections,
      activeSignatures,
      activeHunts,
      detectionsByCategory,
      detectionsBySeverity,
      detectionsByKillChain,
      averageRiskScore,
      averageConfidence,
      containmentRate,
    };
  }, [detections, signatures, hunts, state.timeRange]);

  // Filter detections
  const filteredDetections = useMemo(() => {
    return detections.filter((detection) => {
      const signature = signatures.find((s) => s.id === detection.signatureId);

      const matchesSearch =
        detection.signatureName
          .toLowerCase()
          .includes(state.searchTerm.toLowerCase()) ||
        detection.source.identifier
          .toLowerCase()
          .includes(state.searchTerm.toLowerCase()) ||
        detection.target.identifier
          .toLowerCase()
          .includes(state.searchTerm.toLowerCase());

      const matchesSeverity =
        state.filterSeverity === "all" ||
        detection.severity === state.filterSeverity;
      const matchesStatus =
        state.filterStatus === "all" || detection.status === state.filterStatus;
      const matchesCategory =
        state.filterCategory === "all" ||
        (signature && signature.category === state.filterCategory);

      return (
        matchesSearch && matchesSeverity && matchesStatus && matchesCategory
      );
    });
  }, [
    detections,
    signatures,
    state.searchTerm,
    state.filterSeverity,
    state.filterStatus,
    state.filterCategory,
  ]);

  // Handle signature creation
  const _handleSignatureCreate = useCallback(async () => {
    if (!state.newSignature.name || !state.newSignature.description) {
      setState((prev) => ({
        ...prev,
        error: "Name and description are required",
      }));
      return;
    }

    setState((prev) => ({ ...prev, isCreating: true, error: null }));

    try {
      if (onSignatureCreate) {
        await onSignatureCreate(
          state.newSignature as Omit<
            ThreatSignature,
            "id" | "createdAt" | "detectionCount"
          >,
        );
        setState((prev) => ({
          ...prev,
          success: "Threat signature created successfully",
          showSignatureEditor: false,
          newSignature: {
            name: "",
            description: "",
            category: "malware",
            severity: "medium",
            confidence: 80,
            patterns: [],
            indicators: [],
            mitreTactics: [],
            mitreAttackIds: [],
            killChainPhases: [],
            createdBy: "current-user",
            version: "1.0",
            isActive: true,
            falsePositiveRate: 0,
          },
        }));
      }
    } catch (_error) {
      setState((prev) => ({
        ...prev,
        error: "Failed to create threat signature",
      }));
    } finally {
      setState((prev) => ({ ...prev, isCreating: false }));
    }
  }, [onSignatureCreate, state.newSignature]);

  // Handle detection investigation
  const handleDetectionInvestigate = useCallback(
    async (detectionId: string) => {
      setState((prev) => ({ ...prev, isInvestigating: true, error: null }));

      try {
        if (onDetectionInvestigate) {
          await onDetectionInvestigate(detectionId);
          setState((prev) => ({
            ...prev,
            success: "Investigation initiated successfully",
          }));
        }
      } catch (_error) {
        setState((prev) => ({
          ...prev,
          error: "Failed to initiate investigation",
        }));
      } finally {
        setState((prev) => ({ ...prev, isInvestigating: false }));
      }
    },
    [onDetectionInvestigate],
  );

  // Handle threat response
  const handleThreatResponse = useCallback(
    async (detectionId: string) => {
      if (state.responseActions.length === 0) {
        setState((prev) => ({
          ...prev,
          error: "Please select at least one response action",
        }));
        return;
      }

      setState((prev) => ({ ...prev, isResponding: true, error: null }));

      try {
        if (onDetectionRespond) {
          await onDetectionRespond(detectionId, state.responseActions);
          setState((prev) => ({
            ...prev,
            success: "Threat response initiated successfully",
            showResponseDialog: false,
            responseActions: [],
          }));
        }
      } catch (_error) {
        setState((prev) => ({
          ...prev,
          error: "Failed to initiate threat response",
        }));
      } finally {
        setState((prev) => ({ ...prev, isResponding: false }));
      }
    },
    [onDetectionRespond, state.responseActions],
  );

  // Handle hunt creation
  const _handleHuntCreate = useCallback(async () => {
    if (
      !state.newHunt.name ||
      !state.newHunt.description ||
      !state.newHunt.hypothesis
    ) {
      setState((prev) => ({
        ...prev,
        error: "Name, description, and hypothesis are required",
      }));
      return;
    }

    setState((prev) => ({ ...prev, isCreating: true, error: null }));

    try {
      if (onHuntCreate) {
        await onHuntCreate(
          state.newHunt as Omit<ThreatHunt, "id" | "createdAt" | "progress">,
        );
        setState((prev) => ({
          ...prev,
          success: "Threat hunt created successfully",
          showHuntEditor: false,
        }));
      }
    } catch (_error) {
      setState((prev) => ({ ...prev, error: "Failed to create threat hunt" }));
    } finally {
      setState((prev) => ({ ...prev, isCreating: false }));
    }
  }, [onHuntCreate, state.newHunt]);

  // Handle export
  const handleExport = useCallback(
    async (type: "detections" | "signatures" | "hunts") => {
      setState((prev) => ({ ...prev, isExporting: true, error: null }));

      try {
        if (onExportReport) {
          const filters = {
            timeRange: state.timeRange,
            severity: state.filterSeverity,
            status: state.filterStatus,
            category: state.filterCategory,
            search: state.searchTerm,
          };

          const blob = await onExportReport(type, filters);
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `threat-${type}-${new Date().toISOString().split("T")[0]}.csv`;
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
      state.filterStatus,
      state.filterCategory,
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
      case "active":
      case "planning":
        return "bg-red-100 text-red-600";
      case "investigating":
      case "in_progress":
        return "bg-yellow-100 text-yellow-600";
      case "contained":
      case "completed":
        return "bg-green-100 text-green-600";
      case "resolved":
        return "bg-blue-100 text-blue-600";
      case "false_positive":
      case "cancelled":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "malware":
        return <Target className="w-4 h-4" />;
      case "phishing":
        return <Mail className="w-4 h-4" />;
      case "ddos":
        return <Network className="w-4 h-4" />;
      case "intrusion":
        return <Shield className="w-4 h-4" />;
      case "data_exfiltration":
        return <Database className="w-4 h-4" />;
      case "insider_threat":
        return <Users className="w-4 h-4" />;
      case "apt":
        return <Brain className="w-4 h-4" />;
      case "custom":
        return <Settings className="w-4 h-4" />;
      default:
        return <AlertTriangle className="w-4 h-4" />;
    }
  };

  const getKillChainIcon = (phase: string) => {
    switch (phase.toLowerCase()) {
      case "reconnaissance":
        return <Eye className="w-4 h-4" />;
      case "weaponization":
        return <Zap className="w-4 h-4" />;
      case "delivery":
        return <Mail className="w-4 h-4" />;
      case "exploitation":
        return <Target className="w-4 h-4" />;
      case "installation":
        return <Download className="w-4 h-4" />;
      case "command_and_control":
        return <Network className="w-4 h-4" />;
      case "actions_on_objectives":
        return <Flag className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center">
              <Radar className="w-6 h-6 mr-3 text-red-600" />
              Threat Detection & Response
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
              <Badge className="bg-red-100 text-red-600">
                <Target className="w-3 h-3 mr-1" />
                {threatMetrics.totalDetections} Detections
              </Badge>
              <Badge className="bg-orange-100 text-orange-600">
                <AlertTriangle className="w-3 h-3 mr-1" />
                {threatMetrics.criticalDetections} Critical
              </Badge>
              {realTimeDetection && (
                <Badge className="bg-green-100 text-green-600">
                  <Activity className="w-3 h-3 mr-1" />
                  Real-time
                </Badge>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">
            Advanced threat detection, hunting, and automated response
            capabilities.
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

      {threatMetrics.criticalDetections > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <strong>Critical Threats:</strong>{" "}
            {threatMetrics.criticalDetections} critical threats detected and
            require immediate response.
          </AlertDescription>
        </Alert>
      )}

      {threatMetrics.activeDetections > 0 && (
        <Alert className="border-amber-200 bg-amber-50">
          <Flag className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-amber-800">
            <strong>Active Threats:</strong> {threatMetrics.activeDetections}{" "}
            active threats are currently being monitored.
          </AlertDescription>
        </Alert>
      )}

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex space-x-4 mb-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search threats, signatures, targets..."
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
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="investigating">Investigating</SelectItem>
                <SelectItem value="contained">Contained</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={state.filterCategory}
              onValueChange={(value) =>
                setState((prev) => ({ ...prev, filterCategory: value }))
              }
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="malware">Malware</SelectItem>
                <SelectItem value="phishing">Phishing</SelectItem>
                <SelectItem value="ddos">DDoS</SelectItem>
                <SelectItem value="intrusion">Intrusion</SelectItem>
                <SelectItem value="data_exfiltration">
                  Data Exfiltration
                </SelectItem>
                <SelectItem value="insider_threat">Insider Threat</SelectItem>
                <SelectItem value="apt">APT</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex justify-between items-center">
            <div className="flex space-x-2">
              <Button
                onClick={() =>
                  setState((prev) => ({ ...prev, showHuntEditor: true }))
                }
                size="sm"
                variant="outline"
              >
                <Search className="w-4 h-4 mr-2" />
                Start Hunt
              </Button>
            </div>
            <div className="flex space-x-2">
              <Button
                onClick={() => handleExport("detections")}
                disabled={state.isExporting}
                size="sm"
                variant="outline"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
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
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="detections">Detections</TabsTrigger>
          <TabsTrigger value="signatures">Signatures</TabsTrigger>
          <TabsTrigger value="hunts">Threat Hunts</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
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
                        Total Detections
                      </p>
                      <p className="text-2xl font-bold">
                        {threatMetrics.totalDetections}
                      </p>
                      <p className="text-xs text-gray-500">
                        {threatMetrics.criticalDetections} critical
                      </p>
                    </div>
                    <Target className="w-8 h-8 text-red-500" />
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
                        {threatMetrics.activeDetections}
                      </p>
                      <p className="text-xs text-gray-500">
                        requiring response
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
                        Containment Rate
                      </p>
                      <p className="text-2xl font-bold text-green-600">
                        {threatMetrics.containmentRate.toFixed(1)}%
                      </p>
                      <p className="text-xs text-gray-500">
                        {threatMetrics.containedDetections} contained
                      </p>
                    </div>
                    <Shield className="w-8 h-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        Avg Risk Score
                      </p>
                      <p className="text-2xl font-bold text-orange-600">
                        {threatMetrics.averageRiskScore.toFixed(1)}
                      </p>
                      <p className="text-xs text-gray-500">
                        confidence: {threatMetrics.averageConfidence.toFixed(1)}
                        %
                      </p>
                    </div>
                    <BarChart3 className="w-8 h-8 text-orange-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Critical Detections */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Critical Detections</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {filteredDetections
                    .filter(
                      (d) => d.severity === "critical" || d.severity === "high",
                    )
                    .slice(0, 5)
                    .map((detection) => (
                      <div
                        key={detection.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded"
                      >
                        <div className="flex items-center space-x-3">
                          {getCategoryIcon(
                            signatures.find(
                              (s) => s.id === detection.signatureId,
                            )?.category || "custom",
                          )}
                          <div>
                            <p className="font-medium text-sm">
                              {detection.signatureName}
                            </p>
                            <p className="text-xs text-gray-600">
                              {detection.source.identifier} →{" "}
                              {detection.target.identifier}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge
                            className={getSeverityColor(detection.severity)}
                          >
                            {detection.severity}
                          </Badge>
                          <Badge className={getStatusColor(detection.status)}>
                            {detection.status}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {new Date(detection.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>

            {/* Threat Distribution Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Threats by Category</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(threatMetrics.detectionsByCategory).map(
                      ([category, count]) => (
                        <div
                          key={category}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded"
                        >
                          <div className="flex items-center space-x-2">
                            {getCategoryIcon(category)}
                            <span className="font-medium capitalize">
                              {category.replace("_", " ")}
                            </span>
                          </div>
                          <Badge className="bg-red-100 text-red-600">
                            {count} detections
                          </Badge>
                        </div>
                      ),
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Kill Chain Phases</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(threatMetrics.detectionsByKillChain).map(
                      ([phase, count]) => (
                        <div
                          key={phase}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded"
                        >
                          <div className="flex items-center space-x-2">
                            {getKillChainIcon(phase)}
                            <span className="font-medium capitalize">
                              {phase.replace("_", " ")}
                            </span>
                          </div>
                          <Badge className="bg-orange-100 text-orange-600">
                            {count} detections
                          </Badge>
                        </div>
                      ),
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Detections Tab */}
        <TabsContent value="detections">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">
                Threat Detections ({filteredDetections.length})
              </h3>
            </div>

            <div className="grid gap-4">
              {filteredDetections.map((detection) => (
                <Card
                  key={detection.id}
                  className="hover:shadow-md transition-shadow"
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getCategoryIcon(
                          signatures.find((s) => s.id === detection.signatureId)
                            ?.category || "custom",
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium truncate">
                              {detection.signatureName}
                            </h4>
                            <Badge
                              className={getSeverityColor(detection.severity)}
                            >
                              {detection.severity}
                            </Badge>
                            <Badge className={getStatusColor(detection.status)}>
                              {detection.status}
                            </Badge>
                            <Badge className="bg-purple-100 text-purple-600">
                              Risk: {detection.riskScore}/100
                            </Badge>
                            <Badge className="bg-blue-100 text-blue-600">
                              {detection.confidence}% confidence
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-500 mb-2">
                            <span>Source: {detection.source.identifier}</span>
                            <span>Target: {detection.target.identifier}</span>
                            <span>Vector: {detection.attackVector}</span>
                            <span>Phase: {detection.killChainPhase}</span>
                          </div>
                          <div className="flex items-center space-x-2 text-xs text-gray-600">
                            <Clock className="w-3 h-3" />
                            <span>
                              {new Date(detection.timestamp).toLocaleString()}
                            </span>
                            <span>•</span>
                            <span>MITRE: {detection.mitreAttackId}</span>
                            <span>•</span>
                            <span>
                              Patterns: {detection.matchedPatterns.length}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          onClick={() =>
                            setState((prev) => ({
                              ...prev,
                              selectedDetection: detection,
                              showDetectionDetails: true,
                            }))
                          }
                          size="sm"
                          variant="outline"
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          Details
                        </Button>
                        {detection.status === "active" && (
                          <>
                            <Button
                              onClick={() =>
                                handleDetectionInvestigate(detection.id)
                              }
                              disabled={state.isInvestigating}
                              size="sm"
                              variant="outline"
                            >
                              <Search className="w-3 h-3 mr-1" />
                              Investigate
                            </Button>
                            <Button
                              onClick={() =>
                                setState((prev) => ({
                                  ...prev,
                                  selectedDetection: detection,
                                  showResponseDialog: true,
                                }))
                              }
                              size="sm"
                            >
                              <Shield className="w-3 h-3 mr-1" />
                              Respond
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {filteredDetections.length === 0 && (
              <Card>
                <CardContent className="p-6 text-center">
                  <Target className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Detections Found
                  </h3>
                  <p className="text-sm text-gray-600">
                    No threat detections match your current filters. Try
                    adjusting your search criteria.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Signatures Tab */}
        <TabsContent value="signatures">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">
                Threat Signatures ({signatures.length})
              </h3>
              <Button
                onClick={() =>
                  setState((prev) => ({ ...prev, showSignatureEditor: true }))
                }
                size="sm"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Signature
              </Button>
            </div>

            <div className="grid gap-4">
              {signatures.map((signature) => (
                <Card key={signature.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getCategoryIcon(signature.category)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium">{signature.name}</h4>
                            <Badge
                              className={
                                signature.isActive
                                  ? "bg-green-100 text-green-600"
                                  : "bg-gray-100 text-gray-600"
                              }
                            >
                              {signature.isActive ? "Active" : "Inactive"}
                            </Badge>
                            <Badge
                              className={getSeverityColor(signature.severity)}
                            >
                              {signature.severity}
                            </Badge>
                            <Badge className="bg-blue-100 text-blue-600">
                              {signature.category.replace("_", " ")}
                            </Badge>
                            <Badge className="bg-purple-100 text-purple-600">
                              {signature.confidence}% confidence
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">
                            {signature.description}
                          </p>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-500 mb-2">
                            <span>Patterns: {signature.patterns.length}</span>
                            <span>
                              Indicators: {signature.indicators.length}
                            </span>
                            <span>Detections: {signature.detectionCount}</span>
                            <span>
                              FP Rate: {signature.falsePositiveRate.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {signature.mitreTactics
                              .slice(0, 3)
                              .map((tactic) => (
                                <Badge
                                  key={tactic}
                                  className="bg-gray-100 text-gray-600 text-xs"
                                >
                                  {tactic}
                                </Badge>
                              ))}
                            {signature.mitreTactics.length > 3 && (
                              <Badge className="bg-gray-100 text-gray-600 text-xs">
                                +{signature.mitreTactics.length - 3} more
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          onClick={() =>
                            setState((prev) => ({
                              ...prev,
                              selectedSignature: signature,
                              showSignatureEditor: true,
                            }))
                          }
                          size="sm"
                          variant="outline"
                        >
                          <Edit className="w-3 h-3 mr-1" />
                          Edit
                        </Button>
                        <Button
                          onClick={() => {
                            if (onSignatureDelete) {
                              onSignatureDelete(signature.id);
                            }
                          }}
                          size="sm"
                          variant="destructive"
                        >
                          <Trash2 className="w-3 h-3 mr-1" />
                          Delete
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Hunts Tab */}
        <TabsContent value="hunts">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">
                Threat Hunts ({hunts.length})
              </h3>
              <Button
                onClick={() =>
                  setState((prev) => ({ ...prev, showHuntEditor: true }))
                }
                size="sm"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Hunt
              </Button>
            </div>

            <div className="grid gap-4">
              {hunts.map((hunt) => (
                <Card key={hunt.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium">{hunt.name}</h4>
                          <Badge className={getStatusColor(hunt.status)}>
                            {hunt.status}
                          </Badge>
                          <Badge className={getSeverityColor(hunt.priority)}>
                            {hunt.priority}
                          </Badge>
                          <Badge className="bg-blue-100 text-blue-600">
                            {hunt.huntType.replace("_", " ")}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {hunt.description}
                        </p>
                        <p className="text-sm text-blue-600 mb-2">
                          <strong>Hypothesis:</strong> {hunt.hypothesis}
                        </p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-500 mb-3">
                          <span>Queries: {hunt.queries.length}</span>
                          <span>Findings: {hunt.findings.length}</span>
                          <span>Systems: {hunt.scope.systems.length}</span>
                          <span>
                            Created:{" "}
                            {new Date(hunt.createdAt).toLocaleDateString()}
                          </span>
                        </div>
                        {hunt.status === "active" && (
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span>Progress</span>
                              <span>{hunt.progress}%</span>
                            </div>
                            <Progress value={hunt.progress} className="h-2" />
                          </div>
                        )}
                      </div>
                      <div className="flex space-x-2">
                        {hunt.status === "planning" && (
                          <Button
                            onClick={() => {
                              if (onHuntStart) {
                                onHuntStart(hunt.id);
                              }
                            }}
                            size="sm"
                          >
                            <Play className="w-3 h-3 mr-1" />
                            Start
                          </Button>
                        )}
                        {hunt.status === "active" && (
                          <Button
                            onClick={() => {
                              if (onHuntStop) {
                                onHuntStop(hunt.id);
                              }
                            }}
                            size="sm"
                            variant="destructive"
                          >
                            <StopCircle className="w-3 h-3 mr-1" />
                            Stop
                          </Button>
                        )}
                        <Button
                          onClick={() =>
                            setState((prev) => ({
                              ...prev,
                              selectedHunt: hunt,
                            }))
                          }
                          size="sm"
                          variant="outline"
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          Details
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Detection Trends</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">
                        Detection Rate
                      </span>
                      <span className="text-lg font-bold">
                        {threatMetrics.totalDetections}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">
                        Average Risk Score
                      </span>
                      <span className="text-lg font-bold">
                        {threatMetrics.averageRiskScore.toFixed(1)}/100
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">
                        Containment Rate
                      </span>
                      <span className="text-lg font-bold text-green-600">
                        {threatMetrics.containmentRate.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Signature Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">
                        Active Signatures
                      </span>
                      <span className="text-lg font-bold">
                        {threatMetrics.activeSignatures}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">
                        Average Confidence
                      </span>
                      <span className="text-lg font-bold">
                        {threatMetrics.averageConfidence.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Active Hunts</span>
                      <span className="text-lg font-bold text-blue-600">
                        {threatMetrics.activeHunts}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Response Actions Modal */}
      {state.showResponseDialog && state.selectedDetection && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <CardTitle>
                Threat Response: {state.selectedDetection.signatureName}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Response Actions</Label>
                <div className="space-y-2">
                  {(
                    [
                      "isolate",
                      "block",
                      "quarantine",
                      "monitor",
                      "alert",
                    ] as Array<ThreatResponseAction["type"]>
                  ).map((action) => (
                    <div key={action} className="flex items-center space-x-2">
                      <Checkbox
                        checked={state.responseActions.some(
                          (a) => a.type === action,
                        )}
                        onCheckedChange={(checked) => {
                          setState((prev) => ({
                            ...prev,
                            responseActions: checked
                              ? [
                                  ...prev.responseActions,
                                  {
                                    id: `${action}-${Date.now()}`,
                                    type: action,
                                    target:
                                      prev.selectedDetection?.source
                                        .identifier || "",
                                    status: "pending",
                                    timestamp: new Date().toISOString(),
                                    automated: true,
                                  },
                                ]
                              : prev.responseActions.filter(
                                  (a) => a.type !== action,
                                ),
                          }));
                        }}
                      />
                      <span className="text-sm capitalize">
                        {action} {state.selectedDetection?.source.identifier}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={() => {
                    if (state.selectedDetection) {
                      handleThreatResponse(state.selectedDetection.id);
                    }
                  }}
                  disabled={
                    state.isResponding || state.responseActions.length === 0
                  }
                >
                  {state.isResponding ? "Executing..." : "Execute Response"}
                </Button>
                <Button
                  onClick={() =>
                    setState((prev) => ({
                      ...prev,
                      showResponseDialog: false,
                      responseActions: [],
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

export default ThreatDetection;
