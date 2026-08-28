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

# Real article routes confirmed in CLAUDE.md — tracking stays scoped to these,
# not the whole site (homepage/category pages aren't individual content to track).
TRACKED_PATH_PREFIXES = ["/en/article/", "/articulo/", "/en/fin/", "/es/fin/"]

# GSC data typically finalizes 2-3 days after the fact; pulling a fixed lag
# avoids upserting partial same-day numbers that would look like a big drop.
REPORT_LAG_DAYS = 3

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
    access_token: str, target_date: str, row_limit: int = 5000, max_pages: int = 5
) -> list[dict]:
    all_rows: list[dict] = []
    encoded_site = requests.utils.quote(GSC_SITE_URL, safe="")
    url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query"
    for page in range(max_pages):
        payload = {
            "startDate": target_date,
            "endDate": target_date,
            "dimensions": ["page", "query"],
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


def build_records(rows: list[dict], target_date: str) -> list[dict]:
    records = []
    for row in rows:
        keys = row.get("keys") or []
        if len(keys) < 2:
            continue
        page, query = keys[0], keys[1]
        if not is_tracked_path(page):
            continue
        records.append({
            "date": target_date,
            "page": page,
            "query": query,
            "clicks": int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr": float(row.get("ctr", 0.0)),
            "position": float(row.get("position", 0.0)),
        })
    return records


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
    target_date = (datetime.now(timezone.utc) - timedelta(days=REPORT_LAG_DAYS)).strftime("%Y-%m-%d")
    print(f"📊 GSC tracking for {target_date}")

    try:
        token = get_access_token()
    except Exception as e:
        print(f"⚠️  Could not obtain GSC access token: {e} — aborting run (non-critical)")
        sys.exit(0)

    try:
        rows = fetch_serp_rows(token, target_date)
    except Exception as e:
        print(f"⚠️  GSC API fetch failed: {e} — aborting run (non-critical)")
        sys.exit(0)

    records = build_records(rows, target_date)
    print(f"  📈 {len(rows)} total rows from GSC, {len(records)} within tracked article paths")
    upsert_records(records)
    print("🎉 Done")


if __name__ == "__main__":
    main()
