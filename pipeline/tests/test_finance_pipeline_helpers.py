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


# ── E-E-A-T / YMYL: fuentes autorizadas ──────────────────────────────────────

def test_has_authoritative_source_rejects_a_random_blog():
    # has_external_link() accepted this; on YMYL a blog is not a source, and
    # treating it as one is the weak signal Google's guidelines penalise.
    assert fp.has_external_link("Ver [esto](https://algunblog.com/post)") is True
    assert fp.has_authoritative_source("Ver [esto](https://algunblog.com/post)") is False


def test_has_authoritative_source_accepts_official_us_sources():
    assert fp.has_authoritative_source("Según el [IRS](https://www.irs.gov/es) ...")
    assert fp.has_authoritative_source("[CFPB](https://www.consumerfinance.gov/es/)")
    assert fp.has_authoritative_source("[SSA](https://www.ssa.gov/es/)")


def test_has_authoritative_source_is_not_fooled_by_lookalike_domains():
    # Substring matching would accept these; host matching must not.
    assert fp.has_authoritative_source("https://irs.gov.fake-site.com/x") is False
    assert fp.has_authoritative_source("https://notirs.gov/x") is False
    # A real subdomain of an authoritative domain still counts.
    assert fp.has_authoritative_source("https://apps.irs.gov/x") is True


def test_ensure_authoritative_sources_leaves_a_sourced_article_untouched():
    content = "# Guia\n\nSegun el [IRS](https://www.irs.gov/es) el limite es X."
    assert fp.ensure_authoritative_sources(content, "Impuestos") == content


def test_ensure_authoritative_sources_appends_category_specific_sources():
    content = "# Roth IRA\n\nCuerpo del articulo sin ninguna fuente externa."
    out = fp.ensure_authoritative_sources(content, "Inversión")
    assert "## Fuentes oficiales" in out
    assert "investor.gov" in out
    assert fp.has_authoritative_source(out) is True
    # No inventa afirmaciones: el cuerpo original sigue intacto.
    assert content.strip() in out


def test_every_injected_source_url_is_on_the_authoritative_allowlist():
    # Guard against adding an injected source whose domain the validator
    # would not even recognise as authoritative.
    groups = list(fp.OFFICIAL_SOURCES_BY_CATEGORY.values()) + [fp._DEFAULT_SOURCES]
    for group in groups:
        for _name, url in group:
            assert fp.has_authoritative_source(f"[x]({url})"), url


def test_every_finance_category_has_official_sources():
    # detect_category() can only ever return these; each must map to sources.
    for category in set(fp.FIN_CATEGORIES.values()):
        assert category in fp.OFFICIAL_SOURCES_BY_CATEGORY, category


# ── PUNTO 3: densidad de secciones ───────────────────────────────────────────

def _article(words: int, sections: int) -> str:
    body = " ".join(["palabra"] * (words - sections * 3))
    heads = "".join(f"\n\n## Seccion {i}\n\n" for i in range(sections))
    return "# Titulo\n\n" + heads + body


def test_validator_fails_a_wall_of_text():
    # 4000 words under 5 headings = 800/section. The absolute MIN_H2_SECTIONS
    # floor accepted this; density must not.
    assert fp.validate_article_content(_article(4000, 5), "test") is False


def test_validator_accepts_well_sectioned_long_form():
    # 4000 words across 20 headings = 200/section, the readable range.
    assert fp.validate_article_content(_article(4000, 20), "test") is True


def test_validator_still_enforces_the_absolute_minimums():
    assert fp.validate_article_content(_article(500, 10), "test") is False   # too short
    assert fp.validate_article_content(_article(3000, 2), "test") is False   # too few sections


# ── PUNTO 4: frescura de precios ─────────────────────────────────────────────

def test_pricing_stamp_added_only_when_amounts_are_present():
    assert fp._PRICING_MARK_ES in fp.annotate_pricing_freshness("La comisión es de $5.")
    sin_precio = "Este texto no menciona ningún importe."
    assert fp.annotate_pricing_freshness(sin_precio) == sin_precio


def test_pricing_stamp_detects_apy_without_a_dollar_sign():
    # The finance vertical quotes rates as often as dollar amounts.
    assert fp._PRICING_MARK_ES in fp.annotate_pricing_freshness("Ofrece 4.5% APY.")


def test_pricing_stamp_is_idempotent_so_refreshes_never_stack_it():
    once = fp.annotate_pricing_freshness("Cuesta $29 al mes.")
    assert fp.annotate_pricing_freshness(once) == once
    assert once.count(fp._PRICING_MARK_ES) == 1


# ── PUNTO 1: los duplicados se saltan, no se mutan ───────────────────────────

def test_duplicate_topic_is_skipped_instead_of_mutated(monkeypatch):
    # Mutating a covered topic manufactures cannibalisation: six live articles
    # now chase the "enviar dinero a México / Wise / Remitly" cluster.
    monkeypatch.setattr(fp, "is_duplicate_topic", lambda *a, **k: True)
    called = []
    monkeypatch.setattr(fp, "mutate_topic", lambda *a, **k: called.append(1) or "mutado")

    assert fp.process_topic("Wise vs Remitly", [], [], 0, allow_mutation=False) is None
    assert called == [], "no debe mutar cuando el pool aún tiene candidatos"


def test_mutation_is_still_available_once_the_pool_is_exhausted(monkeypatch):
    monkeypatch.setattr(fp, "is_duplicate_topic", lambda *a, **k: True)
    called = []
    monkeypatch.setattr(fp, "mutate_topic", lambda *a, **k: (called.append(1), "mutado")[1])

    fp.process_topic("Wise vs Remitly", [], [], 0, allow_mutation=True)
    assert called, "con el pool agotado la mutación sigue siendo el último recurso"


def test_mutation_angles_are_search_intent_not_clickbait():
    # Asserted against the angle list itself, not the module source, so the
    # explanatory comment above it cannot make this pass or fail.
    joined = " ".join(fp.MUTATION_ANGLES).lower()
    for banned in ("error mas comun", "error más común", "lo que nadie te cuenta"):
        assert banned not in joined, banned
    # Every angle should point at something a person would actually search for.
    assert any("requisitos" in a or "cuánto cuesta" in a for a in fp.MUTATION_ANGLES)
