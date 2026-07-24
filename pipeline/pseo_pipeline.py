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
- GPT-4o for generation + humanisation (cheap + fast)
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

MODEL_GENERATE  = "gpt-4o"          # quality generation
MODEL_FAST       = "gpt-4o-mini"    # dedup, checks

MIN_WORD_COUNT   = 900
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
# Strategy: tools with HIGH brand search volume but LOW "vs/alternatives" competition
# Ideal for new domains: long-tail, specific, navigational intent

AI_TOOLS = [
    "ChatGPT", "Claude", "Gemini", "Perplexity", "Mistral",
    "Cursor", "GitHub Copilot", "Windsurf", "Bolt", "Lovable",
    "n8n", "Make", "Zapier", "Notion AI", "Obsidian",
    "Supabase", "PlanetScale", "Neon", "Railway", "Render",
    "Vercel", "Netlify", "Fly.io", "Modal", "Replicate",
    "Midjourney", "DALL-E 3", "Stable Diffusion", "Ideogram", "Flux",
    "ElevenLabs", "Suno", "Udio", "HeyGen", "Synthesia",
    "Descript", "CapCut AI", "Runway", "Pika", "Luma AI",
    "Grammarly", "Jasper", "Copy.ai", "Writesonic", "Rytr",
    "Linear", "Height", "Jira", "Asana", "ClickUp",
    "Figma AI", "Framer", "Webflow", "Wix AI", "Squarespace AI",
    "Airtable", "Coda", "Notion", "Confluence", "ClickUp Docs",
    "Langchain", "LlamaIndex", "Haystack", "CrewAI", "AutoGen",
    "Pinecone", "Weaviate", "Chroma", "Qdrant", "Milvus",
]

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
    """X vs Y — highest CTR template for new domains (navigational + commercial intent)"""
    candidates = []
    tools = AI_TOOLS.copy()
    random.shuffle(tools)
    seen_pairs = set()
    for i in range(len(tools)):
        for j in range(i + 1, len(tools)):
            if len(candidates) >= n * 3:
                break
            a, b = tools[i], tools[j]
            pair = tuple(sorted([a.lower(), b.lower()]))
            if pair in seen_pairs:
                continue
            # Only compare tools in the same category (more relevant)
            seen_pairs.add(pair)
            slug = f"{slugify(a)}-vs-{slugify(b)}"
            candidates.append({
                "template": "comparisons",
                "slug": slug,
                "keyword": f"{a} vs {b}",
                "title_hint": f"{a} vs {b}: Which One Is Actually Worth It in 2026?",
                "entity_a": a,
                "entity_b": b,
            })
    random.shuffle(candidates)
    return candidates[:n * 3]


def generate_alternatives_candidates(n: int) -> list[dict]:
    """Best alternatives to X — captures users who want to switch"""
    candidates = []
    tools = AI_TOOLS.copy()
    random.shuffle(tools)
    for tool in tools:
        slug = f"best-alternatives-to-{slugify(tool)}"
        candidates.append({
            "template": "alternatives",
            "slug": slug,
            "keyword": f"best alternatives to {tool}",
            "title_hint": f"7 Best Alternatives to {tool} in 2026 (Ranked by Real Users)",
            "entity_a": tool,
            "entity_b": None,
        })
    return candidates[:n * 3]


def generate_guides_candidates(n: int) -> list[dict]:
    """How to use X for Y — tutorial/guide intent with high long-tail volume"""
    candidates = []
    combos = []
    for tool in AI_TOOLS:
        for use_case in USE_CASES:
            combos.append((tool, use_case))
    random.shuffle(combos)
    for tool, use_case in combos[:n * 4]:
        slug = f"how-to-use-{slugify(tool)}-for-{slugify(use_case)}"
        candidates.append({
            "template": "guides",
            "slug": slug,
            "keyword": f"how to use {tool} for {use_case}",
            "title_hint": f"How to Use {tool} for {use_case.title()} in 2026 (Step-by-Step)",
            "entity_a": tool,
            "entity_b": use_case,
        })
    return candidates[:n * 3]


