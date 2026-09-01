import gsc_tracking as gt


def test_is_tracked_path_matches_known_prefixes():
    assert gt.is_tracked_path("https://www.newstide.news/en/article/best-ai-tools") is True
    assert gt.is_tracked_path("https://www.newstide.news/articulo/mejores-herramientas") is True
    assert gt.is_tracked_path("https://www.newstide.news/en/fin/roth-ira") is True
    assert gt.is_tracked_path("https://www.newstide.news/es/fin/roth-ira") is True


def test_is_tracked_path_excludes_non_article_pages():
    assert gt.is_tracked_path("https://www.newstide.news/") is False
    assert gt.is_tracked_path("https://www.newstide.news/en/articles/ai-tools") is False


def test_build_records_filters_to_tracked_paths_only():
    # Dimensions are now (date, page, query) so one ranged request can cover a
    # backfill; the date travels with each row instead of being passed in.
    rows = [
        {"keys": ["2026-08-24", "https://www.newstide.news/en/article/best-ai-tools", "best ai tools"],
         "clicks": 5, "impressions": 100, "ctr": 0.05, "position": 8.2},
        {"keys": ["2026-08-24", "https://www.newstide.news/en/articles/ai-tools", "ai tools category"],
         "clicks": 1, "impressions": 50, "ctr": 0.02, "position": 15.0},
    ]
    records, skipped_untracked, skipped_junk = gt.build_records(rows)
    assert len(records) == 1
    assert records[0]["page"] == "https://www.newstide.news/en/article/best-ai-tools"
    assert records[0]["date"] == "2026-08-24"
    assert records[0]["clicks"] == 5
    assert skipped_untracked == 1
    assert skipped_junk == 0


def test_build_records_preserves_each_rows_own_date():
    rows = [
        {"keys": ["2026-08-24", "https://www.newstide.news/articulo/a", "consulta uno"],
         "clicks": 1, "impressions": 10, "ctr": 0.1, "position": 5.0},
        {"keys": ["2026-08-25", "https://www.newstide.news/articulo/a", "consulta uno"],
         "clicks": 2, "impressions": 20, "ctr": 0.1, "position": 4.0},
    ]
    records, _, _ = gt.build_records(rows)
    assert {r["date"] for r in records} == {"2026-08-24", "2026-08-25"}


def test_build_records_drops_junk_queries():
    # A page whose impressions come from a photographer's name or a scraper's
    # operator string would otherwise look like a page in demand, and
    # refresh_pipeline.py picks what to rewrite from this table.
    rows = [
        {"keys": ["2026-08-24", "https://www.newstide.news/articulo/a", "marija zaric unsplash"],
         "clicks": 1, "impressions": 8, "ctr": 0.125, "position": 49.1},
        {"keys": ["2026-08-24", "https://www.newstide.news/articulo/a",
                  '"how to build a landing page" -site:reddit.com'],
         "clicks": 0, "impressions": 9, "ctr": 0.0, "position": 3.9},
        {"keys": ["2026-08-24", "https://www.newstide.news/es/fin/b", "roth ira"],
         "clicks": 0, "impressions": 4, "ctr": 0.0, "position": 12.0},
    ]
    records, _, skipped_junk = gt.build_records(rows)
    assert skipped_junk == 2
    assert len(records) == 1
    assert records[0]["query"] == "roth ira"   # short but real — must survive


def test_build_records_skips_malformed_rows():
    rows = [{"keys": ["2026-08-24", "https://www.newstide.news/en/article/x"]}]  # no query
    records, _, _ = gt.build_records(rows)
    assert records == []


def test_get_access_token_prefers_google_access_token(monkeypatch):
    monkeypatch.setenv("GOOGLE_ACCESS_TOKEN", "pre-existing-token")
    assert gt.get_access_token() == "pre-existing-token"


def test_get_access_token_raises_without_any_credentials(monkeypatch):
    monkeypatch.delenv("GOOGLE_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GSC_SERVICE_ACCOUNT_JSON", raising=False)
    try:
        gt.get_access_token()
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass
