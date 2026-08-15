import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import google.api_core.exceptions as google_exceptions
import praw
import prawcore.exceptions as prawcore_exceptions
import os
import json
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("university_comparison_bot")

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

GENERATION_CONFIG = genai.types.GenerationConfig(
    max_output_tokens=8192,
    temperature=0.7,
)

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

# ── Reddit ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_reviews(university_name: str, limit: int = 10) -> list[str]:
    subs = ["college", "AskAcademia", "pakistan", "islamabad",
            university_name.replace(" ", "")]
    posts = []
    for sub in subs:
        try:
            for post in reddit.subreddit(sub).search(
                university_name, sort="relevance", limit=limit
            ):
                text = (post.title + " " + (post.selftext or "")).strip()
                if text:
                    posts.append(text)
        except (prawcore_exceptions.PrawcoreException,
                prawcore_exceptions.NotFound,
                prawcore_exceptions.Forbidden) as e:
            logger.warning("Reddit fetch failed for r/%s (%s): %s", sub, university_name, e)
        except Exception as e:
            logger.warning("Unexpected error fetching r/%s (%s): %s", sub, university_name, e)
    return posts[:40]

# ── Gemini ───────────────────────────────────────────────────────────────────

def build_prompt(uni1: str, reviews1: list, uni2: str | None,
                 reviews2: list | None, filters: dict) -> str:
    prefs = ""
    if any(filters.values()):
        prefs = "Student preferences: " + ", ".join(
            f"{k}: {v}" for k, v in filters.items() if v
        )

    r1 = "\n".join(reviews1[:20]) or "No Reddit data found."
    base = f"""
You are an AI university analyst. Analyze the Reddit student discussions below and
return ONLY a valid JSON object — no markdown fences, no extra text.

{prefs}

University 1: {uni1}
Reddit discussions:
{r1}
"""
    if uni2 and reviews2:
        r2 = "\n".join(reviews2[:20]) or "No Reddit data found."
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

# ── Safe helpers ─────────────────────────────────────────────────────────────

def safe_score(value, default: float = 0.0) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return default
    if score != score:
        return default
    return max(0.0, min(10.0, score))

def safe_name(u: dict | None, fallback: str) -> str:
    if not u:
        return fallback
    name = u.get("name")
    return name if name else fallback

# ── Rendering helpers ────────────────────────────────────────────────────────

def score_bar(score) -> str:
    clamped = safe_score(score)
    filled = round(clamped)
    return "🟦" * filled + "⬜" * (10 - filled) + f"  **{clamped:.1f}/10**"

def render_scorecard(unis: list[dict], name_fallbacks: list[str]) -> None:
    categories = [
        ("Overall", "overall_score"),
        ("Academics", "academic_score"),
        ("Student Life", "student_life_score"),
        ("Value / Cost", "value_score"),
        ("Career", "career_score"),
        ("Satisfaction", "satisfaction_score"),
    ]
    if len(unis) == 2:
        name1 = safe_name(unis[0], name_fallbacks[0] if len(name_fallbacks) > 0 else "University 1")
        name2 = safe_name(unis[1], name_fallbacks[1] if len(name_fallbacks) > 1 else "University 2")
        col_headers = ["Category", name1, name2]
        rows = []
        for label, key in categories:
            s1 = safe_score(unis[0].get(key))
            s2 = safe_score(unis[1].get(key))
            rows.append(f"| {label} | {s1:.1f}/10 | {s2:.1f}/10 |")
        table = "| " + " | ".join(col_headers) + " |\n"
        table += "|---|---|---|\n"
        table += "\n".join(rows)
        st.markdown(table)
    elif unis:
        u = unis[0]
        for label, key in categories:
            st.markdown(f"**{label}:** {score_bar(u.get(key))}")
    else:
        st.info("No score data available.")

