"""
Tool implementations and the TOOL_SPECS sent to Claude on every request.

TOOL_SPECS is a list of JSON schemas that tell the model what each tool does and
what arguments it takes. The descriptions act as instructions — small wording
changes here have a noticeable effect on when and how the model uses each tool.

TOOL_IMPL maps tool names to their Python implementations. run_tool() is the
single dispatch point the agent loop calls after parsing the model's response.
"""

from typing import Any

from . import database, glossary

# NULLIF(denominator, 0) prevents division-by-zero for channels with zero spend or clicks.
_METRIC_SQL: dict[str, str] = {
    "spend":       "SUM(dp.spend)",
    "revenue":     "SUM(dp.revenue)",
    "clicks":      "SUM(dp.clicks)",
    "impressions": "SUM(dp.impressions)",
    "conversions": "SUM(dp.conversions)",
    "roas":        "ROUND(SUM(dp.revenue) / NULLIF(SUM(dp.spend), 0), 2)",
    "cac":         "ROUND(SUM(dp.spend) / NULLIF(SUM(dp.conversions), 0), 2)",
    "cpc":         "ROUND(SUM(dp.spend) / NULLIF(SUM(dp.clicks), 0), 2)",
    "aov":         "ROUND(SUM(dp.revenue) / NULLIF(SUM(dp.conversions), 0), 2)",
    "ctr":         "ROUND(CAST(SUM(dp.clicks) AS REAL) / NULLIF(SUM(dp.impressions), 0), 4)",
    "cvr":         "ROUND(CAST(SUM(dp.conversions) AS REAL) / NULLIF(SUM(dp.clicks), 0), 4)",
}

# SQLite date expressions for each supported granularity level.
_GRANULARITY_SQL: dict[str, str] = {
    "day":   "dp.date",
    "week":  "strftime('%Y-W%W', dp.date)",
    "month": "strftime('%Y-%m', dp.date)",
}


def query_database(sql: str) -> dict[str, Any]:
    return database.run_select(sql)


def get_schema() -> dict[str, Any]:
    return {"schema": database.describe_schema()}


def define_metric(term: str) -> dict[str, Any]:
    hits = glossary.lookup(term)
    return {"definitions": hits or ["No glossary entry found."]}


def get_trend(
    metric: str,
    granularity: str = "week",
    dimension: str | None = None,
) -> dict[str, Any]:
    """Build and run a time-series query for any supported metric.

    The SELECT, JOIN, and GROUP BY clauses are assembled from the dimension
    argument so the same function handles blended totals, channel breakdowns,
    and campaign breakdowns without duplicating SQL.
    """
    metric_expr = _METRIC_SQL.get(metric.lower())
    if metric_expr is None:
        return {"error": f"Unknown metric '{metric}'. Choose from: {', '.join(_METRIC_SQL)}"}

    date_expr = _GRANULARITY_SQL.get(granularity)
    if date_expr is None:
        return {"error": "granularity must be 'day', 'week', or 'month'"}

    if dimension == "channel":
        select = f"ch.name AS dimension, {date_expr} AS period, {metric_expr} AS value"
        joins  = ("JOIN campaigns c ON dp.campaign_id = c.campaign_id "
                  "JOIN channels ch ON c.channel_id = ch.channel_id")
        group  = "ch.name, period"
    elif dimension == "campaign":
        select = f"c.name AS dimension, {date_expr} AS period, {metric_expr} AS value"
        joins  = "JOIN campaigns c ON dp.campaign_id = c.campaign_id"
        group  = "c.name, period"
    elif dimension is None:
        select = f"{date_expr} AS period, {metric_expr} AS value"
        joins  = ""
        group  = "period"
    else:
        return {"error": "dimension must be 'channel', 'campaign', or omitted"}

    sql = (
        f"SELECT {select} "
        f"FROM daily_performance dp {joins} "
        f"GROUP BY {group} ORDER BY period"
    ).strip()

    return database.run_select(sql)


TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "get_schema",
        "description": (
            "Returns the table and column layout of the marketing database. "
            "Call this before writing SQL if you are not sure which columns exist — "
            "it prevents hallucinated column names."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "query_database",
        "description": (
            "Runs a read-only SELECT against the marketing database and returns the rows. "
            "Write standard SQLite SQL. Do your aggregation in SQL (SUM, GROUP BY) rather "
            "than pulling raw rows. The database will reject anything that isn't a SELECT."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A single SQLite SELECT or WITH statement.",
                }
            },
            "required": ["sql"],
        },
    },
    {
        "name": "define_metric",
        "description": (
            "Looks up the business definition and formula for a marketing metric — "
            "things like ROAS, CAC, CTR, CVR, CPC, AOV, or incrementality. "
            "Call this before computing or explaining a metric so you use the right formula."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "term": {
                    "type": "string",
                    "description": "The metric name or phrase to look up, e.g. 'ROAS' or 'customer acquisition cost'.",
                }
            },
            "required": ["term"],
        },
    },
    {
        "name": "get_trend",
        "description": (
            "Aggregates a marketing metric over time and returns a time series. "
            "Use this for trend, week-over-week, or month-over-month questions. "
            "You can optionally break the series down by channel or campaign. "
            "Supported metrics: spend, revenue, clicks, impressions, conversions, "
            "roas, cac, cpc, aov, ctr, cvr."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": (
                        "Which metric to trend. One of: spend, revenue, clicks, "
                        "impressions, conversions, roas, cac, cpc, aov, ctr, cvr."
                    ),
                },
                "granularity": {
                    "type": "string",
                    "enum": ["day", "week", "month"],
                    "description": "How to bucket the time axis. Defaults to week.",
                },
                "dimension": {
                    "type": "string",
                    "enum": ["channel", "campaign"],
                    "description": "Split the series by this dimension. Omit for blended totals.",
                },
            },
            "required": ["metric"],
        },
    },
]

TOOL_IMPL = {
    "get_schema":      get_schema,
    "query_database":  query_database,
    "define_metric":   define_metric,
    "get_trend":       get_trend,
}


def run_tool(name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a tool call by name and return the result."""
    impl = TOOL_IMPL.get(name)
    if impl is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return impl(**tool_input)
    except TypeError as e:
        return {"error": f"Bad arguments for {name}: {e}"}
