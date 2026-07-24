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
# Categories are intentionally tight — only tools that users actually compare.
# FIX: databases_backend split into two logical groups so we never get
#      "PlanetScale vs Netlify" (database vs hosting — nobody searches that).

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
    # ✅ SPLIT: databases vs hosting — never mix these two
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
# FIX: load all existing entity pairs from Supabase at startup.
# This prevents regenerating "Cursor vs Copilot" if it was done in a previous batch.

def load_existing_pairs() -> set:
    """
    Returns a set of frozensets like {frozenset({'cursor', 'github copilot'})}
    covering every comparison already in pseo_pages.
    Also returns all existing slugs and keyword_hashes for dedup.
    """
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
    """
    X vs Y — only pairs tools within the SAME category.
    Skips pairs already in Supabase (live dedup).
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
                pair_key  = tuple(sorted([a.lower(), b.lower()]))
                pair_frozen = frozenset([a.lower(), b.lower()])
                if pair_key in seen_pairs:
                    continue
                if pair_frozen in existing_pairs:
                    continue  # already generated in a previous run
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

    # FIX: explicit pricing honesty rules injected into every prompt.
    # GPT-4o must hedge unknown prices instead of fabricating exact numbers.
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
## {entity_a} — What It Actually Does Well
## {b} — What It Actually Does Well
## Head-to-Head: Features, Pricing, Speed
(include a markdown comparison table — only use prices you are confident about, otherwise write "check website")
## Who Should Choose {entity_a}
## Who Should Choose {b}
## Verdict: Which One Wins in {year}?
## FAQ

Be HONEST. Pick a winner for each use case. Use hedged pricing if uncertain."""

    elif template == "alternatives":
        return f"""{base_rules}

ARTICLE: "{title}"
Keyword: {keyword}

List and review the best alternatives to {entity_a}.

REQUIRED SECTIONS:
## The 7 Best Alternatives to {entity_a} in {year}
(for each alternative: H3 with name, 2 paragraphs covering what it does, pros/cons, pricing, best for)
## Quick Comparison Table
(markdown table: Tool | Best For | Free Plan | Starting Price — use "check website" if unsure of price)
## How to Choose the Right {entity_a} Alternative
## Bottom Line
## FAQ

Real use cases. No fluff. Hedge pricing you're unsure about."""

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
(for each: H3 with tool name, 2 paragraphs: what it does, why great for {entity_a}, pricing — hedge if unsure)
## Tools That Didn't Make the Cut (and Why)
## How to Build Your AI Stack as a {entity_a}
## Bottom Line
## FAQ"""


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
                    "Use hedged language like 'around $X/month' or 'check their website' instead."
                )},
                {"role": "user", "content": prompt},
            ],
            temperature=0.78,
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
        "slug":           slug,
        "template":       candidate["template"],
        "entity_a":       candidate["entity_a"],
        "entity_b":       candidate.get("entity_b"),
        "keyword":        generated["keyword"],
        "keyword_hash":   md5(generated["keyword"]),
        "title":          generated["title"],
        "content":        generated["content"],
        "excerpt":        generated["excerpt"],
        "reading_time":   reading_time(generated["content"]),
        "image_gradient": GRADIENTS[page_index % len(GRADIENTS)],
        "published_at":   published_at,
        "lang":           "en",
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

    # Load existing pairs ONCE at startup — avoids duplicate API calls per candidate
    print("\n🔍 Loading existing pages from Supabase for dedup...")
    existing_pairs = load_existing_pairs()
    print(f"   {len(existing_pairs)} existing entity pairs found — will skip these")

    generator  = TEMPLATE_GENERATORS[args.template]
    candidates = generator(args.batch, existing_pairs)
    print(f"\n📋 Candidate pool: {len(candidates)} items (already-done pairs excluded)")

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
