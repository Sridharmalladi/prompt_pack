"""Feature relationship graph builder.

Constructs a weighted graph where nodes are columns and edges represent
strong correlations or mutual information scores between features.
Detects multicollinearity clusters using Union-Find over high-correlation pairs.
"""

import polars as pl
from loguru import logger

from app.models.responses import (
    FeatureGraph,
    GraphEdge,
    MulticollinearityCluster,
)

# Thresholds for including an edge
_CORR_THRESHOLD: float = 0.3

# Hard cap on edges kept (highest weight wins)
_MAX_EDGES: int = 15

# Threshold for grouping features into a multicollinearity cluster
_MULTICOLLINEARITY_THRESHOLD: float = 0.8


def build_graph(df: pl.DataFrame, target_column: str) -> FeatureGraph:
    """Build feature graph from a Polars DataFrame.

    Edges come from Pearson correlations > _CORR_THRESHOLD between all feature
    pairs. Keeps only the top _MAX_EDGES by absolute weight. Clusters are
    derived from the same correlation matrix at a higher threshold.

    The correlation matrix is computed exactly once and reused for edges,
    cluster detection, and cluster max-correlation calculation.
    """
    logger.info("Graph builder started", cols=df.width, target=target_column)

    numeric_cols = _numeric_feature_columns(df, target_column)
    corr_matrix = _compute_corr_matrix(df, numeric_cols)

    nodes = df.columns  # all columns are nodes regardless of type
    edges = _build_correlation_edges(corr_matrix)
    clusters = _detect_multicollinearity_clusters(numeric_cols, corr_matrix)

    logger.info(
        "Graph built",
        nodes=len(nodes),
        edges=len(edges),
        clusters=len(clusters),
    )
    return FeatureGraph(nodes=nodes, edges=edges, multicollinearity_clusters=clusters)


# ---------------------------------------------------------------------------
# Correlation matrix (single pass — reused by edges and clusters)
# ---------------------------------------------------------------------------

def _compute_corr_matrix(
    df: pl.DataFrame,
    numeric_cols: list[str],
) -> dict[tuple[str, str], float]:
    """Compute all pairwise Pearson correlations in one pass.

    Returns a dict keyed by (col_a, col_b) where col_a < col_b lexicographically
    (upper-triangle only, no duplicates).
    """
    cache: dict[tuple[str, str], float] = {}
    for i, col_a in enumerate(numeric_cols):
        for col_b in numeric_cols[i + 1:]:
            pair = df.select([col_a, col_b]).drop_nulls()
            if len(pair) < 2:
                continue
            corr_val = pair.select(
                pl.corr(col_a, col_b, method="pearson")
            ).item()
            if corr_val is not None:
                cache[(col_a, col_b)] = float(corr_val)
    return cache


# ---------------------------------------------------------------------------
# Edge construction
# ---------------------------------------------------------------------------

def _build_correlation_edges(
    corr_matrix: dict[tuple[str, str], float],
) -> list[GraphEdge]:
    """Return edges above _CORR_THRESHOLD, capped at _MAX_EDGES by abs weight."""
    edges: list[GraphEdge] = [
        GraphEdge(
            source=col_a,
            target=col_b,
            weight=round(corr, 6),
            edge_type="correlation",
        )
        for (col_a, col_b), corr in corr_matrix.items()
        if abs(corr) >= _CORR_THRESHOLD
    ]
    edges.sort(key=lambda e: abs(e.weight), reverse=True)
    return edges[:_MAX_EDGES]


# ---------------------------------------------------------------------------
# Multicollinearity clusters via Union-Find
# ---------------------------------------------------------------------------

def _detect_multicollinearity_clusters(
    numeric_cols: list[str],
    corr_matrix: dict[tuple[str, str], float],
) -> list[MulticollinearityCluster]:
    """Group features whose pairwise |correlation| >= _MULTICOLLINEARITY_THRESHOLD.

    Uses Union-Find so transitive relationships are captured:
    if A~B and B~C then {A, B, C} form one cluster.
    Returns only groups with 2+ members.
    """
    parent: dict[str, str] = {c: c for c in numeric_cols}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for (col_a, col_b), corr in corr_matrix.items():
        if abs(corr) >= _MULTICOLLINEARITY_THRESHOLD:
            union(col_a, col_b)

    # Group by root
    groups: dict[str, list[str]] = {}
    for col in numeric_cols:
        root = find(col)
        groups.setdefault(root, []).append(col)

    clusters: list[MulticollinearityCluster] = []
    for members in groups.values():
        if len(members) < 2:
            continue
        # Max correlation within the cluster — read from the already-computed matrix
        best = max(
            abs(corr_matrix.get((col_a, col_b), corr_matrix.get((col_b, col_a), 0.0)))
            for i, col_a in enumerate(members)
            for col_b in members[i + 1:]
        )
        clusters.append(
            MulticollinearityCluster(
                columns=sorted(members),
                max_correlation=round(best, 6),
            )
        )

    return clusters


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _numeric_feature_columns(df: pl.DataFrame, target_column: str) -> list[str]:
    """Return numeric columns excluding the target."""
    numeric_dtypes = {
        pl.Float32, pl.Float64,
        pl.Int8, pl.Int16, pl.Int32, pl.Int64,
        pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
    }
    return [
        c for c in df.columns
        if c != target_column and df[c].dtype in numeric_dtypes
    ]
