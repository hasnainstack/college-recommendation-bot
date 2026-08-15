# 🎓 University Comparison Bot

Compare universities using real student experiences from Reddit, analysed by Gemini AI.

## Architecture

```
frontend/   ← Next.js 16 · TypeScript · Tailwind CSS · App Router
backend/    ← FastAPI · Python · Gemini API · Reddit (PRAW)
```

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # fill in your keys
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # already set to http://localhost:8000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment Variables

### backend/.env

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | Gemini API key from Google AI Studio |
| `REDDIT_CLIENT_ID` | Reddit app client ID |
| `REDDIT_CLIENT_SECRET` | Reddit app client secret |
| `REDDIT_USERNAME` | Reddit account username |
| `REDDIT_PASSWORD` | Reddit account password |
| `REDDIT_USER_AGENT` | e.g. `UniCompareBot/1.0 by u/YourUsername` |

### frontend/.env.local

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend URL (default: `http://localhost:8000`) |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/compare` | Run single or compare analysis |
| `GET` | `/api/static` | Fetch static university lists |

## Project Structure

```
frontend/
  app/
    layout.tsx          root layout
    page.tsx            main client page
    globals.css         all styles + design tokens
  components/
    layout/             Navbar, Footer, LeftSidebar, RightSidebar
    forms/              CompareForm
    results/            ResultsPanel, Scorecard, WinnersGrid, UniversityCard, LoadingPanel
    ui/                 AboutPage, FAQPage, UniversitiesPage
  lib/
    api.ts              all fetch calls
    constants.ts        design tokens + static data
    utils.ts            helpers
  types/
    index.ts            all TypeScript interfaces

backend/
  app/
    main.py             FastAPI app + all logic
  requirements.txt
  .env.example
```
