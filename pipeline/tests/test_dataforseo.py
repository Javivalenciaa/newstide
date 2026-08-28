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
