# prompt_pack

A collection of AI tools, workflows, and prompts built by Sridhar Malladi. Each directory is a standalone project — some are full apps, some are n8n workflows, some are just prompts.

---

## Projects

### [jd2resume_n8n](./jd2resume_n8n/)
n8n workflow: POST a job description, receive a one-page tailored PDF resume. Two-pass Anthropic pipeline with character budget validation, Gotenberg PDF rendering, and page-count retry loops. Self-hosted with Docker.

### [jd2resume](./jd2resume/)
Prompts behind the resume tailoring system — the meta-recruiter system prompt and JD metadata extraction prompt used in `jd2resume_n8n`.

### [dsbuddy](./dsbuddy/)
AI assistant that auto-profiles uploaded datasets, builds feature correlation graphs, and generates Jupyter notebooks. Uses cost-optimized Claude Haiku/Sonnet routing. FastAPI backend, Next.js frontend.

### [RAGLens](./RAGLens/)
Live benchmarking tool for RAG configurations. Compares baseline, with reranker, with fine-tuned embeddings, and hybrid retrieval side-by-side using LLM-as-judge scoring. Built to quantify what each RAG component actually adds.

### [jobfinddaily](./jobfinddaily/)
MCP server for Claude Desktop that discovers, filters, and scores remote AI/ML startup jobs daily. Sources: HN Hiring + RemoteOK + Tavily. All filtering is deterministic regex — no LLM in the data pipeline.

### [jobapp](./jobapp/)
Job application tracker with semantic search. Upload job postings, parse them, match against resume embeddings. Postgres + pgvector backend, Gradio UI.

### [aiflash](./aiflash/)
AI-powered flashcard generator. Paste any content, get structured study cards back. FastAPI + React.

### [localagent](./localagent/)
Local task agent that classifies intent, routes to the right action handler, and executes. Python, no external orchestration framework.

### [marketing agent](./marketing%20agent/)
Marketing analytics agent that pulls campaign data, runs attribution analysis, and generates executive summaries.

### [resumemaker](./resumemaker/)
Lightweight resume PDF generator. Takes structured input, outputs a formatted PDF. Gradio interface, ReportLab for rendering.

### [Speech2Text](./Speech2Text/)
Voice-to-text tool with post-processing for cleanup and formatting.

### [Prompts](./Prompts/)
Standalone prompts and prompt engineering notes — job search prompts, learning frameworks, and general-purpose system prompts.

---

## Stack patterns across these projects

- **LLM routing:** Most projects use Claude (Haiku for cheap/fast, Sonnet for quality) — routing logic lives in the app, not the prompt.
- **PDF generation:** Gotenberg (HTML → PDF via headless Chromium) for layout-critical outputs; ReportLab for simpler docs.
- **Workflow orchestration:** n8n for webhook-triggered pipelines; plain Python for agent loops.
- **Vector search:** pgvector (Postgres) or FAISS depending on whether persistence matters.
- **Interfaces:** Gradio for quick tools, Next.js/FastAPI for anything user-facing.
