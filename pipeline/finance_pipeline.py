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

# ── NICHE DEFINITION ──────────────────────────────────────────────────────────
# TARGET : Hispanics living in the USA (first & second generation).
#          Huge underserved segment: ~60 M people, most personal finance content
#          in Spanish targets Spain/LATAM and misses US-specific products entirely.
# LANGUAGE: Spanish (ES) — but about US financial products, US laws, US apps.
# CONTENT : Actionable guides on: building credit from zero, saving on a low wage,
#           remittances, ITIN taxes, first investment steps, budgeting for families.
# SEO     : Long-tail queries like "cómo construir crédito sin historial en USA"
#           have good volume + very low competition vs English equivalents.
# TABLE   : finance_articles (same schema as main articles table)
# URL     : newstide.news/en/fin/[slug]   (existing route)

NICHE_LABEL  = "finanzas personales hispanos USA"
SITE_LANG    = "es"
AUTHOR       = "Ana Martínez"   # finance vertical byline

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
MIN_READING_TIME = 5
MIN_WORD_COUNT   = MIN_READING_TIME * 200   # 1 000 palabras
MIN_H2_SECTIONS  = 3

# ── TITLE LENGTH CONSTANTS ────────────────────────────────────────────────────
TITLE_MAX_CHARS = 60
TITLE_SOFT_MIN  = 45
TITLE_SOFT_MAX  = 58

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

*Nota editorial: Este artículo ha sido elaborado con asistencia de inteligencia artificial y revisado por Ana Martínez. Los datos verificados se distinguen de las opiniones editoriales a lo largo del texto. Las fuentes externas enlazadas son independientes de NewsTide.*
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
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n"),("ü","u")]:
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text.strip())
    return text[:60].strip("-")


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


def is_truncated(content: str, reference: str) -> bool:
    stripped = content.strip()
    if not stripped:
        return True
    if stripped[0].islower():
        return True
    if len(reference) > 0 and len(stripped.split()) < len(reference.split()) * 0.60:
        return True
    return False


def has_external_link(content: str) -> bool:
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
            f"🛑 COST LIMIT: reached {MAX_CLAUDE_CALLS_PER_RUN} Claude calls — aborting."
        )
    if _claude_tokens_this_run + output_tokens > MAX_CLAUDE_TOKENS_PER_RUN:
        raise CostLimitExceeded(
            f"🛑 COST LIMIT: tokens would exceed {MAX_CLAUDE_TOKENS_PER_RUN:,} — aborting."
        )


def _register_claude_call(output_tokens: int) -> None:
    global _claude_calls_this_run, _claude_tokens_this_run
    _claude_calls_this_run  += 1
    _claude_tokens_this_run += output_tokens
    print(
        f"  📊 Claude usage: {_claude_calls_this_run}/{MAX_CLAUDE_CALLS_PER_RUN} calls, "
        f"{_claude_tokens_this_run:,}/{MAX_CLAUDE_TOKENS_PER_RUN:,} tokens"
    )


# ── CONTENT VALIDATION ────────────────────────────────────────────────────────
def validate_article_content(content: str, label: str = "article") -> bool:
    words    = len(content.split())
    h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
    ok = True
    if words < MIN_WORD_COUNT:
        print(f"  ❌ VALIDATION FAIL [{label}]: {words} words < {MIN_WORD_COUNT}")
        ok = False
    if h2_count < MIN_H2_SECTIONS:
        print(f"  ❌ VALIDATION FAIL [{label}]: {h2_count} H2 sections (need >= {MIN_H2_SECTIONS})")
        ok = False
    stripped = content.strip()
    if not stripped.startswith("#") and len(stripped) > 0 and stripped[0].islower():
        print(f"  ❌ VALIDATION FAIL [{label}]: starts mid-sentence (truncation)")
        ok = False
    if not has_external_link(content):
        print(f"  ⚠️  VALIDATION WARN [{label}]: no external link — EEAT risk")
    if ok:
        print(f"  ✅ VALIDATION OK [{label}]: {words} words, {h2_count} H2 sections")
    return ok


