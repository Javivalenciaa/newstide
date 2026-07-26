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
- GPT-4.1 for generation (instruction-following + cost-efficient)

Upgrades v2:
- CTR Title Agent: psychological CTR expert generates titles dynamically (no fixed patterns)
- Advanced Humanizer Agent: breaks perplexity, burstiness, n-gram and discourse marker
  AI fingerprints based on 2026 detection research

Usage (via GitHub Actions workflow_dispatch):
  python pipeline/pseo_pipeline.py --template comparisons --batch 10 --spread-days 3
  python pipeline/pseo_pipeline.py --template alternatives --batch 10 --spread-days 7
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

MODEL_GENERATE  = "gpt-4.1"
MODEL_TITLES    = "gpt-4.1"        # CTR Title Agent
MODEL_HUMANIZE  = "gpt-4o"         # Advanced Humanizer Agent (best at style transfer)

MIN_WORD_COUNT   = 900
MIN_H2_SECTIONS  = 4
TITLE_MAX        = 62
TITLE_MIN        = 48
EXCERPT_MAX      = 155
EXCERPT_MIN      = 120

# ── AI DETECTION: FORBIDDEN PATTERNS ─────────────────────────────────────────
# These are the exact linguistic fingerprints that GPTZero, Originality.ai,
# and Copyleaks flag in 2026 (low perplexity tokens + overused discourse markers)
FORBIDDEN_OPENERS = [
    "in the ever-evolving",
    "in today's",
    "in the fast-paced",
    "navigating the",
    "as ai continues",
    "as technology continues",
    "in the rapidly",
    "in the world of",
    "in the landscape of",
    "the world of",
    "it's no secret",
    "let's dive",
    "let's delve",
    "look no further",
    "whether you're a",
]

# High-frequency AI discourse markers that raise burstiness detection scores
AI_CLICHE_MARKERS = [
    "it's worth noting",
    "it is worth noting",
    "it's important to note",
    "it is important to note",
    "needless to say",
    "at the end of the day",
    "in conclusion",
    "to summarize",
    "in summary",
    "in a nutshell",
    "this comprehensive guide",
    "dive deep into",
    "delve into",
    "game-changer",
    "game changer",
    "cutting-edge",
    "groundbreaking",
    "revolutionize",
    "transformative",
    "seamlessly",
    "robust solution",
    "leverage",           # AI loves this word
    "utilize",            # AI loves this word
    "furthermore",        # classic AI discourse marker
    "moreover",           # classic AI discourse marker
    "in addition to",
    "it is crucial",
    "it is essential",
    "plays a crucial role",
    "plays an important role",
    "a wide range of",
    "a variety of",
]

openai_client   = OpenAI(api_key=OPENAI_API_KEY)
supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ── INDEXNOW ──────────────────────────────────────────────────────────────────
INDEXNOW_KEY      = "964bf589528b466cace60749e05cfcb6"
INDEXNOW_HOST     = "www.newstide.news"
INDEXNOW_KEY_LOC  = f"https://{INDEXNOW_HOST}/{INDEXNOW_KEY}.txt"

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
                pair_key    = tuple(sorted([a.lower(), b.lower()]))
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
    return max(1, round(len(text.split()) / 200))

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

def validate_opener(content: str, label: str = "") -> bool:
    first_200 = content[:200].lower()
    for phrase in FORBIDDEN_OPENERS:
        if first_200.startswith(phrase) or first_200.startswith("\n" + phrase):
            print(f"  ❌ [{label}] Cliché opener detected: '{phrase[:40]}...'")
            return False
    return True

def count_ai_markers(content: str) -> int:
    lower = content.lower()
    return sum(1 for marker in AI_CLICHE_MARKERS if marker in lower)

def spread_published_at(idx: int, total: int, spread_days: int) -> str:
    now = datetime.now(timezone.utc)
    if spread_days <= 1 or total <= 1:
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")
    total_seconds = spread_days * 24 * 3600
    step_seconds  = total_seconds / max(total - 1, 1)
    offset        = timedelta(seconds=idx * step_seconds)
    return (now + offset).strftime("%Y-%m-%dT%H:%M:%SZ")

