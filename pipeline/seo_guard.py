"""
Shared SEO guards: accent-safe keyword slugs + entity-level cannibalisation.

Why this module exists
----------------------
Both pipelines deduplicate candidate topics with whole-title trigram
similarity (``match_similar_articles`` / pg_trgm at 0.45) plus a GPT-4o-mini
judgement. On 2026-09-02 both layers passed this pair:

    "Airtable vs. Asana: A Complete Tool Comparison"         (published 09-02)
    "Airtable vs. Asana: Which Tool Is Better for Founders?" (published 08-22)

``similarity()`` between those two titles is 0.33 — below the threshold — even
though they target one identical query. Trigram similarity measures *wording*;
cannibalisation is caused by the *entity pair*. Eight "Airtable vs X" articles
went live in one month this way, and the finance vertical produced three
"enviar dinero a Mexico" pieces in two days.

So this module keys deduplication on the set of named products/brands in the
title instead of on its wording. It is a *pre-generation* check: it runs before
any Claude call, so a blocked candidate costs nothing.

The second half fixes ``_derive_keyword_slug``: it stripped accents as if they
were punctuation ("que" from "qué" became "qu", "comparacion" became
"comparacin") and filtered Spanish text through an English stopword list,
leaving a dangling "-de".

Pure functions only — no network, no Supabase, no env vars — so both pipelines
can import it and the unit tests can exercise it directly.
"""
import re
import unicodedata

# ── ENTITY VOCABULARY ────────────────────────────────────────────────────────
# Products/brands that actually appear in this site's two verticals. Kept as an
# explicit list rather than "any capitalised token" because article titles are
# Title Case, which would make every word look like a brand.
#
# Add new tools here as the niche expands — an unknown brand simply falls back
# to the existing trigram + cluster checks, it never breaks the run.
UNAMBIGUOUS_BRANDS = {
    # no-code / database / project management
    "airtable", "asana", "clickup", "trello", "basecamp", "smartsheet",
    "coda", "mondaycom",
    # automation
    "zapier", "n8n", "integromat", "workato", "trayio",
    "pipedream", "activepieces",
    # site builders / CMS / commerce / no-code
    "webflow", "squarespace", "wix", "framer", "carrd", "ghost",
    "wordpress", "shopify", "gumroad", "lemonsqueezy", "podia",
    "bubble", "adalo", "glide", "appgyver", "softr", "bildr",
    "teachable", "memberful", "kajabi", "manychat", "hostinger",
    # dev stack
    "supabase", "firebase", "vercel", "netlify", "railway", "render",
    "planetscale", "neon", "prisma", "nextjs", "sveltekit", "remix",
    "paddle", "cloudflare", "heroku", "digitalocean",
    # web frameworks and runtimes — added 2026-09-03 after "Flask vs. Django"
    # and "Vercel vs Cloudflare Pages" both published with no entity coverage
    # at all, because none of these names were in this list.
    "django", "flask", "fastapi", "express", "nodejs", "deno", "bun",
    "rails", "laravel", "svelte", "astro", "nuxt", "vue", "angular",
    "flutter", "reactnative", "ionic", "capacitor",
    # databases
    "mongodb", "mysql", "postgres", "postgresql", "redis", "dynamodb",
    "sqlite", "cockroachdb",
    # design / product / support
    "figma", "sketch", "canva", "framer", "elementor",
    "linear", "jira", "zendesk", "intercom", "twilio", "segment",
    "dialogflow", "rasa", "activecampaign", "paypal",
    # AI
    "openai", "chatgpt", "claude", "anthropic", "gemini", "perplexity",
    "midjourney", "cursor", "copilot", "mistral", "llama", "jasper",
    "copyai", "writesonic", "surfer", "clearscope",
    # analytics / marketing
    "mailchimp", "convertkit", "beehiiv", "substack", "hubspot",
    "posthog", "plausible", "fathom", "mixpanel", "amplitude",
    "ahrefs", "semrush", "screamingfrog",
    # finance / fintech (finance vertical)
    "remitly", "westernunion", "moneygram", "xoom", "pangea",
    "revolut", "n26", "brigit", "nubank", "intermex",
    "robinhood", "fidelity", "vanguard", "schwab", "etrade",
    "capitalone", "amex", "bankofamerica", "wellsfargo", "chase",
    "creditkarma", "experian", "equifax", "transunion", "novacredit",
    "turbotax", "hrblock", "taxact", "freetaxusa",
    "googlesheets", "googledocs", "googledrive", "excel",
}

# Brands whose name is also an ordinary word. Counted as an entity only when
# the title is clearly comparative or another unambiguous brand sits beside it
# — otherwise "make time for deep work" would register the automation tool.
AMBIGUOUS_BRANDS = {
    "make", "wise", "chime", "mint", "wave", "square", "stripe", "notion",
    "current", "discover", "ally", "dave", "marcus", "sofi", "varo",
    "monday", "moz", "ria",
}

ALL_BRANDS = UNAMBIGUOUS_BRANDS | AMBIGUOUS_BRANDS

