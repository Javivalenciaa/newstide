#!/usr/bin/env python3
"""
NewsTide pSEO Pipeline
======================
Generates evergreen English-only pSEO pages (comparisons, alternatives, guides)
and writes them to the `pseo_pages` Supabase table.

Strategy: English-first, low-authority domain tactics.
- Long-tail, low-competition keywords (< 1k monthly searches)
- High commercial intent: "X vs Y", "best alternatives to X", "X for [profession]"
- ZERO SerpAPI calls — purely template-driven (no extra API cost)
- GPT-4o for generation (cheap + fast)
- claude-sonnet-4-5 NOT used here — saves budget for daily news pipeline

Usage (via GitHub Actions workflow_dispatch):
  python pipeline/pseo_pipeline.py --template comparisons --batch 10
  python pipeline/pseo_pipeline.py --template alternatives --batch 10
  python pipeline/pseo_pipeline.py --template guides --batch 10
  python pipeline/pseo_pipeline.py --template for-profession --batch 10
"""

import os
import re
import time
import hashlib
import argparse
import random
import requests
from datetime import datetime, timezone, timedelta
from openai import OpenAI
from supabase import create_client

# ── CONFIG ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY       = os.environ["OPENAI_API_KEY"]
SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

MODEL_GENERATE  = "gpt-4o"
MODEL_FAST      = "gpt-4o-mini"

MIN_WORD_COUNT   = 800
MIN_H2_SECTIONS  = 4
TITLE_MAX        = 62
TITLE_MIN        = 48
EXCERPT_MAX      = 155
EXCERPT_MIN      = 120

openai_client   = OpenAI(api_key=OPENAI_API_KEY)
supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ── INDEXNOW ──────────────────────────────────────────────────────────────────
INDEXNOW_KEY      = "964bf589528b466cace60749e05cfcb6"
INDEXNOW_HOST     = "www.newstide.news"
INDEXNOW_KEY_LOC  = f"https://{INDEXNOW_HOST}/{INDEXNOW_KEY}.txt"

def ping_indexnow(urls: list) -> None:
    """Notify Bing/IndexNow about new URLs. Non-blocking — never crashes the pipeline."""
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

GRADIENTS = [
    "linear-gradient(135deg,#0d2a2e,#0d1a2e)",
    "linear-gradient(135deg,#1a0d2e,#2e0d1a)",
    "linear-gradient(135deg,#2e1a0d,#1a2e0d)",
    "linear-gradient(135deg,#0d2e1a,#0d2e2a)",
    "linear-gradient(135deg,#2e0d0d,#1a0d2e)",
    "linear-gradient(135deg,#0d1a2e,#2e2a0d)",
]

# ── KEYWORD UNIVERSE ──────────────────────────────────────────────────────────
TOOL_CATEGORIES = {
    "llm_chatbots": [
        "ChatGPT", "Claude", "Gemini", "Perplexity", "Mistral",
        "Grok", "Llama", "Command R+",
    ],
    "ai_coding": [
        "Cursor", "GitHub Copilot", "Windsurf", "Bolt", "Lovable",
        "Replit AI", "Codeium", "Tabnine",
    ],
    "automation": [
        "n8n", "Make", "Zapier", "Activepieces", "Pipedream",
        "Tray.io", "Workato",
    ],
    "ai_writing": [
        "Jasper", "Copy.ai", "Writesonic", "Rytr",
        "Grammarly", "Sudowrite", "Anyword",
    ],
    "databases": [
        "Supabase", "PlanetScale", "Neon", "Firebase", "Xata", "Turso",
    ],
    "hosting_deployment": [
        "Vercel", "Netlify", "Railway", "Render", "Fly.io", "Coolify",
    ],
    "image_generation": [
        "Midjourney", "DALL-E 3", "Stable Diffusion", "Ideogram", "Flux",
        "Adobe Firefly", "Leonardo AI", "Playground AI",
    ],
    "ai_video": [
        "HeyGen", "Synthesia", "Descript", "CapCut AI", "Runway", "Pika", "Luma AI",
    ],
    "ai_audio_music": [
        "ElevenLabs", "Suno", "Udio", "Mubert", "Soundraw",
    ],
    "project_management": [
        "Linear", "Height", "Jira", "Asana", "ClickUp",
        "Monday.com", "Basecamp", "Plane",
    ],
    "design_nocode": [
        "Figma AI", "Framer", "Webflow", "Wix AI", "Squarespace AI",
        "Canva AI", "Builder.io",
    ],
    "knowledge_docs": [
        "Notion", "Obsidian", "Coda", "Confluence", "Airtable",
        "ClickUp Docs", "Roam Research",
    ],
    "ai_agents_frameworks": [
        "LangChain", "LlamaIndex", "CrewAI", "AutoGen", "Haystack",
        "Flowise", "Dify",
    ],
    "vector_databases": [
        "Pinecone", "Weaviate", "Chroma", "Qdrant", "Milvus",
        "pgvector", "Zilliz",
    ],
}

