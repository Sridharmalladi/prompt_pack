# Marketing Analytics Agent

A conversational agent that lets non-technical marketers ask plain-English questions
about campaign and channel performance and get back actual numbers, the SQL that
produced them, and a short takeaway they can act on.

The core idea: marketing teams have all this data — spend, clicks, conversions,
revenue per campaign per day — but the people who need it can't write SQL. Every
"how's paid social doing this month?" becomes a ticket, and the answer shows up a
day later. Dashboards only answer the questions someone thought to build into them.
This fills the gap.

---

## How it works

```
              ┌──────────────┐     question      ┌─────────────────┐
   user  ───▶ │  CLI / API   │ ───────────────▶  │   Agent loop    │
              └──────────────┘                   │  (Claude +      │
                     ▲                           │   tool-use)     │
            answer + │                           └────────┬────────┘
            takeaway │                                    │ tool calls
                     │                                    ▼
                     │                            ┌───────────────────┐
                     └──────────────────────────  │  Tools            │
                                                  │  • get_schema     │
                                                  │  • query_database │──▶ SQLite
                                                  │  • define_metric  │──▶ glossary
                                                  │  • get_trend      │──▶ time-series
                                                  └───────────────────┘
```

The agent loop is hand-rolled Python — no framework on top of Claude. The model
decides which tools to call and in what order. A "best ROAS" question typically
goes: `define_metric("ROAS")` → `get_schema()` → `query_database(...)` → answer.

---

## Stack

| Layer      | Choice                       | Why                                        |
|------------|------------------------------|--------------------------------------------|
| LLM        | Claude (`claude-sonnet-4-6`) | Good tool-use, configurable                |
| Agent loop | Custom Python (~80 lines)    | Every step is visible, nothing hidden      |
| Data       | SQLite                       | Zero setup, file-based, easy to poke at    |
| Retrieval  | In-code keyword glossary     | No extra dependencies; same interface as a vector DB if you want to swap later |
| API        | FastAPI + session management | Standard service layer for client integration |
| Interface  | CLI + REST API               | CLI for dev, API for integration           |

---

## Quickstart

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Build the demo database (90 days, 8 campaigns, 5 channels)
python data/seed.py

# 3. Add your API key
cp .env.example .env   # then paste your Anthropic key in .env

# 4a. Run the CLI
python -m src.cli

# one-shot mode
python -m src.cli "Which channel had the best ROAS over the last 90 days?"

# watch tool calls as they happen
python -m src.cli --verbose

# 4b. Run the API server
uvicorn src.api:app --reload
# POST http://localhost:8000/ask  {"question": "Which channel had the best ROAS?"}
# GET  http://localhost:8000/health
```

## Tests

The SQL validation, database layer, glossary, and tool dispatch are all unit-tested
and run without an API key:

```bash
pytest -q
```

---

## Questions worth trying

- Which channel had the best ROAS over the last 90 days?
- What's our blended CAC, and which campaign is the most expensive to convert on?
- Did Spring Sale's revenue actually spike, or did we just spend more?
- Rank channels by conversion rate — which one looks underfunded?
- How did ROAS trend week over week by channel? (uses `get_trend`)
- Show me monthly spend vs. revenue — are we scaling efficiently?

## Safety

- Generated SQL is validated to be a single `SELECT`/`WITH` before it runs —
  any write or schema keyword gets rejected (`src/database.py`).
- Results are capped at `MAX_ROWS` so a broad query can't dump a whole table into context.
- The loop stops at `MAX_TURNS` to handle cases where a question is unanswerable.
