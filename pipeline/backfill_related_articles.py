"""
One-off backfill for the persisted `related_articles` sidebar.

Why
---
compute_related_articles() only runs at publish time, so only articles written
after the column shipped ever got one: 12 of 281 rows in `articles`. The other
269 fall back to a live "same category, most recent" query, which produces a
much weaker internal link graph — no title-overlap scoring, no cross-category
relevance — on the overwhelming majority of the site.

Internal links are one of the few ranking levers fully under our control, and
with only 32 of ~784 URLs ever drawing a Search Console impression, spreading
link equity across the archive matters more than adding pages to it.

Safety
------
* Only ever writes the `related_articles` column. Never touches slug, id,
  content, published_at or updated_at.
* Skips rows that already have one, unless --force is passed.
* --dry-run prints what it would write and changes nothing.
* --limit N caps the batch, so this can be run in chunks.
* Every Supabase call is wrapped: one bad row is skipped, never fatal.

Usage
-----
    python pipeline/backfill_related_articles.py --dry-run
    python pipeline/backfill_related_articles.py --limit 50
    python pipeline/backfill_related_articles.py            # everything missing

Needs the same env vars as the pipelines (SUPABASE_URL, SUPABASE_SERVICE_KEY
and the API keys the imports pull in).
"""
import argparse
import sys

import pipeline as p
import finance_pipeline as fp


def _needs_backfill(row: dict, force: bool) -> bool:
    if force:
        return True
    existing = row.get("related_articles")
    return not existing or len(existing) == 0


def backfill_articles(dry_run: bool, limit: int | None, force: bool) -> int:
    """Backfill the solopreneur/indie-hacker table."""
    try:
        res = (
            p.supabase_client.table("articles")
            .select("id, title, title_en, slug, slug_en, category, related_articles")
            .not_.is_("slug_en", "null")
            .order("published_at", desc=True)
            .limit(1000)
            .execute()
        )
        rows = res.data or []
    except Exception as e:
        print(f"❌ Could not read articles: {e}")
        return 0

    targets = [r for r in rows if _needs_backfill(r, force)]
    if limit:
        targets = targets[:limit]
    print(f"📚 articles: {len(rows)} total, {len(targets)} to backfill")

    written = 0
    for row in targets:
        title = row.get("title_en") or row.get("title") or ""
        related = p.compute_related_articles(
            row.get("category") or "", row.get("slug_en") or "", title
        )
        if not related:
            print(f"  ⏭️  no related found for: {title[:55]}")
            continue
        if dry_run:
            names = ", ".join((r.get("title_en") or r.get("title") or "?")[:28] for r in related[:3])
            print(f"  [dry-run] {title[:45]} -> {names}")
            written += 1
            continue
        try:
            p.supabase_client.table("articles").update(
                {"related_articles": related}
            ).eq("id", row["id"]).execute()
            written += 1
            print(f"  ✅ {title[:55]} ({len(related)} links)")
        except Exception as e:
            print(f"  ⚠️  update failed for id={row.get('id')}: {e}")
    return written


def backfill_finance(dry_run: bool, limit: int | None, force: bool) -> int:
    """Backfill the personal-finance table."""
    try:
        res = (
            fp.supabase_client.table("finance_articles")
            .select("id, title, title_en, slug, slug_en, category, related_articles")
            .not_.is_("slug", "null")
            .order("published_at", desc=True)
            .limit(1000)
            .execute()
        )
        rows = res.data or []
    except Exception as e:
        print(f"❌ Could not read finance_articles: {e}")
        return 0

    targets = [r for r in rows if _needs_backfill(r, force)]
    if limit:
        targets = targets[:limit]
    print(f"💰 finance_articles: {len(rows)} total, {len(targets)} to backfill")

    written = 0
    for row in targets:
        title = row.get("title") or ""
        related = fp.compute_related_articles(
            row.get("category") or "", row.get("slug") or "", title
        )
        if not related:
            print(f"  ⏭️  sin relacionados para: {title[:55]}")
            continue
        if dry_run:
            names = ", ".join((r.get("title") or "?")[:28] for r in related[:3])
            print(f"  [dry-run] {title[:45]} -> {names}")
            written += 1
            continue
        try:
            fp.supabase_client.table("finance_articles").update(
                {"related_articles": related}
            ).eq("id", row["id"]).execute()
            written += 1
            print(f"  ✅ {title[:55]} ({len(related)} enlaces)")
        except Exception as e:
            print(f"  ⚠️  update failed for id={row.get('id')}: {e}")
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="print, do not write")
    ap.add_argument("--limit", type=int, default=None, help="cap rows per table")
    ap.add_argument("--force", action="store_true", help="rewrite rows that already have links")
    ap.add_argument("--table", choices=("all", "articles", "finance"), default="all")
    args = ap.parse_args()

    if args.dry_run:
        print("🧪 DRY RUN — nothing will be written\n")

    total = 0
    if args.table in ("all", "articles"):
        total += backfill_articles(args.dry_run, args.limit, args.force)
    if args.table in ("all", "finance"):
        total += backfill_finance(args.dry_run, args.limit, args.force)

    print(f"\n🎉 {'Would backfill' if args.dry_run else 'Backfilled'} {total} article(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
