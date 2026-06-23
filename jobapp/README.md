---
title: JobMatcher
emoji: 🎯
colorFrom: purple
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# JobMatcher — RAG-Powered Resume Screening

**JobMatcher** is a Retrieval-Augmented Generation (RAG) pipeline for recruiting. Drop in a job description and a stack of resumes — the system extracts text, builds semantic embeddings, ranks candidates by cosine similarity, then uses an LLM to write a concise fit-or-no-fit summary for each top candidate. Every step streams live to an animated glassmorphism dashboard.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![RAG](https://img.shields.io/badge/Architecture-RAG-blueviolet)
![sentence-transformers](https://img.shields.io/badge/embeddings-all--MiniLM--L6--v2-orange)
![Docker](https://img.shields.io/badge/Deploy-HuggingFace_Spaces-yellow)

---

## What is RAG and how does JobMatcher use it?

Retrieval-Augmented Generation is a technique that grounds LLM outputs in a specific knowledge base instead of relying on the model's training data alone. Here, the "knowledge base" is the set of uploaded resumes, and the "retrieval" step is cosine similarity over dense embeddings.

The pipeline has four stages:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. EXTRACT   Text is pulled from every PDF and DOCX resume using       │
│               PyPDF2 and python-docx. Files with fewer than 100 chars   │
│               of readable text are filtered out before processing.      │
│                                                                         │
│  2. EMBED     Each resume and the job description are converted into    │
│               384-dimensional dense vectors by sentence-transformers    │
│               (all-MiniLM-L6-v2). This runs entirely locally — no API  │
│               call, no cost, no data leaves your machine.               │
│                                                                         │
│  3. RANK      Cosine similarity between the job-description vector and  │
│               each resume vector produces a score from 0 → 1. The top  │
│               K candidates are selected for the next stage.             │
│                                                                         │
│  4. SUMMARIZE An LLM receives the job description and each top-K resume │
│               inside XML delimiters and writes a 3-sentence fit         │
│               assessment. System prompt blocks prompt injection from     │
│               malicious resume content.                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

Every stage is streamed to the frontend via **Server-Sent Events (SSE)** so you see live progress rather than waiting on a spinner.

---

## Tech stack

| Layer | Technology | Notes |
|---|---|---|
| Backend | FastAPI + Uvicorn | Async, SSE streaming |
| Text extraction | PyPDF2, python-docx | Handles PDF and DOCX |
| Embeddings | `sentence-transformers` `all-MiniLM-L6-v2` | 384-dim, fully local, zero API cost |
| AI summaries | LLM via API | Fit assessment for each top-K candidate |
| Session storage | SQLite | Named sessions persist results across page reloads |
| Frontend | Vanilla HTML/CSS/JS | Animated glassmorphism UI, no build step |
| Deployment | Docker on Hugging Face Spaces | Port 7860, single-command rebuild via git push |

---

## Project structure

```
jobapp/
├── app.py                 # FastAPI routes + SSE pipeline orchestration
├── summarizer.py          # LLM summary integration
├── embeddings.py          # sentence-transformers model wrapper
├── document_processor.py  # PDF and DOCX text extraction
├── utils.py               # Cosine similarity ranking
├── db.py                  # SQLite session persistence
├── init_db.py             # DB bootstrap script
├── static/
│   └── index.html         # Animated glassmorphism UI (single file)
├── Dockerfile             # HF Spaces Docker build
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Running locally

```bash
git clone https://github.com/<your-username>/jobapp.git
cd jobapp

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your LLM API key

uvicorn app:app --reload --port 7860
# Open http://localhost:7860
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | API key for LLM-powered summaries |

The embedding step runs entirely locally — no additional API key or network access needed for ranking.

---

## Deploying to Hugging Face Spaces

The repo is configured as a Docker Space (`sdk: docker`, `app_port: 7860`). A `git push` is all that's needed to trigger a rebuild:

```bash
git remote add space https://huggingface.co/spaces/<username>/<space-name>
git push space main
```

Set `ANTHROPIC_API_KEY` under **Settings → Variables and secrets** in the Space dashboard.

---

## Security

- Resumes and job descriptions are passed to the LLM inside `<job_desc>` and `<resume>` XML delimiters with an explicit system prompt telling the model to ignore any embedded instructions — mitigating prompt injection via document content.
- File size is capped at 10 MB per upload.
- Only `.pdf` and `.docx` extensions are accepted; all other formats are silently skipped.
- API keys are never logged or returned to the frontend.
