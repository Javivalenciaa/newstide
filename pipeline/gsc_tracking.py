"""
GSC tracking → Supabase.

Pulls daily Search Console performance (page, query, clicks, impressions, ctr,
position) for the site's real article paths and upserts it into `serp_tracking`.
Standalone script, independent of pipeline.py/finance_pipeline.py — does not
touch fetch_gsc_queries() in either (that one only feeds candidate topics).

Runs once a day via .github/workflows/gsc-tracking.yml.
"""
import base64
import json
import os
import sys
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

import requests
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
GSC_SITE_URL = os.environ.get("GSC_SITE_URL", "sc-domain:newstide.news")

from dataforseo import is_junk_query

# Real article routes confirmed in CLAUDE.md — tracking stays scoped to these,
# not the whole site (homepage/category pages aren't individual content to track).
TRACKED_PATH_PREFIXES = ["/en/article/", "/articulo/", "/en/fin/", "/es/fin/"]

# GSC data typically finalizes 2-3 days after the fact; pulling a fixed lag
# avoids upserting partial same-day numbers that would look like a big drop.
REPORT_LAG_DAYS = 3

# How many days back to pull, ending at (today - REPORT_LAG_DAYS).
#   1  → the daily incremental run (default, unchanged behaviour)
#   N  → backfill N days in a single ranged request
#
# The daily run alone can only ever accumulate history going forward, one day
# at a time. This workflow first executed on 2026-09-01, so every earlier day
# — the whole 18 Jun–28 Aug period the site actually has data for — would
# never have entered serp_tracking, and refresh_pipeline.py prioritises from
# this table. GSC retains ~16 months, so a one-off backfill recovers all of it.
BACKFILL_DAYS = max(1, int(os.environ.get("GSC_BACKFILL_DAYS", "1")))

supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_access_token() -> str:
    token = os.environ.get("GOOGLE_ACCESS_TOKEN", "").strip()
    if token:
        return token

    sa_json_raw = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "").strip()
    if not sa_json_raw:
        raise RuntimeError("No GSC credentials set (GOOGLE_ACCESS_TOKEN or GSC_SERVICE_ACCOUNT_JSON)")

    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    sa = json.loads(sa_json_raw)

    def _b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    now = int(time.time())
    header = _b64(b'{"alg":"RS256","typ":"JWT"}')
    payload = _b64(json.dumps({
        "iss": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/webmasters.readonly",
        "aud": "https://oauth2.googleapis.com/token",
        "exp": now + 3600,
        "iat": now,
    }).encode())
    private_key = serialization.load_pem_private_key(
        sa["private_key"].replace("\\n", "\n").encode("utf-8"), password=None
    )
    sig = _b64(private_key.sign(f"{header}.{payload}".encode(), padding.PKCS1v15(), hashes.SHA256()))
    jwt_token = f"{header}.{payload}.{sig}"

    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode({
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_token,
        }),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    access_token = resp.json().get("access_token", "")
    if not access_token:
        raise RuntimeError("GSC token exchange returned no access_token")
    return access_token


def is_tracked_path(page_url: str) -> bool:
    return any(prefix in page_url for prefix in TRACKED_PATH_PREFIXES)


def fetch_serp_rows(
    access_token: str, start_date: str, end_date: str,
    row_limit: int = 5000, max_pages: int = 20,
) -> list[dict]:
    """Pull (date, page, query) rows for a date RANGE in one paged request.

    "date" is part of the dimension tuple rather than issuing one request per
    day: a 90-day backfill is a handful of paged calls instead of 90 separate
    round trips, and each row still carries its own day.
    """
    all_rows: list[dict] = []
    encoded_site = requests.utils.quote(GSC_SITE_URL, safe="")
    url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query"
    for page in range(max_pages):
        payload = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["date", "page", "query"],
            "rowLimit": row_limit,
            "startRow": page * row_limit,
        }
        resp = requests.post(
            url, json=payload,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        rows = resp.json().get("rows", [])
        all_rows.extend(rows)
        if len(rows) < row_limit:
            break
    return all_rows


def build_records(rows: list[dict]) -> tuple[list[dict], int, int]:
    """Turn GSC rows into serp_tracking records.

    Returns (records, skipped_untracked, skipped_junk) so the run reports what
    it discarded instead of silently dropping it.

    Junk queries are excluded on purpose. refresh_pipeline.py chooses what to
    rewrite from this table, so a page whose impressions come from a
    stock-photo credit or a scraper's operator string would otherwise look
    like a page in demand and get picked ahead of one that genuinely is.
    """
    records: list[dict] = []
    skipped_untracked = 0
    skipped_junk = 0

    for row in rows:
        keys = row.get("keys") or []
        if len(keys) < 3:
            continue
        row_date, page, query = keys[0], keys[1], keys[2]

        if not is_tracked_path(page):
            skipped_untracked += 1
            continue
        if is_junk_query(query):
            skipped_junk += 1
            continue

        records.append({
            "date": row_date,
            "page": page,
            "query": query,
            "clicks": int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr": float(row.get("ctr", 0.0)),
            "position": float(row.get("position", 0.0)),
        })

    return records, skipped_untracked, skipped_junk


def upsert_records(records: list[dict], batch_size: int = 500) -> None:
    if not records:
        print("  ℹ️  No tracked rows to upsert")
        return
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        try:
            supabase_client.table("serp_tracking").upsert(
                batch, on_conflict="date,page,query"
            ).execute()
            print(f"  ✅ Upserted rows {i}-{i + len(batch)}")
        except Exception as e:
            print(f"  ⚠️  Upsert batch failed (non-critical): {e}")


def main():
    end_date = (datetime.now(timezone.utc) - timedelta(days=REPORT_LAG_DAYS))
    start_date = end_date - timedelta(days=BACKFILL_DAYS - 1)
    end_str, start_str = end_date.strftime("%Y-%m-%d"), start_date.strftime("%Y-%m-%d")

    if BACKFILL_DAYS > 1:
        print(f"📊 GSC tracking — BACKFILL {BACKFILL_DAYS} days: {start_str} → {end_str}")
    else:
        print(f"📊 GSC tracking for {end_str}")

    try:
        token = get_access_token()
    except Exception as e:
        print(f"⚠️  Could not obtain GSC access token: {e} — aborting run (non-critical)")
        sys.exit(0)

    try:
        rows = fetch_serp_rows(token, start_str, end_str)
    except Exception as e:
        print(f"⚠️  GSC API fetch failed: {e} — aborting run (non-critical)")
        sys.exit(0)

    records, skipped_untracked, skipped_junk = build_records(rows)
    print(f"  📈 {len(rows)} rows from GSC → {len(records)} tracked")
    if skipped_untracked:
        print(f"  ↩️  {skipped_untracked} skipped (not an article path)")
    if skipped_junk:
        print(f"  🧹 {skipped_junk} skipped (junk: photo credits, tool operators)")

    upsert_records(records)
    print("🎉 Done")


if __name__ == "__main__":
    main()
