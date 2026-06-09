import os
import hashlib
import re
import time
import requests
from datetime import datetime, timezone
from serpapi import GoogleSearch
from openai import OpenAI
import anthropic
from supabase import create_client

# ── CONFIG ───────────────────────────────────────────────────────────────────
SERPAPI_KEY          = os.environ["SERPAPI_KEY"]
OPENAI_API_KEY       = os.environ["OPENAI_API_KEY"]
ANTHROPIC_API_KEY    = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
UNSPLASH_ACCESS_KEY  = os.environ["UNSPLASH_ACCESS_KEY"]

ARTICLES_PER_DAY     = 3
MODEL_GENERATE       = "claude-sonnet-4-5"
MODEL_HUMANIZE       = "gpt-4o-mini"

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
    "chatgpt": "IA", "claude": "IA", "openai": "IA",
    "startup": "Startups", "emprendimiento": "Startups", "financiación": "Startups",
    "herramienta": "Herramientas", "software": "Herramientas",
    "tutorial": "Tutoriales", "cómo": "Tutoriales", "guía": "Tutoriales",
}

AUTHORS = [
    "Ana Martínez", "Carlos Ruiz", "María López",
    "Pedro Sánchez", "Sofía Jiménez", "Luis Torres"
]

# ── HELPERS ──────────────────────────────────────────────────────────────────
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

def already_published(keyword):
    res = supabase_client.table("articles").select("id").eq("keyword_hash", md5(keyword)).execute()
    return len(res.data) > 0

def normalize_year(text: str) -> str:
    return re.sub(r'\b(2023|2024|2025)\b', '2026', text)

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
        msg = claude_client.messages.create(
            model="claude-haiku-4-5", max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        lines = [l.strip() for l in msg.content[0].text.strip().splitlines() if l.strip()]
        return lines[:3] if lines else ["technology innovation", "digital future", "startup team"]
    except Exception as e:
        print(f"  Claude haiku error: {e}")
        return ["technology innovation", "digital future", "startup team"]

def validate_image(image: dict, title: str) -> bool:
    try:
        msg = claude_client.messages.create(
            model="claude-haiku-4-5", max_tokens=5,
            messages=[{"role": "user", "content": f"Article title: {title}\nImage description: {image['alt']}\n\nIs this image visually relevant and appropriate for a professional tech article? Reply with only YES or NO."}],
        )
        return msg.content[0].text.strip().upper().startswith("Y")
    except:
        return True

def fetch_best_image(queries: list[str], title: str, idx: int = 0) -> dict | None:
    for query in queries:
        img = get_unsplash_image(query, idx=idx)
        if img and validate_image(img, title):
            print(f"  🖼️  Imagen: '{query}' → {img['author']}")
            return img
        time.sleep(0.5)
    return None

# ── STEP 1: TRENDING KEYWORDS ─────────────────────────────────────────────────
def get_keywords():
    print("🔍 Buscando tendencias...")
    keywords = []
    for q in ["inteligencia artificial noticias", "startups tecnología España", "herramientas IA productividad"]:
        try:
            results = GoogleSearch({"q": q, "location": "Spain", "hl": "es", "gl": "es", "api_key": SERPAPI_KEY, "num": 10}).get_dict()
            for r in results.get("organic_results", [])[:4]:
                t = r.get("title", "")
                if t and len(t) > 20:
                    keywords.append(t)
        except Exception as e:
            print(f"  SerpAPI error: {e}")
        time.sleep(1)
    if not keywords:
        keywords = [
            "Cómo usar la IA para automatizar tu negocio en 2026",
            "Las mejores herramientas de IA para startups este año",
            "Guía completa de Claude vs GPT-4o para developers",
        ]
    return keywords

# ── STEP 2: GENERATE ES WITH CLAUDE ──────────────────────────────────────────
def generate_article(keyword):
    print(f"  ✍️  Claude generando ES: {keyword[:60]}...")
    category = detect_category(keyword)
    prompt = f"""Escribe un artículo completo en español sobre: "{keyword}"

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
- El año actual es 2026. Si el keyword menciona años anteriores como 2023, 2024 o 2025 en un contexto de actualidad o consejo, actualízalos a 2026. Solo conserva el año original si es una referencia histórica imprescindible.

Al final, en línea separada escribe exactamente:
EXCERPT: [resumen de 1 frase, máximo 150 caracteres]"""

    message = claude_client.messages.create(
        model=MODEL_GENERATE, max_tokens=2800,
        messages=[{"role": "user", "content": prompt}],
        system="Eres un periodista tech senior especializado en IA, startups y herramientas digitales. Escribes para NewsTide, un medio tech premium en español para founders y developers. Tu estilo es claro, directo y con perspectiva propia. La fecha actual es 2026; nunca uses 2024 o 2025 como año vigente salvo contexto histórico."
    )
    raw = message.content[0].text
    excerpt = ""
    if "EXCERPT:" in raw:
        parts = raw.split("EXCERPT:")
        raw = parts[0].strip()
        excerpt = parts[1].strip()[:200]
    return {"content": raw, "excerpt": excerpt, "category": category}

# ── STEP 3: HUMANIZE ES ───────────────────────────────────────────────────────
def humanize(text):
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

# ── STEP 4: TRANSLATE + HUMANIZE EN ──────────────────────────────────────────
def translate_to_english(es_content: str, es_excerpt: str, es_title: str) -> dict:
    print("  🌐 GPT traduciendo EN...")
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": "You are a professional tech journalist and translator. Translate the following Spanish tech article to natural, fluent American English. Keep all markdown formatting (headings, bold, lists). Adapt idioms and expressions naturally — do not translate literally. Keep the same structure and length. At the end, on a separate line, write exactly: TITLE_EN: [translated H1 title] and EXCERPT_EN: [one sentence summary, max 150 chars]"},
            {"role": "user", "content": f"TITLE: {es_title}\nEXCERPT: {es_excerpt}\n\n{es_content}"}
        ],
        temperature=0.75, max_tokens=2800
    )
    raw = response.choices[0].message.content
    title_en = es_title  # fallback
    excerpt_en = es_excerpt
    content_en = raw

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

