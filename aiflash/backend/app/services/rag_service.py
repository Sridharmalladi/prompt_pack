from typing import List

from app.services import embedding_service

# Maximum characters of context to pass to GPT — keeps prompts within token limits
_MAX_CONTEXT_CHARS = 6000


def retrieve_chunks(query: str, document_id: str, top_k: int = 5) -> List[dict]:
    """
    Embed the query and return the top-k most similar chunks from pgvector.
    Each chunk dict has: id, document_id, chunk_index, content, similarity.
    """
    return embedding_service.similarity_search(query, document_id, top_k)


def build_context(query: str, document_id: str, top_k: int = 5) -> str:
    """
    Retrieve the most relevant chunks for a query and format them as a
    numbered context block ready to be injected into a GPT prompt.

    Returns an empty string if no chunks are found.
    """
    chunks = retrieve_chunks(query, document_id, top_k)
    if not chunks:
        return ""

    parts: List[str] = []
    total_chars = 0

    for i, chunk in enumerate(chunks, start=1):
        content = chunk["content"].strip()
        entry = f"[{i}] {content}"

        if total_chars + len(entry) > _MAX_CONTEXT_CHARS:
            break

        parts.append(entry)
        total_chars += len(entry)

    return "\n\n".join(parts)