# ── LOAD RECENT ARTICLES FROM SUPABASE ────────────────────────────────────────
def get_recent_articles() -> list[dict]:
    """Load last 90 days from finance_articles to maximise dedup coverage."""
    since = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    try:
        res = (
            supabase_client.table("finance_articles")
            .select("title_en, keyword, category, excerpt_en, keyword_hash")
            .gte("published_at", since)
            .order("published_at", desc=True)
            .limit(150)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"  ⚠️  Error reading Supabase finance_articles: {e}")
        return []


def format_recent_context(articles: list[dict]) -> str:
    if not articles:
        return "No hay artículos publicados todavía."
    lines = [f"- [{r.get('category','?')}] {r.get('title_en') or r.get('keyword','')}" for r in articles]
    return "\n".join(lines)


def already_published_hash(keyword: str) -> bool:
    res = supabase_client.table("finance_articles").select("id").eq("keyword_hash", md5(keyword)).execute()
    return len(res.data) > 0


# ── SERPAPI SOURCES ────────────────────────────────────────────────────────────
# Queries written in Spanish targeting US-based Hispanic searches.
# These are genuinely low-competition long-tail terms with real search volume.

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
            params = {
                "q": q, "tbm": "nws",
                "hl": "es", "gl": "us",
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
            print(f"  SerpAPI hispano-news error ({q[:40]}): {e}")
        time.sleep(0.8)
    return results


def fetch_serpapi_credit_saving() -> list[str]:
    """Credit and saving queries — highest search intent for this audience."""
    queries = [
        "tarjetas de crédito para inmigrantes sin historial USA",
        "cómo subir el credit score rápido en Estados Unidos",
        "cómo abrir cuenta bancaria sin documentos USA 2026",
        "mejores bancos para hispanos en Estados Unidos 2026",
        "cómo hacer un presupuesto familiar en USA con poco dinero",
    ]
    results = []
    for q in queries:
        try:
            params = {
                "q": q,
                "hl": "es", "gl": "us",
                "api_key": SERPAPI_KEY, "num": 5,
            }
            data = GoogleSearch(params).get_dict()
            for r in data.get("organic_results", [])[:3]:
                title = r.get("title", "")
                if title and len(title) > 20:
                    results.append(title)
        except Exception as e:
            print(f"  SerpAPI credit-saving error: {e}")
        time.sleep(0.8)
    return results


def fetch_serpapi_inversion_impuestos() -> list[str]:
    """Investment and tax queries — aspirational but real for this audience."""
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
            params = {
                "q": q, "tbm": "nws",
                "hl": "es", "gl": "us",
                "api_key": SERPAPI_KEY, "num": 5,
            }
            data = GoogleSearch(params).get_dict()
            for r in data.get("news_results", data.get("organic_results", []))[:4]:
                title   = r.get("title", "")
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
        f"- {a.get('title_en') or a.get('keyword', '')}" for a in recent_articles[:40]
    )
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Hoy es {today}. Eres editor jefe de NewsTide Finanzas, un medio de finanzas personales EN ESPAÑOL para hispanos que viven en Estados Unidos.

AUDIENCIA: inmigrantes y segunda generación hispana en USA. Muchos tienen poco historial crediticio, envían remesas, trabajan con salarios bajos o medios, quieren invertir pero no saben cómo. La mayoría no encuentra contenido en español sobre productos AMERICANOS (no europeos ni latinoamericanos).

YA PUBLICADO (NO repetir ni usar ángulo similar):
{recent_titles if recent_titles else "Nada todavía."}

Genera exactamente {n} ideas de artículo que rankeen bien en Google para este nicho.

REGLAS EEAT:
1. Ningún número inventado en el título (sin "ahorra $500/mes" sin fuente real).
2. Cada título debe describir algo verificable y útil.
3. Los artículos deben ser sobre productos y leyes AMERICANAS (no españolas ni latinoamericanas).

