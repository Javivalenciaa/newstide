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
_KEYWORD_STOP = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","can","could","should","may",
    "might","shall","how","what","why","when","where","which","who","your",
    "our","vs","vs.","this","that","these","those","it","its","as","on",
    "into","through","during","before","after","above","below","between",
    "under","again","further","then","once","here","there","all","each",
    "few","more","most","other","some","such","no","nor","not","only",
    "own","same","so","than","too","very","just","also","now","about",
}

def extract_core_keyword(title: str) -> str:
    """Extract a short, search-intent keyword from a long title.
    
    DataForSEO Google Ads Search Volume API works best with 2-5 word keywords.
    Long titles (8-11 words) like "How to Build a Web App with Django in 7 Steps"
    return 0 results. This function extracts the core topic.
    
    Examples:
    - "How to Build a Web App with Django in 7 Steps" → "build web app django"
    - "Airtable vs. ClickUp: Which Tool Designs Better Workflows?" → "airtable vs clickup"
    - "Best SEO Tools for Indie Hackers to Boost Traffic in 2026" → "seo tools indie hackers"
    """
    tokens = [
        w for w in re.sub(r"[^a-z0-9\s]", "", title.lower()).split()
        if len(w) > 1 and w not in _KEYWORD_STOP
    ]
    # Keep 3-5 most meaningful words
    selected = tokens[:5]
    if len(selected) < 3 and len(tokens) >= 3:
        return "-".join(tokens[:3])
    return "-".join(selected)


def _safe_items(data: Any) -> list[dict[str, Any]]:
    """Extract result items without indexing a None value."""
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
        for result_item in result:
            if not isinstance(result_item, dict):
                continue
            items = result_item.get("items")
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]

    return []


def fetch_keyword_metrics(keywords: list[str]) -> dict[str, dict[str, Any]]:
    """Fetch keyword metrics from DataForSEO.
    
    Now accepts both long titles and short keywords. For each keyword,
    extracts the core keyword and queries DataForSEO with that.
    Returns a dict keyed by the ORIGINAL keyword (for lookup compatibility).
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
    unique_cores = list(dict.fromkeys(core_keywords))  # preserve order, dedupe
    
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
                        "language_code": "en",
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
