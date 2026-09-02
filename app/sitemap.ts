import { supabase } from '@/lib/supabase'
import { MetadataRoute } from 'next'
import { groupByCluster, MIN_CLUSTER_SIZE } from '@/lib/topicClusters'
import { RETIRED_EN_SLUGS, RETIRED_ES_SLUGS } from '@/lib/consolidatedSlugs'

// ISR 1h: fresh enough for crawlers, avoids cold-start timeouts on every Googlebot hit.
export const revalidate = 3600

const ES_CATS = [
  { slug: 'ia',           label: 'IA' },
  { slug: 'startups',     label: 'Startups' },
  { slug: 'herramientas', label: 'Herramientas' },
  { slug: 'tutoriales',   label: 'Tutoriales' },
  { slug: 'noticias',     label: 'Noticias' },
  // Real categories from pipeline.py's detect_category() (solopreneur/indie hacker niche)
  { slug: 'ai-tools',       label: 'AI Tools' },
  { slug: 'automation',     label: 'Automation' },
  { slug: 'build-launch',   label: 'Build & Launch' },
  { slug: 'indie-hacking',  label: 'Indie Hacking' },
  { slug: 'growth',         label: 'Growth' },
  { slug: 'monetization',   label: 'Monetization' },
  { slug: 'freelancing',    label: 'Freelancing' },
  { slug: 'dev-stack',      label: 'Dev Stack' },
]

