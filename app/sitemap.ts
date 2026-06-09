import { supabase } from '@/lib/supabase'
import { MetadataRoute } from 'next'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const { data: articles } = await supabase
    .from('articles')
    .select('slug, published_at')
    .order('published_at', { ascending: false })

  const esUrls = (articles || []).map((a) => ({
    url: `https://www.newstide.news/articulo/${a.slug}`,
    lastModified: new Date(a.published_at),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }))

  const enUrls = (articles || []).map((a) => ({
    url: `https://www.newstide.news/en/article/${a.slug}`,
    lastModified: new Date(a.published_at),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }))

  return [
    { url: 'https://www.newstide.news',     lastModified: new Date(), priority: 1.0 },
    { url: 'https://www.newstide.news/en',  lastModified: new Date(), priority: 1.0 },
    { url: 'https://www.newstide.news/blog', lastModified: new Date(), priority: 0.9 },
    ...esUrls,
    ...enUrls,
  ]
}