ALL_TOOLS = [tool for tools in TOOL_CATEGORIES.values() for tool in tools]

PROFESSIONS = [
    "indie hackers", "solo founders", "startup founders", "developers",
    "freelancers", "content creators", "product managers", "designers",
    "data scientists", "marketing teams", "sales teams", "recruiters",
    "lawyers", "accountants", "teachers", "researchers", "copywriters",
    "YouTubers", "podcasters", "e-commerce sellers",
]

USE_CASES = [
    "coding", "writing", "SEO", "customer support", "data analysis",
    "video editing", "image generation", "automation", "note-taking",
    "project management", "email writing", "market research",
    "building MVPs", "generating leads", "creating content",
    "saving money", "replacing employees", "scaling fast",
]

# ── LIVE DEDUPLICATION CACHE ──────────────────────────────────────────────────
def load_existing_pairs() -> set:
    existing = set()
    try:
        res = supabase_client.table("pseo_pages") \
            .select("entity_a,entity_b,slug,keyword_hash") \
            .execute()
        for row in res.data:
            a = (row.get("entity_a") or "").lower().strip()
            b = (row.get("entity_b") or "").lower().strip()
            if a and b:
                existing.add(frozenset([a, b]))
    except Exception as e:
        print(f"  ⚠️  Could not load existing pairs: {e}")
    return existing


# ── TEMPLATE ENGINES ──────────────────────────────────────────────────────────

def generate_comparison_candidates(n: int, existing_pairs: set) -> list[dict]:
    candidates = []
    seen_pairs = set()

    for category, tools in TOOL_CATEGORIES.items():
        if len(tools) < 2:
            continue
        tools_shuffled = tools.copy()
        random.shuffle(tools_shuffled)
        for i in range(len(tools_shuffled)):
            for j in range(i + 1, len(tools_shuffled)):
                a, b = tools_shuffled[i], tools_shuffled[j]
                pair_key   = tuple(sorted([a.lower(), b.lower()]))
                pair_frozen = frozenset([a.lower(), b.lower()])
                if pair_key in seen_pairs:
                    continue
                if pair_frozen in existing_pairs:
                    continue
                seen_pairs.add(pair_key)
                slug = f"{slugify(a)}-vs-{slugify(b)}"
                candidates.append({
                    "template": "comparisons",
                    "slug":     slug,
                    "keyword":  f"{a} vs {b}",
                    "entity_a": a,
                    "entity_b": b,
                    "category": category,
                })

    random.shuffle(candidates)
    return candidates[:n * 4]


def generate_alternatives_candidates(n: int, existing_pairs: set) -> list[dict]:
    tools = ALL_TOOLS.copy()
    random.shuffle(tools)
    candidates = []
    for tool in tools:
        pair = frozenset([tool.lower(), "__alternatives__"])
        if pair in existing_pairs:
            continue
        candidates.append({
            "template": "alternatives",
            "slug":     f"best-alternatives-to-{slugify(tool)}",
            "keyword":  f"best alternatives to {tool}",
            "entity_a": tool,
            "entity_b": None,
        })
    return candidates[:n * 3]


def generate_guides_candidates(n: int, existing_pairs: set) -> list[dict]:
    combos = [(tool, use) for tool in ALL_TOOLS for use in USE_CASES]
    random.shuffle(combos)
    candidates = []
    for tool, use_case in combos:
        pair = frozenset([tool.lower(), use_case.lower()])
        if pair in existing_pairs:
            continue
        candidates.append({
            "template": "guides",
            "slug":     f"how-to-use-{slugify(tool)}-for-{slugify(use_case)}",
            "keyword":  f"how to use {tool} for {use_case}",
            "entity_a": tool,
            "entity_b": use_case,
        })
        if len(candidates) >= n * 4:
            break
    return candidates[:n * 3]


