You are building the backend for Data Science Buddy. Read BACKEND_BRIEF_V2.md in full before doing anything else.

Once read, confirm in 5 bullet points that you understand:
1. The tech stack (FastAPI, Polars, scikit-learn, Anthropic SDK)
2. The agentic architecture (Claude as brain, Python functions as tools)
3. The cost constraints (Haiku for orchestration, Sonnet for deep reasoning, prompt caching always on)
4. Hard constraints (no raw data to LLM, max_tokens caps, JSON validation)
5. The data flow from upload → semantic scan → profile → graph → agentic reasoning → response

BUILD STRATEGY — vertical slices, never horizontal layers.

Build in this exact order. After each slice, stop and tell me it's working before moving on:

SLICE 1 — Project skeleton
- Create the full folder structure exactly as defined in the brief
- Add main.py with /health endpoint only
- Set up Docker Compose
- Install dependencies (FastAPI, Polars, scikit-learn, anthropic, pydantic v2, loguru, redis)
- Verify /health returns {"status": "ok"} via curl
- STOP and confirm

SLICE 2 — File upload pipe
- POST /analyze accepts multipart form (file, target_column, problem_type, optional domain)
- Validate file format (csv, xlsx, parquet only)
- Reject files over 100MB with clear error
- Reject if column count > 200
- Return basic file info: filename, size, row count, column count
- Add Pydantic models for the request/response
- STOP and confirm

SLICE 3 — Profiler service
- Implement profiler.py using POLARS (not pandas)
- Sample to 100k rows if dataset is larger
- Compute per-column: dtype, mean, std, missing %, skew
- Top 10 Pearson correlations with target
- Mutual information scores via scikit-learn
- Class distribution + imbalance flag
- IQR outlier detection
- Wire it into /analyze, return the full profile JSON
- STOP and confirm

SLICE 4 — Graph builder
- Implement graph_builder.py
- Nodes = all features, edges = correlations > 0.3 or MI above threshold
- Cap at 15 edges max (highest weight)
- Detect multicollinearity clusters
- Wire into /analyze response
- STOP and confirm

SLICE 5 — Semantic scanner (Haiku micro-call)
- Implement semantic_scanner.py
- Send only column names + first 3 rows to Haiku
- max_tokens = 200, always Haiku
- Returns {column: semantic_label} dict
- Wire into /analyze BEFORE the profiler step
- STOP and confirm

SLICE 6 — Agentic reasoning core
- Implement llm_client.py with native Anthropic SDK tool use
- Define tools as Python functions: get_column_stats, get_correlation, check_leakage, get_distribution, check_outliers, check_missingness_pattern, validate_data_types, propose_interaction
- Claude orchestrates with Haiku for small datasets, Sonnet for complex
- Cap total tool calls per session at 10
- Prompt caching enabled on system prompt always
- max_tokens = 1000
- Temperature = 0
- Parse final JSON output strictly with Pydantic
- On JSON parse fail: retry ONCE with Haiku, then return 422
- Wire into /analyze as final step
- STOP and confirm

SLICE 7 — Chat endpoint
- Implement chat_client.py
- POST /chat takes question + context (summary + insights) + session_id
- Always Haiku, max_tokens = 300
- Hard limit 3 messages per session (track in Redis or in-memory)
- Returns plain text answer + messages_remaining count
- STOP and confirm

SLICE 8 — Notebook export
- Implement notebook_generator.py
- POST /generate-notebook takes insights + summary
- Sonnet, max_tokens = 1500
- Returns valid .ipynb JSON string
- STOP and confirm

SLICE 9 — Error handling + logging hardening
- loguru on every service: entry, exit, errors
- Standard error response format: { error, code, where }
- Graceful handling: unsupported format, missing target column, empty file, parse failures, rate limits
- Add request ID middleware for tracing
- STOP and confirm

RULES FOR EVERY SLICE:
- Use Pydantic v2 for all data models
- Type-hint every function fully
- Add docstrings explaining what each function does and why
- Never write code I'd need to refactor later — clean from the start
- One responsibility per function
- If you find yourself writing the same logic twice, extract a helper
- No bare except clauses — catch specific exceptions
- Log every external call (file read, LLM call, Redis call)
- Validate inputs at boundaries (Pydantic on API, asserts on internal services)

DO NOT:
- Skip ahead to later slices
- Write tests yet (we'll add them after slice 9)
- Add features not in the brief
- Use pandas anywhere — Polars only
- Use LangChain or LlamaIndex — native Anthropic SDK only
- Train any model or use AutoML
- Send raw dataset rows to the LLM, ever

When done with each slice, give me:
- A one-line summary of what works now
- The curl command to test it
- Anything ambiguous you had to decide