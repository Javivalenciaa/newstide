import http.client
import json
import os
import re
import time
from typing import Any

# Filename kept as dataforseo.py to avoid touching the two import lines in
# pipeline.py/finance_pipeline.py and every test file — but as of 2026-08-31
# this module no longer calls DataForSEO. DataForSEO's free trial ran out and
# its $50 minimum deposit wasn't worth it; YepAPI (yepapi.com) returns the
# same shape of data (volume + difficulty) with no minimum deposit, ES+EN
# support, and $0.15/call for up to 100 keywords.
YEPAPI_API_KEY = os.environ.get("YEPAPI_API_KEY", "")

# ── TARGETING STRATEGY (tuned for a young, low-authority site) ───────────────
# The original values (MIN_VOLUME=100, MAX_DIFFICULTY=70) encoded the opposite
# strategy: "prefer high volume, tolerate very hard keywords". On a site with
# a few hundred articles and little link authority those are exactly the terms
# it cannot rank for, so the pipeline kept picking unwinnable topics.
#
# A young site wins the long tail first: low difficulty, modest volume, then
# builds authority upward. Hence a much lower volume floor (real long-tail
# queries sit well under 100/mo) and a much stricter difficulty ceiling.
MIN_VOLUME = 10
MAX_DIFFICULTY = 40
_BATCH_SIZE = 100  # YepAPI's own max keywords per call


def opportunity_score(volume: int, difficulty: int) -> float:
    """Achievable traffic, not raw traffic.

    Volume you cannot rank for is worth nothing, so volume is discounted by
    how close the keyword sits to the difficulty ceiling: full credit at
    difficulty 0, zero credit at MAX_DIFFICULTY and above.

    The previous formula (volume / (difficulty + 1)) still ranked a
    volume-5000/difficulty-70 term above a volume-200/difficulty-5 term —
    backwards for a site that can realistically only win the second one.
    """
    if difficulty >= MAX_DIFFICULTY:
        return 0.0
    winnability = (MAX_DIFFICULTY - difficulty) / MAX_DIFFICULTY
    return round(volume * winnability, 2)


def is_usable_gsc_query(query: str) -> bool:
    """Reject GSC rows that are not real article topics.

    A GSC query is proven demand, but "demand" is not the same as "a topic
    worth writing about". Three kinds of junk reach this list, and pinning
    them to the front of the pool (see pin_priority_first) turned each one
    into a full published article:

      * Stock-photo credits. The pipelines print the Unsplash photographer
        into the article body, so the site ranks for the photographer's
        name. On 2026-08-31 "marija zaric unsplash" was pinned first and
        produced an article about stock-photography income — in a personal
        finance blog for Hispanics in the USA.
      * Navigational single-token brand strings ("novacreditltda",
        "growtika", "robot"). Someone typing one brand token wants that
        brand's own site; no article outranks it, and the topic is usually
        off-niche anyway.
      * SEO-tool operator strings, which are scrapers rather than people:
        '"how to build a landing page" -site:reddit.com -site:twitter.com'.
    """
    q = (query or "").strip().lower()

    if len(q) < 10:
        return False

    # Search operators => a tool, not a person.
    if any(token in q for token in ('-site:', 'site:', ' -"', '+"', ' or ', ' and ')):
        return False
    if q.count('"') >= 2:
        return False

    # Stock-photo credits leaking out of the article body.
    if any(host in q for host in ("unsplash", "pexels", "shutterstock", "getty", "istock")):
        return False

    # Navigational: a single token is a brand lookup, not an article topic.
    if len(q.split()) < 2:
        return False

    # Absurdly long strings are pasted prompts or scraper payloads.
    if len(q.split()) > 12:
        return False

    return True


