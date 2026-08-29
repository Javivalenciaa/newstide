import json

import dataforseo as dfs


# Real google_ads/search_volume/live shape: tasks[i]["result"] is a FLAT list of
# keyword-metric dicts (each has "keyword" directly) — no nested "items" wrapper.
_DEFAULT_RESPONSE = {
    "status_code": 20000,
    "tasks_error": 0,
    "tasks": [{"status_code": 20000, "result": []}],
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
    # Google Ads Search Volume matches real search phrases. A hyphen-joined
    # string is not a phrase anyone searches for and always returns 0 volume,
    # which is exactly what both pipelines saw on every run.
    assert dfs.extract_core_keyword("Best AI Tools for Solopreneurs in 2026") == (
        "best ai tools solopreneurs 2026"
    )
    assert "-" not in dfs.extract_core_keyword("How to Build a Web App with Django")


def test_extract_core_keyword_preserves_spanish_accents_and_drops_filler():
    # An ASCII-only strip turned "cómo" into "cmo" and "planificación" into
    # "planificacin" — non-words that can never match a real keyword. Spanish
    # stopwords ("los", "de", "la", "para") must not eat the 5-token budget.
    core = dfs.extract_core_keyword(
        "Cómo aprovechar los programas de asistencia alimentaria para inmigrantes"
    )
    assert core == "aprovechar programas asistencia alimentaria inmigrantes"

    accented = dfs.extract_core_keyword(
        "Los beneficios de la planificación patrimonial para hispanos"
    )
    assert "planificación" in accented
    assert "planificacin" not in accented


def test_fetch_keyword_metrics_defaults_to_english(monkeypatch):
    monkeypatch.setattr(dfs, "DATAFORSEO_LOGIN", "user")
    monkeypatch.setattr(dfs, "DATAFORSEO_PASSWORD", "pass")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    _FakeConn.response_data = _DEFAULT_RESPONSE
    dfs.fetch_keyword_metrics(["best ai tools for solopreneurs"])
    assert _FakeConn.sent_payloads[0][0]["language_code"] == "en"


def test_fetch_keyword_metrics_accepts_spanish_for_finance_pipeline(monkeypatch):
    monkeypatch.setattr(dfs, "DATAFORSEO_LOGIN", "user")
    monkeypatch.setattr(dfs, "DATAFORSEO_PASSWORD", "pass")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    _FakeConn.response_data = _DEFAULT_RESPONSE
    dfs.fetch_keyword_metrics(["como construir credito en usa"], language_code="es")
    assert _FakeConn.sent_payloads[0][0]["language_code"] == "es"


def test_fetch_keyword_metrics_drops_empty_core_keywords_from_batch(monkeypatch):
    # "a to of" is all stopwords -> extract_core_keyword() returns "". A single
    # empty keyword must never reach the API — it can poison the whole batch.
    monkeypatch.setattr(dfs, "DATAFORSEO_LOGIN", "user")
    monkeypatch.setattr(dfs, "DATAFORSEO_PASSWORD", "pass")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    _FakeConn.response_data = _DEFAULT_RESPONSE
    dfs.fetch_keyword_metrics(["a to of", "best ai tools for solopreneurs"])
    sent_keywords = _FakeConn.sent_payloads[0][0]["keywords"]
    assert "" not in sent_keywords


def test_fetch_keyword_metrics_all_empty_core_keywords_skips_api_call(monkeypatch):
    monkeypatch.setattr(dfs, "DATAFORSEO_LOGIN", "user")
    monkeypatch.setattr(dfs, "DATAFORSEO_PASSWORD", "pass")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    result = dfs.fetch_keyword_metrics(["a to of", "on in at"])
    assert result == {}
    assert _FakeConn.sent_payloads == []


def test_fetch_keyword_metrics_parses_real_flat_result_shape(monkeypatch):
    # This is the actual shape google_ads/search_volume/live returns: keyword
    # objects live DIRECTLY in tasks[i]["result"], not nested under an "items"
    # key. The old _safe_items() only checked for "items" and silently
    # returned [] for every call to this endpoint — this is the regression test.
    monkeypatch.setattr(dfs, "DATAFORSEO_LOGIN", "user")
    monkeypatch.setattr(dfs, "DATAFORSEO_PASSWORD", "pass")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    _FakeConn.response_data = {
        "status_code": 20000,
        "tasks_error": 0,
        "tasks": [{
            "status_code": 20000,
            # DataForSEO echoes back the exact keyword string that was sent —
            # extract_core_keyword() joins tokens with SPACES, because Google
            # Ads Search Volume matches real search phrases. This fixture used
            # to assert the hyphenated shape, which made the test pass against
            # a fake response while production returned 0 results forever.
            "result": [
                {"keyword": "best ai tools solopreneurs 2026", "search_volume": 720, "competition": 0.3},
            ],
        }],
    }
    result = dfs.fetch_keyword_metrics(["Best AI Tools for Solopreneurs in 2026"])
    assert result != {}
    meta = result.get("best ai tools for solopreneurs in 2026")
    assert meta is not None
    assert meta["volume"] == 720


def test_log_task_errors_reports_task_level_failure(capsys):
    data = {
        "status_code": 20000,
        "tasks_error": 1,
        "tasks": [{"status_code": 40402, "status_message": "Insufficient balance"}],
    }
    dfs._log_task_errors(data, batch_idx=0)
    captured = capsys.readouterr()
    assert "40402" in captured.out
    assert "Insufficient balance" in captured.out


def test_log_task_errors_silent_when_task_ok(capsys):
    data = {"status_code": 20000, "tasks_error": 0, "tasks": [{"status_code": 20000}]}
    dfs._log_task_errors(data, batch_idx=0)
    captured = capsys.readouterr()
    assert captured.out == ""