# Multi-word brands need matching before tokenisation splits them apart.
MULTIWORD_BRANDS = {
    "google sheets": "googlesheets",
    "google docs": "googledocs",
    "google drive": "googledrive",
    "microsoft excel": "excel",
    "ms excel": "excel",
    "bank of america": "bankofamerica",
    "wells fargo": "wellsfargo",
    "chase bank": "chase",
    "capital one": "capitalone",
    "american express": "amex",
    "nova credit": "novacredit",
    "credit karma": "creditkarma",
    "western union": "westernunion",
    "money gram": "moneygram",
    "h&r block": "hrblock",
    "monday.com": "mondaycom",
    "next.js": "nextjs",
    "tray.io": "trayio",
    "copy.ai": "copyai",
    "lemon squeezy": "lemonsqueezy",
}

_COMPARISON_MARKERS = re.compile(
    r"\b(vs\.?|versus|compar\w*|alternativ\w*|better|mejor(?:es)?|frente a)\b",
    re.IGNORECASE,
)


# ── TEXT NORMALISATION ───────────────────────────────────────────────────────
def strip_accents(text: str) -> str:
    """Fold accents to their base letter: 'comparacion' from 'comparación'.

    The bug this replaces ran a punctuation strip directly on accented text,
    which deleted the accented letter itself instead of replacing it with its
    base form, so 'comparación' came out as 'comparacin'.
    """
    decomposed = unicodedata.normalize("NFD", text or "")
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


# Bilingual stopword list. The previous English-only set left Spanish function
# words in place, producing slugs like
# 'airtable-asana-comparativa-completa-de' with a dangling preposition.
STOPWORDS = {
    # English
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "can", "could",
    "should", "may", "might", "shall", "how", "what", "why", "when", "where",
    "which", "who", "your", "our", "vs", "its", "it", "you", "we",
    "this", "that", "these", "those", "into", "about", "than", "then",
    # Spanish
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "y", "o", "u", "e", "en", "con", "sin", "por", "para", "como", "que",
    "cual", "cuales", "cuando", "donde", "quien", "quienes", "es", "son",
    "era", "eran", "ser", "estar", "esta", "este", "estos", "estas", "ese",
    "esa", "esos", "esas", "su", "sus", "tu", "tus", "mi", "mis", "lo",
    "se", "no", "si", "mas", "pero", "porque", "sobre", "entre", "hasta",
    "desde", "muy", "ya", "tambien", "todo", "toda", "todos", "todas",
}


def derive_keyword_slug(title: str, max_tokens: int = 5) -> str:
    """Search-intent slug from an article title: accent-safe and bilingual.

    Replaces the broken derivation used by run_content_guardrails() CHECK C.
    Accents are folded to their base letter *before* punctuation is stripped,
    and trailing function words are trimmed so the slug never ends on a
    dangling preposition.
    """
    folded = strip_accents(title or "").lower()
    folded = re.sub(r"[^a-z0-9\s]", " ", folded)
    tokens = [w for w in folded.split() if len(w) > 1 and w not in STOPWORDS]
    if not tokens:
        # Everything was a stopword — fall back to the raw folded words so the
        # caller still gets a non-empty slug rather than an empty string.
        tokens = [w for w in folded.split() if len(w) > 1]
    selected = tokens[:max_tokens]
    while selected and selected[-1] in STOPWORDS:
        selected.pop()
    if len(selected) < 3 and len(tokens) >= 3:
        selected = tokens[:3]
    return "-".join(selected)


# ── ENTITY EXTRACTION ────────────────────────────────────────────────────────
def extract_entities(title: str) -> frozenset:
    """Named products/brands mentioned in a title, normalised.

    'n8n vs Zapier vs Make: solo automation compared' -> {n8n, zapier, make}
    'Why Your Social Media Strategy Fails'            -> empty set
    """
    if not title:
        return frozenset()

    folded = strip_accents(title).lower()
    found: set[str] = set()

    # Multi-word brands first, removing them so their parts are not re-matched.
    for phrase, canonical in MULTIWORD_BRANDS.items():
        if phrase in folded:
            found.add(canonical)
            folded = folded.replace(phrase, " ")

    # Keep dots and digits: 'n8n', 'next.js', 'monday.com' are single tokens.
    tokens = [t.rstrip(".") for t in re.findall(r"[a-z0-9][a-z0-9.]*", folded)]

    unambiguous = {t for t in tokens if t in UNAMBIGUOUS_BRANDS}
    found |= unambiguous

    # An ambiguous name counts only in a context that makes it a product:
    # a comparison title, or another real brand already present.
    if _COMPARISON_MARKERS.search(title) or found:
        found |= {t for t in tokens if t in AMBIGUOUS_BRANDS}

    return frozenset(found)


def entity_collision(candidate: str, existing_titles, min_overlap: int = 2) -> str | None:
    """Return the first existing title that would cannibalise ``candidate``.

    Collision rules, in plain terms:
      * the candidate names at least two products, AND
      * an existing article names at least ``min_overlap`` of those same ones.

    A single shared product is deliberately NOT a collision — "Notion for
    invoicing" and "Notion vs Coda" are legitimately different pages. Single
    entity saturation is handled by the cluster-cooldown check instead.
    """
    cand = extract_entities(candidate)
    if len(cand) < min_overlap:
        return None
    for title in existing_titles:
        if not title:
            continue
        if len(cand & extract_entities(title)) >= min_overlap:
            return title
    return None


def entity_signature(title: str) -> str:
    """Stable key for an entity set — 'airtable|asana'. Empty when no brands."""
    return "|".join(sorted(extract_entities(title)))
