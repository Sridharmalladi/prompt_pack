# dsbuddy

Drop a CSV. Get back something worth reading.

dsbuddy is an AI-powered data analysis tool that turns raw datasets into clear, actionable insights in under 10 seconds — no code, no setup, no fluff.

**Live:** [dsbuddy.vercel.app](https://dsbuddy.vercel.app) · **API:** [dsbuddy.onrender.com](https://dsbuddy.onrender.com)

---

## What it does

Upload any CSV, XLSX, or Parquet file, name your target column, and dsbuddy runs a full automated pipeline:

- **200+ statistics** — missing values, skewness, outliers, correlations, class distributions, duplicate rows, constant columns
- **Semantic column labeling** — understands that `dob` is a date and `amt_usd` is a monetary value
- **Feature relationship graph** — maps which columns are connected, where multicollinearity lives
- **Real model training** — fits Logistic Regression, Random Forest, and Gradient Boosting with 3-fold cross-validation and returns actual scores
- **AI reasoning** — Claude Sonnet reads the full profile and writes a plain-English summary with ranked recommendations and leakage risk flags
- **Streaming progress** — every step streams live so you see exactly what's happening
- **Chat** — ask up to 10 follow-up questions about your dataset; answers stream token by token

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Zustand |
| Backend | FastAPI, Python 3.12, Polars, scikit-learn |
| AI | Anthropic Claude (Haiku for labeling + chat, Sonnet for reasoning) |
| Infra | Vercel (frontend) · Render (backend) · Redis (optional, session store) |

---

## Project structure

```
dsbuddy/
├── frontend/               # Next.js app
│   ├── app/
│   │   ├── upload/         # Landing + upload page
│   │   └── dashboard/      # Analysis results
│   ├── components/
│   │   ├── dashboard/      # Charts, panels, chat drawer
│   │   └── upload/         # Drop zone, progress stepper
│   ├── lib/
│   │   ├── api.ts          # Fetch + SSE streaming client
│   │   ├── store.ts        # Zustand global state
│   │   └── types.ts        # TypeScript interfaces
│   └── public/samples/     # Built-in sample datasets
│
└── backend/                # FastAPI service
    └── app/
        ├── api/routes/     # analyze.py · chat.py
        ├── services/       # profiler · scanner · graph_builder · model_trainer · llm_client · chat_client
        ├── models/         # Pydantic request/response models
        └── core/           # Config · logging · error handlers
```

---

## Running locally

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Copy the example env and fill in your Anthropic key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

uvicorn app.main:app --reload
# API available at http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install

# Point the frontend at your local backend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
# App available at http://localhost:3000
```

### Docker (backend only)

```bash
docker compose up --build
```

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com) |
| `REDIS_URL` | No | Redis connection string. Falls back to in-memory if not set |
| `DEBUG` | No | Set `true` for verbose logging |

> **Never commit `.env`** — it is in `.gitignore`. Use `.env.example` as the template.

### Frontend (`.env.local` or Vercel dashboard)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes in production | Full URL of the backend, e.g. `https://dsbuddy.onrender.com` |

---

## Deploying

### Backend → Render

1. Connect the repo in Render, set root directory to `backend`
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. Add `ANTHROPIC_API_KEY` as an environment variable in the Render dashboard

### Frontend → Vercel

1. Connect the repo in Vercel, set root directory to `frontend`
2. Add `NEXT_PUBLIC_API_URL=https://dsbuddy.onrender.com` as an environment variable
3. Deploy — Vercel handles the rest

---

## Sample datasets

Three built-in datasets are available on the upload page to try the app instantly:

| Dataset | Rows | Target | Task |
|---|---|---|---|
| Spotify Tracks 2024 | 480 | `hit` | Classification |
| NBA Player Stats 2023-24 | 350 | `salary_millions` | Regression |
| Mental Health in Tech | 520 | `treatment` | Classification |

---

## How the analysis pipeline works

```
Upload file
    │
    ├── Semantic scanner    (Claude Haiku)   → column type labels
    ├── Statistical profiler (Polars)        → 200+ metrics per column
    ├── Feature graph builder                → correlation clusters, MI scores
    ├── Model trainer       (scikit-learn)   → 3-fold CV scores for 3 models
    └── LLM reasoning       (Claude Sonnet)  → summary, recommendations, leakage flags
                                                        │
                                               Streamed to browser via SSE
```

Each step emits a Server-Sent Event so the UI updates in real time. The final `done` event carries the full `AnalyzeResponse` JSON.

---

## Key design decisions

- **Polars over pandas** — faster on larger files, no pandas dependency in the backend
- **SSE streaming** — better UX than polling; the frontend consumes the stream with `ReadableStream`
- **No localStorage** — analysis results live in Zustand memory only; refreshing the page clears state
- **Redis optional** — chat session counters fall back to in-memory if Redis is unavailable, so the app works on Render's free tier without an add-on

---

## License

MIT
