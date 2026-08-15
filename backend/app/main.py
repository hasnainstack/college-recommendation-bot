from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
import praw
import prawcore.exceptions as prawcore_exceptions
import os
import json
import re
import logging
from datetime import datetime
from functools import lru_cache
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("university_comparison_bot")

# ── Gemini setup ─────────────────────────────────────────────────────────────

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise RuntimeError("GOOGLE_API_KEY not found in environment variables.")

client = genai.Client(api_key=api_key)

GEMINI_MODEL = "gemini-2.0-flash"

GENERATION_CONFIG = types.GenerateContentConfig(
    max_output_tokens=2048,
    temperature=0.3,
)

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

def _fetch_sub(sub: str, university_name: str, limit: int) -> list[str]:
    posts = []
    try:
        for post in reddit.subreddit(sub).search(university_name, sort="relevance", limit=limit):
            text = (post.title + " " + (post.selftext or "")).strip()
            if text:
                posts.append(text)
    except Exception as e:
        logger.warning("Reddit fetch failed for r/%s (%s): %s", sub, university_name, e)
    return posts


@lru_cache(maxsize=128)
def fetch_reviews_cached(university_name: str, limit: int = 5) -> tuple[str, ...]:
    subs = ["pakistan", "islamabad", "college", university_name.replace(" ", "")]
    posts: list[str] = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(_fetch_sub, sub, university_name, limit): sub for sub in subs}
        for future in as_completed(futures):
            posts.extend(future.result())
    return tuple(posts[:20])


def build_prompt(uni1: str, reviews1: list[str], uni2: Optional[str],
                 reviews2: list[str], filters: Filters) -> str:
    prefs = ""
    filter_dict = filters.model_dump()
    if any(filter_dict.values()):
        prefs = "Student preferences: " + ", ".join(
            f"{k}: {v}" for k, v in filter_dict.items() if v
        )

    r1 = "\n".join(reviews1[:10]) or "No Reddit data found."
    base = f"""
You are an AI university analyst. Analyze the Reddit student discussions below and
return ONLY a valid JSON object — no markdown fences, no extra text.

{prefs}

University 1: {uni1}
Reddit discussions:
{r1}
"""
    if uni2 and reviews2:
        r2 = "\n".join(reviews2[:10]) or "No Reddit data found."
        base += f"""
University 2: {uni2}
Reddit discussions:
{r2}

Return this exact JSON structure:
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
}}
"""
    else:
        base += f"""
Return this exact JSON structure:
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
}}
"""
    return base


def parse_response(text: str) -> dict | None:
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse Gemini response as JSON: %s", e)
        return None

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
async def compare(req: CompareRequest):
    if not req.uni1.strip():
        raise HTTPException(status_code=422, detail="uni1 is required.")
    if req.uni2 is not None and not req.uni2.strip():
        raise HTTPException(status_code=422, detail="uni2 cannot be empty when provided.")

    try:
        with ThreadPoolExecutor(max_workers=2) as ex:
            f1 = ex.submit(fetch_reviews_cached, req.uni1.strip())
            f2 = ex.submit(fetch_reviews_cached, req.uni2.strip()) if req.uni2 else None
            reviews1 = list(f1.result())
            reviews2 = list(f2.result()) if f2 else []
    except prawcore_exceptions.PrawcoreException as e:
        logger.error("Reddit API error: %s", e)
        raise HTTPException(status_code=503, detail=f"Reddit is temporarily unavailable: {e}")

    prompt = build_prompt(req.uni1, reviews1, req.uni2, reviews2, req.filters)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=GENERATION_CONFIG,
        )
        raw = response.text
    except genai.errors.APIError as e:
        logger.error("Gemini API error: %s", e)
        raise HTTPException(status_code=503, detail=f"AI service error: {e}")
    except ValueError as e:
        logger.error("Gemini response unusable: %s", e)
        raise HTTPException(status_code=503, detail="AI returned no usable response.")

    if not raw:
        raise HTTPException(status_code=502, detail="AI returned an empty response.")

    data = parse_response(raw)
    if not data:
        raise HTTPException(status_code=502, detail="AI returned an unexpected format.")

    data["posts_analyzed"] = data.get("posts_analyzed", len(reviews1) + len(reviews2))
    return data