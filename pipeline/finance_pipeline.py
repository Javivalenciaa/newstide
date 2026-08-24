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

# GSC is optional — pipeline runs fine if the env var is not set
GSC_SITE_URL = os.environ.get("GSC_SITE_URL", "sc-domain:newstide.news")

# ── NICHE DEFINITION ──────────────────────────────────────────────────────────
NICHE_LABEL  = "finanzas personales hispanos USA"
SITE_LANG    = "es"
AUTHOR       = "Javier Valencia"

ARTICLES_PER_RUN  = 3
MODEL_GENERATE    = "claude-sonnet-4-5"
MODEL_FAST        = "gpt-4o-mini"
MODEL_HUMANIZE    = "gpt-4o"

# ── SAFETY LIMITS ─────────────────────────────────────────────────────────────
MAX_CLAUDE_CALLS_PER_RUN  = 12
MAX_CLAUDE_TOKENS_PER_RUN = 80_000
MAX_POOL_EXPANSIONS       = 4

_claude_calls_this_run  = 0
_claude_tokens_this_run = 0

# ── CONTENT QUALITY LIMITS ────────────────────────────────────────────────────
# YMYL content (personal finance) requires longer, more thorough articles
MIN_READING_TIME            = 10
MIN_WORD_COUNT              = MIN_READING_TIME * 200   # 2000 words minimum
MIN_H2_SECTIONS             = 3
TOPIC_CLUSTER_COOLDOWN_DAYS = 14   # same cluster can't publish twice in 14 days

# ── TITLE LENGTH CONSTANTS ────────────────────────────────────────────────────
TITLE_MAX_CHARS = 75
TITLE_SOFT_MIN  = 55
TITLE_SOFT_MAX  = 70

# ── CATEGORIES ────────────────────────────────────────────────────────────────
FIN_CATEGORIES = {
    "crédito":        "Crédito",
    "credit":         "Crédito",
    "score":          "Crédito",
    "historial":      "Crédito",
    "tarjeta":        "Crédito",
    "itin":           "Impuestos",
    "taxes":          "Impuestos",
    "impuesto":       "Impuestos",
    "declaración":    "Impuestos",
    "tax":            "Impuestos",
    "ahorrar":        "Ahorro",
    "ahorro":         "Ahorro",
    "emergency fund": "Ahorro",
    "fondo":          "Ahorro",
    "presupuesto":    "Presupuesto",
    "budget":         "Presupuesto",
    "gastos":         "Presupuesto",
    "invertir":       "Inversión",
    "inversión":      "Inversión",
    "bolsa":          "Inversión",
    "etf":            "Inversión",
    "roth":           "Inversión",
    "401k":           "Inversión",
    "remesa":         "Remesas",
    "enviar dinero":  "Remesas",
    "transferencia":  "Remesas",
    "deuda":          "Deudas",
    "debt":           "Deudas",
    "préstamo":       "Deudas",
    "loan":           "Deudas",
    "hipoteca":       "Vivienda",
    "renta":          "Vivienda",
    "apartamento":    "Vivienda",
    "trabajo":        "Ingresos Extra",
    "freelance":      "Ingresos Extra",
    "ganar dinero":   "Ingresos Extra",
    "side hustle":    "Ingresos Extra",
}

GRADIENTS = [
    "linear-gradient(135deg,#0d2a1a,#0d1a0a)",
    "linear-gradient(135deg,#1a2e0d,#0d2e1a)",
    "linear-gradient(135deg,#0a2e0d,#1a2a0d)",
    "linear-gradient(135deg,#0d2e0a,#0a1a0d)",
    "linear-gradient(135deg,#1a2e15,#0d2a0d)",
    "linear-gradient(135deg,#0d1a0a,#1a2e10)",
]

FINANCE_DISCLAIMER_ES = """

---

*Aviso legal: Este artículo es solo para fines informativos y educativos. No constituye asesoramiento financiero ni una recomendación de compra o venta de ningún producto financiero. Consulta con un asesor financiero certificado antes de tomar decisiones económicas importantes. Los resultados pasados no garantizan resultados futuros.*
"""

EDITORIAL_NOTE_ES = """

---

*Nota editorial: Este artículo ha sido elaborado con asistencia de inteligencia artificial y supervisado por Javier Valencia, fundador de NewsTide e Ingeniero Informático. Los datos verificados se distinguen de las opiniones editoriales a lo largo del texto. Las fuentes externas enlazadas son independientes de NewsTide.*
"""

