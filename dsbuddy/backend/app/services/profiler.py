"""Polars-based dataset profiler — no pandas anywhere.

Computes per-column stats, target correlations, mutual information,
class distribution, and IQR outlier counts entirely in Polars + scikit-learn.
"""

from typing import Optional

import polars as pl
from loguru import logger
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression

from app.core.config import settings
from app.models.requests import ProblemType
from app.models.responses import (
    ClassDistribution,
    ColumnProfile,
    CorrelationEdge,
    DataProfile,
    MutualInfoScore,
)

_QUASI_CONSTANT_THRESHOLD = 0.01  # < 1% unique values → quasi-constant

# Ratio below which a classification target is flagged as imbalanced
_IMBALANCE_THRESHOLD = 0.2

# If target has <= this many unique values and is numeric, treat as classification
_MAX_CLASSIFICATION_CARDINALITY = 20

_NUMERIC_DTYPES = frozenset({
    pl.Float32, pl.Float64,
    pl.Int8, pl.Int16, pl.Int32, pl.Int64,
    pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
})


def _effective_problem_type(df: pl.DataFrame, target_column: str, problem_type: ProblemType) -> ProblemType:
    """Resolve ProblemType.unknown to classification or regression by inspecting the target.

    Rules (in order):
    - Non-numeric target → classification (string/categorical columns)
    - Numeric target with <= _MAX_CLASSIFICATION_CARDINALITY unique values → classification
    - Anything else → regression
    """
    if problem_type != ProblemType.unknown:
        return problem_type
    target = df[target_column]
    if target.dtype not in _NUMERIC_DTYPES:
        return ProblemType.classification
    if target.n_unique() <= _MAX_CLASSIFICATION_CARDINALITY:
        return ProblemType.classification
    return ProblemType.regression


def profile(
    df: pl.DataFrame,
    target_column: str,
    problem_type: ProblemType,
    pre_sampled: bool = False,
) -> DataProfile:
    """Run the full profiling pipeline and return a DataProfile.

    When pre_sampled=True the caller already reduced the frame; this function
    records that fact without sampling again. Otherwise it samples internally.
    """
    logger.info("Profiler started", rows=df.height, cols=df.width, target=target_column)

    sampled = pre_sampled
    if not pre_sampled and df.height > settings.sample_rows:
        df = df.sample(n=settings.sample_rows, seed=42)
        sampled = True
        logger.info("Sampled dataset", sample_rows=settings.sample_rows)

    resolved_type = _effective_problem_type(df, target_column, problem_type)

    column_profiles = [_profile_column(df, col) for col in df.columns]
    top_corr = _top_correlations(df, target_column)
    mi_scores = _mutual_info(df, target_column, resolved_type)
    class_dist = _class_distribution(df, target_column, resolved_type)

    duplicate_count = int(df.is_duplicated().sum())
    duplicate_pct = round(duplicate_count / df.height * 100, 2) if df.height > 0 else 0.0
    constant_cols = [c for c in df.columns if df[c].n_unique() == 1]
    quasi_cols = [
        c for c in df.columns
        if c not in constant_cols and df[c].n_unique() / df.height < _QUASI_CONSTANT_THRESHOLD
    ]

    logger.info("Profiler complete", target=target_column)
    return DataProfile(
        sampled=sampled,
        sample_rows=df.height,
        columns=column_profiles,
        top_correlations=top_corr,
        mutual_info=mi_scores,
        class_distribution=class_dist,
        duplicate_count=duplicate_count,
        duplicate_pct=duplicate_pct,
        constant_columns=constant_cols,
        quasi_constant_columns=quasi_cols,
    )


# ---------------------------------------------------------------------------
# Per-column stats
# ---------------------------------------------------------------------------

def _profile_column(df: pl.DataFrame, col: str) -> ColumnProfile:
    """Compute dtype, missingness, numeric stats, and outlier count for one column."""
    series = df[col]
    dtype_str = str(series.dtype)
    total = len(series)
    missing_count = series.null_count()
    missing_pct = (missing_count / total * 100) if total > 0 else 0.0

    mean = std = skew = outlier_count = None
    top_values: Optional[dict[str, int]] = None

    if series.dtype in _NUMERIC_DTYPES:
        numeric = series.drop_nulls().cast(pl.Float64)
        if len(numeric) > 0:
            mean = float(numeric.mean())  # type: ignore[arg-type]
            std = float(numeric.std())    # type: ignore[arg-type]
            skew = _polars_skew(numeric)
            outlier_count = _iqr_outlier_count(numeric)
    else:
        # Categorical / string: top 10 most frequent values
        counts = (
            df.group_by(col)
            .agg(pl.len().alias("n"))
            .sort("n", descending=True)
            .head(10)
        )
        top_values = {
            str(row[col]): int(row["n"])
            for row in counts.to_dicts()
        }

    return ColumnProfile(
        name=col,
        dtype=dtype_str,
        missing_pct=round(missing_pct, 4),
        mean=round(mean, 6) if mean is not None else None,
        std=round(std, 6) if std is not None else None,
        skew=round(skew, 6) if skew is not None else None,
        outlier_count=outlier_count,
        top_values=top_values,
    )


