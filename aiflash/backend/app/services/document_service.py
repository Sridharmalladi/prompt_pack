import logging
import os
import time

logger = logging.getLogger(__name__)

from fastapi import BackgroundTasks, UploadFile

from app.db import crud
from app.db.supabase_client import get_supabase
from app.services import embedding_service
from app.utils.file_parser import parse_file
from app.utils.text_cleaner import clean_text

_EXT_MAP = {".pdf": "pdf", ".docx": "docx", ".txt": "txt"}
_CT_MAP = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}


def _resolve_file_type(filename: str, content_type: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in _EXT_MAP:
        return _EXT_MAP[ext]
    if content_type in _CT_MAP:
        return _CT_MAP[content_type]
    raise ValueError("Unsupported file type. Allowed: PDF, DOCX, TXT")


async def upload_document(
    file: UploadFile,
    user_id: str,
    background_tasks: BackgroundTasks,
) -> dict:
    filename = file.filename or "untitled"
    content_type = file.content_type or "application/octet-stream"
    file_type = _resolve_file_type(filename, content_type)

    file_bytes = await file.read()

    # Unique storage path — prevents name collisions across users/uploads
    timestamp = int(time.time())
    storage_path = f"{user_id}/{timestamp}_{filename}"

    get_supabase().storage.from_("documents").upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": content_type},
    )

    doc = crud.create_document(
        user_id=user_id,
        filename=filename,
        file_type=file_type,
        storage_path=storage_path,
    )

    # Non-blocking — returns 202 immediately; status polled via GET /status
    background_tasks.add_task(process_document, doc["id"], file_bytes, file_type)

    return doc


def process_document(document_id: str, file_bytes: bytes, file_type: str) -> None:
    """
    Background task: parse → clean → store raw text.
    Chunking + embedding are wired in here during Step 5 (embedding_service).
    """
    try:
        raw_text = parse_file(file_bytes, file_type)
        cleaned_text = clean_text(raw_text)
        # Chunk → embed → store in pgvector (Step 5)
        embedding_service.embed_and_store(document_id, cleaned_text)
        crud.update_document_status(document_id, "ready", raw_text=cleaned_text)
    except Exception as exc:
        logger.exception("Document processing failed for %s: %s", document_id, exc)
        crud.update_document_status(document_id, "failed")
