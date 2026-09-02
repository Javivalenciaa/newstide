/**
 * Normalise the persisted `related_articles` column into plain objects.
 *
 * The column was specified as jsonb but landed in Supabase as `text[]` (both
 * tables — verified in information_schema). supabase-py therefore serialises
 * each dict from compute_related_articles() into a JSON *string*, so a row
 * comes back as:
 *
 *   ['{"title":"...","slug":"...","category":"..."}', '{...}', ...]
 *
 * Every consumer instead did `article.related_articles.filter(r => r?.slug_en)`
 * on the assumption that the elements were objects. On a string that property
 * is undefined, so the filter emptied the array on all four article routes and
 * the persisted sidebar silently fell back to a live category query on every
 * request — the column had no effect anywhere.
 *
 * Parsing here rather than changing the column type keeps to the project rule
 * that Supabase migrations only ever ADD columns, and it accepts both shapes,
 * so nothing breaks if the column is ever moved to jsonb.
 */

export type RelatedRecord = {
  title?: string
  title_en?: string
  slug?: string
  slug_en?: string
  category?: string
}

/**
 * Accepts the raw column value in any of its shapes and returns the records it
 * holds. Unparseable entries are dropped rather than thrown — a malformed row
 * should cost one sidebar link, never the whole page render.
 */
export function parseRelatedArticles(raw: unknown): RelatedRecord[] {
  if (!Array.isArray(raw)) return []

  const out: RelatedRecord[] = []
  for (const entry of raw) {
    if (entry && typeof entry === 'object') {
      out.push(entry as RelatedRecord)
      continue
    }
    if (typeof entry === 'string') {
      try {
        const parsed = JSON.parse(entry)
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
          out.push(parsed as RelatedRecord)
        }
      } catch {
        // Not JSON — skip this entry.
      }
    }
  }
  return out
}