def _polars_skew(series: pl.Series) -> float:
    """Compute Pearson's moment skewness using Polars expressions."""
    n = len(series)
    if n < 3:
        return 0.0
    mu = float(series.mean())  # type: ignore[arg-type]
    sigma = float(series.std())  # type: ignore[arg-type]
    if sigma == 0:
        return 0.0
    centred = series - mu
    return float((centred.pow(3).mean()) / (sigma ** 3))  # type: ignore[arg-type]


def _iqr_outlier_count(series: pl.Series) -> int:
    """Count values outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR]."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    if q1 is None or q3 is None:
        return 0
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return int(((series < lower) | (series > upper)).sum())


# ---------------------------------------------------------------------------
# Correlations
# ---------------------------------------------------------------------------

def _top_correlations(df: pl.DataFrame, target_column: str) -> list[CorrelationEdge]:
    """Return the top 10 Pearson correlations between numeric features and the target.

    Skips columns that are non-numeric or identical to the target.
    """
    target = df[target_column]
    if target.dtype not in _NUMERIC_DTYPES:
        logger.debug("Target is non-numeric, skipping correlations", target=target_column)
        return []

    target_f = target.drop_nulls().cast(pl.Float64)
    edges: list[CorrelationEdge] = []

    for col in df.columns:
        if col == target_column:
            continue
        series = df[col]
        if series.dtype not in _NUMERIC_DTYPES:
            continue
        # Align on non-null rows of both columns
        pair = df.select([col, target_column]).drop_nulls()
        if len(pair) < 2:
            continue
        corr_val = pair.select(
            pl.corr(col, target_column, method="pearson")
        ).item()
        if corr_val is not None and corr_val == corr_val:  # skip None and NaN
            edges.append(CorrelationEdge(column=col, correlation=round(float(corr_val), 6)))

    edges.sort(key=lambda e: abs(e.correlation), reverse=True)
    return edges[:10]


# ---------------------------------------------------------------------------
# Mutual information
# ---------------------------------------------------------------------------

def _mutual_info(
    df: pl.DataFrame,
    target_column: str,
    problem_type: ProblemType,
) -> list[MutualInfoScore]:
    """Compute scikit-learn mutual information between numeric features and target.

    Only numeric columns are included; target column is excluded.
    Falls back to empty list if fewer than 2 usable features or target has issues.
    """
    numeric_cols = [
        c for c in df.columns
        if c != target_column and df[c].dtype in _NUMERIC_DTYPES
    ]
    if not numeric_cols:
        return []

    # Drop rows where any selected column or target is null
    cols_to_use = numeric_cols + [target_column]
    clean = df.select(cols_to_use).drop_nulls()
    if len(clean) < 10:
        logger.warning("Too few rows for mutual info after dropping nulls")
        return []

    X = clean.select(numeric_cols).to_numpy()
    y = clean[target_column].to_numpy()

    try:
        if problem_type == ProblemType.classification:
            scores = mutual_info_classif(X, y, random_state=42)
        else:
            scores = mutual_info_regression(X, y, random_state=42)
    except Exception as exc:
        logger.error("Mutual info computation failed", error=str(exc))
        return []

    result = [
        MutualInfoScore(column=col, score=round(float(score), 6))
        for col, score in zip(numeric_cols, scores)
    ]
    result.sort(key=lambda m: m.score, reverse=True)
    return result


# ---------------------------------------------------------------------------
# Class distribution
# ---------------------------------------------------------------------------

def _class_distribution(
    df: pl.DataFrame,
    target_column: str,
    problem_type: ProblemType,
) -> Optional[ClassDistribution]:
    """Compute value counts for classification targets and flag imbalance.

    Imbalance: the smallest class is less than _IMBALANCE_THRESHOLD of the largest.
    """
    if problem_type != ProblemType.classification:
        return None

    counts_df = (
        df.group_by(target_column)
        .agg(pl.len().alias("n"))
        .sort("n", descending=True)
    )
    counts = {str(row[target_column]): int(row["n"]) for row in counts_df.to_dicts()}
    if not counts:
        return None

    values = list(counts.values())
    imbalanced = (min(values) / max(values)) < _IMBALANCE_THRESHOLD

    return ClassDistribution(counts=counts, imbalanced=imbalanced)
