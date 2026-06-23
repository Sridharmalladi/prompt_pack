You are building the frontend for Data Science Buddy. Read FRONTEND_BRIEF_V2.md in full before doing anything else.

Once read, confirm in 5 bullet points that you understand:
1. The tech stack (Next.js 14, TypeScript, Tailwind, shadcn/ui, React Flow, Recharts, Zustand, TanStack Query)
2. The two pages (upload + dashboard) and their responsibilities
3. The TypeScript types must match the backend Pydantic models exactly
4. The constraint that frontend never calls LLM directly — only the FastAPI backend
5. The chat drawer pattern with 3 message limit enforcement in UI

BACKEND CONTEXT: The backend runs on http://localhost:8000. Available endpoints: /health, /analyze, /chat, /generate-notebook. Match the TypeScript types exactly to the backend Pydantic responses.

BUILD STRATEGY — vertical slices, never horizontal layers.

SLICE 1 — Project skeleton + connectivity proof
- Create Next.js 14 app with App Router, TypeScript, Tailwind
- Install shadcn/ui, React Flow, Recharts, Zustand, TanStack Query
- Create lib/api.ts with typed fetch wrappers
- Create lib/types.ts with all interfaces from the brief
- Build a tiny landing page that calls /health on the backend and displays the response
- Verify it works end to end
- STOP and confirm

SLICE 2 — Upload page (no real analysis yet)
- Build app/page.tsx
- Drag-drop zone using react-dropzone + shadcn/ui (.csv, .xlsx, .parquet)
- Target column text input
- Problem type toggle (classification / regression)
- Optional domain selector dropdown
- Submit button posts to /analyze
- ProgressStepper component showing: Uploading → Scanning → Profiling → Reasoning → Done
- On success: store result in Zustand and navigate to /dashboard
- On error: inline error display
- STOP and confirm

SLICE 3 — Dashboard layout + dataset summary
- Build app/dashboard/page.tsx with 3-column desktop layout (stacked on mobile)
- DatasetSummaryCard component: rows, columns, missing %, target, quality badge, semantic labels
- Pull data from Zustand store
- Skeleton loading states
- STOP and confirm

SLICE 4 — Insight panel
- Build InsightPanel with all 8 sections from the schema
- Summary always visible at top
- Other sections collapsible accordion (shadcn/ui Accordion)
- RiskBadge component for severity coloring
- Confidence badges on feature engineering items
- STOP and confirm

SLICE 5 — Feature relationship graph
- Build FeatureGraphView using React Flow
- Nodes = features, color by importance (green/yellow/gray)
- Edge thickness by correlation weight
- Click node opens popover with stats + LLM reasoning
- Semantic labels shown as node badges (ID, DATE, LEAKAGE warning)
- Mini-map + zoom + pan
- STOP and confirm

SLICE 6 — Distribution charts + risk heatmap
- DistributionChart: Recharts histograms for top 6 features (3x2 grid)
- RiskHeatmap: features × risk types grid with hover detail
- Click chart highlights that feature node in the graph above
- STOP and confirm

SLICE 7 — Chat drawer
- Slide-out panel from right (shadcn/ui Sheet)
- Floating button bottom right showing "Ask AI (3 remaining)"
- ChatMessage components for bubbles
- ChatInput with send button + counter
- POST to /chat with session_id + question + context from store
- Disabled state when 0 messages remaining
- Loading dots while waiting for response
- STOP and confirm

SLICE 8 — Notebook export
- Button top right of dashboard
- POST to /generate-notebook
- Loading spinner during generation
- Auto-download as dsbuddy_analysis.ipynb on success
- Toast notification on error
- STOP and confirm

SLICE 9 — Polish + responsive + dark mode
- All skeleton loading states reviewed
- Error states on every async operation
- Mobile responsive: stack panels, hide graph below 768px, chat becomes bottom sheet
- Dark mode via Tailwind dark class
- Smooth transitions and hover states
- STOP and confirm

RULES FOR EVERY SLICE:
- Zero `any` types — fully typed throughout
- All server state through TanStack Query — no raw useEffect fetching
- All global state through Zustand
- Use shadcn/ui components everywhere — no custom UI primitives
- Loading + error state required on every async operation
- Never render raw LLM text — always parse structured JSON fields
- Match Pydantic shapes from backend exactly

DO NOT:
- Skip slices
- Call Claude directly from frontend — only via FastAPI backend
- Show model names, token counts, or cost info to users
- Auto-trigger notebook export — only on explicit button click
- Use any state library other than Zustand + TanStack Query

When done with each slice, give me:
- A one-line summary of what works now
- How to verify visually
- Anything ambiguous you had to decide