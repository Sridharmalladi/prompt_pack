from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text: str) -> np.ndarray:
    """Return a 384-dimensional embedding for a single text."""
    return model.encode(text)


def get_embeddings(texts: list[str]) -> np.ndarray:
    """Return a (N, 384) array of embeddings for a list of texts."""
    return model.encode(texts)
