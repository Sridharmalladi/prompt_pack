# CLAUDE.md — AI Study Assistant Frontend

> A lo-fi illustrated web app for RAG-powered studying and interview prep.
> Aesthetic reference: deep purple night sky, cartoon/anime illustration style, calm & moody.

---

## Project Overview

Build the **React + Vite** frontend for the AI Study Assistant backend. The app allows users to:

1. **Authenticate** via Google OAuth
2. **Upload documents** (PDF, DOCX, TXT) and track processing status
3. **Study Mode** — generate summaries, MCQ quizzes, and flashcards from their documents
4. **Interview Mode** — receive interview questions, submit typed or voice answers, get scored feedback
5. **Session History** — review past study and interview sessions

---

## Tech Stack

| Layer | Tool |
|---|---|
| Framework | React 18 + Vite |
| Routing | React Router v6 |
| State Management | Zustand |
| API Client | Axios with interceptors |
| Styling | Tailwind CSS + custom CSS variables |
| Animations | Framer Motion |
| Forms | React Hook Form + Zod |
| Auth | Google OAuth via `@react-oauth/google` |
| Icons | Lucide React |
| Fonts | Google Fonts (see Design System) |
| Voice Recording | `react-media-recorder` |
| File Upload | `react-dropzone` |
| Notifications | `react-hot-toast` |

---

## Design System

### Aesthetic Direction

**Lo-fi Nocturnal Cartoon** — Inspired by late-night illustrated scenes: deep indigo skies, soft purple glows, warm gold accents, and a hand-drawn illustrated quality. Think lo-fi study beats visualized as a UI. Calm, focused, slightly cinematic.

Every screen should feel like you're studying at 2am with good music on — peaceful, immersive, productive.

### Color Palette (CSS Variables)

```css
:root {
  /* Backgrounds */
  --bg-void:        #0d0818;   /* Deepest background — near black purple */
  --bg-deep:        #120f2a;   /* Main page background */
  --bg-surface:     #1c1640;   /* Cards, panels */
  --bg-elevated:    #251e52;   /* Modals, dropdowns, hover states */
  --bg-overlay:     #2e266b;   /* Selected states, active items */

  /* Purple Scale */
  --purple-dim:     #3d2f8a;
  --purple-mid:     #5b45c2;
  --purple-bright:  #7c62e8;
  --purple-glow:    #a08df0;
  --purple-soft:    #c4b8f8;

  /* Accent — Warm Gold */
  --gold-deep:      #8a6200;
  --gold-mid:       #c49a2a;
  --gold-bright:    #e8c547;
  --gold-glow:      #f5d97a;

  /* Text */
  --text-primary:   #ede8ff;   /* Soft lavender-white */
  --text-secondary: #a89fd4;   /* Muted purple-grey */
  --text-muted:     #6b6190;   /* Subtle, placeholder text */
  --text-inverse:   #0d0818;

  /* Semantic */
  --success:        #4ecca3;   /* Teal-green — scores, correct */
  --warning:        --gold-bright;
  --error:          #e85f7c;   /* Warm pink-red */
  --info:           --purple-bright;

  /* Borders */
  --border-subtle:  rgba(124, 98, 232, 0.15);
  --border-default: rgba(124, 98, 232, 0.3);
  --border-strong:  rgba(124, 98, 232, 0.6);

  /* Glows */
  --glow-purple:    0 0 40px rgba(124, 98, 232, 0.25);
  --glow-gold:      0 0 30px rgba(232, 197, 71, 0.2);
  --glow-card:      0 8px 32px rgba(13, 8, 24, 0.6);
}
```

### Typography

```css
/* Import in index.css */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --font-display:  'Syne', sans-serif;      /* Headings, nav, labels — wide, geometric */
  --font-body:     'DM Sans', sans-serif;   /* Body text, paragraphs */
  --font-mono:     'JetBrains Mono', mono;  /* Code, scores, metadata */
}
```

### Visual Texture & Effects

- **Background grain**: Apply a subtle noise texture overlay on `--bg-deep` using an SVG filter or CSS `background-image: url("data:image/svg+xml...")`. Opacity ~0.04.
- **Ambient blobs**: Place 2–3 large blurred radial gradient blobs in fixed positions behind content (pure CSS, `position: fixed`, `z-index: -1`, `pointer-events: none`). Colors: `--purple-mid` at 15% opacity and `--gold-deep` at 8% opacity.
- **Card glow on hover**: Cards lift with `box-shadow: var(--glow-card)` and a faint `--border-default` border that brightens to `--border-strong` on hover.
- **Glassmorphism panels**: Use `backdrop-filter: blur(16px)` on sidebar and modal elements with `background: rgba(28, 22, 64, 0.7)`.
- **Illustrated empty states**: Each empty state (no documents, no sessions) should use an SVG illustration with the purple/gold palette — characters studying, stars, books floating.

