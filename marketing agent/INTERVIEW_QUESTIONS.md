# Interview Prep — Marketing Analytics Agent

This file is a complete reference for the project. Reading it from top to bottom should
give anyone a clear picture of what was built, why it exists, how it works technically,
and the decisions that shaped it.

---

## The Project at a Glance

**Q: Tell me about this project — what did you build and what problem does it solve?**

I built a conversational AI agent that lets non-technical marketing teams ask questions
about campaign and channel performance in plain English and get back real, precise
answers — the actual number, the SQL that produced it, and a short takeaway they can
act on.

The problem it solves is a bottleneck that exists in almost every marketing org: the
data is all there — daily spend, clicks, conversions, and revenue broken down by
campaign and channel — but the people most responsible for acting on it can't write SQL.
Every question like "how did paid social do last month?" becomes a Slack message to an
analyst, and by the time the answer shows up, the window to act has already closed.
Dashboards help, but they only surface the questions someone thought to hardcode into
them months ago.

This agent removes that bottleneck entirely. You type a question, the agent decides
which tools to call, queries the database, and returns a precise answer with context and
an actionable takeaway — in seconds, with no analyst in the loop.

---

## What Was Built

**Q: Walk me through the full system — what are all the moving parts?**

There are six main pieces:

**1. The agent loop** (`src/agent.py`) — the core of the system. About 80 lines of
Python. It takes a user's question, appends it to a conversation history, sends
everything to Claude along with tool definitions, and loops: if the model asks for a
tool, the loop runs it and feeds the result back; if the model is done, it returns the
final answer. No framework, no magic — just a loop that checks `stop_reason`.

**2. Four tools** (`src/tools.py`) — the actions the agent can take:
- `get_schema` — returns the actual table and column names from the database so Claude
  writes valid SQL instead of guessing
- `query_database` — runs a validated read-only SELECT against SQLite and returns rows
- `define_metric` — looks up the business definition and formula for a metric like
  ROAS, CAC, or CTR before computing it
- `get_trend` — generates a time-series aggregation of any metric by day, week, or
  month, with optional breakdown by channel or campaign

**3. The database layer** (`src/database.py`) — SQLite with a safety validator in
front of it. Every SQL query is checked before it runs: must be a single SELECT or
WITH, no stacked statements, no write or schema-changing keywords. Results are capped
at 200 rows so a broad query doesn't flood the model's context window.

**4. The glossary** (`src/glossary.py`) — a metric definition store that the
`define_metric` tool queries. Backed by keyword overlap today, but the interface is
shaped like a vector store so swapping to pgvector later is a one-file change.

**5. The REST API** (`src/api.py`) — a FastAPI service that wraps the agent with
session management. Each session keeps its own conversation history so follow-up
questions have context. Sessions are keyed by UUID; a DELETE endpoint clears them.

**6. The CLI** (`src/cli.py`) — an interactive terminal interface for development and
demos. Supports one-shot mode (pass a question as an argument) and `--verbose` to
print each tool call as it happens.

---

## Architecture and Technology

**Q: What is the tech stack and why did you choose each piece?**

| Layer        | Choice                      | Why                                                        |
|--------------|-----------------------------|------------------------------------------------------------|
| LLM          | Claude `claude-sonnet-4-6`  | Strong tool-use capabilities; model is configurable via env var |
| Agent loop   | Custom Python (~80 lines)   | Every step is readable; no black-box abstraction to debug  |
| Database     | SQLite                      | Zero setup, single file, easy to share and demo            |
| Retrieval    | Keyword glossary            | No extra dependencies; interface matches a vector store for easy upgrade |
| API          | FastAPI                     | Clean, fast, Pydantic validation, industry standard        |
| Interface    | CLI + REST API              | CLI for local dev, API for integration                     |

**Q: Why no LangChain or similar framework?**

The agent loop is about 80 lines. If I had used LangChain, those 80 lines would have
been hidden inside a framework and I'd need to understand two things — my own logic and
the framework's abstractions — every time something went wrong. Writing it from scratch
means every round-trip between the model and a tool is visible in a single file. When
I explain how it works, I can point to the actual code instead of saying "and then
LangChain handles that part."

---

## How a Question Becomes an Answer

**Q: Walk me through what happens step by step when a user asks "which channel had the best ROAS last quarter?"**

1. The question is appended to `self.messages` as a user turn.
2. The loop calls `client.messages.create(...)` with the full message history and the
   four tool specs passed as JSON schemas.
3. Claude reads the question and the tool descriptions and comes back with
   `stop_reason = "tool_use"`, asking to call `define_metric("ROAS")`.
4. The loop runs it. The glossary returns: *"Return on Ad Spend = revenue / spend.
   A ROAS of 4 means $4 of revenue for every $1 spent. Higher is better."*
5. That result is appended as a `tool_result` turn and sent back to Claude.
6. Claude now asks for `get_schema()` to confirm which tables and columns exist.
7. With the schema in hand, Claude writes a SELECT that joins `daily_performance`,
   `campaigns`, and `channels`, groups by channel name, and computes
   `ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 2)`.
8. The loop passes that SQL through the safety validator, then executes it.
9. Rows come back. Claude synthesizes a final text answer: the top channel, its ROAS,
   and a one-line takeaway like "Paid Search is your most efficient channel — consider
   shifting budget from Display where ROAS is less than half."
