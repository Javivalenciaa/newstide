from datetime import datetime, timezone

import pipeline as p
import finance_pipeline as fp


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    """Chained query builder stub that just returns itself and a fixed result."""

    def __init__(self, rows):
        self._rows = rows

    def select(self, *a, **k): return self

    @property
    def not_(self): return self  # real postgrest-py exposes `.not_` as a property, not a method

    def is_(self, *a, **k): return self
    def neq(self, *a, **k): return self
    def eq(self, *a, **k): return self
    def order(self, *a, **k): return self
    def limit(self, *a, **k): return self
    def execute(self): return _FakeResult(self._rows)


class _FakeTable:
    def __init__(self, rows): self._rows = rows
    def table(self, name): return _FakeQuery(self._rows)


NOW = datetime.now(timezone.utc).isoformat()


def test_compute_related_articles_prefers_matching_category(monkeypatch):
    rows = [
        {"title": "Cursor vs Copilot", "title_en": "Cursor vs Copilot",
         "slug": "cursor-vs-copilot", "slug_en": "cursor-vs-copilot",
         "category": "AI Tools", "published_at": NOW},
        {"title": "How to price your SaaS", "title_en": "How to price your SaaS",
         "slug": "price-saas", "slug_en": "price-saas",
         "category": "Monetization", "published_at": NOW},
    ]
    monkeypatch.setattr(p, "supabase_client", _FakeTable(rows))
    related = p.compute_related_articles("AI Tools", "current-slug", "Best AI Tools 2026")
    assert related[0]["category"] == "AI Tools"
    assert related[0]["slug_en"] == "cursor-vs-copilot"


def test_compute_related_articles_empty_when_fetch_fails(monkeypatch):
    class _Boom:
        def table(self, name): raise RuntimeError("network down")
    monkeypatch.setattr(p, "supabase_client", _Boom())
    assert p.compute_related_articles("AI Tools", "slug", "Title") == []


def test_finance_compute_related_articles_prefers_matching_category(monkeypatch):
    rows = [
        {"title": "Cómo subir el credit score", "title_en": None,
         "slug": "subir-credit-score", "slug_en": None,
         "category": "Crédito", "published_at": NOW},
        {"title": "Roth IRA explicado", "title_en": None,
         "slug": "roth-ira", "slug_en": None,
         "category": "Inversión", "published_at": NOW},
    ]
    monkeypatch.setattr(fp, "supabase_client", _FakeTable(rows))
    related = fp.compute_related_articles("Crédito", "current-slug", "Cómo construir crédito en USA")
    assert related[0]["category"] == "Crédito"
