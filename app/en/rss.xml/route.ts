import { supabase } from '@/lib/supabase'
import { NextResponse } from 'next/server'

export const revalidate = 3600

export async function GET() {
  const { data: articles } = await supabase
    .from('articles')
    .select('title_en, slug_en, slug, excerpt_en, category, author, published_at')
    .order('published_at', { ascending: false })
    .limit(50)

  const items = (articles || []).map((a) => {
    const title = (a as Record<string, string>).title_en || (a as Record<string, string>).title || ''
    const excerpt = (a as Record<string, string>).excerpt_en || (a as Record<string, string>).excerpt || ''
    const slug = a.slug_en || a.slug
    return `  <item>
    <title>${escapeXml(title)}</title>
    <link>https://www.newstide.news/en/article/${slug}</link>
    <guid isPermaLink="true">https://www.newstide.news/en/article/${slug}</guid>
    <description>${escapeXml(excerpt)}</description>
    <category>${escapeXml(a.category)}</category>
    <author>hello@newstide.news (${escapeXml(a.author)})</author>
    <pubDate>${new Date(a.published_at).toUTCString()}</pubDate>
  </item>`
  }).join('\n')

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>NewsTide — Technology &amp; AI</title>
    <link>https://www.newstide.news/en</link>
    <description>Daily news about artificial intelligence, startups and technology for founders and professionals.</description>
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
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}