const EN_CATS = [
  { slug: 'ai',        label: 'AI' },
  { slug: 'startups',  label: 'Startups' },
  { slug: 'tools',     label: 'Tools' },
  { slug: 'tutorials', label: 'Tutorials' },
  { slug: 'news',      label: 'News' },
  { slug: 'ai-tools',       label: 'AI Tools' },
  { slug: 'automation',     label: 'Automation' },
  { slug: 'build-launch',   label: 'Build & Launch' },
  { slug: 'indie-hacking',  label: 'Indie Hacking' },
  { slug: 'growth',         label: 'Growth' },
  { slug: 'monetization',   label: 'Monetization' },
  { slug: 'freelancing',    label: 'Freelancing' },
  { slug: 'dev-stack',      label: 'Dev Stack' },
]

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [articlesRes, pseoRes, financeRes, financeWithEnRes] = await Promise.all([
    supabase
      .from('articles')
      .select('title, title_en, slug, slug_en, published_at')
      .order('published_at', { ascending: false }),
    supabase
      .from('pseo_pages')
      .select('slug, published_at')
      .lte('published_at', new Date().toISOString())
      .order('published_at', { ascending: false }),
    // FIX: fetch both slug (ES) and slug_en (EN) from finance_articles
    supabase
      .from('finance_articles')
      .select('slug, slug_en, title, title_en, published_at')
      .order('published_at', { ascending: false }),
    // Which finance articles actually HAVE an English body. Six rows carry a
    // slug_en with content_en NULL — they were listed here and served an empty
    // page to crawlers. Selecting only slug_en keeps this query cheap.
    supabase
      .from('finance_articles')
      .select('slug_en')
      .not('content_en', 'is', null)
      .not('slug_en', 'is', null),
  ])

  const allArticles = articlesRes.data || []
  const allPseo     = pseoRes.data     || []
  const allFinance  = financeRes.data  || []

  const financeSlugsWithEnglish = new Set(
    (financeWithEnRes.data || []).map((a) => a.slug_en)
  )

  // Legacy duplicate pairs: both language columns hold identical text, so one
  // of the two URLs is noindexed at the page level (see the [slug]/page.tsx
  // files). A noindexed URL does not belong in the sitemap either.
  // title === title_en identifies these exactly — verified against Supabase:
  // 26/26 in articles, 52/52 in finance_articles, zero misses.
  const isDupe = (a: { title?: string | null; title_en?: string | null }) =>
    !!a.title_en && a.title === a.title_en

  // ── Tech articles ──────────────────────────────────────────────
  // English is canonical in this niche, so a duplicate pair keeps /en/article/
  // and drops the /articulo/ twin.
  // Retired slugs are excluded here as well as 301'd in next.config.ts: a URL
  // that redirects but is still advertised in the sitemap sends Google two
  // contradictory instructions and wastes the crawl on a hop.
  const esArticleUrls = allArticles
    .filter((a) => !isDupe(a) && !RETIRED_ES_SLUGS.has(a.slug))
    .map((a) => ({
      url:             `https://www.newstide.news/articulo/${a.slug}`,
      lastModified:    new Date(a.published_at),
      changeFrequency: 'weekly' as const,
      priority:        0.8,
    }))

  const enArticleUrls = allArticles
    .filter((a) => !!a.slug_en && !RETIRED_EN_SLUGS.has(a.slug_en))
    .map((a) => ({
      url:             `https://www.newstide.news/en/article/${a.slug_en}`,
      lastModified:    new Date(a.published_at),
      changeFrequency: 'weekly' as const,
      priority:        0.8,
    }))

  // ── Programmatic SEO (comparisons) ─────────────────────────────
  const pseoUrls = allPseo.map((p) => ({
    url:             `https://www.newstide.news/en/compare/${p.slug}`,
    lastModified:    new Date(p.published_at),
    changeFrequency: 'monthly' as const,
    priority:        0.75,
  }))

  // ── Finance articles — ES + EN ─────────────────────────────────
  // es/fin/{slug}  — Spanish version (slug field)
  const esFinanceUrls = allFinance
    .filter((a) => !!a.slug)
    .map((a) => ({
      url:             `https://www.newstide.news/es/fin/${a.slug}`,
      lastModified:    new Date(a.published_at),
      changeFrequency: 'weekly' as const,
      priority:        0.8,
    }))

  // en/fin/{slug_en}  — English version (slug_en field)
  // Spanish is canonical in this vertical (Hispanics in the USA), so a
  // duplicate pair keeps /es/fin/ and drops the English twin. Also requires a
  // real English body: six rows had a slug_en pointing at content_en NULL.
  const enFinanceUrls = allFinance
    .filter((a) => !!a.slug_en && financeSlugsWithEnglish.has(a.slug_en) && !isDupe(a))
    .map((a) => ({
      url:             `https://www.newstide.news/en/fin/${a.slug_en}`,
      lastModified:    new Date(a.published_at),
      changeFrequency: 'weekly' as const,
      priority:        0.8,
    }))

  // ── Category pages ─────────────────────────────────────────────
  const esCatUrls = ES_CATS.map((c) => ({
    url:             `https://www.newstide.news/articulos/${c.slug}`,
    lastModified:    new Date(),
    changeFrequency: 'daily' as const,
    priority:        0.75,
  }))

  const enCatUrls = EN_CATS.map((c) => ({
    url:             `https://www.newstide.news/en/articles/${c.slug}`,
    lastModified:    new Date(),
    changeFrequency: 'daily' as const,
    priority:        0.75,
  }))

  // ── Topic pillar pages (clusters with >= MIN_CLUSTER_SIZE articles) ────────
  const clusterGroups = groupByCluster(allArticles, (a) => a.title_en || a.title || '')
  const pillarClusters = Array.from(clusterGroups.entries())
    .filter(([, items]) => items.length >= MIN_CLUSTER_SIZE)
    .map(([cluster, items]) => ({
      cluster,
      lastModified: items.reduce(
        (latest, a) => (new Date(a.published_at) > latest ? new Date(a.published_at) : latest),
        new Date(0)
      ),
    }))

  const enTopicUrls = pillarClusters.map(({ cluster, lastModified }) => ({
    url:             `https://www.newstide.news/en/topics/${cluster}`,
    lastModified,
    changeFrequency: 'weekly' as const,
    priority:        0.7,
  }))

  const esTopicUrls = pillarClusters.map(({ cluster, lastModified }) => ({
    url:             `https://www.newstide.news/temas/${cluster}`,
    lastModified,
    changeFrequency: 'weekly' as const,
    priority:        0.7,
  }))

  return [
    // ── Home & section indexes ──────────────────────────────────
    { url: 'https://www.newstide.news',              lastModified: new Date(), changeFrequency: 'hourly'  as const, priority: 1.0 },
    { url: 'https://www.newstide.news/en',            lastModified: new Date(), changeFrequency: 'hourly'  as const, priority: 1.0 },
    { url: 'https://www.newstide.news/articulos',     lastModified: new Date(), changeFrequency: 'hourly'  as const, priority: 0.9 },
    { url: 'https://www.newstide.news/en/articles',   lastModified: new Date(), changeFrequency: 'hourly'  as const, priority: 0.9 },
    { url: 'https://www.newstide.news/en/compare',    lastModified: new Date(), changeFrequency: 'weekly'  as const, priority: 0.85 },
    { url: 'https://www.newstide.news/es/fin',        lastModified: new Date(), changeFrequency: 'hourly'  as const, priority: 0.9 },
    { url: 'https://www.newstide.news/en/fin',        lastModified: new Date(), changeFrequency: 'hourly'  as const, priority: 0.9 },
    // ── Category pages ─────────────────────────────────────────
    ...esCatUrls,
    ...enCatUrls,
    // ── Topic pillar pages ──────────────────────────────────────
    ...esTopicUrls,
    ...enTopicUrls,
    // ── Static pages ───────────────────────────────────────────
    { url: 'https://www.newstide.news/sobre-nosotros',       lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.6 },
    { url: 'https://www.newstide.news/en/about',             lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.6 },
    { url: 'https://www.newstide.news/politica-editorial',   lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/en/editorial-policy',  lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/contacto',             lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/en/contact',           lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: 'https://www.newstide.news/privacidad',           lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.4 },
    { url: 'https://www.newstide.news/en/privacy',           lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.4 },
    { url: 'https://www.newstide.news/aviso-legal',          lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.4 },
    { url: 'https://www.newstide.news/terminos-de-uso',      lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.4 },
    { url: 'https://www.newstide.news/en/legal-notice',      lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.4 },
    { url: 'https://www.newstide.news/en/terms-of-use',      lastModified: new Date(), changeFrequency: 'monthly' as const, priority: 0.4 },
    { url: 'https://www.newstide.news/autores/javier-valencia',     lastModified: new Date(), changeFrequency: 'weekly' as const, priority: 0.7 },
    { url: 'https://www.newstide.news/en/authors/javier-valencia',  lastModified: new Date(), changeFrequency: 'weekly' as const, priority: 0.7 },
    // ── Dynamic articles ───────────────────────────────────────
    ...esArticleUrls,
    ...enArticleUrls,
    ...pseoUrls,
    ...esFinanceUrls,
    ...enFinanceUrls,
  ]
}
