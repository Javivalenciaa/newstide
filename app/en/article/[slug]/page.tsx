import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { notFound, permanentRedirect } from 'next/navigation'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import NewsletterForm from '@/components/NewsletterForm'
import ShareButtons from '@/components/ShareButtons'

export const revalidate = 300

const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef',
  'Herramientas': '#e8d5a3', 'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c'
}

const CAT_EN: Record<string, string> = {
  'IA': 'AI', 'Tutoriales': 'Tutorials',
  'Herramientas': 'Tools', 'Startups': 'Startups', 'Noticias': 'News',
}

const CAT_SLUG_EN: Record<string, string> = {
  'IA': 'ai', 'Tutoriales': 'tutorials',
  'Herramientas': 'tools', 'Startups': 'startups', 'Noticias': 'news',
}

const CAT_SECTION_EN: Record<string, string> = {
  'IA': 'Artificial Intelligence', 'Tutoriales': 'Tutorials',
  'Herramientas': 'Tools & Technology', 'Startups': 'Startups', 'Noticias': 'News',
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

// seoTitle returns bare title only; template: '%s | NewsTide' in layout adds the suffix
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

// Build dynamic keywords from article data: category + title tokens + keyword field
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

/**
 * Extract the first N markdown links from content that look like real sources.
 * Returns schema.org CreativeWork citation objects.
 * Only includes links whose href starts with https:// (no relative links).
 */
function extractCitations(content: string, max = 5): Array<{ '@type': string; url: string; name: string }> {
  if (!content) return []
  // Match [label](https://...) patterns in markdown
  const mdLinkRe = /\[([^\]]{3,80})\]\((https:\/\/[^)]+)\)/g
  const results: Array<{ '@type': string; url: string; name: string }> = []
  let m: RegExpExecArray | null
  while ((m = mdLinkRe.exec(content)) !== null && results.length < max) {
    const label = m[1].trim()
    const href  = m[2].trim()
    // Skip internal links
    if (href.includes('newstide.news')) continue
    results.push({ '@type': 'CreativeWork', name: label, url: href })
  }
  return results
}

/**
 * Extract the first N markdown links to render as a visible Sources section.
 */
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

export async function generateStaticParams() {
  const { data } = await supabase.from('articles').select('slug_en').not('slug_en', 'is', null)
  return (data || []).map((a) => ({ slug: a.slug_en }))
}

