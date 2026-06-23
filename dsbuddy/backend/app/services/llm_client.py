"""Native Anthropic SDK reasoning core.

All dataset statistics are pre-computed by the profiler, graph builder, and
semantic scanner before any LLM call. The full summary is passed in a single
prompt; Claude returns structured JSON in one shot (no tool loop).

Flow:
  1. Build AnalysisContext from profile + graph + semantic labels + MI scores.
  2. Build a text summary of the dataset (no raw rows).
  3. Single Anthropic messages.create call — no tools.
  4. Parse Claude's JSON output with Pydantic.
  5. On parse failure: retry once with Haiku. On second failure: raise.
"""

import json
import re
from dataclasses import dataclass
from typing import Any

import anthropic
from loguru import logger
from pydantic import ValidationError

from app.core.config import settings
from app.models.requests import ProblemType
from app.models.responses import (
    AgenticInsights,
    ColumnProfile,
    DataProfile,
    FeatureGraph,
    Insight,
    Recommendation,
)

_CLIENT = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_MAX_TOKENS = 2000
_SMALL_ROW_THRESHOLD = 50_000
_SMALL_COL_THRESHOLD = 50

# ---------------------------------------------------------------------------
# System prompt (cached on every call)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an expert data scientist. \
You receive a complete statistical profile of a dataset — column types, \
missingness, correlations, mutual information scores, and multicollinearity clusters. \
You never see raw data rows.

Analyse the profile and respond with ONLY a JSON object matching this exact schema:
{
  "summary": "2-3 sentence overview of the dataset quality and key findings",
  "insights": [
    {
      "type": "leakage_risk|multicollinearity|imbalance|high_missingness|outliers|skew|other",
      "severity": "high|medium|low",
      "columns": ["col1"],
      "message": "specific, actionable finding"
    }
  ],
  "recommendations": [
    {
      "category": "preprocessing|feature_engineering|modeling|data_quality",
      "action": "concrete step to take",
      "columns": ["col1"],
      "rationale": "why this improves the model"
    }
  ],
  "suggested_models": ["e.g. RandomForest", "XGBoost"],
  "leakage_risk_columns": []
}
Output ONLY valid JSON — no markdown fences, no explanation."""

# ---------------------------------------------------------------------------
# Analysis context (holds pre-computed stats for summary building)
# ---------------------------------------------------------------------------

@dataclass
class AnalysisContext:
    """Immutable view of dataset stats used to build the prompt summary."""

    col_profiles: dict[str, ColumnProfile]
    target_column: str
    target_corr: dict[str, float]
    mutual_info: dict[str, float]
    graph: FeatureGraph
    semantic_labels: dict[str, str]
    problem_type: ProblemType
    sample_rows: int


def _build_context(
    profile: DataProfile,
    graph: FeatureGraph,
    semantic_labels: dict[str, str],
    target_column: str,
    problem_type: ProblemType,
) -> AnalysisContext:
    col_profiles = {cp.name: cp for cp in profile.columns}
    target_corr = {e.column: e.correlation for e in profile.top_correlations}
    mutual_info = {m.column: m.score for m in profile.mutual_info}
    return AnalysisContext(
        col_profiles=col_profiles,
        target_column=target_column,
        target_corr=target_corr,
        mutual_info=mutual_info,
        graph=graph,
        semantic_labels=semantic_labels,
        problem_type=problem_type,
        sample_rows=profile.sample_rows,
    )


# ---------------------------------------------------------------------------
# Dataset summary sent as the user prompt (no raw rows)
# ---------------------------------------------------------------------------

def _build_dataset_summary(
    ctx: AnalysisContext,
    target_column: str,
    problem_type: ProblemType,
) -> str:
    lines: list[str] = [
        f"Dataset: {ctx.sample_rows} rows, {len(ctx.col_profiles)} columns",
        f"Target column: '{target_column}'  Problem type: {problem_type.value}",
        "",
        "Column profiles:",
    ]
    for col, cp in ctx.col_profiles.items():
        label = ctx.semantic_labels.get(col, "unknown")
        if cp.mean is not None:
            lines.append(
                f"  {col} [{cp.dtype}] label={label} "
                f"missing={cp.missing_pct:.1f}% mean={cp.mean:.3g} "
                f"std={cp.std:.3g} skew={cp.skew:.2f} outliers={cp.outlier_count}"
            )
        else:
            unique = len(cp.top_values) if cp.top_values else "?"
            lines.append(
                f"  {col} [{cp.dtype}] label={label} "
                f"missing={cp.missing_pct:.1f}% unique≈{unique}"
            )

    if ctx.target_corr:
        lines += ["", "Top Pearson correlations with target:"]
        for col, corr in sorted(ctx.target_corr.items(), key=lambda x: abs(x[1]), reverse=True)[:10]:
            lines.append(f"  {col}: {corr:.4f}")

    if ctx.mutual_info:
        lines += ["", "Mutual information scores (higher = more predictive of target):"]
        top_mi = sorted(ctx.mutual_info.items(), key=lambda x: x[1], reverse=True)[:10]
        for col, score in top_mi:
            lines.append(f"  {col}: {score:.4f}")

    if ctx.graph.multicollinearity_clusters:
        lines += ["", "Multicollinearity clusters:"]
        for cl in ctx.graph.multicollinearity_clusters:
            lines.append(f"  {cl.columns}  max_corr={cl.max_correlation:.4f}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------

def _select_model(profile: DataProfile) -> str:
    """Use Sonnet for large/complex datasets; Haiku for everything else."""
    if profile.sample_rows > _SMALL_ROW_THRESHOLD or len(profile.columns) > _SMALL_COL_THRESHOLD:
        logger.info("Selecting Sonnet (complex dataset)", rows=profile.sample_rows, cols=len(profile.columns))
        return settings.llm_reason
    logger.info("Selecting Haiku (small dataset)", rows=profile.sample_rows, cols=len(profile.columns))
    return settings.llm_class


# ---------------------------------------------------------------------------
# Single-shot LLM call (no tools)
# ---------------------------------------------------------------------------

def _single_call(dataset_summary: str, model: str) -> str:
    """Pass the full pre-computed summary and return Claude's raw text response."""
    response = _CLIENT.messages.create(
        model=model,
        max_tokens=_MAX_TOKENS,
        temperature=0,
        system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{
            "role": "user",
            "content": [{"type": "text", "text": dataset_summary, "cache_control": {"type": "ephemeral"}}],
        }],
    )
    for block in response.content:
        if hasattr(block, "text"):
            return block.text
    return ""


