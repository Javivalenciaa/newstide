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
from datetime import datetime, timezone, timedelta
from openai import OpenAI
from supabase import create_client

# ── CONFIG ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY       = os.environ["OPENAI_API_KEY"]
SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

MODEL_GENERATE  = "gpt-4o"
MODEL_FAST      = "gpt-4o-mini"

# Lowered from 900 → 800: GPT-4o reliably produces 820-870 words per article.
# 800 words is still substantial, well above thin-content threshold for Google.
MIN_WORD_COUNT   = 800
MIN_H2_SECTIONS  = 4
TITLE_MAX        = 62
TITLE_MIN        = 48
EXCERPT_MAX      = 155
EXCERPT_MIN      = 120

openai_client   = OpenAI(api_key=OPENAI_API_KEY)
supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

GRADIENTS = [
    "linear-gradient(135deg,#0d2a2e,#0d1a2e)",
    "linear-gradient(135deg,#1a0d2e,#2e0d1a)",
    "linear-gradient(135deg,#2e1a0d,#1a2e0d)",
    "linear-gradient(135deg,#0d2e1a,#0d2e2a)",
    "linear-gradient(135deg,#2e0d0d,#1a0d2e)",
    "linear-gradient(135deg,#0d1a2e,#2e2a0d)",
]

