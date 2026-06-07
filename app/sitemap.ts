import { supabase } from '@/lib/supabase'
import { MetadataRoute } from 'next'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const { data: articles } = await supabase
    .from('articles')
    .select('slug, published_at')
    .order('published_at', { ascending: false })

  const articleUrls = (articles || []).map((a) => ({
    url: `https://newstide.news/articulo/${a.slug}`,
    lastModified: new Date(a.published_at),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }))

  return [
    { url: 'https://newstide.news', lastModified: new Date(), priority: 1.0 },
    { url: 'https://newstide.news/blog', lastModified: new Date(), priority: 0.9 },
    ...articleUrls,
  ]
}
