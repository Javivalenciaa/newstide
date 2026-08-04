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

# ── SAFETY LIMITS (prevent runaway API costs) ─────────────────────────────────
MAX_CLAUDE_CALLS_PER_RUN   = 12
MAX_CLAUDE_TOKENS_PER_RUN  = 80_000
MAX_POOL_EXPANSIONS        = 4

# Counters reset every run — mutated inside generate_article()
_claude_calls_this_run   = 0
_claude_tokens_this_run  = 0

# ── CONTENT QUALITY LIMITS ────────────────────────────────────────────────────
MIN_READING_TIME = 5
MIN_WORD_COUNT   = MIN_READING_TIME * 200  # 1000 words
MIN_H2_SECTIONS  = 3

# ── TITLE LENGTH CONSTANTS ───────────────────────────────────────────────────
TITLE_MAX_CHARS    = 60
TITLE_SOFT_MIN     = 45
TITLE_SOFT_MAX     = 58

# ── AUTHOR (single, real person) ───────────────────────────────────────────────
AUTHOR      = "Javier Valencia"
AUTHOR_SLUG = "javier-valencia"

openai_client   = OpenAI(api_key=OPENAI_API_KEY)
claude_client   = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

GRADIENTS = [
    "linear-gradient(135deg,#0d2a2e,#0d1a2e)",
    "linear-gradient(135deg,#1a0d2e,#2e0d1a)",
    "linear-gradient(135deg,#2e1a0d,#1a2e0d)",
    "linear-gradient(135deg,#0d2e1a,#0d2e2a)",
    "linear-gradient(135deg,#2e0d0d,#1a0d2e)",
    "linear-gradient(135deg,#0d1a2e,#2e2a0d)",
]

CATEGORIES = {
    "inteligencia artificial": "IA", "machine learning": "IA",
    "chatgpt": "IA", "claude": "IA", "openai": "IA", "llm": "IA",
    "gemini": "IA", "mistral": "IA", "agent": "IA",
    "startup": "Startups", "emprendimiento": "Startups", "financiación": "Startups",
    "inversión": "Startups", "seed": "Startups", "serie a": "Startups",
    "funding": "Startups", "raises": "Startups", "million": "Startups",
    "unicorn": "Startups", "unicornio": "Startups", "valuation": "Startups",
    "herramienta": "Herramientas", "software": "Herramientas", "app": "Herramientas",
    "tutorial": "Tutoriales", "cómo": "Tutoriales", "guía": "Tutoriales",
    "paso a paso": "Tutoriales",
    "noticia": "Noticias", "lanza": "Noticias", "anuncia": "Noticias",
}

# ── EDITORIAL NOTE (EEAT transparency) ───────────────────────────────────────
EDITORIAL_NOTE_ES = """

---

*Nota editorial: Este artículo ha sido elaborado con asistencia de inteligencia artificial y revisado por Javier Valencia. Los datos verificados se distinguen de las opiniones editoriales a lo largo del texto. Las fuentes externas enlazadas son independientes de NewsTide.*
"""

EDITORIAL_NOTE_EN = """

---

*Editorial note: This article was produced with AI assistance and reviewed by Javier Valencia. Verified facts are distinguished from editorial opinion throughout the text. External sources linked are independent of NewsTide.*
"""

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

def slugify(text):
    text = smart_trim(text, 60).lower()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n"),("ü","u")]:
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text.strip())
    return text[:60].strip("-")

def slugify_en(text):
    text = smart_trim(text, 60).lower()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n"),("ü","u"),
                 ("à","a"),("è","e"),("ì","i"),("ò","o"),("ù","u"),("â","a"),("ê","e"),
                 ("î","i"),("ô","o"),("û","u"),("ä","a"),("ë","e"),("ï","i"),("ö","o"),("ç","c")]:
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text.strip())
    return text[:60].strip("-")

def md5(text):
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def detect_category(keyword):
    kw = keyword.lower()
    for key, cat in CATEGORIES.items():
        if key in kw:
            return cat
    return "IA"

def reading_time(text):
    return max(MIN_READING_TIME, round(len(text.split()) / 200))

def already_published_hash(keyword):
    res = supabase_client.table("articles").select("id").eq("keyword_hash", md5(keyword)).execute()
    return len(res.data) > 0