def generate_for_profession_candidates(n: int, existing_pairs: set) -> list[dict]:
    candidates = []
    for profession in PROFESSIONS:
        pair = frozenset([profession.lower(), "__best_tools__"])
        if pair not in existing_pairs:
            candidates.append({
                "template": "for-profession",
                "slug":     f"best-ai-tools-for-{slugify(profession)}",
                "keyword":  f"best AI tools for {profession}",
                "entity_a": profession,
                "entity_b": None,
            })
    for tool in random.sample(ALL_TOOLS, min(25, len(ALL_TOOLS))):
        for profession in random.sample(PROFESSIONS, 3):
            pair = frozenset([tool.lower(), profession.lower()])
            if pair in existing_pairs:
                continue
            candidates.append({
                "template": "for-profession",
                "slug":     f"{slugify(tool)}-for-{slugify(profession)}",
                "keyword":  f"{tool} for {profession}",
                "entity_a": tool,
                "entity_b": profession,
            })
    random.shuffle(candidates)
    return candidates[:n * 3]


TEMPLATE_GENERATORS = {
    "comparisons":    generate_comparison_candidates,
    "alternatives":   generate_alternatives_candidates,
    "guides":         generate_guides_candidates,
    "for-profession": generate_for_profession_candidates,
}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text[:70].strip("-")

