// Deterministic topic-cluster key, computed on read — no DB column needed.
// Mirrors pipeline.py's topic_cluster_key() exactly (same stopwords, same slug
// logic) so an article clusters identically whether grouped in Python or here.
const CLUSTER_STOP = new Set([
  '2026', '2025', 'guide', 'guides', 'best', 'how', 'to', 'vs', 'and', 'for',
  'with', 'your', 'the', 'of', 'in', 'on', 'solo', 'solopreneur',
  'solopreneurs', 'indie', 'hacker', 'hackers', 'founder', 'founders',
])

export const MIN_CLUSTER_SIZE = 3

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
}

export function topicClusterKey(title: string): string {
  const tokens = slugify(title)
    .split('-')
    .filter((t) => t.length > 2 && !CLUSTER_STOP.has(t))
  return tokens.slice(0, 5).join('-')
}

export interface ClusterableArticle {
  title_en?: string | null
  title?: string | null
  slug_en?: string | null
  slug?: string | null
  category?: string | null
  excerpt_en?: string | null
  excerpt?: string | null
  published_at: string
}

export function groupByCluster<T extends ClusterableArticle>(
  articles: T[],
  getTitle: (a: T) => string
): Map<string, T[]> {
  const groups = new Map<string, T[]>()
  for (const article of articles) {
    const key = topicClusterKey(getTitle(article))
    if (!key) continue
    const bucket = groups.get(key) || []
    bucket.push(article)
    groups.set(key, bucket)
  }
  return groups
}

// Human-friendly label from a cluster key: "cursor-copilot-review" -> "Cursor Copilot Review"
export function clusterLabel(key: string): string {
  return key
    .split('-')
    .map((w) => (w.length > 0 ? w[0].toUpperCase() + w.slice(1) : w))
    .join(' ')
}
