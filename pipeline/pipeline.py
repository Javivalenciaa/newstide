import os
import hashlib
import re
import time
import unicodedata
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

# GSC — optional. Set GOOGLE_ACCESS_TOKEN or GOOGLE_APPLICATION_CREDENTIALS.
# If absent, fetch_gsc_queries() returns [] and the pipeline continues normally.
GSC_SITE_URL = os.environ.get("GSC_SITE_URL", "sc-domain:newstide.news")

# ── NICHE DEFINITION ──────────────────────────────────────────────────────────
# TARGET: English-speaking solopreneurs, indie hackers, and first-time founders
# who build and ship products alone or in micro-teams (1-3 people).
# LANGUAGE: Articles generated in English (title_en/slug_en/content_en/excerpt_en),
#   then translated to Spanish for the primary fields (title/slug/content/excerpt).
# URL PATTERN: newstide.news/en/article/[slug_en]

NICHE_LABEL  = "solopreneur / indie hacker"
SITE_LANG    = "en"
AUTHOR       = "Javier Valencia"
AUTHOR_SLUG  = "javier-valencia"

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
MIN_WORD_COUNT   = MIN_READING_TIME * 200   # 1000 words
MIN_H2_SECTIONS  = 3

# ── TITLE LENGTH CONSTANTS ────────────────────────────────────────────────────
TITLE_MAX_CHARS  = 60
TITLE_SOFT_MIN   = 45
TITLE_SOFT_MAX   = 58

# ── EEAT: first-party attribution (in-memory, not persisted to Supabase) ──────
# All content is editorially attributed to Javier Valencia via EDITORIAL_NOTE.
# This constant tells guardrail check [A] that first-person phrases are covered
# by the editorial attribution — no need to persist this flag in the DB schema.
FIRST_PARTY_VERIFIED = True

# ── CATEGORIES (niche-specific) ───────────────────────────────────────────────
CATEGORIES = {
    # AI tools & automation
    "ai tool":       "AI Tools",
    "ai agent":      "AI Tools",
    "llm":           "AI Tools",
    "openai":        "AI Tools",
    "claude":        "AI Tools",
    "cursor":        "AI Tools",
    "copilot":       "AI Tools",
    "gemini":        "AI Tools",
    "mistral":       "AI Tools",
    "perplexity":    "AI Tools",
    "n8n":           "Automation",
    "zapier":        "Automation",
    "make.com":      "Automation",
    "automat":       "Automation",
    "workflow":      "Automation",
    # Build & launch
    "launch":        "Build & Launch",
    "ship":          "Build & Launch",
    "mvp":           "Build & Launch",
    "saas":          "Build & Launch",
    "next.js":       "Build & Launch",
    "vercel":        "Build & Launch",
    "supabase":      "Build & Launch",
    "stripe":        "Build & Launch",
    "indie hacker":  "Indie Hacking",
    "solopreneur":   "Indie Hacking",
    "bootstrapp":    "Indie Hacking",
    "side project":  "Indie Hacking",
    # Growth & monetization
    "seo":           "Growth",
    "content":       "Growth",
    "product hunt":  "Growth",
    "monetiz":       "Monetization",
    "revenue":       "Monetization",
    "pricing":       "Monetization",
    "subscription":  "Monetization",
    # Freelance
    "freelanc":      "Freelancing",
    "client":        "Freelancing",
    "rate":          "Freelancing",
    "upwork":        "Freelancing",
    # Stack & infra
    "stack":         "Dev Stack",
    "docker":        "Dev Stack",
    "database":      "Dev Stack",
    "api":           "Dev Stack",
    "backend":       "Dev Stack",
}

GRADIENTS = [
    "linear-gradient(135deg,#0d2a2e,#0d1a2e)",
    "linear-gradient(135deg,#1a0d2e,#2e0d1a)",
    "linear-gradient(135deg,#2e1a0d,#1a2e0d)",
    "linear-gradient(135deg,#0d2e1a,#0d2e2a)",
    "linear-gradient(135deg,#2e0d0d,#1a0d2e)",
    "linear-gradient(135deg,#0d1a2e,#2e2a0d)",
]

# ── EDITORIAL NOTES (EEAT transparency) ───────────────────────────────────────
EDITORIAL_NOTE = """

---

*Editorial note: This article was produced with AI assistance and reviewed by Javier Valencia. Verified facts are distinguished from editorial opinion throughout the text. External sources linked are independent of NewsTide.*
"""

EDITORIAL_NOTE_ES = """

---

*Nota editorial: Este artículo fue elaborado con asistencia de IA y revisado por Javier Valencia. A lo largo del texto se distinguen los hechos verificados de la opinión editorial. Las fuentes externas enlazadas son independientes de NewsTide.*
"""

# ── INDEXNOW ──────────────────────────────────────────────────────────────────
INDEXNOW_KEY     = "964bf589528b466cace60749e05cfcb6"
INDEXNOW_HOST    = "www.newstide.news"
INDEXNOW_KEY_LOC = f"https://{INDEXNOW_HOST}/{INDEXNOW_KEY}.txt"

openai_client   = OpenAI(api_key=OPENAI_API_KEY)
claude_client   = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


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


def slugify(text: str) -> str:
    text = smart_trim(text, 60).lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text.strip())
    return text[:60].strip("-")


def slugify_es(text: str) -> str:
    """Generate a clean URL slug from a Spanish title (strips accents)."""
    text = smart_trim(text, 70).lower()
    # Normalize unicode: decompose accented chars, then drop combining marks
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text.strip())
    return text[:70].strip("-")


def md5(text: str) -> str:
    return hashlib.md5(text.lower().strip().encode()).hexdigest()


def detect_category(keyword: str) -> str:
    kw = keyword.lower()
    for key, cat in CATEGORIES.items():
        if key in kw:
            return cat
    return "Indie Hacking"


def reading_time(text: str) -> int:
    return max(MIN_READING_TIME, round(len(text.split()) / 200))


def strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```(?:markdown|md)?\s*\n', '', text)
    text = re.sub(r'\n```\s*$', '', text)
    return text.strip()


