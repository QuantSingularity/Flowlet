import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Cookie,
  Database,
  Download,
  Edit,
  Eye,
  FileText,
  Lock,
  Settings,
  Shield,
  Trash2,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

interface ConsentCategory {
  id: string;
  name: string;
  description: string;
  purpose: string;
  legalBasis:
    | "consent"
    | "legitimate_interest"
    | "contract"
    | "legal_obligation"
    | "vital_interests"
    | "public_task";
  required: boolean;
  dataTypes: string[];
  retentionPeriod: number; // in days
  thirdParties: string[];
  transferCountries: string[];
}

interface ConsentRecord {
  id: string;
  userId: string;
  categoryId: string;
  granted: boolean;
  timestamp: string;
  ipAddress: string;
  userAgent: string;
  method: "explicit" | "implicit" | "pre_ticked" | "opt_out";
  version: string;
  withdrawnAt?: string;
  withdrawalReason?: string;
}

interface DataSubjectRequest {
  id: string;
  userId: string;
  type:
    | "access"
    | "rectification"
    | "erasure"
    | "portability"
    | "restriction"
    | "objection";
  status: "pending" | "in_progress" | "completed" | "rejected";
  requestedAt: string;
  completedAt?: string;
  description: string;
  response?: string;
  documents?: string[];
}

interface GDPRConsentProps {
  categories?: ConsentCategory[];
  consentRecords?: ConsentRecord[];
  dataSubjectRequests?: DataSubjectRequest[];
  currentConsents?: Record<string, boolean>;
  onConsentUpdate?: (categoryId: string, granted: boolean) => Promise<void>;
  onConsentWithdraw?: (categoryId: string, reason?: string) => Promise<void>;
  onDataSubjectRequest?: (
    request: Omit<DataSubjectRequest, "id" | "requestedAt" | "status">,
  ) => Promise<void>;
  onExportData?: () => Promise<Blob>;
  onDeleteData?: () => Promise<void>;
  showBanner?: boolean;
  onBannerAccept?: (consents: Record<string, boolean>) => void;
  onBannerReject?: () => void;
  className?: string;
}

interface ComponentState {
  activeTab: string;
  showBanner: boolean;
  bannerConsents: Record<string, boolean>;
  isUpdating: boolean;
  isExporting: boolean;
  isDeleting: boolean;
  error: string | null;
  success: string | null;
  selectedRequest: DataSubjectRequest | null;
  newRequestType: DataSubjectRequest["type"];
  newRequestDescription: string;
  withdrawalReason: string;
  showWithdrawalDialog: string | null;
}