def filter_gsc_queries(queries: list[str]) -> list[str]:
    """Apply is_usable_gsc_query() to a GSC result list and report what was cut."""
    kept = [q for q in queries if is_usable_gsc_query(q)]
    dropped = len(queries) - len(kept)
    if dropped:
        print(f"  🧹 GSC: {dropped} junk query/queries filtered out (brand lookups, photo credits, tool operators)")
    return kept


def pin_priority_first(pool: list[str], priority_keys: set[str]) -> list[str]:
    """Move proven-demand candidates to the front, preserving relative order.

    Applied LAST in both pipelines — after sort_pool_by_score() and after
    cluster_aware_reorder() — because each of those re-sorts the whole pool
    and would otherwise bury these again.

    GSC queries are the only candidates backed by impressions this site has
    actually earned: Google already shows these pages for these terms. Moving
    from position 15 to position 5 on a query you already rank for is far
    cheaper traffic than ranking a brand-new article from nothing. Before
    this, such a query with volume below MIN_VOLUME fell into `unscored` and
    sank to the bottom of the pool, where a 3-articles-per-run cap meant it
    was never actually used.
    """
    if not priority_keys:
        return pool

    priority: list[str] = []
    rest: list[str] = []
    for candidate in pool:
        if candidate.lower().strip()[:60] in priority_keys:
            priority.append(candidate)
        else:
            rest.append(candidate)

    if priority:
        print(f"  ⭐ {len(priority)} proven-demand (GSC) candidate(s) pinned to the front")
    return priority + rest

# ── STOPWORDS FOR KEYWORD EXTRACTION ─────────────────────────────────────────
# NOTE: "vs"/"vs." is deliberately NOT here. This niche runs constant "X vs Y"
# comparison titles, and people search "trello vs clickup", not "trello
# clickup" — stripping it produced a 5-word phrase with the one word that
# signals a comparison query removed, which no one actually searches for.
_KEYWORD_STOP = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","can","could","should","may",
    "might","shall","how","what","why","when","where","which","who","your",
    "our","this","that","these","those","it","its","as","on",
    "into","through","during","before","after","above","below","between",
    "under","again","further","then","once","here","there","all","each",
    "few","more","most","other","some","such","no","nor","not","only",
    "own","same","so","than","too","very","just","also","now","about",
    # Spanish stopwords — extract_core_keyword() is also used by
    # finance_pipeline.py for Spanish titles. Without these, a title like
    # "Los beneficios de la planificación patrimonial para hispanos" produced
    # a core keyword of mostly filler words ("los-beneficios-de-la-...")
    # instead of the actual search-intent terms.
    "el","la","los","las","de","del","al","en","con","por","para","que",
    "como","cómo","un","una","unos","unas","es","son","ser","estar","tu",
    "tus","su","sus","este","esta","estos","estas","eso","esa","sin",
    "sobre","entre","hasta","desde","muy","más","mas","menos","tan","tanto",
    "cada","otro","otra","todo","toda","todos","todas","hacia","según",
    "segun","porque","pero","aunque","ni","también","tambien","o","y",
}

def extract_core_keyword(title: str) -> str:
    """Extract a short, search-intent keyword from a long title.

    Keyword-volume APIs (YepAPI included) have real volume data mostly for
    short head/mid-tail phrases. Long titles (8-11 words) like "How to Build
    a Web App with Django in 7 Steps" return 0 results, and even a 5-word
    extracted core ("build simple ecommerce site shopify") usually still
    does — real DataForSEO runs on 2026-08-31 got data back for 38/38
    keywords but 0 cleared the volume threshold at 5 words. 3 words matches
    real query volume far more often while still being specific enough to be
    useful.

    Examples:
    - "How to Build a Web App with Django in 7 Steps" → "build web app"
    - "Airtable vs. ClickUp: Which Tool Designs Better Workflows?" → "airtable vs clickup"
    - "Best SEO Tools for Indie Hackers to Boost Traffic in 2026" → "seo tools indie"
    - "Cómo aprovechar los programas de asistencia alimentaria" → "aprovechar programas asistencia"
    """
    # \w is Unicode-aware in Python 3, so accented letters (á, é, í, ó, ú, ñ)
    # survive this strip instead of being deleted — a bare [^a-z0-9\s] regex
    # turned "cómo" into "cmo" and "línea" into "lnea", neither of which is a
    # real word a keyword database can match (root cause of Spanish keywords
    # always returning 0 results regardless of API health).
    tokens = [
        w for w in re.sub(r"[^\w\s]", "", title.lower()).split()
        if len(w) > 1 and w not in _KEYWORD_STOP
    ]
    # Keep the 3 most meaningful words, joined by SPACES — "best ai tools"
    # has real search volume, "best-ai-tools" is not a phrase anyone types.
    selected = tokens[:3]
    return " ".join(selected)


