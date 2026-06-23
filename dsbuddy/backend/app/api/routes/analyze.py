"""POST /analyze — streaming SSE analysis pipeline."""

import asyncio
import json
import math
from typing import Annotated, AsyncGenerator, Optional

import anthropic
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from loguru import logger

from app.core.config import settings
from app.models.requests import ProblemType
from app.models.responses import AnalyzeResponse, FileInfo
from app.services import graph_builder as graph_svc
from app.services import llm_client
from app.services import profiler as profiler_svc
from app.services import semantic_scanner as scanner_svc
from app.services import model_trainer
from app.services.file_loader import load_dataframe

router = APIRouter(prefix="/analyze", tags=["analyze"])


def _sse(step: str, message: str, data: str | None = None) -> str:
    """Format one SSE event line."""
    if data is not None:
        return f'data: {{"step":"{step}","message":{_json_str(message)},"data":{data}}}\n\n'
    return f'data: {{"step":"{step}","message":{_json_str(message)}}}\n\n'


def _json_str(s: str) -> str:
    return json.dumps(s)


async def _stream(
    df,
    file_info: FileInfo,
    target_column: str,
    problem_type: ProblemType,
    pre_sampled: bool,
) -> AsyncGenerator[str, None]:
    """Async generator that runs each analysis step and yields SSE events."""
    try:
        # Step 1 — semantic scanning
        yield _sse("scanning", "Labeling columns with Claude Haiku...")
        semantic_labels = await asyncio.to_thread(scanner_svc.scan, df)
        yield _sse("scanning_done", "Column labels ready")

        # Step 2 — statistical profiling
        yield _sse("profiling", "Computing 200+ statistical measures...")
        data_profile = await asyncio.to_thread(
            profiler_svc.profile, df, target_column, problem_type, pre_sampled
        )
        yield _sse("profiling_done", "Statistics computed")

        # Step 3 — feature graph
        yield _sse("graph", "Mapping feature relationships...")
        feature_graph = await asyncio.to_thread(graph_svc.build_graph, df, target_column)
        yield _sse("graph_done", "Feature graph ready")

        # Step 4 — model training
        yield _sse("training", "Training models and measuring accuracy...")
        model_scores = await asyncio.to_thread(model_trainer.train, df, target_column, problem_type)
        yield _sse("training_done", f"Trained {len(model_scores)} models")

        # Step 5 — LLM reasoning
        agentic_insights = None
        yield _sse("reasoning", "Claude Sonnet is thinking...")
        try:
            agentic_insights = await asyncio.to_thread(
                llm_client.reason,
                profile=data_profile,
                graph=feature_graph,
                semantic_labels=semantic_labels,
                target_column=target_column,
                problem_type=problem_type,
            )
        except anthropic.RateLimitError:
            logger.warning("Rate limit hit during reasoning — insights skipped")
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
            logger.warning("Agentic reasoning skipped", error=str(exc))
        except ValueError as exc:
            logger.error("Insights parse failed after retry", error=str(exc))

        # Build preview rows — sanitize non-JSON-safe floats
        preview_rows = _safe_preview(df.head(20).to_dicts())

        result = AnalyzeResponse(
            file_info=file_info,
            semantic_labels=semantic_labels,
            profile=data_profile,
            graph=feature_graph,
            insights=agentic_insights,
            model_scores=model_scores,
            preview_rows=preview_rows,
        )

        yield _sse("done", "Analysis complete", data=result.model_dump_json())

    except Exception as exc:
        logger.error("Stream analysis failed", error=str(exc))
        yield f'data: {{"step":"error","message":{json.dumps(str(exc))}}}\n\n'


def _safe_preview(rows: list[dict]) -> list[dict]:
    """Replace NaN/Infinity floats with None so JSON serialization is valid."""
    out = []
    for row in rows:
        clean = {}
        for k, v in row.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                clean[k] = None
            else:
                clean[k] = v
        out.append(clean)
    return out


@router.post("")
async def analyze(
    file: Annotated[UploadFile, File(description="CSV, XLSX, or Parquet dataset")],
    target_column: Annotated[str, Form(description="Name of the prediction target column")],
    problem_type: Annotated[ProblemType, Form()] = ProblemType.unknown,
    domain: Annotated[Optional[str], Form(description="Optional domain hint")] = None,
) -> StreamingResponse:
    logger.info(
        "Analyze request received",
        filename=file.filename,
        target_column=target_column,
        problem_type=problem_type,
    )

    content = await file.read()

    try:
        df = load_dataframe(content, file.filename or "upload")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": str(exc), "code": "INVALID_FILE", "where": "file_loader"},
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(exc), "code": "PARSE_ERROR", "where": "file_loader"},
        ) from exc

    if target_column not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": f"Target column '{target_column}' not found.",
                "code": "MISSING_TARGET",
                "where": "analyze",
            },
        )

    original_row_count = df.height
    pre_sampled = df.height > settings.sample_rows
    if pre_sampled:
        df = df.sample(n=settings.sample_rows, seed=42)
        logger.info("Pre-sampled", original=original_row_count, sample=df.height)

    file_info = FileInfo(
        filename=file.filename or "upload",
        size_bytes=len(content),
        row_count=original_row_count,
        column_count=df.width,
        columns=df.columns,
    )

    return StreamingResponse(
        _stream(df, file_info, target_column, problem_type, pre_sampled),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
