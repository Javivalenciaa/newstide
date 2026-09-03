import refresh_pipeline as rp


def test_refresh_priority_favors_quick_win_position_range():
    quick_win = rp.refresh_priority(impressions=1000, avg_position=10)
    already_top = rp.refresh_priority(impressions=1000, avg_position=2)
    low_impressions = rp.refresh_priority(impressions=1000, avg_position=40)
    assert quick_win > already_top
    assert quick_win > low_impressions


def test_pick_refresh_candidate_prefers_higher_serp_score(monkeypatch):
    monkeypatch.setattr(rp, "fetch_refresh_candidates", lambda table, tf, sf: (
        [{"id": "a1", "title_en": "Old AI tools article", "slug_en": "old-ai-tools"}]
        if table == "articles" else
        [{"id": "f1", "title": "Old finance article", "slug": "old-finance"}]
    ))
    monkeypatch.setattr(rp, "fetch_serp_scores", lambda pages: {
        "https://www.newstide.news/en/article/old-ai-tools": {"impressions": 50, "avg_position": 10},
        "https://www.newstide.news/es/fin/old-finance": {"impressions": 5000, "avg_position": 8},
    })
    candidate = rp.pick_refresh_candidate()
    assert candidate["table"] == "finance_articles"


def test_pick_refresh_candidate_returns_none_when_no_candidates(monkeypatch):
    monkeypatch.setattr(rp, "fetch_refresh_candidates", lambda table, tf, sf: [])
    assert rp.pick_refresh_candidate() is None


def test_pick_refresh_candidate_handles_missing_serp_data(monkeypatch):
    monkeypatch.setattr(rp, "fetch_refresh_candidates", lambda table, tf, sf: (
        [{"id": "a1", "title_en": "Untracked article", "slug_en": "untracked"}]
        if table == "articles" else []
    ))
    monkeypatch.setattr(rp, "fetch_serp_scores", lambda pages: {})
    candidate = rp.pick_refresh_candidate()
    assert candidate is not None
    assert candidate["table"] == "articles"


def test_strip_h1_removes_leading_heading_only():
    assert rp._strip_h1("# My Title\nBody text here") == "Body text here"
    assert rp._strip_h1("No heading\nBody text") == "No heading\nBody text"


# ── 2026-09-03 regressions ───────────────────────────────────────────────────
def test_retention_floor_rejects_a_materially_shorter_rewrite():
    # MIN_CONTENT_RETENTION was declared but never referenced; the prompt says
    # "Do NOT shorten the article", so a rewrite this much shorter is a failure.
    original = "word " * 1000
    shrunk = "word " * 500          # 50% kept, floor is 70%
    assert rp._lost_too_much_content(shrunk, original) is True


def test_retention_floor_accepts_a_normal_rewrite():
    original = "word " * 1000
    rewritten = "word " * 950
    assert rp._lost_too_much_content(rewritten, original) is False


def test_retention_floor_ignores_an_empty_original():
    assert rp._lost_too_much_content("anything", "") is False


def test_stub_articles_are_skipped_before_any_claude_call(monkeypatch, capsys):
    # The two rows that crashed the 09-03 run were 220 and 366 words. A refresh
    # cannot improve a stub, and picking them daily burns Claude calls.
    called = []

    class _FakeQuery:
        def select(self, *a, **k): return self
        def eq(self, *a, **k): return self
        def single(self): return self
        def execute(self):
            return type("R", (), {"data": {"id": 1, "content_en": "word " * 220}})()

    class _FakeSupabase:
        def table(self, *_a, **_k): return _FakeQuery()

    monkeypatch.setattr(rp.p, "supabase_client", _FakeSupabase())
    monkeypatch.setattr(rp, "_refresh_main_article", lambda *a, **k: called.append(1) or True)

    result = rp.refresh_article({
        "table": "articles", "row": {"id": 1},
        "page": "https://www.newstide.news/en/article/stub",
    })

    assert result is False
    assert called == [], "a stub must never reach the Claude call"
    assert "too thin to refresh" in capsys.readouterr().out


def test_declined_articles_are_filtered_out_of_the_candidate_pool(monkeypatch, capsys):
    rows = [
        {"id": 1, "title_en": "ok",      "slug_en": "ok",      "published_at": "2026-01-01", "updated_at": None, "refresh_blocked_at": None},
        {"id": 2, "title_en": "blocked", "slug_en": "blocked", "published_at": "2026-01-01", "updated_at": None, "refresh_blocked_at": "2026-09-03T12:00:00Z"},
    ]

    class _FakeQuery:
        def select(self, *a, **k): return self
        def lte(self, *a, **k): return self
        def order(self, *a, **k): return self
        def limit(self, *a, **k): return self
        @property
        def not_(self): return self
        def is_(self, *a, **k): return self
        def execute(self): return type("R", (), {"data": rows})()

    class _FakeSupabase:
        def table(self, *_a, **_k): return _FakeQuery()

    monkeypatch.setattr(rp.p, "supabase_client", _FakeSupabase())
    out = rp.fetch_refresh_candidates("articles", "title_en", "slug_en")

    assert [r["id"] for r in out] == [1]
    assert "previously declined" in capsys.readouterr().out
