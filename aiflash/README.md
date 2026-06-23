# AI Study Assistant — Backend

A production-quality RAG-powered study and interview preparation API built with FastAPI, Supabase, and OpenAI.

## What It Does

1. User authenticates via Google OAuth → receives a JWT
2. User uploads a PDF, DOCX, or plain text document
3. Backend asynchronously: extracts text → cleans → chunks → embeds (OpenAI) → stores in pgvector
4. User selects a mode:
   - **Study Mode** — generate summaries, MCQ quizzes, and flashcards
   - **Interview Mode** — generate interview questions, submit typed or voice answers, receive scored feedback

## Tech Stack

| Layer | Tool |
|---|---|
| Framework | FastAPI |
| Database | Supabase (PostgreSQL + pgvector) |
| File Storage | Supabase Storage |
| Auth | Google OAuth + JWT |
| LLM | OpenAI GPT-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |
| Speech-to-Text | OpenAI Whisper |
| PDF Parsing | pdfplumber |
| DOCX Parsing | docx2txt |

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, logging
│   ├── config.py               # Environment config via pydantic-settings
│   ├── api/routes.py           # All API endpoints
│   ├── services/
│   │   ├── auth_service.py     # Google OAuth + JWT
│   │   ├── document_service.py # Upload + async processing
│   │   ├── embedding_service.py# Embed + pgvector store/search
│   │   ├── rag_service.py      # Retrieve chunks + build context
│   │   ├── llm_service.py      # All OpenAI GPT calls
│   │   ├── study_service.py    # Summary, quiz, flashcards
│   │   ├── interview_service.py# Generate questions + evaluate answers
│   │   ├── whisper_service.py  # Voice transcription
│   │   └── session_service.py  # Session history + progress
│   ├── db/
│   │   ├── supabase_client.py  # Singleton Supabase client
│   │   └── crud.py             # All DB read/write operations
│   ├── schemas/schemas.py      # Pydantic request/response models
│   ├── middleware/
│   │   └── auth_middleware.py  # JWT verification dependency
│   └── utils/
│       ├── file_parser.py      # PDF/DOCX/TXT extraction
│       ├── text_cleaner.py     # Normalize and clean extracted text
│       └── chunker.py          # Overlapping word-based chunking
└── tests/                      # pytest test suite (all external calls mocked)
```

## Setup

### 1. Clone and create virtual environment

```bash
git clone <repo-url>
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

```
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
GOOGLE_CLIENT_ID=
JWT_SECRET_KEY=        # generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60
MODEL_NAME=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
WHISPER_ENABLED=true
```

### 3. Run Supabase migrations

Run `db/migrations/001_initial_schema.sql` in the Supabase SQL editor, then:

```sql
-- pgvector similarity search function
CREATE OR REPLACE FUNCTION match_chunks(
  query_embedding VECTOR(1536),
  match_document_id UUID,
  match_count INT DEFAULT 5
)
RETURNS TABLE (id UUID, document_id UUID, chunk_index INT, content TEXT, similarity FLOAT)
LANGUAGE SQL STABLE AS $$
  SELECT dc.id, dc.document_id, dc.chunk_index, dc.content,
         1 - (dc.embedding <=> query_embedding) AS similarity
  FROM document_chunks dc
  WHERE dc.document_id = match_document_id
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Add scenario column
ALTER TABLE interview_results ADD COLUMN IF NOT EXISTS scenario TEXT;
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

API docs available at **http://localhost:8000/docs**

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/google` | Verify Google ID token → return JWT |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload PDF/DOCX/TXT |
| GET | `/api/documents/` | List user's documents |
| GET | `/api/documents/{id}/status` | Poll processing status |

### Study
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/study/summary` | Generate summary + key points |
| POST | `/api/study/quiz` | Generate MCQ quiz |
| POST | `/api/study/flashcards` | Generate flashcards |

### Interview
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/interview/generate` | Generate an interview question |
| POST | `/api/interview/evaluate` | Submit answer (text or audio) → score + feedback |

### Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions/` | List all sessions |
| GET | `/api/sessions/{id}` | Get session detail + results |

## Running Tests

```bash
pytest tests/ -v
```

All tests mock Supabase and OpenAI — no real credentials needed to run the test suite.

## CI

GitHub Actions runs the full test suite on every push and pull request to `main`. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
