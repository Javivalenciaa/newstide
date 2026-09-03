"""Tests for the shared entity/keyword guard.

The cases marked "real" are taken verbatim from production: they are the exact
titles that got through pg_trgm + GPT-4o-mini and cannibalised each other.
"""
import seo_guard as g


# ── ACCENT-SAFE SLUG DERIVATION ──────────────────────────────────────────────
def test_strip_accents_folds_rather_than_deletes():
    # The old code deleted the accented letter itself, turning
    # "comparación" into "comparacin" and "qué" into "qu".
    assert g.strip_accents("comparación") == "comparacion"
    assert g.strip_accents("qué") == "que"
    assert g.strip_accents("niño") == "nino"


def test_derive_keyword_slug_keeps_accented_words_whole():
    # real: this Spanish title produced 'por-qu-falla-tu-estrategia' on 09-02
    slug = g.derive_keyword_slug("Por qué falla tu estrategia en redes sociales: errores clave")
    assert "qu-" not in slug
    assert "que" not in slug.split("-")  # 'qué' is a stopword once folded
    assert slug == "falla-estrategia-redes-sociales-errores"


def test_derive_keyword_slug_never_ends_on_a_preposition():
    # real: produced 'airtable-asana-comparativa-completa-de' on 09-02
    slug = g.derive_keyword_slug("Airtable vs. Asana: Comparativa Completa de Herramientas")
    assert not slug.endswith("-de")
    assert slug == "airtable-asana-comparativa-completa-herramientas"


def test_derive_keyword_slug_handles_english_titles():
    assert g.derive_keyword_slug("Why Your Social Media Strategy Fails: Key Missteps") == \
        "social-media-strategy-fails-key"


def test_derive_keyword_slug_survives_an_all_stopword_title():
    assert g.derive_keyword_slug("The And Or But") != ""


# ── ENTITY EXTRACTION ────────────────────────────────────────────────────────
def test_extract_entities_finds_a_comparison_pair():
    assert g.extract_entities("Airtable vs. Asana: A Complete Tool Comparison") == \
        frozenset({"airtable", "asana"})


def test_extract_entities_keeps_alphanumeric_brand_names_intact():
    ents = g.extract_entities("n8n vs Zapier vs Make: solo automation compared")
    assert ents == frozenset({"n8n", "zapier", "make"})


def test_extract_entities_resolves_multiword_brands():
    assert "googlesheets" in g.extract_entities("Airtable vs. Google Sheets: Which Saves Time?")
    assert "bankofamerica" in g.extract_entities("Chime vs Bank of America: cual es mejor")


def test_extract_entities_ignores_titles_with_no_products():
    assert g.extract_entities("Why Your Social Media Strategy Fails: Key Missteps") == frozenset()


def test_ambiguous_brand_alone_in_prose_is_not_an_entity():
    # "make" here is the verb, not the automation tool, and no other brand or
    # comparison marker is present to disambiguate it.
    assert "make" not in g.extract_entities("How to make time for deep work as a solo founder")


# ── COLLISION RULE ───────────────────────────────────────────────────────────
def test_collision_catches_the_september_2_airtable_asana_duplicate():
    # real: similarity() between these two is 0.33, under the 0.45 pg_trgm
    # threshold, so this pair published 11 days apart.
    assert g.entity_collision(
        "Airtable vs. Asana: A Complete Tool Comparison",
        ["Airtable vs. Asana: Which Tool Is Better for Founders?"],
    ) is not None


def test_collision_catches_a_partial_overlap_of_a_triple_comparison():
    # real: n8n/Zapier/Make published 09-02 over Zapier/Make from 08-15
    assert g.entity_collision(
        "n8n vs Zapier vs Make: solo automation compared",
        ["Zapier vs. Make: Which Automation Tool Wins for Founders?"],
    ) is not None


def test_one_shared_product_is_not_a_collision():
    # "Airtable vs Notion" and "Airtable vs Asana" are legitimately different
    # pages targeting different queries — the rule must not merge them.
    assert g.entity_collision(
        "Airtable vs. Notion: Which Tool Is Best for Solo Projects?",
        ["Airtable vs. Asana: Which Tool Is Better for Founders?"],
    ) is None


def test_entity_free_candidate_never_collides():
    assert g.entity_collision(
        "Why Your Social Media Strategy Fails: Key Missteps",
        ["Why Your Email Campaigns Convert at 1%: The Truth"],
    ) is None


def test_collision_tolerates_empty_and_none_titles():
    assert g.entity_collision("Airtable vs Asana", ["", None]) is None


def test_entity_signature_is_order_independent():
    assert g.entity_signature("Airtable vs Asana") == g.entity_signature("Asana vs Airtable")


# ── FORMAT DIVERSITY ─────────────────────────────────────────────────────────
def test_classify_format_buckets_the_real_title_shapes():
    assert g.classify_format("Airtable vs. Asana: A Complete Tool Comparison") == g.FORMAT_COMPARISON
    assert g.classify_format("Best SEO Tools for Indie Hackers in 2026") == g.FORMAT_LISTICLE
    assert g.classify_format("How to Build a Web App with Django in 7 Steps") == g.FORMAT_HOWTO
    assert g.classify_format("Why Your Social Media Strategy Fails") == g.FORMAT_OTHER


def test_classify_format_handles_spanish_titles():
    assert g.classify_format("Cómo enviar dinero a México paso a paso") == g.FORMAT_HOWTO
    assert g.classify_format("Los mejores bancos para hispanos en USA") == g.FORMAT_LISTICLE
    assert g.classify_format("Chime vs Bank of America: cuál conviene") == g.FORMAT_COMPARISON


def test_saturated_format_is_pushed_behind_the_others():
    # Recent window is 100% comparisons — well over the 40% cap.
    recent = ["Airtable vs Asana", "Zapier vs Make", "Vercel vs Netlify"]
    pool = [
        "Notion vs Coda: which ships faster",          # comparison, saturated
        "How to launch a SaaS in 30 days",             # howto, unseen
    ]
    assert g.format_diversity_reorder(pool, recent)[0] == "How to launch a SaaS in 30 days"


def test_reorder_never_drops_or_duplicates_candidates():
    recent = ["Airtable vs Asana"] * 10
    pool = ["A vs B", "How to X", "Best Y tools", "Something else"]
    out = g.format_diversity_reorder(pool, recent)
    assert sorted(out) == sorted(pool)


def test_reorder_is_a_noop_when_nothing_is_saturated():
    # Four formats evenly split — each at 25%, under the 40% cap.
    recent = ["A vs B", "How to X", "Best Y tools", "Something else"]
    pool = ["C vs D", "How to Z"]
    assert g.format_diversity_reorder(pool, recent) == pool


def test_reorder_is_a_noop_with_no_history():
    pool = ["C vs D", "How to Z"]
    assert g.format_diversity_reorder(pool, []) == pool