def render_winners(winners: dict) -> None:
    mapping = {
        "overall": "🏆 Best overall",
        "academics": "📚 Best for academics",
        "student_life": "🎉 Best student life",
        "value": "💰 Best value",
        "career": "💼 Best for careers",
    }
    cols = st.columns(len(mapping))
    for col, (key, label) in zip(cols, mapping.items()):
        winner = winners.get(key) or "—"
        col.markdown(
            f"<div style='background:#FFFFFF;border:1px solid #E5E9F0;border-radius:12px;"
            f"padding:0.7rem;text-align:center;font-size:0.8rem;box-shadow:0 1px 3px rgba(0,0,0,0.04)'>"
            f"<div style='color:#64748B'>{label}</div>"
            f"<div style='font-weight:700;color:#0F172A'>{winner}</div></div>",
            unsafe_allow_html=True,
        )

def render_university_card(u: dict | None, fallback_name: str) -> None:
    if u is None:
        u = {}
    st.markdown(f"### {safe_name(u, fallback_name)}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**👍 What students like**")
        for item in u.get("likes") or []:
            st.markdown(f"- {item}")
        st.markdown("**🎓 Academic experience**")
        st.markdown(u.get("academic_experience") or "—")
        st.markdown("**💼 Career / internships**")
        st.markdown(u.get("career_internships") or "—")
    with col2:
        st.markdown("**👎 Common complaints**")
        for item in u.get("complaints") or []:
            st.markdown(f"- {item}")
        st.markdown("**🏠 Housing / cost**")
        st.markdown(u.get("housing_cost") or "—")
        st.markdown("**🧑‍🤝‍🧑 Student life**")
        st.markdown(u.get("student_life") or "—")
    st.markdown("**⚠️ Things prospective students should know**")
    st.markdown(u.get("things_to_know") or "—")

# ── Static content: Famous Pakistani Universities ───────────────────────────

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

