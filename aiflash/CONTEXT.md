# 🧠 AI Study Assistant — Master Project Context

> This file is the single source of truth for the entire project.
> At the start of every Claude Code session, say:
> **"Read CONTEXT.md and let's continue building"**

---

## 🎯 Project Goal

Build a full-stack AI Study Assistant that is:
- Interview-ready as a portfolio project
- Real-world AI Engineering depth (not a GPT wrapper)
- Clean, layered, maintainable architecture
- Deployable and demonstrable

---

## 🧩 What The App Does

1. User signs in with Google
2. User uploads a PDF, DOCX, or plain text document
3. Backend processes it asynchronously:
   - Extracts and cleans text
   - Chunks it into overlapping segments
   - Generates embeddings for each chunk (OpenAI)
   - Stores vectors in Supabase via pgvector
4. User picks a mode:

**Study Mode**
- Generate a summary + key points
- Generate MCQ quizzes (with options, correct answer, explanation)
- Generate flashcards

**Interview Mode**
- Generate interview-style questions from the document
- Single answer interface — user types OR clicks a mic button to record voice (no mode selection)
- Voice recording → Whisper transcribes → same evaluation pipeline as typed text
- Backend receives either text or audio file, handles both transparently
- Evaluate the answer and return score + strengths + weaknesses + feedback

5. All sessions, scores, and progress are stored and trackable

---

## 🔥 Tech Stack (Finalized)

| Layer | Tool | Why |
|---|---|---|
| Backend Framework | FastAPI (Python) | Async, production-ready, clean |
| Database | Supabase (PostgreSQL) | Free tier, managed, production-grade |
| Vector Storage | Supabase pgvector | Same DB, no separate vector store needed |
| File Storage | Supabase Storage | PDF/DOCX uploads stored here |
| Auth | Google OAuth + JWT | Google token verified by backend, own JWT issued |
| LLM | OpenAI GPT-4o-mini | Cost efficient, high quality |
| Embeddings | OpenAI text-embedding-3-small | Fast, cheap, accurate |
| Speech-to-Text | OpenAI Whisper API | Voice answer transcription |
| PDF Parsing | pdfplumber | Clean text extraction |
| DOCX Parsing | docx2txt | Simple DOCX extraction |
| Async Processing | FastAPI BackgroundTasks | Non-blocking document processing |
| Testing | pytest + httpx | Unit + integration + API tests |
| CI/CD | GitHub Actions | Run tests on every push |
| Deployment | Railway or Render (backend) | Simple, cheap, no DevOps |
| Frontend (later) | Next.js + TypeScript + Tailwind | Built separately after backend complete |

---

## 🏗️ Architecture

```
User Request
     ↓
FastAPI (routes.py)
     ↓
Services Layer (business logic)
     ↓
DB Layer (Supabase client + crud.py)
     ↓
Supabase (PostgreSQL + pgvector + Storage)

AI Calls (all go through llm_service.py)
     ↓
OpenAI API (GPT + Embeddings + Whisper)
```

**RAG Pipeline (on upload — async):**
```
File Upload → Extract Text → Clean Text → Chunk Text
     → Embed Each Chunk (OpenAI) → Store in pgvector (Supabase)
```

**RAG Pipeline (on query):**
```
User Query → Embed Query → Retrieve Top-K Chunks from pgvector
     → Inject Chunks as Context into GPT Prompt → Return Response
```

**Key Rules:**
- Routes ONLY handle HTTP (no business logic)
- Services contain ALL business logic
- DB layer handles ALL database operations
- LLM service is the ONLY place OpenAI is called directly
- No cross-layer mixing
- Every layer independently testable

---

## 📁 Complete File Structure