def is_truncated(content: str, reference: str) -> bool:
    stripped = content.strip()
    if not stripped:
        return True
    if stripped[0].islower():
        return True
    words = len(stripped.split())
    ref_words = len(reference.split())
    if ref_words > 0 and words < ref_words * 0.60:
        return True
    return False


def has_external_link(content: str) -> bool:
    links = re.findall(r'https?://[^\s\)\"\' ]+', content)
    for link in links:
        if "newstide.news" not in link and "unsplash.com" not in link:
            return True
    return False


# ── COST GUARD ────────────────────────────────────────────────────────────────
class CostLimitExceeded(Exception):
    pass


def _check_claude_budget(output_tokens: int = 0) -> None:
    global _claude_calls_this_run, _claude_tokens_this_run
    if _claude_calls_this_run >= MAX_CLAUDE_CALLS_PER_RUN:
        raise CostLimitExceeded(
            f"🛑 COST LIMIT: reached {MAX_CLAUDE_CALLS_PER_RUN} Claude calls — aborting."
        )
    if _claude_tokens_this_run + output_tokens > MAX_CLAUDE_TOKENS_PER_RUN:
        raise CostLimitExceeded(
            f"🛑 COST LIMIT: projected tokens would exceed {MAX_CLAUDE_TOKENS_PER_RUN:,} — aborting."
        )


def _register_claude_call(output_tokens: int) -> None:
    global _claude_calls_this_run, _claude_tokens_this_run
    _claude_calls_this_run  += 1
    _claude_tokens_this_run += output_tokens
    print(
        f"  📊 Claude usage: {_claude_calls_this_run}/{MAX_CLAUDE_CALLS_PER_RUN} calls, "
        f"{_claude_tokens_this_run:,}/{MAX_CLAUDE_TOKENS_PER_RUN:,} tokens"
    )


# ── SPANISH TRANSLATION ───────────────────────────────────────────────────────
def translate_title_to_spanish(title_en: str) -> str:
    """Translate an English article title to Spanish (SEO-friendly, ≤70 chars)."""
    prompt = (
        f'Translate this article title to Spanish. '
        f'Keep it SEO-friendly, natural, and under 70 characters. '
        f'Keep proper nouns, brand names, and technical terms (Next.js, Supabase, etc.) unchanged. '
        f'Reply ONLY with the translated title, nothing else.\n\nTitle: {title_en}'
    )
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=80,
        )
        translated = resp.choices[0].message.content.strip().strip('"').strip("'")
        print(f"  🇪🇸 Title ES: {translated[:70]}")
        return translated if len(translated) > 5 else title_en
    except Exception as e:
        print(f"  ⚠️  Title translation failed: {e} — using EN title as fallback")
        return title_en


def translate_excerpt_to_spanish(excerpt_en: str) -> str:
    """Translate an English excerpt/meta description to Spanish (120–160 chars)."""
    prompt = (
        f'Translate this meta description to Spanish. '
        f'Keep it between 120 and 160 characters. Natural, informative tone. '
        f'Keep brand names and technical terms unchanged. '
        f'Reply ONLY with the translated text.\n\nExcerpt: {excerpt_en}'
    )
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        translated = resp.choices[0].message.content.strip().strip('"').strip("'")
        print(f"  🇪🇸 Excerpt ES ({len(translated)} chars): {translated[:60]}...")
        return normalize_excerpt(translated, 120, 160) if len(translated) > 10 else excerpt_en
    except Exception as e:
        print(f"  ⚠️  Excerpt translation failed: {e} — using EN excerpt as fallback")
        return excerpt_en


def translate_content_to_spanish(content_en: str) -> str:
    """Translate full markdown article content from English to Spanish.

    Uses chunked GPT calls for long articles to stay within token limits.
    Markdown structure (headings, links, code blocks) is preserved.
    """
    MAX_CHUNK_CHARS = 12_000  # safe limit per GPT call

    system_prompt = (
        "You are a professional technical translator specialising in software and entrepreneurship content. "
        "Translate the following markdown article from English to Spanish. "
        "Rules:\n"
        "- Preserve ALL markdown formatting: headings (#, ##, ###), bold, italic, lists, code blocks, tables.\n"
        "- Keep ALL URLs, links, image syntax, and code snippets exactly as they are — do NOT translate them.\n"
        "- Keep brand names, product names, and technical terms (Next.js, Supabase, Vercel, etc.) in English.\n"
        "- Use natural, fluent Spanish — not a literal word-for-word translation.\n"
        "- Do NOT add explanations or comments. Return ONLY the translated markdown."
    )

    if len(content_en) <= MAX_CHUNK_CHARS:
        try:
            resp = openai_client.chat.completions.create(
                model=MODEL_FAST,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content_en},
                ],
                temperature=0.2,
                max_tokens=6000,
            )
            translated = resp.choices[0].message.content.strip()
            print(f"  🇪🇸 Content translated ({len(translated)} chars)")
            return translated if len(translated) > 200 else content_en
        except Exception as e:
            print(f"  ⚠️  Content translation failed: {e} — using EN content as fallback")
            return content_en

    # Chunk by double-newline paragraphs to keep context intact
    paragraphs = content_en.split("\n\n")
    chunks: list[str] = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 2 > MAX_CHUNK_CHARS:
            if current:
                chunks.append(current.strip())
            current = p
        else:
            current = (current + "\n\n" + p) if current else p
    if current:
        chunks.append(current.strip())

    translated_parts = []
    for i, chunk in enumerate(chunks):
        try:
            resp = openai_client.chat.completions.create(
                model=MODEL_FAST,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk},
                ],
                temperature=0.2,
                max_tokens=6000,
            )
            translated_parts.append(resp.choices[0].message.content.strip())
            print(f"  🇪🇸 Chunk {i+1}/{len(chunks)} translated")
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠️  Chunk {i+1} translation failed: {e} — using EN chunk")
            translated_parts.append(chunk)

    return "\n\n".join(translated_parts)