# ---------------------------------------------------------------------------
# JSON parsing + retry
# ---------------------------------------------------------------------------

def _parse_insights(raw: str) -> AgenticInsights:
    """Parse Claude's JSON output into AgenticInsights. Raises ValueError on failure."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
        return AgenticInsights(**data)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise ValueError(f"Parse failed: {exc}") from exc


def _retry_with_haiku(raw: str, dataset_summary: str) -> AgenticInsights:
    """Ask Haiku to repair a malformed JSON response.

    The dataset summary is included so Haiku can fill in genuinely missing
    content rather than hallucinating. Raises ValueError on failure.
    """
    logger.warning("Retrying JSON parse with Haiku")
    if not raw or len(raw) < 10:
        raise ValueError("Raw response is empty or too short to repair.")

    schema_hint = (
        '{"summary":"...","insights":[{"type":"...","severity":"high|medium|low",'
        '"columns":[],"message":"..."}],"recommendations":[{"category":"...",'
        '"action":"...","columns":[],"rationale":"..."}],'
        '"suggested_models":[],"leakage_risk_columns":[]}'
    )
    repair_prompt = (
        f"Dataset context (for reference):\n{dataset_summary}\n\n"
        f"The following JSON is malformed or incomplete. "
        f"Fix it to exactly match this schema:\n{schema_hint}\n\n"
        f"Broken JSON:\n{raw}\n\nOutput ONLY valid JSON."
    )
    response = _CLIENT.messages.create(
        model=settings.llm_class,
        max_tokens=_MAX_TOKENS,
        temperature=0,
        messages=[{"role": "user", "content": repair_prompt}],
    )
    repaired = response.content[0].text if response.content else ""
    return _parse_insights(repaired)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def reason(
    profile: DataProfile,
    graph: FeatureGraph,
    semantic_labels: dict[str, str],
    target_column: str,
    problem_type: ProblemType,
) -> AgenticInsights:
    """Run one-shot reasoning and return structured insights.

    Raises ValueError if JSON parsing fails even after one Haiku retry.
    """
    logger.info("Agentic reasoning started", target=target_column, problem_type=problem_type.value)

    ctx = _build_context(profile, graph, semantic_labels, target_column, problem_type)
    model = _select_model(profile)
    summary = _build_dataset_summary(ctx, target_column, problem_type)

    try:
        raw = _single_call(summary, model)
        logger.debug("Raw LLM output", raw=raw[:500])
    except anthropic.APIStatusError as exc:
        logger.error("API error in reasoning loop", status=exc.status_code, error=str(exc))
        raise
    except anthropic.APIConnectionError as exc:
        logger.error("Connection error in reasoning loop", error=str(exc))
        raise

    try:
        insights = _parse_insights(raw)
    except ValueError:
        try:
            insights = _retry_with_haiku(raw, summary)
        except ValueError as exc:
            logger.error("JSON parse failed after retry", error=str(exc))
            raise

    logger.info("Agentic reasoning complete", insights_count=len(insights.insights))
    return insights
