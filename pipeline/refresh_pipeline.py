"""
Content refresh pipeline — re-generates stale articles (see STALE_AFTER_DAYS) so
time-sensitive content ("best tools 2026", etc.) doesn't decay in rankings.

Standalone script: imports and reuses helper functions from pipeline.py and
finance_pipeline.py (humanize, translate, validators, clients, budget guards)
rather than duplicating them — never modifies those files' generation logic.

Refreshes exactly REFRESH_PER_RUN articles per run, picked across BOTH tables
combined, prioritized by real serp_tracking data (position 4-20 with real
impressions = biggest reclaim-the-ranking opportunity — the same "quick win"
logic already used by fetch_gsc_queries() elsewhere in this codebase), falling
back to oldest-first when no tracking data exists yet for a candidate.

Only `content`/`content_en` are ever updated — slug, id, category, keyword,
and published_at are never touched, so URLs and datePublished never change.
`updated_at` bumps automatically via the Supabase trigger from the Fase 2 SQL.

Runs once a day via .github/workflows/content-refresh.yml.
"""
from datetime import datetime, timezone, timedelta

import pipeline as p
import finance_pipeline as fp
from claude_response import (
    ClaudeDeclined,
    extract_text as _claude_text,
    output_tokens as _claude_output_tokens,
)

# Raised from 1 on 2026-09-02, alongside cutting ARTICLES_PER_RUN from 3 to 2
# in both pipelines: with only 32 of ~784 URLs ever drawing a Search Console
# impression, improving a page that already ranks beats adding another that
# does not.
REFRESH_PER_RUN = 3

# Lowered from 90 on 2026-09-02. At 90 days exactly THREE articles in the whole
# database qualified (and zero finance articles — that vertical only started on
# 2026-07-26), so this daily workflow was re-refreshing the same three rows on
# a loop. At 60 days, 100 articles qualify. "Best tools 2026" content decays
# well inside 90 days anyway.
STALE_AFTER_DAYS = 60

# Never refresh the same article twice inside this window. There was no such
# check, and combined with the tiny candidate pool above it meant the same
# handful of articles got rewritten day after day — churn Google reads as
# instability, not freshness.
REFRESH_COOLDOWN_DAYS = 45

SERP_LOOKBACK_DAYS = 28
MIN_CONTENT_RETENTION = 0.70  # refreshed content must keep at least 70% of original word count

# An article this short is a stub, not something a refresh can improve — the
# model has nothing to work from and the result would still fail the word-count
# bar the publish pipeline enforces. The two rows that crashed the 2026-09-03
# run were 220 and 366 words; they need consolidating or removing, not
# rewriting. Skipping them here also stops them being re-picked every morning.
MIN_WORDS_TO_REFRESH = 600


def _stale_cutoff() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=STALE_AFTER_DAYS)).isoformat()


def _cooldown_cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=REFRESH_COOLDOWN_DAYS)


def _refreshed_recently(updated_at, cutoff: datetime) -> bool:
    """True when updated_at is inside the cooldown window.

    Parsed rather than string-compared: Supabase returns fractional seconds and
    may use 'Z' or '+00:00', so lexicographic comparison against our own
    isoformat() output is not reliable. An unparseable or missing value means
    "never refreshed", which must stay eligible.
    """
    if not updated_at:
        return False
    try:
        dt = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
    except Exception:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt > cutoff


