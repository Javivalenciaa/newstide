import os
import hashlib
import re
import time
import requests
from datetime import datetime, timezone, timedelta
from serpapi import GoogleSearch
from openai import OpenAI
import anthropic
from supabase import create_client

# ── CONFIG ────────────────────────────────────────────────────────────────────
SERPAPI_KEY          = os.environ["SERPAPI_KEY"]
OPENAI_API_KEY       = os.environ["OPENAI_API_KEY"]
ANTHROPIC_API_KEY    = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
UNSPLASH_ACCESS_KEY  = os.environ["UNSPLASH_ACCESS_KEY"]

ARTICLES_PER_RUN   = 3
MODEL_GENERATE     = "claude-sonnet-4-5"
MODEL_FAST         = "gpt-4o-mini"
MODEL_HUMANIZE     = "gpt-4o"

# ── SAFETY LIMITS ─────────────────────────────────────────────────────────────
MAX_CLAUDE_CALLS_PER_RUN   = 12
MAX_CLAUDE_TOKENS_PER_RUN  = 80_000
MAX_POOL_EXPANSIONS        = 4

_claude_calls_this_run   = 0
_claude_tokens_this_run  = 0

# ── CONTENT QUALITY LIMITS ────────────────────────────────────────────────────
MIN_READING_TIME = 5
MIN_WORD_COUNT   = MIN_READING_TIME * 200  # 1000 words
MIN_H2_SECTIONS  = 3

# ── TITLE LENGTH CONSTANTS ───────────────────────────────────────────────────
TITLE_MAX_CHARS  = 60
TITLE_SOFT_MIN   = 45
TITLE_SOFT_MAX   = 58

openai_client   = OpenAI(api_key=OPENAI_API_KEY)
claude_client   = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

GRADIENTS = [
    "linear-gradient(135deg,#0d2a1a,#0d1a0a)",
    "linear-gradient(135deg,#1a2e0d,#0d2e1a)",
    "linear-gradient(135deg,#0a2e0d,#1a2a0d)",
    "linear-gradient(135deg,#0d2e0a,#0a1a0d)",
    "linear-gradient(135deg,#1a2e15,#0d2a0d)",
    "linear-gradient(135deg,#0d1a0a,#1a2e10)",
]

# Finance-specific categories
FIN_CATEGORIES = [
    "Saving Money",
    "Budgeting",
    "Investing",
    "Debt",
    "Credit",
    "Side Hustles",
]

FIN_CAT_KEYWORDS = {
    "save": "Saving Money",
    "saving": "Saving Money",
    "groceries": "Saving Money",
    "rent": "Saving Money",
    "cut": "Saving Money",
    "reduce": "Saving Money",
    "budget": "Budgeting",
    "budgeting": "Budgeting",
    "track": "Budgeting",
    "spending": "Budgeting",
    "invest": "Investing",
    "investing": "Investing",
    "stock": "Investing",
    "etf": "Investing",
    "401k": "Investing",
    "roth": "Investing",
    "ira": "Investing",
    "portfolio": "Investing",
    "index fund": "Investing",
    "high yield": "Investing",
    "cd ": "Investing",
    "debt": "Debt",
    "loan": "Debt",
    "student loan": "Debt",
    "mortgage": "Debt",
    "payoff": "Debt",
    "credit card": "Credit",
    "credit score": "Credit",
    "credit": "Credit",
    "cashback": "Credit",
    "side hustle": "Side Hustles",
    "make money": "Side Hustles",
    "earn": "Side Hustles",
    "income": "Side Hustles",
    "freelance": "Side Hustles",
    "passive income": "Side Hustles",
}

AUTHORS = [
    "Ana Martínez", "Carlos Ruiz", "María López",
    "Pedro Sánchez", "Sofía Jiménez", "Luis Torres"
]

# ── INDEXNOW ──────────────────────────────────────────────────────────────────
INDEXNOW_KEY      = "964bf589528b466cace60749e05cfcb6"
INDEXNOW_HOST     = "www.newstide.news"
INDEXNOW_KEY_LOC  = f"https://{INDEXNOW_HOST}/{INDEXNOW_KEY}.txt"

