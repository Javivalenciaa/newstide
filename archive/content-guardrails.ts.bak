/**
 * content-guardrails.ts
 * Pre-publish content validation for NewsTide articles.
 * Guards against Google June 2026 spam update penalties:
 *   - Scaled content abuse
 *   - Unverified first-person experience claims
 *   - Duplicate ES/EN content on separate URLs
 *   - Stale pricing data
 *   - Repetitive section structure (template spam signal)
 *
 * Usage (in pipeline before Supabase insert):
 *   import { validateArticle } from './content-guardrails'
 *   const result = await validateArticle(articleData, supabaseClient)
 *   if (result.status === 'blocked') throw new Error(result.flags.join('; '))
 *   if (result.status === 'needs_review') articleData.needs_review = true
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js'

// ── TYPES ─────────────────────────────────────────────────────────────────────

export interface ArticleInput {
  title: string
  title_en?: string
  content: string
  content_en?: string
  slug: string
  slug_en?: string
  keyword: string
  source_url?: string
  published_at?: string
  first_party_verified?: boolean
  pricing_verified_at?: string
  // injected by guardrails when needed
  needs_review?: boolean
}

export type GuardrailStatus = 'ok' | 'blocked' | 'needs_review'

export interface GuardrailResult {
  status: GuardrailStatus
  flags: string[]
  /** Mutated copy of the input with guardrail fields applied */
  article: ArticleInput
}

// ── CONSTANTS ─────────────────────────────────────────────────────────────────

/** Phrases that signal unverified first-party experience. */
const FIRST_PERSON_RE =
  /\b(i've|i have|i'm|i am|we've|we have|our team|after \d+ years?|in my \d+ years?|from my experience|my experience|i tested|i tried|i built|i launched|i earned|i made \$)\b/gi

/** Price patterns that require a verified_at timestamp. */
const PRICING_RE = /\$\d+|\d+\s?(usd|eur|€)/gi

/**
 * Similarity threshold (Jaccard on character trigrams) above which
 * ES and EN content are considered duplicate.
 */
const DUPLICATE_THRESHOLD = 0.90

/**
 * Fraction of the last N articles that must share an identical header
 * sequence before we emit a structure-repetition warning.
 */
const STRUCTURE_SIMILARITY_THRESHOLD = 0.60
const STRUCTURE_WINDOW = 20

// ── HELPERS ───────────────────────────────────────────────────────────────────

/** Extract ordered list of H2/H3 headings from markdown content. */
function extractHeadings(content: string): string[] {
  const headingRe = /^#{2,3}\s+(.+)$/gm
  const headings: string[] = []
  let match: RegExpExecArray | null
  while ((match = headingRe.exec(content)) !== null) {
    // Normalise to lowercase slug for structure comparison
    headings.push(match[1].trim().toLowerCase().replace(/[^a-z0-9\s]/g, ''))
  }
  return headings
}

/** Character trigram set from a string. */
function trigrams(text: string): Set<string> {
  const set = new Set<string>()
  const t = text.toLowerCase().replace(/\s+/g, ' ').trim()
  for (let i = 0; i < t.length - 2; i++) {
    set.add(t.slice(i, i + 3))
  }
  return set
}

/** Jaccard similarity between two trigram sets (0–1). */
function jaccard(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 && b.size === 0) return 1
  if (a.size === 0 || b.size === 0) return 0
  let intersection = 0
  for (const t of a) {
    if (b.has(t)) intersection++
  }
  return intersection / (a.size + b.size - intersection)
}

/**
 * Generate a 3-5 word keyword slug from a title.
 * Strips stop-words and returns the most meaningful tokens.
 */
function deriveKeywordSlug(title: string): string {
  const STOP = new Set([
    'a','an','the','and','or','but','in','on','at','to','for',
    'of','with','by','from','is','are','was','were','be','been',
    'being','have','has','had','do','does','did','will','would',
    'can','could','should','may','might','shall','how','what',
    'why','when','where','which','who','your','our','vs','vs.',
  ])
  const tokens = title
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .split(/\s+/)
    .filter((w) => w.length > 1 && !STOP.has(w))
  // Take 3–5 most meaningful tokens (preserve order)
  const selected = tokens.slice(0, 5)
  if (selected.length < 3 && tokens.length >= 3) {
    return tokens.slice(0, 3).join('-')
  }
  return selected.join('-')
}

