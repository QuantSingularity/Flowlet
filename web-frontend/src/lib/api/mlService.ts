import { apiClient } from "./client";

export type RiskLevel = "low" | "medium" | "high" | "critical";
export type FraudAction =
  "allow" | "monitor" | "review" | "challenge" | "block";

export interface ChatReply {
  response: string;
  query_type: string;
  confidence: number;
  confidence_level: "high" | "medium" | "low";
  suggested_actions: string[];
  escalate_to_human: boolean;
  sources: string[];
  session_id: string | null;
  grounded_in_account_data: boolean;
  source: "local" | "llm";
  timestamp: string;
}

export interface RuleHit {
  name: string;
  score: number;
  fraud_type: string;
  description: string;
}

export interface FraudExplanation {
  summary: string;
  rule_hits: RuleHit[];
  primary_risk_factors: Array<{
    feature: string;
    description: string;
    importance: number;
  }>;
  model_scores: Record<string, number>;
}

export interface FraudAnalysis {
  transaction_id: string;
  fraud_analysis: {
    risk_score: number;
    risk_level: RiskLevel;
    risk_factors: string[];
    fraud_types: string[];
    recommended_action: string;
    confidence: number;
    explanation: FraudExplanation;
  };
  alert_created: boolean;
  alert_id: string | null;
  analysis_timestamp: string;
  model_version: string;
  mode: "model" | "rules_only" | null;
}

export type AlertStatus =
  | "pending"
  | "investigating"
  | "reviewed"
  | "confirmed"
  | "false_positive"
  | "dismissed"
  | "resolved";

export interface FraudAlertRecord {
  id: string;
  user_id: string | null;
  transaction_id: string | null;
  alert_type: string;
  status: AlertStatus;
  description: string | null;
  risk_score: number;
  risk_level: RiskLevel | null;
  action: FraudAction | null;
  model_version: string | null;
  created_at: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
  details?: {
    fraud_types?: string[];
    recommended_actions?: string[];
    rule_hits?: RuleHit[];
    confidence?: number;
  };
}

export interface AlertPage {
  alerts: FraudAlertRecord[];
  pagination: { page: number; per_page: number; total: number; pages: number };
}

export interface AlertQuery {
  page?: number;
  per_page?: number;
  status?: AlertStatus;
  risk_level?: RiskLevel;
}

export interface RiskAssessment {
  assessment_id: string;
  overall_risk_score: number;
  overall_risk_level: string;
  category_scores: Record<string, number>;
  risk_factors: Array<{
    factor_name: string;
    category: string;
    score: number;
    description: string;
    impact: string;
  }>;
  predictions: Record<string, number>;
  recommendations: string[];
  monitoring_alerts: string[];
  confidence_score: number;
}

export interface SpendingAnalysis {
  period_days: number;
  total_spent: number;
  total_income: number;
  net_cash_flow: number;
  category_totals: Record<string, number>;
  category_shares: Record<string, number>;
  monthly_trend: number;
  pattern: string;
  recurring: Array<{
    merchant: string;
    period_days: number;
    average_amount: number;
    next_expected: string;
  }>;
  insights: string[];
  alerts: string[];
  forecast: {
    projected_spend: number | null;
    lower_bound?: number;
    upper_bound?: number;
  };
  transaction_count: number;
}

export interface CategorizedTransaction {
  transaction_id: string;
  category: string;
  confidence: number;
  subcategory: string | null;
  tags: string[];
  is_recurring: boolean;
  anomaly_score: number;
  insights: string[];
}

export interface MlHealth {
  status: "healthy" | "degraded" | "disabled" | "error";
  enabled?: boolean;
  fraud_detection?: { mode: string; model_ready: boolean };
}

export interface FraudStatistics {
  total_transactions: number;
  fraud_detected: number;
  fraud_rate: number;
  risk_distribution: Record<RiskLevel, number>;
  fraud_types: Record<string, number>;
  average_risk_score: number;
}

export interface TransactionScreeningRequest {
  amount: number;
  currency?: string;
  transaction_id?: string;
  merchant_info?: { category?: string; location?: string; name?: string };
  device_fingerprint?: string;
}

const toQuery = (params: Record<string, string | number | undefined>) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") search.set(key, String(value));
  });
  const text = search.toString();
  return text ? `?${text}` : "";
};

export const mlService = {
  chat: (query: string, sessionId?: string | null) =>
    apiClient.post<ChatReply>("/ai/chatbot/query", {
      query,
      session_id: sessionId ?? undefined,
    }),

  screenTransaction: (payload: TransactionScreeningRequest) =>
    apiClient.post<FraudAnalysis>("/ai/fraud-detection/analyze", payload),

  listAlerts: (query: AlertQuery = {}) =>
    apiClient.get<AlertPage>(
      `/ai/fraud-detection/alerts${toQuery({ ...query })}`,
    ),

  resolveAlert: (
    alertId: string,
    resolution: Exclude<AlertStatus, "pending">,
    notes?: string,
  ) =>
    apiClient.post<{
      alert: FraudAlertRecord;
      model_feedback_applied: boolean;
    }>(`/ai/fraud-detection/alerts/${alertId}/resolve`, { resolution, notes }),

  respondToAlert: (alertId: string, response: "recognized" | "not_me") =>
    apiClient.post<{ alert: FraudAlertRecord }>(
      `/ai/fraud-detection/alerts/${alertId}/respond`,
      { response },
    ),

  assessRisk: () =>
    apiClient.post<{ assessment: RiskAssessment }>("/ai/risk/assess", {}),

  spendingAnalysis: (days = 90) =>
    apiClient.get<{ analysis: SpendingAnalysis }>(
      `/ai/spending/analysis${toQuery({ days })}`,
    ),

  categorize: (transactions: Array<Record<string, unknown>>) =>
    apiClient.post<{ count: number; results: CategorizedTransaction[] }>(
      "/ai/transactions/categorize",
      { transactions },
    ),

  correctCategory: (transaction: Record<string, unknown>, category: string) =>
    apiClient.post<{ success: boolean }>(
      "/ai/transactions/categorize/correction",
      { transaction, category },
    ),

  health: () => apiClient.get<MlHealth>("/ai/health"),

  fraudStatistics: (hours = 24) =>
    apiClient.get<{ statistics: FraudStatistics }>(
      `/fraud/statistics${toQuery({ hours })}`,
    ),
};

export default mlService;
