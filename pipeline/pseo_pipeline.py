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
                pair_key  = tuple(sorted([a.lower(), b.lower()]))
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
    base_rules = f"""You are a senior tech journalist writing for NewsTide, a premium English-language tech media.
Audience: founders, developers, indie hackers. Smart, busy, skeptical of hype.
Tone: direct, opinionated, slightly informal — like a smart friend who tested this stuff.
Year: {year}. Never reference years before {year} unless historically essential.

{pricing_rules}

STRUCTURE (markdown):
- NO H1 — title is handled separately
- Introduction (no H2 header): lead with real tension or key insight. No "In today's digital world" openers.
- Minimum {MIN_H2_SECTIONS} H2 sections, each 120+ words
- H3 subsections where helpful
- Concrete examples, real pricing (hedged if uncertain), personal takes
- End with "## Verdict" or "## Bottom Line" with a clear recommendation
- "## FAQ" at the end with 3 questions in H3 format (for FAQPage schema)

MINIMUM {MIN_WORD_COUNT} WORDS — short content will be rejected automatically.

SEO:
- Use keyword "{keyword}" naturally in first 100 words and 2-3× total
- Related terms naturally woven in, no stuffing

At the very end, single line:
EXCERPT: [one punchy sentence, {EXCERPT_MIN}-{EXCERPT_MAX} chars, suitable as Google meta description]
"""

    if template == "comparisons":
        b = entity_b or "competitor"
        category_hint = f"\nNote: both tools are in the '{category}' category — make sure the comparison is relevant and makes sense for users choosing between them." if category else ""
        return f"""{base_rules}

ARTICLE: "{title}"
Keyword: {keyword}
{category_hint}

Write a genuine, opinionated comparison of {entity_a} vs {b}.

REQUIRED SECTIONS (use exactly these H2 titles):
## {entity_a} — What It A