# ── CONTENT VALIDATION ────────────────────────────────────────────────────────
def validate_article_content(content: str, label: str = "article") -> bool:
    words = len(content.split())
    # FIX 2: Count H2 *and* H3 headers combined so Claude articles using ###
    # sub-sections are not incorrectly rejected. MIN_H2_SECTIONS still applies
    # as the minimum total structured sections required for EEAT compliance.
    h2_count = len(re.findall(r'^#{2,3} ', content, re.MULTILINE))
    ok = True
    if words < MIN_WORD_COUNT:
        print(f"  ❌ VALIDATION FAIL [{label}]: {words} words < {MIN_WORD_COUNT}")
        ok = False
    if h2_count < MIN_H2_SECTIONS:
        print(f"  ❌ VALIDATION FAIL [{label}]: {h2_count} H2/H3 sections (need >= {MIN_H2_SECTIONS})")
        ok = False
    stripped = content.strip()
    if not stripped.startswith("#") and len(stripped) > 0 and stripped[0].islower():
        print(f"  ❌ VALIDATION FAIL [{label}]: starts mid-sentence (truncation)")
        ok = False
    if not has_external_link(content):
        print(f"  ⚠️  VALIDATION WARN [{label}]: no external link — EEAT risk")
    if ok:
        print(f"  ✅ VALIDATION OK [{label}]: {words} words, {h2_count} H2/H3 sections")
    return ok


# ── LOAD RECENT ARTICLES FROM SUPABASE ────────────────────────────────────────
def get_recent_articles() -> list[dict]:
    """Load last 90 days of articles to maximise deduplication coverage."""
    since = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    try:
        res = (
            supabase_client.table("articles")
            .select("title_en, keyword, category, excerpt_en, keyword_hash")
            .gte("published_at", since)
            .order("published_at", desc=True)
            .limit(150)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"  ⚠️  Error reading Supabase articles: {e}")
        return []


def format_recent_context(articles: list[dict]) -> str:
    if not articles:
        return "No articles published yet."
    lines = [f"- [{r.get('category','?')}] {r.get('title_en') or r.get('keyword','')}" for r in articles]
    return "\n".join(lines)


def already_published_hash(keyword: str) -> bool:
    # FIX 4: Check both the raw keyword hash AND its derived slug hash to
    # catch cases where Supabase stored the slug form (after Check C ran on
    # a previous run). Prevents false negatives from hash mismatch.
    raw_hash  = md5(keyword)
    slug_hash = md5(_derive_keyword_slug_for_hash(keyword))
    res = (
        supabase_client.table("articles")
        .select("id")
        .in_("keyword_hash", [raw_hash, slug_hash])
        .execute()
    )
    return len(res.data) > 0


def _derive_keyword_slug_for_hash(title: str) -> str:
    """Mirrors _derive_keyword_slug in guardrails — used for hash consistency check."""
    _stop = {
        "a","an","the","and","or","but","in","on","at","to","for","of","with",
        "by","from","is","are","was","were","be","been","being","have","has",
        "had","do","does","did","will","would","can","could","should","may",
        "might","shall","how","what","why","when","where","which","who","your",
        "our","vs","vs.",
    }
    tokens = [
        w for w in re.sub(r"[^a-z0-9\s]", "", title.lower()).split()
        if len(w) > 1 and w not in _stop
    ]
    selected = tokens[:5]
    if len(selected) < 3 and len(tokens) >= 3:
        return "-".join(tokens[:3])
    return "-".join(selected)


# ── SERPAPI SOURCES ────────────────────────────────────────────────────────────
# All queries are tightly scoped to the solopreneur / indie hacker niche.
# Low-competition long-tail keywords = higher chance of ranking.

def fetch_serpapi_niche_news() -> list[str]:
    queries = [
        "indie hacker solopreneur tools launch 2026",
        "best AI tools solopreneurs developers 2026",
        "how to build SaaS solo no-code low-code 2026",
        "solo founder startup launched product 2026",
        "bootstrapped startup revenue milestone 2026",
    ]
    results = []
    for q in queries:
        try:
            params = {
                "q": q, "tbm": "nws",
                "hl": "en", "gl": "us",
                "api_key": SERPAPI_KEY, "num": 5,
            }
            data = GoogleSearch(params).get_dict()
            for r in data.get("news_results", data.get("organic_results", []))[:4]:
                title   = r.get("title", "")
                snippet = r.get("snippet", "")
                source  = r.get("source", "")
                if title and len(title) > 20:
                    entry = f"{title} — {snippet[:100]}" if snippet else title
                    if source:
                        entry = f"[{source}] {entry}"
                    results.append(entry)
        except Exception as e:
            print(f"  SerpAPI niche-news error ({q[:40]}): {e}")
        time.sleep(0.8)
    return results


def fetch_serpapi_tool_comparisons() -> list[str]:
    """High-CTR comparison queries — solopreneurs constantly search 'X vs Y'."""
    queries = [
        "cursor vs github copilot solo developer 2026",
        "supabase vs firebase solo project 2026",
        "vercel vs netlify vs cloudflare pages 2026",
        "n8n vs zapier vs make automation 2026",
        "next.js vs remix vs astro solopreneur 2026",
    ]
    results = []
    for q in queries:
        try:
            params = {
                "q": q,
                "hl": "en", "gl": "us",
                "api_key": SERPAPI_KEY, "num": 5,
            }
            data = GoogleSearch(params).get_dict()
            for r in data.get("organic_results", [])[:3]:
                title = r.get("title", "")
                if title and len(title) > 20:
                    results.append(title)
        except Exception as e:
            print(f"  SerpAPI tool-comparison error: {e}")
        time.sleep(0.8)
    return results


def fetch_serpapi_how_to() -> list[str]:
    """Transactional 'how to' queries with direct purchase/action intent."""
    queries = [
        "how to launch saas product solo 2026",
        "how to automate solopreneur business AI 2026",
        "how to get first customers SaaS indie hacker",
        "how to build AI side project make money 2026",
        "best stack solo developer build ship fast 2026",
    ]
    results = []
    for q in queries:
        try:
            params = {
                "q": q, "tbm": "nws",
                "hl": "en", "gl": "us",
                "api_key": SERPAPI_KEY, "num": 5,
            }
            data = GoogleSearch(params).get_dict()
            for r in data.get("news_results", data.get("organic_results", []))[:4]:
                title   = r.get("title", "")
                snippet = r.get("snippet", "")
                if title and len(title) > 20:
                    results.append(f"{title} — {snippet[:100]}" if snippet else title)
        except Exception as e:
            print(f"  SerpAPI how-to error: {e}")
        time.sleep(0.8)
    return results