```
backend/
│
├── app/
│   ├── main.py                        # FastAPI app init, router registration, CORS config
│   ├── config.py                      # All env vars loaded via pydantic BaseSettings
│   │
│   ├── api/
│   │   └── routes.py                  # All API endpoints (single file for now)
│   │
│   ├── services/
│   │   ├── auth_service.py            # Google token verify, JWT issue + validate
│   │   ├── document_service.py        # Upload handling, extraction, chunking orchestration
│   │   ├── embedding_service.py       # Generate embeddings, store in pgvector, similarity search
│   │   ├── rag_service.py             # Full RAG pipeline: retrieve chunks → build context prompt
│   │   ├── llm_service.py             # ALL OpenAI GPT calls (single point of entry)
│   │   ├── study_service.py           # Summary, quiz, flashcard generation (uses rag_service)
│   │   ├── interview_service.py       # Question gen, answer eval, feedback (uses rag_service)
│   │   ├── whisper_service.py         # Audio file → transcribed text via Whisper API
│   │   └── session_service.py         # Create/read sessions, store scores, track progress
│   │
│   ├── db/
│   │   ├── supabase_client.py         # Supabase client singleton (used across all DB ops)
│   │   ├── models.py                  # Table definitions / SQLAlchemy models
│   │   └── crud.py                    # All DB read/write operations (no business logic here)
│   │
│   ├── schemas/
│   │   └── schemas.py                 # All Pydantic request + response models
│   │
│   ├── utils/
│   │   ├── text_cleaner.py            # Remove noise, normalize whitespace, fix OCR errors
│   │   ├── chunker.py                 # Split text into overlapping chunks (custom implementation)
│   │   └── file_parser.py             # PDF → text (pdfplumber), DOCX → text (docx2txt), TXT → text
│   │
│   └── middleware/
│       └── auth_middleware.py         # JWT verification dependency for protected routes
│
├── tests/
│   ├── conftest.py                    # Shared setup: test DB, mock OpenAI, mock Supabase client
│   ├── test_auth.py                   # Google token validation, JWT issue + verify
│   ├── test_document.py               # File upload, text extraction, chunking logic
│   ├── test_rag.py                    # Retrieval accuracy, chunk injection into prompts
│   ├── test_study.py                  # Quiz generation, summary generation
│   ├── test_interview.py              # Question generation, answer evaluation
│   └── test_session.py               # Session creation, score storage, progress retrieval
│
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions: run pytest on every push to main
│
├── requirements.txt
├── .env                               # Never commit this
├── .env.example                       # Safe to commit — shows required variable names
└── README.md
```

---

## 🗄️ Supabase Database Schema

### `users`
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  google_id TEXT UNIQUE NOT NULL,
  name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `documents`
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  file_type TEXT NOT NULL,  -- 'pdf', 'docx', 'txt'
  raw_text TEXT,
  status TEXT DEFAULT 'processing',  -- 'processing', 'ready', 'failed'
  storage_path TEXT,  -- Supabase Storage path
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `document_chunks`
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1536),  -- OpenAI text-embedding-3-small dimension
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast similarity search
CREATE INDEX ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### `study_sessions`
```sql
CREATE TABLE study_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  session_type TEXT NOT NULL,  -- 'quiz', 'summary', 'flashcard'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);
```

### `quiz_results`
```sql
CREATE TABLE quiz_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES study_sessions(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  options JSONB NOT NULL,
  correct_answer TEXT NOT NULL,
  user_answer TEXT,
  is_correct BOOLEAN,
  explanation TEXT
);
```

### `interview_sessions`
```sql
CREATE TABLE interview_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `interview_results`
```sql
CREATE TABLE interview_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  user_answer TEXT,
  score INTEGER,  -- 0 to 10
  strengths JSONB,
  weaknesses JSONB,
  feedback TEXT
);
```

---

## 🌐 API Endpoints

### Auth
```
POST   /api/auth/google              # Send Google token → get back JWT
```

### Documents
```
POST   /api/documents/upload         # Upload PDF/DOCX/TXT → async processing starts
GET    /api/documents/{id}/status    # Poll processing status (processing/ready/failed)
GET    /api/documents/               # List all documents for logged-in user
```

### Study
```
POST   /api/study/summary            # Generate summary + key points for a document
POST   /api/study/quiz               # Generate MCQ quiz (difficulty + num_questions)
POST   /api/study/flashcards         # Generate flashcards
```

### Interview
```
POST   /api/interview/generate       # Generate an interview question from document
POST   /api/interview/evaluate       # Submit answer (text or voice) → get score + feedback
```

### Sessions
```
GET    /api/sessions/                # Get all sessions for logged-in user
GET    /api/sessions/{id}            # Get full detail of one session
```

---

## 📦 Request / Response Shapes

### `POST /api/auth/google`
```json
Request:  { "token": "google_id_token_here" }
Response: { "access_token": "jwt...", "user": { "id": "...", "email": "...", "name": "..." } }
```

### `POST /api/documents/upload`
```
Request: multipart/form-data with file
Response: { "document_id": "uuid", "status": "processing" }
```

### `GET /api/documents/{id}/status`
```json
Response: { "document_id": "uuid", "status": "ready", "filename": "notes.pdf" }
```

### `POST /api/study/quiz`
```json
Request:
{
  "document_id": "uuid",
  "difficulty": "medium",
  "num_questions": 5
}