def fetch_refresh_candidates(table: str, title_field: str, slug_field: str) -> list[dict]:
    try:
        res = (
            p.supabase_client.table(table)
            .select(
                f"id, {title_field}, {slug_field}, category, keyword, "
                f"published_at, updated_at, refresh_blocked_at"
            )
            .lte("published_at", _stale_cutoff())
            .not_.is_(slug_field, "null")
            .order("published_at", desc=False)
            .limit(200)
            .execute()
        )
        rows = res.data or []
    except Exception as e:
        # refresh_blocked_at is optional — retry without it so this keeps
        # working before 20260903_refresh_blocked_column.sql is applied.
        if "refresh_blocked_at" not in str(e):
            print(f"  ⚠️  Could not fetch refresh candidates from {table}: {e}")
            return []
        try:
            res = (
                p.supabase_client.table(table)
                .select(f"id, {title_field}, {slug_field}, category, keyword, published_at, updated_at")
                .lte("published_at", _stale_cutoff())
                .not_.is_(slug_field, "null")
                .order("published_at", desc=False)
                .limit(200)
                .execute()
            )
            rows = res.data or []
        except Exception as e2:
            print(f"  ⚠️  Could not fetch refresh candidates from {table}: {e2}")
            return []

    # Articles the model has already declined to refresh. Retrying the same
    # prompt gets the same decline, so without this they are re-picked every
    # single morning and burn a Claude call each time.
    blocked = [r for r in rows if r.get("refresh_blocked_at")]
    if blocked:
        print(f"  🚫 {len(blocked)} candidate(s) in {table} previously declined by the model — skipping")
        rows = [r for r in rows if not r.get("refresh_blocked_at")]

    # Drop anything refreshed inside the cooldown. Filtered here rather than in
    # the query because updated_at is NULL for every row never refreshed, and a
    # NULL comparison in PostgREST would silently exclude exactly the rows that
    # most need picking.
    cutoff = _cooldown_cutoff()
    fresh_enough = [r for r in rows if not _refreshed_recently(r.get("updated_at"), cutoff)]

    skipped = len(rows) - len(fresh_enough)
    if skipped:
        print(f"  ⏳ {skipped} candidate(s) in {table} still inside the {REFRESH_COOLDOWN_DAYS}-day refresh cooldown")
    return fresh_enough


def fetch_serp_scores(pages: list[str]) -> dict[str, dict]:
    """Aggregate serp_tracking over the last SERP_LOOKBACK_DAYS per page."""
    if not pages:
        return {}
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=SERP_LOOKBACK_DAYS)).date().isoformat()
        res = (
            p.supabase_client.table("serp_tracking")
            .select("page, impressions, position")
            .in_("page", pages)
            .gte("date", since)
            .execute()
        )
        rows = res.data or []
    except Exception as e:
        print(f"  ⚠️  Could not fetch serp_tracking scores (non-critical): {e}")
        return {}

    agg: dict[str, dict] = {}
    for row in rows:
        page = row.get("page")
        if not page:
            continue
        entry = agg.setdefault(page, {"impressions": 0, "positions": []})
        entry["impressions"] += int(row.get("impressions") or 0)
        pos = row.get("position")
        if pos:
            entry["positions"].append(float(pos))

    scores: dict[str, dict] = {}
    for page, entry in agg.items():
        positions = entry["positions"]
        avg_position = sum(positions) / len(positions) if positions else 99.0
        scores[page] = {"impressions": entry["impressions"], "avg_position": avg_position}
    return scores


def refresh_priority(impressions: int, avg_position: float) -> float:
    if 4 <= avg_position <= 20:
        return impressions * 2.0
    if avg_position < 4:
        return impressions * 0.5
    return impressions * 1.0


def pick_refresh_candidate(exclude: set | None = None) -> dict | None:
    """Highest-priority stale article not already handled in this run.

    ``exclude`` holds (table, id) pairs picked earlier in the same run. Without
    it, REFRESH_PER_RUN > 1 would re-select the top-scoring row every iteration
    — the ordering is deterministic and the row's updated_at only moves after
    a successful rewrite.
    """
    exclude = exclude or set()
    articles = fetch_refresh_candidates("articles", "title_en", "slug_en")
    finance = fetch_refresh_candidates("finance_articles", "title", "slug")

    candidates = []
    for a in articles:
        candidates.append({
            "table": "articles", "row": a,
            "page": f"https://www.newstide.news/en/article/{a['slug_en']}",
        })
    for row in finance:
        candidates.append({
            "table": "finance_articles", "row": row,
            "page": f"https://www.newstide.news/es/fin/{row['slug']}",
        })

    candidates = [c for c in candidates if (c["table"], c["row"]["id"]) not in exclude]
    if not candidates:
        return None

    scores = fetch_serp_scores([c["page"] for c in candidates])

    def score(c: dict) -> float:
        s = scores.get(c["page"])
        return refresh_priority(s["impressions"], s["avg_position"]) if s else -1.0

    candidates.sort(key=score, reverse=True)
    return candidates[0]