---

## Project Structure

```
frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── main.jsx
│   ├── App.jsx                     # Router setup
│   ├── index.css                   # Global styles, CSS variables, fonts
│   │
│   ├── api/
│   │   ├── client.js               # Axios instance + JWT interceptor
│   │   ├── auth.js                 # POST /api/auth/google
│   │   ├── documents.js            # Upload, list, poll status
│   │   ├── study.js                # Summary, quiz, flashcards
│   │   ├── interview.js            # Generate question, evaluate answer
│   │   └── sessions.js             # List sessions, get detail
│   │
│   ├── store/
│   │   ├── authStore.js            # Zustand: user, token, login/logout
│   │   ├── documentStore.js        # Zustand: documents list, active doc
│   │   └── sessionStore.js         # Zustand: session history
│   │
│   ├── hooks/
│   │   ├── useDocumentPoller.js    # Poll /status until ready
│   │   ├── useVoiceRecorder.js     # Wrap react-media-recorder
│   │   └── useStudySession.js      # Manage active study/interview state
│   │
│   ├── pages/
│   │   ├── LandingPage.jsx         # Hero + Google login CTA
│   │   ├── DashboardPage.jsx       # Docs list + quick actions
│   │   ├── UploadPage.jsx          # Dropzone + processing progress
│   │   ├── StudyPage.jsx           # Mode selector → content area
│   │   ├── InterviewPage.jsx       # Question flow + answer + feedback
│   │   └── SessionsPage.jsx        # History list + session detail
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.jsx        # Sidebar + main content wrapper
│   │   │   ├── Sidebar.jsx         # Nav links, user avatar, logout
│   │   │   └── TopBar.jsx          # Mobile header
│   │   │
│   │   ├── auth/
│   │   │   └── GoogleSignInButton.jsx
│   │   │
│   │   ├── documents/
│   │   │   ├── DocumentCard.jsx    # Doc name, status badge, actions
│   │   │   ├── DocumentList.jsx
│   │   │   ├── UploadDropzone.jsx
│   │   │   └── ProcessingStatus.jsx # Animated status steps
│   │   │
│   │   ├── study/
│   │   │   ├── ModeSelector.jsx    # Summary / Quiz / Flashcards tabs
│   │   │   ├── SummaryView.jsx     # Summary + key points
│   │   │   ├── QuizView.jsx        # MCQ question + answer reveal
│   │   │   └── FlashcardView.jsx   # Flip card animation
│   │   │
│   │   ├── interview/
│   │   │   ├── QuestionCard.jsx    # Interview question display
│   │   │   ├── AnswerInput.jsx     # Text textarea OR voice recorder
│   │   │   ├── VoiceRecorder.jsx   # Record + waveform animation
│   │   │   └── FeedbackCard.jsx    # Score + detailed feedback
│   │   │
│   │   ├── sessions/
│   │   │   ├── SessionCard.jsx
│   │   │   └── SessionDetail.jsx
│   │   │
│   │   └── ui/
│   │       ├── Button.jsx          # Variants: primary, ghost, danger
│   │       ├── Card.jsx            # Glassmorphism base card
│   │       ├── Badge.jsx           # Status, score, mode labels
│   │       ├── LoadingSpinner.jsx  # Orbital animation in purple
│   │       ├── ProgressBar.jsx     # Gold fill on purple track
│   │       ├── Modal.jsx           # Framer Motion animated modal
│   │       ├── Tooltip.jsx
│   │       └── EmptyState.jsx      # SVG illustration + message
│   │
│   └── utils/
│       ├── formatters.js           # Dates, scores, durations
│       └── validators.js           # File type/size checks
│
├── .env.example
├── vite.config.js
├── tailwind.config.js
└── package.json
```

---

## Pages & Flows

### 1. Landing Page (`/`)

**Purpose**: First impression. Convert visitors to users.

**Layout**:
- Full-screen dark background with ambient blob effects + grain
- Center-aligned hero with large `--font-display` heading
- Subtitle in `--text-secondary`
- Google Sign In button (gold accent, subtle glow)
- Floating illustrated elements (books, stars, document icons) with slow CSS float animation
- Bottom: three feature pills ("Study smarter", "Interview ready", "Your documents, your AI")

**Copy**: 
- Headline: "Study like it's 2am and you're finally in the zone."
- Sub: "Upload your docs. Let AI handle the rest."

---

### 2. Dashboard (`/dashboard`)

**Purpose**: Central hub showing all documents and quick-start actions.

**Layout**:
- Left sidebar (fixed, glassmorphism) with nav links and user avatar
- Main area: "Your Documents" grid
- Each `DocumentCard` shows: filename, upload date, status badge (`processing` / `ready`), and action buttons (Study, Interview, Delete)
- Floating `+` upload button (gold, bottom-right FAB)
- Empty state with illustrated character reading a floating document