Response:
{
  "session_id": "uuid",
  "questions": [
    {
      "question": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "B",
      "explanation": "..."
    }
  ]
}
```

### `POST /api/study/summary`
```json
Request:  { "document_id": "uuid" }
Response: { "session_id": "uuid", "summary": "...", "key_points": ["...", "..."] }
```

### `POST /api/interview/generate`
```json
Request:
{
  "document_id": "uuid",
  "difficulty": "medium"
}

Response:
{
  "session_id": "uuid",
  "question_id": "uuid",
  "question": "...",
  "scenario": "..."
}
```

### `POST /api/interview/evaluate`
```
Request: multipart/form-data
  - question_id: uuid
  - session_id: uuid
  - user_answer: string (if typed)     ← one of these two, not both
  - audio_file: file (if voice recorded) ← backend detects which and handles accordingly

Response:
{
  "score": 7,
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "feedback": "...",
  "transcription": "..."   // only present if voice was used, so frontend can show what was heard
}
```

---

## 🔐 Environment Variables

### `.env` (never commit)
```
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
GOOGLE_CLIENT_ID=
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60
MODEL_NAME=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
WHISPER_ENABLED=true
```

---

## 🧪 Testing Strategy

**3 levels of tests:**

1. **Unit tests** — test a single function with no external calls
   - Example: `chunker.py` gets a long string → assert correct chunk sizes and overlap

2. **Integration tests** — test two layers working together with mocked externals
   - Example: `study_service` calls `llm_service` → mock OpenAI → assert prompt structure

3. **API tests** — spin up test FastAPI app, make real HTTP requests
   - Example: `POST /api/study/quiz` → assert 200 + correct JSON shape
   - Uses separate in-memory test database
   - OpenAI always mocked (never real API calls in tests)

**`conftest.py` sets up:**
- Test Supabase client (mocked)
- Mock OpenAI responses
- Test JWT tokens
- Fresh state before each test

**Run all tests:** `pytest` from project root

---

## 📋 Build Order (Follow This Exactly)

Build in this sequence — each step is testable before moving to the next:

```
1. Project setup (main.py, config.py, requirements.txt, .env)
2. Supabase setup (create tables in Supabase dashboard, supabase_client.py)
3. File parsing utils (file_parser.py, text_cleaner.py, chunker.py)
4. Document upload + async processing (document_service.py + routes)
5. Embedding service (embedding_service.py → pgvector store + query)
6. RAG service (rag_service.py → retrieve + build context prompt)
7. LLM service (llm_service.py → all GPT calls)
8. Study service (study_service.py → summary + quiz + flashcards)
9. Interview service (interview_service.py → generate + evaluate)
10. Whisper service (whisper_service.py → voice transcription)
11. Auth service (auth_service.py → Google OAuth + JWT)
12. Auth middleware (auth_middleware.py → protect routes)
13. Session service (session_service.py → track progress)
14. Tests (write tests for each service as you go)
15. GitHub Actions CI (ci.yml)
16. README
```

---

## 🚀 Deployment Plan

| Service | Platform | Notes |
|---|---|---|
| Backend (FastAPI) | Railway or Render | Free tier available, easy deploy from GitHub |
| Database + Storage + Auth | Supabase | Already cloud-hosted |
| Frontend (Next.js) | Vercel | Built later, free tier |

CORS must be configured in `main.py` to allow frontend domain.

---

## ⚠️ Key Decisions & Reasons

| Decision | Reason |
|---|---|
| Supabase over SQLite | PostgreSQL quality, pgvector for RAG, managed hosting, Google Auth support |
| pgvector over ChromaDB | Single database, no separate vector store, production pattern |
| FastAPI BackgroundTasks over Celery | Simpler setup, sufficient for portfolio scale |
| Single routes.py | Keeps it simple now, easy to split into routers later |
| Custom chunker over LangChain | Shows deeper understanding, better for resume |
| All OpenAI calls in llm_service.py | Single point for mocking in tests, model swapping, rate limit handling |
| Google OAuth + own JWT | Industry standard pattern, shows auth understanding |

---

## 📌 Current Status

- [x] Architecture decided
- [x] Tech stack finalized
- [x] File structure defined
- [x] Database schema designed
- [x] API endpoints specified
- [ ] Building starts now

---

*Last updated: Start of build. Update this file as decisions change.*
