# jd2resume_n8n

Paste a job description, get back a one-page tailored PDF resume. Webhook in, PDF out — no UI, no accounts.

Built on self-hosted n8n. Calls the Anthropic API twice per request (once to read the JD, once to rewrite the resume), validates character budgets, renders to HTML, converts via Gotenberg, and confirms single-page output before saving.

---

## Architecture

```
POST /webhook/resume-tailor
  { "jd": "..." }
         │
         ▼
┌─────────────────────┐
│  Load and Validate  │  reads master_resume.json, both prompts,
│                     │  and resume.html template from disk via fs
│                     │  resets retry counters in staticData
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Build Extract      │  serialises Anthropic API request body
│  Request            │  (model, system prompt, jd as user msg)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Anthropic:         │  POST /v1/messages
│  Extract Metadata   │  extracts company, role, seniority, archetype
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Parse Metadata     │  regex-extracts first {...} block from response
│                     │  builds the full tailoring request body
│                     │  appends retry reason if this is a retry pass
└──────────┬──────────┘
           │
           ▼  ◄──────────────────────────────────────────┐
┌─────────────────────┐                                   │
│  Anthropic:         │  POST /v1/messages                │
│  Tailor Resume      │  rewrites summary, bullets,       │
│                     │  tech stack, projects as JSON     │
└──────────┬──────────┘                                   │
           │                                              │
           ▼                                              │
┌─────────────────────┐      retry (max 2x, with          │
│  Validate Lengths   │  ──► specific compression note) ──┘
│                     │      summary ≤ 280 chars
│                     │      bullets 150–220 chars each
│                     │      tech stack 8–12 items
│                     │      project descriptions ≤ 180 chars
└──────────┬──────────┘
           │  (all budgets pass)
           ▼
┌─────────────────────┐
│  Render HTML        │  populates resume.html placeholders
│                     │  builds experience/project HTML loops
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  HTML to Binary     │  converts HTML string → base64 binary
│                     │  named index.html (required by Gotenberg)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Gotenberg:         │  multipart POST to internal Gotenberg service
│  HTML to PDF        │  returns raw PDF binary
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      retry (max 2x, with tighter budgets,
│  Verify Page Count  │  ──► loops back to Anthropic: Tailor Resume)
│                     │
│  pdf-lib counts     │
│  pages in binary    │
└──────────┬──────────┘
           │  (exactly 1 page)
           ▼
┌─────────────────────┐
│  Save PDF           │  writes to /app/output/
│                     │  filename: Sridhar_Resume_{Company}_{Role}.pdf
└──────────┬──────────┘
           │
           ▼
  { "status": "success",
    "file_path": "...",
    "company": "...",
    "role": "..." }
```

### Key design decisions

**Two-pass Anthropic calls.** The first call is cheap (max 300 tokens) and just reads the JD to get company, role, and recruiter archetype. The second call does the full resume rewrite. Keeping them separate means the tailoring prompt can reference archetype-specific rewrite logic without bloating the metadata extraction.

**Retry loops via backward edges.** n8n doesn't have a native loop node (in v1 execution mode). Retries are implemented by connecting Increment Retry nodes back to Anthropic: Tailor Resume. `$workflow.staticData` holds counters and the retry reason string across loop iterations. Two independent counters: one for length budget violations, one for page overflow.

**All files read at startup.** `Load and Validate` reads `master_resume.json`, both prompt files, and the HTML template upfront using `fs.readFileSync`. This avoids scattered read nodes throughout the graph and makes the data available via `$('Load and Validate')` from any downstream node — including retry branches that reference stable base data.

**Stable node references in retry branches.** Retry nodes that rebuild the Anthropic request body reference `$('Parse Metadata').first().json` for base data (jd, resume, tailorPrompt). Parse Metadata runs once at the start and its output is available throughout the execution regardless of how many retry loops run.

---

## Challenges during the build

**1. Gotenberg rejects files not named `index.html`**
Gotenberg's Chromium-based HTML converter expects the main file to be named `index.html` when submitted as multipart form data. Submitting as `resume.html` silently fails — Gotenberg returns a 200 but the PDF is blank or missing content. The HTML to Binary node explicitly sets `fileName: 'index.html'` on the binary before the Gotenberg POST.

**2. n8n's `readBinaryFile` node changed across versions**
The `n8n-nodes-base.readBinaryFile` node type is not stable across n8n major versions and its binary output property naming is inconsistent. Switched to `fs.readFileSync` inside Code nodes instead — Node.js built-ins are available in n8n's Code node runtime and are not affected by n8n version changes.

**3. Anthropic HTTP request body in n8n**
The `bodyParameters` approach with `name: "="` (a shorthand for sending raw body) only works in some n8n typeVersions and fails silently in others — the request goes out with a malformed or empty body. The fix is to pre-serialize the full request JSON string in a Code node and reference it with `contentType: "raw"` and `body: "={{ $json.requestBody }}"` in the HTTP Request node. Explicit beats clever.

