import json

import dataforseo as dfs


class _FakeResponse:
    def read(self):
        return json.dumps({"status_code": 20000, "tasks": [{"result": [{"items": []}]}]}).encode()


class _FakeConn:
    sent_payloads = []

    def __init__(self, *a, **k): pass
    def request(self, method, path, payload, headers):
        _FakeConn.sent_payloads.append(json.loads(payload))
    def getresponse(self): return _FakeResponse()
    def close(self): pass


def test_fetch_keyword_metrics_defaults_to_english(monkeypatch):
    monkeypatch.setattr(dfs, "DATAFORSEO_LOGIN", "user")
    monkeypatch.setattr(dfs, "DATAFORSEO_PASSWORD", "pass")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    dfs.fetch_keyword_metrics(["best ai tools for solopreneurs"])
    assert _FakeConn.sent_payloads[0][0]["language_code"] == "en"


def test_fetch_keyword_metrics_accepts_spanish_for_finance_pipeline(monkeypatch):
    monkeypatch.setattr(dfs, "DATAFORSEO_LOGIN", "user")
    monkeypatch.setattr(dfs, "DATAFORSEO_PASSWORD", "pass")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
    dfs.fetch_keyword_metrics(["como construir credito en usa"], language_code="es")
    assert _FakeConn.sent_payloads[0][0]["language_code"] == "es"


def test_fetch_keyword_metrics_drops_empty_core_keywords_from_batch(monkeypatch):
    # "a to of" is all stopwords -> extract_core_keyword() returns "". A single
    # empty keyword must never reach the API — it can poison the whole batch.
    monkeypatch.setattr(dfs, "DATAFORSEO_LOGIN", "user")
    monkeypatch.setattr(dfs, "DATAFORSEO_PASSWORD", "pass")
    monkeypatch.setattr(dfs.http.client, "HTTPSConnection", _FakeConn)
    _FakeConn.sent_payloads.clear()
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