**Interactions**:
- Status badges pulse-animate while `processing`
- Cards lift on hover with `--glow-purple`
- Clicking Study/Interview navigates to that mode with `?docId=` param

---

### 3. Upload Page (`/upload`)

**Purpose**: Upload a document and watch it process.

**Layout**:
- Large centered dropzone with dashed animated border (purple)
- Accepts PDF, DOCX, TXT — show file type icons
- After upload: processing pipeline visualized as 5 animated steps:
  1. Uploading
  2. Extracting text
  3. Cleaning
  4. Chunking
  5. Embedding & storing

- Each step has an icon, label, and status (waiting → active pulse → done checkmark)
- Poll `/api/documents/{id}/status` every 2 seconds via `useDocumentPoller`
- On complete: confetti burst + CTA buttons "Start Studying" / "Practice Interview"

---

### 4. Study Page (`/study`)

**Purpose**: Generate and consume study content from a document.

**Layout**:
- Top: document selector dropdown (if multiple docs exist)
- Tab bar: `Summary` | `Quiz` | `Flashcards`

**Summary Tab**:
- "Generate Summary" button triggers POST `/api/study/summary`
- Result: formatted summary block + key points as animated list items
- Loading: skeleton shimmer with purple pulse

**Quiz Tab**:
- "Generate Quiz" button triggers POST `/api/study/quiz`
- Renders MCQ cards one at a time
- User clicks answer → reveal correct/incorrect with color flash + explanation
- Progress bar at top (Q3 of 8)
- Score summary at end with animated score ring

**Flashcard Tab**:
- "Generate Flashcards" button triggers POST `/api/study/flashcards`
- Full 3D flip card animation (CSS `transform: rotateY(180deg)`)
- Front: question / term. Back: answer / definition
- Left/Right navigation arrows
- "I know this" / "Still learning" buttons to track progress

---

### 5. Interview Page (`/interview`)

**Purpose**: Simulate an interview session with AI-generated questions and scored feedback.

**Layout**:
- Document selector at top
- "Generate Question" button → displays `QuestionCard` with animated entrance
- Below question: `AnswerInput` toggle — Text mode or Voice mode

**Text Mode**:
- Large textarea with `--font-body`, subtle border glow on focus
- Word count indicator
- "Submit Answer" button

**Voice Mode** (`VoiceRecorder`):
- Microphone button — click to start recording
- Animated waveform bars (CSS keyframes, purple bars)
- Timer showing recording duration
- "Stop & Submit" button — sends audio blob to `/api/interview/evaluate`

**Feedback Card** (after evaluation):
- Score displayed as large number with animated count-up and color coding:
  - 80–100: `--success` green
  - 50–79: `--gold-bright`
  - 0–49: `--error` pink
- Feedback sections: "What went well", "Areas to improve", "Model answer"
- "Next Question" button resets the flow

---

### 6. Sessions Page (`/sessions`)

**Purpose**: Review past study and interview sessions.

**Layout**:
- List of `SessionCard`s: session type badge, document name, date, item count
- Click to expand `SessionDetail`: full results (quiz answers, interview Q&A + scores)
- Filter bar: All | Study | Interview

---

## API Integration

### Base client (`src/api/client.js`)

```js
import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
})

// Attach JWT from Zustand store on every request
client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401, clear auth and redirect to /
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/'
    }
    return Promise.reject(err)
  }
)

export default client
```

### Environment Variables (`.env`)

```
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

---

## Component Patterns

### Card Component

```jsx
// All cards use this base — glassmorphism effect
<div className="card">
  {children}
</div>

// CSS
.card {
  background: rgba(28, 22, 64, 0.65);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  box-shadow: var(--glow-card);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
  border-color: var(--border-default);
  box-shadow: var(--glow-card), var(--glow-purple);
}
```

### Button Variants

```
primary   → bg: --purple-bright, text: white, hover: --purple-glow
gold      → bg: --gold-bright, text: --bg-void, hover: --gold-glow  (CTAs)
ghost     → border: --border-default, text: --text-secondary, hover: bg --bg-elevated
danger    → border: --error, text: --error, hover: bg rgba(error, 0.1)
```

### Badge / Status Pill

```
processing  → animated pulse dot + "--gold-bright" text on dark bg
ready       → "--success" dot + text
error       → "--error" dot + text
```

### Score Ring

For quiz end screen and interview scores — SVG circle with `stroke-dashoffset` animated from 0 to score value. Color transitions based on score tier.

---

## Animation Guidelines (Framer Motion)

```js
// Page transitions — fade + slide up
const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
  exit:    { opacity: 0, y: -10, transition: { duration: 0.2 } }
}

