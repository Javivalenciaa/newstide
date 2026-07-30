"""One-shot migration: update all articles in Supabase to author='Javier Valencia'.
Run once from the pipeline environment:
    python pipeline/fix_authors.py
"""
import os
from supabase import create_client

SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

res = client.table("articles").update({"author": "Javier Valencia"}).neq("author", "Javier Valencia").execute()
print(f"✅ Updated {len(res.data)} articles to author='Javier Valencia'")
