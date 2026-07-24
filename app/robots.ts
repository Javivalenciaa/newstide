import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        // Default: all crawlers can index everything except internal routes
        userAgent: '*',
        allow: '/',
        disallow: ['/api/', '/_next/'],
      },
      {
        // ChatGPT Search retrieval — allow so content appears in ChatGPT answers
        userAgent: 'OAI-SearchBot',
        allow: '/',
      },
      {
        // OpenAI training crawler — block (content monetization protection)
        userAgent: 'GPTBot',
        disallow: '/',
      },
      {
        // Perplexity retrieval — allow
        userAgent: 'PerplexityBot',
        allow: '/',
      },
      {
        // Anthropic Claude retrieval — allow
        userAgent: 'ClaudeBot',
        allow: '/',
      },
      {
        // Google Gemini training — block
        userAgent: 'Google-Extended',
        disallow: '/',
      },
      {
        // Meta AI training ��� block
        userAgent: 'FacebookBot',
        disallow: '/',
      },
      {
        // Apple AI training — block
        userAgent: 'Applebot-Extended',
        disallow: '/',
      },
      {
        // Bing retrieval — allow (important for ChatGPT web search fallback)
        userAgent: 'Bingbot',
        allow: '/',
      },
    ],
    sitemap: [
      'https://www.newstide.news/sitemap.xml',
      'https://www.newstide.news/news-sitemap.xml',
    ],
  }
}