# ── KEYWORD UNIVERSE ──────────────────────────────────────────────────────────
# Tools grouped by CATEGORY so comparisons are always meaningful.
# "Suno vs Qdrant" is useless. "Suno vs Udio" is a real search query.

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
        "Jasper", "Copy.ai", "Writesonic", "Rytr", "Notion AI",
        "Grammarly", "Sudowrite", "Anyword",
    ],
    "databases_backend": [
        "Supabase", "PlanetScale", "Neon", "Railway", "Render",
        "Vercel", "Netlify", "Fly.io",
    ],
    "image_generation": [
        "Midjourney", "DALL-E 3", "Stable Diffusion", "Ideogram", "Flux",
        "Adobe Firefly", "Leonardo AI", "Playground AI",
    ],
    "ai_video_audio": [
        "ElevenLabs", "Suno", "Udio", "HeyGen", "Synthesia",
        "Descript", "CapCut AI", "Runway", "Pika", "Luma AI",
    ],
    "project_management": [
        "Linear", "Height", "Jira", "Asana", "ClickUp",
        "Notion", "Monday.com", "Basecamp",
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

# Flat list for alternatives / guides / for-profession (categories don't matter there)
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

# ── TEMPLATE ENGINES ──────────────────────────────────────────────────────────

def generate_comparison_candidates(n: int) -> list[dict]:
    """
    X vs Y — only pairs tools within the SAME category.
    This ensures comparisons are semantically valid and searchable.
    """
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
                pair = tuple(sorted([a.lower(), b.lower()]))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                slug = f"{slugify(a)}-vs-{slugify(b)}"
                candidates.append({
                    "template":  "comparisons",
                    "slug":      slug,
                    "keyword":   f"{a} vs {b}",
                    "entity_a":  a,
                    "entity_b":  b,
                    "category":  category,
                })

    random.shuffle(candidates)
    return candidates[:n * 4]  # return 4× pool so we have headroom for skips


def generate_alternatives_candidates(n: int) -> list[dict]:
    """Best alternatives to X — captures users who want to switch"""
    tools = ALL_TOOLS.copy()
    random.shuffle(tools)
    candidates = []
    for tool in tools:
        candidates.append({
            "template": "alternatives",
            "slug":     f"best-alternatives-to-{slugify(tool)}",
            "keyword":  f"best alternatives to {tool}",
            "entity_a": tool,
            "entity_b": None,
        })
    return candidates[:n * 3]


def generate_guides_candidates(n: int) -> list[dict]:
    """How to use X for Y — tutorial/guide intent with high long-tail volume"""
    combos = [(tool, use) for tool in ALL_TOOLS for use in USE_CASES]
    random.shuffle(combos)
    candidates = []
    for tool, use_case in combos[:n * 4]:
        candidates.append({
            "template": "guides",
            "slug":     f"how-to-use-{slugify(tool)}-for-{slugify(use_case)}",
            "keyword":  f"how to use {tool} for {use_case}",
            "entity_a": tool,
            "entity_b": use_case,
        })
    return candidates[:n * 3]


def generate_for_profession_candidates(n: int) -> list[dict]:
    """Best AI tools for [profession] — high commercial intent, easy to rank"""
    candidates = []
    for profession in PROFESSIONS:
        candidates.append({
            "template": "for-profession",
            "slug":     f"best-ai-tools-for-{slugify(profession)}",
            "keyword":  f"best AI tools for {profession}",
            "entity_a": profession,
            "entity_b": None,
        })
    for tool in random.sample(ALL_TOOLS, min(25, len(ALL_TOOLS))):
        for profession in random.sample(PROFESSIONS, 3):
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

# ── DEDUPLICATION ─────────────────────────────────────────────────────────────

def already_exists(slug: str) -> bool:
    res = supabase_client.table("pseo_pages").select("id").eq("slug", slug).execute()
    return len(res.data) > 0

def already_exists_hash(keyword: str) -> bool:
    res = supabase_client.table("pseo_pages").select("id").eq("keyword_hash", md5(keyword)).execute()
    return len(res.data) > 0

# ── TITLE PATTERNS ────────────────────────────────────────────────────────────
# CTR-optimised for low-authority domains: numbers, year, parenthetical proof,
# tension/contrast, audience specificity.

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

def build_prompt(template: str, title: str, keyword: str, entity_a: str, entity_b: str | None) -> str:
    year = "2026"

    base_rules = f"""You are a senior tech journalist writing for NewsTide, a premium English-language tech media.
Audience: founders, developers, indie hackers. Smart, busy, skeptical of hype.
Tone: direct, opinionated, slightly informal — like a smart friend who tested this stuff.
Year: {year}. Never reference years before {year} unless historically essential.

STRUCTURE (markdown):
- NO H1 — title is handled separately
- Introduction (no H2 header): lead with real tension or key insight. No "In today's digital world" openers.
- Minimum {MIN_H2_SECTIONS} H2 sections, each 120+ words
- H3 subsections where helpful
- Concrete examples, real pricing, personal takes
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
        return f"""{base_rules}

ARTICLE: "{title}"
Keyword: {keyword}

Write a genuine, opinionated comparison of {entity_a} vs {b}.

REQUIRED SECTIONS (use exactly these H2 titles):
## {entity_a} — What It Actually Does Well
## {b} — What It Actually Does Well
## Head-to-Head: Features, Pricing, Speed
(include a markdown comparison table here)
## Who Should Choose {entity_a}
## Who Should Choose {b}
## Verdict: Which One Wins in {year}?
## FAQ

Be HONEST. Pick a winner for each use case. Include real {year} pricing."""

    elif template == "alternatives":
        return f"""{base_rules}

ARTICLE: "{title}"
Keyword: {keyword}

List and review the best alternatives to {entity_a}.

REQUIRED SECTIONS:
## The 7 Best Alternatives to {entity_a} in {year}
(for each alternative: H3 with name, 2 paragraphs covering what it does, pros/cons, pricing, best for)
## Quick Comparison Table
(markdown table: Tool | Best For | Free Plan | Starting Price)
## How to Choose the Right {entity_a} Alternative
## Bottom Line
## FAQ

Real pricing. Real use cases. No fluff."""

    elif template == "guides":
        b = entity_b or "this task"
        return f"""{base_rules}

ARTICLE: "{title}"
Keyword: {keyword}

Write a practical, actionable guide on using {entity_a} for {b}.

REQUIRED SECTIONS:
## Is {entity_a} the Right Tool for {b}?
## Getting Started: Setup in Under 10 Minutes
## The Core Workflow (Step by Step)
## Advanced Tips That Actually Make a Difference
## Common Mistakes and How to Avoid Them
## Real Results: What Teams Are Getting
## Bottom Line
## FAQ

Include specific prompts, settings, or workflows. Be concrete."""

    else:  # for-profession
        b = entity_b or "professionals"
        if entity_b and entity_b in ALL_TOOLS:
            return f"""{base_rules}

ARTICLE: "{title}"
Keyword: {keyword}

Is {entity_a} actually useful for {b}? Give a real answer.

REQUIRED SECTIONS:
## What {b} Actually Need From AI Tools
## Where {entity_a} Fits Into a {b}'s Workflow
## The Real Wins for {b} Using {entity_a}
## The Frustrations Nobody Talks About
## Pricing: Is It Worth It for {b}?
## Verdict
## FAQ"""
        else:
            return f"""{base_rules}

ARTICLE: "{title}"
Keyword: {keyword}

List and review the best AI tools for {entity_a}.

REQUIRED SECTIONS:
## How AI Is Changing the Game for {entity_a}
## The 10 Best AI Tools for {entity_a} in {year}
(for each: H3 with tool name, 2 paragraphs: what it does, why great for {entity_a}, pricing)
## Tools That Didn't Make the Cut (and Why)
## How to Build Your AI Stack as a {entity_a}
## Bottom Line
## FAQ"""


def generate_page(candidate: dict) -> dict | None:
    template = candidate["template"]
    entity_a = candidate["entity_a"]
    entity_b = candidate.get("entity_b")
    keyword  = candidate["keyword"]

    title  = pick_title(template, entity_a, entity_b)
    print(f"  📝 Title: {title} ({len(title)} chars)")

    prompt = build_prompt(template, title, keyword, entity_a, entity_b)

    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_GENERATE,
            messages=[
                {"role": "system", "content": (
                    "You are a senior tech journalist and SEO expert. "
                    "Write authoritative, opinionated, deeply useful content. "
                    "Never write filler. Every sentence adds value. "
                    f"Current year is 2026. Minimum {MIN_WORD_COUNT} words required."
                )},
                {"role": "user", "content": prompt},
            ],
            temperature=0.80,
            max_tokens=3800,
        )
        raw = resp.choices[0].message.content.strip()
        raw = strip_code_fences(raw)
    except Exception as e:
        print(f"  ❌ GPT-4o error: {e}")
        return None

    excerpt = ""
    if "EXCERPT:" in raw:
        parts   = raw.split("EXCERPT:")
        raw     = parts[0].strip()
        excerpt = normalize_excerpt(parts[1].strip())

    if not validate_content(raw, label="generated"):
        print("  ❌ Content failed validation — skipping")
        return None

    return {
        "title":   title,
        "content": raw,
        "excerpt": excerpt or smart_trim(title + " — Full guide for 2026 on NewsTide.", EXCERPT_MAX),
        "keyword": keyword,
    }