INDEXNOW_KEY     = "964bf589528b466cace60749e05cfcb6"
INDEXNOW_HOST    = "www.newstide.news"
INDEXNOW_KEY_LOC = f"https://{INDEXNOW_HOST}/{INDEXNOW_KEY}.txt"

# Finance articles are served at /es/fin/<slug>
FINANCE_URL_PREFIX = f"https://{INDEXNOW_HOST}/es/fin"

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
    """Trim text to at most `limit` chars, cutting only at a word boundary.
    Used as a LAST-RESORT safety net — do NOT call this on titles before the
    LLM has had a chance to produce a complete sentence."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= limit:
        return text
    cut = text[:limit + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.strip(" -:;,.")


def normalize_excerpt(text: str, min_len: int = 120, max_len: int = 155) -> str:
    text = re.sub(r'^\*+\s*', '', (text or '').strip())
    text = re.sub(r"\s+", " ", text)
    text = text.strip(' "\'')
    if len(text) <= max_len:
        return text
    cut = text[:max_len + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.strip(" -:;,.") + "."


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug. Cap at 75 chars AFTER slugification."""
    text = text.lower()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n"),("ü","u")]:
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text.strip())
    if len(text) > 75:
        cut = text[:76]
        if "-" in cut:
            cut = cut.rsplit("-", 1)[0]
        text = cut
    return text.strip("-")


def fix_double_quotes(text: str) -> str:
    return text.replace('""', '"')


def md5(text: str) -> str:
    return hashlib.md5(text.lower().strip().encode()).hexdigest()


def detect_category(keyword: str) -> str:
    kw = keyword.lower()
    for key, cat in FIN_CATEGORIES.items():
        if key in kw:
            return cat
    return "Ahorro"


def reading_time(text: str) -> int:
    return max(MIN_READING_TIME, round(len(text.split()) / 200))


def strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```(?:markdown|md)?\s*\n', '', text)
    text = re.sub(r'\n```\s*$', '', text)
    return text.strip()


def has_external_link(content: str) -> bool:
    links = re.findall(r'https?://[^\s\)\"\' ]+', content)
    for link in links:
        if "newstide.news" not in link and "unsplash.com" not in link:
            return True
    return False


def clean_serp_candidate(text: str) -> str:
    text = re.sub(r'^\[[^\]]+\]\s*', '', (text or '').strip())
    text = re.sub(r'\s*—\s*.{0,120}$', '', text).strip()
    return re.sub(r"\s+", " ", text).strip()


def topic_cluster_key(text: str) -> str:
    stop = {"2026","2025","guia","guía","mejores","mejor","como","cómo",
            "paso","vs","en","de","la","el","los","las","para","que","con",
            "sin","por","una","uno","tu","su","usa","estados","unidos"}
    base = slugify(text)
    tokens = [t for t in base.split('-') if len(t) > 2 and t not in stop]
    return '-'.join(tokens[:5])


def topic_cluster_on_cooldown(
    candidate: str,
    recent_articles: list[dict],
    published_this_run: list[str],
) -> bool:
    cand_key = topic_cluster_key(candidate)
    if not cand_key:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=TOPIC_CLUSTER_COOLDOWN_DAYS)
    for article in recent_articles:
        title = article.get("title") or article.get("keyword", "")
        if topic_cluster_key(title) != cand_key:
            continue
        pub = article.get("published_at")
        if not pub:
            return True
        try:
            dt = datetime.fromisoformat(str(pub).replace('Z', '+00:00'))
            if dt >= cutoff:
                return True
        except Exception:
            return True
    for title in published_this_run:
        if topic_cluster_key(title) == cand_key:
            return True
    return False


# ── COST GUARD ────────────────────────────────────────────────────────────────
class CostLimitExceeded(Exception):
    pass


def _check_claude_budget(output_tokens: int = 0) -> None:
    global _claude_calls_this_run, _claude_tokens_this_run
    if _claude_calls_this_run >= MAX_CLAUDE_CALLS_PER_RUN:
        raise CostLimitExceeded(f"🛑 COST LIMIT: reached {MAX_CLAUDE_CALLS_PER_RUN} Claude calls — aborting.")
    if _claude_tokens_this_run + output_tokens > MAX_CLAUDE_TOKENS_PER_RUN:
        raise CostLimitExceeded(f"🛑 COST LIMIT: tokens would exceed {MAX_CLAUDE_TOKENS_PER_RUN:,} — aborting.")