# ── Page config & CSS ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="University Comparison Bot", page_icon="🎓", layout="wide"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background: #F3F6FB; min-height: 100vh; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        background-color: transparent !important;
        max-width: 1400px;
    }

    /* ---- Force readable text everywhere, regardless of browser/system
             dark-mode theme leaking a white default text color onto our
             white cards. This is the fix for the invisible-text bug. ---- */
    .stApp, .stApp p, .stApp li, .stApp span, .stApp label,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4,
    .stCaption, .stTextInput label, .stSelectbox label, .stRadio label,
    .stExpander, .stExpander summary, .stExpander p,
    .stTabs [data-baseweb="tab"] p, .stTabs [data-baseweb="tab-panel"],
    table, th, td,
    .stDataFrame, .stTable {
        color: #0F172A !important;
    }
    /* Muted/secondary text stays readable too */
    .stCaption, .stCaption p { color: #64748B !important; }
    /* Keep text inside colored alert boxes (info/warning/error) as Streamlit
       already sets appropriate contrast for those — don't override. */
    .stAlert p, .stAlert span, .stAlert div { color: inherit !important; }

    /* ---- Top nav pill buttons ---- */
    .topnav-wrap {
        background: #FFFFFF; border-radius: 16px; padding: 0.65rem 1.2rem;
        margin-bottom: 1.5rem; border: 1px solid #E5E9F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        display: flex; align-items: center; justify-content: space-between;
    }
    .topnav-brand {
        font-weight: 800; font-size: 1.05rem; color: #0F172A !important;
        white-space: nowrap;
    }
    /* Nav buttons container — remove all default Streamlit button spacing */
    .nav-pills > div { gap: 0 !important; }
    .nav-pills .stButton { margin: 0 !important; }
    .nav-pills .stButton > button {
        background: transparent !important;
        color: #475569 !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 0.45rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        width: auto !important;
        margin: 0 0.15rem !important;
        box-shadow: none !important;
        transition: background 0.15s ease, color 0.15s ease !important;
    }
    .nav-pills .stButton > button:hover {
        background: #F1F5F9 !important;
        color: #0F172A !important;
        transform: none !important;
        box-shadow: none !important;
    }
    .nav-pills .stButton > button p { color: inherit !important; }
    /* Active pill — injected via a wrapper div with class nav-active */
    .nav-active .stButton > button {
        background: #EAF0FE !important;
        color: #3B5BFA !important;
        border: 1px solid rgba(59,91,250,0.25) !important;
    }
    .nav-active .stButton > button p { color: #3B5BFA !important; }

    /* ---- Generic white card ---- */
    .panel {
        background: #FFFFFF; border: 1px solid #E5E9F0; border-radius: 16px;
        padding: 1.4rem 1.6rem; margin-bottom: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .badge-pill {
        display:inline-block; background:#EAF0FE; color:#475569 !important; border-radius:999px;
        padding:0.35rem 0.9rem; font-size:0.82rem; font-weight:500; margin-bottom:1rem;
    }
    .badge-pill b { color:#3B5BFA !important; }
    .main-title { font-size: 2.4rem; font-weight: 800; color: #0F172A !important; text-align:center; margin-bottom:0.6rem; }
    .main-title .accent { color:#3B5BFA !important; }
    .subtitle { font-size: 1rem; color: #64748B !important; text-align:center; margin-bottom: 1.8rem; }
    .subtitle .reddit { color:#FF4500 !important; font-weight:600; }

    .step-heading { display:flex; align-items:center; gap:0.6rem; margin: 1.1rem 0 0.7rem 0; }
    .step-num {
        width:26px; height:26px; border-radius:8px; background:#3B5BFA; color:white !important;
        display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.85rem;
        flex-shrink:0;
    }
    .step-heading .txt { font-weight:700; font-size:1.05rem; color:#0F172A !important; }
    .step-heading .opt { font-weight:400; color:#94A3B8 !important; font-size:0.9rem; margin-left:0.2rem; }

    .helper-text { color:#94A3B8 !important; font-size:0.8rem; margin: 0.15rem 0 0.9rem 0; }

    .stTextInput > div > div > input {
        background: #FFFFFF; border-radius: 10px;
        border: 1.5px solid #E2E8F0 !important;
        padding: 10px 14px; color: #0F172A !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #3B5BFA !important; outline: none !important;
        box-shadow: 0 0 0 3px rgba(59,91,250,0.12) !important;
    }
    .stSelectbox > div > div { border-radius: 10px !important; border: 1.5px solid #E2E8F0 !important; }

    .stButton > button {
        background: #3B5BFA !important;
        color: white !important; border-radius: 999px !important;
        padding: 0.9rem 2rem !important; font-weight: 700 !important;
        font-size: 1rem !important; border: none !important;
        width: 100% !important; margin-top: 0.8rem !important;
        box-shadow: 0 8px 20px rgba(59,91,250,0.30) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 10px 26px rgba(59,91,250,0.42) !important;
    }
    .stButton > button p { color: white !important; }

    .footnote { text-align:center; color:#94A3B8 !important; font-size:0.82rem; margin-top:0.9rem; }

    .why-item { display:flex; gap:0.7rem; align-items:flex-start; margin-bottom:1rem; }
    .why-check {
        width:20px; height:20px; border-radius:999px; background:#DCFCE7; color:#16A34A !important;
        display:flex; align-items:center; justify-content:center; font-size:0.75rem; flex-shrink:0; margin-top:0.1rem;
    }
    .why-item .title { font-weight:700; color:#0F172A !important; font-size:0.92rem; }
    .why-item .desc { color:#94A3B8 !important; font-size:0.82rem; }
    .section-title { font-weight:700; color:#3B5BFA !important; font-size:0.95rem; margin-bottom:0.9rem; }
    .section-title.dark { color:#0F172A !important; }

    .feat-item { display:flex; gap:0.7rem; align-items:flex-start; margin-bottom:1rem; }
    .feat-icon {
        width:34px; height:34px; border-radius:9px; background:#EAF0FE; color:#3B5BFA !important;
        display:flex; align-items:center; justify-content:center; font-size:1rem; flex-shrink:0;
    }
    .feat-item .title { font-weight:700; color:#0F172A !important; font-size:0.9rem; }
    .feat-item .desc { color:#94A3B8 !important; font-size:0.8rem; }

    .pop-row {
        display:flex; align-items:center; justify-content:space-between;
        padding:0.55rem 0; border-bottom:1px solid #F1F5F9; font-size:0.88rem;
    }
    .pop-row:last-child { border-bottom:none; }
    .pop-row .rank { color:#94A3B8 !important; font-weight:600; margin-right:0.5rem; }
    .pop-row .name { color:#0F172A !important; font-weight:600; }
    .pop-row .chev { color:#CBD5E1 !important; }

    .tip-box { background:#EAF0FE; border-radius:12px; padding:1rem 1.1rem; margin-top:1rem; }
    .tip-box .title { font-weight:700; color:#0F172A !important; font-size:0.88rem; margin-bottom:0.2rem; }
    .tip-box .desc { color:#475569 !important; font-size:0.8rem; }

    .uni-list-item {
        padding: 0.5rem 0.7rem; border-radius: 8px; margin-bottom: 0.4rem;
        background: #F8FAFC; color:#0F172A !important; font-size: 0.92rem;
        border: 1px solid #F1F5F9;
    }
    .uni-list-item b { color: #3B5BFA !important; }

    .disclaimer {
        background: #F8FAFC; border-radius: 10px;
        padding: 0.8rem 1rem; font-size: 0.8rem; color: #64748B !important;
        margin-top: 1.5rem; border-left: 3px solid #3B5BFA;
    }
    .footer {
        text-align: center; margin-top: 2.5rem; padding-top: 1.2rem;
        border-top: 1px solid #E5E9F0;
        font-size: 0.88rem; color: #64748B !important;
    }
    /* mode toggle radio (inside home panel) stays horizontal */
    div[data-testid="stRadio"] > div { flex-direction: row; gap: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state / navigation ───────────────────────────────────────────────

NAV_ITEMS = ["🏠 Home", "ℹ️ About Us", "❓ FAQ", "🎓 Famous Universities (Pak)"]

if "nav_page" not in st.session_state:
    st.session_state.nav_page = "🏠 Home"

# Top nav bar: brand on left, pill buttons on right
nav_left, nav_right = st.columns([1, 3])
with nav_left:
    st.markdown(
        '<div style="background:#FFFFFF;border:1px solid #E5E9F0;border-radius:16px;'
        'padding:0.65rem 1.2rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        '<span class="topnav-brand">🎓 UniCompare</span></div>',
        unsafe_allow_html=True,
    )
with nav_right:
    st.markdown(
        '<div style="background:#FFFFFF;border:1px solid #E5E9F0;border-radius:16px;'
        'padding:0.4rem 0.8rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">',
        unsafe_allow_html=True,
    )
    pill_cols = st.columns(len(NAV_ITEMS))
    for col, item in zip(pill_cols, NAV_ITEMS):
        is_active = st.session_state.nav_page == item
        wrapper_class = "nav-active nav-pills" if is_active else "nav-pills"
        col.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
        if col.button(item, key=f"nav_{item}"):
            st.session_state.nav_page = item
            st.rerun()
        col.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

nav_page = st.session_state.nav_page

# ── 3-column layout (sidebars persist across pages) ─────────────────────────

left_col, main_col, right_col = st.columns([1, 2.3, 1], gap="medium")

with left_col:
    st.markdown(
        """
        <div class="panel">
            <div class="section-title dark">Why use this?</div>
            <div class="why-item">
                <div class="why-check">✓</div>
                <div><div class="title">Real student reviews</div><div class="desc">from Reddit (live)</div></div>
            </div>
            <div class="why-item">
                <div class="why-check">✓</div>
                <div><div class="title">Compare universities</div><div class="desc">side-by-side</div></div>
            </div>
            <div class="why-item">
                <div class="why-check">✓</div>
                <div><div class="title">Make better, informed</div><div class="desc">decisions</div></div>
            </div>
            <div class="why-item">
                <div class="why-check">✓</div>
                <div><div class="title">100% Free to use</div><div class="desc">No sign-up required</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right_col:
    pop_rows_html = "".join(
        f'<div class="pop-row"><span><span class="rank">#{i+1}</span>'
        f'<span class="name">{comp}</span></span><span class="chev">›</span></div>'
        for i, comp in enumerate(POPULAR_PK_COMPARISONS)
    )
    st.markdown(
        f"""
        <div class="panel">
            <div class="section-title dark">⭐ What you'll get</div>
            <div class="feat-item">
                <div class="feat-icon">💬</div>
                <div><div class="title">Real student opinions</div><div class="desc">from Reddit communities</div></div>
            </div>
            <div class="feat-item">
                <div class="feat-icon">⚖️</div>
                <div><div class="title">Side-by-side comparison</div><div class="desc">of key aspects</div></div>
            </div>
            <div class="feat-item">
                <div class="feat-icon">📈</div>
                <div><div class="title">Pros &amp; Cons analysis</div><div class="desc">for each university</div></div>
            </div>
            <div class="feat-item">
                <div class="feat-icon">💡</div>
                <div><div class="title">AI-powered summary</div><div class="desc">with key takeaways</div></div>
            </div>
        </div>
        <div class="panel">
            <div class="section-title">🎓 Popular Pakistani Uni Comparisons</div>
            {pop_rows_html}
            <div class="tip-box">
                <div class="title">💡 Tip</div>
                <div class="desc">Be specific with university names for more accurate results.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Main center content — depends on nav_page ────────────────────────────────

with main_col:

    if nav_page == "🏠 Home":
        st.markdown('<div class="panel">', unsafe_allow_html=True)

        st.markdown(
            """
            <div style="text-align:center;">
                <span class="badge-pill">⚡ Powered by <b>live Reddit</b> student reviews</span>
                <div class="main-title">🎓 University <span class="accent">Comparison Bot</span></div>
                <div class="subtitle">Compare universities based on real student experiences, reviews,
                    and insights from <span class="reddit">Reddit</span>.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mode = st.radio(
            "Analysis mode",
            ["Single University Analysis", "Compare Two Universities"],
            label_visibility="collapsed",
            horizontal=True,
        )

        st.markdown(
            '<div class="step-heading"><div class="step-num">1</div>'
            '<div class="txt">Enter University Name(s)</div></div>',
            unsafe_allow_html=True,
        )

        uni1 = st.text_input(
            "uni1", placeholder="Enter the first university name",
            label_visibility="collapsed", key="uni1"
        )
        st.markdown('<div class="helper-text">Example: Harvard University</div>', unsafe_allow_html=True)

        uni2 = None
        if mode == "Compare Two Universities":
            uni2 = st.text_input(
                "uni2", placeholder="Enter the second university name",
                label_visibility="collapsed", key="uni2"
            )
            st.markdown('<div class="helper-text">Example: Stanford University</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="step-heading"><div class="step-num">2</div>'
            '<div class="txt">Comparison Options</div><div class="opt">(Optional)</div></div>',
            unsafe_allow_html=True,
        )

        with st.expander("⚙️ Personalise your results"):
            pref_col1, pref_col2 = st.columns(2)
            with pref_col1:
                program = st.text_input("Intended program / degree", placeholder="e.g. Computer Science")
                budget = st.text_input("Budget / tuition range", placeholder="e.g. Under $20,000/yr")
                career_goal = st.text_input("Career goal", placeholder="e.g. Software Engineer")
            with pref_col2:
                study_level = st.selectbox("Study level", ["", "Undergraduate", "Graduate", "PhD"])
                campus_priority = st.selectbox("Campus life priority", ["", "Low", "Medium", "High"])
                intl_support = st.selectbox("International student support", ["", "Not important", "Important", "Very important"])

        filters = {
            "program": program,
            "budget": budget,
            "career_goal": career_goal,
            "study_level": study_level,
            "campus_priority": campus_priority,
            "international_support": intl_support,
        }

        btn_label = "✨ Compare Universities" if mode == "Compare Two Universities" else "✨ Get Insights"
        run_clicked = st.button(btn_label)

        st.markdown(
            '<div class="footnote">🛡️ We fetch live data from Reddit. Results may vary.</div>',
            unsafe_allow_html=True,
        )

        st.markdown('</div>', unsafe_allow_html=True)  # close .panel

        if run_clicked:
            if not uni1:
                st.warning("Please enter at least one university name.")
                st.stop()
            if mode == "Compare Two Universities" and not uni2:
                st.warning("Please enter the second university name.")
                st.stop()

            steps = [
                "🔎 Finding university information…",
                "💬 Collecting student discussions…",
                "🧠 Analysing student sentiment…",
                "⚖️ Comparing universities…" if mode == "Compare Two Universities" else "📊 Preparing insights…",
                "✨ Almost ready…",
            ]
            progress = st.progress(0)
            status = st.empty()

            reviews1: list[str] = []
            reviews2: list[str] = []
            data: dict | None = None

            try:
                status.info(steps[0])
                progress.progress(10)
                reviews1 = fetch_reviews(uni1)

                status.info(steps[1])
                progress.progress(30)
                reviews2 = fetch_reviews(uni2) if uni2 else []

                status.info(steps[2])
                progress.progress(55)
                prompt = build_prompt(uni1, reviews1, uni2, reviews2, filters)

                status.info(steps[3])
                progress.progress(75)
                try:
                    response = model.generate_content(prompt, generation_config=GENERATION_CONFIG)
                    raw = response.text
                except google_exceptions.GoogleAPICallError as e:
                    logger.error("Gemini API call failed: %s", e)
                    progress.empty()
                    status.empty()
                    st.error(f"⚠️ The AI service returned an error: {e}. Please try again shortly.")
                    st.stop()
                except ValueError as e:
                    logger.error("Gemini response had no usable text: %s", e)
                    progress.empty()
                    status.empty()
                    st.error(
                        "⚠️ The AI didn't return a usable response (it may have been "
                        "blocked or cut off). Please try again."
                    )
                    st.stop()

                status.info(steps[4])
                progress.progress(95)
                data = parse_response(raw)

                progress.progress(100)
                status.empty()
                progress.empty()

            except (prawcore_exceptions.PrawcoreException,) as e:
                progress.empty()
                status.empty()
                logger.error("Reddit API error: %s", e)
                st.error(f"⚠️ Couldn't reach Reddit right now: {e}. Please try again shortly.")
                st.stop()
            except Exception as e:
                progress.empty()
                status.empty()
                logger.exception("Unexpected error during analysis pipeline")
                st.error(
                    f"⚠️ Something went wrong ({type(e).__name__}): {e}\n\n"
                    "Please check your API keys and try again. "
                    "If the university wasn't found, try a more common name."
                )
                st.stop()

            if not data:
                st.error(
                    "The AI returned an unexpected format. Please try again. "
                    "If this persists, the university name may be too ambiguous."
                )
                st.stop()

            unis = data.get("universities") or []
            posts_count = data.get("posts_analyzed", len(reviews1) + len(reviews2))
            data_date = data.get("data_date", datetime.now().strftime("%Y-%m-%d"))
            confidence = data.get("confidence", "medium")

            st.markdown('<div class="panel">', unsafe_allow_html=True)

            if mode == "Compare Two Universities" and len(unis) == 2:
                name1 = safe_name(unis[0], uni1)
                name2 = safe_name(unis[1], uni2 or "University 2")
                st.markdown(f"## 🏆 {name1} vs {name2}")

                winners = data.get("winners") or {}
                if winners:
                    st.markdown("#### Overall winners")
                    render_winners(winners)
                    st.markdown("")

                st.markdown("#### 📊 Scorecard")
                st.caption("⚠️ Scores are AI-generated estimates based on Reddit discussions, not official rankings.")
                render_scorecard(unis, [uni1, uni2 or "University 2"])

                if data.get("comparison_summary"):
                    st.markdown("#### 🤖 AI Comparison Summary")
                    st.markdown(data["comparison_summary"])

                st.divider()
                st.markdown("#### 💬 What Students Say")
                tab1, tab2 = st.tabs([name1, name2])
                with tab1:
                    render_university_card(unis[0], uni1)
                with tab2:
                    render_university_card(unis[1], uni2 or "University 2")

            elif unis:
                u = unis[0]
                name = safe_name(u, uni1)
                st.markdown(f"## 📋 {name} — Analysis")
                st.caption("⚠️ Scores are AI-generated estimates based on Reddit discussions, not official rankings.")
                render_scorecard([u], [uni1])
                st.divider()
                st.markdown("#### 💬 What Students Say")
                render_university_card(u, uni1)

            else:
                st.warning("No university data was returned. Please try again with a different name.")

            if data.get("recommendation"):
                st.divider()
                st.markdown("#### 🎯 AI Recommendation")
                st.info(data["recommendation"])

            st.divider()
            st.markdown("#### 🔗 Sources & Transparency")
            st.markdown(
                f"- **Platform:** Reddit  \n"
                f"- **Discussions analysed:** ~{posts_count}  \n"
                f"- **Data collected:** {data_date}  \n"
                f"- **AI confidence:** {confidence}  \n"
                f"- Reddit opinions are anecdotal and may not represent all students."
            )

            st.markdown(
                '<div class="disclaimer">⚠️ <strong>Disclaimer:</strong> AI-generated insights are intended '
                "to help with research and comparison. Student reviews are subjective and may not represent "
                "the overall university experience. Always verify tuition, admission requirements, rankings, "
                "and official policies through the university's official website.</div>",
                unsafe_allow_html=True,
            )

            st.markdown('</div>', unsafe_allow_html=True)

    elif nav_page == "ℹ️ About Us":
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("## ℹ️ About Us")
        st.markdown(
            "**University Comparison Bot** helps students research and compare universities "
            "using real, live student discussions pulled from Reddit, analysed by AI to surface "
            "academics, student life, value, and career outcomes side-by-side."
        )
        st.markdown(
            "- Built to make university research faster and less overwhelming.\n"
            "- Combines live Reddit sentiment with an AI summary — not an official ranking.\n"
            "- 100% free, no sign-up required."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    elif nav_page == "❓ FAQ":
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("## ❓ Frequently Asked Questions")

        faqs = [
            ("Where does the data come from?",
             "Live discussions and reviews pulled from Reddit, analysed with Gemini AI."),
            ("Are the scores official rankings?",
             "No — scores are AI-generated estimates based on Reddit sentiment, not official rankings."),
            ("Is it free to use?",
             "Yes, 100% free and no sign-up is required."),
            ("Can I compare more than two universities?",
             "Not yet — comparing more than two universities at once is coming soon."),
            ("How accurate are the results?",
             "Accuracy depends on how much relevant Reddit discussion exists for a university, "
             "so results for less-discussed schools may be less reliable."),
        ]
        for q, a in faqs:
            with st.expander(q):
                st.markdown(a)
        st.markdown('</div>', unsafe_allow_html=True)

    elif nav_page == "🎓 Famous Universities (Pak)":
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("## 🎓 Famous Universities in Pakistan")
        st.caption(
            "⚠️ These lists reflect commonly cited reputation by field, not an official or "
            "live ranking. Always verify current standing on each university's official site."
        )
        for category, unis_list in FAMOUS_UNIS_PK.items():
            st.markdown(f"#### {category}")
            for i, uni_name in enumerate(unis_list, start=1):
                st.markdown(
                    f'<div class="uni-list-item"><b>{i}.</b> {uni_name}</div>',
                    unsafe_allow_html=True,
                )
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="footer">Made with ❤️ by <strong>Hasnain Asif Khan</strong>'
    "<br><small>⚙️ Gemini API · Streamlit · Reddit API</small></div>",
    unsafe_allow_html=True,
)