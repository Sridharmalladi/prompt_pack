"""Quick sklearn model training — returns real cross-validated scores.

Caps at 10k rows, 12-second timeout per model. Works without pandas:
converts Polars directly to numpy, handles nulls in Polars before handing
off to sklearn.
"""

import math
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

import numpy as np
import polars as pl
from loguru import logger
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import OrdinalEncoder

from app.models.requests import ProblemType
from app.models.responses import ModelFitResult

_MAX_ROWS = 10_000
_CV_FOLDS = 3
_TIMEOUT_SECONDS = 12

_NUMERIC_DTYPES = frozenset({
    pl.Float32, pl.Float64,
    pl.Int8, pl.Int16, pl.Int32, pl.Int64,
    pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
})


def train(
    df: pl.DataFrame,
    target_column: str,
    problem_type: ProblemType,
) -> list[ModelFitResult]:
    """Train 3 models and return cross-validated scores for each.

    Never raises — callers can always treat model_scores as optional enrichment.
    """
    try:
        return _train(df, target_column, problem_type)
    except Exception as exc:
        logger.error("Model training outer error", error=str(exc))
        return []


def _train(df: pl.DataFrame, target: str, problem_type: ProblemType) -> list[ModelFitResult]:
    if df.height > _MAX_ROWS:
        df = df.sample(n=_MAX_ROWS, seed=42)

    feature_cols = [c for c in df.columns if c != target]
    if not feature_cols:
        return []

    numeric_cols = [c for c in feature_cols if df[c].dtype in _NUMERIC_DTYPES]
    categorical_cols = [c for c in feature_cols if c not in numeric_cols]

    # ── Build X (numpy float64, no nulls) ─────────────────────────────────────
    parts: list[np.ndarray] = []

    if numeric_cols:
        # Fill each numeric null with column median in Polars, then convert to numpy
        filled = {}
        for col in numeric_cols:
            series = df[col]
            median = series.drop_nulls().median()
            filled[col] = series.fill_null(median if median is not None else 0.0).cast(pl.Float64)
        num_arr = pl.DataFrame(filled).to_numpy()
        parts.append(num_arr)

    if categorical_cols:
        # Fill nulls with the most frequent value, cast to string
        filled = {}
        for col in categorical_cols:
            series = df[col].cast(pl.Utf8)
            mode_vals = series.drop_nulls().mode()
            fill_val = mode_vals[0] if len(mode_vals) > 0 else "__missing__"
            filled[col] = series.fill_null(fill_val)
        cat_str = pl.DataFrame(filled).to_numpy(allow_copy=True)
        # OrdinalEncoder handles object/string arrays
        enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        cat_arr = enc.fit_transform(cat_str).astype(np.float64)
        parts.append(cat_arr)

    if not parts:
        return []

    X = np.hstack(parts)

    # ── Build y ────────────────────────────────────────────────────────────────
    y_series = df[target]
    if y_series.dtype in _NUMERIC_DTYPES:
        median = y_series.drop_nulls().median()
        y = y_series.fill_null(median if median is not None else 0).cast(pl.Float64).to_numpy()
    else:
        y_str = y_series.cast(pl.Utf8).fill_null("__missing__").to_numpy(allow_copy=True)
        label_enc = OrdinalEncoder()
        y = label_enc.fit_transform(y_str.reshape(-1, 1)).ravel()

    # ── Determine task type ────────────────────────────────────────────────────
    if problem_type == ProblemType.unknown:
        n_unique = len(np.unique(y[~np.isnan(y.astype(float))]))
        is_classification = df[target].dtype not in _NUMERIC_DTYPES or n_unique <= 20
    else:
        is_classification = problem_type == ProblemType.classification

    if is_classification:
        y = y.astype(np.int64)
        n_classes = len(np.unique(y))
        models = [
            ("Logistic Regression", LogisticRegression(max_iter=300, random_state=42)),
            ("Random Forest", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)),
            ("Gradient Boosting", GradientBoostingClassifier(n_estimators=100, random_state=42)),
        ]
        primary_scoring = "accuracy"
        secondary_scoring = "f1_weighted"
        auc_scoring = "roc_auc" if n_classes == 2 else None
    else:
        y = y.astype(np.float64)
        n_classes = 0
        models = [
            ("Ridge Regression", Ridge()),
            ("Random Forest", RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)),
            ("Gradient Boosting", GradientBoostingRegressor(n_estimators=100, random_state=42)),
        ]
        primary_scoring = "r2"
        secondary_scoring = "neg_root_mean_squared_error"
        auc_scoring = None

    # Drop rows where y is NaN
    y_float = y.astype(float)
    valid_mask = ~np.isnan(y_float)
    X = X[valid_mask]
    y = y[valid_mask]

    if len(y) < _CV_FOLDS:
        logger.warning("Too few rows after cleaning for CV", rows=len(y))
        return []

    # ── Train each model ───────────────────────────────────────────────────────
    results = []
    for name, estimator in models:
        result = _score_model(name, estimator, X, y, primary_scoring, secondary_scoring, auc_scoring)
        results.append(result)
        logger.info("Model scored", name=name, metrics=result.metrics, error=result.error)

    return results


def _score_model(
    name: str,
    estimator,
    X: np.ndarray,
    y: np.ndarray,
    primary: str,
    secondary: str,
    auc: str | None,
) -> ModelFitResult:
    t0 = time.perf_counter()

    def run():
        metrics: dict[str, float] = {}
        scores = cross_val_score(estimator, X, y, scoring=primary, cv=_CV_FOLDS)
        metrics[_label(primary)] = _safe(float(scores.mean()))
        scores2 = cross_val_score(estimator, X, y, scoring=secondary, cv=_CV_FOLDS)
        metrics[_label(secondary)] = _safe(abs(float(scores2.mean())))
        if auc:
            try:
                auc_scores = cross_val_score(estimator, X, y, scoring=auc, cv=_CV_FOLDS)
                metrics[_label(auc)] = _safe(float(auc_scores.mean()))
            except Exception:
                pass
        return metrics

    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(run)
        try:
            metrics = future.result(timeout=_TIMEOUT_SECONDS)
            return ModelFitResult(
                model_name=name,
                metrics=metrics,
                fit_time_seconds=round(time.perf_counter() - t0, 2),
            )
        except FuturesTimeout:
            return ModelFitResult(
                model_name=name,
                metrics={},
                fit_time_seconds=round(time.perf_counter() - t0, 2),
                error="Timed out",
            )
        except Exception as exc:
            return ModelFitResult(
                model_name=name,
                metrics={},
                fit_time_seconds=round(time.perf_counter() - t0, 2),
                error=str(exc)[:200],
            )


def _label(scoring: str) -> str:
    return {
        "accuracy": "accuracy",
        "f1_weighted": "f1",
        "roc_auc": "auc",
        "r2": "r2",
        "neg_root_mean_squared_error": "rmse",
    }.get(scoring, scoring)


def _safe(v: float) -> float:
    return round(v, 4) if not (math.isnan(v) or math.isinf(v)) else 0.0
