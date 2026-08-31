import { supabase } from '@/lib/supabase'

export const revalidate = 3600

const BASE_URL = 'https://www.newstide.news'

type SitemapUrl = {
  loc: string
  lastmod?: string | null
  changefreq: 'weekly' | 'monthly'
  priority: number
}

function escapeXml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function toLastmod(value?: string | null) {
  const date = value ? new Date(value) : null
  return date && !Number.isNaN(date.getTime()) ? date.toISOString() : undefined
}

export async function GET() {
  const now = new Date().toISOString()
  const [articlesRes, pseoRes, financeRes, financeWithEnRes] = await Promise.all([
    supabase
      .from('articles')
      .select('slug, slug_en, title, title_en, published_at')
      .not('slug', 'is', null)
      .lte('published_at', now)
      .order('published_at', { ascending: false }),
    supabase
      .from('pseo_pages')
      .select('slug, published_at')
      .not('slug', 'is', null)
      .lte('published_at', now)
      .order('published_at', { ascending: false }),
    supabase
      .from('finance_articles')
      .select('slug, slug_en, title, title_en, published_at')
      .lte('published_at', now)
      .order('published_at', { ascending: false }),
    supabase
      .from('finance_articles')
      .select('slug_en')
      .not('content_en', 'is', null)
      .not('slug_en', 'is', null),
  ])

  const financeSlugsWithEnglish = new Set(
    (financeWithEnRes.data || []).map((a) => a.slug_en)
  )

  // Legacy duplicate pairs — identical text in both language columns. One of
  // the two URLs is noindexed at page level, so neither sitemap should list it.
  const isDupe = (a: { title?: string | null; title_en?: string | null }) =>
    !!a.title_en && a.title === a.title_en

  const urls = new Map<string, SitemapUrl>()
  const add = (entry: SitemapUrl) => urls.set(entry.loc, entry)

  for (const article of articlesRes.data ?? []) {
    // English is canonical in this niche — a duplicate pair drops /articulo/.
    if (article.slug && !isDupe(article)) {
      add({
        loc: `${BASE_URL}/articulo/${encodeURIComponent(article.slug)}`,
        lastmod: toLastmod(article.published_at),
        changefreq: 'weekly',
        priority: 0.8,
      })
    }

    if (article.slug_en) {
      add({
        loc: `${BASE_URL}/en/article/${encodeURIComponent(article.slug_en)}`,
        lastmod: toLastmod(article.published_at),
        changefreq: 'weekly',
        priority: 0.8,
      })
    }
  }

  for (const page of pseoRes.data ?? []) {
    if (!page.slug) continue
    add({
      loc: `${BASE_URL}/en/compare/${encodeURIComponent(page.slug)}`,
      lastmod: toLastmod(page.published_at),
      changefreq: 'monthly',
      priority: 0.75,
    })
  }

  for (const article of financeRes.data ?? []) {
    // FIX: this loop only ever emitted /en/fin/ — the 101 Spanish finance
    // articles (the site's primary revenue niche) were never in this
    // sitemap despite the file being named "complete" and being listed in
    // robots.txt alongside the main sitemap.
    if (article.slug) {
      add({
        loc: `${BASE_URL}/es/fin/${encodeURIComponent(article.slug)}`,
        lastmod: toLastmod(article.published_at),
        changefreq: 'weekly',
        priority: 0.8,
      })
    }

    // Spanish is canonical in this vertical, and the English URL must have a
    // real English body — six rows carried a slug_en with content_en NULL.
    if (
      article.slug_en &&
      financeSlugsWithEnglish.has(article.slug_en) &&
      !isDupe(article)
    ) {
      add({
        loc: `${BASE_URL}/en/fin/${encodeURIComponent(article.slug_en)}`,
        lastmod: toLastmod(article.published_at),
        changefreq: 'weekly',
        priority: 0.8,
      })
    }
  }

  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${Array.from(urls.values()).map(({ loc, lastmod, changefreq, priority }) => `  <url>\n    <loc>${escapeXml(loc)}</loc>${lastmod ? `\n    <lastmod>${lastmod}</lastmod>` : ''}\n    <changefreq>${changefreq}</changefreq>\n    <priority>${priority}</priority>\n  </url>`).join('\n')}\n</urlset>`

  return new Response(body, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 's-maxage=3600, stale-while-revalidate=86400',
    },
  })
}
