import { supabase } from '@/lib/supabase'
import { MetadataRoute } from 'next'

// FIX: force-dynamic caused sitemap to regenerate on every Googlebot request,
// risking cold-start timeouts and inconsistent responses. ISR (1h) is correct
// for a news sitemap: fresh enough, stable enough for crawlers.
export const revalidate = 3600

const ES_CATS = [
  { slug: 'ia',           label: 'IA' },
  { slug: 'startups',     label: 'Startups' },
  { slug: 'herramientas', label: 'Herramientas' },
  { slug: 'tutoriales',   label: 'Tutoriales' },
  { slug: 'noticias',     label: 'Noticias' },
]

const EN_CATS = [
  { slug: 'ai',        label: 'AI' },
  { slug: 'startups',  label: 'Startups' },
  { slug: 'tools',     label: 'Tools' },
  { slug: 'tutorials', label: 'Tutorials' },
  { slug: 'news',      label: 'News' },
]

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [articlesRes, pseoRes, financeRes] = await Promise.all([
    supabase.from('articles').select('slug, slug_en, published_at').order('published_at', { ascending: false }),
    supabase.from('pseo_pages').select('slug, published_at').lte('published_at', new Date().toISOString()).order('published_at', { ascending: false }),
    supabase.from('finance_articles').select('slug_en, published_at').not('slug_en', 'is', null).order('published_at', { ascending: false }),
  ])

  const allArticles = articlesRes.data || []
  const allPseo     = pseoRes.data     || []
  const allFinance  = financeRes.data  || []

  const esArticleUrls = allArticles.map((a) => ({
    url:             `https://www.newstide.news/articulo/${a.slug}`,
    lastModified:    new Date(a.published_at),
    changeFrequency: 'weekly' as const,
    priority:        0.8,
  }))

  const enArticleUrls = allArticles
    .filter((a) => !!a.slug_en)
    .map((a) => ({
      url:             `https://www.newstide.news/en/article/${a.slug_en}`,
      lastModified:    new Date(a.published_at),
      changeFrequency: 'weekly' as const,
      priority:        0.8,
    }))

  const pseoUrls = allPseo.map((p) => ({
    url:             `https://www.newstide.news/en/compare/${p.slug}`,
    lastModified:    new Date(p.published_at),
    changeFrequency: 'monthly' as const,
    priority:        0.75,
  }))

  const financeArticleUrls = allFinance.map((a) => ({
    url:             `https://www.newstide.news/en/fin/${a.slug_en}`,
    lastModified:    new Date(a.published_at),
    changeFrequency: 'weekly' as const,
    priority:        0.8,
  }))

  const esCatUrls = ES_CATS.map((c) => ({
    url: `https://www.newstide.news/articulos/${c.slug}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.75,
  }))

  const enCatUrls = EN_CATS.map((c) => ({
    url: `https://www.newstide.news/en/articles/${c.slug}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.75,
  }))

  return [
    { url: 'https://www.newstide.news',            lastModified: new Date(), changeFrequency: 'hourly'  as const, priority: 1.0 },
    { url: 'https://www.newstide.news/en',          lastModified: new Date(), changeFrequency: 'hourly'  as const, priority: 1.0 },
    { url: 'https://www.newstide.news/articulos',   lastModified: new Date(), changeFrequency: 'hourly'  as const, priority: 0.9 },
    { url: 'https://www.newstide.news/en/articles', lastModified: new Date(), changeFrequency: 'hourly'  as const, priority: 0.9 },
    { url: 'https://www.newstide.news/en/compare',  lastModified: new Date(), changeFrequency: 'weekly'  as const, priority: 0.85 },
    { url: 'https://www.newstide.news/en/fin',      lastModified: new Date(), changeFrequency: 'hourly'  as const, priority: 0.9 },
    ...esCatUrls,
    ...enCatUrls,
    { url: 'https://www.newstide.news/sobre-nosotros',      lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.6 },
    { url: 'https://www.newstide.news/en/about',            lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.6 },
    { url: 'https://www.newstide.news/politica-editorial',  lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/en/editorial-policy', lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/contacto',            lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/en/contact',          lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/privacidad',          lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.4 },
    { url: 'https://www.newstide.news/en/privacy',          lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.4 },
    { url: 'https://www.newstide.news/autores/javier-valencia',    lastModified: new Date(), changeFrequency: 'weekly' as const, priority: 0.7 },
    { url: 'https://www.newstide.news/en/authors/javier-valencia', lastModified: new Date(), changeFrequency: 'weekly' as const, priority: 0.7 },
    ...esArticleUrls,
    ...enArticleUrls,
    ...pseoUrls,
    ...financeArticleUrls,
  ]
}
