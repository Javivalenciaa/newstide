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
MODEL_FAST         = "gpt-4o-mini"          # cheap model for dedup / classification
MODEL_HUMANIZE     = "gpt-4o-mini"

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
    "herramienta": "Herramientas", "software": "Herramientas", "app": "Herramientas",
    "tutorial": "Tutoriales", "cómo": "Tutoriales", "guía": "Tutoriales",
    "paso a paso": "Tutoriales",
    "noticia": "Noticias", "lanza": "Noticias", "anuncia": "Noticias",
}

AUTHORS = [
    "Ana Martínez", "Carlos Ruiz", "María López",
    "Pedro Sánchez", "Sofía Jiménez", "Luis Torres"
]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def slugify(text):
    text = text.lower()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n"),("ü","u")]:
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text.strip())
    return text[:80]

def md5(text):
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def detect_category(keyword):
    kw = keyword.lower()
    for key, cat in CATEGORIES.items():
        if key in kw:
            return cat
    return "IA"

def reading_time(text):
    return max(1, round(len(text.split()) / 200))

def already_published_hash(keyword):
    res = supabase_client.table("articles").select("id").eq("keyword_hash", md5(keyword)).execute()
    return len(res.data) > 0

def normalize_year(text: str) -> str:
    return re.sub(r'\b(2023|2024|2025)\b', '2026', text)

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
    """Fetch specific today's news headlines — not generic trends."""
    queries = [
        "OpenAI Anthropic Google DeepMind news today",
        "startups IA financiación noticias hoy",
        "inteligencia artificial empresa producto lanzamiento",
        "herramientas developer IA 2026",
        "tech startup España Europa noticias",
    ]
    results = []
    for q in queries:
        try:
            params = {
                "q": q, "tbm": "nws",
                "hl": "es", "gl": "es",
                "api_key": SERPAPI_KEY, "num": 6
            }
            data = GoogleSearch(params).get_dict()
            for r in data.get("news_results", data.get("organic_results", []))[:4]:
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                if title and len(title) > 20:
                    results.append(f"{title} — {snippet[:100]}" if snippet else title)
        except Exception as e:
            print(f"  SerpAPI error ({q[:30]}): {e}")
        time.sleep(0.8)
    return results

