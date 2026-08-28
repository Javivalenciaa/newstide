"""
Minimal DataForSEO connectivity check — costs exactly ONE keyword lookup,
nothing else. No Claude/OpenAI calls, no Supabase writes, no articles published.

Run manually via .github/workflows/dataforseo-smoke-test.yml (workflow_dispatch)
or locally with the same env vars pipeline.py needs (DATAFORSEO_LOGIN,
DATAFORSEO_PASSWORD). Prints the raw parsed metrics so we can see with our own
eyes that a real number comes back, instead of trusting the fix blindly.
"""
from dataforseo import fetch_keyword_metrics

TEST_KEYWORD = "best ai tools"

if __name__ == "__main__":
    print(f"🔎 Testing DataForSEO with a single keyword: '{TEST_KEYWORD}'")
    result = fetch_keyword_metrics([TEST_KEYWORD])
    if not result:
        print("❌ Still empty — the fix did not resolve it, or credentials/credit issue.")
    else:
        print(f"✅ Got real data back:\n{result}")
