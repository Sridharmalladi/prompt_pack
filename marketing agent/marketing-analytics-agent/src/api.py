"""
REST API — wraps the agent with session management so clients can have multi-turn
conversations over HTTP.

Run:  uvicorn src.api:app --reload

Endpoints
---------
POST   /ask              Ask a question. Pass session_id to continue an existing
                         conversation; omit it to start a new one.
DELETE /session/{id}     Clear the conversation history for a session.
GET    /health           Liveness check — returns active session count.
"""

import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agent import Agent

app = FastAPI(title="Marketing Analytics Agent", version="0.1.0")

# One Agent instance per session so follow-up questions carry full conversation history.
# This is in-memory and single-process — swap for Redis to scale or survive restarts.
_sessions: dict[str, Agent] = {}


class AskRequest(BaseModel):
    question: str
    session_id: str | None = None  # omit to start a new session
    verbose: bool = False


class AskResponse(BaseModel):
    answer: str
    session_id: str  # echoed back so the client can continue the conversation


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "active_sessions": len(_sessions)}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    sid = req.session_id or str(uuid.uuid4())
    if sid not in _sessions:
        try:
            _sessions[sid] = Agent()
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))
    answer = _sessions[sid].ask(req.question, verbose=req.verbose)
    return AskResponse(answer=answer, session_id=sid)


@app.delete("/session/{session_id}")
def clear_session(session_id: str) -> dict:
    _sessions.pop(session_id, None)
    return {"cleared": session_id}
