import { apiFetch } from "./client";

export interface Anomaly {
  id: number;
  guard_id: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  speed_kmh: number;
  time_gap_seconds: number;
  distance_from_previous_m: number;
  distance_to_road_m: number;
  final_hybrid_score: number;
  final_risk_level: string;
  final_anomaly: boolean;
  anomaly_reason: string | null;
}

export interface Metrics {
  total_anomalies: number;
  total_actionable_events: number;
  critical_anomalies: number;
  high_anomalies: number;
  medium_anomalies: number;
  immediate_alerts: number;
}

export interface AnomalyResponse {
  data: Anomaly[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export async function getAnomalies(
  page: number = 1,
  limit: number = 10,
  riskLevel: string = "All"
): Promise<AnomalyResponse> {
  const params = new URLSearchParams();

  params.append("page", page.toString());
  params.append("limit", limit.toString());

  if (riskLevel !== "All") {
    params.append("risk_level", riskLevel);
  }

  return apiFetch<AnomalyResponse>(
    `/api/anomalies?${params.toString()}`
  );
}

export async function getMetrics(): Promise<Metrics> {
  return apiFetch<Metrics>("/api/metrics");
}

// =========================================================
// EVALUATION
// =========================================================

export interface EvaluationMethod {
  tp: number;
  fp: number;
  tn: number;
  fn: number;
  precision: number;
  recall: number;
  f1: number;
  false_positive_rate: number;
  false_negative_rate: number;
  support: number;
}

export interface EvaluationResponse {
  labeled_examples: number;

  comparison: {
    methods: Record<string, EvaluationMethod>;
    best_method: string | null;
  };

  gps_anomalies: Record<string, number>;

  checkin_anomalies: number;

  patrol_anomalies: number;

  patrol_types: Record<string, number>;
}

export async function getEvaluation(): Promise<EvaluationResponse> {
  return apiFetch<EvaluationResponse>(
    "/api/evaluation"
  );
}

// =========================================================
// THRESHOLDS
// =========================================================

export async function getThresholds(): Promise<
  Record<string, unknown>
> {
  return apiFetch<Record<string, unknown>>(
    "/api/config/thresholds"
  );
}

export async function updateThresholds(
  updates: Record<string, unknown>
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    "/api/config/thresholds",
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updates),
    }
  );
}