def _register_claude_call(output_tokens: int) -> None:
    global _claude_calls_this_run, _claude_tokens_this_run
    _claude_calls_this_run  += 1
    _claude_tokens_this_run += output_tokens
    print(f"  📊 Claude: {_claude_calls_this_run}/{MAX_CLAUDE_CALLS_PER_RUN} calls, {_claude_tokens_this_run:,}/{MAX_CLAUDE_TOKENS_PER_RUN:,} tokens")


# ── CONTENT VALIDATION ────────────────────────────────────────────────────────
def validate_article_content(content: str, label: str = "article") -> bool:
    words    = len(content.split())
    h2_count = len(re.findall(r'^#{2,3} ', content, re.MULTILINE))
    ok = True
    if words < MIN_WORD_COUNT:
        print(f"  ❌ VALIDATION FAIL [{label}]: {words} words < {MIN_WORD_COUNT}")
        ok = False
    if h2_count < MIN_H2_SECTIONS:
        print(f"  ❌ VALIDATION FAIL [{label}]: {h2_count} H2/H3 (need >= {MIN_H2_SECTIONS})")
        ok = False
    stripped = content.strip()
    if not stripped.startswith("#") and len(stripped) > 0 and stripped[0].islower():
        print(f"  ❌ VALIDATION FAIL [{label}]: starts mid-sentence (truncation)")
        ok = False
    if content.rstrip().endswith("..."):
        print(f"  ❌ VALIDATION FAIL [{label}]: content ends with '...' — likely truncated")
        ok = False
    if not has_external_link(content):
        print(f"  ⚠️  VALIDATION WARN [{label}]: no external link — EEAT risk")
    if ok:
        print(f"  ✅ VALIDATION OK [{label}]: {words} words, {h2_count} H2/H3 sections")
    return ok


# ── LOAD RECENT ARTICLES (BOTH TABLES) ───────────────────────────────────────
def get_recent_articles() -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=180)).isoformat()
    combined: list[dict] = []
    for table in ("finance_articles", "articles"):
        try:
            res = (
                supabase_client.table(table)
                .select("title, keyword, category, excerpt, published_at")
                .gte("published_at", since)
                .order("published_at", desc=True)
                .limit(300)
                .execute()
            )
            combined.extend(res.data or [])
            print(f"  📚 {table}: {len(res.data or [])} articles loaded")
        except Exception as e:
            print(f"  ⚠️  Error reading {table}: {e}")
    print(f"  📊 Total dedup context: {len(combined)} articles")
    return combined


def format_recent_context(articles: list[dict]) -> str:
    if not articles:
        return "No hay artículos publicados todavía."
    return "\n".join(
        f"- [{r.get('category','?')}] {r.get('title') or r.get('keyword','')}"
        for r in articles[:120]
    )


def already_published_hash(keyword: str) -> bool:
    clean = slugify(clean_serp_candidate(keyword))
    hashes = list({md5(keyword), md5(clean)})
    for table in ("finance_articles", "articles"):
        try:
            res = supabase_client.table(table).select("id").in_("keyword_hash", hashes).execute()
            if res.data:
                return True
        except Exception:
            pass
    return False


# ── GSC: FETCH HIGH-OPPORTUNITY QUERIES ──────────────────────────────────────
# Pulls queries where the finance site already has impressions but low CTR
# (position 4-20) — easy wins for the content pipeline.
# Requires GOOGLE_APPLICATION_CREDENTIALS env var pointing to a service-account
# JSON file with Search Console read access, OR a valid access token via
# GOOGLE_ACCESS_TOKEN. Silently skips if credentials are not available.

