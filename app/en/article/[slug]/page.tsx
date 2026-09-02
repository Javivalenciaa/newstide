import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { parseRelatedArticles } from '@/lib/relatedArticles'
import { notFound, permanentRedirect } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import ReactMarkdown from 'react-markdown'
import { stripImageCredits } from '@/lib/articleContent'
import NewsletterForm from '@/components/NewsletterForm'
import ShareButtons from '@/components/ShareButtons'

// 1 hora: aligns with ES counterpart. publish-hook calls revalidatePath on each publish.
export const revalidate = 3600
export const dynamicParams = true

const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef',
  'Herramientas': '#e8d5a3', 'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c',
  // Real categories from pipeline.py's detect_category() (solopreneur/indie hacker niche)
  'AI Tools': '#6ecfca', 'Automation': '#9b8cef', 'Build & Launch': '#e8d5a3',
  'Indie Hacking': '#7ecf9b', 'Growth': '#ef6c6c', 'Monetization': '#f0a050',
  'Freelancing': '#8ecae6', 'Dev Stack': '#c9a0f5',
}

const CAT_EN: Record<string, string> = {
  'IA': 'AI', 'Tutoriales': 'Tutorials',
  'Herramientas': 'Tools', 'Startups': 'Startups', 'Noticias': 'News',
  'AI Tools': 'AI Tools', 'Automation': 'Automation', 'Build & Launch': 'Build & Launch',
  'Indie Hacking': 'Indie Hacking', 'Growth': 'Growth', 'Monetization': 'Monetization',
  'Freelancing': 'Freelancing', 'Dev Stack': 'Dev Stack',
}

const CAT_SLUG_EN: Record<string, string> = {
  'IA': 'ai', 'Tutoriales': 'tutorials',
  'Herramientas': 'tools', 'Startups': 'startups', 'Noticias': 'news',
  'AI Tools': 'ai-tools', 'Automation': 'automation', 'Build & Launch': 'build-launch',
  'Indie Hacking': 'indie-hacking', 'Growth': 'growth', 'Monetization': 'monetization',
  'Freelancing': 'freelancing', 'Dev Stack': 'dev-stack',
}

const CAT_SECTION_EN: Record<string, string> = {
  'IA': 'Artificial Intelligence', 'Tutoriales': 'Tutorials',
  'Herramientas': 'Tools & Technology', 'Startups': 'Startups', 'Noticias': 'News',
  'AI Tools': 'AI Tools', 'Automation': 'Automation', 'Build & Launch': 'Build & Launch',
  'Indie Hacking': 'Indie Hacking', 'Growth': 'Growth', 'Monetization': 'Monetization',
  'Freelancing': 'Freelancing', 'Dev Stack': 'Dev Stack',
}

// Safe slug fallback for any category not yet mapped above (was hardcoded to 'ai'/'Technology').
function slugifyCategory(cat: string): string {
  return cat.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

const AUTHOR_SLUG = 'javier-valencia'
const AUTHOR_PAGE_EN = `https://www.newstide.news/en/authors/${AUTHOR_SLUG}`

function Badge({ cat }: { cat: string }) {
  const color = CAT_COLORS[cat] || '#6ecfca'
  const label = CAT_EN[cat] || cat
  return (
    <span style={{
      display: 'inline-block', padding: '4px 10px', borderRadius: '6px',
      fontSize: '10px', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase',
      background: `${color}18`, color, border: `1px solid ${color}30`
    }}>{label}</span>
  )
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
}

function seoTitle(title: string): string {
  const max = 57
  if (title.length <= max) return title
  const cut = title.substring(0, max)
  const lastSpace = cut.lastIndexOf(' ')
  return lastSpace > 20 ? cut.substring(0, lastSpace) : cut
}

function seoDescription(excerpt: string, fallback: string): string {
  const text = excerpt || fallback
  if (text.length <= 155) return text
  const cut = text.substring(0, 152)
  const lastSpace = cut.lastIndexOf(' ')
  return `${cut.substring(0, lastSpace > 50 ? lastSpace : 152)}...`
}

function buildKeywords(cat: string, title: string, keyword?: string | null): string[] {
  const catLabel = CAT_EN[cat] || cat
  const stopWords = new Set(['the','a','an','and','or','of','in','on','to','for','is','are','was','were','with','at','by','from','as','how','why','what','when','where'])
  const titleTokens = title
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .split(/\s+/)
    .filter((t) => t.length > 3 && !stopWords.has(t))
    .slice(0, 4)
  const extra = keyword ? [keyword] : []
  return [catLabel, 'NewsTide', ...extra, ...titleTokens]
    .map((k) => k.trim())
    .filter((k, i, arr) => k && arr.indexOf(k) === i)
    .slice(0, 8)
}

function extractCitations(content: string, max = 5): Array<{ '@type': string; url: string; name: string }> {
  if (!content) return []
  const mdLinkRe = /\[([^\]]{3,80})\]\((https:\/\/[^)]+)\)/g
  const results: Array<{ '@type': string; url: string; name: string }> = []
  let m: RegExpExecArray | null
  while ((m = mdLinkRe.exec(content)) !== null && results.length < max) {
    const label = m[1].trim()
    const href  = m[2].trim()
    if (href.includes('newstide.news')) continue
    results.push({ '@type': 'CreativeWork', name: label, url: href })
  }
  return results
}

