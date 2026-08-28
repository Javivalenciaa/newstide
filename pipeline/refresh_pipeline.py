"""
Content refresh pipeline — re-generates stale articles (>90 days) so
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

REFRESH_PER_RUN = 1
STALE_AFTER_DAYS = 90
SERP_LOOKBACK_DAYS = 28
MIN_CONTENT_RETENTION = 0.70  # refreshed content must keep at least 70% of original word count


def _stale_cutoff() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=STALE_AFTER_DAYS)).isoformat()


def fetch_refresh_candidates(table: str, title_field: str, slug_field: str) -> list[dict]:
    try:
        res = (
            p.supabase_client.table(table)
            .select(f"id, {title_field}, {slug_field}, category, keyword, published_at")
            .lte("published_at", _stale_cutoff())
            .not_.is_(slug_field, "null")
            .order("published_at", desc=False)
            .limit(200)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"  ⚠️  Could not fetch refresh candidates from {table}: {e}")
        return []


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


def pick_refresh_candidate() -> dict | None:
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

    if not candidates:
        return None

    scores = fetch_serp_scores([c["page"] for c in candidates])

    def score(c: dict) -> float:
        s = scores.get(c["page"])
        return refresh_priority(s["impressions"], s["avg_position"]) if s else -1.0

    candidates.sort(key=score, reverse=True)
    return candidates[0]


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
    p._register_claude_call(message.usage.output_tokens if hasattr(message, "usage") else 6000)
    raw = _strip_h1(message.content[0].text)

    if p.is_truncated(raw, content_en):
        print("  ❌ Refreshed content looks truncated/shorter than original — skipping")
        return False
    if not p.validate_article_content(raw, label="refresh-raw"):
        print("  ❌ Refreshed content failed validation — skipping update")
        return False

    humanized = p.humanize(raw)
    if not p.validate_article_content(humanized, label="refresh-humanized") or p.is_truncated(humanized, raw):
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
    fp._register_claude_call(message.usage.output_tokens if hasattr(message, "usage") else 8000)
    raw = _strip_h1(message.content[0].text)

    if not fp.validate_article_content(raw, label="refresh-raw"):
        print("  ❌ Contenido refrescado inválido — saltando actualización")
        return False

    humanized = fp.humanize(raw)
    if not fp.validate_article_content(humanized, label="refresh-humanizado"):
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

    print(f"\n🔄 Refreshing [{table}] {candidate['page']}")
    try:
        if table == "articles":
            return _refresh_main_article(full)
        return _refresh_finance_article(full)
    except (p.CostLimitExceeded, fp.CostLimitExceeded) as e:
        print(f"\n{e}")
        return False
    except Exception as e:
        print(f"  ❌ Refresh failed: {e}")
        return False


def main():
    print(f"\n🔄 NewsTide Content Refresh — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🎯 Target: {REFRESH_PER_RUN} article(s), stale after {STALE_AFTER_DAYS} days")

    refreshed = 0
    for _ in range(REFRESH_PER_RUN):
        candidate = pick_refresh_candidate()
        if not candidate:
            print("  ℹ️  No stale candidates found — nothing to refresh")
            break
        if refresh_article(candidate):
            refreshed += 1

    print(f"\n🎉 Done: {refreshed}/{REFRESH_PER_RUN} article(s) refreshed")


if __name__ == "__main__":
    main()