// Staggered list items
const listVariants = {
  animate: { transition: { staggerChildren: 0.07 } }
}
const itemVariants = {
  initial: { opacity: 0, x: -16 },
  animate: { opacity: 1, x: 0 }
}

// Modal entrance
const modalVariants = {
  initial: { opacity: 0, scale: 0.92 },
  animate: { opacity: 1, scale: 1, transition: { type: 'spring', stiffness: 300, damping: 25 } }
}
```

---

## Routing Structure

```jsx
// App.jsx
<Routes>
  <Route path="/"           element={<LandingPage />} />
  <Route element={<ProtectedRoute />}>
    <Route element={<AppShell />}>
      <Route path="/dashboard"  element={<DashboardPage />} />
      <Route path="/upload"     element={<UploadPage />} />
      <Route path="/study"      element={<StudyPage />} />
      <Route path="/interview"  element={<InterviewPage />} />
      <Route path="/sessions"   element={<SessionsPage />} />
    </Route>
  </Route>
</Routes>
```

`ProtectedRoute` checks `authStore.token` — redirects to `/` if not authenticated.

---

## State Management (Zustand)

```js
// authStore.js
{
  user: null,        // { name, email, picture }
  token: null,       // JWT string
  login: (user, token) => void,
  logout: () => void,
}

// documentStore.js
{
  documents: [],          // array of document objects
  activeDocId: null,
  setActiveDoc: (id) => void,
  addDocument: (doc) => void,
  updateDocStatus: (id, status) => void,
}
```

Persist `authStore` to `localStorage` using Zustand `persist` middleware (token only, not full user object).

---

## Tailwind Config

```js
// tailwind.config.js
export default {
  content: ['./src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        void:    '#0d0818',
        deep:    '#120f2a',
        surface: '#1c1640',
        elevated:'#251e52',
        purple: {
          dim:    '#3d2f8a',
          mid:    '#5b45c2',
          bright: '#7c62e8',
          glow:   '#a08df0',
          soft:   '#c4b8f8',
        },
        gold: {
          deep:   '#8a6200',
          mid:    '#c49a2a',
          bright: '#e8c547',
          glow:   '#f5d97a',
        },
      },
      fontFamily: {
        display: ['Syne', 'sans-serif'],
        body:    ['DM Sans', 'sans-serif'],
        mono:    ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'float':     'float 6s ease-in-out infinite',
        'pulse-glow':'pulse-glow 2s ease-in-out infinite',
        'waveform':  'waveform 1.2s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':       { transform: 'translateY(-12px)' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 8px rgba(124,98,232,0.4)' },
          '50%':       { boxShadow: '0 0 24px rgba(124,98,232,0.8)' },
        },
        waveform: {
          '0%':   { height: '4px' },
          '100%': { height: '24px' },
        },
      },
    },
  },
}
```

---

## Development Commands

```bash
# Install
npm install

# Dev server
npm run dev

# Build
npm run build

# Preview build
npm run preview
```

---

## Key Implementation Notes

1. **Voice recording**: Use `react-media-recorder` to capture audio as a `Blob`, then send via `FormData` to `/api/interview/evaluate` with `answer_audio` field.

2. **Document polling**: Poll every 2s with `setInterval`, clear on `status === 'ready'` or `status === 'error'`. Show animated step progress during polling.

3. **Flashcard flip**: Use CSS `perspective` + `transform-style: preserve-3d` on the card container, and `rotateY(180deg)` on click. Front/back are absolutely positioned children.

4. **Google Sign In flow**:
   ```js
   // After Google returns credential (ID token):
   const { data } = await authApi.googleLogin(credential)
   authStore.login(data.user, data.token)
   navigate('/dashboard')
   ```

5. **Error states**: Every API call should have a caught error path that shows a `react-hot-toast` in `--error` color with a helpful message.

6. **Loading skeletons**: Use CSS `background: linear-gradient(90deg, var(--bg-surface), var(--bg-elevated), var(--bg-surface))` animated shimmer — not spinners — for content that loads inline.

7. **Responsive layout**: Sidebar collapses to bottom nav bar on mobile (`< 768px`). All cards go full-width on small screens.

---

## Quality Bar

Before considering the frontend complete, verify:

- [ ] All 6 pages render correctly with real API data
- [ ] Google OAuth flow completes end-to-end
- [ ] Document upload + status polling works
- [ ] All three study modes (summary, quiz, flashcards) are functional
- [ ] Voice recording captures audio and receives feedback
- [ ] Sessions page shows accurate history
- [ ] Framer Motion page transitions are smooth
- [ ] Mobile layout is usable on 375px width
- [ ] No console errors in production build
- [ ] JWT persists across page refresh
- [ ] 401 errors log the user out gracefully