def generate_for_profession_candidates(n: int) -> list[dict]:
    """Best AI tools for [profession] — high commercial intent, easy to rank"""
    candidates = []
    for profession in PROFESSIONS:
        slug = f"best-ai-tools-for-{slugify(profession)}"
        candidates.append({
            "template": "for-profession",
            "slug": slug,
            "keyword": f"best AI tools for {profession}",
            "title_hint": f"10 Best AI Tools for {profession.title()} in 2026 (That Actually Work)",
            "entity_a": profession,
            "entity_b": None,
        })
    # Also create tool × profession combinations
    for tool in random.sample(AI_TOOLS, min(20, len(AI_TOOLS))):
        for profession in random.sample(PROFESSIONS, 3):
            slug = f"{slugify(tool)}-for-{slugify(profession)}"
            candidates.append({
                "template": "for-profession",
                "slug": slug,
                "keyword": f"{tool} for {profession}",
                "title_hint": f"{tool} for {profession.title()}: Is It Worth It in 2026?",
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
    words   = len(content.split())
    h2s     = len(re.findall(r'^## ', content, re.MULTILINE))
    ok = True
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

# ── TITLE OPTIMISATION ────────────────────────────────────────────────────────
# Research-backed CTR patterns for low-authority domains in 2026:
# 1. Numbers + specificity: "7 Best", "10 Alternatives"
# 2. Year: "in 2026" (freshness signal + less competition than evergreen)
# 3. Parenthetical proof: "(Tested by Founders)", "(Honest Review)"
# 4. Contrast/tension: "vs", "Actually Worth It", "Nobody Talks About"
# 5. Audience specificity: "for Developers", "for Solo Founders"

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
        "I Tried 9 {a} Alternatives — Here Are the 4 Worth Paying For",
        "Best {a} Alternatives in 2026: Ranked by Real Teams",
        "Tired of {a}? These 6 Alternatives Are Better for Founders",
    ],
    "guides": [
        "How to Use {a} for {b} in 2026 (Full Walkthrough)",
        "{a} for {b}: The Step-by-Step Guide Nobody Wrote Yet",
        "Using {a} for {b}: What Actually Works in 2026",
        "The Right Way to Use {a} for {b} (With Real Examples)",
        "{a} + {b}: The Workflow That's Saving Teams 10 Hours a Week",
    ],
    "for-profession": [
        "Best AI Tools for {a} in 2026 (I Use 3 of These Daily)",
        "10 AI Tools Every {a} Should Know About in 2026",
        "How {a} Are Using AI to 10x Their Output in 2026",
        "The AI Stack for {a}: What's Actually Worth Paying For",
        "AI for {a}: The Tools That Replaced Half My Workflow",
    ],
}

def pick_title(template: str, entity_a: str, entity_b: str | None) -> str:
    patterns = CTR_TITLE_PATTERNS.get(template, ["{a} — NewsTide Guide 2026"])
    pattern  = random.choice(patterns)
    title = pattern.replace("{a}", entity_a).replace("{b}", entity_b or "")
    title = smart_trim(title, TITLE_MAX)
    # Ensure minimum length — append year if too short
    if len(title) < TITLE_MIN:
        title = smart_trim(f"{title} — 2026 Guide", TITLE_MAX)
    return title

# ── CONTENT GENERATION ────────────────────────────────────────────────────────

def build_prompt(template: str, title: str, keyword: str, entity_a: str, entity_b: str | None) -> str:
    year = "2026"

    base_rules = f"""
You are a senior tech journalist writing for NewsTide, a premium English-language tech media.
Audience: founders, developers, indie hackers. They are smart, busy, skeptical of hype.
Tone: direct, opinionated, slightly informal — like a smart friend who has tested this stuff.
Year: {year}. Never reference years before {year} unless historically essential.

STRUCTURE (markdown):
- NO H1 — the title is handled separately
- Introduction paragraph: lead with the real tension or the key insight. No "In today's digital world" BS.
- Minimum {MIN_H2_SECTIONS} H2 sections, each substantive (150+ words)
- H3 subsections where helpful
- Concrete examples, real pricing data where applicable, personal takes
- End with a "Bottom Line" or "Verdict" H2 with a clear recommendation
- FAQ section at the end with 3-4 questions in H3 format (used for FAQPage schema)

MINIMUM {MIN_WORD_COUNT} WORDS. Short = rejected. Go deep.

SEO:
- Naturally use keyword "{keyword}" in first 100 words and 2-3 times total
- Use related terms naturally (don't keyword-stuff)
- Write for humans first, Google second

At the very end, on its own line:
EXCERPT: [one sentence, {EXCERPT_MIN}-{EXCERPT_MAX} chars, irresistibly clickable, suitable as meta description]
"""

    if template == "comparisons":
        b = entity_b or "competitor"
        return f"""{base_rules}

ARTICLE TOPIC: "{title}"
Keyword: {keyword}

Write a genuine comparison of {entity_a} vs {b}.

REQUIRED SECTIONS:
1. Why this comparison matters right now (intro — no H2)
2. ## {entity_a} — What It's Actually Good At
3. ## {b} — What It's Actually Good At
4. ## Head-to-Head: Features, Pricing, Speed (use a markdown table)
5. ## Who Should Use {entity_a}
6. ## Who Should Use {b}
7. ## Verdict: Which One Wins in 2026?
8. ## FAQ

Be HONEST. If one is clearly better for a use case, say so. Don't be neutral to the point of useless.
Include realistic pricing as of {year}."""

    elif template == "alternatives":
        return f"""{base_rules}

ARTICLE TOPIC: "{title}"
Keyword: {keyword}

List and review the best alternatives to {entity_a}.

REQUIRED SECTIONS:
1. Why people look for {entity_a} alternatives (intro — no H2)
2. ## The 7 Best Alternatives to {entity_a} in 2026
   (for each: H3 with name, 2-3 paragraphs: what it does, pros/cons, pricing, best for)
3. ## Quick Comparison Table (markdown table: Tool | Best For | Free Plan | Starting Price)
4. ## How to Choose the Right Alternative
5. ## Bottom Line
6. ## FAQ

Be specific. Real pricing. Real use cases. Don't just list tool names."""

    elif template == "guides":
        b = entity_b or "this use case"
        return f"""{base_rules}

ARTICLE TOPIC: "{title}"
Keyword: {keyword}

Write a practical guide on how to use {entity_a} for {b}.

REQUIRED SECTIONS:
1. Why {entity_a} is (or isn't) a good fit for {b} (intro — no H2)
2. ## Getting Started: Setting Up {entity_a} for {b}
3. ## The Core Workflow (step by step)
4. ## Advanced Tips and Tricks
5. ## Common Mistakes to Avoid
6. ## Real Results: What Teams Are Actually Getting
7. ## Bottom Line
8. ## FAQ

Include specific prompts, workflows, or settings where applicable. Make it actionable."""

    else:  # for-profession
        b = entity_b or "professionals"
        if entity_b and entity_b in AI_TOOLS:
            # tool for profession
            return f"""{base_rules}

ARTICLE TOPIC: "{title}"
Keyword: {keyword}

Explore why (or why not) {entity_a} is worth it for {b}.

REQUIRED SECTIONS:
1. The real question: does {entity_a} actually help {b}? (intro — no H2)
2. ## What {b} Actually Need From AI Tools
3. ## How {entity_a} Fits Into a {b}'s Workflow
4. ## The Biggest Wins for {b} Using {entity_a}
5. ## Limitations and Frustrations
6. ## Pricing: Is It Worth It for {b}?
7. ## Verdict
8. ## FAQ"""
        else:
            # best AI tools for profession
            return f"""{base_rules}

ARTICLE TOPIC: "{title}"
Keyword: {keyword}

List and review the best AI tools for {entity_a}.

REQUIRED SECTIONS:
1. How AI is changing the game for {entity_a} (intro — no H2)
2. ## The 10 Best AI Tools for {entity_a} in 2026
   (for each: H3 with tool name, 2 paragraphs: what it does, why it's great for {entity_a}, pricing)
3. ## Tools That Didn't Make the Cut (and Why)
4. ## How to Build Your AI Stack as a {entity_a}
5. ## Bottom Line
6. ## FAQ"""