# ── SLUG/HASH DEDUPLICATION ───────────────────────────────────────────────────

def already_exists(slug: str) -> bool:
    res = supabase_client.table("pseo_pages").select("id").eq("slug", slug).execute()
    return len(res.data) > 0

def already_exists_hash(keyword: str) -> bool:
    res = supabase_client.table("pseo_pages").select("id").eq("keyword_hash", md5(keyword)).execute()
    return len(res.data) > 0

# ── CTR TITLE AGENT ───────────────────────────────────────────────────────────
# Generates psychologically optimized titles dynamically.
# Based on 2026 research on click psychology: curiosity gaps, loss aversion,
# social proof, specificity, and pattern interruption.

CTR_AGENT_SYSTEM = """You are a world-class headline copywriter and CTR optimization expert.
You have studied 10 million Google Search clicks and know exactly what makes people click.

YOUR EXPERTISE:
- Curiosity gap: reveal just enough to create unbearable curiosity
- Loss aversion: people click to avoid missing out or making expensive mistakes
- Specificity: concrete numbers and names beat vague promises every time
- Pattern interruption: break expected formats to stand out in SERP
- Emotional contrast: tension, surprise, the "wait, what?" moment
- Social proof with stakes: "5 YC startups switched", "saves $800/month"

PSYCHOLOGICAL LEVERS YOU USE:
1. The Reveal: "The real reason X beats Y" — implies hidden truth
2. The Warning: "Why most people get X wrong" — fear of being wrong
3. The Insider: "What nobody tells you about X" — exclusive knowledge
4. The Data Shock: "X costs 3x more than Y — here's the math" — numbers create authority
5. The Verdict After Testing: "I used both for 30 days — here's what happened"
6. The Counterintuitive: "X is worse than Y — unless you're a developer"
7. The Stakes Raiser: "The wrong choice here costs startups $2k/month"

STRICT RULES:
- Title MUST be between 48 and 62 characters (count carefully)
- NEVER use: "game-changer", "revolutionize", "comprehensive", "ultimate guide"
- NEVER start with "How to" unless it's for guides template and has a number or twist
- No clickbait that can't be delivered in the article
- Make every word earn its place — cut mercilessly
- The title should make someone stop scrolling and think "I need to read this NOW"

Output ONLY the title text. No quotes, no explanation."""

