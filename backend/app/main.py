from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import Groq
import praw
import prawcore.exceptions as prawcore_exceptions
import os
import json
import re
import logging
import time
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("university_comparison_bot")

# ── Gemini setup ─────────────────────────────────────────────────────────────

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise RuntimeError("GOOGLE_API_KEY not found in environment variables.")

client = genai.Client(api_key=api_key)

GEMINI_MODEL = "gemini-3.6-flash"

GENERATION_CONFIG = types.GenerateContentConfig(
    max_output_tokens=2500,
    temperature=0.2,
)

# ── Groq setup (fallback when Gemini is unavailable) ─────────────────────────

groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

GROQ_MODEL = "openai/gpt-oss-120b"  # Groq's current recommended general-purpose model
GROQ_MAX_TOKENS = 2500
GROQ_TEMPERATURE = 0.2

REDDIT_FETCH_TIMEOUT = 4  # seconds per subreddit search
POST_CHAR_LIMIT = 300      # truncate each Reddit post before caching
MIN_POSTS_TO_TRUST_REDDIT = 3   # below this, treat the uni as "Reddit-sparse"
SPARSE_STREAK_TO_SKIP = 2        # consecutive sparse results before we stop trying

# ── Reddit setup ─────────────────────────────────────────────────────────────

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

# ── Static data ───────────────────────────────────────────────────────────────

FAMOUS_UNIS_PK = {
    "💻 Best for Computer Science": [
        "NUST — National University of Sciences & Technology, Islamabad",
        "LUMS — Lahore University of Management Sciences (SBASSE)",
        "FAST-NUCES — National University of Computer & Emerging Sciences",
        "GIKI — Ghulam Ishaq Khan Institute of Engineering Sciences & Technology",
        "ITU — Information Technology University, Lahore",
        "COMSATS University Islamabad",
        "PUCIT — Punjab University College of Information Technology, Lahore",
        "UET Lahore — University of Engineering & Technology",
        "Air University, Islamabad",
        "Bahria University, Islamabad",
    ],
    "💼 Best for BBA / Business": [
        "LUMS — Suleman Dawood School of Business",
        "IBA Karachi — Institute of Business Administration",
        "NBS — NUST Business School, Islamabad",
        "IoBM — Institute of Business Management, Karachi",
        "LSE — Lahore School of Economics",
        "FAST School of Management",
        "Bahria University Business School",
        "COMSATS Business School",
        "UCP — University of Central Punjab, CBM",
        "Iqra University, Karachi",
    ],
    "🎨 Best for Arts / Humanities & Social Sciences": [
        "University of the Punjab, Lahore",
        "University of Karachi",
        "GCU — Government College University, Lahore",
        "Quaid-i-Azam University, Islamabad",
        "LUMS — Mushtaq Ahmad Gurmani School of Humanities & Social Sciences",
        "Kinnaird College for Women, Lahore",
        "Forman Christian College (A Chartered University), Lahore",
        "NCA — National College of Arts, Lahore",
        "BNU — Beaconhouse National University, Lahore",
        "Fatima Jinnah Women University, Rawalpindi",
    ],
}

POPULAR_PK_COMPARISONS = [
    "NUST vs LUMS",
    "FAST-NUCES vs GIKI",
    "IBA Karachi vs LUMS",
    "COMSATS vs Air University",
    "Punjab University vs Karachi University",
]


# ── Self-learning Reddit-yield cache ──────────────────────────────────────────
# No hardcoded university list. Every university is tried on Reddit the same
# way. We track how many posts actually came back each time, and once a
# university has proven sparse (few/no posts) several times in a row, we
# stop bothering to fetch for it and let the model answer from its own
# knowledge instead. This state is persisted to disk so what it "learns"
# survives server restarts instead of resetting every deploy.

_YIELD_HISTORY_PATH = os.path.join(os.path.dirname(__file__), "reddit_yield_history.json")

