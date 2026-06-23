from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 300,  # words per chunk
    overlap: int = 50,      # words of overlap between consecutive chunks
) -> List[str]:
    """
    Split text into overlapping word-based chunks.

    Word-based (not character-based) so chunks never cut a word in half,
    keeping embeddings semantically cleaner.

    chunk_size=300 words ≈ 400 tokens — well within text-embedding-3-small's
    8191-token limit, with room for longer words and punctuation.
    """
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        if end >= len(words):
            break

        # Advance by (chunk_size - overlap) so the next chunk re-uses the
        # last `overlap` words of the current chunk — preserving context
        # across chunk boundaries.
        start += chunk_size - overlap

    return chunks
