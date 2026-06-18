import { supabase } from '@/lib/supabase'
import { NextResponse } from 'next/server'

export const revalidate = 3600

export async function GET() {
  const { data: articles } = await supabase
    .from('articles')
    .select('title, slug, excerpt, category, author, published_at, cover_image_url')
    .order('published_at', { ascending: false })
    .limit(50)

  const items = (articles || []).map((a) => `  <item>
    <title>${escapeXml(a.title)}</title>
    <link>https://www.newstide.news/articulo/${a.slug}</link>
    <guid isPermaLink="true">https://www.newstide.news/articulo/${a.slug}</guid>
    <description>${escapeXml(a.excerpt || '')}</description>
    <category>${escapeXml(a.category)}</category>
    <author>hola@newstide.news (${escapeXml(a.author)})</author>
    <pubDate>${new Date(a.published_at).toUTCString()}</pubDate>${a.cover_image_url ? `
    <enclosure url="${escapeXml(a.cover_image_url)}" type="image/jpeg" length="0" />` : ''}
  </item>`).join('\n')

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>NewsTide — Tecnología e IA</title>
    <link>https://www.newstide.news</link>
    <description>Noticias diarias sobre inteligencia artificial, startups y tecnología para founders y profesionales.</description>
    <language>es</language>
    <managingEditor>hola@newstide.news (NewsTide)</managingEditor>
    <webMaster>hola@newstide.news</webMaster>
    <copyright>© 2026 NewsTide</copyright>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <ttl>60</ttl>
    <image>
      <url>https://www.newstide.news/favicon-192x192.png</url>
      <title>NewsTide</title>
      <link>https://www.newstide.news</link>
    </image>
    <atom:link href="https://www.newstide.news/rss.xml" rel="self" type="application/rss+xml" />
${items}
  </channel>
</rss>`

  return new NextResponse(xml, {
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
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
