from typing import List, Optional

from app.db.supabase_client import get_supabase


# ── Users ─────────────────────────────────────────────────────

def upsert_user(google_id: str, email: str, name: str, avatar_url: str) -> dict:
    """
    Insert on first login, update name/avatar on subsequent logins.
    Uses Supabase upsert with google_id as the conflict key.
    """
    result = (
        get_supabase()
        .table("users")
        .upsert(
            {
                "google_id": google_id,
                "email": email,
                "name": name,
                "avatar_url": avatar_url,
            },
            on_conflict="google_id",
        )
        .execute()
    )
    return result.data[0]


def get_user(user_id: str) -> Optional[dict]:
    result = (
        get_supabase()
        .table("users")
        .select("*")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    return result.data


# ── Documents ─────────────────────────────────────────────────

def create_document(
    user_id: str,
    filename: str,
    file_type: str,
    storage_path: str,
) -> dict:
    result = (
        get_supabase()
        .table("documents")
        .insert({
            "user_id": user_id,
            "filename": filename,
            "file_type": file_type,
            "storage_path": storage_path,
            "status": "processing",
        })
        .execute()
    )
    return result.data[0]


def get_document(document_id: str) -> Optional[dict]:
    result = (
        get_supabase()
        .table("documents")
        .select("*")
        .eq("id", document_id)
        .maybe_single()
        .execute()
    )
    return result.data


def update_document_status(
    document_id: str,
    status: str,
    raw_text: Optional[str] = None,
) -> None:
    payload: dict = {"status": status}
    if raw_text is not None:
        payload["raw_text"] = raw_text
    (
        get_supabase()
        .table("documents")
        .update(payload)
        .eq("id", document_id)
        .execute()
    )


# ── Document chunks (pgvector) ────────────────────────────────

def store_chunks(
    document_id: str,
    chunks: List[str],
    embeddings: List[List[float]],
) -> None:
    rows = [
        {
            "document_id": document_id,
            "chunk_index": i,
            "content": chunk,
            "embedding": embedding,
        }
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]
    get_supabase().table("document_chunks").insert(rows).execute()


def search_chunks(
    document_id: str,
    query_embedding: List[float],
    top_k: int = 5,
) -> List[dict]:
    """Call the match_chunks Postgres function (pgvector cosine similarity)."""
    result = get_supabase().rpc(
        "match_chunks",
        {
            "query_embedding": query_embedding,
            "match_document_id": document_id,
            "match_count": top_k,
        },
    ).execute()
    return result.data


# ── Study sessions ────────────────────────────────────────────

def create_study_session(user_id: str, document_id: str, session_type: str) -> dict:
    result = (
        get_supabase()
        .table("study_sessions")
        .insert({
            "user_id": user_id,
            "document_id": document_id,
            "session_type": session_type,
        })
        .execute()
    )
    return result.data[0]


def complete_study_session(session_id: str) -> None:
    from datetime import datetime, timezone
    (
        get_supabase()
        .table("study_sessions")
        .update({"completed_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", session_id)
        .execute()
    )


def store_quiz_results(session_id: str, questions: list) -> None:
    rows = [
        {
            "session_id": session_id,
            "question": q["question"],
            "options": q["options"],
            "correct_answer": q["correct_answer"],
            "explanation": q.get("explanation", ""),
        }
        for q in questions
    ]
    get_supabase().table("quiz_results").insert(rows).execute()


# ── Interview sessions ────────────────────────────────────────

def create_interview_session(user_id: str, document_id: str) -> dict:
    result = (
        get_supabase()
        .table("interview_sessions")
        .insert({"user_id": user_id, "document_id": document_id})
        .execute()
    )
    return result.data[0]


def store_interview_question(session_id: str, question: str, scenario: str) -> dict:
    result = (
        get_supabase()
        .table("interview_results")
        .insert({
            "session_id": session_id,
            "question": question,
            "scenario": scenario,
        })
        .execute()
    )
    return result.data[0]


def get_interview_question(question_id: str) -> Optional[dict]:
    result = (
        get_supabase()
        .table("interview_results")
        .select("*")
        .eq("id", question_id)
        .maybe_single()
        .execute()
    )
    return result.data


def update_interview_result(
    question_id: str,
    user_answer: str,
    score: int,
    strengths: list,
    weaknesses: list,
    feedback: str,
) -> None:
    (
        get_supabase()
        .table("interview_results")
        .update({
            "user_answer": user_answer,
            "score": score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "feedback": feedback,
        })
        .eq("id", question_id)
        .execute()
    )


# ── Session retrieval ─────────────────────────────────────────

def get_user_study_sessions(user_id: str) -> list:
    result = (
        get_supabase()
        .table("study_sessions")
        .select("id, session_type, document_id, created_at, completed_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def get_user_interview_sessions(user_id: str) -> list:
    result = (
        get_supabase()
        .table("interview_sessions")
        .select("id, document_id, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def get_study_session(session_id: str) -> Optional[dict]:
    result = (
        get_supabase()
        .table("study_sessions")
        .select("*")
        .eq("id", session_id)
        .maybe_single()
        .execute()
    )
    return result.data


def get_quiz_results(session_id: str) -> list:
    result = (
        get_supabase()
        .table("quiz_results")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )
    return result.data


def get_interview_session(session_id: str) -> Optional[dict]:
    result = (
        get_supabase()
        .table("interview_sessions")
        .select("*")
        .eq("id", session_id)
        .maybe_single()
        .execute()
    )
    return result.data


def get_interview_results(session_id: str) -> list:
    result = (
        get_supabase()
        .table("interview_results")
        .select("id, question, scenario, user_answer, score, strengths, weaknesses, feedback")
        .eq("session_id", session_id)
        .execute()
    )
    return result.data


def get_user_documents(user_id: str) -> list:
    result = (
        get_supabase()
        .table("documents")
        .select("id, filename, file_type, status, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data