10. `stop_reason = "end_turn"` — the answer is returned. The whole thing takes 3-4
    turns and a few seconds.

---

## The Safety Layer

**Q: How do you prevent the agent from deleting or modifying data?**

Three layers:

**Layer 1 — SQL validation.** Every query goes through `is_safe_select()` in
`database.py` before it runs. It strips the trailing semicolon, checks for any
remaining semicolons (stacked statements like `SELECT 1; DROP TABLE channels`), and
runs a regex over forbidden keywords: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
REPLACE, ATTACH, DETACH, PRAGMA, VACUUM. The query also has to start with SELECT or
WITH or it's rejected outright.

**Layer 2 — Row cap.** Results are limited to `MAX_ROWS = 200`. A broad query can't
dump an entire table into the model's context and degrade response quality.

**Layer 3 — Turn cap.** The loop stops at `MAX_TURNS = 8`. If the model gets stuck
calling tools without converging on an answer, it gives up gracefully rather than
running forever.

**Q: What are the limits of your SQL safety approach?**

It's regex-based, not parser-based. A sufficiently creative payload could theoretically
slip through. In this system the only realistic threat is a confused model, not someone
actively trying to exploit an endpoint — so the approach is solid for this threat model.
For production with arbitrary external users, the right fix is opening the database
connection with a read-only user at the driver level, so writes fail regardless of what
SQL reaches it.

---

## The Glossary and Retrieval Design

**Q: How does the glossary work and why build it with that interface?**

The glossary is a Python dict of term to definition. The `lookup(query)` function
tokenizes the query and each term+definition, counts token overlap, boosts exact acronym
matches, and returns the top-k results. It's lightweight keyword retrieval — fast and
dependency-free.

The interface — `lookup(query) -> list[str]` — was designed from the start to look
identical to what you'd expose over a vector store like pgvector or Pinecone. The agent
never calls the glossary directly; it only ever goes through `define_metric`, which
calls `glossary.lookup()`. That means upgrading the retrieval backend is a one-file
change: swap in a dense embedding model and a vector index, keep the same function
signature, and nothing else in the codebase changes.

---

## Sessions and Multi-Turn Conversations

**Q: If a user asks a follow-up question, does the agent remember the previous answer?**

Yes. The `Agent` class keeps `self.messages` alive between calls, so the full
conversation history is passed to Claude on every turn. "Which campaign had the worst
CAC?" followed by "What was its total spend?" works correctly because the second
question joins the same message list and Claude has the prior context.

The FastAPI endpoint maps one `Agent` instance per session ID in an in-memory dict.
Sessions persist across questions within a server process but not across restarts. For
production, the right upgrade is persisting the message history to Redis — the session
structure is a simple list, so the migration is straightforward.

---

## Testing

**Q: How do you test this without making live API calls every time?**

The test suite in `tests/test_tools.py` covers SQL validation, schema introspection,
glossary lookup, tool dispatch, and the database layer — none of which touch the
Anthropic API. The tests import `database`, `glossary`, and `tools` directly, bypassing
the agent entirely. A `conftest.py` fixture automatically seeds the database before any
test runs, so there's no manual setup required. `pytest -q` runs the full suite fast and
free.

The one thing unit tests don't cover is end-to-end reasoning quality — whether Claude
actually produces a sensible answer to a real question. That was validated manually by
running the CLI against the seeded dataset with questions where the correct answer was
already known.

---

## What's Next

**Q: What would you add if you had more time?**

Three things in order of value:

**Charting.** `get_trend` already returns structured time-series rows. Right now the
model describes the trend in words, which is always worse than showing a plot. A
charting tool that takes those rows and renders a line chart would be a much better
user experience.

**Dense embeddings.** Swap the keyword glossary for pgvector so paraphrases work —
"return on investment" should reach ROAS even though the words don't overlap. The
`lookup()` interface is already shaped for this; only the backend changes.

**Structured logging.** Replace the `--verbose` stdout flag with JSON trace logs for
every tool call and result. Right now it's fine for local development but useless in a
deployed service where you need to trace what the model did on a given question.

---

## Scalability

**Q: How would this hold up at scale?**

The current design is intentionally simple — single process, in-memory sessions, SQLite.
That's the right call for a demo. For production scale, three things would change:

- **Database** → Postgres. Handles concurrent connections properly, supports read-only
  users at the connection level (cleaner than regex validation), and pgvector is already
  there for glossary embeddings.
- **Sessions** → Redis. Persist the message history so the service survives restarts
  and can scale horizontally across workers.
- **Observability** → structured JSON logging of every agent turn so you can trace and
  debug production sessions without reproducing them locally.

The agent loop itself wouldn't change. The architecture was designed so the
intelligence layer (Claude + tools) is completely separate from the storage and serving
layers, which makes swapping those backends straightforward.

---

## My Role

**Q: What was your specific contribution to this project?**

The project was built using AI tools throughout — for architecture decisions,
implementation, identifying bottlenecks, and planning for scale. My contribution was in
the direction and judgment: deciding what to build, framing the right questions for the
AI, evaluating what it produced, and pushing on the parts that weren't good enough.

Key decisions I drove: skipping a framework to keep the loop transparent and debuggable,
designing the safety validator to handle stacked statements rather than just checking the
first word, shaping the glossary interface to mirror a vector store from day one, and
thinking through where the system would break under load before those became real
problems. The skill was knowing what questions to ask, which answers to trust, and where
to push back and iterate.
