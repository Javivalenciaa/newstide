import { supabase } from '@/lib/supabase'

// force-dynamic: Googlebot-News crawls every ~5-15 min.
// A cached 30-min sitemap means fresh articles are invisible to Google News.
// With force-dynamic the CDN edge serves a max-age=300 (5 min) response,
// so a new article appears in the sitemap within 5 minutes of publishing.
export const dynamic = 'force-dynamic'
export const revalidate = 0

function xmlEscape(value: string): string {
  if (!value) return ''
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

export async function GET() {
  const since = new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString()

  const { data: articles } = await supabase
    .from('articles')
    .select('slug, slug_en, title, title_en, published_at')
    .gte('published_at', since)
    .order('published_at', { ascending: false })
    .limit(1000)

  const items = (articles || []).flatMap((a) => [
    `  <url>
    <loc>https://www.newstide.news/articulo/${xmlEscape(a.slug)}</loc>
    <news:news>
      <news:publication>
        <news:name>NewsTide</news:name>
        <news:language>es</news:language>
      </news:publication>
      <news:publication_date>${new Date(a.published_at).toISOString()}</news:publication_date>
      <news:title>${xmlEscape(a.title)}</news:title>
    </news:news>
  </url>`,
    ...(a.slug_en && a.title_en
      ? [
          `  <url>
    <loc>https://www.newstide.news/en/article/${xmlEscape(a.slug_en)}</loc>
    <news:news>
      <news:publication>
        <news:name>NewsTide</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>${new Date(a.published_at).toISOString()}</news:publication_date>
      <news:title>${xmlEscape(a.title_en)}</news:title>
    </news:news>
  </url>`,
        ]
      : []),
  ])

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset
  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
${items.join('\n')}
</urlset>`

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      // CDN caches 5 min. Googlebot-News sees articles within 5 min of publish.
      // stale-while-revalidate=120 avoids thundering-herd on simultaneous crawls.
      'Cache-Control': 'public, max-age=300, stale-while-revalidate=120',
    },
  })
}