# ── SAVE ──────────────────────────────────────────────────────────────────────

def save_page(candidate: dict, generated: dict, page_index: int, spread_days: int) -> bool:
    offset_hours = int((page_index / max(1, spread_days)) * spread_days * 24)
    published_at = (datetime.now(timezone.utc) + timedelta(hours=offset_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

    slug = candidate["slug"]
    if already_exists(slug):
        slug = f"{slug}-{md5(candidate['keyword'])[:6]}"

    data = {
        "slug":          slug,
        "template":      candidate["template"],
        "entity_a":      candidate["entity_a"],
        "entity_b":      candidate.get("entity_b"),
        "keyword":       generated["keyword"],
        "keyword_hash":  md5(generated["keyword"]),
        "title":         generated["title"],
        "content":       generated["content"],
        "excerpt":       generated["excerpt"],
        "reading_time":  reading_time(generated["content"]),
        "image_gradient": GRADIENTS[page_index % len(GRADIENTS)],
        "published_at":  published_at,
        "lang":          "en",
    }

    try:
        supabase_client.table("pseo_pages").insert(data).execute()
        print(f"  ✅ Saved: {generated['title'][:70]} (publish: {published_at[:10]})")
        return True
    except Exception as e:
        print(f"  ❌ Supabase error: {e}")
        return False


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="NewsTide pSEO Pipeline")
    parser.add_argument("--template", required=True,
                        choices=["comparisons", "alternatives", "guides", "for-profession"])
    parser.add_argument("--batch",       type=int, default=10)
    parser.add_argument("--spread-days", type=int, default=7)
    args = parser.parse_args()

    print(f"\n🚀 NewsTide pSEO Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Template : {args.template}")
    print(f"   Batch    : {args.batch} pages")
    print(f"   Spread   : over {args.spread_days} days")
    print("=" * 60)

    generator  = TEMPLATE_GENERATORS[args.template]
    candidates = generator(args.batch)
    print(f"\n📋 Candidate pool: {len(candidates)} items")

    published = []
    pool_idx  = 0

    while len(published) < args.batch and pool_idx < len(candidates):
        candidate = candidates[pool_idx]
        pool_idx += 1

        slug    = candidate["slug"]
        keyword = candidate["keyword"]

        print(f"\n[{len(published)+1}/{args.batch}] {keyword[:70]}")

        if already_exists(slug) or already_exists_hash(keyword):
            print("  ⏭️  Already exists — skipping")
            continue

        generated = generate_page(candidate)
        if not generated:
            continue

        saved = save_page(candidate, generated, len(published), args.spread_days)
        if saved:
            published.append(generated["title"])
            print(f"  ✅ [{len(published)}/{args.batch}] Done")
            time.sleep(1.5)

    print(f"\n{'='*60}")
    print(f"🎉 pSEO Pipeline finished: {len(published)} pages generated")
    for i, t in enumerate(published, 1):
        print(f"   {i}. {t[:80]}")


if __name__ == "__main__":
    main()