def generate_page(candidate: dict) -> dict | None:
    template  = candidate["template"]
    entity_a  = candidate["entity_a"]
    entity_b  = candidate.get("entity_b")
    keyword   = candidate["keyword"]

    title = pick_title(template, entity_a, entity_b)
    print(f"  📝 Title: {title} ({len(title)} chars)")

    prompt = build_prompt(template, title, keyword, entity_a, entity_b)

    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_GENERATE,
            messages=[
                {"role": "system", "content": (
                    "You are a senior tech journalist and SEO expert. "
                    "Write authoritative, opinionated, deeply useful content. "
                    "Never write filler. Every sentence must add value. "
                    "Current year is 2026."
                )},
                {"role": "user", "content": prompt},
            ],
            temperature=0.82,
            max_tokens=3500,
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
        "title":    title,
        "content":  raw,
        "excerpt":  excerpt or smart_trim(title + " — Full guide for 2026 on NewsTide.", EXCERPT_MAX),
        "keyword":  keyword,
    }


# ── SAVE ──────────────────────────────────────────────────────────────────────

def save_page(candidate: dict, generated: dict, page_index: int, spread_days: int) -> bool:
    """
    Saves to pseo_pages table.
    published_at is spread across the next `spread_days` days to avoid
    publishing 10 pages at the same timestamp (looks spammy to Google).
    """
    # Spread publication dates: e.g. 10 pages over 7 days = ~1.4/day
    offset_hours = int((page_index / max(1, spread_days)) * spread_days * 24)
    published_at = (datetime.now(timezone.utc) + timedelta(hours=offset_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

    slug = candidate["slug"]
    # Ensure slug uniqueness by appending hash fragment if needed
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
                        choices=["comparisons", "alternatives", "guides", "for-profession"],
                        help="Which pSEO template to generate")
    parser.add_argument("--batch", type=int, default=10,
                        help="Number of pages to generate (default: 10)")
    parser.add_argument("--spread-days", type=int, default=7,
                        help="Spread publication over N days (default: 7)")
    args = parser.parse_args()

    print(f"\n🚀 NewsTide pSEO Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Template : {args.template}")
    print(f"   Batch    : {args.batch} pages")
    print(f"   Spread   : over {args.spread_days} days")
    print("=" * 60)

    # Generate candidate pool
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
            time.sleep(1.5)  # rate limit courtesy

    print(f"\n{'='*60}")
    print(f"🎉 pSEO Pipeline finished: {len(published)} pages generated")
    for i, t in enumerate(published, 1):
        print(f"   {i}. {t[:80]}")


if __name__ == "__main__":
    main()