def _lost_too_much_content(refreshed: str, original: str) -> bool:
    """True when the rewrite dropped below MIN_CONTENT_RETENTION of the original.

    MIN_CONTENT_RETENTION was declared when this file was written but never
    referenced — the only length guard in use was p.is_truncated(), which
    allows a drop to 60% and is not applied at all on the finance path. The
    prompt says "Do NOT shorten the article", so a refresh that returns a
    materially shorter article has not done its job, and publishing it makes
    the page worse than before it was touched.
    """
    ref_words = len(original.split())
    if ref_words == 0:
        return False
    kept = len(refreshed.split()) / ref_words
    if kept < MIN_CONTENT_RETENTION:
        print(
            f"  ❌ Refresh kept only {kept*100:.0f}% of the original length "
            f"(floor is {MIN_CONTENT_RETENTION*100:.0f}%) — skipping update"
        )
        return True
    return False


def _mark_refresh_blocked(table: str, article_id, reason: str) -> None:
    """Record that the model declined this article, so it stops being picked.

    Best-effort: if the column is not there yet the run continues unchanged —
    the article simply gets retried on the next run, which is the behaviour
    before this existed.
    """
    client = p.supabase_client if table == "articles" else fp.supabase_client
    try:
        client.table(table).update({
            "refresh_blocked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "refresh_blocked_reason": reason[:300],
        }).eq("id", article_id).execute()
        print("  📌 Marked as declined — it will not be picked again")
    except Exception as e:
        print(f"  ⚠️  Could not mark article as declined (non-critical): {e}")


def _strip_h1(raw: str) -> str:
    lines = raw.strip().split("\n")
    if lines and lines[0].strip().startswith("# "):
        return "\n".join(lines[1:]).strip()
    return raw.strip()


def _refresh_main_article(article: dict) -> bool:
    title_en = article.get("title_en") or article.get("title")
    content_en = article.get("content_en") or article.get("content") or ""
    keyword = article.get("keyword") or title_en

    p._check_claude_budget(output_tokens=6000)
    prompt = f"""This article was published a while ago and needs a light refresh to stay
accurate and competitive for: "{keyword}"

CURRENT ARTICLE:
{content_en}

TASK:
- Update anything time-sensitive (year references, "currently", tool version claims).
- Keep the same structure, headings, and EEAT rules (never invent data or stats).
- Keep all existing external links unless clearly outdated; you may add ONE new one.
- Do NOT change the core angle or shorten the article.
- Preserve the H1 exactly as-is: {title_en}

Return the FULL updated article in markdown, starting with the H1."""
    message = p.claude_client.messages.create(
        model=p.MODEL_GENERATE, max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
        system=(
            "You are refreshing an existing published article. Never invent data. "
            "Preserve structure and links unless clearly stale."
        ),
    )
    p._register_claude_call(_claude_output_tokens(message, 6000))
    raw = _strip_h1(_claude_text(message, context=title_en[:60]))

    if p.is_truncated(raw, content_en):
        print("  ❌ Refreshed content looks truncated/shorter than original — skipping")
        return False
    if _lost_too_much_content(raw, content_en):
        return False
    if not p.validate_article_content(raw, label="refresh-raw"):
        print("  ❌ Refreshed content failed validation — skipping update")
        return False

    humanized = p.humanize(raw)
    if (
        not p.validate_article_content(humanized, label="refresh-humanized")
        or p.is_truncated(humanized, raw)
        or _lost_too_much_content(humanized, content_en)
    ):
        humanized = raw

    content_en_final = humanized + p.EDITORIAL_NOTE
    print("  🌐 Re-translating to Spanish...")
    content_es = p.translate_content_to_spanish(humanized)
    content_es_final = content_es + p.EDITORIAL_NOTE_ES

    try:
        p.supabase_client.table("articles").update({
            "content_en": content_en_final,
            "content": content_es_final,
        }).eq("id", article["id"]).execute()
        print(f"  ✅ Refreshed: {title_en[:60]}")
        p.ping_indexnow([f"https://www.newstide.news/en/article/{article.get('slug_en')}"])
        return True
    except Exception as e:
        print(f"  ❌ Update failed: {e}")
        return False


