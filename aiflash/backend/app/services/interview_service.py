from app.db import crud
from app.services import llm_service, rag_service

_QUESTION_QUERY = "key concepts technical details processes important topics"


def generate_question(
    document_id: str,
    user_id: str,
    difficulty: str = "medium",
) -> dict:
    """
    Retrieve relevant chunks, generate one interview-style question + scenario.
    Creates an interview_session and stores the question in interview_results.
    """
    context = rag_service.build_context(_QUESTION_QUERY, document_id, top_k=5)
    if not context:
        raise ValueError("No content found for this document.")

    system = (
        "You are an expert technical interviewer. Generate realistic, thought-provoking "
        "interview questions based strictly on the provided content. "
        "Always respond with valid JSON."
    )
    user = (
        f"Based on the following content, generate one {difficulty}-difficulty "
        f"interview question.\n\n"
        f"CONTENT:\n{context}\n\n"
        f"Return JSON:\n"
        f'{{"question": "...", "scenario": "A short 1-2 sentence context that frames the question"}}'
    )

    result = llm_service.chat_json(system, user)

    session = crud.create_interview_session(user_id, document_id)
    question_row = crud.store_interview_question(
        session_id=session["id"],
        question=result["question"],
        scenario=result.get("scenario", ""),
    )

    return {
        "session_id": session["id"],
        "question_id": question_row["id"],
        "question": result["question"],
        "scenario": result.get("scenario", ""),
    }


def stream_evaluate(
    question_id: str,
    session_id: str,
    user_answer: str,
):
    """
    Generator that streams the interview feedback token by token as SSE events.
    Yields: start event → token events → done event (with score/strengths/weaknesses).
    """
    question_row = crud.get_interview_question(question_id)
    if not question_row:
        raise ValueError("Question not found.")

    yield {"type": "start"}

    system = (
        "You are a strict but fair technical interviewer. "
        "Write a detailed paragraph of actionable feedback evaluating the candidate's answer."
    )
    user = (
        f"QUESTION: {question_row['question']}\n\n"
        f"CANDIDATE'S ANSWER: {user_answer}\n\n"
        f"Write your feedback:"
    )

    full_text = []
    for token in llm_service.chat_stream(system, user):
        full_text.append(token)
        yield {"type": "token", "content": token}

    # Extract structured score/strengths/weaknesses from the collected feedback
    eval_system = "You are a technical interviewer. Always respond with valid JSON."
    eval_user = (
        f"QUESTION: {question_row['question']}\n\n"
        f"CANDIDATE'S ANSWER: {user_answer}\n\n"
        f"FEEDBACK: {''.join(full_text)}\n\n"
        f"Based on the above, return JSON:\n"
        f'{{"score": 7, "strengths": ["...", "..."], "weaknesses": ["...", "..."]}}'
    )
    eval_result = llm_service.chat_json(eval_system, eval_user)

    crud.update_interview_result(
        question_id=question_id,
        user_answer=user_answer,
        score=eval_result["score"],
        strengths=eval_result.get("strengths", []),
        weaknesses=eval_result.get("weaknesses", []),
        feedback="".join(full_text),
    )

    yield {
        "type": "done",
        "score": eval_result["score"],
        "strengths": eval_result.get("strengths", []),
        "weaknesses": eval_result.get("weaknesses", []),
    }


def evaluate_answer(
    question_id: str,
    session_id: str,
    user_answer: str,
) -> dict:
    """
    Score the user's answer (0–10) with strengths, weaknesses, and actionable feedback.
    Retrieves the original question from DB, passes both to GPT for evaluation.
    """
    question_row = crud.get_interview_question(question_id)
    if not question_row:
        raise ValueError("Question not found.")

    system = (
        "You are a strict but fair technical interviewer evaluating a candidate's answer. "
        "Score objectively and give actionable feedback. "
        "Always respond with valid JSON."
    )
    user = (
        f"QUESTION: {question_row['question']}\n\n"
        f"CANDIDATE'S ANSWER: {user_answer}\n\n"
        f"Evaluate this answer and return JSON:\n"
        f'{{"score": 7, "strengths": ["...", "..."], "weaknesses": ["...", "..."], '
        f'"feedback": "A concise paragraph of actionable feedback"}}'
    )

    result = llm_service.chat_json(system, user)

    crud.update_interview_result(
        question_id=question_id,
        user_answer=user_answer,
        score=result["score"],
        strengths=result.get("strengths", []),
        weaknesses=result.get("weaknesses", []),
        feedback=result.get("feedback", ""),
    )

    return {
        "score": result["score"],
        "strengths": result.get("strengths", []),
        "weaknesses": result.get("weaknesses", []),
        "feedback": result.get("feedback", ""),
        "transcription": None,  # populated by whisper_service in Step 10
    }