**4. pdf-lib in n8n's sandboxed environment**
n8n Code nodes block external `require()` calls by default. `require('pdf-lib')` throws unless `NODE_FUNCTION_ALLOW_EXTERNAL=pdf-lib` is set as an environment variable on the n8n container. Also, `PDFDocument.load()` is async — n8n Code nodes support `await` natively since v0.198, but only if the Code node is set to run in async mode (typeVersion 2).

**5. Retry loop data availability**
When a retry loop fires (Increment Length Retry → Anthropic: Tailor Resume → Validate Lengths), `$('Parse Metadata')` is referenced inside Validate Lengths to retrieve base data. This works because n8n stores each node's most recent output for the entire execution — it's not cleared on loop-back. If Validate Lengths instead used `$input.first()` to get base data, it would receive the Anthropic API response (not base data) and fail.

**6. LLM JSON wrapping**
Claude occasionally wraps its JSON output in markdown code fences (` ```json ... ``` `). A direct `JSON.parse()` on the raw response text throws. Both parse nodes use `text.match(/\{[\s\S]*\}/)` to extract the first complete `{...}` block before parsing, which handles both wrapped and unwrapped responses.

**7. Page overflow retry needs independent counter**
Length validation and page overflow are two different failure modes, and each needs its own retry limit. Using a single counter would let a length retry "use up" page overflow retries, or vice versa. Two counters in `$workflow.staticData` (`retryCount` and `pageRetryCount`) are reset independently: page overflow resets `retryCount` to 0 so length validation retries are fresh on the next tailoring pass.

---

## Prerequisites

- Docker and Docker Compose
- Anthropic API key — [console.anthropic.com](https://console.anthropic.com)

---

## Setup

```bash
git clone https://github.com/Sridharmalladi/jd2resume_n8n.git
cd jd2resume_n8n

cp .env.example .env
# paste your Anthropic API key into .env

mkdir -p output
docker-compose up -d
```

The `output/` directory must exist before starting — the n8n container writes PDFs there. On Linux, run `chmod 777 output` if the container can't write to it (Docker Desktop on Mac handles this automatically).

---

## Import the workflow

1. Open [http://localhost:5678](http://localhost:5678)
2. Create your owner account on first launch
3. **Workflows → Import from file** → select `workflow.json`
4. Toggle **Active** in the top-right corner

---

## Send a job description

```bash
curl -X POST http://localhost:5678/webhook/resume-tailor \
  -H "Content-Type: application/json" \
  -d '{
    "jd": "We are hiring a Senior Data Scientist to lead our experimentation platform and build production ML models for growth at Acme Corp..."
  }'
```

Success response:

```json
{
  "status": "success",
  "file_path": "/app/output/Sridhar_Resume_Acme_Corp_Senior_Data_Scientist.pdf",
  "company": "Acme Corp",
  "role": "Senior Data Scientist"
}
```

The PDF is at `./output/Sridhar_Resume_Acme_Corp_Senior_Data_Scientist.pdf` on your host machine.

---

## Update the master resume

Edit `data/master_resume.json` directly. No restart needed — the file is read on every request.

Fields you'll update most often:
- `experience[].bullets` — source bullets the LLM rewrites from
- `tech_stack` — full list; 8–12 most relevant are selected per JD
- `projects` — add or swap projects here

---

## Troubleshooting

**401 from Anthropic**
Check that `ANTHROPIC_API_KEY` in `.env` is valid. Restart after editing:
```bash
docker-compose down && docker-compose up -d
```

**Gotenberg not reachable**
Both services must be on the same Docker network. Check:
```bash
docker-compose ps
docker-compose logs gotenberg
```
The n8n container reaches Gotenberg at `http://gotenberg:3000` via the `resume_net` bridge network.

**pdf-lib module not found**
Confirm the env var is set:
```bash
docker-compose exec n8n env | grep pdf
```
Should show `NODE_FUNCTION_ALLOW_EXTERNAL=pdf-lib`.

**PDF is more than one page**
The page overflow retry loop will fire up to 2 times automatically with tighter compression instructions. If it still overflows, reduce the number of bullets in `data/master_resume.json` (Prolific Technologies can safely go from 5 bullets to 4).

**Output directory permission error**
Run `chmod 777 output` on the host, then restart the stack.

---

## Project structure

```
jd2resume_n8n/
├── workflow.json              # n8n workflow — import this
├── data/
│   └── master_resume.json     # source resume, edit this to update content
├── templates/
│   └── resume.html            # single-page HTML template with {{placeholders}}
├── prompts/
│   ├── tailor_system.md       # full tailoring system prompt
│   └── extract_metadata.md    # short prompt to extract company + role from JD
├── output/                    # generated PDFs land here (gitignored)
├── docker-compose.yml
├── .env.example
└── README.md
```