// ── CHECK A — First-person unverified claims ──────────────────────────────────

function checkFirstPerson(
  article: ArticleInput,
  flags: string[],
): GuardrailStatus {
  if (article.first_party_verified === true) return 'ok'
  const matches = article.content.match(FIRST_PERSON_RE)
  if (matches && matches.length > 0) {
    const unique = [...new Set(matches.map((m) => m.toLowerCase()))]
    flags.push(
      `[A] Unverified first-person phrases detected (${unique.slice(0, 5).join(', ')}) — ` +
        `set first_party_verified=true or remove these phrases.`,
    )
    return 'needs_review'
  }
  return 'ok'
}

// ── CHECK B — ES/EN duplicate content ────────────────────────────────────────

function checkDuplicateContent(
  article: ArticleInput,
  flags: string[],
): GuardrailStatus {
  const contentEN = article.content_en
  if (!contentEN) return 'ok'
  const simScore = jaccard(trigrams(article.content), trigrams(contentEN))
  if (simScore >= DUPLICATE_THRESHOLD) {
    flags.push(
      `[B] ES/EN content similarity is ${(simScore * 100).toFixed(1)}% ` +
        `(threshold ${DUPLICATE_THRESHOLD * 100}%) — ` +
        `content_en must be a genuine translation/adaptation, not a copy.`,
    )
    return 'blocked'
  }
  return 'ok'
}

// ── CHECK C — Keyword must be a search-intent slug, not a verbatim H1 ─────────

function checkKeyword(
  article: ArticleInput,
  flags: string[],
): { status: GuardrailStatus; suggestedKeyword?: string } {
  const keyword = article.keyword || ''
  // If keyword looks like the full title (>6 words OR identical after normalise)
  const titleNorm = article.title.toLowerCase().trim()
  const kwNorm = keyword.toLowerCase().trim()
  const wordCount = keyword.split(/\s+/).filter(Boolean).length

  const isTitleLiteral = kwNorm === titleNorm
  const isTooLong = wordCount > 6

  if (isTitleLiteral || isTooLong) {
    const suggested = deriveKeywordSlug(article.title)
    flags.push(
      `[C] keyword "${keyword.slice(0, 60)}" is ${isTitleLiteral ? 'identical to the title' : 'too long (' + wordCount + ' words)'}. ` +
        `Suggested search-intent slug: "${suggested}".`,
    )
    return { status: 'needs_review', suggestedKeyword: suggested }
  }
  return { status: 'ok' }
}

// ── CHECK D — Pricing without verification timestamp ─────────────────────────

function checkPricing(
  article: ArticleInput,
  flags: string[],
): GuardrailStatus {
  const hasPrice = PRICING_RE.test(article.content)
  // Reset lastIndex after test() call on a global regex
  PRICING_RE.lastIndex = 0
  if (hasPrice && !article.pricing_verified_at) {
    const now = new Date().toISOString()
    // Auto-stamp; caller should persist this value
    article.pricing_verified_at = now
    flags.push(
      `[D] Article contains prices but pricing_verified_at was missing — ` +
        `auto-stamped to ${now}. Re-verify prices before next run if stale.`,
    )
    // This is a warning-level flag: auto-fixed, not blocking
    return 'needs_review'
  }
  return 'ok'
}

// ── CHECK E — Repetitive section structure across recent articles ─────────────

async function checkStructureRepetition(
  article: ArticleInput,
  supabase: SupabaseClient,
  flags: string[],
): Promise<GuardrailStatus> {
  let recentArticles: Array<{ content?: string; content_en?: string }> = []

  try {
    const { data } = await supabase
      .from('articles')
      .select('content, content_en')
      .order('published_at', { ascending: false })
      .limit(STRUCTURE_WINDOW)
    recentArticles = data ?? []
  } catch (e) {
    console.warn('[guardrails] Could not fetch recent articles for structure check:', e)
    return 'ok'
  }

  if (recentArticles.length < 3) return 'ok'

  const candidateHeadings = extractHeadings(article.content).join('|')
  if (!candidateHeadings) return 'ok'

  let matchCount = 0
  for (const row of recentArticles) {
    const existing = extractHeadings(row.content || row.content_en || '').join('|')
    if (!existing) continue
    // Use trigram similarity on the concatenated heading string
    const sim = jaccard(trigrams(candidateHeadings), trigrams(existing))
    if (sim >= STRUCTURE_SIMILARITY_THRESHOLD) matchCount++
  }

  const fraction = matchCount / recentArticles.length
  if (fraction >= STRUCTURE_SIMILARITY_THRESHOLD) {
    flags.push(
      `[E] Repetitive section structure: ${matchCount}/${recentArticles.length} recent articles ` +
        `share a similar heading layout (${(fraction * 100).toFixed(0)}% similarity). ` +
        `Vary H2 order or topics to avoid template-spam signals.`,
    )
    // Warn in logs but do not block — editorial decision
    console.warn(
      `[guardrails][E] STRUCTURE WARNING: ${matchCount}/${recentArticles.length} ` +
        `articles match current heading structure (${(fraction * 100).toFixed(0)}%).`,
    )
    return 'needs_review'
  }
  return 'ok'
}

