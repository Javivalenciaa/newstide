"""
dataforseo.py — Shared DataForSEO keyword metrics module for NewsTide pipelines.

Used by: pipeline.py (articles table) and finance_pipeline.py (finance_articles table).

Responsibilities:
  1. fetch_keyword_metrics(keywords)  → dict[keyword, {volume, difficulty, kw_score}]
  2. sort_pool_by_score(pool, metrics) → pool sorted best-first, unscored appended last
  3. enrich_article_data(data, kw, metrics) → adds search_volume / keyword_difficulty /
     kw_score fields to the article dict before Supabase insert

Degrades gracefully: if DATAFORSEO_LOGIN or DATAFORSEO_PASSWORD env vars are not set,
or if the API call fails for any reason, every function returns safe fallback values
so neither pipeline is ever blocked.

DataForSEO endpoint used:
  POST https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live
  Auth: HTTP Basic (login:password, base64-encoded)
  Cost: ~$0.0006 per keyword — for 30 kw/day ≈ $0.54/month
"""

import base64
import http.client
import json
import math
import os
import time
from typing import Any

# ── CONFIG ────────────────────────────────────────────────────────────────────
DATAFORSEO_LOGIN    = os.environ.get("DATAFORSEO_LOGIN", "")
DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD", "")

# Keyword filtering thresholds — tune here, nowhere else
MIN_VOLUME     = 100    # discard keywords with < 100 monthly searches
MAX_DIFFICULTY = 70     # discard keywords with SEO difficulty > 70
# Score formula: volume / (difficulty + 1) — higher = better ROI
# difficulty+1 avoids division-by-zero on brand-new keywords (difficulty=0)

# DataForSEO rate limit: max 2000 keywords/min on live endpoint.
# We batch in groups of 100 to stay well within limits and keep calls cheap.
_BATCH_SIZE = 100


# ── MAIN ENTRY POINT ─────────────────────────────────────────────────────────

def fetch_keyword_metrics(keywords: list[str]) -> dict[str, dict[str, Any]]:
    """
    Fetch monthly search volume + SEO difficulty for each keyword.

    Returns a dict keyed by the original keyword string:
        {
          "cursor vs github copilot": {
              "volume":     4400,
              "difficulty": 28,
              "kw_score":   152.0   # volume / (difficulty + 1)
          },
          ...
        }

    If credentials are missing or the API call fails, returns {} so the caller
    can continue without keyword data (pipelines degrade gracefully).
    """
    if not DATAFORSEO_LOGIN or not DATAFORSEO_PASSWORD:
        print("  ℹ️  DataForSEO: credentials not set — skipping keyword metrics")
        return {}

    if not keywords:
        return {}

    print(f"  📊 DataForSEO: fetching metrics for {len(keywords)} keywords...")

    results: dict[str, dict[str, Any]] = {}
    batches = [
        keywords[i : i + _BATCH_SIZE]
        for i in range(0, len(keywords), _BATCH_SIZE)
    ]

    auth_token = base64.b64encode(
        f"{DATAFORSEO_LOGIN}:{DATAFORSEO_PASSWORD}".encode()
    ).decode()

    for batch_idx, batch in enumerate(batches):
        try:
            payload = json.dumps(
                [
                    {
                        "keywords": batch,
                        "language_code": "en",
                        "location_code": 2840,  # United States
                    }
                ]
            )
            conn = http.client.HTTPSConnection("api.dataforseo.com")
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
            raw = response.read().decode()
            conn.close()

            data = json.loads(raw)

            if data.get("status_code") != 20000:
                print(
                    f"  ⚠️  DataForSEO batch {batch_idx+1}: API error "
                    f"status={data.get('status_code')} msg={data.get('status_message', '')[:80]}"
                )
                continue

            items = (
                data.get("tasks", [{}])[0]
                .get("result", [{}])[0]
                .get("items", [])
                or []
            )

            for item in items:
                kw         = item.get("keyword", "")
                volume     = int(item.get("search_volume") or 0)
                competition = float(item.get("competition") or 0)  # 0.0–1.0
                # DataForSEO "competition" is an AdWords metric (0–1).
                # We convert it to a 0–100 SEO difficulty proxy.
                # This is directionally correct for topic prioritisation:
                # high ad competition ≈ high organic competition.
                difficulty = round(competition * 100)
                kw_score   = round(volume / (difficulty + 1), 2)
                results[kw.lower().strip()] = {
                    "volume":     volume,
                    "difficulty": difficulty,
                    "kw_score":   kw_score,
                }

            print(
                f"  ✅ DataForSEO batch {batch_idx+1}/{len(batches)}: "
                f"{len(items)} results returned"
            )

            # Polite pause between batches
            if batch_idx < len(batches) - 1:
                time.sleep(0.5)

        except Exception as exc:
            print(f"  ⚠️  DataForSEO batch {batch_idx+1} failed (non-critical): {exc}")
            continue

    return results


def sort_pool_by_score(
    pool: list[str], metrics: dict[str, dict[str, Any]]
) -> list[str]:
    """
    Re-order pool so high-ROI keywords (high volume, low difficulty) come first.

    Keywords that pass both MIN_VOLUME and MAX_DIFFICULTY filters are sorted
    descending by kw_score and placed at the top of the pool.
    Keywords with no metrics data or below-threshold scores are appended at the
    end in their original order — they are never discarded, just deprioritised.
    This guarantees the pipeline always has candidates even when DataForSEO
    returns partial or empty results.
    """
    if not metrics:
        return pool  # no data — return original order unchanged

    scored, unscored = [], []

    for kw in pool:
        key = kw.lower().strip()
        # Try exact match first, then substring match on first 50 chars
        meta = metrics.get(key) or metrics.get(key[:50])
        if meta:
            vol  = meta["volume"]
            diff = meta["difficulty"]
            # Apply quality filters — below threshold goes to unscored bucket
            if vol >= MIN_VOLUME and diff <= MAX_DIFFICULTY:
                scored.append((kw, meta["kw_score"]))
            else:
                unscored.append(kw)
        else:
            unscored.append(kw)

    # Sort scored pool best-first
    scored.sort(key=lambda x: x[1], reverse=True)

    total_scored = len(scored)
    sorted_pool  = [kw for kw, _ in scored] + unscored

    print(
        f"  🎯 DataForSEO scoring: {total_scored} keywords above threshold "
        f"(vol≥{MIN_VOLUME}, diff≤{MAX_DIFFICULTY}), "
        f"{len(unscored)} appended unscored"
    )
    return sorted_pool


def enrich_article_data(
    data: dict, keyword: str, metrics: dict[str, dict[str, Any]]
) -> dict:
    """
    Add search_volume, keyword_difficulty, and kw_score to the article data dict.

    Called by save_article() in both pipeline.py and finance_pipeline.py,
    just before the Supabase insert. The three new fields are optional columns
    (added via ALTER TABLE … IF NOT EXISTS) so existing rows are unaffected.

    If no metrics are available for this keyword the fields are set to None,
    which Supabase stores as NULL — never blocks the insert.
    """
    key  = keyword.lower().strip()
    meta = metrics.get(key) or metrics.get(key[:50])
    if meta:
        data["search_volume"]       = meta["volume"]
        data["keyword_difficulty"]   = meta["difficulty"]
        data["kw_score"]             = meta["kw_score"]
    else:
        data["search_volume"]       = None
        data["keyword_difficulty"]   = None
        data["kw_score"]             = None
    return data