function extractFAQs(content: string): Array<{ question: string; answer: string }> {
  const faqs: Array<{ question: string; answer: string }> = []
  const h3Regex = /^###\s+(.+\?)\s*\n+([^#]+)/gm
  let match
  while ((match = h3Regex.exec(content)) !== null && faqs.length < 5) {
    const question = match[1].trim()
    const answer = match[2].replace(/\*\*/g, '').trim().substring(0, 300)
    if (question && answer) faqs.push({ question, answer })
  }
  return faqs
}

// Only for genuine "How to X" titles — steps are the article's real H2 sections,
// nothing invented. Skips FAQ/conclusion/mistakes sections, which aren't steps.
function extractHowToSteps(content: string, title: string): Array<{ name: string; text: string }> {
  if (!/^(how to|how i|how they)\b/i.test(title.trim())) return []
  const steps: Array<{ name: string; text: string }> = []
  const sections = content.split(/^##\s+/m).slice(1)
  for (const section of sections) {
    const lines = section.split('\n')
    const heading = (lines[0] || '').trim()
    if (!heading || /^(faq|frequently asked|conclusion|common mistakes|what nobody tells you|who this is for)/i.test(heading)) continue
    let text = ''
    for (const line of lines.slice(1)) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('!') || trimmed.startsWith('|')) continue
      text = trimmed.replace(/\*\*(.+?)\*\*/g, '$1').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      break
    }
    if (heading && text) steps.push({ name: heading, text: text.slice(0, 300) })
    if (steps.length >= 8) break
  }
  return steps.length >= 3 ? steps : []
}

// Conservative: only real tool names lifted verbatim from a "X vs Y" title, no invented data.
function extractSoftwareMentions(title: string): Array<{ name: string }> {
  const m = title.match(/^(.+?)\s+vs\.?\s+(.+?)(?:[:\-–—]|$)/i)
  if (!m) return []
  const a = m[1].trim()
  const b = m[2].trim()
  if (!a || !b || a.length > 40 || b.length > 40) return []
  return [{ name: a }, { name: b }]
}

function extractVisibleSources(content: string, max = 5): Array<{ label: string; href: string }> {
  if (!content) return []
  const mdLinkRe = /\[([^\]]{3,80})\]\((https:\/\/[^)]+)\)/g
  const results: Array<{ label: string; href: string }> = []
  let m: RegExpExecArray | null
  while ((m = mdLinkRe.exec(content)) !== null && results.length < max) {
    const label = m[1].trim()
    const href  = m[2].trim()
    if (href.includes('newstide.news')) continue
    results.push({ label, href })
  }
  return results
}

const FIELDS = 'id, title, title_en, excerpt, excerpt_en, content, content_en, slug, slug_en, category, published_at, updated_at, cover_image_url, author, keyword, related_articles'

type RelatedArticleEN = { title_en: string; title: string; slug_en: string; category?: string }

