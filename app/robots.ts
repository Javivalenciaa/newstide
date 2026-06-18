import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/api/', '/_next/'],
      },
    ],
    sitemap: [
      'https://www.newstide.news/sitemap.xml',
      'https://www.newstide.news/news-sitemap.xml',
    ],
    host: 'https://www.newstide.news',
  }
}