def generate_ctr_title(template: str, entity_a: str, entity_b: str | None, keyword: str) -> str:
    """CTR Title Agent: generates a psychologically optimized title using GPT."""

    b = entity_b or ""

    template_context = {
        "comparisons": f"""You're writing a comparison article: {entity_a} vs {b}
Audience: developers, indie hackers, startup founders who need to choose between these two tools.
They've probably already Googled this — your title needs to beat every other result.

Generate ONE killer title that:
- Makes them feel they'll FINALLY get a clear answer
- Implies you've done the work they haven't
- Uses tension, a number, or a surprising angle
- Is between 48-62 characters

Examples of the energy you want (adapt, don't copy):
- "Cursor vs Copilot: I Tested Both for 6 Months. Here's the Truth"  [too long, adapt]
- "n8n vs Zapier: The Real Cost Difference Nobody Calculates"
- "Supabase vs Firebase: Which Saves More Money at Scale?"
- "Claude vs ChatGPT: The Benchmark That Surprised 3 YC Teams"
""",
        "alternatives": f"""You're writing an alternatives article for: {entity_a}
Audience: developers or founders frustrated with {entity_a} who are actively looking to switch.
They're in "research mode" — your title needs to promise relief and a clear answer.

Generate ONE title that:
- Validates their frustration with {entity_a}
- Promises specific, tested alternatives
- Uses a number (7, 5, 9) or a surprising qualifier
- Is between 48-62 characters

Examples of the energy (adapt, don't copy):
- "7 {entity_a} Alternatives That Don't Break After Free Tier"
- "Tired of {entity_a}? These 5 Switch in Under an Hour"
- "The {entity_a} Alternatives 4 Founders Actually Switched To"
""",
        "guides": f"""You're writing a guide: how to use {entity_a} for {b}
Audience: busy developers or founders who want real results fast, not theory.
They've seen a hundred "how to" guides — yours needs to promise something different.

Generate ONE title that:
- Implies a shortcut, a real result, or a specific outcome
- Has a number or a time frame if it fits naturally
- Is concrete about what they'll achieve
- Is between 48-62 characters

Examples of the energy (adapt, don't copy):
- "{entity_a} for {b}: The 20-Minute Setup That Actually Works"
- "How to Use {entity_a} for {b} (and Cut Your Time in Half)"
- "{entity_a} + {b}: The Workflow 500 Developers Are Using"
""",
        "for-profession": f"""You're writing a tools roundup for: {entity_a} (profession/audience)
Target reader: a {entity_a} who wants to use AI to work better, faster, or earn more.
They see "best tools" lists every day — your title needs a sharper angle.

Generate ONE title that:
- Speaks directly to a {entity_a}'s specific pain or goal
- Is opinionated and specific (not generic "best tools")
- Uses a number or a qualifying phrase that creates contrast
- Is between 48-62 characters

Examples of the energy (adapt, don't copy):
- "AI Tools for {entity_a}: The 6 That Are Worth Paying For"
- "How {entity_a} Use AI to Ship 3x Faster in 2026"
- "The AI Stack Every {entity_a} Needs — and 4 to Skip"
""",
    }

    context = template_context.get(template, f"Write a killer title for: {keyword}")

    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_TITLES,
            messages=[
                {"role": "system", "content": CTR_AGENT_SYSTEM},
                {"role": "user",   "content": context},
            ],
            temperature=0.9,
            max_tokens=80,
        )
        raw_title = resp.choices[0].message.content.strip().strip('"').strip("'")
        # Enforce hard character limit
        title = smart_trim(raw_title, TITLE_MAX)
        # Enforce minimum length — pad with year context if too short
        if len(title) < TITLE_MIN:
            title = smart_trim(f"{title} — 2026", TITLE_MAX)
        print(f"  🎯 CTR Title Agent: \"{title}\" ({len(title)} chars)")
        return title
    except Exception as e:
        print(f"  ⚠️  CTR Title Agent error: {e} — using keyword as fallback")
        return smart_trim(keyword.title(), TITLE_MAX)


# ── ADVANCED HUMANIZER AGENT ──────────────────────────────────────────────────
# Breaks the 4 main AI detection signals identified in 2026 research:
# 1. Low perplexity — predictable word choices
# 2. Low burstiness — uniform sentence lengths
# 3. AI discourse markers — "furthermore", "moreover", "it's worth noting"
# 4. N-gram fingerprints — repeated syntactic patterns from LLM training data

HUMANIZER_SYSTEM = """You are an expert editor who has studied exactly how AI text detectors work in 2026.

HOW AI DETECTORS CATCH AI TEXT (what you must break):

1. LOW PERPLEXITY: AI picks the most predictable word every time.
   FIX: Swap expected words for surprising-but-correct alternatives.
   "The tool is very useful" → "The tool earns its keep."
   "This can help you save time" → "This buys you back hours."
   "It is important to" → "You'll want to" or just delete it.

2. UNIFORM BURSTINESS (coefficient of variation < 0.30 = AI detected):
   AI writes sentences of similar length (15-20 words each).
   FIX: Violently vary sentence length. Mix 3-word punches with complex compound sentences.
   "Short. Then a much longer one that builds, adds context, and lands somewhere unexpected."
   Target: vary between 4-word sentences and 35-word sentences within the same paragraph.

3. DISCOURSE MARKERS — AI fingerprints (replace ALL of these):
   "furthermore" → "and here's the thing" / "what's more" / cut entirely
   "moreover" → "on top of that" / "also" / restructure
   "it's worth noting" → "something people miss:" / cut
   "it is important to note" → just say the thing directly
   "in conclusion" → "bottom line:" / "so where does that leave you?"
   "to summarize" → don't summarize, end with a punch
   "leverage" → "use" / "tap into" / "pull from"
   "utilize" → "use" (always)
   "seamlessly" → delete or replace with specific behavior
   "robust" → "solid" / "battle-tested" / be specific
   "cutting-edge" → name the actual feature
   "game-changer" → explain WHY it changes things specifically

4. N-GRAM REPETITION (LLM syntactic fingerprints):
   AI repeats sentence structures: "X is Y. X does Z. X can help with..."
   FIX: Vary how you introduce each point. Mix:
   - Questions: "What does this mean for your workflow?"
   - Fragments: "Not ideal. Especially if you're on a tight budget."
   - Parentheticals: "The API (which runs on gpt-4.1 under the hood) handles this automatically."
   - Direct address: "If you're a solo founder, this matters more than you think."
   - Em dashes for interruption: "The free tier — 500 requests/month — covers most indie projects."

5. PARAGRAPH LENGTH UNIFORMITY:
   AI writes uniform paragraph sizes (3-4 sentences each).
   FIX: Mix single-sentence paragraphs with dense multi-sentence ones.
   One-liner paragraphs create visual rhythm and feel human.

WHAT NOT TO DO:
- Don't change facts, data, tool names, or the article's conclusions
- Don't add fake personal anecdotes you can't verify
- Don't make the article sound casual if the original is authoritative
- Don't remove markdown headers — keep all ## and ### structure

OUTPUT: Return ONLY the rewritten article. No explanations, no preamble."""

