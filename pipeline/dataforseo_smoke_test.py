"""
Minimal YepAPI connectivity check — costs exactly ONE keyword lookup ($0.15),
nothing else. No Claude/OpenAI calls, no Supabase writes, no articles published.

Run manually via .github/workflows/dataforseo-smoke-test.yml (workflow_dispatch)
or locally with the same env var pipeline.py needs (YEPAPI_API_KEY). Prints the
raw parsed metrics so we can see with our own eyes that a real number comes
back, instead of trusting the integration blindly.
"""
from dataforseo import fetch_keyword_metrics

TEST_KEYWORD = "best ai tools"

if __name__ == "__main__":
    print(f"🔎 Testing YepAPI with a single keyword: '{TEST_KEYWORD}'")
    result = fetch_keyword_metrics([TEST_KEYWORD])
    if not result:
        print("❌ Still empty — check YEPAPI_API_KEY / credit balance.")
    else:
        print(f"✅ Got real data back:\n{result}")
