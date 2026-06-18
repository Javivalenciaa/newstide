import { supabase } from '@/lib/supabase'
import { NextResponse } from 'next/server'

export const revalidate = 3600 // refresh each hour

export async function GET() {
  const twoDaysAgo = new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString()

  const { data: articles } = await supabase
    .from('articles')
    .select('title, title_en, slug, slug_en, published_at')
    .gte('published_at', twoDaysAgo)
    .order('published_at', { ascending: false })
    .limit(1000)

  const items = (articles || []).flatMap((a) => [
    `  <url>
    <loc>https://www.newstide.news/articulo/${a.slug}</loc>
    <news:news>
      <news:publication>
        <news:name>NewsTide</news:name>
        <news:language>es</news:language>
      </news:publication>
      <news:publication_date>${new Date(a.published_at).toISOString()}</news:publication_date>
      <news:title>${escapeXml(a.title)}</news:title>
    </news:news>
  </url>`,
    ...(a.slug_en ? [
      `  <url>
    <loc>https://www.newstide.news/en/article/${a.slug_en}</loc>
    <news:news>
      <news:publication>
        <news:name>NewsTide</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>${new Date(a.published_at).toISOString()}</news:publication_date>
      <news:title>${escapeXml(a.title_en || a.title)}</news:title>
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

  return new NextResponse(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 's-maxage=3600, stale-while-revalidate',
    },
  })
}

function escapeXml(str: string): string {
  if (!str) return ''
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}