export function GDPRConsent({
  categories = [],
  consentRecords = [],
  dataSubjectRequests = [],
  currentConsents = {},
  onConsentUpdate,
  onConsentWithdraw,
  onDataSubjectRequest,
  onExportData,
  onDeleteData,
  showBanner = false,
  onBannerAccept,
  onBannerReject,
  className = "",
}: GDPRConsentProps) {
  const [state, setState] = useState<ComponentState>({
    activeTab: "overview",
    showBanner: showBanner,
    bannerConsents: {},
    isUpdating: false,
    isExporting: false,
    isDeleting: false,
    error: null,
    success: null,
    selectedRequest: null,
    newRequestType: "access",
    newRequestDescription: "",
    withdrawalReason: "",
    showWithdrawalDialog: null,
  });

  // Initialize banner consents with required categories
  useEffect(() => {
    const initialConsents: Record<string, boolean> = {};
    categories.forEach((category) => {
      initialConsents[category.id] =
        category.required || currentConsents[category.id] || false;
    });
    setState((prev) => ({ ...prev, bannerConsents: initialConsents }));
  }, [categories, currentConsents]);

  // Handle consent update
  const handleConsentUpdate = useCallback(
    async (categoryId: string, granted: boolean) => {
      setState((prev) => ({ ...prev, isUpdating: true, error: null }));

      try {
        if (onConsentUpdate) {
          await onConsentUpdate(categoryId, granted);
          setState((prev) => ({
            ...prev,
            success: `Consent ${granted ? "granted" : "withdrawn"} successfully`,
          }));
        }
      } catch (_error) {
        setState((prev) => ({ ...prev, error: "Failed to update consent" }));
      } finally {
        setState((prev) => ({ ...prev, isUpdating: false }));
      }
    },
    [onConsentUpdate],
  );

  // Handle consent withdrawal
  const handleConsentWithdraw = useCallback(
    async (categoryId: string) => {
      setState((prev) => ({ ...prev, isUpdating: true, error: null }));

      try {
        if (onConsentWithdraw) {
          await onConsentWithdraw(categoryId, state.withdrawalReason);
          setState((prev) => ({
            ...prev,
            success: "Consent withdrawn successfully",
            showWithdrawalDialog: null,
            withdrawalReason: "",
          }));
        }
      } catch (_error) {
        setState((prev) => ({ ...prev, error: "Failed to withdraw consent" }));
      } finally {
        setState((prev) => ({ ...prev, isUpdating: false }));
      }
    },
    [onConsentWithdraw, state.withdrawalReason],
  );

  // Handle data subject request
  const handleDataSubjectRequest = useCallback(async () => {
    if (!state.newRequestDescription.trim()) {
      setState((prev) => ({
        ...prev,
        error: "Please provide a description for your request",
      }));
      return;
    }

    setState((prev) => ({ ...prev, isUpdating: true, error: null }));

    try {
      if (onDataSubjectRequest) {
        await onDataSubjectRequest({
          userId: "current-user", // This would come from auth context
          type: state.newRequestType,
          description: state.newRequestDescription,
        });
        setState((prev) => ({
          ...prev,
          success: "Data subject request submitted successfully",
          newRequestDescription: "",
        }));
      }
    } catch (_error) {
      setState((prev) => ({ ...prev, error: "Failed to submit request" }));
    } finally {
      setState((prev) => ({ ...prev, isUpdating: false }));
    }
  }, [onDataSubjectRequest, state.newRequestType, state.newRequestDescription]);

  // Handle data export
  const handleDataExport = useCallback(async () => {
    setState((prev) => ({ ...prev, isExporting: true, error: null }));

    try {
      if (onExportData) {
        const blob = await onExportData();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `personal-data-export-${new Date().toISOString().split("T")[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 100);

        setState((prev) => ({
          ...prev,
          success: "Data export completed successfully",
        }));
      }
    } catch (_error) {
      setState((prev) => ({ ...prev, error: "Failed to export data" }));
    } finally {
      setState((prev) => ({ ...prev, isExporting: false }));
    }
  }, [onExportData]);

  // Handle data deletion
  const handleDataDeletion = useCallback(async () => {
    if (
      !confirm(
        "Are you sure you want to delete all your personal data? This action cannot be undone.",
      )
    ) {
      return;
    }

    setState((prev) => ({ ...prev, isDeleting: true, error: null }));

    try {
      if (onDeleteData) {
        await onDeleteData();
        setState((prev) => ({
          ...prev,
          success: "Data deletion request submitted successfully",
        }));
      }
    } catch (_error) {
      setState((prev) => ({
        ...prev,
        error: "Failed to submit deletion request",
      }));
    } finally {
      setState((prev) => ({ ...prev, isDeleting: false }));
    }
  }, [onDeleteData]);

  // Handle banner accept
  const handleBannerAccept = useCallback(() => {
    if (onBannerAccept) {
      onBannerAccept(state.bannerConsents);
    }
    setState((prev) => ({ ...prev, showBanner: false }));
  }, [onBannerAccept, state.bannerConsents]);

  // Handle banner reject
  const handleBannerReject = useCallback(() => {
    if (onBannerReject) {
      onBannerReject();
    }
    setState((prev) => ({ ...prev, showBanner: false }));
  }, [onBannerReject]);

  const getLegalBasisColor = (basis: string) => {
    switch (basis) {
      case "consent":
        return "bg-green-100 text-green-600";
      case "legitimate_interest":
        return "bg-blue-100 text-blue-600";
      case "contract":
        return "bg-purple-100 text-purple-600";
      case "legal_obligation":
        return "bg-orange-100 text-orange-600";
      case "vital_interests":
        return "bg-red-100 text-red-600";
      case "public_task":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const getRequestStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-100 text-yellow-600";
      case "in_progress":
        return "bg-blue-100 text-blue-600";
      case "completed":
        return "bg-green-100 text-green-600";
      case "rejected":
        return "bg-red-100 text-red-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const getRequestTypeIcon = (type: string) => {
    switch (type) {
      case "access":
        return <Eye className="w-4 h-4" />;
      case "rectification":
        return <Edit className="w-4 h-4" />;
      case "erasure":
        return <Trash2 className="w-4 h-4" />;
      case "portability":
        return <Download className="w-4 h-4" />;
      case "restriction":
        return <Lock className="w-4 h-4" />;
      case "objection":
        return <XCircle className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const requiredCategories = categories.filter((c) => c.required);
  const optionalCategories = categories.filter((c) => !c.required);
  const grantedConsents = Object.values(currentConsents).filter(Boolean).length;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* GDPR Consent Banner */}
      {state.showBanner && (
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t shadow-lg p-4">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-start justify-between space-x-4">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <Cookie className="w-5 h-5 text-blue-600" />
                  <h3 className="font-medium">
                    Cookie and Privacy Preferences
                  </h3>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  We use cookies and similar technologies to provide, protect,
                  and improve our services. You can choose which categories of
                  data processing you consent to.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
                  {categories.map((category) => (
                    <div
                      key={category.id}
                      className="flex items-center space-x-2"
                    >
                      <Checkbox
                        checked={state.bannerConsents[category.id]}
                        onCheckedChange={(checked) => {
                          if (!category.required) {
                            setState((prev) => ({
                              ...prev,
                              bannerConsents: {
                                ...prev.bannerConsents,
                                [category.id]: checked as boolean,
                              },
                            }));
                          }
                        }}
                        disabled={category.required}
                      />
                      <div>
                        <span className="text-sm font-medium">
                          {category.name}
                        </span>
                        {category.required && (
                          <Badge className="ml-1 text-xs bg-red-100 text-red-600">
                            Required
                          </Badge>
                        )}
                        <p className="text-xs text-gray-500">
                          {category.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={handleBannerReject}
                  variant="outline"
                  size="sm"
                >
                  Reject All
                </Button>
                <Button onClick={handleBannerAccept} size="sm">
                  Accept Selected
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center">
              <Shield className="w-6 h-6 mr-3 text-blue-600" />
              GDPR Compliance & Privacy
            </div>
            <div className="flex items-center space-x-2">
              <Badge className="bg-blue-100 text-blue-600">
                <Database className="w-3 h-3 mr-1" />
                {grantedConsents} Consents
              </Badge>
              <Badge className="bg-green-100 text-green-600">
                <CheckCircle className="w-3 h-3 mr-1" />
                GDPR Compliant
              </Badge>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">
            Manage your privacy preferences and exercise your data protection
            rights under GDPR.
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

      {/* Main Content */}
      <Tabs
        value={state.activeTab}
        onValueChange={(value) =>
          setState((prev) => ({ ...prev, activeTab: value }))
        }
      >
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="consents">Consents</TabsTrigger>
          <TabsTrigger value="rights">Your Rights</TabsTrigger>
          <TabsTrigger value="requests">Requests</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      Total Categories
                    </p>
                    <p className="text-2xl font-bold">{categories.length}</p>
                  </div>
                  <Database className="w-8 h-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      Granted Consents
                    </p>
                    <p className="text-2xl font-bold text-green-600">
                      {grantedConsents}
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
                      Consent Records
                    </p>
                    <p className="text-2xl font-bold">
                      {consentRecords.length}
                    </p>
                  </div>
                  <FileText className="w-8 h-8 text-purple-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      Active Requests
                    </p>
                    <p className="text-2xl font-bold text-orange-600">
                      {
                        dataSubjectRequests.filter(
                          (r) =>
                            r.status === "pending" ||
                            r.status === "in_progress",
                        ).length
                      }
                    </p>
                  </div>
                  <Clock className="w-8 h-8 text-orange-500" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button
                  onClick={handleDataExport}
                  disabled={state.isExporting}
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                >
                  <Download
                    className={`w-6 h-6 mb-2 ${state.isExporting ? "animate-pulse" : ""}`}
                  />
                  <span>Export My Data</span>
                </Button>

                <Button
                  onClick={() =>
                    setState((prev) => ({ ...prev, activeTab: "consents" }))
                  }
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                >
                  <Settings className="w-6 h-6 mb-2" />
                  <span>Manage Consents</span>
                </Button>

                <Button
                  onClick={() =>
                    setState((prev) => ({ ...prev, activeTab: "rights" }))
                  }
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                >
                  <Shield className="w-6 h-6 mb-2" />
                  <span>Exercise Rights</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Consents Tab */}
        <TabsContent value="consents">
          <div className="space-y-6">
            {/* Required Consents */}
            {requiredCategories.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Lock className="w-5 h-5 mr-2 text-red-600" />
                    Required Data Processing
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {requiredCategories.map((category) => (
                    <div
                      key={category.id}
                      className="p-4 border rounded-lg bg-red-50"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium">{category.name}</h4>
                            <Badge className="bg-red-100 text-red-600">
                              Required
                            </Badge>
                            <Badge
                              className={getLegalBasisColor(
                                category.legalBasis,
                              )}
                            >
                              {category.legalBasis.replace("_", " ")}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">
                            {category.description}
                          </p>
                          <p className="text-sm text-gray-600 mb-2">
                            <strong>Purpose:</strong> {category.purpose}
                          </p>
                          <div className="flex flex-wrap gap-2 text-xs">
                            <span>
                              <strong>Data Types:</strong>{" "}
                              {category.dataTypes.join(", ")}
                            </span>
                            <span>
                              <strong>Retention:</strong>{" "}
                              {category.retentionPeriod} days
                            </span>
                          </div>
                        </div>
                        <Badge className="bg-green-100 text-green-600">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Active
                        </Badge>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Optional Consents */}
            {optionalCategories.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Settings className="w-5 h-5 mr-2 text-blue-600" />
                    Optional Data Processing
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {optionalCategories.map((category) => {
                    const isGranted = currentConsents[category.id];
                    return (
                      <div key={category.id} className="p-4 border rounded-lg">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <h4 className="font-medium">{category.name}</h4>
                              <Badge
                                className={getLegalBasisColor(
                                  category.legalBasis,
                                )}
                              >
                                {category.legalBasis.replace("_", " ")}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">
                              {category.description}
                            </p>
                            <p className="text-sm text-gray-600 mb-2">
                              <strong>Purpose:</strong> {category.purpose}
                            </p>
                            <div className="flex flex-wrap gap-2 text-xs text-gray-500 mb-3">
                              <span>
                                <strong>Data Types:</strong>{" "}
                                {category.dataTypes.join(", ")}
                              </span>
                              <span>
                                <strong>Retention:</strong>{" "}
                                {category.retentionPeriod} days
                              </span>
                              {category.thirdParties.length > 0 && (
                                <span>
                                  <strong>Third Parties:</strong>{" "}
                                  {category.thirdParties.join(", ")}
                                </span>
                              )}
                              {category.transferCountries.length > 0 && (
                                <span>
                                  <strong>Countries:</strong>{" "}
                                  {category.transferCountries.join(", ")}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center space-x-3">
                            <Badge
                              className={
                                isGranted
                                  ? "bg-green-100 text-green-600"
                                  : "bg-gray-100 text-gray-600"
                              }
                            >
                              {isGranted ? "Granted" : "Not Granted"}
                            </Badge>
                            <Switch
                              checked={isGranted}
                              onCheckedChange={(checked: boolean) =>
                                handleConsentUpdate(category.id, checked)
                              }
                              disabled={state.isUpdating}
                            />
                            {isGranted && (
                              <Button
                                onClick={() =>
                                  setState((prev) => ({
                                    ...prev,
                                    showWithdrawalDialog: category.id,
                                  }))
                                }
                                size="sm"
                                variant="outline"
                              >
                                Withdraw
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Your Rights Tab */}
        <TabsContent value="rights">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Your Data Protection Rights</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  Under GDPR, you have several rights regarding your personal
                  data. You can exercise these rights by submitting a request
                  below.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-4">
                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <Eye className="w-5 h-5 text-blue-600" />
                        <h4 className="font-medium">Right of Access</h4>
                      </div>
                      <p className="text-sm text-gray-600">
                        Request a copy of all personal data we hold about you.
                      </p>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <Edit className="w-5 h-5 text-green-600" />
                        <h4 className="font-medium">Right to Rectification</h4>
                      </div>
                      <p className="text-sm text-gray-600">
                        Request correction of inaccurate or incomplete personal
                        data.
                      </p>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <Trash2 className="w-5 h-5 text-red-600" />
                        <h4 className="font-medium">Right to Erasure</h4>
                      </div>
                      <p className="text-sm text-gray-600">
                        Request deletion of your personal data (right to be
                        forgotten).
                      </p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <Download className="w-5 h-5 text-purple-600" />
                        <h4 className="font-medium">
                          Right to Data Portability
                        </h4>
                      </div>
                      <p className="text-sm text-gray-600">
                        Receive your personal data in a structured,
                        machine-readable format.
                      </p>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <Lock className="w-5 h-5 text-orange-600" />
                        <h4 className="font-medium">Right to Restriction</h4>
                      </div>
                      <p className="text-sm text-gray-600">
                        Request restriction of processing of your personal data.
                      </p>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <XCircle className="w-5 h-5 text-gray-600" />
                        <h4 className="font-medium">Right to Object</h4>
                      </div>
                      <p className="text-sm text-gray-600">
                        Object to processing of your personal data for specific
                        purposes.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium mb-2">Quick Actions</h4>
                  <div className="flex space-x-2">
                    <Button
                      onClick={handleDataExport}
                      disabled={state.isExporting}
                      size="sm"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Export My Data
                    </Button>
                    <Button
                      onClick={handleDataDeletion}
                      disabled={state.isDeleting}
                      size="sm"
                      variant="destructive"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete My Data
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Submit New Request */}
            <Card>
              <CardHeader>
                <CardTitle>Submit Data Subject Request</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Request Type</Label>
                  <select
                    value={state.newRequestType}
                    onChange={(e) =>
                      setState((prev) => ({
                        ...prev,
                        newRequestType: e.target
                          .value as DataSubjectRequest["type"],
                      }))
                    }
                    className="w-full mt-1 p-2 border rounded-md"
                  >
                    <option value="access">Right of Access</option>
                    <option value="rectification">
                      Right to Rectification
                    </option>
                    <option value="erasure">Right to Erasure</option>
                    <option value="portability">
                      Right to Data Portability
                    </option>
                    <option value="restriction">Right to Restriction</option>
                    <option value="objection">Right to Object</option>
                  </select>
                </div>

                <div>
                  <Label>Description</Label>
                  <Textarea
                    value={state.newRequestDescription}
                    onChange={(e) =>
                      setState((prev) => ({
                        ...prev,
                        newRequestDescription: e.target.value,
                      }))
                    }
                    placeholder="Please describe your request in detail..."
                    className="mt-1"
                    rows={4}
                  />
                </div>

                <Button
                  onClick={handleDataSubjectRequest}
                  disabled={
                    state.isUpdating || !state.newRequestDescription.trim()
                  }
                >
                  Submit Request
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Requests Tab */}
        <TabsContent value="requests">
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Your Data Subject Requests</h3>

            {dataSubjectRequests.length === 0 ? (
              <Card>
                <CardContent className="p-6 text-center">
                  <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Requests
                  </h3>
                  <p className="text-sm text-gray-600">
                    You haven't submitted any data subject requests yet.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {dataSubjectRequests.map((request) => (
                  <Card key={request.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3">
                          {getRequestTypeIcon(request.type)}
                          <div>
                            <h4 className="font-medium capitalize">
                              {request.type.replace("_", " ")} Request
                            </h4>
                            <p className="text-sm text-gray-600 mt-1">
                              {request.description}
                            </p>
                            <div className="flex items-center space-x-2 mt-2">
                              <Badge
                                className={getRequestStatusColor(
                                  request.status,
                                )}
                              >
                                {request.status.replace("_", " ")}
                              </Badge>
                              <span className="text-xs text-gray-500">
                                Submitted:{" "}
                                {new Date(
                                  request.requestedAt,
                                ).toLocaleDateString()}
                              </span>
                              {request.completedAt && (
                                <span className="text-xs text-gray-500">
                                  Completed:{" "}
                                  {new Date(
                                    request.completedAt,
                                  ).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                            {request.response && (
                              <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
                                <strong>Response:</strong> {request.response}
                              </div>
                            )}
                          </div>
                        </div>
                        <Button
                          onClick={() =>
                            setState((prev) => ({
                              ...prev,
                              selectedRequest: request,
                            }))
                          }
                          size="sm"
                          variant="outline"
                        >
                          View Details
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Withdrawal Dialog */}
      {state.showWithdrawalDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Withdraw Consent</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-600">
                Please provide a reason for withdrawing your consent (optional):
              </p>
              <Textarea
                value={state.withdrawalReason}
                onChange={(e) =>
                  setState((prev) => ({
                    ...prev,
                    withdrawalReason: e.target.value,
                  }))
                }
                placeholder="Reason for withdrawal..."
                rows={3}
              />
              <div className="flex space-x-2">
                <Button
                  onClick={() =>
                    handleConsentWithdraw(state.showWithdrawalDialog!)
                  }
                  disabled={state.isUpdating}
                >
                  Withdraw Consent
                </Button>
                <Button
                  onClick={() =>
                    setState((prev) => ({
                      ...prev,
                      showWithdrawalDialog: null,
                      withdrawalReason: "",
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

export default GDPRConsent;
