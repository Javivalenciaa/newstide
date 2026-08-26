import os
import hashlib
import re
import time
import unicodedata
import requests
import json
from datetime import datetime, timezone, timedelta
from serpapi import GoogleSearch
from openai import OpenAI
import anthropic
from supabase import create_client
from dataforseo import fetch_keyword_metrics, sort_pool_by_score, enrich_article_data

# ── CONFIG ────────────────────────────────────────────────────────────────────
SERPAPI_KEY          = os.environ["SERPAPI_KEY"]
OPENAI_API_KEY       = os.environ["OPENAI_API_KEY"]
ANTHROPIC_API_KEY    = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
UNSPLASH_ACCESS_KEY  = os.environ["UNSPLASH_ACCESS_KEY"]

# GSC — optional. Set GSC_SERVICE_ACCOUNT_JSON (JSON string from GitHub secret).
# If absent, fetch_gsc_queries() returns [] and the pipeline continues normally.
GSC_SITE_URL = os.environ.get("GSC_SITE_URL", "sc-domain:newstide.news")
GSC_SERVICE_ACCOUNT_JSON = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "")