import { supabase } from '@/lib/supabase'

export const revalidate = 1800

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
    .limit(100)

  const items = (articles || []).flatMap((a) => [
    `  <url>
    <loc>https://www.newstide.news/articulo/${a.slug}</loc>
    <news:news>
      <news:publication>
        <news:name>NewsTide</news:name>
        <news:language>es</news:language>
      </news:publication>
      <news:publication_date>${new Date(a.published_at).toISOString()}</news:publication_date>
      <news:title>${xmlEscape(a.title)}</news:title>
    </news:news>
  </url>`,
    ...(a.slug_en && a.title_en ? [
      `  <url>
    <loc>https://www.newstide.news/en/article/${a.slug_en}</loc>
    <news:news>
      <news:publication>
        <news:name>NewsTide</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>${new Date(a.published_at).toISOString()}</news:publication_date>
      <news:title>${xmlEscape(a.title_en)}</news:title>
    </news:news>
  </url>`
    ] : []),
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
      'Cache-Control': 'public, s-maxage=1800, stale-while-revalidate=3600',
    },
  })
}
