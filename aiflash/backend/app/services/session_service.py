from app.db import crud


def get_user_sessions(user_id: str) -> list:
    """
    Return all study and interview sessions for the user,
    merged and sorted newest-first.
    """
    study = crud.get_user_study_sessions(user_id)
    interview = crud.get_user_interview_sessions(user_id)

    sessions = []

    for s in study:
        sessions.append({
            "id": s["id"],
            "type": "study",
            "session_type": s["session_type"],
            "document_id": s["document_id"],
            "created_at": s["created_at"],
            "completed_at": s.get("completed_at"),
        })

    for s in interview:
        sessions.append({
            "id": s["id"],
            "type": "interview",
            "session_type": "interview",
            "document_id": s["document_id"],
            "created_at": s["created_at"],
            "completed_at": None,
        })

    sessions.sort(key=lambda x: x["created_at"], reverse=True)
    return sessions


def get_session_detail(session_id: str) -> dict:
    """
    Return full session detail including results.
    Checks study_sessions first, then interview_sessions.
    Raises ValueError if not found.
    """
    session = crud.get_study_session(session_id)
    if session:
        detail = {**session, "type": "study", "results": []}
        if session["session_type"] == "quiz":
            detail["results"] = crud.get_quiz_results(session_id)
        return detail

    session = crud.get_interview_session(session_id)
    if session:
        return {
            **session,
            "type": "interview",
            "session_type": "interview",
            "results": crud.get_interview_results(session_id),
        }

    raise ValueError("Session not found.")