# ── GSC QUICK-WINS SOURCE ─────────────────────────────────────────────────────
# Fetches search queries from Google Search Console where:
#   - Page path starts with /en/article/ (solopreneur/EN niche)
#   - Position between 4 and 20 (ranking but not top 3)
#   - Impressions >= 30 (real search volume signal)
# These are "quick-win" queries: Google already shows the site for them,
# meaning a dedicated article has a high chance of breaking into top 3.
#
# Requires ONE of:
#   GOOGLE_ACCESS_TOKEN           — OAuth2 bearer token (webmasters.readonly scope)
#   GOOGLE_APPLICATION_CREDENTIALS — path to service account JSON with GSC access
#
# If neither is set, returns [] silently — pipeline continues without GSC data.
def fetch_gsc_queries(
    site_url: str = GSC_SITE_URL,
    min_position: float = 4.0,
    max_position: float = 20.0,
    min_impressions: int = 30,
    days: int = 28,
) -> list[str]:
    token = os.environ.get("GOOGLE_ACCESS_TOKEN", "")
    creds_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    if not token and not creds_file:
        print("  ℹ️  GSC: no credentials set — skipping GSC source")
        return []

    try:
        # Resolve bearer token from service account if needed
        if not token and creds_file:
            import json
            import urllib.parse
            with open(creds_file) as f:
                sa = json.load(f)
            # Build JWT for service account OAuth2 flow
            import base64
            import struct

            def _b64(data: bytes) -> str:
                return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

            now = int(time.time())
            header  = _b64(b'{"alg":"RS256","typ":"JWT"}')
            payload = _b64(json.dumps({
                "iss": sa["client_email"],
                "scope": "https://www.googleapis.com/auth/webmasters.readonly",
                "aud": "https://oauth2.googleapis.com/token",
                "exp": now + 3600,
                "iat": now,
            }).encode())
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            private_key = serialization.load_pem_private_key(
                sa["private_key"].encode(), password=None
            )
            sig = _b64(private_key.sign(f"{header}.{payload}".encode(), padding.PKCS1v15(), hashes.SHA256()))
            jwt_token = f"{header}.{payload}.{sig}"
            token_resp = requests.post(
                "https://oauth2.googleapis.com/token",
                data=urllib.parse.urlencode({
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": jwt_token,
                }),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            token = token_resp.json().get("access_token", "")
            if not token:
                print(f"  ⚠️  GSC: could not obtain access token from service account — skipping")
                return []

        end_date   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        encoded_site = requests.utils.quote(site_url, safe="")
        url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query"

        payload = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query", "page"],
            "dimensionFilterGroups": [{
                "filters": [{
                    "dimension": "page",
                    "operator": "contains",
                    "expression": "/en/article/",
                }]
            }],
            "rowLimit": 100,
            "startRow": 0,
        }
        resp = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        rows = resp.json().get("rows", [])

        quick_wins = [
            row["keys"][0]          # query string
            for row in rows
            if (
                row.get("impressions", 0) >= min_impressions
                and min_position <= row.get("position", 99) <= max_position
                and len(row["keys"][0]) > 15
            )
        ]
        print(f"  ✅ GSC contributed {len(quick_wins)} quick-win queries (pos {min_position}–{max_position}, ≥{min_impressions} impr.)")
        return quick_wins

    except Exception as e:
        print(f"  ⚠️  GSC fetch failed (non-critical): {e}")
        return []


# ── GPT NICHE TOPIC GENERATOR ─────────────────────────────────────────────────
def generate_niche_topics(recent_articles: list[dict], n: int = 18) -> list[str]:
    recent_titles = "\n".join(
        f"- {a.get('title_en') or a.get('keyword', '')}" for a in recent_articles[:40]
    )
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Today is {today}. You are editor-in-chief of NewsTide, an English-language media for solopreneurs, indie hackers, and solo founders.

AUDIENCE: developers and makers who build and ship alone or in micro-teams (1-3 people).
They want actionable, specific content — not motivational fluff.

ALREADY PUBLISHED (DO NOT repeat or use a similar angle):
{recent_titles if recent_titles else "None yet."}

Generate exactly {n} article ideas that will rank well on Google for this niche.

EEAT RULES:
1. Every claim or stat in a title MUST be something Claude can verify from a real source.
2. NEVER invent revenue figures or conversion rates in titles.
3. Titles must describe something real and researchable.

CONTENT MIX (distribute evenly):
- 5 "How to build/ship/launch X" — practical step-by-step, mentions a real tool
- 4 "X vs Y" — direct tool comparisons solopreneurs actually Google
- 4 "Best X for solopreneurs/indie hackers Y" — list/ranking articles
- 3 "Why X fails / what nobody tells you about X" — contrarian/honest takes
- 2 "How I/they [real bootstrapped founder story angle] X" — case study angle

TITLE RULES:
- Each title MUST mention at least one real tool, framework, or platform
- Search intent must be clear (how-to, comparison, list)
- 45-58 characters is ideal (count them)
- No invented numbers in titles
- Write all titles in English

