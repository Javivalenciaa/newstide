import os
import hashlib
import re
import time
from datetime import datetime
from serpapi import GoogleSearch
from openai import OpenAI
import anthropic
from supabase import create_client

# ── CONFIG ─────────────────────────────────────────────────────────────────
SERPAPI_KEY          = os.environ["SERPAPI_KEY"]
OPENAI_API_KEY       = os.environ["OPENAI_API_KEY"]
ANTHROPIC_API_KEY    = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

ARTICLES_PER_DAY     = 3
MODEL_GENERATE       = "claude-sonnet-4-5"   # Claude para generar (calidad)
MODEL_HUMANIZE       = "gpt-4o-mini"          # GPT para humanizar (barato)

openai_client    = OpenAI(api_key=OPENAI_API_KEY)
claude_client    = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
supabase_client  = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

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

# ── HELPERS ────────────────────────────────────────────────────────────────
def slugify(text):
    text = text.lower()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n"),("ü","u")]:
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9\\s-]", "", text)
    text = re.sub(r"[\\s]+", "-", text.strip())
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

# ── STEP 1: TRENDING KEYWORDS ─────────────────────────────────────────────
def get_keywords():
    print("🔍 Buscando tendencias...")
    keywords = []
    queries = [
        "inteligencia artificial noticias",
        "startups tecnología España",
        "herramientas IA productividad",
    ]
    for q in queries:
        try:
            results = GoogleSearch({
                "q": q, "location": "Spain", "hl": "es", "gl": "es",
                "api_key": SERPAPI_KEY, "num": 10
            }).get_dict()
            for r in results.get("organic_results", [])[:4]:
                title = r.get("title", "")
                if title and len(title) > 20:
                    keywords.append(title)
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

# ── STEP 2: GENERATE WITH CLAUDE ──────────────────────────────────────────
def generate_article(keyword):
    print(f"  ✍️  Claude generando: {keyword[:60]}...")
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

Al final, en línea separada escribe exactamente:
EXCERPT: [resumen de 1 frase, máximo 150 caracteres]"""

    message = claude_client.messages.create(
        model=MODEL_GENERATE,
        max_tokens=2800,
        messages=[{"role": "user", "content": prompt}],
        system="Eres un periodista tech senior especializado en IA, startups y herramientas digitales. Escribes para NewsTide, un medio tech premium en español para founders y developers. Tu estilo es claro, directo y con perspectiva propia."
    )

    raw = message.content[0].text
    excerpt = ""
    if "EXCERPT:" in raw:
        parts = raw.split("EXCERPT:")
        raw = parts[0].strip()
        excerpt = parts[1].strip()[:200]

    return {"content": raw, "excerpt": excerpt, "category": category}

# ── STEP 3: HUMANIZE WITH GPT-4O MINI ────────────────────────────────────
def humanize(text):
    print("  🧠 GPT humanizando...")
    response = openai_client.chat.completions.create(
        model=MODEL_HUMANIZE,
        messages=[
            {"role": "system", "content": """Eres un editor humano con 15 años de experiencia en medios digitales.
Reescribe el artículo aplicando estas reglas SIN cambiar el contenido ni los datos:

ESTILO:
- Mezcla frases cortas (5-8 palabras) con frases largas (18-28 palabras)
- Usa conectores variados: "sin embargo", "dicho esto", "lo curioso es que", "ojo"
- Añade opinión ocasional: "lo que más me sorprende", "honestamente", "en mi experiencia"
- Incluye 1-2 preguntas retóricas naturales

VOCABULARIO (sustituye palabras típicas de IA):
- "fundamental" → "clave"
- "en conclusión" → "para cerrar"
- "es importante destacar" → reescribir o eliminar
- "robusto" → "sólido" o "fiable"
- "implementar" → "aplicar" o "poner en marcha"

Mantén todos los encabezados markdown. Devuelve SOLO el artículo, sin explicaciones."""},
            {"role": "user", "content": text}
        ],
        temperature=0.88,
        max_tokens=2800
    )
    return response.choices[0].message.content

# ── STEP 4: SAVE TO SUPABASE ──────────────────────────────────────────────
def save_article(keyword, content, excerpt, category, idx):
    lines = content.strip().split("\\n")
    title = keyword[:100]
    for line in lines[:5]:
        if line.strip().startswith("# "):
            title = line.strip()[2:].strip()
            break

    # Quitar la línea H1 del contenido
    if lines and lines[0].strip().startswith("# "):
        content = "\\n".join(lines[1:]).strip()

    data = {
        "title": title,
        "slug": slugify(title),
        "content": content,
        "excerpt": excerpt or title[:150],
        "category": category,
        "author": AUTHORS[idx % len(AUTHORS)],
        "keyword": keyword,
        "keyword_hash": md5(keyword),
        "reading_time": reading_time(content),
        "featured": idx == 0,
        "image_gradient": GRADIENTS[idx % len(GRADIENTS)],
    }

    try:
        supabase_client.table("articles").insert(data).execute()
        print(f"  ✅ Guardado: {title[:60]}")
        return True
    except Exception as e:
        print(f"  ❌ Error guardando: {e}")
        return False

# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    print(f"\\n🚀 NewsTide Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
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
        print(f"\\n📝 Artículo {i+1}/{min(len(nuevas), ARTICLES_PER_DAY)}")
        try:
            result = generate_article(keyword)
            humanized = humanize(result["content"])
            if save_article(keyword, humanized, result["excerpt"], result["category"], i):
                publicados += 1
            time.sleep(2)
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\\n✅ Completado: {publicados} artículos publicados")

if __name__ == "__main__":
    main()

with open('/home/user/output/requirements.txt', 'w') as f:
    f.write(requirements_updated)

print("Pipeline con Claude listo")
print("\nCambios respecto a la versión anterior:")
print("  - Línea 13: ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']")
print("  - Línea 17: MODEL_GENERATE = 'claude-sonnet-4-5'")
print("  - Línea 20: claude_client = anthropic.Anthropic(...)")
print("  - Función generate_article: usa claude_client.messages.create()")
print("  - requirements.txt: añadido anthropic>=0.25.0")
print("  - daily.yml: añadir secret ANTHROPIC_API_KEY")