def _load_yield_history() -> dict[str, dict]:
    try:
        with open(_YIELD_HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_yield_history() -> None:
    try:
        with open(_YIELD_HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(_reddit_yield_history, f, indent=2)
    except OSError as e:
        logger.warning("Failed to persist Reddit yield history: %s", e)


# uni_name -> {"sparse_streak": int, "skip": bool}
_reddit_yield_history: dict[str, dict] = _load_yield_history()

def _should_skip_reddit(name: str) -> bool:
    n = name.lower().strip()
    history = _reddit_yield_history.get(n)
    return bool(history and history.get("skip"))


def _record_reddit_yield(name: str, post_count: int) -> None:
    n = name.lower().strip()
    history = _reddit_yield_history.setdefault(n, {"sparse_streak": 0, "skip": False})
    if post_count < MIN_POSTS_TO_TRUST_REDDIT:
        history["sparse_streak"] += 1
        if history["sparse_streak"] >= SPARSE_STREAK_TO_SKIP:
            history["skip"] = True
            logger.info("[%s] Learned to skip Reddit (sparse %d times in a row)",
                        name, history["sparse_streak"])
    else:
        history["sparse_streak"] = 0
        history["skip"] = False
    _save_yield_history()

# ── Schemas ───────────────────────────────────────────────────────────────────

class Filters(BaseModel):
    program: str = ""
    budget: str = ""
    career_goal: str = ""
    study_level: str = ""
    campus_priority: str = ""
    international_support: str = ""

class CompareRequest(BaseModel):
    uni1: str
    uni2: Optional[str] = None
    filters: Filters = Filters()

# ── Core logic ────────────────────────────────────────────────────────────────

def _search_reddit_all(university_name: str, limit: int) -> list[dict]:
    """Search across all of Reddit instead of a fixed subreddit list — Reddit's
    own relevance ranking finds the right posts wherever they actually live,
    instead of us guessing which subreddits might have them."""
    posts: list[dict] = []
    try:
        for post in reddit.subreddit("all").search(
            university_name, sort="relevance", limit=limit
        ):
            text = (post.title + " " + (post.selftext or "")).strip()[:POST_CHAR_LIMIT]
            if text:
                posts.append({
                    "text": text,
                    "title": post.title,
                    "url": f"https://reddit.com{post.permalink}",
                    "subreddit": str(post.subreddit),
                })
    except (prawcore_exceptions.PrawcoreException,
            prawcore_exceptions.NotFound,
            prawcore_exceptions.Forbidden) as e:
        logger.warning("Reddit search failed (%s): %s", university_name, e)
    except Exception as e:
        logger.warning("Unexpected error searching Reddit (%s): %s", university_name, e)
    return posts


_reddit_cache: dict[str, tuple[dict, ...]] = {}

def fetch_reviews_cached(university_name: str, limit: int = 20) -> tuple[dict, ...]:
    if university_name in _reddit_cache:
        return _reddit_cache[university_name]
    if _should_skip_reddit(university_name):
        logger.info("[%s] Skipping Reddit (famous, or learned to be sparse — using model knowledge)", university_name)
        _reddit_cache[university_name] = ()
        return ()
    posts: list[dict] = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_search_reddit_all, university_name, limit)
        try:
            posts = future.result(timeout=REDDIT_FETCH_TIMEOUT)
        except TimeoutError:
            logger.warning("[%s] Reddit search hit timeout, no results", university_name)
        except Exception as e:
            logger.warning("[%s] Reddit search failed: %s", university_name, e)
    result = tuple(posts[:20])
    _record_reddit_yield(university_name, len(result))
    _reddit_cache[university_name] = result
    return result


def build_prompt(uni1: str, reviews1: list[dict], uni2: Optional[str],
                 reviews2: list[dict], filters: Filters) -> str:
    prefs = ""
    filter_dict = filters.model_dump()
    if any(filter_dict.values()):
        prefs = "Student preferences: " + ", ".join(
            f"{k}: {v}" for k, v in filter_dict.items() if v
        )

    r1 = "\n".join(p["text"] for p in reviews1[:10])
    src1 = f"{uni1} Reddit posts:\n{r1}" if r1 else f"{uni1}: use your training knowledge."
    base = f"""Return ONLY valid JSON, no markdown. {prefs}
{src1}"""
    if uni2:
        r2 = "\n".join(p["text"] for p in reviews2[:10])
        src2 = f"{uni2} Reddit posts:\n{r2}" if r2 else f"{uni2}: use your training knowledge."
        base += f"\n{src2}"
        base += f"""

Return JSON:
{{
  "mode": "compare",
  "universities": [
    {{
      "name": "{uni1}",
      "overall_score": <1-10>,
      "academic_score": <1-10>,
      "student_life_score": <1-10>,
      "value_score": <1-10>,
      "career_score": <1-10>,
      "satisfaction_score": <1-10>,
      "strengths": ["...", "..."],
      "weaknesses": ["...", "..."],
      "likes": ["...", "..."],
      "complaints": ["...", "..."],
      "academic_experience": "...",
      "housing_cost": "...",
      "student_life": "...",
      "career_internships": "...",
      "things_to_know": "..."
    }},
    {{
      "name": "{uni2}",
      "overall_score": <1-10>,
      "academic_score": <1-10>,
      "student_life_score": <1-10>,
      "value_score": <1-10>,
      "career_score": <1-10>,
      "satisfaction_score": <1-10>,
      "strengths": ["...", "..."],
      "weaknesses": ["...", "..."],
      "likes": ["...", "..."],
      "complaints": ["...", "..."],
      "academic_experience": "...",
      "housing_cost": "...",
      "student_life": "...",
      "career_internships": "...",
      "things_to_know": "..."
    }}
  ],
  "winners": {{
    "overall": "{uni1} or {uni2}",
    "academics": "{uni1} or {uni2}",
    "student_life": "{uni1} or {uni2}",
    "value": "{uni1} or {uni2}",
    "career": "{uni1} or {uni2}"
  }},
  "comparison_summary": "...",
  "recommendation": "...",
  "confidence": "low | medium | high",
  "posts_analyzed": <number>,
  "data_date": "{datetime.now().strftime('%Y-%m-%d')}"
}}"""
    else:
        base += f"""
Return JSON:
{{
  "mode": "single",
  "universities": [
    {{
      "name": "{uni1}",
      "overall_score": <1-10>,
      "academic_score": <1-10>,
      "student_life_score": <1-10>,
      "value_score": <1-10>,
      "career_score": <1-10>,
      "satisfaction_score": <1-10>,
      "strengths": ["...", "..."],
      "weaknesses": ["...", "..."],
      "likes": ["...", "..."],
      "complaints": ["...", "..."],
      "academic_experience": "...",
      "housing_cost": "...",
      "student_life": "...",
      "career_internships": "...",
      "things_to_know": "..."
    }}
  ],
  "comparison_summary": null,
  "recommendation": "...",
  "confidence": "low | medium | high",
  "posts_analyzed": <number>,
  "data_date": "{datetime.now().strftime('%Y-%m-%d')}"
}}"""
    return base


def parse_response(text: str) -> dict | None:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse model response as JSON: %s", e)
        # Fallback: model may have added stray text before/after the JSON,
        # or the JSON got cut off mid-generation. Try to pull out the
        # outermost {...} block and parse that instead of giving up.
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as e2:
                logger.warning("Fallback JSON extraction also failed: %s", e2)
        logger.warning("Raw model output that failed to parse:\n%s", cleaned[:3000])
        return None


def call_gemini(prompt: str) -> str:
    """Primary generator."""
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=GENERATION_CONFIG,
    )
    raw = response.text
    if not raw:
        raise ValueError("Gemini returned an empty response.")
    return raw


