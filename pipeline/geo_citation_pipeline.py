import os
import hashlib
import re
import time
import sys
import requests
from datetime import datetime, timezone
from openai import OpenAI
import anthropic
from supabase import create_client

# ── CONFIG ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY       = os.environ["OPENAI_API_KEY"]
ANTHROPIC_API_KEY    = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
UNSPLASH_ACCESS_KEY  = os.environ["UNSPLASH_ACCESS_KEY"]

ARTICLES_PER_RUN   = 5
MODEL_GENERATE     = "claude-sonnet-4-5"
MODEL_FAST         = "gpt-4o-mini"
MODEL_HUMANIZE     = "gpt-4o"

# ── SAFETY LIMITS ─────────────────────────────────────────────────────────────
MAX_CLAUDE_CALLS_PER_RUN   = 15
MAX_CLAUDE_TOKENS_PER_RUN  = 100_000

_claude_calls_this_run  = 0
_claude_tokens_this_run = 0

# ── CONTENT QUALITY LIMITS ────────────────────────────────────────────────────
MIN_READING_TIME = 6
MIN_WORD_COUNT   = MIN_READING_TIME * 200   # 1 200 words
MIN_H2_SECTIONS  = 4

# ── TITLE LENGTH CONSTANTS ───────────────────────────────────────────────────
TITLE_MAX_CHARS = 60
TITLE_SOFT_MIN  = 45
TITLE_SOFT_MAX  = 58

openai_client   = OpenAI(api_key=OPENAI_API_KEY)
claude_client   = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

GRADIENTS = [
    "linear-gradient(135deg,#0d2a2e,#0d1a2e)",
    "linear-gradient(135deg,#1a0d2e,#2e0d1a)",
    "linear-gradient(135deg,#2e1a0d,#1a2e0d)",
    "linear-gradient(135deg,#0d2e1a,#0d2e2a)",
    "linear-gradient(135deg,#2e0d0d,#1a0d2e)",
]

AUTHORS = [
    "Ana Martínez", "Carlos Ruiz", "María López",
    "Pedro Sánchez", "Sofía Jiménez",
]

# ── FIXED TOPICS (GEO-CITATION STRATEGY) ─────────────────────────────────────
# Each entry: (topic_key, title_es_hint, title_en_hint, category, source_url, source_name)
GEO_CITATION_TOPICS = [
    (
        "stripe_radar_ach_sepa_fraud",
        "Cómo Stripe Radar usa IA para reducir fraude en pagos ACH y SEPA",
        "How Stripe Radar Uses AI to Reduce Fraud in ACH and SEPA Payments",
        "IA",
        "https://stripe.com/docs/radar",
        "Stripe Documentation",
    ),
    (
        "claude_code_enterprise_dev_teams",
        "Cómo Claude Code está entrando en empresas y qué cambia para equipos de desarrollo",
        "How Claude Code Is Entering Enterprise and What Changes for Dev Teams",
        "IA",
        "https://www.anthropic.com/claude",
        "Anthropic",
    ),
    (
        "claude_cognizant_enterprise_ai_adoption",
        "Qué enseña el despliegue de Claude en Cognizant sobre adopción de IA enterprise",
        "What Cognizant's Claude Deployment Reveals About Enterprise AI Adoption",
        "Startups",
        "https://www.cognizant.com/us/en/ai",
        "Cognizant",
    ),
    (
        "openai_deployment_company_enterprise",
        "Cómo OpenAI está industrializando despliegues empresariales con su Deployment Company",
        "How OpenAI Is Industrializing Enterprise Deployments with Its Deployment Company",
        "Startups",
        "https://openai.com/enterprise",
        "OpenAI",
    ),
    (
        "openai_vs_anthropic_enterprise_adoption",
        "OpenAI vs Anthropic en empresa: adopción, control y casos reales de uso",
        "OpenAI vs Anthropic in Enterprise: Adoption, Control and Real Use Cases",
        "IA",
        "https://openai.com/enterprise",
        "OpenAI",
    ),
]

# ── INDEXNOW ──────────────────────────────────────────────────────────────────
INDEXNOW_HOST    = "www.newstide.news"
INDEXNOW_KEY     = os.environ.get("INDEXNOW_KEY", "964bf589528b466cace60749e05cfcb6")
INDEXNOW_KEY_LOC = f"https://{INDEXNOW_HOST}/{INDEXNOW_KEY}.txt"

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

def slugify_en(text: str) -> str:
    text = smart_trim(text, 60).lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text.strip())
    return text[:60].strip("-")

