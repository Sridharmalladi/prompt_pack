# How DSBuddy Works — Frontend ↔ Backend, Start to Finish

---

## The Big Picture

This app has two completely separate programs running in two completely separate places:

| | Frontend | Backend |
|---|---|---|
| **What it is** | Next.js (React) | FastAPI (Python) |
| **Where it runs** | Vercel | Render |
| **What it does** | Shows the UI, collects user input | Does all the real work (reads the CSV, calls Claude, computes stats) |
| **URL** | `frontend-eight-beta-66.vercel.app` | `dsbuddy-api.onrender.com` |
| **Language** | TypeScript | Python |

They are not one app. They are two apps that talk to each other over the internet using HTTP — the same protocol your browser uses to load any webpage.

---

## How They Talk

The frontend never touches the CSV file after upload. It never runs Python. It never calls Claude directly. It just sends an HTTP request to the backend and waits for a response.

```
User picks a CSV
       ↓
Browser sends POST /analyze (with the file attached) to Render URL
       ↓
FastAPI receives the file, runs Polars profiling, calls Claude API
       ↓
FastAPI returns one big JSON object
       ↓
Next.js saves that JSON into Zustand (in-memory state)
       ↓
React reads from Zustand and renders the dashboard
```

That's the entire data flow. Everything on the dashboard — the charts, the AI insights, the risk heatmap — is just React reading from that one JSON object and drawing it.

---

## The Environment Variable Problem (Why the App Broke)

The frontend code that makes the API call looks like this:

```ts
// frontend/lib/api.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
```

This says: "use the environment variable if it exists, otherwise fall back to localhost."

**On your laptop:** The backend runs on `localhost:8000`. This works.

**On Vercel:** There is no `localhost:8000`. The backend is on Render. So if `NEXT_PUBLIC_API_URL` is not set, every single API call silently fails and the user sees nothing.

This is why setting the environment variable in Vercel and then redeploying is mandatory — not optional.

### Why a redeploy is required after changing an env var

There are two kinds of environment variables in Next.js:

| Type | Prefix | When it's read | Example |
|---|---|---|---|
| **Server-side** | none / `NEXT_` | At request time (runtime) | `ANTHROPIC_API_KEY` |
| **Client-side** | `NEXT_PUBLIC_` | At **build time** (baked into JS bundle) | `NEXT_PUBLIC_API_URL` |

`NEXT_PUBLIC_API_URL` starts with `NEXT_PUBLIC_`, which means Next.js literally copies the value into the JavaScript file during `npm run build`. The running app on Vercel is that pre-built JS file. Changing the variable in the Vercel dashboard does not change an already-built file. You have to rebuild — that's what "Redeploy" does.

---

## What Vercel Actually Does

Vercel is not just a server. It runs `npm run build` on your code whenever you push to GitHub (if connected), then serves the output. Each deployment is a snapshot.

```
You push to GitHub
       ↓
Vercel clones your repo
       ↓
Vercel runs: npm install && npm run build
       ↓
Next.js compiles all your .tsx files into static HTML + JS bundles
       ↓
NEXT_PUBLIC_API_URL gets baked into those JS bundles at this step
       ↓
Vercel hosts those files and serves them globally via CDN
```

So "the app on Vercel" is actually a folder of compiled HTML/JS/CSS files, not running TypeScript. That's why changing code means you must push + redeploy.

---

## What Render Actually Does

Render runs your FastAPI Python server inside a Docker container, 24/7 (on the free plan it sleeps after 15 minutes of inactivity and takes ~30 seconds to wake up).

```
You push to GitHub
       ↓
Render (if connected) builds the Docker image from backend/Dockerfile
       ↓
Docker installs all pip packages from requirements.txt
       ↓
Render runs: uvicorn app.main:app --host 0.0.0.0 --port 8000
       ↓
Your FastAPI server is now live at dsbuddy-api.onrender.com
```

The backend is always-on Python. It keeps no state between requests — every `/analyze` call is fresh.

---

## The Full Request Lifecycle (One Analysis Run)

```
1. User drops titanic.csv on the upload page

2. Browser creates a FormData object with the file attached
   POST https://dsbuddy-api.onrender.com/analyze
   Content-Type: multipart/form-data

3. Render wakes up (if sleeping), FastAPI handles the request:
   a. Reads the CSV into a Polars DataFrame
   b. Computes column stats, correlations, mutual info (profiler.py)
   c. Builds a feature graph (nodes = columns, edges = correlations)
   d. Calls Claude Haiku → extracts column semantic labels
   e. Calls Claude Sonnet → generates insights + recommendations
   f. Pydantic validates and serializes everything into JSON

4. FastAPI returns ~50KB of JSON in one response

5. Browser receives the JSON
   → lib/normalize.ts cleans it (null arrays → [], NaN correlations filtered)
   → Zustand store saves it: setResult(normalizedData)
   → router.push("/dashboard")

6. Dashboard page renders:
   → reads result from Zustand
   → React renders InsightPanel, FeatureGraphView, CorrelationPanel, etc.
   → each component reads from the same single JSON object
   → if any component crashes, ErrorBoundary catches it and shows
     an inline error instead of killing the whole page
```

---

## Why the Dashboard Was Crashing

The crash was `TypeError: Cannot read properties of undefined (reading 'length')`.

Claude (the LLM) sometimes returns `"columns": null` inside an Insight object. The frontend code was doing `item.columns.length` — calling `.length` on `null` throws.

The fix was two-layered:

1. **Backend** (`models/responses.py`): `columns: list[str] = Field(default_factory=list)` — Pydantic now defaults null to `[]` before the response even leaves the server.

2. **Frontend** (`lib/normalize.ts`): One normalization pass over the entire API response the moment it enters the Zustand store. Every array field gets `?? []`. This is the "trust boundary" pattern — you never trust data from an external source (even your own LLM) until you've cleaned it.

---

## Key Concepts to Know Cold

**REST API:** The standard way two programs talk over HTTP. The frontend calls URLs on the backend (`GET /health`, `POST /analyze`). The backend responds with JSON. That's it.

**CORS:** Cross-Origin Resource Sharing. When a browser on `vercel.app` tries to call `onrender.com`, the browser blocks it by default (different "origins"). The backend must explicitly say "I allow requests from vercel.app" using CORS headers. FastAPI's `CORSMiddleware` handles this.

**Environment variable:** A value injected into a program from outside — not hardcoded in the source. Used for secrets (API keys) and config that changes between environments (local vs production).

**Build time vs runtime:** Build time = when Vercel runs `npm run build`. Runtime = when a user actually loads the page. `NEXT_PUBLIC_` vars are read at build time. Server secrets are read at runtime.

**Zustand:** In-memory state manager in the browser. Holds the analysis result while the user is on the dashboard. Resets on page refresh (no localStorage) — that's why refreshing the dashboard redirects to upload.

**Pydantic:** Python's data validation library. Defines the shape of the JSON the backend returns. If the LLM returns unexpected data, Pydantic catches it before it reaches the frontend.

**Error boundary:** A React component that wraps other components and catches their crashes. Instead of the whole page going blank, just that section shows an error message.

**Docker:** Packages the Python app + all its dependencies into one portable container. Render runs that container. This is why "it works on my machine" also works on Render — same container everywhere.

---

## The Deployment Checklist (What Must Be True for the App to Work)

```
Vercel:
  ✓ Connected to GitHub repo (auto-deploys on push to main)
  ✓ Root Directory = frontend  (or vercel deploy run from frontend/)
  ✓ NEXT_PUBLIC_API_URL = https://dsbuddy-api.onrender.com
  ✓ Rebuilt after env var was added

Render:
  ✓ ANTHROPIC_API_KEY = sk-ant-...
  ✓ Service is running (check Logs for "Uvicorn running on 0.0.0.0:8000")
  ✓ Connected to GitHub repo (auto-deploys on push to main)

CORS (backend/app/main.py):
  ✓ allow_origins includes https://frontend-eight-beta-66.vercel.app
     (or "*" for development)
```

If any one of these is wrong, the app breaks in a different way:
- Missing `NEXT_PUBLIC_API_URL` → every API call goes to localhost → silent failure
- Missing `ANTHROPIC_API_KEY` → analysis runs but returns no AI insights
- Wrong CORS → browser blocks the request → "Network Error" in the console
- Wrong Root Directory → Vercel builds the wrong folder → 404 on all pages
