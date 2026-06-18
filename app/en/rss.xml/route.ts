import { supabase } from '@/lib/supabase'
import { NextResponse } from 'next/server'

export const revalidate = 3600

export async function GET() {
  const { data: articles } = await supabase
    .from('articles')
    .select('title, title_en, slug, slug_en, excerpt, excerpt_en, category, author, published_at, cover_image_url')
    .not('slug_en', 'is', null)
    .order('published_at', { ascending: false })
    .limit(50)

  const CAT_EN: Record<string, string> = {
    'IA': 'AI', 'Tutoriales': 'Tutorials',
    'Herramientas': 'Tools', 'Startups': 'Startups', 'Noticias': 'News',
  }

  const items = (articles || []).map((a) => {
    const title = a.title_en || a.title
    const description = a.excerpt_en || a.excerpt || ''
    const slug = a.slug_en || a.slug
    const url = `https://www.newstide.news/en/article/${slug}`
    const cat = CAT_EN[a.category] || a.category
    return `  <item>
    <title>${escapeXml(title)}</title>
    <link>${url}</link>
    <guid isPermaLink="true">${url}</guid>
    <description>${escapeXml(description)}</description>
    <category>${escapeXml(cat)}</category>
    <author>hello@newstide.news (${escapeXml(a.author)})</author>
    <pubDate>${new Date(a.published_at).toUTCString()}</pubDate>${a.cover_image_url ? `
    <enclosure url="${escapeXml(a.cover_image_url)}" type="image/jpeg" length="0" />` : ''}
  </item>`
  }).join('\n')

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>NewsTide — Technology &amp; AI</title>
    <link>https://www.newstide.news/en</link>
    <description>Daily news on artificial intelligence, startups and technology for founders and professionals.</description>
    <language>en</language>
    <managingEditor>hello@newstide.news (NewsTide)</managingEditor>
    <webMaster>hello@newstide.news</webMaster>
    <copyright>© 2026 NewsTide</copyright>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <ttl>60</ttl>
    <image>
      <url>https://www.newstide.news/favicon-192x192.png</url>
      <title>NewsTide</title>
      <link>https://www.newstide.news/en</link>
    </image>
    <atom:link href="https://www.newstide.news/en/rss.xml" rel="self" type="application/rss+xml" />
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
