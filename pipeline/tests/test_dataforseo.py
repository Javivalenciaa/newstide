import json

import dataforseo as dfs


# Real YepAPI shape (docs.yepapi.com/seo-keywords/keywords):
# {"ok": true, "data": {"keywords": [{keyword, volume, difficulty, ...}], "skipped": [...]}}
_DEFAULT_RESPONSE = {
    "ok": True,
    "data": {"keywords": [], "skipped": []},
}


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode()


class _FakeConn:
    sent_payloads = []
    response_data = _DEFAULT_RESPONSE

    def __init__(self, *a, **k): pass
    def request(self, method, path, payload, headers):
        _FakeConn.sent_payloads.append(json.loads(payload))
    def getresponse(self): return _FakeResponse(_FakeConn.response_data)
    def close(self): pass


def test_extract_core_keyword_uses_spaces_not_hyphens():
    # Keyword-volume APIs match real search phrases. A hyphen-joined
    # string is not a phrase anyone searches for and always returns 0 volume,
    # which is exactly what both pipelines saw on every run under DataForSEO.
    assert dfs.extract_core_keyword("Best AI Tools for Solopreneurs in 2026") == (
        "best ai tools"
    )
    assert "-" not in dfs.extract_core_keyword("How to Build a Web App with Django")


def test_extract_core_keyword_keeps_vs_for_comparison_titles():
    # "vs" used to be stripped as a stopword, turning "Trello vs. ClickUp" into
    # "trello clickup tool fits solo" — 5 words, missing the one word that
    # signals a comparison query, that nobody actually searches for.
    assert dfs.extract_core_keyword(
        "Trello vs. ClickUp: Which Tool Fits Solo Projects Better?"
    ) == "trello vs clickup"
    assert dfs.extract_core_keyword(
        "Airtable vs. ClickUp: Which Tool Designs Better Workflows?"
    ) == "airtable vs clickup"


def test_extract_core_keyword_preserves_spanish_accents_and_drops_filler():
    # An ASCII-only strip turned "cómo" into "cmo" and "planificación" into
    # "planificacin" — non-words that can never match a real keyword. Spanish
    # stopwords ("los", "de", "la", "para") must not eat the 3-token budget.
    core = dfs.extract_core_keyword(
        "Cómo aprovechar los programas de asistencia alimentaria para inmigrantes"
    )
    assert core == "aprovechar programas asistencia"

    accented = dfs.extract_core_keyword(
        "Los beneficios de la planificación patrimonial para hispanos"
    )
    assert "planificación" in accented
    assert "planificacin" not in accented


def test_fetch_keyword_metrics_returns_empty_without_api_key(monkeypatch):
    monkeypatch.setattr(dfs, "YEPAPI_API_KEY", "")
    assert dfs.fetch_keyword_metrics(["best ai tools"]) == {}


def test_fetch_keyword_metrics_defaults_to_english(monkeypatch):
    monkeypatch.setattr(dfs, "YEPAPI_API_KEY", "test-key")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    _FakeConn.response_data = _DEFAULT_RESPONSE
    dfs.fetch_keyword_metrics(["best ai tools for solopreneurs"])
    assert _FakeConn.sent_payloads[0]["language"] == "en"


def test_fetch_keyword_metrics_accepts_spanish_for_finance_pipeline(monkeypatch):
    monkeypatch.setattr(dfs, "YEPAPI_API_KEY", "test-key")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    _FakeConn.response_data = _DEFAULT_RESPONSE
    dfs.fetch_keyword_metrics(["como construir credito en usa"], language_code="es")
    assert _FakeConn.sent_payloads[0]["language"] == "es"


def test_fetch_keyword_metrics_sends_us_location_code(monkeypatch):
    monkeypatch.setattr(dfs, "YEPAPI_API_KEY", "test-key")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    _FakeConn.response_data = _DEFAULT_RESPONSE
    dfs.fetch_keyword_metrics(["best ai tools"])
    assert _FakeConn.sent_payloads[0]["location_code"] == 2840


def test_fetch_keyword_metrics_drops_empty_core_keywords_from_batch(monkeypatch):
    # "a to of" is all stopwords -> extract_core_keyword() returns "". A single
    # empty keyword must never reach the API — it can poison the whole batch.
    monkeypatch.setattr(dfs, "YEPAPI_API_KEY", "test-key")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    _FakeConn.response_data = _DEFAULT_RESPONSE
    dfs.fetch_keyword_metrics(["a to of", "best ai tools for solopreneurs"])
    sent_keywords = _FakeConn.sent_payloads[0]["keywords"]
    assert "" not in sent_keywords


def test_fetch_keyword_metrics_all_empty_core_keywords_skips_api_call(monkeypatch):
    monkeypatch.setattr(dfs, "YEPAPI_API_KEY", "test-key")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    result = dfs.fetch_keyword_metrics(["a to of", "on in at"])
    assert result == {}
    assert _FakeConn.sent_payloads == []


def test_fetch_keyword_metrics_parses_real_yepapi_shape(monkeypatch):
    # docs.yepapi.com/seo-keywords/keywords: {"ok": true, "data": {"keywords": [...]}}
    # difficulty comes back DIRECTLY from YepAPI (0-100), unlike DataForSEO,
    # which only gave a 0-1 "competition" float that had to be multiplied by 100.
    monkeypatch.setattr(dfs, "YEPAPI_API_KEY", "test-key")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    _FakeConn.response_data = {
        "ok": True,
        "data": {
            "keywords": [
                {"keyword": "best ai tools", "volume": 720, "difficulty": 34, "cpc": 2.1},
            ],
            "skipped": [],
        },
    }
    result = dfs.fetch_keyword_metrics(["Best AI Tools for Solopreneurs in 2026"])
    assert result != {}
    meta = result.get("best ai tools for solopreneurs in 2026")
    assert meta is not None
    assert meta["volume"] == 720
    assert meta["difficulty"] == 34


def test_fetch_keyword_metrics_handles_api_failure_response(monkeypatch, capsys):
    monkeypatch.setattr(dfs, "YEPAPI_API_KEY", "test-key")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    _FakeConn.response_data = {"ok": False, "error": "invalid api key"}
    result = dfs.fetch_keyword_metrics(["best ai tools"])
    assert result == {}
    captured = capsys.readouterr()
    assert "YepAPI" in captured.out


def test_fetch_keyword_metrics_logs_skipped_keywords(monkeypatch, capsys):
    monkeypatch.setattr(dfs, "YEPAPI_API_KEY", "test-key")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    _FakeConn.response_data = {
        "ok": True,
        "data": {
            "keywords": [],
            "skipped": [{"keyword": "best ai tools", "reason": "no data"}],
        },
    }
    dfs.fetch_keyword_metrics(["best ai tools"])
    captured = capsys.readouterr()
    assert "1 keyword(s) skipped" in captured.out
