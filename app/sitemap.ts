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

  const staticPages = [
    { url: 'https://www.newstide.news', priority: 1.0, changeFrequency: 'daily' as const },
    { url: 'https://www.newstide.news/en', priority: 1.0, changeFrequency: 'daily' as const },
    { url: 'https://www.newstide.news/articulos', priority: 0.9, changeFrequency: 'daily' as const },
    { url: 'https://www.newstide.news/en/articles', priority: 0.9, changeFrequency: 'daily' as const },
    { url: 'https://www.newstide.news/sobre-nosotros', priority: 0.7, changeFrequency: 'monthly' as const },
    { url: 'https://www.newstide.news/en/about', priority: 0.7, changeFrequency: 'monthly' as const },
    { url: 'https://www.newstide.news/politica-editorial', priority: 0.6, changeFrequency: 'monthly' as const },
    { url: 'https://www.newstide.news/en/editorial-policy', priority: 0.6, changeFrequency: 'monthly' as const },
    { url: 'https://www.newstide.news/privacidad', priority: 0.5, changeFrequency: 'yearly' as const },
    { url: 'https://www.newstide.news/en/privacy', priority: 0.5, changeFrequency: 'yearly' as const },
    { url: 'https://www.newstide.news/contacto', priority: 0.6, changeFrequency: 'monthly' as const },
    { url: 'https://www.newstide.news/en/contact', priority: 0.6, changeFrequency: 'monthly' as const },
    { url: 'https://www.newstide.news/autores/maria-lopez', priority: 0.6, changeFrequency: 'monthly' as const },
    { url: 'https://www.newstide.news/autores/carlos-ruiz', priority: 0.6, changeFrequency: 'monthly' as const },
    { url: 'https://www.newstide.news/autores/ana-martinez', priority: 0.6, changeFrequency: 'monthly' as const },
  ].map((p) => ({
    ...p,
    lastModified: new Date(),
  }))

  return [...staticPages, ...esArticleUrls, ...enArticleUrls]
}