def md5(text: str) -> str:
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def reading_time(text: str) -> int:
    return max(MIN_READING_TIME, round(len(text.split()) / 200))

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

def already_published_hash(keyword: str) -> bool:
    res = supabase_client.table("articles").select("id").eq("keyword_hash", md5(keyword)).execute()
    return len(res.data) > 0

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
            f"🛑 COST LIMIT: projected tokens ({_claude_tokens_this_run + output_tokens:,}) "
            f"would exceed {MAX_CLAUDE_TOKENS_PER_RUN:,} — aborting."
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
        print(f"  ❌ VALIDATION FAIL [{label}]: {words} words < {MIN_WORD_COUNT} minimum")
        ok = False
    if h2_count < MIN_H2_SECTIONS:
        print(f"  ❌ VALIDATION FAIL [{label}]: {h2_count} H2 sections (need >= {MIN_H2_SECTIONS})")
        ok = False
    stripped = content.strip()
    if not stripped.startswith("#") and stripped and stripped[0].islower():
        print(f"  ❌ VALIDATION FAIL [{label}]: starts mid-sentence (truncation)")
        ok = False
    if ok:
        print(f"  ✅ VALIDATION OK [{label}]: {words} words, {h2_count} H2 sections")
    return ok

# ── GENERATE ARTICLE WITH CLAUDE ─────────────────────────────────────────────
EDITORIAL_NOTE_ES = """

---

*Nota editorial: Este artículo ha sido elaborado con asistencia de inteligencia artificial y revisado por Javier Valencia. Los hechos verificados se distinguen de las opiniones editoriales a lo largo del texto. Las fuentes externas enlazadas son independientes de NewsTide.*
"""

EDITORIAL_NOTE_EN = """

---

*Editorial note: This article was produced with AI assistance and reviewed by Javier Valencia. Verified facts are distinguished from editorial opinion throughout the text. External sources linked are independent of NewsTide.*
"""

def generate_article_es(
    topic_key: str,
    title_hint_es: str,
    title_hint_en: str,
    category: str,
    source_url: str,
    source_name: str,
) -> dict:
    global _claude_calls_this_run, _claude_tokens_this_run
    print(f"  ✍️  Claude generating ES: {title_hint_es[:70]}...")

    _check_claude_budget(output_tokens=7000)

    prompt = f"""Escribe un artículo largo y riguroso en español sobre el siguiente tema:

TEMA: {title_hint_es}

Este artículo está diseñado para maximizar citaciones en motores de búsqueda generativa (Bing Copilot, ChatGPT, Perplexity). Para eso debe ser autoritativo, preciso y estructurado de forma que un LLM pueda extraer respuestas directas.

FUENTE PRINCIPAL A CITAR: {source_name} — {source_url}

REGLAS DE CONTENIDO (NO NEGOCIABLES):
1. CERO datos inventados. Ninguna cifra, porcentaje, ARR, latencia o estadística que no sea verificable. Si no hay dato confirmado, usa lenguaje cualitativo: "mejora significativa", "reducción notable", "según fuentes del sector".
2. Separa claramente: (a) hechos verificados con fuente, (b) declaraciones atribuidas a alguien concreto, (c) opinión editorial — nunca los mezcles sin aclararlo.
3. Cita al menos 1-2 fuentes externas reales con enlace en markdown, incluyendo: {source_url}

ESTRUCTURA OBLIGATORIA:
1. H1: título SEO optimizado ({TITLE_SOFT_MIN}-{TITLE_SOFT_MAX} chars, MÁXIMO {TITLE_MAX_CHARS})
2. Párrafo inicial "answer-first" (2-3 frases): responde directamente la pregunta del titular, sin rodeos, en las primeras líneas del artículo — esta sección es la más probable de ser citada por LLMs
3. Al menos 4 secciones H2 con profundidad real
4. Una tabla comparativa en formato Markdown con datos reales (no inventados) — si no hay datos duros, la tabla puede ser cualitativa con atributos reales
5. Sección FAQ al final con exactamente 4 preguntas en formato H3 (### Pregunta) seguidas de respuesta — patrón que usa el extractor de FAQs del sitio
6. Nota editorial estándar (añadida automáticamente al final, no la incluyas tú)

REQUISITOS ADICIONALES:
- Mínimo {MIN_WORD_COUNT} palabras
- Tone: experto pero accesible, no corporativo
- Año actual: 2026. Actualiza referencias previas salvo que sean históricamente esenciales
- Categoría del artículo: {category}
- NO empieces con "En el mundo de..." ni frases genéricas
- Incluye la URL {source_url} como enlace en el cuerpo del artículo

SEO TÍTULO H1 (CRÍTICO):
- DEBE estar entre {TITLE_SOFT_MIN} y {TITLE_SOFT_MAX} caracteres
- LÍMITE DURO: nunca superar {TITLE_MAX_CHARS} caracteres
- Sin comillas en el título

Al final, en línea separada escribe exactamente:
EXCERPT: [resumen de 120 a 155 caracteres, con gancho, apto como meta description]"""

    message = claude_client.messages.create(
        model=MODEL_GENERATE,
        max_tokens=7000,
        messages=[{"role": "user", "content": prompt}],
        system=(
            f"Eres un periodista tecnológico senior especializado en IA, enterprise software y startups. "
            f"Escribes para NewsTide, medio digital en español para fundadores, CTOs y equipos de desarrollo. "
            f"Tu estilo es directo, preciso y con criterio propio. Año actual: 2026. "
            f"NUNCA inventas datos. Si no tienes un dato verificado, usas lenguaje cualitativo. "
            f"Títulos H1: entre {TITLE_SOFT_MIN} y {TITLE_SOFT_MAX} caracteres, NUNCA más de {TITLE_MAX_CHARS}. "
            f"Los artículos deben ser completos, con tablas Markdown y sección FAQ obligatoria."
        ),
    )
    output_tokens = message.usage.output_tokens if hasattr(message, "usage") else 7000
    _register_claude_call(output_tokens)

    raw = message.content[0].text
    excerpt_es = ""
    if "EXCERPT:" in raw:
        parts      = raw.split("EXCERPT:")
        raw        = parts[0].strip()
        excerpt_es = normalize_excerpt(parts[1].strip(), 120, 155)
    return {"content_es": raw, "excerpt_es": excerpt_es, "category": category}