DISTRIBUCIÓN DE CONTENIDO:
- 5 guías prácticas paso a paso: "Cómo [hacer X] en USA si eres inmigrante/hispano"
- 4 comparativas directas: "X vs Y: cuál conviene a los hispanos en USA"
- 4 guías de productos US específicos: crédito, bancos, apps, inversión para este público
- 3 temas de impuestos/ITIN/taxes: muy buscados, muy poca competencia en español
- 2 remesas / envío de dinero: Wise, Remitly, Western Union comparados

REGLAS DE TÍTULO:
- Cada título debe mencionar una herramienta, banco, app o producto REAL (Chime, Credit Karma, Roth IRA, ITIN, Wise, Remitly, etc.)
- Intención de búsqueda clara: cómo, cuál, mejor, comparativa
- 45-58 caracteres ideal (cuenta los caracteres)
- Sin números inventados
- Todo en ESPAÑOL

Formato: un título por línea, sin numeración, sin explicación."""

    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.90,
            max_tokens=900,
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        print(f"  🧠 GPT generó {len(lines)} ideas de nicho")
        return lines[:n]
    except Exception as e:
        print(f"  ⚠️  Error generando temas: {e}")
        return []


# ── SAFE FALLBACK TOPICS ──────────────────────────────────────────────────────
def get_fallback_topics() -> list[str]:
    """Evergreen, verifiable topics for Hispanics in USA — no invented stats."""
    return [
        "Cómo construir crédito en USA sin historial crediticio",
        "Tarjetas de crédito para inmigrantes sin Social Security",
        "Cómo declarar impuestos con ITIN en Estados Unidos",
        "Wise vs Remitly: cuál conviene para enviar dinero a México",
        "Cómo abrir cuenta bancaria sin documentos en USA 2026",
        "Roth IRA explicado para hispanos que viven en USA",
        "Cómo subir tu credit score 100 puntos en 6 meses",
        "Mejores bancos para hispanos en Estados Unidos 2026",
        "Cómo hacer un presupuesto familiar viviendo en USA",
        "Cómo invertir en bolsa siendo inmigrante en América",
        "Chime vs Bank of America: qué banco conviene al hispano",
        "Cómo comprar casa siendo inmigrante en Estados Unidos",
        "Qué es el ITIN y para qué sirve en USA",
        "Mejores apps para ahorrar dinero en Estados Unidos",
        "Cómo enviar remesas baratas desde USA a Latinoamérica",
        "Deudas médicas en USA: qué derechos tienes como hispano",
        "401k explicado en español para trabajadores en USA",
        "Cómo salir de deudas de tarjeta de crédito en USA",
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
    existing_str = "\n".join(f"- {t}" for t in all_existing[:50] if t)
    prompt = f"""Artículo candidato: "{candidate}"

Artículos ya publicados:
{existing_str}

¿El candidato cubre EL MISMO tema específico o un ángulo muy similar a algún artículo existente?
Solo es duplicado si: mismo producto/herramienta principal Y mismo caso de uso o comparación.
Herramientas distintas, público distinto o ángulo distinto = NO es duplicado.

Responde SOLO: YES o NO"""
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
        "una guía paso a paso con ejemplos reales de productos americanos",
        "una comparativa directa entre dos herramientas concretas disponibles en USA",
        "el error más común que cometen los hispanos con este tema financiero y cómo evitarlo",
        "un enfoque para alguien que acaba de llegar a USA y no sabe por dónde empezar",
        "una guía específica para familias hispanas con hijos en Estados Unidos",
        "un análisis del coste real de este producto financiero para el hispano promedio",
    ]
    angle = angles[attempt % len(angles)]
    prompt = f"""Tienes este tema: "{original}"

Es demasiado similar a los ya publicados:
{recent_titles}

Transfórmalo usando este ángulo específico: {angle}

El nuevo tema debe:
- Mencionar una herramienta, banco o producto AMERICANO real
- Ser algo que un hispano en USA buscaría en Google
- Sin números inventados
- Máximo 120 caracteres
- En ESPAÑOL

