import numpy as np

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    Cosine similarity = (A · B) / (||A|| * ||B||)

    Args:
        vec1 (np.ndarray): First vector
        vec2 (np.ndarray): Second vector

    Returns:
        float: Similarity score between -1 and 1
    """
    dot_product = np.dot(vec1, vec2)               # Numerator: dot product of vec1 and vec2
    norm_vec1 = np.linalg.norm(vec1)                # Denominator part 1: magnitude of vec1
    norm_vec2 = np.linalg.norm(vec2)                # Denominator part 2: magnitude of vec2

    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0  # Avoid division by zero

    similarity = dot_product / (norm_vec1 * norm_vec2)
    return similarity

def rank_resumes(job_embedding: np.ndarray, resume_embeddings: list[np.ndarray], resumes: list[str], top_k: int = 5):
    """
    Rank resumes by similarity to the job description embedding.

    Args:
        job_embedding (np.ndarray): Embedding of the job description
        resume_embeddings (list[np.ndarray]): List of embeddings for each resume
        resumes (list[str]): List of resume texts corresponding to embeddings
        top_k (int): Number of top candidates to return

    Returns:
        list of dicts: Each dict contains:
            - 'resume': resume text
            - 'similarity': similarity score
            - 'index': original index in the resumes list
    """
    scores = []
    for idx, emb in enumerate(resume_embeddings):
        score = cosine_similarity(job_embedding, emb)
        scores.append((idx, score))

    # Sort by similarity score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    # Select top K results
    top_results = []
    for idx, score in scores[:top_k]:
        top_results.append({
            'resume': resumes[idx],
            'similarity': float(score),  # Convert numpy float to Python float
            'index': idx
        })

    return top_results