def md5(text: str) -> str:
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def smart_trim(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= limit:
        return text
    cut = text[:limit + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.strip(" -:;,.")

def normalize_excerpt(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip()).strip(' "\'')
    if len(text) <= EXCERPT_MAX:
        return text
    cut = text[:EXCERPT_MAX + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.strip(" -:;,.") + "."

def reading_time(text: str) -> int:
    return max(5, round(len(text.split()) / 200))

def strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```(?:markdown|md)?\s*\n', '', text)
    text = re.sub(r'\n```\s*$', '', text)
    return text.strip()

def validate_content(content: str, label: str = "") -> bool:
    words = len(content.split())
    h2s   = len(re.findall(r'^## ', content, re.MULTILINE))
    ok    = True
    if words < MIN_WORD_COUNT:
        print(f"  ❌ [{label}] Only {words} words (min {MIN_WORD_COUNT})")
        ok = False
    if h2s < MIN_H2_SECTIONS:
        print(f"  ❌ [{label}] Only {h2s} H2 sections (min {MIN_H2_SECTIONS})")
        ok = False
    if ok:
        print(f"  ✅ [{label}] {words} words, {h2s} H2 sections")
    return ok

# ── SLUG/HASH DEDUPLICATION ───────────────────────────────────────────────────

def already_exists(slug: str) -> bool:
    res = supabase_client.table("pseo_pages").select("id").eq("slug", slug).execute()
    return len(res.data) > 0

def already_exists_hash(keyword: str) -> bool:
    res = supabase_client.table("pseo_pages").select("id").eq("keyword_hash", md5(keyword)).execute()
    return len(res.data) > 0

# ── TITLE PATTERNS ────────────────────────────────────────────────────────────

CTR_TITLE_PATTERNS = {
    "comparisons": [
        "{a} vs {b}: The Honest Verdict for Developers (2026)",
        "{a} vs {b} in 2026: I Tested Both So You Don't Have To",
        "{a} vs {b}: Which One Saves More Money for Startups?",
        "{a} vs {b}: The Feature Breakdown Nobody Shows You",
        "{a} or {b}? A Solo Founder's Honest Take in 2026",
    ],
    "alternatives": [
        "7 Best Alternatives to {a} in 2026 (Free + Paid)",
        "Top {a} Alternatives for Developers Who Need More",
        "I Tried 9 {a} Alternatives — Here Are the 4 Worth It",
        "Best {a} Alternatives in 2026: Ranked by Real Teams",
        "Tired of {a}? 6 Alternatives Better for Founders",
    ],
    "guides": [
        "How to Use {a} for {b} in 2026 (Full Walkthrough)",
        "{a} for {b}: The Step-by-Step Guide Nobody Wrote Yet",
        "Using {a} for {b}: What Actually Works in 2026",
        "The Right Way to Use {a} for {b} (Real Examples)",
        "{a} + {b}: The Workflow Saving Teams 10 Hours a Week",
    ],
    "for-profession": [
        "Best AI Tools for {a} in 2026 (I Use 3 of These Daily)",
        "10 AI Tools Every {a} Should Know in 2026",
        "How {a} Are Using AI to 10x Their Output in 2026",
        "The AI Stack for {a}: What's Actually Worth Paying For",
        "AI for {a}: Tools That Replaced Half My Workflow",
    ],
}

def pick_title(template: str, entity_a: str, entity_b: str | None) -> str:
    patterns = CTR_TITLE_PATTERNS.get(template, ["{a} — NewsTide Guide 2026"])
    pattern  = random.choice(patterns)
    title    = pattern.replace("{a}", entity_a).replace("{b}", entity_b or "")
    title    = smart_trim(title, TITLE_MAX)
    if len(title) < TITLE_MIN:
        title = smart_trim(f"{title} — 2026 Guide", TITLE_MAX)
    return title

# ── CONTENT GENERATION ────────────────────────────────────────────────────────

def build_prompt(template: str, title: str, keyword: str, entity_a: str, entity_b: str | None, category: str = "") -> str:
    year = "2026"

    pricing_rules = """
PRICING RULES (critical — violations will be rejected):
- Only state prices you are confident are accurate as of 2026.
- If you are NOT sure of the exact price, write: "pricing starts around $X/month" or "check their website for current pricing" — never invent specific numbers.
- For tools with public free tiers, mention them. For enterprise-only tools, say "custom pricing".
- Never write a price table with made-up numbers. Only include prices you know.
"""

    base_rules = (
        "You are a senior tech journalist writing for NewsTide, a premium English-language tech media.\n"
        "Audience: founders, developers, indie hackers. Smart, busy, skeptical of hype.\n"
        "Tone: direct, opinionated, slightly informal — like a smart friend who tested this stuff.\n"
        f"Year: {year}. Never reference years before {year} unless historically essential.\n"
        f"\n{pricing_rules}\n"
        "STRUCTURE (markdown):\n"
        "- NO H1 — title is handled separately\n"
        "- Introduction (no H2 header): lead with real tension or key insight. No \"In today's digital world\" openers.\n"
        f"- Minimum {MIN_H2_SECTIONS} H2 sections, each 120+ words\n"
        "- H3 subsections where helpful\n"
        "- Concrete examples, real pricing (hedged if uncertain), personal takes\n"
        "- End with \"## Verdict\" or \"## Bottom Line\" with a clear recommendation\n"
        "- \"## FAQ\" at the end with 3 questions in H3 format (for FAQPage schema)\n"
        "\n"
        f"MINIMUM {MIN_WORD_COUNT} WORDS — short content will be rejected automatically.\n"
        "\n"
        "SEO:\n"
        f"- Use keyword \"{keyword}\" naturally in first 100 words and 2-3x total\n"
        "- Related terms naturally woven in, no stuffing\n"
        "\n"
        "At the very end, single line:\n"
        f"EXCERPT: [one punchy sentence, {EXCERPT_MIN}-{EXCERPT_MAX} chars, suitable as Google meta description]\n"
    )

    if template == "comparisons":
        b = entity_b or "competitor"
        category_hint = f"\nNote: both tools are in the '{category}' category — make sure the comparison is relevant and makes sense for users choosing between them." if category else ""
        return (
            base_rules
            + f"\n\nARTICLE: \"{title}\"\nKeyword: {keyword}\n{category_hint}\n\n"
            + f"Write a genuine, opinionated comparison of {entity_a} vs {b}.\n\n"
            + "REQUIRED SECTIONS (use exactly these H2 titles):\n"
            + f"## {entity_a} — What It Actually Does Well\n"
            + f"## {b} — What It Actually Does Well\n"
            + "## Head-to-Head: Features, Pricing, Speed\n"
            + "(include a markdown comparison table — only use prices you are confident about, otherwise write \"check website\")\n"
            + f"## Who Should Choose {entity_a}\n"
            + f"## Who Should Choose {b}\n"
            + f"## Verdict: Which One Wins in {year}?\n"
            + "## FAQ\n\n"
            + "Be HONEST. Pick a winner for each use case. Use hedged pricing if uncertain."
        )

    elif template == "alternatives":
        return (
            base_rules
            + f"\n\nARTICLE: \"{title}\"\nKeyword: {keyword}\n\n"
            + f"List and review the best alternatives to {entity_a}.\n\n"
            + "REQUIRED SECTIONS:\n"
            + f"## The 7 Best Alternatives to {entity_a} in {year}\n"
            + f"(for each alternative: H3 with name, 2 paragraphs covering what it does, pros/cons, pricing, best for)\n"
            + "## Quick Comparison Table\n"
            + "(markdown table: Tool | Best For | Free Plan | Starting Price — use \"check website\" if unsure of price)\n"
            + f"## How to Choose the Right {entity_a} Alternative\n"
            + "## Bottom Line\n"
            + "## FAQ\n\n"
            + "Real use cases. No fluff. Hedge pricing you're unsure about."
        )

    elif template == "guides":
        b = entity_b or "this task"
        return (
            base_rules
            + f"\n\nARTICLE: \"{title}\"\nKeyword: {keyword}\n\n"
            + f"Write a practical, actionable guide on using {entity_a} for {b}.\n\n"
            + "REQUIRED SECTIONS:\n"
            + f"## Is {entity_a} the Right Tool for {b}?\n"
            + "## Getting Started: Setup in Under 10 Minutes\n"
            + "## The Core Workflow (Step by Step)\n"
            + "## Advanced Tips That Actually Make a Difference\n"
            + "## Common Mistakes and How to Avoid Them\n"
            + "## Real Results: What Teams Are Getting\n"
            + "## Bottom Line\n"
            + "## FAQ\n\n"
            + "Include specific prompts, settings, or workflows. Be concrete."
        )

    else:  # for-profession
        b = entity_b or "professionals"
        if entity_b and entity_b in ALL_TOOLS:
            return (
                base_rules
                + f"\n\nARTICLE: \"{title}\"\nKeyword: {keyword}\n\n"
                + f"Is {entity_a} actually useful for {b}? Give a real answer.\n\n"
                + "REQUIRED SECTIONS:\n"
                + f"## What {b} Actually Need From AI Tools\n"
                + f"## Where {entity_a} Fits Into a {b}'s Workflow\n"
                + f"## The Real Wins for {b} Using {entity_a}\n"
                + "## The Frustrations Nobody Talks About\n"
                + f"## Pricing: Is It Worth It for {b}?\n"
                + "## Verdict\n"
                + "## FAQ"
            )
        else:
            return (
                base_rules
                + f"\n\nARTICLE: \"{title}\"\nKeyword: {keyword}\n\n"
                + f"List and review the best AI tools for {entity_a}.\n\n"
                + "REQUIRED SECTIONS:\n"
                + f"## How AI Is Changing the Game for {entity_a}\n"
                + f"## The 10 Best AI Tools for {entity_a} in {year}\n"
                + f"(for each: H3 with tool name, 2 paragraphs: what it does, why great for {entity_a}, pricing — hedge if unsure)\n"
                + f"## Tools That Didn't Make the Cut (and Why)\n"
                + f"## How to Build Your AI Stack as a {entity_a}\n"
                + "## Bottom Line\n"
                + "## FAQ"
            )


def generate_page(candidate: dict) -> dict | None:
    template = candidate["template"]
    entity_a = candidate["entity_a"]
    entity_b = candidate.get("entity_b")
    keyword  = candidate["keyword"]
    category = candidate.get("category", "")

    title  = pick_title(template, entity_a, entity_b)
    print(f"  📝 Title: {title} ({len(title)} chars)")

    prompt = build_prompt(template, title, keyword, entity_a, entity_b, category)

    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_GENERATE,
            messages=[
                {"role": "system", "content": (
                    "You are a senior tech journalist and SEO expert. "
                    "Write authoritative, opinionated, deeply useful content. "
                    "Never write filler. Every sentence adds value. "
                    f"Current year is 2026. Minimum {MIN_WORD_COUNT} words required. "
                    "IMPORTANT: Never invent specific pricing numbers you are not confident about. "
                    "Use hedged language like 'around $X/month' or 'check their website'."
                )},
                {"role": "user", "content": prompt},
            ],
            temperature=0.75,
            max_tokens=4000,
        )
        raw = resp.choices[0].message.content.strip()
        raw = strip_code_fences(raw)
    except Exception as e:
        print(f"  ❌ GPT error: {e}")
        return None

    excerpt = ""
    if "EXCERPT:" in raw:
        parts   = raw.split("EXCERPT:")
        raw     = parts[0].strip()
        excerpt = normalize_excerpt(parts[1].strip())

    if not validate_content(raw, label=keyword[:40]):
        print(f"  ⚠️  Content too short — retrying once with higher token limit...")
        try:
            resp2 = openai_client.chat.completions.create(
                model=MODEL_GENERATE,
                messages=[
                    {"role": "system", "content": (
                        "You are a senior tech journalist. Write LONG, thorough, exhaustive content. "
                        f"Minimum {MIN_WORD_COUNT} words — absolutely required. Every section must be detailed."
                    )},
                    {"role": "user", "content": prompt + f"\n\nREMINDER: Write at least {MIN_WORD_COUNT} words. Do not stop early."},
                ],
                temperature=0.7,
                max_tokens=4500,
            )
            raw2 = strip_code_fences(resp2.choices[0].message.content.strip())
            if "EXCERPT:" in raw2:
                parts2  = raw2.split("EXCERPT:")
                raw2    = parts2[0].strip()
                excerpt = normalize_excerpt(parts2[1].strip())
            if validate_content(raw2, label=f"{keyword[:40]}-retry"):
                raw = raw2
            else:
                print(f"  ❌ Retry also failed — skipping this candidate")
                return None
        except Exception as e:
            print(f"  ❌ Retry GPT error: {e}")
            return None

    return {
        "title":    title,
        "content":  raw,
        "excerpt":  excerpt,
        "keyword":  keyword,
        "entity_a": entity_a,
        "entity_b": entity_b,
        "template": template,
        "category": category,
        "slug":     candidate["slug"],
    }


# ── SAVE TO SUPABASE ──────────────────────────────────────────────────────────

def save_page(page: dict, idx: int) -> bool:
    slug    = page["slug"]
    keyword = page["keyword"]

    if already_exists(slug):
        print(f"  ⏭️  Slug already exists — skipping: {slug}")
        return False
    if already_exists_hash(keyword):
        print(f"  ⏭️  Keyword hash already exists — skipping: {keyword}")
        return False

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rt      = reading_time(page["content"])

    data = {
        "title":          page["title"],
        "slug":           slug,
        "content":        page["content"],
        "excerpt":        page["excerpt"] or page["title"],
        "keyword":        keyword,
        "keyword_hash":   md5(keyword),
        "template":       page["template"],
        "entity_a":       page["entity_a"],
        "entity_b":       page.get("entity_b"),
        "category":       page.get("category", ""),
        "reading_time":   rt,
        "image_gradient": GRADIENTS[idx % len(GRADIENTS)],
        "published_at":   now_iso,
    }

    try:
        supabase_client.table("pseo_pages").insert(data).execute()
        print(f"  ✅ Saved: {page['title'][:70]}")
        # ── Ping IndexNow so Bing indexes immediately ──
        pseo_url = f"https://www.newstide.news/compare/{slug}"
        ping_indexnow([pseo_url])
        return True
    except Exception as e:
        print(f"  ❌ Error saving: {e}")
        return False


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="NewsTide pSEO Pipeline")
    parser.add_argument("--template", choices=list(TEMPLATE_GENERATORS.keys()), required=True)
    parser.add_argument("--batch",    type=int, default=10)
    args = parser.parse_args()

    print(f"\n🚀 pSEO Pipeline — {args.template} — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(f"🎯 Target: {args.batch} pages")

    print("\n📚 Loading existing pairs from Supabase...")
    existing_pairs = load_existing_pairs()
    print(f"   {len(existing_pairs)} existing pairs loaded")

    generator  = TEMPLATE_GENERATORS[args.template]
    candidates = generator(args.batch, existing_pairs)
    print(f"\n🔍 {len(candidates)} candidates generated for template '{args.template}'")

    saved_count = 0
    tried_count = 0

    for candidate in candidates:
        if saved_count >= args.batch:
            break

        tried_count += 1
        slug    = candidate["slug"]
        keyword = candidate["keyword"]

        print(f"\n[{saved_count+1}/{args.batch}] {keyword[:70]}")

        if already_exists(slug):
            print(f"  ⏭️  Already exists (slug) — skipping")
            continue
        if already_exists_hash(keyword):
            print(f"  ⏭️  Already exists (hash) — skipping")
            continue

        page = generate_page(candidate)
        if page is None:
            print(f"  ❌ Generation failed — skipping")
            continue

        ok = save_page(page, idx=saved_count)
        if ok:
            saved_count += 1
            if saved_count < args.batch:
                time.sleep(1)

    print(f"\n{'='*60}")
    print(f"🎉 pSEO Pipeline finished: {saved_count}/{args.batch} pages saved")
    print(f"   Candidates tried: {tried_count}")


if __name__ == "__main__":
    main()