def normalize_publication_date_refs(text: str) -> str:
    """
    SAFE version: only updates 'published in', 'updated in', 'as of', 'en', 'actualizado en'
    date references when they clearly refer to the publication date — NOT historical facts.
    Replaces standalone years only when preceded by publication-context phrases.
    Never rewrites historical references like 'GPT-4 launched in 2023'.
    """
    # Only match years after explicit publication/currency signals
    publication_patterns = [
        (r'(actualizado en|actualizado:)\s*(2023|2024|2025)', r'\1 2026'),
        (r'(updated in|updated:)\s*(2023|2024|2025)', r'\1 2026'),
        (r'(as of)\s*(2023|2024|2025)', r'\1 2026'),
        (r'(\()\s*(2023|2024|2025)\s*(\))', r'\g<1>2026\3'),  # e.g. "(2025 edition)" → "(2026)"
        (r'(\bguía\b.*?)\b(2023|2024|2025)\b', r'\g<1>2026'),
        (r'(\bguide\b.*?)\b(2023|2024|2025)\b', r'\g<1>2026'),
    ]
    for pattern, replacement in publication_patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```(?:markdown|md)?\s*\n', '', text)
    text = re.sub(r'\n```\s*$', '', text)
    return text.strip()

def is_truncated(content_en: str, content_es: str) -> bool:
    stripped = content_en.strip()
    if not stripped:
        return True
    if stripped[0].islower():
        return True
    words_en = len(stripped.split())
    words_es = len(content_es.split())
    if words_es > 0 and words_en < words_es * 0.60:
        return True
    return False

def has_external_link(content: str) -> bool:
    """Verify article contains at least one real external link (not newstide.news)."""
    links = re.findall(r'https?://[^\s\)\"\']+', content)
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
    words = len(content.split())
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
    if not has_external_link(content):
        print(f"  ⚠️  VALIDATION WARN [{label}]: no external link found — EEAT risk")
        # Warning only, not hard fail — some valid articles may not need external links
    if ok:
        print(f"  ✅ VALIDATION OK [{label}]: {words} words, {h2_count} H2 sections")
    return ok

# ── LOAD RECENT ARTICLES ──────────────────────────────────────────────────────
def get_recent_articles() -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    try:
        res = supabase_client.table("articles") \
            .select("title, keyword, category, excerpt") \
            .gte("published_at", since) \
            .order("published_at", desc=True) \
            .limit(60) \
            .execute()
        return res.data or []
    except Exception as e:
        print(f"  ⚠️  Error leyendo Supabase: {e}")
        return []

def format_recent_context(articles: list[dict]) -> str:
    if not articles:
        return "No hay artículos recientes."
    lines = [f"- [{r['category']}] {r['title']}" for r in articles]
    return "\n".join(lines)