export async function generateMetadata(
  { params }: { params: Promise<{ slug: string }> }
): Promise<Metadata> {
  const { slug } = await params
  const { data: article } = await supabase
    .from('articles')
    .select('title, title_en, excerpt, excerpt_en, slug, slug_en, category, published_at, updated_at, cover_image_url')
    .eq('slug_en', slug)
    .maybeSingle()

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
  const url    = `https://www.newstide.news/en/article/${enSlug}`
  const urlES  = `https://www.newstide.news/articulo/${article.slug}`
  const images = article.cover_image_url
    ? [{ url: article.cover_image_url, width: 1200, height: 630, alt: rawTitle }]
    : [{ url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630, alt: 'NewsTide' }]

  return {
    title,
    description,
    alternates: {
      canonical: url,
      languages: { 'en': url, 'es': urlES, 'x-default': url },
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

  const { data: article } = await supabase
    .from('articles')
    .select('id, title, title_en, excerpt, excerpt_en, content, content_en, slug, slug_en, category, published_at, updated_at, cover_image_url, author, keyword')
    .eq('slug_en', slug)
    .maybeSingle()

  if (!article) notFound()

  if (!article.slug_en) permanentRedirect(`/articulo/${article.slug}`)

  const rawTitle   = article.title_en   || article.title
  const rawExcerpt = article.excerpt_en || article.excerpt
  const rawContent = article.content_en || article.content
  const cat        = article.category || 'AI'
  const catSlugEN  = CAT_SLUG_EN[cat] || 'ai'
  const catLabelEN = CAT_EN[cat] || cat
  const catSection = CAT_SECTION_EN[cat] || 'Technology'
  const url        = `https://www.newstide.news/en/article/${article.slug_en}`
  const urlES      = `https://www.newstide.news/articulo/${article.slug}`
  const keywords   = buildKeywords(cat, rawTitle, article.keyword)

  // E-E-A-T: extract real outbound citations from article content
  const citations     = extractCitations(rawContent)
  const visibleSources = extractVisibleSources(rawContent)

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
      // Points to EN canonical author page — consistent @id across all EN article schemas
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
    // E-E-A-T: citation array — populated from real outbound links in the article body
    ...(citations.length > 0 && { citation: citations }),
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

  return (
    <main className="article-page">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }} />

      {/* HERO */}
      {article.cover_image_url && (
        <div className="article-hero">
          <img
            src={article.cover_image_url}
            alt={rawTitle}
            style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }}
          />
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

      {/* BREADCRUMB */}
      <div className="container" style={{ paddingTop: 16, paddingBottom: 0 }}>
        <nav aria-label="Breadcrumb" style={{ fontSize: 13, color: 'var(--muted)', display: 'flex', gap: 6, alignItems: 'center' }}>
          <Link href="/en" style={{ color: 'var(--muted)' }}>Home</Link>
          <span>›</span>
          <Link href={`/en/articles/${catSlugEN}`} style={{ color: 'var(--muted)' }}>{catLabelEN}</Link>
          <span>›</span>
          <span style={{ color: 'var(--text)' }}>{rawTitle.length > 50 ? rawTitle.substring(0, 50) + '…' : rawTitle}</span>
        </nav>
      </div>

      {/* BODY */}
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

            {/* ── E-E-A-T: Visible Sources section ─────────────────────────────
                Only rendered when the article content contains real outbound links.
                This makes sources visible to both readers and Google crawlers,
                which is a direct EEAT trust signal. */}
            {visibleSources.length > 0 && (
              <section
                aria-label="Sources"
                style={{
                  marginTop: 48,
                  paddingTop: 28,
                  borderTop: '1px solid var(--border)',
                }}
              >
                <h2 style={{
                  fontSize: 13,
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: 'var(--muted)',
                  marginBottom: 14,
                }}>
                  Sources
                </h2>
                <ol style={{ margin: 0, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {visibleSources.map((s, i) => (
                    <li key={i} style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.5 }}>
                      <a
                        href={s.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: 'var(--cyan)', textDecoration: 'none' }}
                      >
                        {s.label}
                      </a>
                    </li>
                  ))}
                </ol>
              </section>
            )}

            {/* HREFLANG notice */}
            <div style={{ marginTop: 40, paddingTop: 32, borderTop: '1px solid var(--border)' }}>
              <p style={{ fontSize: 13, color: 'var(--muted)' }}>
                🇪🇸 Also available in Spanish: <Link href={urlES} style={{ color: 'var(--cyan)' }}>Leer en español</Link>
              </p>
            </div>

            <ShareButtons url={url} title={rawTitle} />
            <NewsletterForm />
          </article>

          {/* SIDEBAR */}
          <aside>
            <div style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 12, padding: 24,
            }}>
              <p style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 16 }}>More in {catLabelEN}</p>
              <Link
                href={`/en/articles/${catSlugEN}`}
                style={{
                  display: 'block', padding: '10px 14px', background: 'rgba(110,207,202,0.06)',
                  border: '1px solid rgba(110,207,202,0.15)', borderRadius: 8,
                  fontSize: 13, color: 'var(--cyan)', textDecoration: 'none', textAlign: 'center',
                }}
              >
                Browse all {catLabelEN} articles →
              </Link>
            </div>

            {/* E-E-A-T: Author card in sidebar — visible trust signal */}
            <div style={{
              marginTop: 20,
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 12, padding: 24,
            }}>
              <p style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Written by</p>
              <Link
                href={AUTHOR_PAGE_EN}
                style={{ display: 'flex', gap: 12, alignItems: 'center', textDecoration: 'none' }}
              >
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