async function getArticle(slug: string) {
  const { data: byEn } = await supabase
    .from('articles')
    .select(FIELDS)
    .eq('slug_en', slug)
    .maybeSingle()
  if (byEn) return byEn

  const { data: byEs } = await supabase
    .from('articles')
    .select(FIELDS)
    .eq('slug', slug)
    .maybeSingle()
  if (byEs) {
    if (byEs.slug_en) {
      permanentRedirect(`/en/article/${byEs.slug_en}`)
    } else {
      permanentRedirect(`/articulo/${byEs.slug}`)
    }
  }

  const { data: fuzzy } = await supabase
    .from('articles')
    .select(FIELDS)
    .ilike('slug_en', `%${slug}%`)
    .limit(1)
    .maybeSingle()
  return fuzzy || null
}

export async function generateStaticParams() {
  const { data } = await supabase
    .from('articles')
    .select('slug_en')
    .not('slug_en', 'is', null)
  if (!data) return []
  return data
    .filter((a) => typeof a.slug_en === 'string' && a.slug_en.trim() !== '')
    .map((a) => ({ slug: a.slug_en as string }))
}

export async function generateMetadata(
  { params }: { params: Promise<{ slug: string }> }
): Promise<Metadata> {
  const { slug } = await params
  const article = await getArticle(slug)

  if (!article) return {
    title: 'Article not found',
    description: 'This content is not available on NewsTide — AI, startups and tech news.'
  }

  const rawTitle    = article.title_en || article.title
  const title       = seoTitle(rawTitle)
  const description = seoDescription(
    article.excerpt_en || article.excerpt,
    'Technology, AI and trends for founders, developers and professionals. Updated daily on NewsTide.'
  )
  const enSlug = article.slug_en
  const url    = enSlug
    ? `https://www.newstide.news/en/article/${enSlug}`
    : `https://www.newstide.news/articulo/${article.slug}`
  const urlES  = `https://www.newstide.news/articulo/${article.slug}`
  const ogCategory = CAT_EN[article.category] || article.category || ''
  const images = article.cover_image_url
    ? [{ url: article.cover_image_url, width: 1200, height: 630, alt: rawTitle }]
    : [{
        url: `https://www.newstide.news/api/og?title=${encodeURIComponent(title)}&category=${encodeURIComponent(ogCategory)}`,
        width: 1200, height: 630, alt: rawTitle,
      }]

  return {
    title,
    description,
    alternates: {
      canonical: url,
      languages: {
        'en': url,
        'es': urlES,
        'x-default': url,
      },
    },
    openGraph: {
      title: rawTitle,
      description,
      url,
      siteName: 'NewsTide',
      locale: 'en_US',
      type: 'article',
      publishedTime: article.published_at,
      modifiedTime: article.updated_at || article.published_at,
      authors: ['Javier Valencia'],
      images,
    },
    twitter: {
      card: 'summary_large_image',
      title: rawTitle,
      description,
      images: article.cover_image_url
        ? [article.cover_image_url]
        : ['https://www.newstide.news/og-image.png'],
    },
  }
}