def fetch_gsc_queries(
    site_url: str = GSC_SITE_URL,
    days_back: int = 28,
    row_limit: int = 50,
) -> list[str]:
    """
    Returns a list of query strings from GSC where:
      - page matches /es/fin/ (finance section)
      - average position between 4 and 20 (quick-win territory)
      - at least 30 impressions in the last `days_back` days

    Falls back to [] silently if credentials or API are unavailable.
    """
    access_token = os.environ.get("GOOGLE_ACCESS_TOKEN", "")
    credentials_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    if not access_token and not credentials_file:
        print("  ℹ️  GSC: no credentials set — skipping GSC source")
        return []

    # ── Obtain a bearer token ─────────────────────────────────────────────
    if not access_token and credentials_file:
        try:
            import google.oauth2.service_account as sa
            import google.auth.transport.requests as ga_requests
            creds = sa.Credentials.from_service_account_file(
                credentials_file,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
            )
            creds.refresh(ga_requests.Request())
            access_token = creds.token
        except Exception as e:
            print(f"  ⚠️  GSC: could not obtain service-account token: {e}")
            return []

    end_date   = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days_back)

    payload = {
        "startDate":  str(start_date),
        "endDate":    str(end_date),
        "dimensions": ["query"],
        "dimensionFilterGroups": [{
            "filters": [{
                "dimension":  "page",
                "operator":   "contains",
                "expression": "/es/fin/",
            }]
        }],
        "rowLimit": row_limit,
        "startRow": 0,
    }

    try:
        resp = requests.post(
            f"https://searchconsole.googleapis.com/webmasters/v3/sites/{requests.utils.quote(site_url, safe='')}/searchAnalytics/query",
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type":  "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        rows = resp.json().get("rows", [])
    except Exception as e:
        print(f"  ⚠️  GSC API error: {e}")
        return []

    # Filter: position 4-20 AND at least 30 impressions
    candidates = []
    for row in rows:
        position    = row.get("position", 0)
        impressions = row.get("impressions", 0)
        query       = (row.get("keys") or [""])[0].strip()
        if query and 4 <= position <= 20 and impressions >= 30:
            candidates.append(query)

    print(f"  📊 GSC: {len(candidates)} finance queries in positions 4-20 (≥30 impressions)")
    return candidates


# ── SERPAPI SOURCES ────────────────────────────────────────────────────────────
def fetch_serpapi_hispano_news() -> list[str]:
    queries = [
        "cómo construir crédito sin historial en USA 2026",
        "cómo ahorrar dinero con sueldo mínimo en Estados Unidos",
        "cómo enviar remesas a México de forma más barata 2026",
        "cómo declarar impuestos con ITIN en USA 2026",
        "mejores aplicaciones para ahorrar dinero hispanos USA",
    ]
    results = []
    for q in queries:
        try:
            params = {"q": q, "tbm": "nws", "hl": "es", "gl": "us", "api_key": SERPAPI_KEY, "num": 5}
            data = GoogleSearch(params).get_dict()
            for r in data.get("news_results", data.get("organic_results", []))[:4]:
                title = clean_serp_candidate(r.get("title", ""))
                snippet = r.get("snippet", "")
                if title and len(title) > 20:
                    results.append(f"{title} — {snippet[:100]}" if snippet else title)
        except Exception as e:
            print(f"  SerpAPI hispano-news error ({q[:40]}): {e}")
        time.sleep(0.8)
    return results


def fetch_serpapi_credit_saving() -> list[str]:
    queries = [
        "tarjetas de crédito para inmigrantes sin Social Security USA",
        "cómo subir el credit score rápido en Estados Unidos",
        "cómo abrir cuenta bancaria sin documentos USA 2026",
        "mejores bancos para hispanos en Estados Unidos 2026",
        "cómo hacer un presupuesto familiar en USA con poco dinero",
    ]
    results = []
    for q in queries:
        try:
            params = {"q": q, "hl": "es", "gl": "us", "api_key": SERPAPI_KEY, "num": 5}
            data = GoogleSearch(params).get_dict()
            for r in data.get("organic_results", [])[:3]:
                title = clean_serp_candidate(r.get("title", ""))
                if title and len(title) > 20:
                    results.append(title)
        except Exception as e:
            print(f"  SerpAPI credit-saving error: {e}")
        time.sleep(0.8)
    return results


def fetch_serpapi_inversion_impuestos() -> list[str]:
    queries = [
        "cómo invertir en bolsa siendo inmigrante en USA 2026",
        "Roth IRA para hispanos en Estados Unidos explicado",
        "cómo declarar taxes freelance hispano USA 2026",
        "mejores apps para invertir con poco dinero en USA",
        "cómo comprar casa siendo inmigrante en Estados Unidos",
    ]
    results = []
    for q in queries:
        try:
            params = {"q": q, "tbm": "nws", "hl": "es", "gl": "us", "api_key": SERPAPI_KEY, "num": 5}
            data = GoogleSearch(params).get_dict()
            for r in data.get("news_results", data.get("organic_results", []))[:4]:
                title = clean_serp_candidate(r.get("title", ""))
                snippet = r.get("snippet", "")
                if title and len(title) > 20:
                    results.append(f"{title} — {snippet[:100]}" if snippet else title)
        except Exception as e:
            print(f"  SerpAPI inversión error: {e}")
        time.sleep(0.8)
    return results


# ── GPT NICHE TOPIC GENERATOR ─────────────────────────────────────────────────
def generate_niche_topics(recent_articles: list[dict], n: int = 18) -> list[str]:
    recent_titles = "\n".join(
        f"- {a.get('title') or a.get('keyword', '')}" for a in recent_articles[:60]
    )
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Hoy es {today}. Eres editor jefe de NewsTide Finanzas, un medio EN ESPAÑOL para hispanos en USA.

YA PUBLICADO (NO repetir ni usar ángulo similar):
{recent_titles if recent_titles else "Nada todavía."}

Genera exactamente {n} ideas de artículo que rankeen bien en Google.
- Productos y leyes AMERICANAS reales.
- Sin números inventados en el título.
- Todo en ESPAÑOL.
- Cada título debe ser una frase COMPLETA entre {TITLE_SOFT_MIN} y {TITLE_SOFT_MAX} caracteres.
- NUNCA cortes un título a la mitad. NUNCA uses puntos suspensivos.

Formato: un título por línea, sin numeración, sin explicación."""
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.90,
            max_tokens=900,
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        return lines[:n]
    except Exception as e:
        print(f"  ⚠️  Error generando temas: {e}")
        return []


def get_fallback_topics() -> list[str]:
    return [
        "Cómo construir crédito en USA sin historial crediticio desde cero",
        "Tarjetas de crédito para inmigrantes sin Social Security en USA",
        "Cómo declarar impuestos con ITIN en Estados Unidos paso a paso",
        "Wise vs Remitly: cuál conviene para enviar dinero a México en 2026",
        "Cómo abrir cuenta bancaria sin documentos en USA en 2026",
        "Roth IRA explicado para hispanos que viven en Estados Unidos",
        "Cómo subir tu credit score en USA sin endeudarte en 2026",
        "Mejores bancos para hispanos en Estados Unidos en 2026",
        "Cómo hacer un presupuesto familiar viviendo en USA con poco dinero",
        "Cómo invertir en bolsa siendo inmigrante en América sin experiencia",
        "Chime vs Bank of America: cuál es mejor para hispanos en USA",
        "Cómo comprar casa siendo inmigrante en Estados Unidos con ITIN",
        "Qué es el ITIN y para qué sirve en Estados Unidos en 2026",
        "Mejores apps para ahorrar dinero en Estados Unidos este año",
        "Cómo enviar remesas baratas desde USA a Latinoamérica en 2026",
        "Deudas médicas en USA: derechos que tienes como hispano residente",
        "Cómo funciona el 401k explicado en español para trabajadores en USA",
        "Cómo salir de deudas de tarjeta de crédito en USA sin arruinarte",
    ]


# ── DEDUPLICATION ─────────────────────────────────────────────────────────────
def is_duplicate_topic(
    candidate: str, recent_articles: list[dict], published_this_run: list[str]
) -> bool:
    if topic_cluster_on_cooldown(candidate, recent_articles, published_this_run):
        print(f"  🕐 Cluster cooldown hit: {candidate[:60]}")
        return True

    all_existing = [
        a.get("title") or a.get("keyword", "") for a in recent_articles
    ] + published_this_run
    if not all_existing:
        return False

    existing_str = "\n".join(f"- {t}" for t in all_existing[:60] if t)
    prompt = f"""Artículo candidato: "{candidate}"

Artículos ya publicados:
{existing_str}

¿El candidato cubre EL MISMO tema específico o un ángulo muy similar?
Solo YES si: mismo producto principal Y mismo caso de uso.
Responde SOLO: YES o NO"""
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5,
        )
        return resp.choices[0].message.content.strip().upper().startswith("YES")
    except Exception:
        return False


def mutate_topic(original: str, recent_articles: list[dict], attempt: int) -> str:
    recent_titles = "\n".join(
        f"- {a.get('title') or a.get('keyword', '')}" for a in recent_articles[:25]
    )
    angles = [
        "una guía paso a paso con ejemplos reales de productos americanos",
        "una comparativa directa entre dos herramientas concretas disponibles en USA",
        "el error más común que cometen los hispanos con este tema financiero y cómo evitarlo",
        "un enfoque para alguien que acaba de llegar a USA y no sabe por dónde empezar",
    ]
    angle = angles[attempt % len(angles)]
    prompt = f"""Tienes este tema: "{original}"

Es demasiado similar a los ya publicados:
{recent_titles}

Transfórmalo usando este ángulo: {angle}
El nuevo título debe ser una frase COMPLETA entre {TITLE_SOFT_MIN} y {TITLE_SOFT_MAX} caracteres.
NUNCA cortes a la mitad. NUNCA uses puntos suspensivos.
Responde SOLO con el nuevo título (1 línea)."""
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            max_tokens=80,
        )
        mutated = clean_serp_candidate(resp.choices[0].message.content.strip().strip('"').strip("'"))
        print(f"  🔄 Mutado (intento {attempt+1}): {mutated[:70]}")
        return mutated if len(mutated) > 15 else original
    except Exception:
        return original


# ── BUILD CANDIDATE POOL ──────────────────────────────────────────────────────
def build_candidate_pool(recent_articles: list[dict]) -> list[str]:
    print("🔍 Construyendo pool de candidatos finanzas...")
    pool = []

    print("  📰 Source 1: Noticias hispanas (SerpAPI)...")
    pool.extend(fetch_serpapi_hispano_news())

    print("  💳 Source 2: Crédito y ahorro (SerpAPI)...")
    pool.extend(fetch_serpapi_credit_saving())

    print("  📈 Source 3: Inversión e impuestos (SerpAPI)...")
    pool.extend(fetch_serpapi_inversion_impuestos())

    print("  📊 Source 4: GSC quick-wins (posiciones 4-20 en /es/fin/)...")
    gsc_queries = fetch_gsc_queries()
    if gsc_queries:
        pool.extend(gsc_queries)
        print(f"  ✅ GSC aportó {len(gsc_queries)} queries al pool")
    else:
        print("  ℹ️  GSC sin datos — continuando sin esa fuente")

    print("  🧠 Source 5: Temas GPT (niche)...")
    pool.extend(generate_niche_topics(recent_articles, n=18))

    pool.extend(get_fallback_topics())

    seen, unique = set(), []
    for p in pool:
        cleaned = clean_serp_candidate(p)
        key = cleaned.lower().strip()[:60]
        if key not in seen and len(cleaned) > 20:
            seen.add(key)
            unique.append(cleaned)

    print(f"  ✅ Pool: {len(unique)} candidatos únicos")
    return unique


# ── GENERATE ARTICLE WITH CLAUDE ──────────────────────────────────────────────
def generate_article(keyword: str, recent_context: str) -> dict:
    category = detect_category(keyword)
    _check_claude_budget(output_tokens=8000)

    prompt = f"""Escribe un artículo completo EN ESPAÑOL sobre finanzas personales para hispanos en USA: "{keyword}"

YA PUBLICADO — no repetir estos temas ni ángulos:
{recent_context}

ESTE ES YMYL — sigue E-E-A-T estrictamente.
- Toda cifra o dato DEBE citar fuente real inline.
- Incluye al menos 2 enlaces externos reales a fuentes primarias americanas.
- MÍNIMO {MIN_WORD_COUNT} palabras.
- 4-5 H2 y FAQ con 3-4 H3.
- Sección honesta "Cuándo esto NO funciona".
- Todo en ESPAÑOL.
- El H1 del artículo DEBE ser una frase completa entre {TITLE_SOFT_MIN} y {TITLE_SOFT_MAX} caracteres. NUNCA lo cortes a la mitad. NUNCA uses puntos suspensivos en el título.
- Al final escribe: EXCERPT: [120 a 155 caracteres en español]"""

    message = claude_client.messages.create(
        model=MODEL_GENERATE,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
        system=(
            f"Eres un periodista financiero senior para hispanos en USA. "
            f"Nunca inventas datos. Todas las leyes y productos son americanos. "
            f"REGLA DE TÍTULOS: el H1 debe tener entre {TITLE_SOFT_MIN} y {TITLE_SOFT_MAX} caracteres. "
            f"NUNCA cortes un título a la mitad. NUNCA uses puntos suspensivos en ningún título. "
            f"El título DEBE ser siempre una oración o frase nominal COMPLETA con sentido propio. "
            f"REGLA DE CONTENIDO: NUNCA uses '...' dentro del cuerpo del artículo para indicar que hay más texto. "
            f"Si una sección queda incompleta, complétala o elimínala. El artículo debe terminar con una conclusión o sección final completa."
        ),
    )
    output_tokens = message.usage.output_tokens if hasattr(message, "usage") else 8000
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
    print("  🧠 GPT humanizando...")
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": (
                "Reescribe el artículo en español con estilo humano y natural. "
                "NO cambies datos, cifras ni fuentes. "
                "Mantén todos los encabezados markdown, tablas, FAQs y enlaces externos. "
                "NUNCA uses puntos suspensivos '...' en el cuerpo del artículo. "
                "NUNCA cortes secciones a la mitad — si una sección empieza, termínala completamente."
            )},
            {"role": "user", "content": text}
        ],
        temperature=0.85,
        max_tokens=8000,
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
        f"Título: {title}\nResumen: {excerpt}\n\n"
        "Dame 3 búsquedas cortas en INGLÉS (2-4 palabras) para fotos de Unsplash. "
        "Las búsquedas deben ser MUY específicas al tema del artículo, no genéricas. "
        "Responde SOLO con las 3 búsquedas, una por línea."
    )
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST, max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        return lines[:3] if lines else ["family budget planning", "personal finance money", "credit card wallet"]
    except Exception:
        return ["family budget planning", "personal finance money", "credit card wallet"]


def fetch_best_image(queries: list[str], title: str, idx: int = 0) -> dict | None:
    for query in queries:
        img = get_unsplash_image(query, idx=idx)
        if img:
            print(f"  🖼️  Imagen: '{query}' → {img['author']}")
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
def fetch_related_articles(category: str, current_slug: str, limit: int = 12) -> list[dict]:
    try:
        res = (
            supabase_client.table("finance_articles")
            .select("title, slug, excerpt")
            .eq("category", category)
            .not_.is_("slug", "null")
            .neq("slug", current_slug)
            .order("published_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [r for r in (res.data or []) if r.get("slug") and r.get("title")]
    except Exception as e:
        print(f"  ⚠️  Internal link fetch failed: {e}")
        return []


def inject_internal_links(content: str, category: str, slug: str) -> str:
    related = fetch_related_articles(category, slug, limit=12)
    if not related:
        return content
    candidates_str = "\n".join(
        f'- Título: "{r["title"]}" | URL: {FINANCE_URL_PREFIX}/{r["slug"]}'
        for r in related
    )
    prompt = f"""Añade 2-3 enlaces internos naturales al artículo.

ENLACES DISPONIBLES:
{candidates_str}

REGLAS:
1. Inserta solo dentro de párrafos, nunca en encabezados.
2. Máximo 3 enlaces. Usa solo las URLs listadas.
3. Devuelve el ARTÍCULO COMPLETO con enlaces insertados. Sin explicaciones.
4. NUNCA uses puntos suspensivos '...' ni cortes el contenido.

ARTÍCULO:
{content}"""
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=8000,
        )
        result = strip_code_fences(resp.choices[0].message.content.strip())
        if len(result) >= len(content) * 0.80:
            print(f"  🔗 Internal links injected ({len(related)} candidates)")
            return result
        return content
    except Exception as e:
        print(f"  ⚠️  Internal link injection failed: {e}")
        return content


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

    title = smart_trim(title, TITLE_MAX_CHARS)
    content = fix_double_quotes(content)
    clean_keyword = slugify(clean_serp_candidate(keyword))
    excerpt = normalize_excerpt(excerpt or title[:150], 120, 155)
    rt = max(MIN_READING_TIME, reading_time(content))
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content_final = content + EDITORIAL_NOTE_ES + FINANCE_DISCLAIMER_ES

    data = {
        "title":           title,
        "slug":            slug,
        "content":         content_final,
        "excerpt":         excerpt,
        "category":        category,
        "author":          AUTHOR,
        "keyword":         clean_keyword,
        "keyword_hash":    md5(clean_keyword),
        "reading_time":    rt,
        "featured":        article_idx == 0,
        "image_gradient":  GRADIENTS[article_idx % len(GRADIENTS)],
        "published_at":    now_iso,
        "cover_image_url": cover_image_url,
    }
    try:
        supabase_client.table("finance_articles").insert(data).execute()
        print(f"  ✅ Guardado: {title[:70]}")
        ping_indexnow([f"{FINANCE_URL_PREFIX}/{slug}"])
        return title
    except Exception as e:
        print(f"  ❌ Error guardando: {e}")
        return None


# ── PROCESS ONE TOPIC ─────────────────────────────────────────────────────────
def process_topic(
    topic: str,
    recent_articles: list[dict],
    published_this_run: list[str],
    article_idx: int,
) -> str | None:
    recent_context = format_recent_context(recent_articles)
    candidate = clean_serp_candidate(topic)

    for attempt in range(5):
        if not is_duplicate_topic(candidate, recent_articles, published_this_run):
            break
        print(f"  ⚠️  Duplicado — mutando (intento {attempt+1}/5)...")
        candidate = mutate_topic(candidate, recent_articles, attempt)
    else:
        print(f"  ❌ No se encontró ángulo único: {topic[:50]} — saltando")
        return None

    if already_published_hash(candidate):
        print(f"  ⏭️  Hash ya existe — saltando")
        return None

    print(f"  🎯 Aprobado: {candidate[:80]}")
    try:
        result      = generate_article(candidate, recent_context)
        raw_content = result["content"]

        if not validate_article_content(raw_content, label="claude-raw"):
            print("  ❌ Output inválido — saltando")
            return None

        humanized = humanize(raw_content)
        if not validate_article_content(humanized, label="humanizado"):
            print("  ⚠️  Humanizado inválido — usando output original")
            humanized = raw_content

        title_preview = candidate[:100]
        for line in humanized.strip().split("\n")[:5]:
            if line.strip().startswith("# "):
                title_preview = line.strip()[2:].strip()
                break
        slug = slugify(title_preview)

        print("  🔍 Buscando imágenes en Unsplash...")
        queries    = get_image_queries(title_preview, result["excerpt"])
        cover_img  = fetch_best_image(queries, title_preview, idx=0)
        inline_img = fetch_best_image(queries, title_preview, idx=1)
        content    = inject_images(humanized, cover_img, inline_img)

        print("  🔗 Inyectando enlaces internos...")
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
        print(f"  ❌ Error procesando '{candidate[:50]}': {e}")
        return None


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n🚀 NewsTide Finance Pipeline [{NICHE_LABEL.upper()}] — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    print("📚 Cargando artículos recientes (180 días, ambas tablas)...")
    recent_articles = get_recent_articles()

    candidate_pool = build_candidate_pool(recent_articles)
    published_titles: list[str] = []
    pool_index = 0
    extra_niche_attempts = 0

    print(f"\n🎯 Objetivo: {ARTICLES_PER_RUN} artículos\n")

    try:
        while len(published_titles) < ARTICLES_PER_RUN:
            if pool_index >= len(candidate_pool):
                extra_niche_attempts += 1
                if extra_niche_attempts > MAX_POOL_EXPANSIONS:
                    print(f"⛔ Pool agotado tras {MAX_POOL_EXPANSIONS} expansiones — abortando.")
                    break
                print(f"\n♻️  Expandiendo pool (intento {extra_niche_attempts}/{MAX_POOL_EXPANSIONS})...")
                extra = generate_niche_topics(
                    recent_articles + [
                        {"title": t, "category": "Ahorro", "keyword": t, "excerpt": "", "published_at": datetime.now(timezone.utc).isoformat()}
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
                    "title": saved, "keyword": topic,
                    "category": detect_category(topic), "excerpt": "",
                    "published_at": datetime.now(timezone.utc).isoformat(),
                })
                print(f"\n✅ Artículo {len(published_titles)}/{ARTICLES_PER_RUN}: {saved[:60]}")
                if len(published_titles) < ARTICLES_PER_RUN:
                    time.sleep(2)

    except CostLimitExceeded as e:
        print(f"\n{e}")

    print(f"\n{'='*60}")
    print(f"🎉 Hecho: {len(published_titles)} artículos publicados")
    print(f"📊 Claude: {_claude_calls_this_run} calls | {_claude_tokens_this_run:,} tokens")
    for i, t in enumerate(published_titles, 1):
        print(f"   {i}. {t[:80]}")


if __name__ == "__main__":
    main()
