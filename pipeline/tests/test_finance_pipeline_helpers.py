from datetime import datetime, timedelta, timezone

import finance_pipeline as fp
import dataforseo as dfs


def test_smart_trim_cuts_at_word_boundary():
    assert fp.smart_trim("hello world foo bar", 12) == "hello world"


def test_normalize_excerpt_strips_leading_asterisks_and_caps_length():
    out = fp.normalize_excerpt("* " + ("word " * 40).strip(), 120, 155)
    assert not out.startswith("*")
    assert len(out) <= 156


def test_slugify_strips_spanish_accents_and_caps_at_75():
    slug = fp.slugify("Cómo Invertir en el Mercado sin Experiencia Previa " * 3)
    assert "ó" not in slug and "í" not in slug
    assert len(slug) <= 75
    assert slug == slug.strip("-")


def test_fix_double_quotes_collapses_doubled_quotes():
    assert fp.fix_double_quotes('He said ""hello"" to me') == 'He said "hello" to me'


def test_detect_category_matches_known_keyword():
    assert fp.detect_category("cómo subir el credit score") == "Crédito"
    assert fp.detect_category("declarar taxes con ITIN") == "Impuestos"


def test_detect_category_falls_back_to_default():
    assert fp.detect_category("tema totalmente no relacionado") == "Ahorro"


def test_reading_time_has_a_floor():
    assert fp.reading_time("palabra " * 10) == fp.MIN_READING_TIME


def test_has_external_link_ignores_own_domain():
    assert fp.has_external_link("Ver https://irs.gov/itin para más info") is True
    assert fp.has_external_link("Ver https://newstide.news/es/fin/x") is False


def test_clean_serp_candidate_strips_source_prefix_and_snippet_suffix():
    raw = "[Reuters] Cómo abrir cuenta bancaria sin documentos — según un reporte de 2026"
    cleaned = fp.clean_serp_candidate(raw)
    assert not cleaned.startswith("[Reuters]")
    assert "según un reporte" not in cleaned


def test_topic_cluster_key_ignores_stopwords_and_year():
    key_a = fp.topic_cluster_key("Cómo construir crédito en USA sin historial 2026")
    key_b = fp.topic_cluster_key("Cómo construir crédito en USA sin historial 2025")
    assert key_a == key_b  # year is a stopword, shouldn't split the cluster


def test_topic_cluster_on_cooldown_true_within_window():
    recent = [{
        "title": "Cómo construir crédito en USA sin historial",
        "published_at": datetime.now(timezone.utc).isoformat(),
    }]
    assert fp.topic_cluster_on_cooldown(
        "Cómo construir crédito en USA sin historial", recent, []
    ) is True


def test_topic_cluster_on_cooldown_false_after_window_expires():
    old_date = (datetime.now(timezone.utc) - timedelta(days=fp.TOPIC_CLUSTER_COOLDOWN_DAYS + 5)).isoformat()
    recent = [{"title": "Cómo construir crédito en USA sin historial", "published_at": old_date}]
    assert fp.topic_cluster_on_cooldown(
        "Cómo construir crédito en USA sin historial", recent, []
    ) is False


def test_cluster_aware_reorder_boosts_building_depth_clusters():
    recent = [
        {"title": "Cómo subir el credit score en USA", "keyword": ""},
        {"title": "Cómo subir el credit score en USA", "keyword": ""},
        {"title": "Cómo subir el credit score en USA", "keyword": ""},
    ]
    pool = ["Roth IRA explicado para hispanos", "Cómo subir el credit score en USA"]
    reordered = fp.cluster_aware_reorder(pool, recent)
    assert reordered[0] == "Cómo subir el credit score en USA"


def test_is_duplicate_topic_trgm_true_when_rpc_returns_matches(monkeypatch):
    class _Resp:
        data = [{"title": "Cómo subir el credit score en USA", "slug": "subir-credit-score", "similarity": 0.6}]

    class _FakeRpc:
        def execute(self): return _Resp()

    monkeypatch.setattr(fp.supabase_client, "rpc", lambda name, params: _FakeRpc())
    assert fp.is_duplicate_topic_trgm("Cómo subir el credit score rápido en USA") is True


def test_is_duplicate_topic_trgm_fails_closed_on_rpc_error(monkeypatch):
    def _raise(name, params):
        raise RuntimeError("network down")
    monkeypatch.setattr(fp.supabase_client, "rpc", _raise)
    assert fp.is_duplicate_topic_trgm("Cualquier cosa") is False


def test_fetch_gsc_queries_returns_empty_without_credentials(monkeypatch):
    # GSC_SERVICE_ACCOUNT_JSON is read once into a module-level constant at import
    # time (unlike pipeline.py, which re-reads os.environ per call) — patch that.
    monkeypatch.delenv("GOOGLE_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(fp, "GSC_SERVICE_ACCOUNT_JSON", "")
    assert fp.fetch_gsc_queries() == []


def test_dataforseo_fetch_keyword_metrics_returns_empty_without_credentials(monkeypatch):
    monkeypatch.setattr(dfs, "YEPAPI_API_KEY", "")
    assert dfs.fetch_keyword_metrics(["como construir credito en usa"]) == {}


def test_topic_cluster_on_cooldown_false_for_unrelated_topic():
    recent = [{
        "title": "Cómo construir crédito en USA sin historial",
        "published_at": datetime.now(timezone.utc).isoformat(),
    }]
    assert fp.topic_cluster_on_cooldown("Roth IRA explicado para hispanos", recent, []) is False
