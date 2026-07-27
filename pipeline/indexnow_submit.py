#!/usr/bin/env python3
"""
IndexNow bulk submitter — llámalo al final de pipeline.py o como script standalone.

Uso standalone:
  python pipeline/indexnow_submit.py  # envía las últimas 50 URLs de Supabase

O importa submit_urls() desde pipeline.py para llamarlo tras publicar artículos.
"""

import os
import requests
from supabase import create_client

INDEXNOW_KEY = os.getenv("INDEXNOW_KEY", "449864d8a7154e33b47bcd42fc5b899a")
HOST = "www.newstide.news"
KEY_LOCATION = f"https://{HOST}/{INDEXNOW_KEY}.txt"
INDEXNOW_API = "https://api.indexnow.org/IndexNow"


def submit_urls(urls: list[str]) -> dict:
    """Submit a list of URLs to IndexNow. Returns the API response info."""
    if not urls:
        return {"skipped": True}

    # IndexNow max 10,000 URLs per request; chunk if needed
    chunk_size = 500
    results = []
    for i in range(0, len(urls), chunk_size):
        chunk = urls[i : i + chunk_size]
        payload = {
            "host": HOST,
            "key": INDEXNOW_KEY,
            "keyLocation": KEY_LOCATION,
            "urlList": chunk,
        }
        resp = requests.post(
            INDEXNOW_API,
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30,
        )
        print(f"[IndexNow] submitted {len(chunk)} URLs → HTTP {resp.status_code}")
        results.append({"submitted": len(chunk), "status": resp.status_code})

    return {"batches": results}


def get_recent_slugs(limit: int = 50) -> list[str]:
    """Fetch the most recently published article slugs from Supabase."""
    url = os.environ["NEXT_PUBLIC_SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    sb = create_client(url, key)

    # Ajusta el nombre de tabla y columna si difiere en tu schema
    result = (
        sb.table("articles")
        .select("slug, slug_en")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    urls = []
    for row in result.data:
        if row.get("slug"):
            urls.append(f"https://{HOST}/articulo/{row['slug']}")
        if row.get("slug_en"):
            urls.append(f"https://{HOST}/en/article/{row['slug_en']}")
    return urls


if __name__ == "__main__":
    print("[IndexNow] Fetching recent articles from Supabase...")
    article_urls = get_recent_slugs(limit=50)
    print(f"[IndexNow] Found {len(article_urls)} URLs to submit")
    submit_urls(article_urls)
