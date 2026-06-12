import { supabase } from '@/lib/supabase'
import { MetadataRoute } from 'next'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const { data: articles } = await supabase
    .from('articles')
    .select('slug, published_at')
    .order('published_at', { ascending: false })

  const esArticleUrls = (articles || []).map((a) => ({
    url: `https://www.newstide.news/articulo/${a.slug}`,
    lastModified: new Date(a.published_at),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }))

  const enArticleUrls = (articles || []).map((a) => ({
    url: `https://www.newstide.news/en/article/${a.slug}`,
    lastModified: new Date(a.published_at),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }))

  return [
    {
      url: 'https://www.newstide.news',
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 1.0,
    },
    {
      url: 'https://www.newstide.news/en',
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 1.0,
    },
    {
      url: 'https://www.newstide.news/articulos',
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.9,
    },
    {
      url: 'https://www.newstide.news/en/articles',
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.9,
    },
    ...esArticleUrls,
    ...enArticleUrls,
  ]
}