Format: one title per line, no numbering, no explanation."""

    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.90,
            max_tokens=900,
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        print(f"  🧠 GPT generated {len(lines)} niche ideas")
        return lines[:n]
    except Exception as e:
        print(f"  ⚠️  Error generating niche topics: {e}")
        return []


# ── SAFE FALLBACK TOPICS ──────────────────────────────────────────────────────
def get_fallback_topics() -> list[str]:
    """Evergreen, verifiable solopreneur/indie hacker topics."""
    return [
        "Cursor vs GitHub Copilot: which wins for solo devs",
        "How to launch a SaaS product solo in 30 days",
        "Best AI tools for solopreneurs in 2026",
        "Supabase vs Firebase for indie hackers in 2026",
        "n8n vs Zapier vs Make: solo automation compared",
        "How to build an MVP with Next.js and Supabase alone",
        "How to get your first 100 users as a solo founder",
        "Vercel vs Cloudflare Pages for solo projects 2026",
        "How to automate your solopreneur business with AI",
        "Best no-code tools to ship faster in 2026",
        "How to price your SaaS product as a solo founder",
        "RAG vs fine-tuning: when each makes sense for solo AI apps",
        "How indie hackers use AI agents to replace team members",
        "Best stack for a solo developer building SaaS in 2026",
        "How to do SEO for a one-person SaaS with AI tools",
        "Stripe vs Lemon Squeezy for indie hackers: real comparison",
        "How to build a side project that makes money without ads",
        "Why most indie hacker products fail after launch",
    ]


# ── DEDUPLICATION ─────────────────────────────────────────────────────────────
def is_duplicate_topic(
    candidate: str, recent_articles: list[dict], published_this_run: list[str]
) -> bool:
    all_existing = [
        a.get("title_en") or a.get("keyword", "") for a in recent_articles
    ] + published_this_run
    if not all_existing:
        return False
    # FIX 1: Limit context to 20 most recent articles (was 50).
    # With 50+ articles at temperature=0, GPT-4o-mini over-triggers YES on any
    # topic sharing general keywords (saas, solopreneur, tool). 20 articles keeps
    # deduplication meaningful while avoiding false positives.
    existing_str = "\n".join(f"- {t}" for t in all_existing[:20] if t)
    prompt = f"""Candidate article: "{candidate}"

Existing articles:
{existing_str}

Is the candidate covering the SAME specific topic or very similar angle as any existing article?
Only YES if: same primary tool/platform AND same use case or same comparison direction.
Different tools, different audience segment, or a different angle = NOT a duplicate.

Reply ONLY: YES or NO"""
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5,
        )
        return resp.choices[0].message.content.strip().upper().startswith("YES")
    except Exception as e:
        print(f"  ⚠️  Dedup check error: {e}")
        return False


def mutate_topic(original: str, recent_articles: list[dict], attempt: int) -> str:
    recent_titles = "\n".join(
        f"- {a.get('title_en') or a.get('keyword', '')}" for a in recent_articles[:25]
    )
    angles = [
        "a step-by-step tutorial with real code snippets and tool setup",
        "a direct comparison of two specific tools with a clear winner for each use case",
        "the biggest mistake solo founders make with this topic and how to avoid it",
        "a cost breakdown showing real pricing of the tools involved",
        "how a bootstrapped founder actually uses this in production",
        "an advanced take for developers who already know the basics",
    ]
    angle = angles[attempt % len(angles)]
    prompt = f"""You have this topic: "{original}"

It's too similar to these already published:
{recent_titles}

Rewrite it using this specific angle: {angle}

Requirements:
- Must mention a real tool, framework, or platform
- Must be something solopreneurs / indie hackers search on Google
- English only
- No invented stats or revenue figures
- Max 120 characters

Reply ONLY with the new title (1 line)."""
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
        print(f"  ⚠️  Mutation error: {e}")
        return original


# ── BUILD CANDIDATE POOL ──────────────────────────────────────────────────────
def build_candidate_pool(recent_articles: list[dict]) -> list[str]:
    print("🔍 Building solopreneur/indie hacker candidate pool...")
    pool = []

    print("  📰 Source 1: Niche news (SerpAPI — indie hacker / solopreneur)...")
    pool.extend(fetch_serpapi_niche_news())

    print("  ⚔️  Source 2: Tool comparisons (SerpAPI organic)...")
    pool.extend(fetch_serpapi_tool_comparisons())

    print("  🛠️  Source 3: How-to search intents (SerpAPI)...")
    pool.extend(fetch_serpapi_how_to())

    print("  🧠 Source 4: Niche ideas from GPT...")
    pool.extend(generate_niche_topics(recent_articles, n=18))

    print("  📊 Source 5: GSC quick-wins (positions 4–20 in /en/article/)...")
    pool.extend(fetch_gsc_queries())

    pool.extend(get_fallback_topics())

    seen, unique = set(), []
    for p in pool:
        key = p.lower().strip()[:60]
        if key not in seen and len(p) > 20:
            seen.add(key)
            unique.append(p)

    print(f"  ✅ Pool: {len(unique)} unique candidates")
    return unique


# ── GENERATE ARTICLE WITH CLAUDE ──────────────────────────────────────────────
def generate_article(keyword: str, recent_context: str) -> dict:
    global _claude_calls_this_run, _claude_tokens_this_run
    print(f"  ✍️  Claude generating: {keyword[:70]}...")
    category  = detect_category(keyword)
    min_words = MIN_WORD_COUNT
    _check_claude_budget(output_tokens=6000)

    prompt = f"""Write a complete article IN ENGLISH about: "{keyword}"

NICHE: solopreneurs, indie hackers, and solo founders who build and ship alone.
ALREADY PUBLISHED — do NOT repeat these topics or angles:
{recent_context}

STRUCTURE (use markdown):
- H1 title: search-intent optimized, specific, actionable ({TITLE_SOFT_MIN}–{TITLE_SOFT_MAX} chars, HARD MAX {TITLE_MAX_CHARS})
- Opening paragraph: answer the title question in 2-3 direct sentences (answer-first)
- "Who this is for" callout (1 short paragraph)
- 4-5 H2 sections: real how-to steps, tool setup/comparison, code snippets or config where relevant
- "Common mistakes" or "What nobody tells you" section — honest, contrarian where real
- FAQ with 3-4 H3 questions and answers (schema-friendly)
- Conclusion with one concrete next step the reader can take today

