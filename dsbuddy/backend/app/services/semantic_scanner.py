"""Haiku micro-call that assigns semantic labels to column names.

Only column names and the first 3 data rows are sent to the LLM — never
the full dataset. max_tokens is capped at 200 to keep cost negligible.
"""

import json
from typing import Any

import anthropic
from loguru import logger

import polars as pl

from app.core.config import settings

_CLIENT = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_SYSTEM_PROMPT = (
    "You are a data type classifier. "
    "Given column names and a few sample values, return a JSON object mapping "
    "each column name to a short semantic label (e.g. 'age', 'monetary_amount', "
    "'identifier', 'date', 'category', 'boolean', 'free_text', 'geographic', "
    "'percentage', 'score', 'unknown'). "
    "Respond with ONLY the JSON object, no explanation."
)


def scan(df: pl.DataFrame) -> dict[str, str]:
    """Call Haiku with column names + first 3 rows; return semantic label map.

    The payload sent to the LLM is intentionally minimal:
      - Column names only (no dtypes, no stats)
      - First 3 rows as a list of dicts
    This keeps cost under $0.001 per call and never leaks sensitive row data.
    """
    logger.info("Semantic scanner started", cols=df.width)

    payload = _build_payload(df)
    prompt = f"Columns and sample data:\n{json.dumps(payload, default=str)}"

    logger.debug("Sending semantic scan request to Haiku", payload_keys=list(payload["columns"]))

    try:
        response = _CLIENT.messages.create(
            model=settings.llm_class,
            max_tokens=200,
            temperature=0,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIStatusError as exc:
        logger.error("Haiku API error during semantic scan", status=exc.status_code, error=str(exc))
        return _fallback_labels(df)
    except anthropic.APIConnectionError as exc:
        logger.error("Haiku connection error during semantic scan", error=str(exc))
        return _fallback_labels(df)

    raw = response.content[0].text.strip()
    logger.debug("Semantic scan raw response", raw=raw)

    labels = _parse_labels(raw, df)
    logger.info("Semantic scanner complete", labels=labels)
    return labels


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_payload(df: pl.DataFrame) -> dict[str, Any]:
    """Build the minimal payload: column names + first 3 rows as list of dicts."""
    sample_rows = df.head(3).to_dicts()
    # Truncate any string values to 80 chars to avoid blowing the token budget
    truncated: list[dict[str, Any]] = []
    for row in sample_rows:
        truncated.append(
            {k: (str(v)[:80] if isinstance(v, str) else v) for k, v in row.items()}
        )
    return {"columns": df.columns, "sample_rows": truncated}


def _parse_labels(raw: str, df: pl.DataFrame) -> dict[str, str]:
    """Parse the JSON response; fall back to 'unknown' for any missing columns."""
    # Strip markdown code fences if Haiku wraps with them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        parsed: dict[str, str] = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Semantic scan JSON parse failed, using fallback", error=str(exc))
        return _fallback_labels(df)

    # Ensure every column has a label
    return {col: parsed.get(col, "unknown") for col in df.columns}


def _fallback_labels(df: pl.DataFrame) -> dict[str, str]:
    """Return 'unknown' for every column when the LLM call fails."""
    return {col: "unknown" for col in df.columns}
