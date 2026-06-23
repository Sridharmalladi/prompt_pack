/**
 * Normalizes a raw API response at the trust boundary.
 * Every component below this point can assume no array field is null.
 */

import type {
  AnalyzeResponse,
  AgenticInsights,
  Insight,
  Recommendation,
} from "./types";

function normalizeInsight(i: unknown): Insight {
  const raw = (i ?? {}) as Partial<Insight>;
  return {
    type: raw.type ?? "unknown",
    severity: raw.severity ?? "low",
    columns: raw.columns ?? [],
    message: raw.message ?? "",
  };
}

function normalizeRecommendation(r: unknown): Recommendation {
  const raw = (r ?? {}) as Partial<Recommendation>;
  return {
    category: raw.category ?? "other",
    action: raw.action ?? "",
    columns: raw.columns ?? [],
    rationale: raw.rationale ?? "",
  };
}

function normalizeInsights(ins: unknown): AgenticInsights | null {
  if (!ins) return null;
  const raw = ins as Partial<AgenticInsights>;
  return {
    summary: raw.summary ?? "",
    insights: (raw.insights ?? []).map(normalizeInsight),
    recommendations: (raw.recommendations ?? []).map(normalizeRecommendation),
    suggested_models: raw.suggested_models ?? [],
    leakage_risk_columns: raw.leakage_risk_columns ?? [],
  };
}

export function normalizeResponse(raw: AnalyzeResponse): AnalyzeResponse {
  return {
    ...raw,
    insights: normalizeInsights(raw.insights),
    profile: raw.profile
      ? {
          ...raw.profile,
          columns: raw.profile.columns ?? [],
          top_correlations: (raw.profile.top_correlations ?? [])
            .filter((e) => e.correlation != null && e.correlation === e.correlation)
            .map((e) => ({ ...e, correlation: e.correlation })),
          mutual_info: raw.profile.mutual_info ?? [],
          duplicate_count: raw.profile.duplicate_count ?? 0,
          duplicate_pct: raw.profile.duplicate_pct ?? 0,
          constant_columns: raw.profile.constant_columns ?? [],
          quasi_constant_columns: raw.profile.quasi_constant_columns ?? [],
        }
      : null,
    graph: raw.graph
      ? {
          ...raw.graph,
          nodes: raw.graph.nodes ?? [],
          edges: raw.graph.edges ?? [],
          multicollinearity_clusters: raw.graph.multicollinearity_clusters ?? [],
        }
      : null,
    semantic_labels: raw.semantic_labels ?? null,
    model_scores: raw.model_scores ?? [],
    preview_rows: raw.preview_rows ?? [],
  };
}
