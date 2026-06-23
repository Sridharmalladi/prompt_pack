// TypeScript interfaces mirroring backend Pydantic v2 models exactly.

// ── Enums ─────────────────────────────────────────────────────────────────────

export type ProblemType = "classification" | "regression" | "clustering" | "unknown";

// Matches the labels the semantic scanner actually returns (lowercase)
export type SemanticLabel =
  | "age"
  | "monetary_amount"
  | "identifier"
  | "date"
  | "category"
  | "boolean"
  | "free_text"
  | "geographic"
  | "percentage"
  | "score"
  | "unknown";

export type RiskSeverity = "low" | "medium" | "high";

// ── File / Upload ──────────────────────────────────────────────────────────────

export interface FileInfo {
  filename: string;
  size_bytes: number;
  row_count: number;
  column_count: number;
  columns: string[];
}

export interface ErrorResponse {
  error: string;
  code: string;
  where: string;
}

// ── Profiler ───────────────────────────────────────────────────────────────────

export interface ColumnProfile {
  name: string;
  dtype: string;
  missing_pct: number;
  mean: number | null;
  std: number | null;
  skew: number | null;
  outlier_count: number | null;
  top_values: Record<string, number> | null;
}

export interface CorrelationEdge {
  column: string;
  correlation: number;
}

export interface MutualInfoScore {
  column: string;
  score: number;
}

export interface ClassDistribution {
  counts: Record<string, number>;
  imbalanced: boolean;
}

export interface DataProfile {
  sampled: boolean;
  sample_rows: number;
  columns: ColumnProfile[];
  top_correlations: CorrelationEdge[];
  mutual_info: MutualInfoScore[];
  class_distribution: ClassDistribution | null;
  duplicate_count: number;
  duplicate_pct: number;
  constant_columns: string[];
  quasi_constant_columns: string[];
}

// ── Graph Builder ──────────────────────────────────────────────────────────────

// Backend returns nodes as plain strings (column names), not objects
export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
  edge_type: "correlation" | "mutual_info";
}

export interface MulticollinearityCluster {
  columns: string[];
  max_correlation: number;
}

export interface FeatureGraph {
  nodes: string[];
  edges: GraphEdge[];
  multicollinearity_clusters: MulticollinearityCluster[];
}

// ── Agentic Insights ───────────────────────────────────────────────────────────

export interface Insight {
  type: string;
  severity: RiskSeverity;
  columns: string[];
  message: string;
}

export interface Recommendation {
  category: string;
  action: string;
  columns: string[];
  rationale: string;
}

export interface AgenticInsights {
  summary: string;
  insights: Insight[];
  recommendations: Recommendation[];
  suggested_models: string[];
  leakage_risk_columns: string[];
}

// ── Model Training ─────────────────────────────────────────────────────────────

export interface ModelFitResult {
  model_name: string;
  metrics: Record<string, number>;
  fit_time_seconds: number;
  error: string | null;
}

// ── Top-level Analyze Response ─────────────────────────────────────────────────

export interface AnalyzeResponse {
  file_info: FileInfo;
  profile: DataProfile | null;
  graph: FeatureGraph | null;
  semantic_labels: Record<string, string> | null;
  insights: AgenticInsights | null;
  model_scores: ModelFitResult[];
  preview_rows: Record<string, unknown>[];
}

// ── Chat ───────────────────────────────────────────────────────────────────────

export interface ChatRequest {
  session_id: string;
  question: string;
  context_summary: string;
  context_insights?: string;
}

export interface ChatResponse {
  answer: string;
  messages_remaining: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}


// ── Health ─────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
}

// ── Upload Form State ──────────────────────────────────────────────────────────

export interface UploadFormState {
  file: File | null;
  target_column: string;
  problem_type: ProblemType;
  domain: string;
}

export type UploadStep =
  | "idle"
  | "uploading"
  | "scanning"
  | "profiling"
  | "graph"
  | "training"
  | "reasoning"
  | "done"
  | "error";
