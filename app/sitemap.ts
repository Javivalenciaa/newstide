import { supabase } from '@/lib/supabase'
import { MetadataRoute } from 'next'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const { data: articles } = await supabase
    .from('articles')
    .select('slug, slug_en, published_at')
    .order('published_at', { ascending: false })

  const esArticleUrls = (articles || []).map((a) => ({
    url: `https://www.newstide.news/articulo/${a.slug}`,
    lastModified: new Date(a.published_at),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }))

  const enArticleUrls = (articles || []).map((a) => ({
    url: `https://www.newstide.news/en/article/${a.slug_en || a.slug}`,
    lastModified: new Date(a.published_at),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }))

  return [
    { url: 'https://www.newstide.news', lastModified: new Date(), changeFrequency: 'hourly' as const, priority: 1.0 },
    { url: 'https://www.newstide.news/en', lastModified: new Date(), changeFrequency: 'hourly' as const, priority: 1.0 },
    { url: 'https://www.newstide.news/articulos', lastModified: new Date(), changeFrequency: 'hourly' as const, priority: 0.9 },
    { url: 'https://www.newstide.news/en/articles', lastModified: new Date(), changeFrequency: 'hourly' as const, priority: 0.9 },
    { url: 'https://www.newstide.news/sobre-nosotros', lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.6 },
    { url: 'https://www.newstide.news/en/about', lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.6 },
    { url: 'https://www.newstide.news/politica-editorial', lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/en/editorial-policy', lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/contacto', lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/en/contact', lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/privacidad', lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.4 },
    { url: 'https://www.newstide.news/en/privacy', lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.4 },
    { url: 'https://www.newstide.news/autores/maria-lopez', lastModified: new Date(), changeFrequency: 'weekly' as const, priority: 0.6 },
    { url: 'https://www.newstide.news/autores/carlos-ruiz', lastModified: new Date(), changeFrequency: 'weekly' as const, priority: 0.6 },
    { url: 'https://www.newstide.news/autores/ana-martinez', lastModified: new Date(), changeFrequency: 'weekly' as const, priority: 0.6 },
    { url: 'https://www.newstide.news/en/authors/maria-lopez', lastModified: new Date(), changeFrequency: 'weekly' as const, priority: 0.6 },
    { url: 'https://www.newstide.news/en/authors/carlos-ruiz', lastModified: new Date(), changeFrequency: 'weekly' as const, priority: 0.6 },
    { url: 'https://www.newstide.news/en/authors/ana-martinez', lastModified: new Date(), changeFrequency: 'weekly' as const, priority: 0.6 },
    ...esArticleUrls,
    ...enArticleUrls,
  ]
}