export default async function ArticlePageEN({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params

  const article = await getArticle(slug)

  if (!article) notFound()

  if (!article.slug_en) permanentRedirect(`/articulo/${article.slug}`)

  const rawTitle   = article.title_en   || article.title
  const rawExcerpt = article.excerpt_en || article.excerpt
  const rawContent = stripImageCredits(article.content_en || article.content)
  const cat        = article.category || 'AI'
  const catSlugEN  = CAT_SLUG_EN[cat] || slugifyCategory(cat)
  const catLabelEN = CAT_EN[cat] || cat
  const catSection = CAT_SECTION_EN[cat] || cat
  const url        = `https://www.newstide.news/en/article/${article.slug_en}`
  const urlES      = `https://www.newstide.news/articulo/${article.slug}`
  const keywords   = buildKeywords(cat, rawTitle, article.keyword)

  const citations      = extractCitations(rawContent)
  const visibleSources = extractVisibleSources(rawContent)
  const faqs           = extractFAQs(rawContent)
  const howToSteps     = extractHowToSteps(rawContent, rawTitle)
  const softwareMentions = extractSoftwareMentions(rawTitle)

  // Prefer the persisted related_articles column (computed once at publish time
  // by compute_related_articles() in pipeline.py); only entries with an EN slug
  // are usable here. Falls back to a live query for articles published before
  // that column existed.
  const persistedRelated: RelatedArticleEN[] = parseRelatedArticles(article.related_articles)
    .filter((r): r is RelatedArticleEN => !!r.slug_en && !!(r.title_en || r.title))

  let relatedEN: RelatedArticleEN[] = persistedRelated.slice(0, 4)
  if (relatedEN.length === 0) {
    const { data: related } = await supabase
      .from('articles')
      .select('title_en, title, slug_en, category')
      .eq('category', cat)
      .not('slug_en', 'is', null)
      .neq('slug_en', article.slug_en)
      .order('published_at', { ascending: false })
      .limit(4)
    relatedEN = related || []
  }

  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'NewsArticle',
    headline: rawTitle,
    description: rawExcerpt,
    url,
    datePublished: article.published_at,
    dateModified: article.updated_at || article.published_at,
    inLanguage: 'en',
    isAccessibleForFree: true,
    speakable: {
      '@type': 'SpeakableSpecification',
      cssSelector: ['.article-main-title', '.article-byline'],
    },
    image: article.cover_image_url
      ? { '@type': 'ImageObject', url: article.cover_image_url, width: 1200, height: 630 }
      : { '@type': 'ImageObject', url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630 },
    author: {
      '@type': 'Person',
      '@id': AUTHOR_PAGE_EN,
      name: 'Javier Valencia',
      url: AUTHOR_PAGE_EN,
      jobTitle: 'Founder & Editor-in-Chief',
      worksFor: { '@id': 'https://www.newstide.news/#organization' },
    },
    publisher: { '@id': 'https://www.newstide.news/#organization' },
    isPartOf: { '@id': 'https://www.newstide.news/en#website' },
    articleSection: catSection,
    keywords,
    mainEntityOfPage: { '@type': 'WebPage', '@id': url },
    ...(citations.length > 0 && { citation: citations }),
    ...(softwareMentions.length > 0 && {
      mentions: softwareMentions.map((m) => ({ '@type': 'SoftwareApplication', name: m.name })),
    }),
  }

  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home',       item: 'https://www.newstide.news/en' },
      { '@type': 'ListItem', position: 2, name: catLabelEN,   item: `https://www.newstide.news/en/articles/${catSlugEN}` },
      { '@type': 'ListItem', position: 3, name: rawTitle,     item: url },
    ],
  }

  const faqSchema = faqs.length > 0 ? {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map(({ question, answer }) => ({
      '@type': 'Question',
      name: question,
      acceptedAnswer: { '@type': 'Answer', text: answer },
    })),
  } : null

  const howToSchema = howToSteps.length > 0 ? {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: rawTitle,
    step: howToSteps.map(({ name, text }) => ({ '@type': 'HowToStep', name, text })),
  } : null

  return (
    <main className="article-page">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }} />
      {faqSchema && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }} />
      )}
      {howToSchema && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }} />
      )}

      {article.cover_image_url && (
        <div className="article-hero">
          {/* Cover image: next/image with priority for LCP + fill to reserve space and prevent CLS */}
          <div style={{ position: 'absolute', inset: 0 }}>
            <Image
              src={article.cover_image_url}
              alt={rawTitle}
              fill
              priority
              sizes="100vw"
              style={{ objectFit: 'cover' }}
            />
          </div>
          <div className="article-hero-overlay" />
          <div className="container">
            <div className="article-header">
              <div className="article-meta-top">
                <Badge cat={cat} />
                <span className="meta-sep">·</span>
                <span>{formatDate(article.published_at)}</span>
              </div>
              <h1 className="article-main-title">{rawTitle}</h1>
              <p className="article-byline">By Javier Valencia · NewsTide</p>
            </div>
          </div>
        </div>
      )}

      {!article.cover_image_url && (
        <div className="container page-main">
          <div style={{ paddingTop: 48 }}>
            <div className="article-meta-top">
              <Badge cat={cat} />
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{formatDate(article.published_at)}</span>
            </div>
            <h1 className="article-main-title" style={{ marginTop: 16 }}>{rawTitle}</h1>
            <p className="article-byline" style={{ fontSize: 14, color: 'var(--muted)', marginTop: 8 }}>By Javier Valencia · NewsTide</p>
          </div>
        </div>
      )}

      <div className="container" style={{ paddingTop: 16, paddingBottom: 0 }}>
        <nav aria-label="Breadcrumb" style={{ fontSize: 13, color: 'var(--muted)', display: 'flex', gap: 6, alignItems: 'center' }}>
          <Link href="/en" style={{ color: 'var(--muted)' }}>Home</Link>
          <span>›</span>
          <Link href={`/en/articles/${catSlugEN}`} style={{ color: 'var(--muted)' }}>{catLabelEN}</Link>
          <span>›</span>
          <span style={{ color: 'var(--text)' }}>{rawTitle.length > 50 ? rawTitle.substring(0, 50) + '…' : rawTitle}</span>
        </nav>
      </div>

      <div className="container">
        <div className="article-body-grid">
          <article className="article-body-wrap" style={{ padding: 0 }}>
            {rawExcerpt && (
              <p style={{
                fontSize: 18, lineHeight: 1.65, color: 'var(--muted)',
                marginBottom: 32, fontWeight: 300, borderLeft: '3px solid var(--cyan)',
                paddingLeft: 20,
              }}>
                {rawExcerpt}
              </p>
            )}

            <div className="article-content">
              <ReactMarkdown>{rawContent}</ReactMarkdown>
            </div>

            {visibleSources.length > 0 && (
              <section aria-label="Sources" style={{ marginTop: 48, paddingTop: 28, borderTop: '1px solid var(--border)' }}>
                <h2 style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 14 }}>Sources</h2>
                <ol style={{ margin: 0, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {visibleSources.map((s, i) => (
                    <li key={i} style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.5 }}>
                      <a href={s.href} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)', textDecoration: 'none' }}>
                        {s.label}
                      </a>
                    </li>
                  ))}
                </ol>
              </section>
            )}

            {relatedEN.length > 0 && (
              <div style={{ marginTop: 48 }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 20, color: 'var(--text)' }}>More in {catLabelEN}</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {relatedEN.map((r) => (
                    <Link key={r.slug_en} href={`/en/article/${r.slug_en}`}
                      style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '12px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, textDecoration: 'none', transition: 'border-color 0.2s' }}>
                      <span style={{ fontSize: 18, flexShrink: 0 }}>→</span>
                      <span style={{ fontSize: 14, color: 'var(--text)', fontWeight: 500, lineHeight: 1.4 }}>{r.title_en || r.title}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div style={{ marginTop: 40, paddingTop: 32, borderTop: '1px solid var(--border)' }}>
              <p style={{ fontSize: 13, color: 'var(--muted)' }}>
                🇪🇸 Also available in Spanish: <Link href={urlES} style={{ color: 'var(--cyan)' }}>Leer en español</Link>
              </p>
            </div>

            <ShareButtons url={url} title={rawTitle} />
            <NewsletterForm />
          </article>

          <aside>
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
              <p style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 16 }}>More in {catLabelEN}</p>
              <Link
                href={`/en/articles/${catSlugEN}`}
                style={{ display: 'block', padding: '10px 14px', background: 'rgba(110,207,202,0.06)', border: '1px solid rgba(110,207,202,0.15)', borderRadius: 8, fontSize: 13, color: 'var(--cyan)', textDecoration: 'none', textAlign: 'center' }}
              >
                Browse all {catLabelEN} articles →
              </Link>
            </div>

            <div style={{ marginTop: 20, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
              <p style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Written by</p>
              <Link href={AUTHOR_PAGE_EN} style={{ display: 'flex', gap: 12, alignItems: 'center', textDecoration: 'none' }}>
                <div style={{
                  width: 40, height: 40, borderRadius: '50%',
                  background: 'linear-gradient(135deg, var(--cyan), #9b8cef)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 14, fontWeight: 800, color: 'var(--bg)', flexShrink: 0,
                }}>JV</div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>Javier Valencia</div>
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>Founder & Editor-in-Chief</div>
                </div>
              </Link>
            </div>
          </aside>
        </div>
      </div>
    </main>
  )
}