def humanize_content(content: str, label: str = "") -> str:
    """Advanced Humanizer Agent: breaks AI detection patterns."""
    print(f"  🧬 Humanizer Agent running on [{label}]...")

    marker_count = count_ai_markers(content)
    if marker_count > 0:
        print(f"     Found {marker_count} AI markers to eliminate")

    try:
        resp = openai_client.chat.completions.create(
            model=MODEL_HUMANIZE,
            messages=[
                {"role": "system", "content": HUMANIZER_SYSTEM},
                {"role": "user",   "content": content},
            ],
            temperature=0.85,
            max_tokens=5500,
        )
        humanized = resp.choices[0].message.content.strip()
        humanized = strip_code_fences(humanized)

        # Verify markers were reduced
        new_marker_count = count_ai_markers(humanized)
        reduction = marker_count - new_marker_count
        print(f"     AI markers: {marker_count} → {new_marker_count} (eliminated {reduction})")

        return humanized
    except Exception as e:
        print(f"  ⚠️  Humanizer error: {e} — returning original")
        return content


# ── SYSTEM PROMPT ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a senior tech journalist writing for NewsTide, a premium English-language tech publication.
Audience: developers, indie hackers, solo founders. Smart, busy, skeptical of hype.
Year: 2026. Everything you write must reflect the current AI/dev tool landscape as of 2026.

