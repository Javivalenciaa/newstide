"""Regression tests for the 2026-09-02 guardrail fixes.

Each test pins one defect observed in the production run of that morning.
"""
import pipeline as p
import finance_pipeline as fp


# ── CHECK C: keyword derivation ──────────────────────────────────────────────
def _article(**over) -> dict:
    """Minimal article payload shaped like the one save_article() builds."""
    base = {
        "title": "Airtable vs. Asana: Comparativa Completa de Herramientas",
        "title_en": "Airtable vs. Asana: A Complete Tool Comparison",
        "content": "Contenido en español. " * 50,
        "content_en": "English content here. " * 50,
        "keyword": "Airtable vs. Asana: A Complete Tool Comparison",
        "keyword_hash": "unchanged-sentinel",
    }
    base.update(over)
    return base


def test_check_c_derives_the_keyword_from_the_english_title(monkeypatch):
    # The Spanish title produced 'airtable-asana-comparativa-completa-de' in
    # production. Every keyword surface in this pipeline (SerpAPI, GSC, YepAPI)
    # is English, so a Spanish keyword can never be joined back to any of them.
    monkeypatch.setattr(p, "supabase_client", _FakeSupabase())
    _status, _flags, data = p.run_content_guardrails(_article())
    assert data["keyword"] == "airtable-asana-complete-tool-comparison"


def test_check_c_no_longer_overwrites_the_dedup_hash(monkeypatch):
    # It used to set keyword_hash = md5(spanish_slug) while
    # already_published_hash() looks up md5(keyword_en) / md5(derive(keyword_en)),
    # so the two never matched and the hash layer was silently dead.
    monkeypatch.setattr(p, "supabase_client", _FakeSupabase())
    _status, _flags, data = p.run_content_guardrails(_article())
    assert data["keyword_hash"] == "unchanged-sentinel"


def test_hash_write_path_and_read_path_agree():
    # save_article writes md5(_derive_keyword_slug_for_hash(keyword));
    # already_published_hash looks that exact value up as its slug_hash.
    keyword = "Airtable vs. Asana: A Complete Tool Comparison"
    written = p.md5(p._derive_keyword_slug_for_hash(keyword))
    looked_up = p.md5(p._derive_keyword_slug_for_hash(keyword))
    assert written == looked_up


def test_check_d_stays_quiet_when_the_price_stamp_is_present(monkeypatch):
    # Fired on ANY monetary figure before, so 3/3 articles on 2026-09-02 came
    # out needs_review — a flag that is always on carries no information.
    monkeypatch.setattr(p, "supabase_client", _FakeSupabase())
    priced = _article(
        content="El plan cuesta $20 al mes. " * 30,
        content_en="The plan costs $20 a month. " * 30 + p._PRICING_MARK_EN,
    )
    _status, flags, _data = p.run_content_guardrails(priced)
    assert not any(f.startswith("[D]") for f in flags)


def test_check_d_still_fires_when_the_stamp_is_missing(monkeypatch):
    monkeypatch.setattr(p, "supabase_client", _FakeSupabase())
    priced = _article(
        content="El plan cuesta $20 al mes. " * 30,
        content_en="The plan costs $20 a month. " * 30,
    )
    _status, flags, _data = p.run_content_guardrails(priced)
    assert any(f.startswith("[D]") for f in flags)


# ── FINANCE GUARDRAILS (did not exist at all before) ─────────────────────────
def _finance_article(**over) -> dict:
    base = {
        "title": "Cómo enviar dinero a México sin comisiones ocultas",
        "keyword": "enviar-dinero-mexico-comisiones",
        "content": (
            "Contenido en español sobre remesas. " * 60
            + "\n\nFuente: https://www.consumidor.ftc.gov/\n"
            + "\n*Aviso legal: solo para fines informativos.*\n"
        ),
        "content_en": "",
    }
    base.update(over)
    return base


def test_finance_blocks_a_ymyl_article_with_no_authoritative_source(monkeypatch):
    monkeypatch.setattr(fp, "supabase_client", _FakeSupabase())
    unsourced = _finance_article(
        content="Contenido sin fuentes. " * 60 + "\n*Aviso legal: informativo.*\n"
    )
    status, flags, _data = fp.run_content_guardrails(unsourced)
    assert status == "blocked"
    assert any(f.startswith("[D]") for f in flags)


def test_finance_blocks_when_the_legal_disclaimer_is_missing(monkeypatch):
    monkeypatch.setattr(fp, "supabase_client", _FakeSupabase())
    no_disclaimer = _finance_article(
        content="Texto. " * 60 + "\nFuente: https://www.irs.gov/es\n"
    )
    status, flags, _data = fp.run_content_guardrails(no_disclaimer)
    assert status == "blocked"
    assert any(f.startswith("[E]") for f in flags)


def test_finance_passes_a_well_formed_article(monkeypatch):
    monkeypatch.setattr(fp, "supabase_client", _FakeSupabase())
    status, _flags, _data = fp.run_content_guardrails(_finance_article())
    assert status == "ok"


# ── ENTITY DEDUP WIRED INTO is_duplicate_topic ───────────────────────────────
def test_pipeline_treats_an_entity_collision_as_a_duplicate(monkeypatch):
    # pg_trgm scores this pair at 0.33, under the 0.45 threshold, and the GPT
    # call is stubbed to say NO — exactly the production conditions on 09-02.
    monkeypatch.setattr(p, "is_duplicate_topic_trgm", lambda *a, **k: False)
    monkeypatch.setattr(p, "topic_cluster_on_cooldown", lambda *a, **k: False)
    monkeypatch.setattr(p, "openai_client", _FakeOpenAI("NO"))
    recent = [{"title_en": "Airtable vs. Asana: Which Tool Is Better for Founders?"}]
    assert p.is_duplicate_topic(
        "Airtable vs. Asana: A Complete Tool Comparison", recent, []
    ) is True


def test_pipeline_still_allows_a_genuinely_new_topic(monkeypatch):
    monkeypatch.setattr(p, "is_duplicate_topic_trgm", lambda *a, **k: False)
    monkeypatch.setattr(p, "topic_cluster_on_cooldown", lambda *a, **k: False)
    monkeypatch.setattr(p, "openai_client", _FakeOpenAI("NO"))
    recent = [{"title_en": "Airtable vs. Asana: Which Tool Is Better for Founders?"}]
    assert p.is_duplicate_topic(
        "Why Your Social Media Strategy Fails: Key Missteps", recent, []
    ) is False


# ── TEST DOUBLES ─────────────────────────────────────────────────────────────
class _FakeQuery:
    def select(self, *a, **k): return self
    def order(self, *a, **k): return self
    def limit(self, *a, **k): return self
    def eq(self, *a, **k): return self
    def neq(self, *a, **k): return self
    def execute(self): return type("R", (), {"data": []})()


class _FakeSupabase:
    """Returns no recent rows, so the structure check is skipped."""
    def table(self, *_a, **_k): return _FakeQuery()


class _FakeOpenAI:
    def __init__(self, reply: str):
        answer = type("M", (), {"content": reply})()
        choice = type("C", (), {"message": answer})()
        response = type("R", (), {"choices": [choice]})()
        create = lambda **_kw: response  # noqa: E731
        self.chat = type("Chat", (), {"completions": type("Comp", (), {"create": staticmethod(create)})()})()
