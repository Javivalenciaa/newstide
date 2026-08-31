import base64
import http.client
import json
import os
import re
import time
from typing import Any

DATAFORSEO_LOGIN = os.environ.get("DATAFORSEO_LOGIN", "")
DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD", "")

MIN_VOLUME = 100
MAX_DIFFICULTY = 70
_BATCH_SIZE = 100

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

    DataForSEO Google Ads Search Volume API has real volume data mostly for
    short head/mid-tail phrases. Long titles (8-11 words) like "How to Build
    a Web App with Django in 7 Steps" return 0 results, and even a 5-word
    extracted core ("build simple ecommerce site shopify") usually still
    does — real runs on 2026-08-31 got data back for 38/38 keywords but 0
    cleared the volume threshold at 5 words. 3 words matches real query
    volume far more often while still being specific enough to be useful.

    Examples:
    - "How to Build a Web App with Django in 7 Steps" → "build web app"
    - "Airtable vs. ClickUp: Which Tool Designs Better Workflows?" → "airtable vs clickup"
    - "Best SEO Tools for Indie Hackers to Boost Traffic in 2026" → "seo tools indie"
    - "Cómo aprovechar los programas de asistencia alimentaria" → "aprovechar programas asistencia"
    """
    # \w is Unicode-aware in Python 3, so accented letters (á, é, í, ó, ú, ñ)
    # survive this strip instead of being deleted — a bare [^a-z0-9\s] regex
    # turned "cómo" into "cmo" and "línea" into "lnea", neither of which is a
    # real word DataForSEO's keyword database can match (root cause of
    # Spanish keywords always returning 0 results regardless of API health).
    tokens = [
        w for w in re.sub(r"[^\w\s]", "", title.lower()).split()
        if len(w) > 1 and w not in _KEYWORD_STOP
    ]
    # Keep the 3 most meaningful words, joined by SPACES.
    # Google Ads Search Volume matches real search phrases: "best ai tools"
    # has volume, "best-ai-tools" is not a phrase anyone types and returns 0.
    # This function joined tokens with "-" since the file was created, while
    # its own docstring documented spaces — so every lookup in both pipelines
    # (English and Spanish alike) asked for a string no user has ever
    # searched. That is why DataForSEO reported 0 results on every run even
    # after the response-parsing and accent fixes. 5 words was also tried and
    # confirmed too long in production (2026-08-31: 38/38 keywords returned
    # data, 0/38 cleared the volume threshold) — 3 words matches real query
    # volume much more often.
    selected = tokens[:3]
    return " ".join(selected)


def _log_task_errors(data: dict, batch_idx: int) -> None:
    """DataForSEO's v3 API separates a top-level status_code (was the HTTP request
    well-formed?) from a PER-TASK status_code (did the task itself succeed? e.g.
    40402 = insufficient credits, 40501 = invalid field). fetch_keyword_metrics()
    only ever checked the top-level one, so a task-level failure (most commonly:
    no balance on the account) silently looked identical to "0 results, no volume
    data available" — this makes that failure visible instead of silent."""
    tasks_error = data.get("tasks_error")
    if tasks_error:
        print(f"  ⚠️  DataForSEO batch {batch_idx + 1}: {tasks_error} task(s) reported an error")
    for task in data.get("tasks") or []:
        if not isinstance(task, dict):
            continue
        task_status = task.get("status_code")
        if task_status and task_status != 20000:
            print(
                f"  ⚠️  DataForSEO batch {batch_idx + 1}: task status={task_status} "
                f"msg={str(task.get('status_message', ''))[:150]}"
            )

def _safe_items(data: Any) -> list[dict[str, Any]]:
    """Extract result items without indexing a None value.

    google_ads/search_volume/live returns keyword-metric objects DIRECTLY in
    tasks[i]["result"] (each dict has a "keyword" field) — it does NOT nest
    them inside a result_item["items"] wrapper the way SERP-type endpoints do.
    The original version only ever checked for that "items" wrapper, so it
    silently returned [] on every single call to this endpoint regardless of
    whether DataForSEO actually had data — root cause of the "0 results
    returned" runs on 2026-08-28 (both pipelines, both languages, no error of
    any kind — a perfectly successful response that was just parsed wrong).
    """
    if not isinstance(data, dict):
        return []

    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        return []

    for task in tasks:
        if not isinstance(task, dict):
            continue
        result = task.get("result")
        if not isinstance(result, list):
            continue

        # Shape actually returned by this endpoint: result = [{keyword, search_volume, ...}, ...]
        flat_items = [r for r in result if isinstance(r, dict) and "keyword" in r]
        if flat_items:
            return flat_items

        # Fallback shape (SERP-type endpoints): result = [{items: [...]}]
        for result_item in result:
            if not isinstance(result_item, dict):
                continue
            items = result_item.get("items")
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]

    return []