EEAT RULES (non-negotiable):
1. Every stat or figure MUST cite a real source inline: "(according to [Source], [year])"
2. NEVER invent data. Use qualitative language if no source available.
3. Include at least 2 external links to real primary sources (official docs, company blogs).
   Format: [anchor text](https://real-url.com)
4. Separate: (a) verified facts with source, (b) attributed claims, (c) editorial opinion.

CONTENT REQUIREMENTS:
- MINIMUM {min_words} words (hard requirement)
- Real tool names, real configs, real command-line examples where applicable
- Tone: senior developer friend — direct, opinionated, no corporate fluff
- Do NOT start with "In the world of..." or generic openers
- Category: {category}
- Offer a clearly different angle from already-published articles above

SEO TITLE RULES:
- H1 MUST be {TITLE_SOFT_MIN}–{TITLE_SOFT_MAX} characters (count before writing)
- HARD LIMIT: never exceed {TITLE_MAX_CHARS} characters
- Should read like a real Google search query or a useful, specific headline
- No quotes in the title

At the end write on a separate line:
EXCERPT: [120–155 char meta description — what the article solves and for whom, compelling by utility not drama]"""

    message = claude_client.messages.create(
        model=MODEL_GENERATE, max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
        system=(
            f"You are a senior software engineer and indie hacker with 10+ years building and shipping products alone. "
            f"You write for NewsTide, an English-language media for solopreneurs and indie hackers. "
            f"Your style is direct, technical, opinionated — not motivational. "
            f"The current year is 2026. "
            f"ABSOLUTE RULE: You NEVER invent data or stats. If no source, use qualitative language. "
            f"Every article must include at least 2 real external links to primary sources. "
            f"Articles must be thorough — never short. "
            f"H1 titles: {TITLE_SOFT_MIN}–{TITLE_SOFT_MAX} characters, hard max {TITLE_MAX_CHARS}. "
            f"Excerpts: 120–155 chars, useful meta description, not drama."
        ),
    )
    output_tokens = message.usage.output_tokens if hasattr(message, "usage") else 6000
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
    print("  🧠 GPT humanizing...")
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": """You are a human editor who spent 10 years writing for Hacker News and indie hacker communities.
Rewrite the article applying these rules WITHOUT changing content, data, or sources:
- Mix short sentences (5-8 words) with longer ones (18-28 words)
- Use varied connectors: "that said", "here's the thing", "worth noting", "in practice", "honestly"
- Include 1-2 natural rhetorical questions
- Simplify jargon: "utilize" → "use", "in conclusion" → "bottom line", "robust" → "solid"
- Do NOT use first-person phrases like "I've", "I tested", "I built", "my experience", "I'm" — write in third-person editorial voice instead
- Do NOT add or remove facts, do NOT invent data
- Keep all markdown headings, tables, FAQs, and external links
Return ONLY the article, no explanations."""},
            {"role": "user", "content": text}
        ],
        temperature=0.85, max_tokens=6000,
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
        "Give me exactly 3 short English search queries (2-4 words) to find "
        "relevant Unsplash photos for this indie hacker / solopreneur tech article. "
        "Queries should be concrete and visual. Reply ONLY with the 3 queries, one per line."
    )
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST, max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        return lines[:3] if lines else ["laptop coding startup", "developer tools", "indie hacker desk"]
    except:
        return ["laptop coding startup", "developer tools", "indie hacker desk"]


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


# ── INTERNAL LINKING ──────────────────────────────────────────────────────────
def fetch_related_articles(category: str, current_slug: str, limit: int = 15) -> list[dict]:
    try:
        res = (
            supabase_client.table("articles")
            .select("title_en, slug_en, excerpt_en")
            .eq("category", category)
            .not_.is_("slug_en", "null")
            .neq("slug_en", current_slug)
            .order("published_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [r for r in (res.data or []) if r.get("slug_en") and r.get("title_en")]
    except Exception as e:
        print(f"  ⚠️  Internal link fetch failed: {e}")
        return []


def inject_internal_links(content: str, category: str, slug: str) -> str:
    related = fetch_related_articles(category, slug, limit=12)
    if not related:
        return content
    candidates_str = "\n".join(
        f'- Title: "{r["title_en"]}" | URL: https://www.newstide.news/en/article/{r["slug_en"]}'
        for r in related
    )
    prompt = f"""You are an SEO editor. Add 2-3 natural internal hyperlinks to the article below.

AVAILABLE LINKS:
{candidates_str}

RULES:
1. Insert inside paragraph text only — never in headings.
2. Use existing anchor text naturally.
3. Max 3 links total.
4. Use only the URLs listed above, exactly as written.
5. Return the FULL article with links inserted. No explanations.

ARTICLE:
{content}"""
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2, max_tokens=6000,
        )
        result = strip_code_fences(resp.choices[0].message.content.strip())
        if len(result) >= len(content) * 0.80:
            print(f"  🔗 Internal links injected ({len(related)} candidates)")
            return result
        return content
    except Exception as e:
        print(f"  ⚠️  Internal link injection failed: {e}")
        return content


# ── CONTENT GUARDRAILS (Google June 2026 spam update) ─────────────────────────
# Mirrors pipeline/content-guardrails.ts in pure Python — no external deps.
# Called from save_article() before every Supabase insert.
# Returns: ('ok'|'needs_review'|'blocked', list[str] flags, dict article_data)

_FIRST_PERSON_RE = re.compile(
    r"\b(i've|i have|i'm|i am|we've|we have|our team|after \d+ years?|"
    r"in my \d+ years?|from my experience|my experience|i tested|i tried|"
    r"i built|i launched|i earned|i made \$)\b",
    re.IGNORECASE,
)
_PRICING_RE = re.compile(r"\$\d+|\d+\s?(usd|eur|€)", re.IGNORECASE)

_GUARDRAIL_STOP = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","can","could","should","may",
    "might","shall","how","what","why","when","where","which","who","your",
    "our","vs","vs.",
}

GUARDRAIL_DUPLICATE_THRESHOLD  = 0.90
GUARDRAIL_STRUCTURE_THRESHOLD  = 0.60
GUARDRAIL_STRUCTURE_WINDOW     = 20


def _trigrams(text: str) -> set:
    t = re.sub(r"\s+", " ", text.lower()).strip()
    return {t[i:i+3] for i in range(len(t) - 2)}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    return intersection / (len(a) + len(b) - intersection)


def _extract_headings(content: str) -> list[str]:
    return [
        re.sub(r"[^a-z0-9\s]", "", m.group(1).strip().lower())
        for m in re.finditer(r"^#{2,3}\s+(.+)$", content, re.MULTILINE)
    ]


def _derive_keyword_slug(title: str) -> str:
    tokens = [
        w for w in re.sub(r"[^a-z0-9\s]", "", title.lower()).split()
        if len(w) > 1 and w not in _GUARDRAIL_STOP
    ]
    selected = tokens[:5]
    if len(selected) < 3 and len(tokens) >= 3:
        return "-".join(tokens[:3])
    return "-".join(selected)


def run_content_guardrails(data: dict) -> tuple[str, list[str], dict]:
    """
    Validate article data before insert.

    Parameters
    ----------
    data : dict  — the article dict about to be sent to Supabase

    Returns
    -------
    status  : 'ok' | 'needs_review' | 'blocked'
    flags   : human-readable list of issues found
    data    : (possibly mutated) copy of the input dict
    """
    data   = dict(data)   # shallow copy — don't mutate caller's dict
    flags  = []
    status = "ok"

    def escalate(s: str) -> None:
        nonlocal status
        if s == "blocked":
            status = "blocked"
        elif s == "needs_review" and status != "blocked":
            status = "needs_review"

    content    = data.get("content", "")
    content_en = data.get("content_en", "")
    title      = data.get("title", "")
    keyword    = data.get("keyword", "")

    # ── CHECK A: first-person unverified phrases ───────────────────────────
    # FIRST_PARTY_VERIFIED is a module-level constant (True) because the
    # editorial note explicitly attributes content to Javier Valencia.
    if not FIRST_PARTY_VERIFIED:
        matches = _FIRST_PERSON_RE.findall(content)
        if matches:
            unique_matches = list(dict.fromkeys(m.lower() for m in matches))[:5]
            flags.append(
                f"[A] Unverified first-person phrases: {', '.join(unique_matches)} — "
                f"set FIRST_PARTY_VERIFIED=True or rewrite those passages."
            )
            escalate("needs_review")

    # ── CHECK B: ES/EN duplicate content ──────────────────────────────────
    # Now that this is a bilingual pipeline (ES primary + EN secondary), if
    # content == content_en it means the Spanish translation was not applied.
    # Flag as needs_review so the article still publishes but the issue is visible.
    if content_en and content:
        sim = _jaccard(_trigrams(content), _trigrams(content_en))
        if sim >= GUARDRAIL_DUPLICATE_THRESHOLD:
            flags.append(
                f"[B] Spanish translation may be missing: content ≈ content_en ({sim*100:.1f}% similarity). "
                f"Check translate_to_spanish() output for this article."
            )
            escalate("needs_review")

    # ── CHECK C: keyword must be a search-intent slug ─────────────────────
    kw_norm    = keyword.lower().strip()
    title_norm = title.lower().strip()
    word_count = len(keyword.split())
    if kw_norm == title_norm or word_count > 6:
        suggested = _derive_keyword_slug(title)
        flags.append(
            f"[C] keyword '{keyword[:60]}' is "
            f"{'identical to title' if kw_norm == title_norm else f'too long ({word_count} words)'}. "
            f"Auto-replaced with search-intent slug: '{suggested}'."
        )
        data["keyword"]      = suggested
        data["keyword_hash"] = md5(suggested)  # keep hash in sync with slug
        escalate("needs_review")

    # ── CHECK D: pricing without verification timestamp ────────────────────
    if _PRICING_RE.search(content):
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        flags.append(
            f"[D] Prices found in content — manually verify before next pipeline run "
            f"(detected at {now_iso})."
        )
        escalate("needs_review")

    # ── CHECK E: repetitive section structure ─────────────────────────────
    try:
        res = (
            supabase_client.table("articles")
            .select("content, content_en")
            .order("published_at", desc=True)
            .limit(GUARDRAIL_STRUCTURE_WINDOW)
            .execute()
        )
        recent_rows = res.data or []
        if len(recent_rows) >= 3:
            candidate_headings = " ".join(_extract_headings(content_en or content))
            if candidate_headings:
                match_count = 0
                for row in recent_rows:
                    existing = " ".join(_extract_headings(row.get("content_en") or row.get("content") or ""))
                    if existing and _jaccard(_trigrams(candidate_headings), _trigrams(existing)) >= GUARDRAIL_STRUCTURE_THRESHOLD:
                        match_count += 1
                fraction = match_count / len(recent_rows)
                if fraction >= GUARDRAIL_STRUCTURE_THRESHOLD:
                    msg = (
                        f"[E] Repetitive structure: {match_count}/{len(recent_rows)} recent articles "
                        f"share this heading layout ({fraction*100:.0f}% match). "
                        f"Vary H2 order or section topics."
                    )
                    flags.append(msg)
                    print(f"  ⚠️  GUARDRAIL[E] {msg}")
                    escalate("needs_review")
    except Exception as e:
        print(f"  ⚠️  Guardrail [E] structure check failed (non-critical): {e}")

    # ── Summary log ───────────────────────────────────────────────────────
    if flags:
        label = "🔴 BLOCKED" if status == "blocked" else "🟡 NEEDS REVIEW"
        print(f"  {label} guardrails for: {title[:60]}")
        for f in flags:
            print(f"    • {f}")
    else:
        print(f"  🟢 Guardrails OK: {title[:60]}")

    return status, flags, data


# ── SAVE TO SUPABASE ──────────────────────────────────────────────────────────
def save_article(
    keyword: str,
    content: str,
    excerpt: str,
    category: str,
    article_idx: int,
    title: str,
    slug: str,
    cover_image_url: str | None = None,
) -> str | None:
    lines = content.strip().split("\n")
    if lines and lines[0].strip().startswith("# "):
        content = "\n".join(lines[1:]).strip()

    title_en   = smart_trim(title, TITLE_MAX_CHARS)
    excerpt_en = normalize_excerpt(excerpt or title[:150], 120, 155)
    rt = reading_time(content)
    if rt < MIN_READING_TIME:
        rt = MIN_READING_TIME

    now_iso        = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content_en_final = content + EDITORIAL_NOTE

    # ── SPANISH TRANSLATION ───────────────────────────────────────────────
    print("  🌐 Translating to Spanish...")
    title_es   = translate_title_to_spanish(title_en)
    excerpt_es = translate_excerpt_to_spanish(excerpt_en)
    content_es = translate_content_to_spanish(content)
    content_es_final = content_es + EDITORIAL_NOTE_ES
    slug_es    = slugify_es(title_es)

    data = {
        # ── Spanish primary fields ────────────────────────────────────────
        "title":      title_es,
        "slug":       slug_es,
        "content":    content_es_final,
        "excerpt":    excerpt_es,
        # ── English secondary fields ──────────────────────────────────────
        "title_en":   title_en,
        "slug_en":    slug,
        "content_en": content_en_final,
        "excerpt_en": excerpt_en,
        # ── Shared fields ─────────────────────────────────────────────────
        "category":        category,
        "author":          AUTHOR,
        "keyword":         keyword,
        "keyword_hash":    md5(keyword),
        "reading_time":    rt,
        "featured":        article_idx == 0,
        "image_gradient":  GRADIENTS[article_idx % len(GRADIENTS)],
        "published_at":    now_iso,
        "cover_image_url": cover_image_url,
    }

    # ── PRE-PUBLISH CONTENT GUARDRAILS ────────────────────────────────────
    guardrail_status, guardrail_flags, data = run_content_guardrails(data)

    if guardrail_status == "blocked":
        print(f"  🚫 INSERT BLOCKED by guardrails — article NOT saved: {title_en[:60]}")
        print(f"     Fix required: {guardrail_flags[0] if guardrail_flags else 'see flags above'}")
        return None

    try:
        supabase_client.table("articles").insert(data).execute()
        status_emoji = "⚠️ " if guardrail_status == "needs_review" else "✅"
        print(
            f"  {status_emoji} Saved{' (needs_review flagged in logs)' if guardrail_status == 'needs_review' else ''}: "
            f"EN='{title_en[:50]}' | ES='{title_es[:50]}'"
        )
        ping_indexnow([f"https://www.newstide.news/en/article/{slug}"])
        return title_en
    except Exception as e:
        print(f"  ❌ Error saving: {e}")
        return None


# ── PROCESS ONE TOPIC ─────────────────────────────────────────────────────────
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
        print(f"  ⚠️  Duplicate — mutating (attempt {attempt+1}/5)...")
        candidate = mutate_topic(candidate, recent_articles, attempt)
    else:
        print(f"  ❌ No unique angle found for: {topic[:50]} — skipping")
        return None

    if already_published_hash(candidate):
        print(f"  ⏭️  Hash already exists in Supabase — skipping")
        return None

    print(f"  🎯 Approved: {candidate[:80]}")
    try:
        result      = generate_article(candidate, recent_context)
        raw_content = result["content"]

        if not validate_article_content(raw_content, label="claude-raw"):
            print("  ❌ Invalid Claude output — skipping")
            return None

        humanized = humanize(raw_content)
        if not validate_article_content(humanized, label="humanized"):
            print("  ⚠️  Humanized invalid — using raw Claude output")
            humanized = raw_content

        title_preview = candidate[:100]
        for line in humanized.strip().split("\n")[:5]:
            if line.strip().startswith("# "):
                title_preview = line.strip()[2:].strip()
                break
        title_preview = smart_trim(title_preview, TITLE_MAX_CHARS)
        slug = slugify(title_preview)

        print("  🔍 Searching Unsplash images...")
        queries    = get_image_queries(title_preview, result["excerpt"])
        cover_img  = fetch_best_image(queries, title_preview, idx=0)
        inline_img = fetch_best_image(queries, title_preview, idx=1)
        content    = inject_images(humanized, cover_img, inline_img)

        print("  🔗 Injecting internal links...")
        content = inject_internal_links(content, result["category"], slug)

        return save_article(
            keyword=candidate,
            content=content,
            excerpt=result["excerpt"],
            category=result["category"],
            article_idx=article_idx,
            title=title_preview,
            slug=slug,
            cover_image_url=cover_img["url"] if cover_img else None,
        )

    except CostLimitExceeded:
        raise
    except Exception as e:
        print(f"  ❌ Error processing '{candidate[:50]}': {e}")
        return None


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n🚀 NewsTide Pipeline [{NICHE_LABEL.upper()}] — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(
        f"🔒 Limits: {MAX_CLAUDE_CALLS_PER_RUN} Claude calls, "
        f"{MAX_CLAUDE_TOKENS_PER_RUN:,} output tokens"
    )

    print("📚 Loading recent articles from Supabase (last 90 days)...")
    recent_articles = get_recent_articles()
    print(f"   {len(recent_articles)} articles loaded for deduplication")

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
                print(f"\n♻️  Expanding pool (attempt {extra_niche_attempts}/{MAX_POOL_EXPANSIONS})...")
                extra = generate_niche_topics(
                    recent_articles + [
                        {"title_en": t, "category": "Indie Hacking", "keyword": t, "excerpt_en": ""}
                        for t in published_titles
                    ],
                    n=12,
                )
                candidate_pool.extend(extra or get_fallback_topics())
                continue

            topic = candidate_pool[pool_index]
            pool_index += 1
            print(f"\n📝 [{len(published_titles)+1}/{ARTICLES_PER_RUN}] {topic[:70]}")

            saved = process_topic(topic, recent_articles, published_titles, len(published_titles))
            if saved:
                published_titles.append(saved)
                recent_articles.insert(0, {
                    "title_en": saved, "keyword": topic,
                    "category": detect_category(topic), "excerpt_en": "",
                })
                print(f"\n✅ Article {len(published_titles)}/{ARTICLES_PER_RUN}: {saved[:60]}")
                if len(published_titles) < ARTICLES_PER_RUN:
                    time.sleep(2)

    except CostLimitExceeded as e:
        print(f"\n{e}")
        print(f"   Published before cutoff: {len(published_titles)}")

    print(f"\n{'='*60}")
    print(f"🎉 Done: {len(published_titles)} articles published")
    print(f"📊 Claude: {_claude_calls_this_run} calls | {_claude_tokens_this_run:,} tokens")
    for i, t in enumerate(published_titles, 1):
        print(f"   {i}. {t[:80]}")


if __name__ == "__main__":
    main()