def _safe_yepapi_items(data: Any) -> list[dict[str, Any]]:
    """Extract the keyword-metric list from a YepAPI response without
    indexing a None value. Documented shape (docs.yepapi.com/seo-keywords/keywords):
    {"ok": true, "data": {"keywords": [{keyword, volume, difficulty, ...}], "skipped": [...]}}
    """
    if not isinstance(data, dict):
        return []
    inner = data.get("data")
    if not isinstance(inner, dict):
        return []
    items = inner.get("keywords")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def fetch_keyword_metrics(
    keywords: list[str], language_code: str = "en"
) -> dict[str, dict[str, Any]]:
    """Fetch keyword metrics (volume, difficulty) from YepAPI.

    Accepts both long titles and short keywords. For each keyword, extracts
    the core keyword and queries YepAPI with that. Returns a dict keyed by
    the ORIGINAL keyword (for lookup compatibility).

    language_code defaults to "en" (pipeline.py's solopreneur niche).
    finance_pipeline.py passes "es" — its keywords are Spanish, and search
    volume is language-sensitive.
    """
    if not YEPAPI_API_KEY:
        print("  ℹ️  YepAPI: credentials not set — skipping keyword metrics")
        return {}

    if not keywords:
        return {}

    print(f"  📊 YepAPI: fetching metrics for {len(keywords)} keywords...")
    results: dict[str, dict[str, Any]] = {}

    # Extract core keywords for API calls
    core_keywords = [extract_core_keyword(kw) for kw in keywords]
    # extract_core_keyword() returns "" when a title is all stopwords/too short.
    # A single empty keyword in a batch can make the API reject the WHOLE
    # batch (every keyword in it looks like it "returned 0 results" with no
    # visible error) — so it must never reach the API.
    unique_cores = [c for c in dict.fromkeys(core_keywords) if c]  # preserve order, dedupe, drop empties

    if not unique_cores:
        print("  ℹ️  YepAPI: no usable core keywords extracted — skipping")
        return {}

    batches = [
        unique_cores[i : i + _BATCH_SIZE]
        for i in range(0, len(unique_cores), _BATCH_SIZE)
    ]

    for batch_idx, batch in enumerate(batches):
        conn = None
        try:
            payload = json.dumps({
                "keywords": batch,
                "location_code": 2840,  # United States — matches both niches (US EN + US-Hispanic ES)
                "language": language_code,
            })
            conn = http.client.HTTPSConnection("api.yepapi.com", timeout=30)
            conn.request(
                "POST",
                "/v1/seo/keywords",
                payload,
                {
                    "x-api-key": YEPAPI_API_KEY,
                    "Content-Type": "application/json",
                },
            )
            response = conn.getresponse()
            raw = response.read().decode("utf-8", errors="replace")

            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                print(f"  ⚠️  YepAPI batch {batch_idx + 1}: invalid JSON: {exc}")
                continue

            if not isinstance(data, dict):
                print(f"  ⚠️  YepAPI batch {batch_idx + 1}: unexpected response type")
                continue

            if not data.get("ok"):
                print(
                    f"  ⚠️  YepAPI batch {batch_idx + 1}: API reported failure — "
                    f"{str(data)[:200]}"
                )
                continue

            skipped = ((data.get("data") or {}).get("skipped")) or []
            if skipped:
                print(f"  ⚠️  YepAPI batch {batch_idx + 1}: {len(skipped)} keyword(s) skipped by the API")

            items = _safe_yepapi_items(data)

            # Build a lookup from core keyword → metrics
            core_metrics: dict[str, dict[str, Any]] = {}
            for item in items:
                keyword = str(item.get("keyword") or "").strip()
                if not keyword:
                    continue

                try:
                    volume = int(item.get("volume") or 0)
                except (TypeError, ValueError):
                    volume = 0

                try:
                    difficulty = int(item.get("difficulty") or 0)
                except (TypeError, ValueError):
                    difficulty = 0

                kw_score = opportunity_score(volume, difficulty)
                core_metrics[keyword.lower()] = {
                    "volume": volume,
                    "difficulty": difficulty,
                    "kw_score": kw_score,
                }

            # Map back to original keywords
            for original_kw, core_kw in zip(keywords, core_keywords):
                meta = core_metrics.get(core_kw.lower())
                if meta:
                    results[original_kw.lower()] = meta
                    results[original_kw.lower().strip()[:60]] = meta  # also index by truncated form

            print(
                f"  ✅ YepAPI batch {batch_idx + 1}/{len(batches)}: "
                f"{len(items)} results returned"
            )

            if batch_idx < len(batches) - 1:
                time.sleep(0.5)

        except Exception as exc:
            print(f"  ⚠️  YepAPI batch {batch_idx + 1} failed (non-critical): {exc}")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    return results


