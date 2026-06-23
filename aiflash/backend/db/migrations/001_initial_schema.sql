-- ============================================================
-- AI Study Assistant — Initial Schema
-- Run this once in the Supabase SQL editor (Dashboard → SQL editor)
-- ============================================================

-- ── users ────────────────────────────────────────────────────
CREATE TABLE users (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  email       TEXT        UNIQUE NOT NULL,
  google_id   TEXT        UNIQUE NOT NULL,
  name        TEXT,
  avatar_url  TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── documents ────────────────────────────────────────────────
CREATE TABLE documents (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID        REFERENCES users(id) ON DELETE CASCADE,
  filename     TEXT        NOT NULL,
  file_type    TEXT        NOT NULL,   -- 'pdf' | 'docx' | 'txt'
  raw_text     TEXT,
  status       TEXT        DEFAULT 'processing',  -- 'processing' | 'ready' | 'failed'
  storage_path TEXT,                   -- Supabase Storage path
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── document_chunks (pgvector) ────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID        REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INTEGER     NOT NULL,
  content     TEXT        NOT NULL,
  embedding   VECTOR(1536),            -- text-embedding-3-small dimension
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat index for fast cosine similarity search
CREATE INDEX ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ── study_sessions ────────────────────────────────────────────
CREATE TABLE study_sessions (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID        REFERENCES users(id) ON DELETE CASCADE,
  document_id  UUID        REFERENCES documents(id) ON DELETE CASCADE,
  session_type TEXT        NOT NULL,   -- 'quiz' | 'summary' | 'flashcard'
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- ── quiz_results ──────────────────────────────────────────────
CREATE TABLE quiz_results (
  id             UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id     UUID    REFERENCES study_sessions(id) ON DELETE CASCADE,
  question       TEXT    NOT NULL,
  options        JSONB   NOT NULL,
  correct_answer TEXT    NOT NULL,
  user_answer    TEXT,
  is_correct     BOOLEAN,
  explanation    TEXT
);

-- ── interview_sessions ────────────────────────────────────────
CREATE TABLE interview_sessions (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        REFERENCES users(id) ON DELETE CASCADE,
  document_id UUID        REFERENCES documents(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── interview_results ─────────────────────────────────────────
CREATE TABLE interview_results (
  id         UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID    REFERENCES interview_sessions(id) ON DELETE CASCADE,
  question   TEXT    NOT NULL,
  user_answer TEXT,
  score      INTEGER,   -- 0–10
  strengths  JSONB,
  weaknesses JSONB,
  feedback   TEXT
);