def _refresh_finance_article(article: dict) -> bool:
    title = article.get("title")
    content = article.get("content") or ""
    keyword = article.get("keyword") or title

    fp._check_claude_budget(output_tokens=8000)
    prompt = f"""Este artículo se publicó hace tiempo y necesita una actualización ligera para
seguir siendo preciso y competitivo sobre: "{keyword}"

ARTÍCULO ACTUAL:
{content}

TAREA:
- Actualiza cualquier referencia temporal (años, "actualmente", cifras que puedan haber cambiado).
- Mantén la misma estructura y las reglas E-E-A-T (nunca inventes datos).
- Mantén los enlaces externos existentes salvo que estén claramente obsoletos; puedes añadir UNO nuevo.
- No cambies el ángulo principal ni acortes el artículo.
- Preserva el H1 exactamente: {title}

Devuelve el ARTÍCULO COMPLETO actualizado en markdown, empezando por el H1."""
    message = fp.claude_client.messages.create(
        model=fp.MODEL_GENERATE, max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
        system=(
            "Estás actualizando un artículo ya publicado. Nunca inventes datos. "
            "Preserva estructura y enlaces salvo que estén claramente obsoletos."
        ),
    )
    fp._register_claude_call(_claude_output_tokens(message, 8000))
    raw = _strip_h1(_claude_text(message, context=title[:60]))

    if _lost_too_much_content(raw, content):
        return False
    if not fp.validate_article_content(raw, label="refresh-raw"):
        print("  ❌ Contenido refrescado inválido — saltando actualización")
        return False

    humanized = fp.humanize(raw)
    if (
        not fp.validate_article_content(humanized, label="refresh-humanizado")
        or _lost_too_much_content(humanized, content)
    ):
        humanized = raw

    content_final = fp.fix_double_quotes(humanized) + fp.EDITORIAL_NOTE_ES + fp.FINANCE_DISCLAIMER_ES

    try:
        fp.supabase_client.table("finance_articles").update({
            "content": content_final,
        }).eq("id", article["id"]).execute()
        print(f"  ✅ Refrescado: {title[:60]}")
        fp.ping_indexnow([f"https://www.newstide.news/es/fin/{article.get('slug')}"])
        return True
    except Exception as e:
        print(f"  ❌ Error actualizando: {e}")
        return False


def refresh_article(candidate: dict) -> bool:
    table = candidate["table"]
    client = p.supabase_client if table == "articles" else fp.supabase_client
    try:
        res = client.table(table).select("*").eq("id", candidate["row"]["id"]).single().execute()
        full = res.data
    except Exception as e:
        print(f"  ⚠️  Could not load full row: {e}")
        return False
    if not full:
        return False

    # A stub cannot be meaningfully refreshed — see MIN_WORDS_TO_REFRESH.
    body = full.get("content_en") or full.get("content") or ""
    words = len(body.split())
    if words < MIN_WORDS_TO_REFRESH:
        print(
            f"\n⏭️  Skipping [{table}] {candidate['page']} — "
            f"only {words} words, too thin to refresh"
        )
        return False

    print(f"\n🔄 Refreshing [{table}] {candidate['page']}")
    try:
        if table == "articles":
            return _refresh_main_article(full)
        return _refresh_finance_article(full)
    except (p.CostLimitExceeded, fp.CostLimitExceeded) as e:
        print(f"\n{e}")
        return False
    except ClaudeDeclined as e:
        # HTTP 200, empty content, stop_reason="refusal". This used to surface
        # as "list index out of range" from content[0], and because nothing
        # recorded it the same article was re-picked every single morning.
        print(f"  🚫 {e}")
        _mark_refresh_blocked(table, full.get("id"), str(e))
        return False
    except Exception as e:
        print(f"  ❌ Refresh failed: {e}")
        return False


def main():
    print(f"\n🔄 NewsTide Content Refresh — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🎯 Target: {REFRESH_PER_RUN} article(s), stale after {STALE_AFTER_DAYS} days")

    refreshed = 0
    seen: set = set()
    for _ in range(REFRESH_PER_RUN):
        candidate = pick_refresh_candidate(exclude=seen)
        if not candidate:
            print("  ℹ️  No stale candidates found — nothing to refresh")
            break
        # Recorded whether or not the rewrite succeeds: a candidate that just
        # failed would otherwise be re-picked immediately and fail again.
        seen.add((candidate["table"], candidate["row"]["id"]))
        if refresh_article(candidate):
            refreshed += 1

    print(f"\n🎉 Done: {refreshed}/{REFRESH_PER_RUN} article(s) refreshed")


if __name__ == "__main__":
    main()
