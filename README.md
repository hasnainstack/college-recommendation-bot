# University Comparison Bot

Compare Pakistani universities using real student experiences from Reddit, analysed by Gemini AI.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16 · React 19 · TypeScript · Tailwind CSS 4 · App Router |
| Backend | FastAPI · Python · Gemini 1.5 Flash · PRAW (Reddit) |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Google AI Studio](https://aistudio.google.com) API key (free tier)
- Reddit app credentials from [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env         # then fill in your keys
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # pre-configured for localhost:8000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment Variables

### `backend/.env`

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | Gemini API key from Google AI Studio |
| `REDDIT_CLIENT_ID` | Reddit app client ID |
| `REDDIT_CLIENT_SECRET` | Reddit app client secret |
| `REDDIT_USERNAME` | Reddit account username |
| `REDDIT_PASSWORD` | Reddit account password |
| `REDDIT_USER_AGENT` | e.g. `UniCompareBot/1.0 by u/YourUsername` |

### `frontend/.env.local`

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend URL (default: `http://localhost:8000`) |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/compare` | Analyse a single university or compare two |
| `GET` | `/api/static` | Fetch categorised university lists |

## How It Works

1. User submits one or two university names via the frontend form
2. Backend checks if the university is well-known — if so, skips Reddit and uses Gemini's training knowledge directly
3. For lesser-known universities, Reddit is searched in parallel across relevant subreddits using `ThreadPoolExecutor`
4. Fetched posts are truncated and passed to Gemini 1.5 Flash with a structured prompt
5. Gemini returns a JSON response with scores, pros, cons, and a verdict
6. Results are rendered in the frontend with scorecards and a winner summary

## Project Structure

```
backend/
  app/
    main.py                 FastAPI app, Gemini integration, Reddit fetching
  requirements.txt
  .env.example

frontend/
  app/
    layout.tsx              Root layout with custom cursor
    page.tsx                Main client page
    globals.css             Global styles and design tokens
  components/
    layout/                 Navbar, Footer, Hero, FeatureStrip, Sidebars, CustomCursor
    forms/                  CompareForm
    results/                ResultsPanel, Scorecard, WinnersGrid, UniversityCard, LoadingPanel
    ui/                     AboutPage, FAQPage, UniversitiesPage
  lib/
    api.ts                  API fetch functions
    constants.ts            Static data and design tokens
    utils.ts                Utility helpers
  types/
    index.ts                TypeScript interfaces
  next.config.ts            API proxy rewrites to FastAPI
```

## Notes

- The Gemini free tier only supports `gemini-1.5-flash` — do not change the model name
- The Next.js frontend proxies all `/api/*` requests to FastAPI via `next.config.ts` rewrites, so no CORS configuration is needed
- Reddit fetch results are cached in memory per university to avoid redundant API calls
- `reddit_yield_history.json` tracks which subreddits yield useful results over time