# ── SOURCE 2: SERPAPI TRENDING SEARCHES ──────────────────────────────────────
def fetch_serpapi_trends() -> list[str]:
    """Google trending searches related to tech/AI."""
    queries = [
        "inteligencia artificial novedades junio 2026",
        "mejores herramientas IA developers 2026",
        "startups tecnología inversión 2026",
        "automatización empresas IA casos de uso",
        "modelos lenguaje LLM comparativa 2026",
    ]
    results = []
    for q in queries:
        try:
            params = {
                "q": q, "location": "Spain",
                "hl": "es", "gl": "es",
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

# ── SOURCE 3: NICHE TOPIC GENERATOR (AI-driven) ──────────────────────────────
def generate_niche_topics(recent_articles: list[dict], n: int = 15) -> list[str]:
    """
    Ask GPT to brainstorm N very specific, niche topics that:
    - haven't been covered yet
    - are based on real 2026 trends in AI/startups/tools
    - are hyper-specific (tool + audience + use case)
    """
    recent_titles = "\n".join(f"- {a['title']}" for a in recent_articles[:30])
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Hoy es {today}. Eres editor jefe de NewsTide, un medio tech premium para founders y developers en español.

Artículos ya publicados (NO repetir ni similar):
{recent_titles if recent_titles else "Ninguno aún."}

Genera exactamente {n} ideas de artículos muy específicos y diferentes entre sí.

REGLAS:
1. NUNCA generes títulos genéricos como "Las mejores herramientas de IA" o "El futuro de la IA"
2. Cada idea debe mencionar una herramienta/modelo/empresa REAL y concreta (Claude 3.5, Cursor, Supabase, Linear, Vercel, Mistral, Perplexity, etc.)
3. Mezcla estos ángulos: tutorial técnico, noticia de producto, caso de uso real, comparativa, error común, dato sorprendente
4. Temas posibles: LLMs, agentes de IA, dev tools, automatización, startups europeas, product building, RAG, fine-tuning, infraestructura IA
5. Cada idea COMPLETAMENTE diferente de las ya publicadas
6. Usa ángulos tipo: "Por qué X falla cuando...", "Cómo [empresa] usa X para...", "El problema real de X que nadie menciona", "[Herramienta] vs [Herramienta]: cuál usar para..."

Formato: una idea por línea, sin numeración, sin explicación. Solo el título/ángulo del artículo."""

    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.92,
            max_tokens=800,
        )
        lines = [l.strip() for l in resp.choices[0].message.content.strip().splitlines() if l.strip()]
        print(f"  🧠 GPT generó {len(lines)} ideas de nicho")
        return lines[:n]
    except Exception as e:
        print(f"  ⚠️  Error generando nichos: {e}")
        return []

# ── SOURCE 4: EMERGENCY FALLBACK TOPICS ──────────────────────────────────────
def get_fallback_topics() -> list[str]:
    """Hardcoded specific topics as last resort — always different angles."""
    today = datetime.now().strftime("%B %Y")
    return [
        f"Cursor vs GitHub Copilot en {today}: cuál usar según tu stack",
        f"Cómo Supabase está cambiando el backend de las startups en {today}",
        f"El problema real de los agentes de IA autónomos en producción",
        f"Mistral vs Claude Haiku: cuándo usar modelos pequeños y cuándo no",
        f"Por qué el 80% de los proyectos RAG fracasan en producción",
        f"Cómo Vercel AI SDK simplifica la integración de LLMs en Next.js",
        f"Linear vs Jira: por qué los mejores equipos de producto están migrando",
        f"Fine-tuning vs RAG: la decisión que define tu arquitectura IA en {today}",
        f"Cómo las startups europeas están compitiendo con Silicon Valley en IA",
        f"El stack técnico de las 10 startups de IA más prometedoras de Europa",
        f"Por qué Perplexity está amenazando el modelo de negocio de Google",
        f"Cómo usar n8n + Claude para automatizar flujos de trabajo sin código",
        f"El error más caro que cometen los founders al escalar con IA",
        f"Notion AI vs Obsidian: gestión del conocimiento para product managers",
        f"Cómo Anthropic está ganando terreno en empresas frente a OpenAI",
    ]

# ── DEDUPLICATION ENGINE ──────────────────────────────────────────────────────
def is_duplicate_topic(candidate: str, recent_articles: list[dict], published_this_run: list[str]) -> bool:
    """
    Uses GPT-4o-mini to check if candidate overlaps with recent articles OR
    articles published in this same pipeline run.
    Returns True if it's a duplicate/too similar.
    """
    all_existing = [a["title"] for a in recent_articles] + published_this_run
    if not all_existing:
        return False

    existing_str = "\n".join(f"- {t}" for t in all_existing[:40])
    prompt = f"""Artículo candidato: "{candidate}"

Artículos existentes:
{existing_str}

¿El artículo candidato cubre el MISMO tema específico o un ángulo muy similar a alguno de los existentes?

Criterio: solo es duplicado si trata literalmente el mismo tema principal (misma herramienta + mismo contexto, o mismo caso de uso exacto). Diferentes herramientas, diferentes audiencias, o diferentes ángulos NO son duplicados aunque pertenezcan a la misma categoría general.

Responde ÚNICAMENTE: YES o NO"""

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
        return False  # On error, don't block — let it through

def mutate_topic(original: str, recent_articles: list[dict], attempt: int) -> str:
    """
    If a topic is too similar to existing ones, mutate it into a different angle.
    Uses GPT to find a genuinely different spin.
    """
    recent_titles = "\n".join(f"- {a['title']}" for a in recent_articles[:20])
    angles = [
        "un tutorial técnico paso a paso muy específico",
        "una comparativa directa entre dos herramientas concretas",
        "un caso de uso real de una empresa o startup conocida",
        "un error común o problema que nadie menciona sobre este tema",
        "un dato contraintuitivo o estadística sorprendente",
        "el impacto en startups europeas o en español específicamente",
    ]
    angle = angles[attempt % len(angles)]
    prompt = f"""Tienes este tema: "{original}"

Es demasiado similar a artículos ya publicados:
{recent_titles}

Transforma el tema en un artículo completamente diferente usando este ángulo específico: {angle}

El nuevo tema debe:
- Ser concreto y diferente de los ya publicados
- Mencionar una herramienta, empresa o caso de uso real
- Tener un título atractivo para developers o founders

Responde ÚNICAMENTE con el nuevo título/ángulo (1 línea, máximo 120 caracteres)."""

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
        print(f"  ⚠️  Error mutando: {e}")
        return original

# ── BUILD CANDIDATE POOL ──────────────────────────────────────────────────────
def build_candidate_pool(recent_articles: list[dict]) -> list[str]:
    """
    Builds a large pool of candidate topics from 4 sources.
    Returns a deduplicated list, most-specific-first.
    """
    print("🔍 Construyendo pool de candidatos (4 fuentes)...")

    pool = []

    # Source 1: Today's news
    print("  📰 Fuente 1: Noticias del día (SerpAPI news)...")
    news = fetch_serpapi_news()
    print(f"     → {len(news)} titulares obtenidos")
    pool.extend(news)

    # Source 2: Trending searches
    print("  📈 Fuente 2: Búsquedas trending (SerpAPI organic)...")
    trends = fetch_serpapi_trends()
    print(f"     → {len(trends)} tendencias obtenidas")
    pool.extend(trends)

    # Source 3: AI-generated niche topics
    print("  🧠 Fuente 3: Ideas de nicho (GPT-4o-mini)...")
    niche = generate_niche_topics(recent_articles, n=15)
    print(f"     → {len(niche)} ideas de nicho generadas")
    pool.extend(niche)

    # Source 4: Fallback hardcoded (always available)
    fallback = get_fallback_topics()
    pool.extend(fallback)

    # Deduplicate by exact text
    seen = set()
    unique = []
    for p in pool:
        key = p.lower().strip()[:60]
        if key not in seen and len(p) > 20:
            seen.add(key)
            unique.append(normalize_year(p))

    print(f"  ✅ Pool total: {len(unique)} candidatos únicos")
    return unique

# ── GENERATE ARTICLE WITH CLAUDE ─────────────────────────────────────────────
def generate_article(keyword: str, recent_context: str) -> dict:
    print(f"  ✍️  Claude generando ES: {keyword[:70]}...")
    category = detect_category(keyword)
    prompt = f"""Escribe un artículo completo en español sobre: "{keyword}"

ARTÍCULOS YA PUBLICADOS EN NEWSTIDE (no repitas estas temáticas ni estos ángulos):
{recent_context}

ESTRUCTURA (usa markdown):
- Título H1 atractivo y específico (no el keyword literal)
- Introducción de 2 párrafos que enganche desde la primera frase
- 3 o 4 secciones H2 con contenido de valor real
- Subsecciones H3 cuando sea necesario
- Conclusión con reflexión propia y pregunta al lector

REQUISITOS:
- Entre 1.200 y 1.600 palabras
- Datos concretos, ejemplos reales, perspectiva propia
- Tono: experto pero accesible, no corporativo
- Nunca empieces con "En el mundo de..." ni frases genéricas
- Categoría del artículo: {category}
- El año actual es 2026. Actualiza referencias de años anteriores a 2026 salvo contexto histórico imprescindible.
- El artículo DEBE ofrecer un ángulo diferente a los ya publicados — profundiza en lo específico

Al final, en línea separada escribe exactamente:
EXCERPT: [resumen de 1 frase, máximo 150 caracteres]"""

    message = claude_client.messages.create(
        model=MODEL_GENERATE, max_tokens=2800,
        messages=[{"role": "user", "content": prompt}],
        system="Eres un periodista tech senior especializado en IA, startups y herramientas digitales. Escribes para NewsTide, un medio tech premium en español para founders y developers. Tu estilo es claro, directo y con perspectiva propia. La fecha actual es 2026. Cada artículo debe tener un ángulo único y concreto."
    )
    raw = message.content[0].text
    excerpt = ""
    if "EXCERPT:" in raw:
        parts = raw.split("EXCERPT:")
        raw = parts[0].strip()
        excerpt = parts[1].strip()[:200]
    return {"content": raw, "excerpt": excerpt, "category": category}

# ── HUMANIZE WITH GPT ─────────────────────────────────────────────────────────
def humanize(text: str) -> str:
    print("  🧠 GPT humanizando ES...")
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": """Eres un editor humano con 15 años de experiencia en medios digitales.
Reescribe el artículo aplicando estas reglas SIN cambiar el contenido ni los datos:
- Mezcla frases cortas (5-8 palabras) con frases largas (18-28 palabras)
- Usa conectores variados: "sin embargo", "dicho esto", "lo curioso es que", "ojo"
- Añade opinión ocasional: "lo que más me sorprende", "honestamente", "en mi experiencia"
- Incluye 1-2 preguntas retóricas naturales
- "fundamental" → "clave", "en conclusión" → "para cerrar", "robusto" → "sólido"
Mantén todos los encabezados markdown. Devuelve SOLO el artículo, sin explicaciones."""},
            {"role": "user", "content": text}
        ],
        temperature=0.88, max_tokens=2800
    )
    return response.choices[0].message.content

# ── TRANSLATE + HUMANIZE EN ───────────────────────────────────────────────────
def translate_to_english(es_content: str, es_excerpt: str, es_title: str) -> dict:
    print("  🌐 GPT traduciendo EN...")
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": "You are a professional tech journalist and translator. Translate the following Spanish tech article to natural, fluent American English. Keep all markdown formatting. Adapt idioms naturally. At the end write: TITLE_EN: [translated H1 title] and EXCERPT_EN: [one sentence summary, max 150 chars]"},
            {"role": "user", "content": f"TITLE: {es_title}\nEXCERPT: {es_excerpt}\n\n{es_content}"}
        ],
        temperature=0.75, max_tokens=2800
    )
    raw = response.choices[0].message.content
    title_en, excerpt_en, content_en = es_title, es_excerpt, raw

    if "TITLE_EN:" in raw:
        parts = raw.split("TITLE_EN:")
        content_en = parts[0].strip()
        rest = parts[1]
        if "EXCERPT_EN:" in rest:
            title_en = rest.split("EXCERPT_EN:")[0].strip()[:150]
            excerpt_en = rest.split("EXCERPT_EN:")[1].strip()[:200]
        else:
            title_en = rest.strip()[:150]
    elif "EXCERPT_EN:" in raw:
        parts = raw.split("EXCERPT_EN:")
        content_en = parts[0].strip()
        excerpt_en = parts[1].strip()[:200]

    return {"title_en": title_en, "content_en": content_en, "excerpt_en": excerpt_en}

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
            print(f"  🖼️  Imagen: '{query}' → {img['author']}")
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

# ── SAVE TO SUPABASE ──────────────────────────────────────────────────────────
def save_article(keyword, content_es, excerpt_es, category, idx, content_en, title_en, excerpt_en):
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

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {
        "title":         title_es,
        "slug":          slugify(title_es),
        "content":       content_es,
        "excerpt":       excerpt_es or title_es[:150],
        "title_en":      title_en or title_es,
        "content_en":    content_en,
        "excerpt_en":    excerpt_en or excerpt_es or title_es[:150],
        "category":      category,
        "author":        AUTHORS[idx % len(AUTHORS)],
        "keyword":       keyword,
        "keyword_hash":  md5(keyword),
        "reading_time":  reading_time(content_es),
        "featured":      idx == 0,
        "image_gradient": GRADIENTS[idx % len(GRADIENTS)],
        "published_at":  now_iso,
    }
    try:
        supabase_client.table("articles").insert(data).execute()
        print(f"  ✅ Guardado: {title_es[:70]}")
        return title_es
    except Exception as e:
        print(f"  ❌ Error guardando: {e}")
        return None

# ── PROCESS ONE TOPIC → ARTICLE ───────────────────────────────────────────────
def process_topic(topic: str, recent_articles: list[dict], published_this_run: list[str], article_idx: int) -> str | None:
    """
    Takes a raw topic, validates it's not a duplicate (with mutation retry),
    generates, humanizes, translates and saves. Returns saved title or None.
    """
    recent_context = format_recent_context(recent_articles)

    # Dedup loop: up to 5 mutation attempts
    candidate = topic
    for attempt in range(5):
        if not is_duplicate_topic(candidate, recent_articles, published_this_run):
            break
        print(f"  ⚠️  Duplicado detectado — mutando (intento {attempt+1}/5)...")
        candidate = mutate_topic(candidate, recent_articles, attempt)
    else:
        print(f"  ❌ No se pudo encontrar ángulo único para: {topic[:50]} — saltando")
        return None

    # Also skip if exact hash already in DB
    if already_published_hash(candidate):
        print(f"  ⏭️  Hash exacto ya existe — saltando")
        return None

    print(f"  🎯 Topic aprobado: {candidate[:80]}")

    try:
        result    = generate_article(candidate, recent_context)
        humanized = humanize(result["content"])

        # Extract actual title from generated content
        title_preview = candidate[:100]
        for line in humanized.strip().split("\n")[:5]:
            if line.strip().startswith("# "):
                title_preview = line.strip()[2:].strip()
                break

        print("  🔍 Buscando imágenes Unsplash...")
        queries    = get_image_queries(title_preview, result["excerpt"])
        cover_img  = fetch_best_image(queries, title_preview, idx=0)
        inline_img = fetch_best_image(queries, title_preview, idx=1)
        content_es = inject_images(humanized, cover_img, inline_img)

        en = translate_to_english(content_es, result["excerpt"], title_preview)

        saved_title = save_article(
            candidate, content_es, result["excerpt"], result["category"],
            article_idx, en["content_en"], en["title_en"], en["excerpt_en"]
        )
        return saved_title

    except Exception as e:
        print(f"  ❌ Error procesando '{candidate[:50]}': {e}")
        return None

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n🚀 NewsTide Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # 1. Load existing articles for dedup context
    print("📚 Cargando artículos recientes de Supabase...")
    recent_articles = get_recent_articles()
    print(f"   {len(recent_articles)} artículos del último mes cargados")

    # 2. Build large candidate pool from 4 sources
    candidate_pool = build_candidate_pool(recent_articles)

    # 3. Publish loop — keep going until 3 articles published
    published_titles: list[str] = []   # titles published in THIS run (for intra-run dedup)
    pool_index = 0
    extra_niche_attempts = 0

    print(f"\n🎯 Objetivo: {ARTICLES_PER_RUN} artículos\n")

    while len(published_titles) < ARTICLES_PER_RUN:

        # If we've exhausted the pool, generate more niche topics on-the-fly
        if pool_index >= len(candidate_pool):
            extra_niche_attempts += 1
            if extra_niche_attempts > 4:
                print("⚠️  Pool agotado tras múltiples expansiones — forzando fallbacks directos")
                # Force-generate with unique timestamp to avoid dedup
                ts = datetime.now().strftime("%H:%M:%S")
                forced_topics = [
                    f"Cómo Claude 3.5 Sonnet supera a GPT-4o en tareas de código ({ts})",
                    f"El estado del mercado de IA en Europa en junio 2026: datos reales ({ts})",
                    f"Por qué los developers están abandonando ChatGPT por alternativas ({ts})",
                ]
                candidate_pool.extend(forced_topics)
            else:
                print(f"\n♻️  Pool agotado — generando más temas de nicho (expansión {extra_niche_attempts})...")
                extra = generate_niche_topics(recent_articles + [{"title": t, "category": "IA", "keyword": t, "excerpt": ""} for t in published_titles], n=10)
                candidate_pool.extend(extra)
                if not extra:
                    candidate_pool.extend(get_fallback_topics())
            continue  # restart loop check

        topic = candidate_pool[pool_index]
        pool_index += 1

        print(f"\n📝 [{len(published_titles)+1}/{ARTICLES_PER_RUN}] Procesando: {topic[:70]}")

        saved = process_topic(
            topic,
            recent_articles,
            published_titles,
            article_idx=len(published_titles)
        )

        if saved:
            published_titles.append(saved)
            # Add to recent_articles in memory so next article avoids it too
            recent_articles.insert(0, {
                "title": saved,
                "keyword": topic,
                "category": detect_category(topic),
                "excerpt": ""
            })
            print(f"\n✅ Artículo {len(published_titles)}/{ARTICLES_PER_RUN} publicado: {saved[:60]}")
            if len(published_titles) < ARTICLES_PER_RUN:
                print("   Continuando con el siguiente...\n")
            time.sleep(2)

    print(f"\n{'='*60}")
    print(f"🎉 Pipeline completado: {len(published_titles)} artículos publicados")
    for i, t in enumerate(published_titles, 1):
        print(f"   {i}. {t[:80]}")

if __name__ == "__main__":
    main()