TONE
- Direct, opinionated, slightly informal. Like a smart friend who actually used the tools.
- No filler. Every sentence must add real value.
- Use contractions (it's, you're, don't). Write like a human, not a press release.

OPENER RULES — CRITICAL, STRICTLY ENFORCED:
Your first sentence MUST NOT start with any of these patterns (instant rejection):
- "In the ever-evolving..."
- "In today's..."
- "In the fast-paced..."
- "Navigating the..."
- "As AI continues..."
- "As technology continues..."
- "Whether you're a..."
- "It's no secret that..."
- "Let's dive..."
- "Let's delve..."
- "Look no further..."
Instead, start with: a sharp observation, a real tension, a number/stat, or a direct verdict.
Example good openers:
- "Jasper costs $49/month. That's the first thing most teams question when they evaluate it."
- "Three things keep developers from committing to Cursor: price, privacy, and offline support."
- "Picking the wrong deployment platform at seed stage can cost you 40 hours of migration work later."

TOOL ACCURACY — CRITICAL:
- Only mention tools that are actively maintained and well-known in 2026.
- DO NOT include: Bard AI (renamed Gemini), Peppertype.ai (defunct), DeepArt, Artbreeder, CodeStream (acquired/inactive), or any tool you are not confident is active.
- For AI code editors, the main players are: Cursor, Windsurf, GitHub Copilot, Codeium, Tabnine, Bolt, Lovable, Replit AI. Use these, not generic IDEs.
- For LLMs: ChatGPT, Claude, Gemini, Perplexity, Mistral, Grok, Llama, Command R+. Never list deprecated models.

PRICING RULES — CRITICAL:
- Only state prices you are highly confident are accurate as of 2026.
- If uncertain: write "pricing starts around $X/month" or "check their website for current pricing".
- Never invent exact prices for tools you're unsure about.
- Never write a price table with made-up numbers.
- Always mention free tiers where they exist (e.g., Cursor has a free tier, GitHub Copilot is ~$10/month).

STRUCTURE:
- NO H1 — the title is injected separately
- Introduction paragraph (no H2): start with the sharp opener, establish the real tension or insight
- Minimum 4 H2 sections, each 120+ words
- H3 subsections where helpful
- End with ## Verdict or ## Bottom Line with a clear, opinionated recommendation
- ## FAQ at the very end, exactly 3 questions in H3 format

MINIMUM 900 WORDS — non-negotiable.

SEO:
- Use the target keyword naturally in the first 100 words and 2-3 times total
- Weave in related terms naturally, no stuffing

FINAL LINE (required):
EXCERPT: [one punchy, specific sentence, 120-155 chars, suitable as Google meta description. No generic phrases.]
""".strip()

# ── CONTENT GENERATION ────────────────────────────────────────────────────────

def build_prompt(template: str, title: str, keyword: str, entity_a: str, entity_b: str | None, category: str = "") -> str:
    year = "2026"

    if template == "comparisons":
        b = entity_b or "competitor"
        category_hint = (
            f"Note: both tools are in the '{category}' category — "
            "ensure the comparison is specific to that use case context."
        ) if category else ""
        return (
            f"Write the article: \"{title}\"\n"
            f"Target keyword: {keyword}\n"
            f"{category_hint}\n\n"
            f"Compare {entity_a} vs {b} honestly and specifically. No generic comparisons.\n\n"
            "REQUIRED H2 SECTIONS (use exactly these):\n"
            f"## {entity_a} — What It Actually Does Well\n"
            f"## {b} — What It Actually Does Well\n"
            "## Head-to-Head: Features, Pricing, Speed\n"
            "   Include a markdown table. Only use pricing you are confident about; otherwise 'check website'.\n"
            f"## Who Should Pick {entity_a}\n"
            f"## Who Should Pick {b}\n"
            f"## Verdict: The Winner for {year}\n"
            "## FAQ (3 H3 questions specific to this comparison)\n\n"
            "Requirements:\n"
            "- Pick a clear winner for each use case. Don't sit on the fence.\n"
            "- Mention specific features, limits, or quirks from personal testing perspective.\n"
            f"- Minimum 900 words."
        )

    elif template == "alternatives":
        return (
            f"Write the article: \"{title}\"\n"
            f"Target keyword: {keyword}\n\n"
            f"List and honestly review the best alternatives to {entity_a} as of {year}.\n"
            f"Only include tools that are actively maintained and directly compete with {entity_a}.\n\n"
            "REQUIRED H2 SECTIONS:\n"
            f"## Why Teams Are Moving Away From {entity_a}\n"
            f"   (real reasons: pricing, missing features, UX friction — be specific)\n"
            f"## The Best {entity_a} Alternatives in {year}\n"
            f"   For each alternative (7 total), write an H3 with the tool name, then cover:\n"
            "   - What it does better than {entity_a}\n"
            "   - Real limitations\n"
            "   - Pricing (hedged if uncertain)\n"
            "   - Who it's best for\n"
            "## Quick Comparison Table\n"
            "   Columns: Tool | Best For | Free Plan | Starting Price\n"
            f"## How to Choose the Right {entity_a} Alternative\n"
            "## Bottom Line\n"
            "## FAQ (3 H3 questions)\n\n"
            "Requirements:\n"
            "- DO NOT pad with defunct or barely-relevant tools to reach 7. Only real, active, direct competitors.\n"
            "- Start the article with a sharp observation about why someone would leave {entity_a}.\n"
            f"- Minimum 900 words."
        )

    elif template == "guides":
        b = entity_b or "this task"
        return (
            f"Write the article: \"{title}\"\n"
            f"Target keyword: {keyword}\n\n"
            f"Write a practical, step-by-step guide on using {entity_a} for {b}.\n\n"
            "REQUIRED H2 SECTIONS:\n"
            f"## Is {entity_a} Actually the Right Tool for {b}?\n"
            "   (honest assessment — when it works, when it doesn't)\n"
            "## Setup: Get Running in Under 10 Minutes\n"
            "   (real steps, specific settings, not generic instructions)\n"
            "## The Core Workflow (Step by Step)\n"
            "   (include specific prompts, configurations, or examples)\n"
            "## Advanced Techniques That Actually Move the Needle\n"
            "## The Mistakes Everyone Makes (and How to Avoid Them)\n"
            "## Bottom Line\n"
            "## FAQ (3 H3 questions)\n\n"
            "Requirements:\n"
            "- Be concrete. Include actual example prompts or workflow steps.\n"
            "- Mention real limitations of using {entity_a} for {b}.\n"
            f"- Minimum 900 words."
        )

    else:  # for-profession
        b = entity_b or "professionals"
        if entity_b and entity_b in ALL_TOOLS:
            return (
                f"Write the article: \"{title}\"\n"
                f"Target keyword: {keyword}\n\n"
                f"Is {entity_a} actually worth it for {b}? Give a real, opinionated answer.\n\n"
                "REQUIRED H2 SECTIONS:\n"
                f"## What {b} Actually Need From an AI Tool\n"
                f"## Where {entity_a} Fits Into a {b}'s Workflow\n"
                f"## The Real Wins: What {b} Use It For Daily\n"
                "   (specific use cases with concrete examples)\n"
                "## The Honest Drawbacks for This Use Case\n"
                f"## Pricing Reality for {b}\n"
                "## Verdict\n"
                "## FAQ (3 H3 questions)\n\n"
                f"- Minimum 900 words."
            )
        else:
            return (
                f"Write the article: \"{title}\"\n"
                f"Target keyword: {keyword}\n\n"
                f"List and review the best AI tools for {entity_a} as of {year}.\n"
                "Only include tools that are actively maintained and specifically useful for this audience.\n\n"
                "REQUIRED H2 SECTIONS:\n"
                f"## How AI Is Actually Changing Work for {entity_a}\n"
                "   (concrete examples, not generic hype)\n"
                f"## The Best AI Tools for {entity_a} in {year}\n"
                f"   For each tool (8-10 total), write an H3 with the name, then:\n"
                f"   - What it does specifically for {entity_a}\n"
                "   - Real-world use case\n"
                "   - Pricing (hedged if uncertain)\n"
                "## Tools That Didn't Make the Cut (and Why)\n"
                f"## How to Build Your AI Stack as a {entity_a}\n"
                "## Bottom Line\n"
                "## FAQ (3 H3 questions)\n\n"
                f"- Minimum 900 words."
            )


def generate_page(candidate: dict) -> dict | None:
    template = candidate["template"]
    entity_a = candidate["entity_a"]
    entity_b = candidate.get("entity_b")
    keyword  = candidate["keyword"]
    category = candidate.get("category", "")

    # ── Step 1: CTR Title Agent ───────────────────────────────────────────────
    title = generate_ctr_title(template, entity_a, entity_b, keyword)

    print(f"  📝 Generating content for: {title}")

    prompt = build_prompt(template, title, keyword, entity_a, entity_b, category)

    def call_model(max_tokens: int, temperature: float) -> str | None:
        try:
            resp = openai_client.chat.completions.create(
                model=MODEL_GENERATE,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return strip_code_fences(resp.choices[0].message.content.strip())
        except Exception as e:
            print(f"  ❌ GPT error: {e}")
            return None

    # ── Step 2: Generate raw content ─────────────────────────────────────────
    raw = call_model(max_tokens=4500, temperature=0.7)
    if raw is None:
        return None

    excerpt = ""
    if "EXCERPT:" in raw:
        parts   = raw.split("EXCERPT:")
        raw     = parts[0].strip()
        excerpt = normalize_excerpt(parts[1].strip())

    # Validate: word count + H2 count
    if not validate_content(raw, label=keyword[:40]):
        print(f"  ⚠️  Content too short — retrying with more tokens...")
        raw2 = call_model(max_tokens=5000, temperature=0.65)
        if raw2 is None:
            return None
        if "EXCERPT:" in raw2:
            parts2  = raw2.split("EXCERPT:")
            raw2    = parts2[0].strip()
            excerpt = normalize_excerpt(parts2[1].strip())
        if not validate_content(raw2, label=f"{keyword[:40]}-retry"):
            print(f"  ❌ Retry also failed — skipping")
            return None
        raw = raw2

    # Validate: opener quality
    if not validate_opener(raw, label=keyword[:40]):
        print(f"  ⚠️  Cliché opener — retrying once...")
        raw3 = call_model(max_tokens=4500, temperature=0.8)
        if raw3 is None:
            return None
        if "EXCERPT:" in raw3:
            parts3  = raw3.split("EXCERPT:")
            raw3    = parts3[0].strip()
            excerpt = normalize_excerpt(parts3[1].strip())
        if not validate_opener(raw3, label=f"{keyword[:40]}-opener-retry"):
            print(f"  ⚠️  Still cliché after retry — accepting anyway (check manually)")
        else:
            raw = raw3

    # ── Step 3: Advanced Humanizer Agent ─────────────────────────────────────
    humanized = humanize_content(raw, label=keyword[:40])

    # Validate content wasn't broken by humanizer
    if not validate_content(humanized, label=f"{keyword[:40]}-humanized"):
        print(f"  ⚠️  Humanizer broke content length — using pre-humanize version")
        humanized = raw

    return {
        "title":    title,
        "content":  humanized,
        "excerpt":  excerpt,
        "keyword":  keyword,
        "entity_a": entity_a,
        "entity_b": entity_b,
        "template": template,
        "category": category,
        "slug":     candidate["slug"],
    }


# ── SAVE TO SUPABASE ──────────────────────────────────────────────────────────

def save_page(page: dict, idx: int, spread_days: int = 1, total: int = 1) -> bool:
    slug    = page["slug"]
    keyword = page["keyword"]

    if already_exists(slug):
        print(f"  ⏭️  Slug already exists — skipping: {slug}")
        return False
    if already_exists_hash(keyword):
        print(f"  ⏭️  Keyword hash already exists — skipping: {keyword}")
        return False

    published_at = spread_published_at(idx, total, spread_days)
    rt           = reading_time(page["content"])

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
        "reading_time":   rt,
        "image_gradient": GRADIENTS[idx % len(GRADIENTS)],
        "published_at":   published_at,
    }

    try:
        supabase_client.table("pseo_pages").insert(data).execute()
        print(f"  ✅ Saved [{published_at[:10]}]: {page['title'][:70]}")
        pseo_url = f"https://www.newstide.news/compare/{slug}"
        ping_indexnow([pseo_url])
        return True
    except Exception as e:
        print(f"  ❌ Error saving: {e}")
        return False


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="NewsTide pSEO Pipeline")
    parser.add_argument(
        "--template",
        choices=list(TEMPLATE_GENERATORS.keys()),
        required=True,
        help="pSEO template to run",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=10,
        help="Number of pages to generate",
    )
    parser.add_argument(
        "--spread-days",
        type=int,
        default=1,
        dest="spread_days",
        help="Spread publication timestamps over N days (anti-spam SEO signal)",
    )
    args = parser.parse_args()

    print(f"\n🚀 pSEO Pipeline v2 — {args.template} — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(f"🎯 Target: {args.batch} pages | Spread: {args.spread_days} day(s)")
    print(f"🤖 Models: Generate={MODEL_GENERATE} | Titles={MODEL_TITLES} | Humanize={MODEL_HUMANIZE}")

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

        print(f"\n[{saved_count + 1}/{args.batch}] {keyword[:70]}")

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

        ok = save_page(page, idx=saved_count, spread_days=args.spread_days, total=args.batch)
        if ok:
            saved_count += 1
            if saved_count < args.batch:
                time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"🎉 pSEO Pipeline v2 finished: {saved_count}/{args.batch} pages saved")
    print(f"   Candidates tried: {tried_count}")


if __name__ == "__main__":
    main()
