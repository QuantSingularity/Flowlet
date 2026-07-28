import {
  AlertTriangle,
  CheckCircle,
  CreditCard,
  Database,
  Download,
  Eye,
  FileText,
  Key,
  Monitor,
  Network,
  Settings,
  Shield,
  XCircle,
} from "lucide-react";
import React, { useCallback, useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface PCIRequirement {
  id: string;
  number: string;
  title: string;
  description: string;
  category:
    "network" | "data" | "vulnerability" | "access" | "monitoring" | "policy";
  status: "compliant" | "non_compliant" | "in_progress" | "not_applicable";
  lastAssessed: string;
  nextAssessment: string;
  evidence: string[];
  remediation?: string;
  priority: "critical" | "high" | "medium" | "low";
}

interface SecurityControl {
  id: string;
  name: string;
  description: string;
  implemented: boolean;
  effectiveness: number; // 0-100
  lastTested: string;
  testResults: string;
  owner: string;
  automationLevel: "manual" | "semi_automated" | "automated";
}

interface VulnerabilityAssessment {
  id: string;
  type: "network" | "application" | "system";
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  description: string;
  discoveredAt: string;
  status: "open" | "in_progress" | "resolved" | "accepted";
  cvssScore?: number;
  remediation: string;
  assignedTo: string;
  dueDate: string;
}

interface ComplianceReport {
  id: string;
  type:
    | "self_assessment"
    | "external_audit"
    | "penetration_test"
    | "vulnerability_scan";
  generatedAt: string;
  period: string;
  overallScore: number;
  findings: number;
  recommendations: number;
  status: "draft" | "final" | "submitted";
  assessor: string;
  nextReview: string;
}

interface PCIDSSComplianceProps {
  requirements?: PCIRequirement[];
  securityControls?: SecurityControl[];
  vulnerabilities?: VulnerabilityAssessment[];
  complianceReports?: ComplianceReport[];
  overallComplianceScore?: number;
  onRequirementUpdate?: (
    requirementId: string,
    status: string,
    evidence?: string[],
  ) => Promise<void>;
  onControlTest?: (controlId: string) => Promise<void>;
  onVulnerabilityUpdate?: (
    vulnerabilityId: string,
    status: string,
    notes?: string,
  ) => Promise<void>;
  onGenerateReport?: (type: string) => Promise<void>;
  onExportReport?: (reportId: string) => Promise<Blob>;
  className?: string;
}

interface ComponentState {
  activeTab: string;
  selectedRequirement: PCIRequirement | null;
  selectedVulnerability: VulnerabilityAssessment | null;
  isUpdating: boolean;
  isGenerating: boolean;
  isTesting: boolean;
  error: string | null;
  success: string | null;
  filterCategory: string;
  filterStatus: string;
  showDetails: boolean;
}

export function PCIDSSCompliance({
  requirements = [],
  securityControls = [],
  vulnerabilities = [],
  complianceReports = [],
  overallComplianceScore = 0,
  onRequirementUpdate,
  onControlTest,
  onVulnerabilityUpdate,
  onGenerateReport,
  onExportReport,
  className = "",
}: PCIDSSComplianceProps) {
  const [state, setState] = useState<ComponentState>({
    activeTab: "overview",
    selectedRequirement: null,
    selectedVulnerability: null,
    isUpdating: false,
    isGenerating: false,
    isTesting: false,
    error: null,
    success: null,
    filterCategory: "all",
    filterStatus: "all",
    showDetails: false,
  });

  // Calculate compliance metrics
  const complianceMetrics = React.useMemo(() => {
    const total = requirements.length;
    const compliant = requirements.filter(
      (r) => r.status === "compliant",
    ).length;
    const nonCompliant = requirements.filter(
      (r) => r.status === "non_compliant",
    ).length;
    const inProgress = requirements.filter(
      (r) => r.status === "in_progress",
    ).length;
    const notApplicable = requirements.filter(
      (r) => r.status === "not_applicable",
    ).length;

    const criticalVulns = vulnerabilities.filter(
      (v) => v.severity === "critical" && v.status === "open",
    ).length;
    const highVulns = vulnerabilities.filter(
      (v) => v.severity === "high" && v.status === "open",
    ).length;

    const implementedControls = securityControls.filter(
      (c) => c.implemented,
    ).length;
    const totalControls = securityControls.length;

    return {
      total,
      compliant,
      nonCompliant,
      inProgress,
      notApplicable,
      complianceRate: total > 0 ? (compliant / total) * 100 : 0,
      criticalVulns,
      highVulns,
      implementedControls,
      totalControls,
      controlImplementationRate:
        totalControls > 0 ? (implementedControls / totalControls) * 100 : 0,
    };
  }, [requirements, vulnerabilities, securityControls]);

  // Filter requirements
  const filteredRequirements = React.useMemo(() => {
    return requirements.filter((req) => {
      const categoryMatch =
        state.filterCategory === "all" || req.category === state.filterCategory;
      const statusMatch =
        state.filterStatus === "all" || req.status === state.filterStatus;
      return categoryMatch && statusMatch;
    });
  }, [requirements, state.filterCategory, state.filterStatus]);

  // Handle requirement update
  const handleRequirementUpdate = useCallback(
    async (requirementId: string, status: string, evidence?: string[]) => {
      setState((prev) => ({ ...prev, isUpdating: true, error: null }));

      try {
        if (onRequirementUpdate) {
          await onRequirementUpdate(requirementId, status, evidence);
          setState((prev) => ({
            ...prev,
            success: "Requirement updated successfully",
          }));
        }
      } catch (_error) {
        setState((prev) => ({
          ...prev,
          error: "Failed to update requirement",
        }));
      } finally {
        setState((prev) => ({ ...prev, isUpdating: false }));
      }
    },
    [onRequirementUpdate],
  );

  // Handle control test
  const handleControlTest = useCallback(
    async (controlId: string) => {
      setState((prev) => ({ ...prev, isTesting: true, error: null }));

      try {
        if (onControlTest) {
          await onControlTest(controlId);
          setState((prev) => ({
            ...prev,
            success: "Control test initiated successfully",
          }));
        }
      } catch (_error) {
        setState((prev) => ({ ...prev, error: "Failed to test control" }));
      } finally {
        setState((prev) => ({ ...prev, isTesting: false }));
      }
    },
    [onControlTest],
  );

  // Handle vulnerability update
  const handleVulnerabilityUpdate = useCallback(
    async (vulnerabilityId: string, status: string, notes?: string) => {
      setState((prev) => ({ ...prev, isUpdating: true, error: null }));

      try {
        if (onVulnerabilityUpdate) {
          await onVulnerabilityUpdate(vulnerabilityId, status, notes);
          setState((prev) => ({
            ...prev,
            success: "Vulnerability updated successfully",
          }));
        }
      } catch (_error) {
        setState((prev) => ({
          ...prev,
          error: "Failed to update vulnerability",
        }));
      } finally {
        setState((prev) => ({ ...prev, isUpdating: false }));
      }
    },
    [onVulnerabilityUpdate],
  );

  // Handle report generation
  const handleGenerateReport = useCallback(
    async (type: string) => {
      setState((prev) => ({ ...prev, isGenerating: true, error: null }));

      try {
        if (onGenerateReport) {
          await onGenerateReport(type);
          setState((prev) => ({
            ...prev,
            success: "Report generation initiated",
          }));
        }
      } catch (_error) {
        setState((prev) => ({ ...prev, error: "Failed to generate report" }));
      } finally {
        setState((prev) => ({ ...prev, isGenerating: false }));
      }
    },
    [onGenerateReport],
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case "compliant":
        return "bg-green-100 text-green-600";
      case "non_compliant":
        return "bg-red-100 text-red-600";
      case "in_progress":
        return "bg-yellow-100 text-yellow-600";
      case "not_applicable":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-100 text-red-600";
      case "high":
        return "bg-orange-100 text-orange-600";
      case "medium":
        return "bg-yellow-100 text-yellow-600";
      case "low":
        return "bg-blue-100 text-blue-600";
      case "info":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "network":
        return <Network className="w-4 h-4" />;
      case "data":
        return <Database className="w-4 h-4" />;
      case "vulnerability":
        return <AlertTriangle className="w-4 h-4" />;
      case "access":
        return <Key className="w-4 h-4" />;
      case "monitoring":
        return <Monitor className="w-4 h-4" />;
      case "policy":
        return <FileText className="w-4 h-4" />;
      default:
        return <Shield className="w-4 h-4" />;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center">
              <CreditCard className="w-6 h-6 mr-3 text-blue-600" />
              PCI DSS Compliance Dashboard
            </div>
            <div className="flex items-center space-x-2">
              <Badge
                className={
                  overallComplianceScore >= 90
                    ? "bg-green-100 text-green-600"
                    : overallComplianceScore >= 70
                      ? "bg-yellow-100 text-yellow-600"
                      : "bg-red-100 text-red-600"
                }
              >
                <Shield className="w-3 h-3 mr-1" />
                {overallComplianceScore.toFixed(1)}% Compliant
              </Badge>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Overall Compliance Score</span>
                <span>{overallComplianceScore.toFixed(1)}%</span>
              </div>
              <Progress value={overallComplianceScore} className="h-3" />
            </div>
            <p className="text-sm text-gray-600">
              Monitor and maintain PCI DSS compliance for secure payment card
              data handling.
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

      {/* Critical Alerts */}
      {complianceMetrics.criticalVulns > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <strong>Critical Alert:</strong> {complianceMetrics.criticalVulns}{" "}
            critical vulnerabilities require immediate attention.
          </AlertDescription>
        </Alert>
      )}

      {complianceMetrics.complianceRate < 80 && (
        <Alert className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-amber-800">
            <strong>Compliance Warning:</strong> Current compliance rate is
            below 80%. Immediate action required.
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
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="requirements">Requirements</TabsTrigger>
          <TabsTrigger value="controls">Controls</TabsTrigger>
          <TabsTrigger value="vulnerabilities">Vulnerabilities</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      Compliant Requirements
                    </p>
                    <p className="text-2xl font-bold text-green-600">
                      {complianceMetrics.compliant}
                    </p>
                    <p className="text-xs text-gray-500">
                      of {complianceMetrics.total} total
                    </p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      Non-Compliant
                    </p>
                    <p className="text-2xl font-bold text-red-600">
                      {complianceMetrics.nonCompliant}
                    </p>
                    <p className="text-xs text-gray-500">require attention</p>
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
                      Critical Vulnerabilities
                    </p>
                    <p className="text-2xl font-bold text-red-600">
                      {complianceMetrics.criticalVulns}
                    </p>
                    <p className="text-xs text-gray-500">immediate action</p>
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
                      Security Controls
                    </p>
                    <p className="text-2xl font-bold text-blue-600">
                      {complianceMetrics.implementedControls}
                    </p>
                    <p className="text-xs text-gray-500">
                      of {complianceMetrics.totalControls} implemented
                    </p>
                  </div>
                  <Shield className="w-8 h-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Compliance by Category */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Compliance by Category</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[
                  "network",
                  "data",
                  "vulnerability",
                  "access",
                  "monitoring",
                  "policy",
                ].map((category) => {
                  const categoryReqs = requirements.filter(
                    (r) => r.category === category,
                  );
                  const categoryCompliant = categoryReqs.filter(
                    (r) => r.status === "compliant",
                  ).length;
                  const categoryRate =
                    categoryReqs.length > 0
                      ? (categoryCompliant / categoryReqs.length) * 100
                      : 0;

                  return (
                    <div key={category} className="p-4 border rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        {getCategoryIcon(category)}
                        <h4 className="font-medium capitalize">{category}</h4>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>
                            {categoryCompliant}/{categoryReqs.length}
                          </span>
                          <span>{categoryRate.toFixed(1)}%</span>
                        </div>
                        <Progress value={categoryRate} className="h-2" />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Button
                  onClick={() => handleGenerateReport("self_assessment")}
                  disabled={state.isGenerating}
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                >
                  <FileText className="w-6 h-6 mb-2" />
                  <span>Generate Assessment</span>
                </Button>

                <Button
                  onClick={() =>
                    setState((prev) => ({
                      ...prev,
                      activeTab: "vulnerabilities",
                    }))
                  }
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                >
                  <AlertTriangle className="w-6 h-6 mb-2" />
                  <span>Review Vulnerabilities</span>
                </Button>

                <Button
                  onClick={() =>
                    setState((prev) => ({ ...prev, activeTab: "controls" }))
                  }
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                >
                  <Shield className="w-6 h-6 mb-2" />
                  <span>Test Controls</span>
                </Button>

                <Button
                  onClick={() =>
                    setState((prev) => ({ ...prev, activeTab: "reports" }))
                  }
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                >
                  <Download className="w-6 h-6 mb-2" />
                  <span>Export Reports</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Requirements Tab */}
        <TabsContent value="requirements">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">PCI DSS Requirements</h3>
              <div className="flex space-x-2">
                <select
                  value={state.filterCategory}
                  onChange={(e) =>
                    setState((prev) => ({
                      ...prev,
                      filterCategory: e.target.value,
                    }))
                  }
                  className="px-3 py-1 border rounded-md text-sm"
                >
                  <option value="all">All Categories</option>
                  <option value="network">Network Security</option>
                  <option value="data">Data Protection</option>
                  <option value="vulnerability">
                    Vulnerability Management
                  </option>
                  <option value="access">Access Control</option>
                  <option value="monitoring">Monitoring</option>
                  <option value="policy">Policy</option>
                </select>
                <select
                  value={state.filterStatus}
                  onChange={(e) =>
                    setState((prev) => ({
                      ...prev,
                      filterStatus: e.target.value,
                    }))
                  }
                  className="px-3 py-1 border rounded-md text-sm"
                >
                  <option value="all">All Statuses</option>
                  <option value="compliant">Compliant</option>
                  <option value="non_compliant">Non-Compliant</option>
                  <option value="in_progress">In Progress</option>
                  <option value="not_applicable">Not Applicable</option>
                </select>
              </div>
            </div>

            <div className="grid gap-4">
              {filteredRequirements.map((requirement) => (
                <Card key={requirement.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getCategoryIcon(requirement.category)}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium">
                              {requirement.number}: {requirement.title}
                            </h4>
                            <Badge
                              className={getStatusColor(requirement.status)}
                            >
                              {requirement.status.replace("_", " ")}
                            </Badge>
                            {requirement.priority === "critical" && (
                              <Badge className="bg-red-100 text-red-600">
                                Critical
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mb-2">
                            {requirement.description}
                          </p>
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span>
                              Last Assessed:{" "}
                              {new Date(
                                requirement.lastAssessed,
                              ).toLocaleDateString()}
                            </span>
                            <span>
                              Next Assessment:{" "}
                              {new Date(
                                requirement.nextAssessment,
                              ).toLocaleDateString()}
                            </span>
                            <span>
                              Evidence: {requirement.evidence.length} items
                            </span>
                          </div>
                          {requirement.remediation && (
                            <div className="mt-2 p-2 bg-yellow-50 rounded text-sm">
                              <strong>Remediation:</strong>{" "}
                              {requirement.remediation}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          onClick={() =>
                            setState((prev) => ({
                              ...prev,
                              selectedRequirement: requirement,
                            }))
                          }
                          size="sm"
                          variant="outline"
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          Details
                        </Button>
                        {requirement.status !== "compliant" && (
                          <Button
                            onClick={() =>
                              handleRequirementUpdate(
                                requirement.id,
                                "in_progress",
                              )
                            }
                            disabled={state.isUpdating}
                            size="sm"
                          >
                            Update Status
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

        {/* Controls Tab */}
        <TabsContent value="controls">
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Security Controls</h3>

            <div className="grid gap-4">
              {securityControls.map((control) => (
                <Card key={control.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium">{control.name}</h4>
                          <Badge
                            className={
                              control.implemented
                                ? "bg-green-100 text-green-600"
                                : "bg-red-100 text-red-600"
                            }
                          >
                            {control.implemented
                              ? "Implemented"
                              : "Not Implemented"}
                          </Badge>
                          <Badge className="bg-blue-100 text-blue-600">
                            {control.automationLevel.replace("_", " ")}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {control.description}
                        </p>
                        <div className="space-y-2">
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span>Effectiveness</span>
                              <span>{control.effectiveness}%</span>
                            </div>
                            <Progress
                              value={control.effectiveness}
                              className="h-2"
                            />
                          </div>
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span>
                              Last Tested:{" "}
                              {new Date(
                                control.lastTested,
                              ).toLocaleDateString()}
                            </span>
                            <span>Owner: {control.owner}</span>
                          </div>
                          {control.testResults && (
                            <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
                              <strong>Test Results:</strong>{" "}
                              {control.testResults}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          onClick={() => handleControlTest(control.id)}
                          disabled={state.isTesting}
                          size="sm"
                          variant="outline"
                        >
                          <Settings className="w-3 h-3 mr-1" />
                          Test Control
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Vulnerabilities Tab */}
        <TabsContent value="vulnerabilities">
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Vulnerability Management</h3>

            <div className="grid gap-4">
              {vulnerabilities.map((vulnerability) => (
                <Card key={vulnerability.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium">{vulnerability.title}</h4>
                          <Badge
                            className={getSeverityColor(vulnerability.severity)}
                          >
                            {vulnerability.severity}
                          </Badge>
                          <Badge
                            className={
                              vulnerability.status === "open"
                                ? "bg-red-100 text-red-600"
                                : vulnerability.status === "resolved"
                                  ? "bg-green-100 text-green-600"
                                  : "bg-yellow-100 text-yellow-600"
                            }
                          >
                            {vulnerability.status.replace("_", " ")}
                          </Badge>
                          {vulnerability.cvssScore && (
                            <Badge className="bg-gray-100 text-gray-600">
                              CVSS: {vulnerability.cvssScore}
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {vulnerability.description}
                        </p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500 mb-2">
                          <span>
                            Discovered:{" "}
                            {new Date(
                              vulnerability.discoveredAt,
                            ).toLocaleDateString()}
                          </span>
                          <span>Assigned to: {vulnerability.assignedTo}</span>
                          <span>
                            Due:{" "}
                            {new Date(
                              vulnerability.dueDate,
                            ).toLocaleDateString()}
                          </span>
                        </div>
                        <div className="p-2 bg-blue-50 rounded text-sm">
                          <strong>Remediation:</strong>{" "}
                          {vulnerability.remediation}
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          onClick={() =>
                            setState((prev) => ({
                              ...prev,
                              selectedVulnerability: vulnerability,
                            }))
                          }
                          size="sm"
                          variant="outline"
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          Details
                        </Button>
                        {vulnerability.status === "open" && (
                          <Button
                            onClick={() =>
                              handleVulnerabilityUpdate(
                                vulnerability.id,
                                "in_progress",
                              )
                            }
                            disabled={state.isUpdating}
                            size="sm"
                          >
                            Start Remediation
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

        {/* Reports Tab */}
        <TabsContent value="reports">
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">Compliance Reports</h3>
              <div className="flex space-x-2">
                <Button
                  onClick={() => handleGenerateReport("self_assessment")}
                  disabled={state.isGenerating}
                  size="sm"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Generate Self-Assessment
                </Button>
                <Button
                  onClick={() => handleGenerateReport("vulnerability_scan")}
                  disabled={state.isGenerating}
                  size="sm"
                  variant="outline"
                >
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  Vulnerability Scan
                </Button>
              </div>
            </div>

            <div className="grid gap-4">
              {complianceReports.map((report) => (
                <Card key={report.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium capitalize">
                            {report.type.replace("_", " ")}
                          </h4>
                          <Badge
                            className={
                              report.status === "final"
                                ? "bg-green-100 text-green-600"
                                : report.status === "submitted"
                                  ? "bg-blue-100 text-blue-600"
                                  : "bg-yellow-100 text-yellow-600"
                            }
                          >
                            {report.status}
                          </Badge>
                        </div>
                        <div className="space-y-1 text-sm text-gray-600">
                          <p>Period: {report.period}</p>
                          <p>
                            Generated:{" "}
                            {new Date(report.generatedAt).toLocaleDateString()}
                          </p>
                          <p>Assessor: {report.assessor}</p>
                          <p>
                            Overall Score:{" "}
                            <span className="font-medium">
                              {report.overallScore}%
                            </span>
                          </p>
                          <p>
                            Findings: {report.findings} | Recommendations:{" "}
                            {report.recommendations}
                          </p>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          onClick={() => {
                            if (onExportReport) {
                              onExportReport(report.id);
                            }
                          }}
                          size="sm"
                          variant="outline"
                        >
                          <Download className="w-3 h-3 mr-1" />
                          Export
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default PCIDSSCompliance;