# ── STEP 5: INJECT IMAGES ────────────────────────────────────────────────────
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

# ── STEP 6: SAVE TO SUPABASE ─────────────────────────────────────────────────
def save_article(keyword, content_es, excerpt_es, category, idx, content_en, title_en, excerpt_en):
    lines = content_es.strip().split("\n")
    title_es = keyword[:100]
    for line in lines[:5]:
        if line.strip().startswith("# "):
            title_es = line.strip()[2:].strip()
            break
    if lines and lines[0].strip().startswith("# "):
        content_es = "\n".join(lines[1:]).strip()

    # strip H1 from EN content too
    en_lines = content_en.strip().split("\n")
    if en_lines and en_lines[0].strip().startswith("# "):
        content_en = "\n".join(en_lines[1:]).strip()

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {
        "title":      title_es,
        "slug":       slugify(title_es),
        "content":    content_es,
        "excerpt":    excerpt_es or title_es[:150],
        "title_en":   title_en or title_es,
        "content_en": content_en,
        "excerpt_en": excerpt_en or excerpt_es or title_es[:150],
        "category":   category,
        "author":     AUTHORS[idx % len(AUTHORS)],
        "keyword":    keyword,
        "keyword_hash": md5(keyword),
        "reading_time": reading_time(content_es),
        "featured":   idx == 0,
        "image_gradient": GRADIENTS[idx % len(GRADIENTS)],
        "published_at":   now_iso,
    }
    try:
        supabase_client.table("articles").insert(data).execute()
        print(f"  ✅ Guardado: {title_es[:60]}")
        return True
    except Exception as e:
        print(f"  ❌ Error guardando: {e}")
        return False

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n🚀 NewsTide Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    keywords = get_keywords()
    nuevas = [k for k in keywords if not already_published(k)]
    print(f"📋 Keywords nuevas: {len(nuevas)}")
    if not nuevas:
        nuevas = [
            f"Tendencias IA para empresas {datetime.now().strftime('%B %Y')}",
            f"Mejores herramientas tech {datetime.now().strftime('%B %Y')}",
        ]

    publicados = 0
    for i, keyword in enumerate(nuevas[:ARTICLES_PER_DAY]):
        print(f"\n📝 Artículo {i+1}/{min(len(nuevas), ARTICLES_PER_DAY)}")
        try:
            kw = normalize_year(keyword)
            if kw != keyword:
                print(f"  📅 Keyword normalizado: {kw[:80]}")

            result   = generate_article(kw)
            humanized = humanize(result["content"])

            title_preview = kw[:100]
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

            if save_article(kw, content_es, result["excerpt"], result["category"], i,
                            en["content_en"], en["title_en"], en["excerpt_en"]):
                publicados += 1
            time.sleep(2)
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\n✅ Completado: {publicados} artículos publicados")

if __name__ == "__main__":
    main()