# ── SOURCE 1: SERPAPI TRENDING NEWS ──────────────────────────────────────────
def fetch_serpapi_news() -> list[str]:
    queries = [
        "AI startup funding round million 2026",
        "OpenAI Anthropic Claude launch announcement today",
        "AI unicorn valuation Series A Series B 2026",
        "tech startup raises capital AI product news",
        "artificial intelligence company acquisition deal 2026",
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
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                source = r.get("source", "")
                if title and len(title) > 20:
                    # Store source alongside title for EEAT traceability
                    entry = f"{title} — {snippet[:100]}" if snippet else title
                    if source:
                        entry = f"[{source}] {entry}"
                    results.append(entry)
        except Exception as e:
            print(f"  SerpAPI error ({q[:30]}): {e}")
        time.sleep(0.8)
    return results

# ── SOURCE 2: SERPAPI TRENDING SEARCHES ──────────────────────────────────────
def fetch_serpapi_trends() -> list[str]:
    queries = [
        "AI tools developers productivity 2026",
        "best AI startup to watch 2026",
        "AI productivity tools developers founders",
        "LLM comparison GPT Claude Gemini 2026",
        "startup funding news this week AI",
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

# ── SOURCE 3: FUNDING NEWS SPECIFIC ──────────────────────────────────────────
def fetch_funding_news() -> list[str]:
    queries = [
        "AI startup Series A funding 2026 million announced",
        "new AI unicorn valuation 2026",
        "VC investment artificial intelligence startup today",
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
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                source = r.get("source", "")
                if title and len(title) > 20:
                    entry = f"{title} — {snippet[:120]}" if snippet else title
                    if source:
                        entry = f"[{source}] {entry}"
                    results.append(entry)
        except Exception as e:
            print(f"  SerpAPI funding error ({q[:30]}): {e}")
        time.sleep(0.8)
    return results

# ── SOURCE 4: NICHE TOPIC GENERATOR ──────────────────────────────────────────
def generate_niche_topics(recent_articles: list[dict], n: int = 15) -> list[str]:
    recent_titles = "\n".join(f"- {a['title']}" for a in recent_articles[:30])
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Today is {today}. You are editor-in-chief of NewsTide, a premium Spanish-language tech media for founders and developers.

Already published (DO NOT repeat or use similar angle):
{recent_titles if recent_titles else "None yet."}

Generate exactly {n} highly specific article ideas that will rank well on Google Search and be genuinely useful for developers and founders.

EEAT RULES (non-negotiable):
1. Every number, statistic or claim in the title MUST be something Claude can verify or attribute to a real source when writing the article. If you cannot attribute a figure to a real source, do NOT put it in the title.
2. NEVER invent funding amounts, percentages or user counts in titles (e.g. avoid "Cómo ganar 5.000€/mes" — there is no verifiable source for that).
3. Titles must describe something real and specific — not a promise or a fabrication.

TITLE QUALITY RULES:
1. Each idea must mention a REAL, concrete tool/model/company (Claude, Cursor, Supabase, Linear, Vercel, Mistral, Perplexity, n8n, Stripe, etc.)
2. Distribute across these types:
   - 4 ideas: Practical how-to with a clear, real outcome (e.g. "Cómo integrar Claude en tu stack de Supabase sin perder contexto")
   - 4 ideas: Real news analysis — funding, launches, pivots with verifiable events
   - 4 ideas: Direct comparisons between two specific tools with a clear question (e.g. "Cursor vs Copilot: cuál conviene en un equipo de 3 devs")
   - 3 ideas: Evergreen explainers with real depth (e.g. "RAG vs fine-tuning: cuándo usar cada uno según tu caso de uso")
3. Titles must be specific, clear and compelling — they should make a developer or founder want to click because the content sounds useful and credible, not because it sounds dramatic.
4. Use tension and contrast when it reflects something real: "Por qué X falla cuando...", "X vs Y en producción", "El coste real de..."
5. NO invented numbers in titles. NO "gana X€/mes" promises. NO "de la que nadie habla" drama.
6. Write all titles IN SPANISH.

Format: one idea per line, no numbering, no explanation. Just the article title/angle."""

    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.88,
            max_tokens=800,
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        print(f"  🧠 GPT generated {len(lines)} niche ideas")
        return lines[:n]
    except Exception as e:
        print(f"  ⚠️  Error generating niches: {e}")
        return []

# ── SOURCE 5: SAFE FALLBACK TOPICS (no invented stats) ───────────────────────
def get_fallback_topics() -> list[str]:
    """
    Safe fallback topics with no fabricated figures or unverifiable claims.
    All titles describe real, researchable questions — not invented outcomes.
    """
    return [
        "Cursor vs GitHub Copilot: diferencias reales para equipos pequeños",
        "Cómo integrar la API de Claude en un proyecto de Next.js paso a paso",
        "RAG vs fine-tuning: cuándo usar cada enfoque según tu caso de uso",
        "Mistral vs Claude Haiku: comparativa de costes y rendimiento en producción",
        "Cómo Supabase simplifica el backend de startups sin equipo dedicado",
        "n8n vs Zapier vs Make: comparativa real para automatizar flujos de trabajo",
        "Qué es un agente IA y por qué la mayoría falla en producción",
        "Anthropic vs OpenAI: diferencias de política, API y precios en 2026",
        "Cómo construir un pipeline RAG con Supabase y LangChain",
        "Por qué Perplexity está ganando terreno en búsqueda frente a Google",
        "Vercel AI SDK vs LangChain: cuál elegir para tu próximo proyecto",
        "Cómo evaluar el coste real de GPT-4o antes de escalar tu producto",
        "Qué enseña el crecimiento de Linear sobre product-led growth en B2B",
        "Fine-tuning en 2026: cuándo compensa y cuándo es un error costoso",
        "Cómo las startups europeas están compitiendo con modelos abiertos más ligeros",
    ]

# ── DEDUPLICATION ENGINE ──────────────────────────────────────────────────────
def is_duplicate_topic(candidate: str, recent_articles: list[dict], published_this_run: list[str]) -> bool:
    all_existing = [a["title"] for a in recent_articles] + published_this_run
    if not all_existing:
        return False
    existing_str = "\n".join(f"- {t}" for t in all_existing[:40])
    prompt = f"""Candidate article: "{candidate}"

Existing articles:
{existing_str}

Does the candidate cover the SAME specific topic or a very similar angle to any existing article?

Criterion: only a duplicate if it literally covers the same main topic (same tool + same context, or exact same use case). Different tools, different audiences, or different angles are NOT duplicates even if in the same general category.

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
    recent_titles = "\n".join(f"- {a['title']}" for a in recent_articles[:20])
    angles = [
        "un tutorial técnico paso a paso con ejemplos de código real",
        "una comparativa directa entre dos herramientas concretas con un ganador claro según el caso de uso",
        "un análisis de un caso real documentado de una empresa o startup conocida",
        "un error común o limitación técnica real de este tema que pocos explican bien",
        "una comparación de costes reales usando precios públicos de las herramientas",
        "un explainer técnico: cómo funciona por dentro, para desarrolladores",
    ]
    angle = angles[attempt % len(angles)]
    prompt = f"""Tienes este tema: "{original}"

Es demasiado similar a artículos ya publicados:
{recent_titles}

Transfórmalo en un artículo completamente diferente usando este ángulo específico: {angle}

El nuevo tema debe:
- Ser concreto y diferente de los artículos publicados
- Mencionar una herramienta, empresa o caso de uso real
- Tener un título claro y útil para desarrolladores o fundadores — sin números inventados, sin promesas falsas
- Estar escrito EN ESPAÑOL

Responde SOLO con el nuevo título/ángulo (1 línea, máx 120 caracteres)."""
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
    print("🔍 Building candidate pool (5 sources)...")
    pool = []
    print("  📰 Source 1: Daily news — funding & launches (SerpAPI news EN)...")
    news = fetch_serpapi_news()
    print(f"     → {len(news)} headlines fetched")
    pool.extend(news)
    print("  💰 Source 2: Funding-specific news (SerpAPI news EN)...")
    funding = fetch_funding_news()
    print(f"     → {len(funding)} funding stories fetched")
    pool.extend(funding)
    print("  📈 Source 3: Trending searches US (SerpAPI organic)...")
    trends = fetch_serpapi_trends()
    print(f"     → {len(trends)} trends fetched")
    pool.extend(trends)
    print("  🧠 Source 4: Niche ideas — EEAT-compliant (GPT-4o-mini)...")
    niche = generate_niche_topics(recent_articles, n=15)
    print(f"     → {len(niche)} niche ideas generated")
    pool.extend(niche)
    # Safe fallback — no invented stats
    fallback = get_fallback_topics()
    pool.extend(fallback)
    seen = set()
    unique = []
    for p in pool:
        key = p.lower().strip()[:60]
        if key not in seen and len(p) > 20:
            seen.add(key)
            unique.append(normalize_publication_date_refs(p))
    print(f"  ✅ Total pool: {len(unique)} unique candidates")
    return unique

# ── GENERATE ARTICLE WITH CLAUDE ─────────────────────────────────────────────
def generate_article(keyword: str, recent_context: str) -> dict:
    global _claude_calls_this_run, _claude_tokens_this_run
    print(f"  ✍️  Claude generating: {keyword[:70]}...")
    category = detect_category(keyword)
    min_words = MIN_WORD_COUNT
    _check_claude_budget(output_tokens=6000)
    prompt = f"""Escribe un artículo completo EN ESPAÑOL sobre: "{keyword}"

YA PUBLICADO EN NEWSTIDE (no repitas estos temas ni ángulos):
{recent_context}

ESTRUCTURA (usa markdown):
- Título H1: específico, descriptivo y con gancho real (NO el keyword en bruto)
- Párrafo de apertura "answer-first": responde en 2-3 frases directamente la pregunta del título
- 4 o 5 secciones H2 con profundidad y valor real
- Subsecciones H3 donde sea necesario
- Tabla comparativa en Markdown cuando haya datos reales que comparar
- Ejemplos concretos, código real o referencias verificables donde aplique
- Sección FAQ con 3-4 preguntas H3 y respuestas al final
- Conclusión con perspectiva editorial y una pregunta al lector

REGLAS DE EEAT (NO NEGOCIABLES):
1. Toda cifra concreta (€, %, usuarios, parámetros) DEBE atribuirse a una fuente real en el mismo párrafo.
   Formato: "(según [Nombre de la fuente], [año])". Si no tienes la fuente, usa lenguaje cualitativo.
2. NUNCA inventes datos. Si no sabes el dato exacto, escribe "según estimaciones del sector" o "datos no publicados oficialmente".
3. Incluye al menos 1 enlace externo real a una fuente primaria (documentación oficial, blog de la empresa, estudio verificado).
   Usa el formato markdown: [texto del enlace](https://url-real.com)
4. Separa claramente: (a) hechos verificados con fuente, (b) declaraciones atribuidas a alguien, (c) opinión editorial.
5. NO empieces frases con cifras inventadas como "El 80% de los agentes IA fallan" salvo que tengas fuente real.

REQUISITOS DE CONTENIDO:
- MÍNIMO {min_words} palabras (obligatorio — los artículos cortos serán rechazados)
- Objetivo ideal: entre {min_words} y {min_words + 500} palabras
- Tono: experto pero accesible, directo, con criterio propio — no corporativo
- Nunca empieces con "En el mundo de..." ni frases genéricas
- Categoría del artículo: {category}
- El artículo DEBE ofrecer un ángulo diferente a los ya publicados

TÍTULO H1 — REGLAS (CRÍTICO):
- DEBE tener entre {TITLE_SOFT_MIN} y {TITLE_SOFT_MAX} caracteres (contando espacios)
- LÍMITE DURO: nunca superes {TITLE_MAX_CHARS} caracteres
- Debe ser específico, descriptivo y atractivo — que genere curiosidad o resuelva una duda real
- Usa contraste, preguntas, comparaciones o ángulos concretos: "X vs Y", "Por qué X...", "Cómo funciona X en..."
- PROHIBIDO: títulos con números inventados ("gana X€", "el 80%..."), frases de drama vacío o promesas sin base
- Sin comillas en el título
- Cuenta los caracteres antes de escribir — si supera {TITLE_SOFT_MAX}, acórtalo

Al final, en una línea separada escribe exactamente:
EXCERPT: [resumen de 120 a 155 caracteres: describe con precisión qué resuelve el artículo y para quién — claro, útil y con gancho real]"""

    message = claude_client.messages.create(
        model=MODEL_GENERATE, max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
        system=(
            f"Eres un periodista tecnológico senior especializado en IA, startups y herramientas para desarrolladores. "
            f"Escribes para NewsTide, un medio tech premium en ESPAÑOL para fundadores y desarrolladores. "
            f"Tu estilo es claro, directo y con opinión editorial fundamentada. El año actual es 2026. "
            f"REGLA ABSOLUTA: NUNCA inventas datos, cifras o estadísticas. Si no tienes la fuente, usas lenguaje cualitativo. "
            f"Cada artículo debe tener al menos un enlace externo real a una fuente primaria verificable. "
            f"Los artículos deben ser exhaustivos y bien desarrollados — nunca cortos. "
            f"IMPORTANTE: Los títulos H1 deben tener entre {TITLE_SOFT_MIN} y {TITLE_SOFT_MAX} caracteres, "
            f"nunca más de {TITLE_MAX_CHARS}. Títulos específicos y útiles — no dramáticos ni inventados. "
            f"TODOS los artículos deben estar escritos completamente en ESPAÑOL. "
            f"Los excerpts deben describir con precisión qué resuelve el artículo — clickables por utilidad, no por drama."
        )
    )
    output_tokens = message.usage.output_tokens if hasattr(message, 'usage') else 6000
    _register_claude_call(output_tokens)
    raw = message.content[0].text
    excerpt = ""
    if "EXCERPT:" in raw:
        parts = raw.split("EXCERPT:")
        raw = parts[0].strip()
        excerpt = normalize_excerpt(parts[1].strip(), 120, 155)
    return {"content": raw, "excerpt": excerpt, "category": category}

# ── HUMANIZE WITH GPT ─────────────────────────────────────────────────────────
def humanize(text: str) -> str:
    print("  🧠 GPT humanizing...")
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": """Eres un editor humano con 15 años de experiencia en medios digitales en español.
Reescribe el artículo aplicando estas reglas SIN cambiar el contenido, los datos ni las fuentes:
- Mezcla frases cortas (5-8 palabras) con largas (18-28 palabras)
- Usa conectores variados: "sin embargo", "dicho esto", "lo que más me sorprende aquí", "vale la pena señalar", "en la práctica"
- Añade voz editorial puntual: "lo que más llama la atención", "honestamente", "desde mi punto de vista"
- Incluye 1-2 preguntas retóricas naturales
- Simplifica jerga: "fundamental" → "clave", "en conclusión" → "en definitiva", "robusto" → "sólido"
- CRÍTICO: NO añadas ni elimines datos, NO inventes cifras, NO cambies ninguna fuente citada
- IMPORTANTE: Mantén el texto completamente en ESPAÑOL. No traduzcas ni cambies el idioma.
- Conserva todos los encabezados markdown, tablas, FAQs y enlaces externos.
Devuelve SOLO el artículo, sin explicaciones."""},
            {"role": "user", "content": text}
        ],
        temperature=0.85, max_tokens=6000
    )
    return response.choices[0].message.content

# ── TRANSLATE + HUMANIZE EN ───────────────────────────────────────────────────
def _run_translation(es_content: str, es_excerpt: str, es_title: str) -> dict:
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": (
                "You are a professional tech journalist and translator. "
                "Translate the following Spanish tech article to natural, fluent American English. "
                "Keep all markdown formatting, tables, FAQ sections and external links intact. Adapt idioms naturally. "
                f"IMPORTANT: Start your response with exactly these two lines before the article body:\n"
                f"TITLE_EN: [translated H1 title, between {TITLE_SOFT_MIN} and {TITLE_SOFT_MAX} characters, "
                f"NEVER more than {TITLE_MAX_CHARS} characters including spaces, specific and useful, no quotes — "
                f"count the characters before writing, if it exceeds {TITLE_SOFT_MAX} characters shorten it]\n"
                f"EXCERPT_EN: [one sentence summary, 120 to 155 characters, describes what the article resolves and for whom — compelling by utility, not drama]\n"
                "Then a blank line, then the full translated article body (without the H1 title line)."
            )},
            {"role": "user", "content": f"TITLE: {es_title}\nEXCERPT: {es_excerpt}\n\n{es_content}"}
        ],
        temperature=0.75, max_tokens=6000
    )
    raw = response.choices[0].message.content.strip()
    title_en = es_title
    excerpt_en = es_excerpt
    lines = raw.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("TITLE_EN:"):
            title_en = smart_trim(line[len("TITLE_EN:"):].strip(), TITLE_MAX_CHARS)
            body_start = i + 1
        elif line.startswith("EXCERPT_EN:"):
            excerpt_en = normalize_excerpt(line[len("EXCERPT_EN:"):].strip(), 120, 155)
            body_start = i + 1
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1
    content_en = "\n".join(lines[body_start:]).strip()
    content_en = strip_code_fences(content_en)
    slug_en = slugify_en(title_en)
    return {"title_en": title_en, "content_en": content_en, "excerpt_en": excerpt_en, "slug_en": slug_en}

def translate_to_english(es_content: str, es_excerpt: str, es_title: str) -> dict:
    print("  🌐 GPT translating EN...")
    max_attempts = 3
    result = None
    for attempt in range(max_attempts):
        result = _run_translation(es_content, es_excerpt, es_title)
        if not is_truncated(result["content_en"], es_content):
            if attempt > 0:
                print(f"  ✅ Translation correct on attempt {attempt + 1}")
            return result
        print(f"  ⚠️  Truncated translation detected (attempt {attempt + 1}/{max_attempts}) — retrying...")
        time.sleep(2)
    print(f"  ❌ Translation truncated after {max_attempts} attempts — saving last attempt")
    return result

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
            "url": pick["urls"]["regular"],
            "alt": pick.get("alt_description") or query,
            "author": pick["user"]["name"],
            "author_url": pick["user"]["links"]["html"],
        }
    except Exception as e:
        print(f"  Unsplash error: {e}")
        return None

def get_image_queries(title: str, excerpt: str) -> list[str]:
    prompt = (
        f"Article title: {title}\nSummary: {excerpt}\n\n"
        "Give me exactly 3 short English search queries (2-4 words each) to find "
        "relevant, visually appealing Unsplash photos for this tech article. "
        "Queries should be concrete and visual. Reply with ONLY the 3 queries, one per line."
    )
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST, max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        return lines[:3] if lines else ["technology innovation", "digital future", "startup team"]
    except:
        return ["technology innovation", "digital future", "startup team"]

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
        return f"![{alt}]({img['url']})\n*Foto: [{img['author']}]({img['author_url']}) en Unsplash*\n"
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
def fetch_related_articles_en(category: str, current_slug_en: str, limit: int = 15) -> list[dict]:
    try:
        res = (
            supabase_client.table("articles")
            .select("title_en, slug_en, excerpt_en")
            .eq("category", category)
            .not_.is_("slug_en", "null")
            .neq("slug_en", current_slug_en)
            .order("published_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [r for r in (res.data or []) if r.get("slug_en") and r.get("title_en")]
    except Exception as e:
        print(f"  ⚠️  Internal link fetch failed (non-critical): {e}")
        return []

def inject_internal_links(content_en: str, category: str, slug_en: str) -> str:
    related = fetch_related_articles_en(category, slug_en, limit=12)
    if not related:
        print("  ℹ️  No related articles found for internal linking — skipping")
        return content_en
    candidates_str = "\n".join(
        f'- Title: "{r["title_en"]}" | URL: https://www.newstide.news/en/article/{r["slug_en"]}'
        for r in related
    )
    prompt = f"""You are an SEO editor. Your task is to add 2-3 natural internal hyperlinks to the article below.

AVAILABLE INTERNAL LINKS (choose only the most contextually relevant ones):
{candidates_str}

RULES:
1. Insert links ONLY inside paragraph text — never inside headings (lines starting with # or ##).
2. Use the most relevant anchor text already present in the article body.
3. Each link must feel completely natural.
4. Do NOT add more than 3 links total.
5. Do NOT invent URLs. Use ONLY the URLs listed above exactly as written.
6. Do NOT modify any other part of the article.
7. If no natural insertion point exists for a given link, skip it.
8. Return the FULL article with the links inserted. No explanations, no preamble.

ARTICLE:
{content_en}"""
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=6000,
        )
        result = resp.choices[0].message.content.strip()
        result = strip_code_fences(result)
        if len(result) >= len(content_en) * 0.80:
            print(f"  🔗 Internal links injected ({len(related)} candidates available)")
            return result
        else:
            print("  ⚠️  Internal link injection returned truncated content — using original")
            return content_en
    except Exception as e:
        print(f"  ⚠️  Internal link injection failed (non-critical): {e}")
        return content_en

# ── SAVE TO SUPABASE ──────────────────────────────────────────────────────────
def save_article(keyword, content_es, excerpt_es, category, idx, content_en, title_en, excerpt_en, slug_en, cover_image_url=None):
    lines = content_es.strip().split("\n")
    title_es = keyword[:100]
    for line in lines[:5]:
        if line.strip().startswith("# "):
            title_es = line.strip()[2:].strip()
            break
    if lines and lines[0].strip().startswith("# "):
        content_es = "\n".join(lines[1:]).strip()
    en_lines = content_en.strip().split("\n")
    if en_lines and en_lines[0].strip().startswith("# "):
        content_en = "\n".join(en_lines[1:]).strip()
    title_es   = smart_trim(title_es, TITLE_MAX_CHARS)
    title_en   = smart_trim(title_en or title_es, TITLE_MAX_CHARS)
    excerpt_es = normalize_excerpt(excerpt_es or title_es[:150], 120, 155)
    excerpt_en = normalize_excerpt(excerpt_en or excerpt_es or title_es[:150], 120, 155)
    rt = reading_time(content_es)
    if rt < MIN_READING_TIME:
        print(f"  ⚠️  reading_time={rt} < {MIN_READING_TIME} — forcing to {MIN_READING_TIME}")
        rt = MIN_READING_TIME
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    slug_es = slugify(title_es)

    # Append editorial transparency notes
    content_es_final = content_es + EDITORIAL_NOTE_ES
    content_en_final = content_en + EDITORIAL_NOTE_EN

    data = {
        "title":           title_es,
        "slug":            slug_es,
        "content":         content_es_final,
        "excerpt":         excerpt_es,
        "title_en":        title_en,
        "slug_en":         slug_en or slugify_en(title_en),
        "content_en":      content_en_final,
        "excerpt_en":      excerpt_en,
        "category":        category,
        "author":          AUTHOR,
        "keyword":         keyword,
        "keyword_hash":    md5(keyword),
        "reading_time":    rt,
        "featured":        idx == 0,
        "image_gradient":  GRADIENTS[idx % len(GRADIENTS)],
        "published_at":    now_iso,
        "cover_image_url": cover_image_url,
    }
    try:
        supabase_client.table("articles").insert(data).execute()
        print(f"  ✅ Saved: {title_es[:70]}")
        final_slug_en = slug_en or slugify_en(title_en)
        ping_indexnow([f"https://www.newstide.news/en/article/{final_slug_en}"])
        return title_es
    except Exception as e:
        print(f"  ❌ Error saving: {e}")
        return None

# ── PROCESS ONE TOPIC → ARTICLE ───────────────────────────────────────────────
def process_topic(topic: str, recent_articles: list[dict], published_this_run: list[str], article_idx: int) -> str | None:
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
        if not validate_article_content(humanized, label="humanized-es"):
            print(f"  ⚠️  Humanized invalid — using original Claude content")
            humanized = raw_content
        title_preview = candidate[:100]
        for line in humanized.strip().split("\n")[:5]:
            if line.strip().startswith("# "):
                title_preview = line.strip()[2:].strip()
                break
        print("  🔍 Searching Unsplash images...")
        queries    = get_image_queries(title_preview, result["excerpt"])
        cover_img  = fetch_best_image(queries, title_preview, idx=0)
        inline_img = fetch_best_image(queries, title_preview, idx=1)
        content_es = inject_images(humanized, cover_img, inline_img)
        cover_image_url = cover_img["url"] if cover_img else None
        en = translate_to_english(content_es, result["excerpt"], title_preview)
        if not validate_article_content(en["content_en"], label="translated-en"):
            print(f"  ⚠️  EN translation invalid after retries — saving anyway, review manually")
        print("  🔗 Injecting internal links (EN)...")
        en["content_en"] = inject_internal_links(
            en["content_en"], result["category"], en["slug_en"]
        )
        saved_title = save_article(
            candidate, content_es, result["excerpt"], result["category"],
            article_idx, en["content_en"], en["title_en"], en["excerpt_en"],
            en["slug_en"],
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
    print(f"\n🚀 NewsTide Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(
        f"🔒 Safety limits: "
        f"max {MAX_CLAUDE_CALLS_PER_RUN} Claude calls, "
        f"max {MAX_CLAUDE_TOKENS_PER_RUN:,} output tokens, "
        f"max {MAX_POOL_EXPANSIONS} pool expansions"
    )
    print("📚 Loading recent articles from Supabase...")
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
                    recent_articles + [{"title": t, "category": "IA", "keyword": t, "excerpt": ""} for t in published_titles],
                    n=10
                )
                candidate_pool.extend(extra)
                if not extra:
                    # Safe fallback only — no pool expansion with fake stats
                    print("  ⚠️  GPT niche generation returned empty — using safe fallback topics")
                    candidate_pool.extend(get_fallback_topics())
                continue
            topic = candidate_pool[pool_index]
            pool_index += 1
            print(f"\n📝 [{len(published_titles)+1}/{ARTICLES_PER_RUN}] Processing: {topic[:70]}")
            saved = process_topic(
                topic, recent_articles, published_titles,
                article_idx=len(published_titles)
            )
            if saved:
                published_titles.append(saved)
                recent_articles.insert(0, {
                    "title": saved, "keyword": topic,
                    "category": detect_category(topic), "excerpt": ""
                })
                print(f"\n✅ Article {len(published_titles)}/{ARTICLES_PER_RUN} published: {saved[:60]}")
                if len(published_titles) < ARTICLES_PER_RUN:
                    print("   Continuing with next...\n")
                time.sleep(2)
    except CostLimitExceeded as e:
        print(f"\n{e}")
        print(f"   Articles published before cutoff: {len(published_titles)}")
    print(f"\n{'='*60}")
    print(f"🎉 Pipeline finished: {len(published_titles)} articles published")
    print(f"📊 Total Claude calls: {_claude_calls_this_run} | Output tokens: {_claude_tokens_this_run:,}")
    for i, t in enumerate(published_titles, 1):
        print(f"   {i}. {t[:80]}")

if __name__ == "__main__":
    main()