def ping_indexnow(urls: list) -> None:
    if not urls:
        return
    try:
        resp = requests.post(
            "https://api.indexnow.org/IndexNow",
            json={
                "host": INDEXNOW_HOST,
                "key": INDEXNOW_KEY,
                "keyLocation": INDEXNOW_KEY_LOC,
                "urlList": urls,
            },
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=10,
        )
        print(f"  🔍 IndexNow: {resp.status_code} — pinged {len(urls)} URL(s)")
    except Exception as e:
        print(f"  ⚠️  IndexNow ping failed (non-critical): {e}")

# ── HELPERS ───────────────────────────────────────────────────────────────────
def smart_trim(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= limit:
        return text
    cut = text[:limit + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.strip(" -:;,.")

def normalize_excerpt(text: str, min_len: int = 120, max_len: int = 155) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    text = text.strip(' "\'')
    if len(text) <= max_len:
        return text
    cut = text[:max_len + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.strip(" -:;,.") + "."

def slugify_en(text):
    text = smart_trim(text, 60).lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text.strip())
    return text[:60].strip("-")

def md5(text):
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def detect_fin_category(keyword: str) -> str:
    kw = keyword.lower()
    for key, cat in FIN_CAT_KEYWORDS.items():
        if key in kw:
            return cat
    return "Saving Money"

def reading_time(text):
    return max(MIN_READING_TIME, round(len(text.split()) / 200))

def already_published_hash(keyword: str) -> bool:
    res = supabase_client.table("finance_articles").select("id").eq("keyword_hash", md5(keyword)).execute()
    return len(res.data) > 0

def normalize_year(text: str) -> str:
    return re.sub(r'\b(2023|2024|2025)\b', '2026', text)

def strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```(?:markdown|md)?\s*\n', '', text)
    text = re.sub(r'\n```\s*$', '', text)
    return text.strip()

def is_truncated(content_en: str, content_ref: str) -> bool:
    stripped = content_en.strip()
    if not stripped:
        return True
    if stripped[0].islower():
        return True
    words_en  = len(stripped.split())
    words_ref = len(content_ref.split())
    if words_ref > 0 and words_en < words_ref * 0.60:
        return True
    return False

# ── COST GUARD ────────────────────────────────────────────────────────────────
class CostLimitExceeded(Exception):
    pass

def _check_claude_budget(output_tokens: int = 0) -> None:
    global _claude_calls_this_run, _claude_tokens_this_run
    if _claude_calls_this_run >= MAX_CLAUDE_CALLS_PER_RUN:
        raise CostLimitExceeded(
            f"🛑 COST LIMIT: reached {MAX_CLAUDE_CALLS_PER_RUN} Claude calls this run — aborting."
        )
    if _claude_tokens_this_run + output_tokens > MAX_CLAUDE_TOKENS_PER_RUN:
        raise CostLimitExceeded(
            f"🛑 COST LIMIT: projected output tokens ({_claude_tokens_this_run + output_tokens:,}) "
            f"would exceed {MAX_CLAUDE_TOKENS_PER_RUN:,} — aborting."
        )

def _register_claude_call(output_tokens: int) -> None:
    global _claude_calls_this_run, _claude_tokens_this_run
    _claude_calls_this_run  += 1
    _claude_tokens_this_run += output_tokens
    print(
        f"  📊 Claude usage this run: {_claude_calls_this_run}/{MAX_CLAUDE_CALLS_PER_RUN} calls, "
        f"{_claude_tokens_this_run:,}/{MAX_CLAUDE_TOKENS_PER_RUN:,} output tokens"
    )

# ── CONTENT VALIDATION ────────────────────────────────────────────────────────
def validate_article_content(content: str, label: str = "article") -> bool:
    words   = len(content.split())
    h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
    ok = True
    if words < MIN_WORD_COUNT:
        print(f"  ❌ VALIDATION FAIL [{label}]: {words} words < {MIN_WORD_COUNT} minimum")
        ok = False
    if h2_count < MIN_H2_SECTIONS:
        print(f"  ❌ VALIDATION FAIL [{label}]: only {h2_count} H2 sections (need >= {MIN_H2_SECTIONS})")
        ok = False
    stripped = content.strip()
    if not stripped.startswith("#") and len(stripped) > 0 and stripped[0].islower():
        print(f"  ❌ VALIDATION FAIL [{label}]: content starts mid-sentence (truncation detected)")
        ok = False
    if ok:
        print(f"  ✅ VALIDATION OK [{label}]: {words} words, {h2_count} H2 sections")
    return ok

# ── LOAD RECENT FINANCE ARTICLES ──────────────────────────────────────────────
def get_recent_articles() -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    try:
        res = supabase_client.table("finance_articles") \
            .select("title_en, keyword, category, excerpt_en") \
            .gte("published_at", since) \
            .order("published_at", desc=True) \
            .limit(60) \
            .execute()
        return res.data or []
    except Exception as e:
        print(f"  ⚠️  Error reading Supabase finance_articles: {e}")
        return []

def format_recent_context(articles: list[dict]) -> str:
    if not articles:
        return "No recent articles yet."
    lines = [f"- [{r['category']}] {r['title_en']}" for r in articles]
    return "\n".join(lines)

# ── SOURCE 1: SERPAPI FINANCE NEWS ────────────────────────────────────────────
def fetch_serpapi_news() -> list[str]:
    queries = [
        "how to save money on groceries tips 2026",
        "best budgeting apps Americans 2026",
        "personal finance tips US 2026",
        "high yield savings account rates 2026",
        "how to pay off debt faster 2026",
    ]
    results = []
    for q in queries:
        try:
            params = {
                "q": q, "tbm": "nws",
                "hl": "en", "gl": "us",
                "api_key": SERPAPI_KEY, "num": 6
            }
            data = GoogleSearch(params).get_dict()
            for r in data.get("news_results", data.get("organic_results", []))[:4]:
                title   = r.get("title", "")
                snippet = r.get("snippet", "")
                if title and len(title) > 20:
                    results.append(f"{title} — {snippet[:100]}" if snippet else title)
        except Exception as e:
            print(f"  SerpAPI error ({q[:30]}): {e}")
        time.sleep(0.8)
    return results

# ── SOURCE 2: SERPAPI FINANCE TRENDS ──────────────────────────────────────────
def fetch_serpapi_trends() -> list[str]:
    queries = [
        "best cashback credit cards USA 2026",
        "AI investing apps beginners 2026",
        "side hustles make money online 2026",
        "how to lower car insurance bill",
        "best index funds beginners 2026",
    ]
    results = []
    for q in queries:
        try:
            params = {
                "q": q, "location": "United States",
                "hl": "en", "gl": "us",
                "api_key": SERPAPI_KEY, "num": 5
            }
            data = GoogleSearch(params).get_dict()
            for r in data.get("organic_results", [])[:3]:
                title = r.get("title", "")
                if title and len(title) > 20:
                    results.append(title)
        except Exception as e:
            print(f"  SerpAPI trends error: {e}")
        time.sleep(0.8)
    return results

# ── SOURCE 3: FINANCE SEARCH INTENT QUERIES ───────────────────────────────────
def fetch_finance_search_intents() -> list[str]:
    queries = [
        "best apps save money automatically 2026",
        "how much emergency fund should I have",
        "Roth IRA vs 401k which is better 2026",
    ]
    results = []
    for q in queries:
        try:
            params = {
                "q": q, "tbm": "nws",
                "hl": "en", "gl": "us",
                "api_key": SERPAPI_KEY, "num": 5
            }
            data = GoogleSearch(params).get_dict()
            for r in data.get("news_results", data.get("organic_results", []))[:4]:
                title   = r.get("title", "")
                snippet = r.get("snippet", "")
                if title and len(title) > 20:
                    results.append(f"{title} — {snippet[:120]}" if snippet else title)
        except Exception as e:
            print(f"  SerpAPI finance intent error ({q[:30]}): {e}")
        time.sleep(0.8)
    return results

# ── SOURCE 4: NICHE FINANCE TOPIC GENERATOR ───────────────────────────────────
def generate_niche_topics(recent_articles: list[dict], n: int = 15) -> list[str]:
    recent_titles = "\n".join(f"- {a['title_en']}" for a in recent_articles[:30])
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Today is {today}. You are editor-in-chief of NewsTide Finance, a personal finance media for everyday Americans.

Already published (DO NOT repeat or use similar angle):
{recent_titles if recent_titles else "None yet."}

Generate exactly {n} highly specific article ideas on personal finance (USA audience), optimized for HIGH Google Search volume — real search queries people type.

RULES:
1. NEVER generate opinion pieces, lifestyle essays, or "how I saved X" personal stories.
2. Every idea must answer a REAL search query with clear intent, e.g.:
   - "how to save money on groceries without coupons"
   - "best budgeting apps for couples 2026"
   - "how to raise credit score 100 points fast"
   - "best cashback apps USA 2026"
   - "high yield savings account vs CD which is better"
   - "how to make money investing with AI apps"
   - "how to lower car insurance in [state]"
   - "how to build emergency fund when broke"
3. Distribute across: Saving Money (4), Budgeting (3), Investing (4), Debt/Credit (2), Side Hustles (2)
4. Titles must be searchable, action-oriented, specific — NOT vague or clickbait-only
5. Include numbers, year, or comparison when it makes the title more useful
6. NO: "The secret to...", "You won't believe...", "Why I switched to..."

Format: one idea per line, no numbering, no explanation. Just the search-intent title."""

    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.90,
            max_tokens=800,
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        print(f"  🧠 GPT generated {len(lines)} finance niche ideas")
        return lines[:n]
    except Exception as e:
        print(f"  ⚠️  Error generating finance niches: {e}")
        return []

# ── SOURCE 5: FALLBACK FINANCE TOPICS ─────────────────────────────────────────
def get_fallback_topics() -> list[str]:
    today_year = "2026"
    return [
        f"How to Save Money on Groceries Without Coupons ({today_year})",
        f"Best Budgeting Apps for Couples {today_year}: Ranked and Tested",
        f"How to Raise Your Credit Score 100 Points in 90 Days",
        f"High Yield Savings Account vs CD: Which Wins in {today_year}",
        f"Best Cashback Apps USA {today_year}: Up to 15% Back on Everyday Spending",
        f"How to Invest With AI Apps as a Complete Beginner",
        f"How to Lower Your Car Insurance Bill by $500/Year",
        f"How to Build a $1,000 Emergency Fund in 60 Days",
        f"Roth IRA vs 401k: The Decision That Saves You Thousands",
        f"How to Pay Off $10,000 in Credit Card Debt Fast",
        f"Best Index Funds for Beginners {today_year}: 5 Picks Under $100",
        f"How to Make $500/Month in Passive Income with Dividend Stocks",
        f"Best Side Hustles That Actually Pay Well in {today_year}",
        f"How to Negotiate a Lower Rent With Your Landlord",
        f"How to Stop Living Paycheck to Paycheck: A 6-Step Plan",
    ]

# ── DEDUPLICATION ENGINE ──────────────────────────────────────────────────────
def is_duplicate_topic(candidate: str, recent_articles: list[dict], published_this_run: list[str]) -> bool:
    all_existing = [a["title_en"] for a in recent_articles] + published_this_run
    if not all_existing:
        return False
    existing_str = "\n".join(f"- {t}" for t in all_existing[:40])
    prompt = f"""Candidate article: "{candidate}"

Existing articles:
{existing_str}

Does the candidate cover the SAME specific topic or a very similar angle to any existing article?
Criterion: only a duplicate if it covers the same main topic (same financial goal + same audience). Different tools, different angles, or different sub-topics are NOT duplicates.

Reply ONLY: YES or NO"""
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5,
        )
        answer = resp.choices[0].message.content.strip().upper()
        return answer.startswith("YES")
    except Exception as e:
        print(f"  ⚠️  Error dedup check: {e}")
        return False

def mutate_topic(original: str, recent_articles: list[dict], attempt: int) -> str:
    recent_titles = "\n".join(f"- {a['title_en']}" for a in recent_articles[:20])
    angles = [
        "a step-by-step actionable guide with real dollar amounts",
        "a comparison between two specific tools or strategies with a clear winner",
        "a common mistake that costs people money on this topic",
        "a counterintuitive approach that works better than the standard advice",
        "a beginner-friendly guide with specific app or product recommendations",
        "an approach for a specific life situation (student, family, freelancer)",
    ]
    angle = angles[attempt % len(angles)]
    prompt = f"""You have this personal finance topic: "{original}"

It's too similar to already published articles:
{recent_titles}

Transform it into a completely different article using this specific angle: {angle}

The new topic must:
- Be a real search query Americans type into Google
- Mention a specific tool, strategy or dollar amount
- Have a useful, search-optimized title (not clickbait)

Reply ONLY with the new title (1 line, max 120 characters)."""
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            max_tokens=80,
        )
        mutated = resp.choices[0].message.content.strip().strip('"').strip("'")
        print(f"  🔄 Mutated (attempt {attempt+1}): {mutated[:70]}")
        return mutated if len(mutated) > 15 else original
    except Exception as e:
        print(f"  ⚠️  Error mutating: {e}")
        return original

# ── BUILD CANDIDATE POOL ──────────────────────────────────────────────────────
def build_candidate_pool(recent_articles: list[dict]) -> list[str]:
    print("🔍 Building finance candidate pool (5 sources)...")
    pool = []

    print("  📰 Source 1: Finance news (SerpAPI news EN)...")
    news = fetch_serpapi_news()
    print(f"     → {len(news)} headlines fetched")
    pool.extend(news)

    print("  📈 Source 2: Trending finance searches US (SerpAPI organic)...")
    trends = fetch_serpapi_trends()
    print(f"     → {len(trends)} trends fetched")
    pool.extend(trends)

    print("  🎯 Source 3: Finance search intents (SerpAPI news)...")
    intents = fetch_finance_search_intents()
    print(f"     → {len(intents)} intent signals fetched")
    pool.extend(intents)

    print("  🧠 Source 4: Niche finance ideas (GPT-4o-mini)...")
    niche = generate_niche_topics(recent_articles, n=15)
    print(f"     → {len(niche)} niche ideas generated")
    pool.extend(niche)

    fallback = get_fallback_topics()
    pool.extend(fallback)

    seen = set()
    unique = []
    for p in pool:
        key = p.lower().strip()[:60]
        if key not in seen and len(p) > 20:
            seen.add(key)
            unique.append(normalize_year(p))
    print(f"  ✅ Total pool: {len(unique)} unique candidates")
    return unique

# ── GENERATE ARTICLE WITH CLAUDE ─────────────────────────────────────────────
FINANCE_DISCLAIMER = """

---

*Disclaimer: This article is for informational and educational purposes only. It does not constitute financial advice, investment advice, or a recommendation to buy or sell any financial product. Always consult a qualified financial advisor before making financial decisions. Past performance is not indicative of future results.*
"""

def generate_article(keyword: str, recent_context: str) -> dict:
    global _claude_calls_this_run, _claude_tokens_this_run
    print(f"  ✍️  Claude generating finance article: {keyword[:70]}...")
    category  = detect_fin_category(keyword)
    min_words = MIN_WORD_COUNT

    _check_claude_budget(output_tokens=6000)

    prompt = f"""Write a complete personal finance article in English about: "{keyword}"

ALREADY PUBLISHED ON NEWSTIDE FINANCE (do not repeat these topics or angles):
{recent_context}

THIS IS A YMYL (Your Money Your Life) ARTICLE — follow Google E-E-A-T guidelines strictly:
- Cite real, verifiable data (FDIC rates, historical averages, government stats) where possible
- Be honest about risks and limitations
- Acknowledge when advice depends on individual circumstances
- Do NOT promise specific returns or guarantee outcomes
- Do NOT make dangerous financial claims

STRUCTURE (use markdown):
- H1 title: search-intent optimized, practical, specific (45-58 chars, HARD MAX 60)
- Introduction: 2 paragraphs — hook with a relatable situation or concrete stat, then explain what the reader will learn
- "Who this is for" section: be explicit about who benefits most from this article
- 4-5 H2 sections covering: the core how-to steps, specific tools/apps/strategies with real names, a comparison or ranking where relevant, common mistakes to avoid
- "When this doesn't work" section: honest caveats (income level, existing debt, credit score, etc.)
- Conclusion: practical next step the reader can take today

REQUIREMENTS:
- MINIMUM {min_words} words
- Practical steps, not vague advice — include real app names, real account types, real numbers
- Tone: knowledgeable friend, not a corporate financial services firm
- USA focus: US accounts, US tax laws, US apps
- Current year is 2026
- Category: {category}
- Do NOT start with "In the world of..." or generic openings

SEO TITLE RULES (CRITICAL):
- H1 MUST be between {TITLE_SOFT_MIN} and {TITLE_SOFT_MAX} characters
- HARD LIMIT: never exceed {TITLE_MAX_CHARS} characters
- Must match search intent — it should read like something someone would actually Google
- Count chars before writing

At the end, on a separate line write exactly:
EXCERPT: [120 to 155 char summary that answers what the article does and for whom — compelling, not generic]"""

    message = claude_client.messages.create(
        model=MODEL_GENERATE, max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
        system=(
            f"You are a senior personal finance writer and editor with 15 years of experience. "
            f"You write for NewsTide Finance, a practical personal finance site for everyday Americans. "
            f"Your content is actionable, honest, and grounded in real data. You follow Google E-E-A-T guidelines strictly. "
            f"The current year is 2026. "
            f"IMPORTANT: H1 titles must be between {TITLE_SOFT_MIN} and {TITLE_SOFT_MAX} characters, "
            f"never more than {TITLE_MAX_CHARS}. "
            f"Excerpts are meta descriptions — make them answer the search query directly."
        )
    )
    output_tokens = message.usage.output_tokens if hasattr(message, 'usage') else 6000
    _register_claude_call(output_tokens)

    raw = message.content[0].text
    excerpt = ""
    if "EXCERPT:" in raw:
        parts   = raw.split("EXCERPT:")
        raw     = parts[0].strip()
        excerpt = normalize_excerpt(parts[1].strip(), 120, 155)
    return {"content": raw, "excerpt": excerpt, "category": category}

# ── HUMANIZE WITH GPT ─────────────────────────────────────────────────────────
def humanize(text: str) -> str:
    print("  🧠 GPT humanizing finance article...")
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": """You are a human editor with 15 years in personal finance media.
Rewrite the article applying these rules WITHOUT changing data, facts or financial accuracy:
- Mix short sentences (5-8 words) with longer ones (18-28 words)
- Use varied connectors: "however", "that said", "here's the thing", "worth noting", "in practice"
- Add occasional first-person editorial voice: "what most people miss here", "in my experience", "honestly"
- Include 1-2 natural rhetorical questions
- Replace jargon: "utilize" → "use", "in conclusion" → "bottom line", "robust" → "solid"
- Do NOT add or remove financial facts, do NOT invent data
Keep all markdown headings. Return ONLY the article, no explanations."""},
            {"role": "user", "content": text}
        ],
        temperature=0.85, max_tokens=6000
    )
    return response.choices[0].message.content

# ── UNSPLASH ──────────────────────────────────────────────────────────────────
def get_unsplash_image(query: str, idx: int = 0) -> dict | None:
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 5, "orientation": "landscape", "content_filter": "high"},
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return None
        pick = results[min(idx, len(results) - 1)]
        return {
            "url":        pick["urls"]["regular"],
            "alt":        pick.get("alt_description") or query,
            "author":     pick["user"]["name"],
            "author_url": pick["user"]["links"]["html"],
        }
    except Exception as e:
        print(f"  Unsplash error: {e}")
        return None

def get_image_queries(title: str, excerpt: str) -> list[str]:
    prompt = (
        f"Article title: {title}\nSummary: {excerpt}\n\n"
        "Give me exactly 3 short English search queries (2-4 words each) to find "
        "relevant, visually appealing Unsplash photos for this personal finance article. "
        "Queries should be concrete and visual (e.g. 'savings jar coins', 'budget planning notebook', 'credit card wallet'). "
        "Reply with ONLY the 3 queries, one per line."
    )
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST, max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        return lines[:3] if lines else ["personal finance money", "savings budget", "financial planning"]
    except:
        return ["personal finance money", "savings budget", "financial planning"]

def fetch_best_image(queries: list[str], title: str, idx: int = 0) -> dict | None:
    for query in queries:
        img = get_unsplash_image(query, idx=idx)
        if img:
            print(f"  🖼️  Image: '{query}' → {img['author']}")
            return img
        time.sleep(0.4)
    return None

def inject_images(content: str, cover: dict | None, inline: dict | None) -> str:
    def img_md(img: dict) -> str:
        alt = img["alt"].replace('"', "'")
        return f"![{alt}]({img['url']})\n*Photo: [{img['author']}]({img['author_url']}) on Unsplash*\n"
    lines = content.split("\n")
    if cover:
        new_lines, inserted, blank = [], False, False
        for line in lines:
            new_lines.append(line)
            if not inserted and line.strip() and not line.startswith("#"):
                blank = True
            elif blank and not line.strip():
                new_lines += ["", img_md(cover)]
                inserted = True
                blank = False
        lines = new_lines
    if inline:
        new_lines, h2_count = [], 0
        for line in lines:
            new_lines.append(line)
            if line.startswith("## "):
                h2_count += 1
                if h2_count == 2:
                    new_lines += ["", img_md(inline)]
        lines = new_lines
    return "\n".join(lines)

# ── SAVE TO SUPABASE (finance_articles) ───────────────────────────────────────
def save_article(
    keyword: str,
    content_en: str,
    excerpt_en: str,
    title_en: str,
    slug_en: str,
    category: str,
    article_idx: int,
    cover_image_url: str | None = None,
) -> str | None:
    # Strip H1 from body if present
    lines = content_en.strip().split("\n")
    if lines and lines[0].strip().startswith("# "):
        content_en = "\n".join(lines[1:]).strip()

    title_en   = smart_trim(title_en, TITLE_MAX_CHARS)
    excerpt_en = normalize_excerpt(excerpt_en or title_en[:150], 120, 155)
    rt = reading_time(content_en)
    if rt < MIN_READING_TIME:
        print(f"  ⚠️  reading_time={rt} < {MIN_READING_TIME} — forcing to {MIN_READING_TIME}")
        rt = MIN_READING_TIME

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Append disclaimer
    content_en_with_disclaimer = content_en + FINANCE_DISCLAIMER

    data = {
        "title":           title_en,
        "slug":            slug_en,
        "content":         content_en_with_disclaimer,  # ES field stores EN (finance is EN-only vertical)
        "excerpt":         excerpt_en,
        "title_en":        title_en,
        "slug_en":         slug_en,
        "content_en":      content_en_with_disclaimer,
        "excerpt_en":      excerpt_en,
        "category":        category,
        "author":          AUTHORS[article_idx % len(AUTHORS)],
        "keyword":         keyword,
        "keyword_hash":    md5(keyword),
        "reading_time":    rt,
        "featured":        article_idx == 0,
        "image_gradient":  GRADIENTS[article_idx % len(GRADIENTS)],
        "published_at":    now_iso,
        "cover_image_url": cover_image_url,
    }
    try:
        supabase_client.table("finance_articles").insert(data).execute()
        print(f"  ✅ Saved to finance_articles: {title_en[:70]}")
        final_slug = slug_en or slugify_en(title_en)
        ping_indexnow([f"https://www.newstide.news/en/fin/{final_slug}"])
        return title_en
    except Exception as e:
        print(f"  ❌ Error saving: {e}")
        return None

# ── PROCESS ONE TOPIC → ARTICLE ───────────────────────────────────────────────
def process_topic(
    topic: str,
    recent_articles: list[dict],
    published_this_run: list[str],
    article_idx: int,
) -> str | None:
    recent_context = format_recent_context(recent_articles)
    candidate = topic
    for attempt in range(5):
        if not is_duplicate_topic(candidate, recent_articles, published_this_run):
            break
        print(f"  ⚠️  Duplicate detected — mutating (attempt {attempt+1}/5)...")
        candidate = mutate_topic(candidate, recent_articles, attempt)
    else:
        print(f"  ❌ Could not find unique angle for: {topic[:50]} — skipping")
        return None

    if already_published_hash(candidate):
        print(f"  ⏭️  Exact hash already exists — skipping")
        return None

    print(f"  🎯 Topic approved: {candidate[:80]}")
    try:
        result      = generate_article(candidate, recent_context)
        raw_content = result["content"]

        if not validate_article_content(raw_content, label="claude-raw"):
            print(f"  ❌ Article discarded (invalid Claude output) — skipping topic")
            return None

        humanized = humanize(raw_content)
        if not validate_article_content(humanized, label="humanized"):
            print(f"  ⚠️  Humanized invalid — using original Claude content")
            humanized = raw_content

        # Extract title from H1
        title_preview = candidate[:100]
        for line in humanized.strip().split("\n")[:5]:
            if line.strip().startswith("# "):
                title_preview = line.strip()[2:].strip()
                break
        title_preview = smart_trim(title_preview, TITLE_MAX_CHARS)
        slug = slugify_en(title_preview)

        print("  🔍 Searching Unsplash images...")
        queries    = get_image_queries(title_preview, result["excerpt"])
        cover_img  = fetch_best_image(queries, title_preview, idx=0)
        inline_img = fetch_best_image(queries, title_preview, idx=1)
        content    = inject_images(humanized, cover_img, inline_img)
        cover_image_url = cover_img["url"] if cover_img else None

        saved_title = save_article(
            keyword=candidate,
            content_en=content,
            excerpt_en=result["excerpt"],
            title_en=title_preview,
            slug_en=slug,
            category=result["category"],
            article_idx=article_idx,
            cover_image_url=cover_image_url,
        )
        return saved_title

    except CostLimitExceeded as e:
        raise
    except Exception as e:
        print(f"  ❌ Error processing '{candidate[:50]}': {e}")
        return None

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n🚀 NewsTide Finance Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(
        f"🔒 Safety limits: "
        f"max {MAX_CLAUDE_CALLS_PER_RUN} Claude calls, "
        f"max {MAX_CLAUDE_TOKENS_PER_RUN:,} output tokens"
    )

    print("📚 Loading recent finance articles from Supabase...")
    recent_articles = get_recent_articles()
    print(f"   {len(recent_articles)} articles from last 45 days loaded")

    candidate_pool = build_candidate_pool(recent_articles)

    published_titles: list[str] = []
    pool_index = 0
    extra_niche_attempts = 0

    print(f"\n🎯 Target: {ARTICLES_PER_RUN} articles\n")

    try:
        while len(published_titles) < ARTICLES_PER_RUN:
            if pool_index >= len(candidate_pool):
                extra_niche_attempts += 1
                if extra_niche_attempts > MAX_POOL_EXPANSIONS:
                    print(f"⛔ Pool exhausted after {MAX_POOL_EXPANSIONS} expansions — aborting.")
                    break
                print(f"\n♻️  Pool exhausted — generating more niche topics (expansion {extra_niche_attempts}/{MAX_POOL_EXPANSIONS})...")
                extra = generate_niche_topics(
                    recent_articles + [{"title_en": t, "category": "Saving Money", "keyword": t, "excerpt_en": ""} for t in published_titles],
                    n=10
                )
                candidate_pool.extend(extra)
                if not extra:
                    candidate_pool.extend(get_fallback_topics())
                continue

            topic = candidate_pool[pool_index]
            pool_index += 1

            print(f"\n📝 [{len(published_titles)+1}/{ARTICLES_PER_RUN}] Processing: {topic[:70]}")

            saved = process_topic(
                topic,
                recent_articles,
                published_titles,
                article_idx=len(published_titles),
            )

            if saved:
                published_titles.append(saved)
                recent_articles.insert(0, {
                    "title_en": saved,
                    "keyword":  topic,
                    "category": detect_fin_category(topic),
                    "excerpt_en": "",
                })
                print(f"\n✅ Article {len(published_titles)}/{ARTICLES_PER_RUN} published: {saved[:60]}")
                if len(published_titles) < ARTICLES_PER_RUN:
                    print("   Continuing with next...\n")
                time.sleep(2)

    except CostLimitExceeded as e:
        print(f"\n{e}")
        print(f"   Articles published before cutoff: {len(published_titles)}")

    print(f"\n{'='*60}")
    print(f"🎉 Finance Pipeline finished: {len(published_titles)} articles published")
    print(f"📊 Total Claude calls: {_claude_calls_this_run} | Output tokens: {_claude_tokens_this_run:,}")
    for i, t in enumerate(published_titles, 1):
        print(f"   {i}. {t[:80]}")

if __name__ == "__main__":
    main()