def fetch_keyword_metrics(
    keywords: list[str], language_code: str = "en"
) -> dict[str, dict[str, Any]]:
    """Fetch keyword metrics from DataForSEO.

    Now accepts both long titles and short keywords. For each keyword,
    extracts the core keyword and queries DataForSEO with that.
    Returns a dict keyed by the ORIGINAL keyword (for lookup compatibility).

    language_code defaults to "en" (pipeline.py's solopreneur niche, unchanged
    behavior). finance_pipeline.py passes "es" — its keywords are Spanish, and
    Google Ads keyword volume is language-sensitive.
    """
    if not DATAFORSEO_LOGIN or not DATAFORSEO_PASSWORD:
        print("  ℹ️  DataForSEO: credentials not set — skipping keyword metrics")
        return {}

    if not keywords:
        return {}

    print(f"  📊 DataForSEO: fetching metrics for {len(keywords)} keywords...")
    results: dict[str, dict[str, Any]] = {}
    
    # Extract core keywords for API calls
    core_keywords = [extract_core_keyword(kw) for kw in keywords]
    # extract_core_keyword() returns "" when a title is all stopwords/too short.
    # A single empty keyword in a batch can make DataForSEO reject the WHOLE
    # batch (every keyword in it looks like it "returned 0 results" with no
    # visible error) — so it must never reach the API.
    unique_cores = [c for c in dict.fromkeys(core_keywords) if c]  # preserve order, dedupe, drop empties

    if not unique_cores:
        print("  ℹ️  DataForSEO: no usable core keywords extracted — skipping")
        return {}

    batches = [
        unique_cores[i : i + _BATCH_SIZE]
        for i in range(0, len(unique_cores), _BATCH_SIZE)
    ]

    auth_token = base64.b64encode(
        f"{DATAFORSEO_LOGIN}:{DATAFORSEO_PASSWORD}".encode("utf-8")
    ).decode("ascii")

    for batch_idx, batch in enumerate(batches):
        conn = None
        try:
            payload = json.dumps(
                [
                    {
                        "keywords": batch,
                        "language_code": language_code,
                        "location_code": 2840,
                    }
                ]
            )
            conn = http.client.HTTPSConnection("api.dataforseo.com", timeout=30)
            conn.request(
                "POST",
                "/v3/keywords_data/google_ads/search_volume/live",
                payload,
                {
                    "Authorization": f"Basic {auth_token}",
                    "Content-Type": "application/json",
                },
            )
            response = conn.getresponse()
            raw = response.read().decode("utf-8", errors="replace")

            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                print(
                    f"  ⚠️  DataForSEO batch {batch_idx + 1}: invalid JSON: {exc}"
                )
                continue

            if not isinstance(data, dict):
                print(
                    f"  ⚠️  DataForSEO batch {batch_idx + 1}: unexpected response type"
                )
                continue

            if data.get("status_code") != 20000:
                print(
                    f"  ⚠️  DataForSEO batch {batch_idx + 1}: API error "
                    f"status={data.get('status_code')} "
                    f"msg={str(data.get('status_message', ''))[:120]}"
                )
                continue

            _log_task_errors(data, batch_idx)
            items = _safe_items(data)

            # Build a lookup from core keyword → metrics
            core_metrics: dict[str, dict[str, Any]] = {}
            for item in items:
                keyword = str(item.get("keyword") or "").strip()
                if not keyword:
                    continue

                try:
                    volume = int(item.get("search_volume") or 0)
                except (TypeError, ValueError):
                    volume = 0

                try:
                    competition = float(item.get("competition") or 0)
                except (TypeError, ValueError):
                    competition = 0.0

                difficulty = round(competition * 100)
                kw_score = round(volume / (difficulty + 1), 2)
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
                f"  ✅ DataForSEO batch {batch_idx + 1}/{len(batches)}: "
                f"{len(items)} results returned"
            )

            if batch_idx < len(batches) - 1:
                time.sleep(0.5)

        except Exception as exc:
            print(
                f"  ⚠️  DataForSEO batch {batch_idx + 1} failed "
                f"(non-critical): {exc}"
            )
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
        f"  🎯 DataForSEO scoring: {len(scored)} keywords above threshold "
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
