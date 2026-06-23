"""Reads an uploaded file into a Polars DataFrame with upfront validation."""

import io
from typing import Literal

import polars as pl
from loguru import logger

from app.core.config import settings

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".csv", ".xlsx", ".parquet"})
MAX_BYTES: int = settings.max_file_size_mb * 1024 * 1024


def load_dataframe(
    content: bytes,
    filename: str,
) -> pl.DataFrame:
    """Parse file bytes into a Polars DataFrame.

    Raises ValueError for unsupported format, oversized file, or too many columns.
    Raises RuntimeError if parsing fails for an unexpected reason.
    """
    logger.info("Loading file", filename=filename, size_bytes=len(content))

    ext = _extension(filename)
    _validate_extension(ext, filename)
    _validate_size(content, filename)

    df = _parse(content, ext, filename)
    _validate_columns(df, filename)

    logger.info(
        "File loaded",
        filename=filename,
        rows=df.height,
        cols=df.width,
    )
    return df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extension(filename: str) -> str:
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot != -1 else ""


def _validate_extension(ext: str, filename: str) -> None:
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '{ext}'. "
            f"Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )


def _validate_size(content: bytes, filename: str) -> None:
    if len(content) > MAX_BYTES:
        mb = len(content) / (1024 * 1024)
        raise ValueError(
            f"File '{filename}' is {mb:.1f} MB — limit is {settings.max_file_size_mb} MB."
        )


def _validate_columns(df: pl.DataFrame, filename: str) -> None:
    if df.width > settings.max_columns:
        raise ValueError(
            f"File '{filename}' has {df.width} columns — limit is {settings.max_columns}."
        )
    if df.height == 0:
        raise ValueError(f"File '{filename}' is empty (0 rows).")


def _parse(content: bytes, ext: str, filename: str) -> pl.DataFrame:
    """Dispatch to the correct Polars reader based on extension."""
    buf = io.BytesIO(content)
    try:
        if ext == ".csv":
            return pl.read_csv(buf, infer_schema_length=10_000)
        if ext == ".xlsx":
            return pl.read_excel(buf)
        if ext == ".parquet":
            return pl.read_parquet(buf)
    except Exception as exc:
        logger.error("Parse error", filename=filename, error=str(exc))
        raise RuntimeError(f"Failed to parse '{filename}': {exc}") from exc
    raise ValueError(f"Unhandled extension '{ext}'")
