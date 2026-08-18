import type { MetadataRoute } from 'next'

const BASE_URL = 'https://www.newstide.news'

type Article = {
  slug?: string | null
  updated_at?: string | null
  published_at?: string | null
}

async function getArticles(): Promise<Article[]> {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_SITE_URL ?? BASE_URL}/api/articles`, {
      next: { revalidate: 3600 },
    })

    if (!response.ok) return []

    const data = await response.json()
    const articles = Array.isArray(data) ? data : data.articles
    return Array.isArray(articles) ? articles : []
  } catch {
    return []
  }
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const articles = await getArticles()
  const lastModified = new Date()
  const urls = new Set<string>()

  const add = (path: string) => urls.add(`${BASE_URL}${path}`)

  add('/')
  add('/articulos')
  add('/en/articles')
  add('/autores')
  add('/en/authors')
  add('/contacto')
  add('/en/contact')
  add('/sobre-nosotros')
  add('/en/about')
  add('/aviso-legal')
  add('/en/legal-notice')
  add('/privacidad')
  add('/en/privacy')
  add('/terminos-de-uso')
  add('/en/terms-of-use')
  add('/politica-editorial')
  add('/en/editorial-policy')

  for (const article of articles) {
    if (!article.slug) continue
    const slug = encodeURIComponent(article.slug)
    const modified = article.updated_at ?? article.published_at ?? lastModified

    add(`/articulo/${slug}`)
    add(`/en/article/${slug}`)
    add(`/es/fin/${slug}`)

    urls.add(`${BASE_URL}/articulo/${slug}`)
    urls.add(`${BASE_URL}/en/article/${slug}`)
    urls.add(`${BASE_URL}/es/fin/${slug}`)

    void modified
  }

  return Array.from(urls).map((url) => ({
    url,
    lastModified,
    changeFrequency: 'daily',
    priority: url.includes('/article/') || url.includes('/articulo/') || url.includes('/fin/') ? 0.8 : 0.5,
  }))
}
