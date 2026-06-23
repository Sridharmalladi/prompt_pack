from typing import List

from openai import OpenAI

from app.config import settings
from app.db import crud
from app.utils.chunker import chunk_text

_client = OpenAI(api_key=settings.openai_api_key)

# Embed up to 20 chunks per API call — reduces round-trips for large documents
_BATCH_SIZE = 20


def _batch_embed(texts: List[str]) -> List[List[float]]:
    embeddings: List[List[float]] = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        response = _client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
        )
        # response.data may not be in order — sort by index to be safe
        ordered = sorted(response.data, key=lambda x: x.index)
        embeddings.extend(item.embedding for item in ordered)
    return embeddings


def embed_text(text: str) -> List[float]:
    """Embed a single string — used for query embedding at retrieval time."""
    return _batch_embed([text])[0]


def embed_and_store(document_id: str, cleaned_text: str) -> None:
    """
    Chunk cleaned text, embed all chunks in batches, store in pgvector.
    Called from the document processing background task.
    """
    chunks = chunk_text(cleaned_text)
    if not chunks:
        return

    embeddings = _batch_embed(chunks)
    crud.store_chunks(document_id, chunks, embeddings)


def similarity_search(
    query: str,
    document_id: str,
    top_k: int = 5,
) -> List[dict]:
    """
    Embed query and retrieve the top-k most similar chunks from pgvector.
    Used by rag_service to build context for GPT prompts.
    """
    query_embedding = embed_text(query)
    return crud.search_chunks(document_id, query_embedding, top_k)
