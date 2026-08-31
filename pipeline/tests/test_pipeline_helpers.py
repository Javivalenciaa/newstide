import pipeline as p
import dataforseo as dfs


def test_smart_trim_cuts_at_word_boundary():
    assert p.smart_trim("hello world foo bar", 12) == "hello world"


def test_smart_trim_noop_under_limit():
    assert p.smart_trim("short title", 60) == "short title"


def test_normalize_excerpt_enforces_max_and_strips_quotes():
    text = '"' + ("word " * 40).strip() + '"'
    out = p.normalize_excerpt(text, 120, 155)
    assert len(out) <= 156
    assert not out.startswith('"')
    assert out.endswith(".")


def test_slugify_strips_punctuation_and_caps_length():
    slug = p.slugify("How to Build a SaaS: The Complete Guide (2026)!!")
    assert slug == slug.lower()
    assert " " not in slug
    assert ":" not in slug and "!" not in slug
    assert len(slug) <= 60


def test_slugify_es_strips_accents():
    assert p.slugify_es("Cómo Invertir en el Mercado Español") == \
        "como-invertir-en-el-mercado-espanol"


def test_md5_is_case_and_whitespace_insensitive():
    assert p.md5("  Best AI Tools  ") == p.md5("best ai tools")


def test_detect_category_matches_known_keyword():
    assert p.detect_category("cursor vs github copilot") == "AI Tools"
    assert p.detect_category("subscription pricing for indie makers") == "Monetization"


def test_detect_category_falls_back_to_default():
    assert p.detect_category("totally unrelated gibberish topic") == "Indie Hacking"


def test_reading_time_has_a_floor():
    assert p.reading_time("word " * 10) == p.MIN_READING_TIME
    assert p.reading_time("word " * 2000) > p.MIN_READING_TIME


def test_strip_code_fences_removes_markdown_wrapper():
    wrapped = "```markdown\n# Title\nBody\n```"
    assert p.strip_code_fences(wrapped) == "# Title\nBody"


def test_is_truncated_detects_lowercase_start_and_short_length():
    assert p.is_truncated("lowercase start of sentence", "reference text here") is True
    assert p.is_truncated("", "anything") is True
    full = "Full sentence. " * 20
    assert p.is_truncated(full, "Full sentence. " * 20) is False


def test_has_external_link_ignores_own_domain():
    assert p.has_external_link("See https://example.com/tool for details") is True
    assert p.has_external_link("See https://newstide.news/articulo/x") is False
    assert p.has_external_link("no links here") is False


def test_derive_keyword_slug_for_hash_drops_stopwords():
    slug = p._derive_keyword_slug_for_hash("How to Build a SaaS Product Solo")
    assert "how" not in slug.split("-")
    assert "to" not in slug.split("-")


def test_jaccard_similarity_bounds():
    a = p._trigrams("hello world")
    b = p._trigrams("hello world")
    assert p._jaccard(a, b) == 1.0
    assert p._jaccard(set(), set()) == 1.0
    assert p._jaccard({"abc"}, set()) == 0.0


def test_extract_headings_gets_h2_and_h3():
    content = "# Title\n## First Section\nBody\n### Sub question?\nAnswer"
    headings = p._extract_headings(content)
    assert "first section" in headings
    assert "sub question" in headings


def test_run_content_guardrails_flags_title_as_keyword():
    data = {
        "content": "Normal article body with no first-person claims.",
        "content_en": "Different enough english content to avoid the duplicate flag here friend.",
        "title": "How To Build A SaaS Product Solo",
        "keyword": "How To Build A SaaS Product Solo",
    }
    status, flags, out = p.run_content_guardrails(data)
    assert status == "needs_review"
    assert any("[C]" in f for f in flags)
    assert out["keyword"] != data["title"]


def test_fetch_gsc_queries_returns_empty_without_credentials(monkeypatch):
    monkeypatch.delenv("GOOGLE_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GSC_SERVICE_ACCOUNT_JSON", raising=False)
    assert p.fetch_gsc_queries() == []


def test_fetch_gsc_queries_fails_closed_on_malformed_service_account_json(monkeypatch):
    monkeypatch.setenv("GSC_SERVICE_ACCOUNT_JSON", "not-valid-json")
    assert p.fetch_gsc_queries() == []


def test_dataforseo_fetch_keyword_metrics_returns_empty_without_credentials(monkeypatch):
    monkeypatch.setattr(dfs, "YEPAPI_API_KEY", "")
    assert dfs.fetch_keyword_metrics(["best ai tools 2026"]) == {}


def test_topic_cluster_key_ignores_niche_stopwords():
    key_a = p.topic_cluster_key("Cursor vs GitHub Copilot for Solopreneurs 2026")
    key_b = p.topic_cluster_key("Cursor vs GitHub Copilot: Best Guide for Indie Hackers")
    assert key_a == key_b


def test_cluster_aware_reorder_boosts_building_depth_clusters():
    recent = [
        {"title_en": "Cursor vs GitHub Copilot comparison", "keyword": ""},
        {"title_en": "Cursor vs GitHub Copilot comparison", "keyword": ""},
        {"title_en": "Cursor vs GitHub Copilot comparison", "keyword": ""},
    ]
    pool = ["How to price your SaaS product solo", "Cursor vs GitHub Copilot comparison"]
    reordered = p.cluster_aware_reorder(pool, recent)
    assert reordered[0] == "Cursor vs GitHub Copilot comparison"


def test_is_duplicate_topic_trgm_true_when_rpc_returns_matches(monkeypatch):
    class _Resp:
        data = [{"title_en": "Cursor vs GitHub Copilot", "slug_en": "cursor-vs-copilot", "similarity": 0.7}]

    class _FakeRpc:
        def execute(self): return _Resp()

    monkeypatch.setattr(p.supabase_client, "rpc", lambda name, params: _FakeRpc())
    assert p.is_duplicate_topic_trgm("Cursor vs GitHub Copilot for solo devs") is True


def test_is_duplicate_topic_trgm_false_when_rpc_returns_nothing(monkeypatch):
    class _Resp:
        data = []

    class _FakeRpc:
        def execute(self): return _Resp()

    monkeypatch.setattr(p.supabase_client, "rpc", lambda name, params: _FakeRpc())
    assert p.is_duplicate_topic_trgm("A totally unique never-before-seen topic") is False


def test_is_duplicate_topic_trgm_fails_closed_on_rpc_error(monkeypatch):
    def _raise(name, params):
        raise RuntimeError("network down")
    monkeypatch.setattr(p.supabase_client, "rpc", _raise)
    assert p.is_duplicate_topic_trgm("Anything") is False


def test_run_content_guardrails_ok_on_clean_data():
    data = {
        "content": "Clean body text with plenty of words describing indie hacking tactics for founders.",
        "content_en": "",
        "title": "Some Real Article Title",
        "keyword": "saas pricing tactics",
    }
    status, flags, _ = p.run_content_guardrails(data)
    assert status in ("ok", "needs_review")  # Check E may warn depending on network, never blocks here
    assert not any(f.startswith("[B]") for f in flags)
