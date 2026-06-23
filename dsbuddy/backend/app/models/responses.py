"""Pydantic v2 response models."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """Basic metadata returned immediately after a file is accepted."""

    filename: str
    size_bytes: int
    row_count: int
    column_count: int
    columns: list[str]


class ErrorResponse(BaseModel):
    """Standard error envelope returned on all 4xx / 5xx responses."""

    error: str
    code: str
    where: str


class ColumnProfile(BaseModel):
    """Per-column statistics computed by the profiler."""

    name: str
    dtype: str
    missing_pct: float = Field(ge=0.0, le=100.0)
    mean: Optional[float] = None
    std: Optional[float] = None
    skew: Optional[float] = None
    outlier_count: Optional[int] = None
    top_values: Optional[dict[str, int]] = None


class CorrelationEdge(BaseModel):
    """Pearson correlation between a feature and the target."""

    column: str
    correlation: float


class MutualInfoScore(BaseModel):
    """Mutual information score between a feature and the target."""

    column: str
    score: float


class ClassDistribution(BaseModel):
    """Class value counts and imbalance flag for classification targets."""

    counts: dict[str, int]
    imbalanced: bool


class DataProfile(BaseModel):
    """Full profiler output wired into AnalyzeResponse."""

    sampled: bool
    sample_rows: int
    columns: list[ColumnProfile]
    top_correlations: list[CorrelationEdge]
    mutual_info: list[MutualInfoScore]
    class_distribution: Optional[ClassDistribution] = None
    duplicate_count: int = 0
    duplicate_pct: float = 0.0
    constant_columns: list[str] = Field(default_factory=list)
    quasi_constant_columns: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    """Weighted edge between two columns in the feature graph."""

    source: str
    target: str
    weight: float
    edge_type: str  # "correlation" | "mutual_info"


class MulticollinearityCluster(BaseModel):
    """Group of features that are highly correlated with each other."""

    columns: list[str]
    max_correlation: float


class FeatureGraph(BaseModel):
    """Feature relationship graph with edges and multicollinearity clusters."""

    nodes: list[str]
    edges: list[GraphEdge]
    multicollinearity_clusters: list[MulticollinearityCluster]


class Insight(BaseModel):
    """A single data-quality or modelling concern flagged by the agent."""

    type: str  # e.g. leakage_risk | multicollinearity | imbalance | high_missingness | outliers | skew
    severity: Literal["high", "medium", "low"]
    columns: list[str] = Field(default_factory=list)
    message: str


class Recommendation(BaseModel):
    """A concrete action suggested by the agent."""

    category: str  # preprocessing | feature_engineering | modeling | data_quality
    action: str
    columns: list[str] = Field(default_factory=list)
    rationale: str


class AgenticInsights(BaseModel):
    """Structured output from the Claude reasoning loop."""

    summary: str
    insights: list[Insight] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    suggested_models: list[str] = Field(default_factory=list)
    leakage_risk_columns: list[str] = Field(default_factory=list)


class NotebookResponse(BaseModel):
    """Response for POST /generate-notebook."""

    notebook_json: str
    cell_count: int


class ChatResponse(BaseModel):
    """Response for POST /chat."""

    answer: str
    messages_remaining: int
    session_id: str


class ModelFitResult(BaseModel):
    """Cross-validated score for one sklearn model."""

    model_name: str
    metrics: dict[str, float]
    fit_time_seconds: float
    error: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Top-level response for POST /analyze (grows with each slice)."""

    file_info: FileInfo
    semantic_labels: Optional[dict[str, str]] = None
    profile: Optional[DataProfile] = None
    graph: Optional[FeatureGraph] = None
    insights: Optional[AgenticInsights] = None
    model_scores: list[ModelFitResult] = Field(default_factory=list)
    preview_rows: list[dict[str, object]] = Field(default_factory=list)
