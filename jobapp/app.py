import os
import asyncio
import json
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

from db import init_db, save_session, load_all_sessions, load_session, delete_session
from document_processor import extract_text_from_pdf, extract_text_from_docx
from embeddings import get_embedding, get_embeddings
from utils import rank_resumes
from summarizer import generate_summary

init_db()

app = FastAPI(title="JobMatcher")
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory job registry (single-worker only — fine for demo/HF Spaces)
_jobs: dict[str, asyncio.Queue] = {}

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


# ── Pipeline ───────────────────────────────────────────────────────────────

async def run_pipeline(
    job_id: str,
    job_desc: str,
    resume_texts: list[str],
    filenames: list[str],
    session_name: str,
    top_k: int,
):
    q = _jobs[job_id]

    async def emit(event_type: str, **data):
        await q.put({"type": event_type, **data})

    loop = asyncio.get_event_loop()

    try:
        # Step 1 — filter
        await emit("step", step="extract", message="Validating and filtering resumes…", progress=10)
        valid = [
            (t, n) for t, n in zip(resume_texts, filenames)
            if len(t.strip()) >= 100
            and "No text found" not in t
            and not t.startswith("Error")
        ]
        if not valid:
            await emit("error", message="No readable text found in the uploaded files.")
            return

        texts, names = zip(*valid)
        texts, names = list(texts), list(names)
        await emit("step", step="extract", message=f"{len(texts)} resume(s) extracted successfully.", progress=25, done=True)

        # Step 2 — embeddings
        await emit("step", step="embed", message="Generating 384-dim semantic embeddings…", progress=30)
        job_emb = await loop.run_in_executor(None, get_embedding, job_desc.strip())
        resumes_emb = await loop.run_in_executor(None, get_embeddings, texts)
        await emit("step", step="embed", message="Embeddings generated.", progress=50, done=True)

        # Step 3 — ranking
        await emit("step", step="rank", message="Ranking candidates by cosine similarity…", progress=55)
        top_candidates = rank_resumes(job_emb, resumes_emb, texts, min(top_k, len(texts)))
        await emit("step", step="rank", message=f"Top {len(top_candidates)} candidates ranked.", progress=65, done=True)

        # Step 4 — summaries
        await emit("step", step="summarize", message="Generating AI summaries…", progress=70)
        results = []
        for i, candidate in enumerate(top_candidates):
            orig_idx = candidate["index"]
            filename = names[orig_idx] if orig_idx < len(names) else f"Resume {orig_idx + 1}"
            clean_name = Path(filename).stem

            summary = await loop.run_in_executor(
                None, generate_summary, job_desc, candidate["resume"]
            )
            results.append({
                "filename": clean_name,
                "similarity": round(candidate["similarity"], 4),
                "summary": summary,
            })

            progress = 70 + int((i + 1) / len(top_candidates) * 25)
            await emit(
                "step",
                step="summarize",
                message=f"Summarised {i + 1}/{len(top_candidates)} candidates…",
                progress=progress,
            )

        if session_name:
            save_session(session_name, job_desc, texts, results)

        await emit("complete", results=results, progress=100)

    except Exception as e:
        await emit("error", message=str(e))
    finally:
        await asyncio.sleep(300)
        _jobs.pop(job_id, None)


# ── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/api/match")
async def start_match(
    background_tasks: BackgroundTasks,
    job_description: str = Form(...),
    session_name: str = Form(""),
    top_k: int = Form(5),
    files: list[UploadFile] = File(...),
):
    if not job_description.strip():
        raise HTTPException(400, "Job description is required.")
    if not files:
        raise HTTPException(400, "At least one resume file is required.")

    resume_texts: list[str] = []
    filenames: list[str] = []

    for f in files:
        content = await f.read()
        if len(content) > MAX_FILE_BYTES:
            raise HTTPException(400, f"{f.filename} exceeds the 10 MB limit.")

        ext = Path(f.filename or "").suffix.lower()
        if ext == ".pdf":
            text = extract_text_from_pdf(content)
        elif ext in (".docx", ".doc"):
            text = extract_text_from_docx(content)
        else:
            continue  # silently skip unsupported formats

        if text and len(text.strip()) >= 100 and not text.startswith("Error"):
            resume_texts.append(text)
            filenames.append(f.filename or f"file_{len(filenames) + 1}")

    if not resume_texts:
        raise HTTPException(422, "No readable text could be extracted from the uploaded files.")

    job_id = str(uuid4())
    _jobs[job_id] = asyncio.Queue()
    background_tasks.add_task(
        run_pipeline, job_id, job_description, resume_texts, filenames, session_name, top_k
    )
    return {"job_id": job_id}


@app.get("/api/stream/{job_id}")
async def stream_progress(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(404, "Job not found.")

    async def generator():
        q = _jobs[job_id]
        while True:
            try:
                event = await asyncio.wait_for(q.get(), timeout=60.0)
                yield f"data: {json.dumps(event)}\n\n"
                if event["type"] in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                yield 'data: {"type":"ping"}\n\n'

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/sessions")
async def get_sessions():
    return {"sessions": load_all_sessions()}


@app.get("/api/sessions/{session_name}")
async def get_session(session_name: str):
    data = load_session(session_name)
    if not data:
        raise HTTPException(404, f"Session '{session_name}' not found.")
    return data


@app.delete("/api/sessions/{session_name}")
async def remove_session(session_name: str):
    delete_session(session_name)
    return {"message": f"Session '{session_name}' deleted."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=True)
