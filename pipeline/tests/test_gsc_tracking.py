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
    rows = [
        {"keys": ["https://www.newstide.news/en/article/best-ai-tools", "best ai tools"],
         "clicks": 5, "impressions": 100, "ctr": 0.05, "position": 8.2},
        {"keys": ["https://www.newstide.news/en/articles/ai-tools", "ai tools category"],
         "clicks": 1, "impressions": 50, "ctr": 0.02, "position": 15.0},
    ]
    records = gt.build_records(rows, "2026-08-24")
    assert len(records) == 1
    assert records[0]["page"] == "https://www.newstide.news/en/article/best-ai-tools"
    assert records[0]["date"] == "2026-08-24"
    assert records[0]["clicks"] == 5


def test_build_records_skips_malformed_rows():
    rows = [{"keys": ["https://www.newstide.news/en/article/x"]}]  # missing query dimension
    assert gt.build_records(rows, "2026-08-24") == []


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