Responde SOLO con el nuevo título (1 línea)."""
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            max_tokens=80,
        )
        mutated = resp.choices[0].message.content.strip().strip('"').strip("'")
        print(f"  🔄 Mutado (intento {attempt+1}): {mutated[:70]}")
        return mutated if len(mutated) > 15 else original
    except Exception as e:
        print(f"  ⚠️  Mutation error: {e}")
        return original


# ── BUILD CANDIDATE POOL ──────────────────────────────────────────────────────
def build_candidate_pool(recent_articles: list[dict]) -> list[str]:
    print("🔍 Construyendo pool de candidatos (hispanos USA finanzas)...")
    pool = []

    print("  📰 Fuente 1: Noticias finanzas hispanos USA (SerpAPI ES)...")
    pool.extend(fetch_serpapi_hispano_news())

    print("  💳 Fuente 2: Crédito y ahorro (SerpAPI ES orgánico)...")
    pool.extend(fetch_serpapi_credit_saving())

    print("  📈 Fuente 3: Inversión e impuestos (SerpAPI ES)...")
    pool.extend(fetch_serpapi_inversion_impuestos())

    print("  🧠 Fuente 4: Ideas de nicho (GPT)...")
    pool.extend(generate_niche_topics(recent_articles, n=18))

    pool.extend(get_fallback_topics())

    seen, unique = set(), []
    for p in pool:
        key = p.lower().strip()[:60]
        if key not in seen and len(p) > 20:
            seen.add(key)
            unique.append(p)

    print(f"  ✅ Pool total: {len(unique)} candidatos únicos")
    return unique


# ── GENERATE ARTICLE WITH CLAUDE ──────────────────────────────────────────────
def generate_article(keyword: str, recent_context: str) -> dict:
    global _claude_calls_this_run, _claude_tokens_this_run
    print(f"  ✍️  Claude generando: {keyword[:70]}...")
    category  = detect_category(keyword)
    min_words = MIN_WORD_COUNT
    _check_claude_budget(output_tokens=6000)

    prompt = f"""Escribe un artículo completo EN ESPAÑOL sobre finanzas personales para hispanos en USA: "{keyword}"

YA PUBLICADO — no repetir estos temas ni ángulos:
{recent_context}

AUDIENCIA: Hispanos viviendo en Estados Unidos — muchos inmigrantes de primera generación, trabajadores con salarios bajos o medios, personas que quieren entender el sistema financiero americano pero no encuentran contenido en español sobre productos US específicos.

ESTE ES UN ARTÍCULO YMYL (Your Money Your Life) — sigue E-E-A-T estrictamente:
- Cita datos reales y verificables (tasas FDIC, estadísticas del CFPB, datos oficiales del IRS)
- Sé honesto sobre riesgos y limitaciones
- NO prometas rendimientos específicos ni garantices resultados
- Haz referencia a productos AMERICANOS reales (no españoles ni latinoamericanos)

ESTRUCTURA (usa markdown):
- Título H1: optimizado para búsqueda en español, práctico, específico ({TITLE_SOFT_MIN}–{TITLE_SOFT_MAX} chars, LÍMITE {TITLE_MAX_CHARS})
- Introducción: 2 párrafos — engancha con una situación real que reconocerá el lector hispano, luego explica qué aprenderá
- Sección "Para quién es esta guía": explícita sobre quién se beneficia más
- 4-5 secciones H2: pasos concretos, herramientas/apps/productos con nombres reales, comparativa cuando haya datos
- Sección "Cuándo esto NO funciona": limitaciones honestas (estado migratorio, ingresos, etc.)
- FAQ con 3-4 preguntas H3 y respuestas (schema-friendly)
- Conclusión: próximo paso concreto que el lector puede dar hoy

REGLAS EEAT (no negociables):
1. Toda cifra o dato DEBE citar fuente real inline: "(según [Fuente], [año])"
2. NUNCA inventes datos. Usa lenguaje cualitativo si no tienes la fuente.
3. Incluye al menos 2 enlaces externos reales a fuentes primarias americanas
   (IRS.gov, CFPB.gov, documentación oficial de bancos o apps).
   Formato: [texto del enlace](https://url-real.com)
4. Distingue claramente: (a) hechos verificados con fuente, (b) declaraciones atribuidas, (c) opinión editorial.

REQUISITOS DE CONTENIDO:
- MÍNIMO {min_words} palabras (obligatorio)
- Nombres reales de productos americanos: Chime, Credit Karma, Wise, Remitly, Cash App, Acorns, Robinhood, etc.
- Tono: amigo de confianza que sabe del tema — no corporativo, no paternalista
- USA: leyes americanas, productos americanos, contexto americano
- Año actual: 2026
- Categoría: {category}
- NO empieces con "En el mundo de..." ni frases genéricas
- Ángulo claramente diferente a los artículos ya publicados

TÍTULO H1 — REGLAS (CRÍTICO):
- DEBE tener entre {TITLE_SOFT_MIN} y {TITLE_SOFT_MAX} caracteres
- LÍMITE DURO: nunca superes {TITLE_MAX_CHARS} caracteres
- Debe leerse como algo que una persona real buscaría en Google en español
- Sin comillas en el título

Al final, en una línea separada escribe exactamente:
EXCERPT: [resumen de 120 a 155 caracteres en español: qué resuelve el artículo y para quién — útil y con gancho real]"""

    message = claude_client.messages.create(
        model=MODEL_GENERATE, max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
        system=(
            f"Eres un periodista financiero senior con 15 años de experiencia cubriendo finanzas personales "
            f"para la comunidad hispana en Estados Unidos. Conoces el sistema bancario americano, "
            f"las leyes del IRS, el sistema de crédito de FICO, y los productos disponibles para inmigrantes. "
            f"Escribes para NewsTide Finanzas, un medio EN ESPAÑOL para hispanos que viven en USA. "
            f"Tu estilo es claro, directo y empático — como un amigo de confianza que sabe del tema. "
            f"El año actual es 2026. "
            f"REGLA ABSOLUTA: NUNCA inventas datos, cifras ni estadísticas. Si no tienes la fuente, usas lenguaje cualitativo. "
            f"Todos los productos y leyes que menciones son AMERICANOS. "
            f"Títulos H1: entre {TITLE_SOFT_MIN} y {TITLE_SOFT_MAX} caracteres, nunca más de {TITLE_MAX_CHARS}. "
            f"Los excerpts son meta descriptions — útiles y concretos, no dramáticos."
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
    print("  🧠 GPT humanizando...")
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": """Eres un editor humano con 15 años de experiencia en medios de finanzas personales para la comunidad hispana en Estados Unidos.
Reescribe el artículo aplicando estas reglas SIN cambiar los datos, cifras, fuentes ni hechos:
- Mezcla frases cortas (5-8 palabras) con largas (18-28 palabras)
- Usa conectores variados: "sin embargo", "dicho esto", "lo que más importa aquí", "en la práctica", "honestamente"
- Añade voz editorial puntual: "lo que nadie te explica", "desde mi experiencia", "lo que más me llama la atención"
- Incluye 1-2 preguntas retóricas naturales
- Simplifica jerga: "fundamental" → "clave", "en conclusión" → "en definitiva"
- USA: asegúrate de que todos los productos y leyes mencionados sean americanos
- CRÍTICO: NO añadas ni elimines datos, NO inventes cifras, NO cambies ninguna fuente
- IMPORTANTE: Mantén el texto completamente en ESPAÑOL
- Conserva todos los encabezados markdown, tablas, FAQs y enlaces externos
Devuelve SOLO el artículo, sin explicaciones."""},
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
        f"Título del artículo: {title}\nResumen: {excerpt}\n\n"
        "Dame exactamente 3 búsquedas cortas en INGLÉS (2-4 palabras) para encontrar "
        "fotos de Unsplash relevantes para este artículo de finanzas personales para hispanos en USA. "
        "Las búsquedas deben ser concretas y visuales (ej: 'family budget planning', 'credit card wallet', 'savings jar'). "
        "Responde SOLO con las 3 búsquedas, una por línea."
    )
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST, max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        return lines[:3] if lines else ["family budget planning", "personal finance money", "credit card wallet"]
    except:
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
        f'- Título: "{r["title_en"]}" | URL: https://www.newstide.news/en/fin/{r["slug_en"]}'
        for r in related
    )
    prompt = f"""Eres un editor SEO. Añade 2-3 enlaces internos naturales al artículo de abajo.

ENLACES DISPONIBLES:
{candidates_str}

REGLAS:
1. Inserta los enlaces solo dentro de párrafos — nunca en encabezados.
2. Usa el texto ancla que ya existe en el artículo de forma natural.
3. Máximo 3 enlaces en total.
4. Usa SOLO las URLs listadas arriba, exactamente como están escritas.
5. Devuelve el ARTÍCULO COMPLETO con los enlaces insertados. Sin explicaciones.

ARTÍCULO:
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


# ── SAVE TO SUPABASE (finance_articles) ───────────────────────────────────────
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

    title   = smart_trim(title, TITLE_MAX_CHARS)
    excerpt = normalize_excerpt(excerpt or title[:150], 120, 155)
    rt = reading_time(content)
    if rt < MIN_READING_TIME:
        rt = MIN_READING_TIME

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content_final = content + EDITORIAL_NOTE_ES + FINANCE_DISCLAIMER_ES

    data = {
        "title":           title,
        "slug":            slug,
        "content":         content_final,
        "excerpt":         excerpt,
        "title_en":        title,
        "slug_en":         slug,
        "content_en":      content_final,
        "excerpt_en":      excerpt,
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
    try:
        supabase_client.table("finance_articles").insert(data).execute()
        print(f"  ✅ Guardado en finance_articles: {title[:70]}")
        ping_indexnow([f"https://www.newstide.news/en/fin/{slug}"])
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
    candidate = topic

    for attempt in range(5):
        if not is_duplicate_topic(candidate, recent_articles, published_this_run):
            break
        print(f"  ⚠️  Duplicado — mutando (intento {attempt+1}/5)...")
        candidate = mutate_topic(candidate, recent_articles, attempt)
    else:
        print(f"  ❌ No se encontró ángulo único para: {topic[:50]} — saltando")
        return None

    if already_published_hash(candidate):
        print(f"  ⏭️  Hash ya existe en Supabase — saltando")
        return None

    print(f"  🎯 Aprobado: {candidate[:80]}")
    try:
        result      = generate_article(candidate, recent_context)
        raw_content = result["content"]

        if not validate_article_content(raw_content, label="claude-raw"):
            print("  ❌ Output de Claude inválido — saltando")
            return None

        humanized = humanize(raw_content)
        if not validate_article_content(humanized, label="humanizado"):
            print("  ⚠️  Humanizado inválido — usando output original de Claude")
            humanized = raw_content

        title_preview = candidate[:100]
        for line in humanized.strip().split("\n")[:5]:
            if line.strip().startswith("# "):
                title_preview = line.strip()[2:].strip()
                break
        title_preview = smart_trim(title_preview, TITLE_MAX_CHARS)
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
    print(
        f"🔒 Límites: {MAX_CLAUDE_CALLS_PER_RUN} Claude calls, "
        f"{MAX_CLAUDE_TOKENS_PER_RUN:,} output tokens"
    )

    print("📚 Cargando artículos recientes de Supabase (últimos 90 días)...")
    recent_articles = get_recent_articles()
    print(f"   {len(recent_articles)} artículos cargados para deduplicación")

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
                        {"title_en": t, "category": "Ahorro", "keyword": t, "excerpt_en": ""}
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
                print(f"\n✅ Artículo {len(published_titles)}/{ARTICLES_PER_RUN}: {saved[:60]}")
                if len(published_titles) < ARTICLES_PER_RUN:
                    time.sleep(2)

    except CostLimitExceeded as e:
        print(f"\n{e}")
        print(f"   Publicados antes del corte: {len(published_titles)}")

    print(f"\n{'='*60}")
    print(f"🎉 Hecho: {len(published_titles)} artículos publicados")
    print(f"📊 Claude: {_claude_calls_this_run} calls | {_claude_tokens_this_run:,} tokens")
    for i, t in enumerate(published_titles, 1):
        print(f"   {i}. {t[:80]}")


if __name__ == "__main__":
    main()