def sort_pool_by_score(
    pool: list[str], metrics: dict[str, dict[str, Any]]
) -> list[str]:
    if not metrics:
        return pool

    scored: list[tuple[str, float]] = []
    unscored: list[str] = []

    for keyword in pool:
        key = keyword.lower().strip()
        # Try multiple lookup strategies
        meta = (
            metrics.get(key) or
            metrics.get(key[:60]) or
            metrics.get(extract_core_keyword(key).lower())
        )
        if not isinstance(meta, dict):
            unscored.append(keyword)
            continue

        try:
            volume = int(meta.get("volume") or 0)
            difficulty = int(meta.get("difficulty") or 0)
            score = float(meta.get("kw_score") or 0)
        except (TypeError, ValueError):
            unscored.append(keyword)
            continue

        if volume >= MIN_VOLUME and difficulty <= MAX_DIFFICULTY:
            scored.append((keyword, score))
        else:
            unscored.append(keyword)

    scored.sort(key=lambda item: item[1], reverse=True)
    sorted_pool = [keyword for keyword, _ in scored] + unscored

    print(
        f"  🎯 YepAPI scoring: {len(scored)} keywords above threshold "
        f"(vol≥{MIN_VOLUME}, diff≤{MAX_DIFFICULTY}), "
        f"{len(unscored)} appended unscored"
    )
    return sorted_pool


def enrich_article_data(
    data: dict, keyword: str, metrics: dict[str, dict[str, Any]]
) -> dict:
    """Enrich article data with keyword metrics.

    Now uses extract_core_keyword() for robust lookup even when
    keyword is a long title.
    """
    key = keyword.lower().strip()
    # Try multiple lookup strategies for robustness
    meta = (
        metrics.get(key) or
        metrics.get(key[:60]) or
        metrics.get(extract_core_keyword(key).lower())
    )

    if isinstance(meta, dict):
        data["search_volume"] = meta.get("volume")
        data["keyword_difficulty"] = meta.get("difficulty")
        data["kw_score"] = meta.get("kw_score")
    else:
        data["search_volume"] = None
        data["keyword_difficulty"] = None
        data["kw_score"] = None

    return data
