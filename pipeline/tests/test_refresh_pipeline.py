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