// ── MAIN EXPORT ───────────────────────────────────────────────────────────────

/**
 * Run all guardrail checks on an article draft before inserting into Supabase.
 *
 * @param articleInput - The article data to validate (mutated in-place for auto-fixes).
 * @param supabase     - Supabase client (needed for check E).
 * @returns GuardrailResult with status, human-readable flags, and mutated article.
 *
 * Status semantics:
 *   'ok'           → safe to publish
 *   'needs_review' → set needs_review=true in DB; human review required
 *   'blocked'      → do NOT insert; fix the issue first
 */
export async function validateArticle(
  articleInput: ArticleInput,
  supabase: SupabaseClient,
): Promise<GuardrailResult> {
  // Work on a shallow copy so we can mutate safely
  const article: ArticleInput = { ...articleInput }
  const flags: string[] = []
  // Explicit type annotation prevents TypeScript from narrowing to 'never'
  let worstStatus: GuardrailStatus = 'ok'

  function escalate(s: GuardrailStatus): void {
    if (s === 'blocked') worstStatus = 'blocked'
    else if (s === 'needs_review' && worstStatus !== 'blocked') worstStatus = 'needs_review'
  }

  // A — first-person
  escalate(checkFirstPerson(article, flags))

  // B — ES/EN duplicate (blocking)
  escalate(checkDuplicateContent(article, flags))

  // C — keyword slug quality
  const checkC = checkKeyword(article, flags)
  if (checkC.suggestedKeyword) {
    article.keyword = checkC.suggestedKeyword
  }
  escalate(checkC.status)

  // D — pricing verification
  escalate(checkPricing(article, flags))

  // E — structure repetition (async, non-blocking)
  escalate(await checkStructureRepetition(article, supabase, flags))

  if (worstStatus !== 'ok') {
    if (worstStatus === 'needs_review') article.needs_review = true
    console.warn(
      `[guardrails] Article "${article.title?.slice(0, 60)}" → ${(worstStatus as string).toUpperCase()}\n` +
        flags.map((f) => `  • ${f}`).join('\n'),
    )
  } else {
    console.log(`[guardrails] ✅ Article "${article.title?.slice(0, 60)}" passed all checks.`)
  }

  return { status: worstStatus, flags, article }
}

// ── STANDALONE CLI HELPER (optional, for testing) ─────────────────────────────
// Run with: npx ts-node pipeline/content-guardrails.ts
if (require.main === module) {
  const supabaseUrl = process.env.SUPABASE_URL ?? ''
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY ?? ''
  const sb = createClient(supabaseUrl, supabaseKey)

  const testArticle: ArticleInput = {
    title: 'Best AI Tools for Solopreneurs in 2026',
    content:
      '## Introduction\nI\'ve been testing these tools for 3 years. Our team found that $49/month is the sweet spot.\n## Top Tools\nContent here.\n## Pricing\nMost tools cost $20–$100 per month.',
    content_en:
      '## Introduction\nI\'ve been testing these tools for 3 years. Our team found that $49/month is the sweet spot.\n## Top Tools\nContent here.\n## Pricing\nMost tools cost $20–$100 per month.',
    slug: 'best-ai-tools-solopreneurs-2026',
    keyword: 'Best AI Tools for Solopreneurs in 2026',
  }

  validateArticle(testArticle, sb).then((result) => {
    console.log('\nResult:', JSON.stringify(result, null, 2))
  })
}