def call_groq(prompt: str) -> str:
    """Fallback generator, used automatically whenever Gemini fails."""
    if not groq_client:
        raise RuntimeError("GROQ_API_KEY not configured — no fallback available.")
    completion = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "Return ONLY valid JSON, no markdown, no commentary."},
            {"role": "user", "content": prompt},
        ],
        temperature=GROQ_TEMPERATURE,
        max_tokens=GROQ_MAX_TOKENS,
        response_format={"type": "json_object"},
    )
    raw = completion.choices[0].message.content
    if not raw:
        raise ValueError("Groq returned an empty response.")
    return raw


def generate_with_fallback(prompt: str, req_label: str) -> tuple[str, str]:
    """Try Gemini first; on any failure, automatically fall back to Groq.
    Returns (raw_text, model_used)."""
    try:
        raw = call_gemini(prompt)
        return raw, GEMINI_MODEL
    except Exception as gemini_error:
        logger.warning("[%s] Gemini failed (%s) — falling back to Groq (%s)",
                        req_label, gemini_error, GROQ_MODEL)
        try:
            raw = call_groq(prompt)
            return raw, GROQ_MODEL
        except Exception as groq_error:
            logger.error("[%s] Groq fallback also failed: %s", req_label, groq_error)
            raise HTTPException(
                status_code=503,
                detail=f"AI service unavailable — Gemini failed ({gemini_error}) and Groq fallback also failed ({groq_error}).",
            )

# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="University Comparison API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/static")
def get_static():
    return {
        "famous_unis": FAMOUS_UNIS_PK,
        "popular_comparisons": POPULAR_PK_COMPARISONS,
    }


@app.post("/api/compare")
def compare(req: CompareRequest):
    if not req.uni1.strip():
        raise HTTPException(status_code=422, detail="uni1 is required.")
    if req.uni2 is not None and not req.uni2.strip():
        raise HTTPException(status_code=422, detail="uni2 cannot be empty when provided.")

    req_label = f"{req.uni1}" + (f" vs {req.uni2}" if req.uni2 else "")

    # ── Stage 1: Reddit fetch ────────────────────────────────────────────────
    t0 = time.perf_counter()
    try:
        if req.uni2:
            with ThreadPoolExecutor(max_workers=2) as executor:
                future1 = executor.submit(fetch_reviews_cached, req.uni1.strip())
                future2 = executor.submit(fetch_reviews_cached, req.uni2.strip())
                reviews1 = list(future1.result())
                reviews2 = list(future2.result())
        else:
            reviews1 = list(fetch_reviews_cached(req.uni1.strip()))
            reviews2 = []
    except prawcore_exceptions.PrawcoreException as e:
        logger.error("Reddit API error: %s", e)
        raise HTTPException(status_code=503, detail=f"Reddit is temporarily unavailable: {e}")
    t1 = time.perf_counter()
    logger.info("[%s] Reddit fetch: %.0fms (%d posts)", req_label, (t1 - t0) * 1000, len(reviews1) + len(reviews2))

    # ── Stage 2: Prompt build ────────────────────────────────────────────────
    t2 = time.perf_counter()
    prompt = build_prompt(req.uni1, reviews1, req.uni2, reviews2, req.filters)
    t3 = time.perf_counter()
    logger.info("[%s] Prompt build: %.0fms (%d chars)", req_label, (t3 - t2) * 1000, len(prompt))

    # ── Stage 3: Gemini call, with automatic Groq fallback ──────────────────
    t4 = time.perf_counter()
    raw, model_used = generate_with_fallback(prompt, req_label)
    t5 = time.perf_counter()
    logger.info("[%s] %s call: %.0fms (%d chars out)", req_label, model_used, (t5 - t4) * 1000, len(raw or ""))
    logger.info("[%s] Total: %.0fms", req_label, (t5 - t0) * 1000)

    if not raw:
        raise HTTPException(status_code=502, detail="AI returned an empty response.")

    data = parse_response(raw)
    if not data:
        raise HTTPException(status_code=502, detail="AI returned an unexpected format.")

    data["posts_analyzed"] = data.get("posts_analyzed", len(reviews1) + len(reviews2))
    data["model_used"] = model_used  # lets the frontend show which engine actually answered

    # Attach real Reddit sources ourselves — never let the model generate
    # URLs, since it can hallucinate plausible-looking but fake links.
    seen_urls = set()
    sources = []
    for post in list(reviews1) + list(reviews2):
        if post["url"] not in seen_urls:
            seen_urls.add(post["url"])
            sources.append({
                "title": post["title"],
                "url": post["url"],
                "subreddit": post["subreddit"],
            })
    data["reddit_sources"] = sources

    return data