# ── HUMANIZE WITH GPT ─────────────────────────────────────────────────────────
def humanize(text: str) -> str:
    print("  🧠 GPT humanizing...")
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": """Eres un editor humano con 15 años en medios digitales tech.
Reescribe el artículo aplicando estas reglas SIN cambiar datos, hechos ni fuentes:
- Mezcla frases cortas (5-8 palabras) con largas (18-28 palabras)
- Usa conectores variados: "sin embargo", "dicho esto", "vale la pena señalar", "en la práctica"
- Añade voz editorial puntual: "lo que más llama la atención aquí", "honestamente", "en mi experiencia"
- Incluye 1-2 preguntas retóricas naturales
- Simplifica jerga: "implementar" → "poner en marcha", "en conclusión" → "en definitiva"
- NO añadas ni elimines datos, NO inventes cifras
Mantén todos los encabezados markdown, tablas y la sección FAQ intactos. Devuelve SOLO el artículo."""},
            {"role": "user", "content": text}
        ],
        temperature=0.85,
        max_tokens=7000,
    )
    return response.choices[0].message.content

# ── TRANSLATE ES → EN ─────────────────────────────────────────────────────────
def _run_translation(es_content: str, es_excerpt: str, es_title: str) -> dict:
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": (
                "You are a professional tech journalist and translator. "
                "Translate the following Spanish tech article to natural, fluent American English. "
                "Keep all markdown formatting, tables, FAQ structure and external links intact. Adapt idioms naturally. "
                f"IMPORTANT: Start your response with exactly these two lines before the article body:\n"
                f"TITLE_EN: [translated H1 title, between {TITLE_SOFT_MIN} and {TITLE_SOFT_MAX} characters, "
                f"NEVER more than {TITLE_MAX_CHARS} characters including spaces, highly specific, no quotes — "
                f"count characters before writing, shorten if it exceeds {TITLE_SOFT_MAX}]\n"
                f"EXCERPT_EN: [one sentence summary, 120 to 155 characters, suitable as meta description]\n"
                "Then a blank line, then the full translated article body (without the H1 title line)."
            )},
            {"role": "user", "content": f"TITLE: {es_title}\nEXCERPT: {es_excerpt}\n\n{es_content}"}
        ],
        temperature=0.75,
        max_tokens=7000,
    )
    raw       = response.choices[0].message.content.strip()
    title_en   = es_title
    excerpt_en = es_excerpt
    content_en = raw
    lines      = raw.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("TITLE_EN:"):
            title_en   = smart_trim(line[len("TITLE_EN:"):].strip(), TITLE_MAX_CHARS)
            body_start = i + 1
        elif line.startswith("EXCERPT_EN:"):
            excerpt_en = normalize_excerpt(line[len("EXCERPT_EN:"):].strip(), 120, 155)
            body_start = i + 1
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1
    content_en = "\n".join(lines[body_start:]).strip()
    content_en = strip_code_fences(content_en)
    slug_en    = slugify_en(title_en)
    return {"title_en": title_en, "content_en": content_en, "excerpt_en": excerpt_en, "slug_en": slug_en}

def translate_to_english(es_content: str, es_excerpt: str, es_title: str) -> dict:
    print("  🌐 GPT translating EN...")
    for attempt in range(3):
        result = _run_translation(es_content, es_excerpt, es_title)
        if not is_truncated(result["content_en"], es_content):
            if attempt > 0:
                print(f"  ✅ Translation OK on attempt {attempt + 1}")
            return result
        print(f"  ⚠️  Truncated translation (attempt {attempt + 1}/3) — retrying...")
        time.sleep(2)
    print("  ❌ Translation truncated after 3 attempts — saving last attempt")
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
        "relevant, visually appealing Unsplash photos for this enterprise tech article. "
        "Queries should be concrete and visual. Reply with ONLY the 3 queries, one per line."
    )
    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST, max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        return lines[:3] if lines else ["enterprise technology", "AI software team", "digital transformation"]
    except:
        return ["enterprise technology", "AI software team", "digital transformation"]

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
        # Attribution lives in the markdown image title (rendered as the
        # image `title` attribute), NOT as a body paragraph. It used to be
        # appended as an italic '*Photo: [name](url) on Unsplash*' line,
        # which made the photographer's name indexable article text --
        # 'marija zaric unsplash' became the single highest-clicked query
        # on the whole site. The Unsplash License does not require
        # attribution, so keeping it out of prose is permitted.
        credit = f"Photo by {img['author']} on Unsplash"
        return f'![{alt}]({img["url"]} "{credit}")\n'
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
                blank    = False
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

# ── SAVE TO SUPABASE (articles table) ─────────────────────────────────────────
def save_article(
    keyword: str,
    content_es: str,
    excerpt_es: str,
    category: str,
    idx: int,
    content_en: str,
    title_en: str,
    excerpt_en: str,
    slug_en: str,
    cover_image_url: str | None = None,
) -> str | None:
    # Extract ES title from H1
    lines_es  = content_es.strip().split("\n")
    title_es  = keyword[:100]
    for line in lines_es[:5]:
        if line.strip().startswith("# "):
            title_es = line.strip()[2:].strip()
            break
    if lines_es and lines_es[0].strip().startswith("# "):
        content_es = "\n".join(lines_es[1:]).strip()

    # Strip H1 from EN body too
    lines_en = content_en.strip().split("\n")
    if lines_en and lines_en[0].strip().startswith("# "):
        content_en = "\n".join(lines_en[1:]).strip()

    title_es   = smart_trim(title_es, TITLE_MAX_CHARS)
    title_en   = smart_trim(title_en or title_es, TITLE_MAX_CHARS)
    excerpt_es = normalize_excerpt(excerpt_es or title_es[:150], 120, 155)
    excerpt_en = normalize_excerpt(excerpt_en or excerpt_es, 120, 155)
    rt = reading_time(content_es)
    if rt < MIN_READING_TIME:
        rt = MIN_READING_TIME
    now_iso  = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    slug_es  = slugify(title_es)
    slug_en  = slug_en or slugify_en(title_en)

    # Append editorial notes
    content_es_final = content_es + EDITORIAL_NOTE_ES
    content_en_final = content_en + EDITORIAL_NOTE_EN

    data = {
        "title":           title_es,
        "slug":            slug_es,
        "content":         content_es_final,
        "excerpt":         excerpt_es,
        "title_en":        title_en,
        "slug_en":         slug_en,
        "content_en":      content_en_final,
        "excerpt_en":      excerpt_en,
        "category":        category,
        "author":          AUTHORS[idx % len(AUTHORS)],
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
        return (title_es, slug_es, slug_en)
    except Exception as e:
        print(f"  ❌ Error saving: {e}")
        return None

# ── PROCESS ONE TOPIC ─────────────────────────────────────────────────────────
def process_topic(
    topic_key: str,
    title_hint_es: str,
    title_hint_en: str,
    category: str,
    source_url: str,
    source_name: str,
    article_idx: int,
) -> tuple | None:
    if already_published_hash(topic_key):
        print(f"  ⏭️  Already published (hash match): {topic_key} — skipping")
        return None

    print(f"  🎯 Processing: {title_hint_es[:70]}")
    try:
        result     = generate_article_es(topic_key, title_hint_es, title_hint_en, category, source_url, source_name)
        raw_content = result["content_es"]

        if not validate_article_content(raw_content, label="claude-raw-es"):
            print("  ❌ Article discarded (invalid Claude output)")
            return None

        humanized_es = humanize(raw_content)
        if not validate_article_content(humanized_es, label="humanized-es"):
            print("  ⚠️  Humanized invalid — using original Claude content")
            humanized_es = raw_content

        # Extract ES title
        title_es_final = title_hint_es[:100]
        for line in humanized_es.strip().split("\n")[:5]:
            if line.strip().startswith("# "):
                title_es_final = line.strip()[2:].strip()
                break
        title_es_final = smart_trim(title_es_final, TITLE_MAX_CHARS)

        print("  🔍 Fetching Unsplash images...")
        queries    = get_image_queries(title_es_final, result["excerpt_es"])
        cover_img  = fetch_best_image(queries, title_es_final, idx=0)
        inline_img = fetch_best_image(queries, title_es_final, idx=1)
        content_es = inject_images(humanized_es, cover_img, inline_img)
        cover_image_url = cover_img["url"] if cover_img else None

        en = translate_to_english(content_es, result["excerpt_es"], title_es_final)
        if not validate_article_content(en["content_en"], label="translated-en"):
            print("  ⚠️  EN translation invalid after retries — saving anyway")

        saved = save_article(
            keyword=topic_key,
            content_es=content_es,
            excerpt_es=result["excerpt_es"],
            category=result["category"],
            idx=article_idx,
            content_en=en["content_en"],
            title_en=en["title_en"],
            excerpt_en=en["excerpt_en"],
            slug_en=en["slug_en"],
            cover_image_url=cover_image_url,
        )
        return saved  # (title_es, slug_es, slug_en) or None

    except CostLimitExceeded:
        raise
    except Exception as e:
        print(f"  ❌ Error processing '{topic_key}': {e}")
        return None

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n🚀 NewsTide Geo-Citation Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 65)
    print(
        f"🔒 Safety limits: max {MAX_CLAUDE_CALLS_PER_RUN} Claude calls, "
        f"max {MAX_CLAUDE_TOKENS_PER_RUN:,} output tokens"
    )
    print(f"🎯 Fixed topics: {len(GEO_CITATION_TOPICS)} articles to generate\n")

    published_slugs_es: list[str] = []
    published_slugs_en: list[str] = []
    published_titles:   list[str] = []

    try:
        for idx, (topic_key, title_hint_es, title_hint_en, category, source_url, source_name) in enumerate(
            GEO_CITATION_TOPICS
        ):
            print(f"\n📝 [{idx+1}/{len(GEO_CITATION_TOPICS)}] {title_hint_es[:70]}")

            result = process_topic(
                topic_key=topic_key,
                title_hint_es=title_hint_es,
                title_hint_en=title_hint_en,
                category=category,
                source_url=source_url,
                source_name=source_name,
                article_idx=idx,
            )

            if result:
                title_es_saved, slug_es_saved, slug_en_saved = result
                published_titles.append(title_es_saved)
                published_slugs_es.append(f"https://{INDEXNOW_HOST}/articulo/{slug_es_saved}")
                published_slugs_en.append(f"https://{INDEXNOW_HOST}/en/article/{slug_en_saved}")
                print(f"  ✅ Article {idx+1} done: {title_es_saved[:60]}")
            else:
                print(f"  ⚠️  Article {idx+1} skipped")

            if idx < len(GEO_CITATION_TOPICS) - 1:
                time.sleep(2)

    except CostLimitExceeded as e:
        print(f"\n{e}")
        print(f"   Articles published before cutoff: {len(published_titles)}")

    # ── Bulk IndexNow ping for all 10 URLs (5 ES + 5 EN) ──────────────────────
    all_urls = published_slugs_es + published_slugs_en
    if all_urls:
        print(f"\n🔍 Submitting {len(all_urls)} URLs to IndexNow (Bing)...")
        ping_indexnow(all_urls)

    print(f"\n{'='*65}")
    print(f"🎉 Geo-Citation Pipeline finished: {len(published_titles)}/{len(GEO_CITATION_TOPICS)} articles published")
    print(f"📊 Total Claude calls: {_claude_calls_this_run} | Output tokens: {_claude_tokens_this_run:,}")
    for i, t in enumerate(published_titles, 1):
        print(f"   {i}. {t[:80]}")

    if len(published_titles) < len(GEO_CITATION_TOPICS):
        missing = len(GEO_CITATION_TOPICS) - len(published_titles)
        print(f"\n⚠️  WARNING: {missing} article(s) were skipped (already published or error).")
        sys.exit(0)  # non-fatal — already-published is expected on re-runs

if __name__ == "__main__":
    main()
