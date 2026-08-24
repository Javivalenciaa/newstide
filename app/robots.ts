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
        // Googlebot News — explicitly allowed with full access for Google News indexing
        userAgent: 'Googlebot-News',
        allow: '/',
      },
      {
        // Googlebot — explicit full access
        userAgent: 'Googlebot',
        allow: '/',
      },
      {
        // Bingbot — important for ChatGPT web search fallback and Copilot
        userAgent: 'Bingbot',
        allow: '/',
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
        // Anthropic Claude retrieval (ClaudeBot)
        userAgent: 'ClaudeBot',
        allow: '/',
      },
      {
        // Anthropic training crawler — block
        userAgent: 'anthropic-ai',
        disallow: '/',
      },
      {
        // You.com AI search retrieval — allow
        userAgent: 'YouBot',
        allow: '/',
      },
      {
        // Amazon Alexa / Amazonbot retrieval — allow
        userAgent: 'Amazonbot',
        allow: '/',
      },
      {
        // DuckDuckGo AI assistant retrieval — allow
        userAgent: 'DuckAssistBot',
        allow: '/',
      },
      {
        // Meta AI retrieval (external agent, not training) — allow
        userAgent: 'meta-externalagent',
        allow: '/',
      },
      {
        // Meta AI training — block
        userAgent: 'FacebookBot',
        disallow: '/',
      },
      {
        // Google Gemini training — block
        userAgent: 'Google-Extended',
        disallow: '/',
      },
      {
        // Apple AI training — block
        userAgent: 'Applebot-Extended',
        disallow: '/',
      },
      {
        // Naver AI (Korean market) — allow
        userAgent: 'Yeti',
        allow: '/',
      },
      {
        // Petal search (Huawei) — allow for broader reach
        userAgent: 'PetalBot',
        allow: '/',
      },
    ],
    sitemap: [
      'https://www.newstide.news/sitemap.xml',
      'https://www.newstide.news/news-sitemap.xml',
      'https://www.newstide.news/sitemap-complete.xml',
    ],
    host: 'https://www.newstide.news',
  }
}
