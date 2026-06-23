from app.db import crud
from app.services import llm_service, rag_service

# Broad queries that pull the most relevant chunks for each task
_SUMMARY_QUERY = "main topics key concepts overview introduction"
_QUIZ_QUERY = "key facts definitions important concepts principles"
_FLASHCARD_QUERY = "definitions terms key concepts vocabulary"


def generate_summary(document_id: str, user_id: str) -> dict:
    context = rag_service.build_context(_SUMMARY_QUERY, document_id, top_k=8)
    if not context:
        raise ValueError("No content found for this document.")

    system = (
        "You are an expert academic tutor. Summarize study material clearly and concisely. "
        "Always respond with valid JSON."
    )
    user = (
        f"Based on the following content from a study document, provide:\n"
        f"1. A comprehensive summary (3-5 paragraphs)\n"
        f"2. A list of 5-8 key points\n\n"
        f"CONTENT:\n{context}\n\n"
        f'Return JSON: {{"summary": "...", "key_points": ["...", "..."]}}'
    )

    result = llm_service.chat_json(system, user)

    session = crud.create_study_session(user_id, document_id, "summary")
    crud.complete_study_session(session["id"])

    return {
        "session_id": session["id"],
        "summary": result["summary"],
        "key_points": result.get("key_points", []),
    }


def stream_summary(document_id: str, user_id: str):
    """
    Generator that streams the summary text token by token as SSE events.
    Yields: start event → token events → done event (with key_points).
    """
    context = rag_service.build_context(_SUMMARY_QUERY, document_id, top_k=8)
    if not context:
        raise ValueError("No content found for this document.")

    system = (
        "You are an expert academic tutor. Summarize study material clearly and concisely. "
        "Write 3-5 paragraphs covering the main topics and key concepts."
    )
    user = f"Summarize the following study document content:\n\n{context}"

    session = crud.create_study_session(user_id, document_id, "summary")
    yield {"type": "start", "session_id": session["id"]}

    full_text = []
    for token in llm_service.chat_stream(system, user):
        full_text.append(token)
        yield {"type": "token", "content": token}

    # Generate key_points from the collected summary
    kp_system = "You are an academic tutor. Always respond with valid JSON."
    kp_user = (
        f"Extract 5-8 key points from this summary:\n\n{''.join(full_text)}\n\n"
        f'Return JSON: {{"key_points": ["...", "..."]}}'
    )
    kp_result = llm_service.chat_json(kp_system, kp_user)

    crud.complete_study_session(session["id"])
    yield {"type": "done", "key_points": kp_result.get("key_points", [])}


def generate_quiz(
    document_id: str,
    user_id: str,
    difficulty: str = "medium",
    num_questions: int = 5,
) -> dict:
    context = rag_service.build_context(_QUIZ_QUERY, document_id, top_k=6)
    if not context:
        raise ValueError("No content found for this document.")

    system = (
        "You are an expert exam question writer. Create challenging but fair multiple "
        "choice questions based strictly on the provided content. "
        "Always respond with valid JSON."
    )
    user = (
        f"Based on the following content, generate {num_questions} multiple choice "
        f"questions at {difficulty} difficulty.\n\n"
        f"CONTENT:\n{context}\n\n"
        f"Return JSON:\n"
        f'{{"questions": [{{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], '
        f'"correct_answer": "A", "explanation": "..."}}]}}'
    )

    result = llm_service.chat_json(system, user)
    questions = result.get("questions", [])

    session = crud.create_study_session(user_id, document_id, "quiz")
    crud.store_quiz_results(session["id"], questions)
    crud.complete_study_session(session["id"])

    return {
        "session_id": session["id"],
        "questions": questions,
    }


def generate_flashcards(
    document_id: str,
    user_id: str,
    num_cards: int = 10,
) -> dict:
    context = rag_service.build_context(_FLASHCARD_QUERY, document_id, top_k=6)
    if not context:
        raise ValueError("No content found for this document.")

    system = (
        "You are an expert educator creating study flashcards. "
        "Always respond with valid JSON."
    )
    user = (
        f"Based on the following content, generate {num_cards} flashcards "
        f"covering key terms, concepts, and facts.\n\n"
        f"CONTENT:\n{context}\n\n"
        f'Return JSON: {{"flashcards": [{{"front": "...", "back": "..."}}]}}'
    )

    result = llm_service.chat_json(system, user)
    flashcards = result.get("flashcards", [])

    session = crud.create_study_session(user_id, document_id, "flashcard")
    crud.complete_study_session(session["id"])

    return {
        "session_id": session["id"],
        "flashcards": flashcards,
    }
