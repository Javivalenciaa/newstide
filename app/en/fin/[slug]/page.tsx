import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import NewsletterForm from '@/components/NewsletterForm'
import ShareButtons from '@/components/ShareButtons'

export const revalidate = 300
export const dynamicParams = true

const FIN_CAT_COLORS: Record<string, string> = {
  'Saving Money':  '#6ecfca',
  'Budgeting':     '#9b8cef',
  'Investing':     '#7ecf9b',
  'Debt':          '#ef6c6c',
  'Credit':        '#e8d5a3',
  'Side Hustles':  '#f0a050',
}

const AUTHOR_SLUG   = 'javier-valencia'
const AUTHOR_PAGE_EN = `https://www.newstide.news/en/authors/${AUTHOR_SLUG}`

function Badge({ cat }: { cat: string }) {
  const color = FIN_CAT_COLORS[cat] || '#6ecfca'
  return (
    <span style={{
      display: 'inline-block', padding: '4px 10px', borderRadius: '6px',
      fontSize: '10px', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase',
      background: `${color}18`, color, border: `1px solid ${color}30`,
    }}>{cat}</span>
  )
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
}

function seoTitle(title: string, siteName = 'NewsTide'): string {
  const max = 60 - siteName.length - 3
  if (title.length <= max) return `${title} | ${siteName}`
  const cut = title.substring(0, max)
  const lastSpace = cut.lastIndexOf(' ')
  return `${cut.substring(0, lastSpace > 20 ? lastSpace : max)} | ${siteName}`
}

function seoDescription(excerpt: string, fallback: string): string {
  const text = excerpt || fallback
  if (text.length <= 155) return text
  const cut = text.substring(0, 152)
  const lastSpace = cut.lastIndexOf(' ')
  return `${cut.substring(0, lastSpace > 50 ? lastSpace : 152)}...`
}

export async function generateStaticParams() {
  const { data } = await supabase.from('finance_articles').select('slug_en').not('slug_en', 'is', null)
  return (data || []).map((a) => ({ slug: a.slug_en }))
}

export async function generateMetadata(
  { params }: { params: Promise<{ slug: string }> }
): Promise<Metadata> {
  const { slug } = await params
  const { data: article } = await supabase
    .from('finance_articles')
    .select('title, title_en, excerpt, excerpt_en, slug_en, category, published_at, cover_image_url')
    .eq('slug_en', slug)
    .maybeSingle()

  if (!article) return {
    title: 'Article not found | NewsTide',
    description: 'This content is not available on NewsTide.'
  }

  const rawTitle    = article.title_en || article.title
  const title       = seoTitle(rawTitle)
  const description = seoDescription(
    article.excerpt_en || article.excerpt,
    'Practical personal finance guide on NewsTide.'
  )
  const url    = `https://www.newstide.news/en/fin/${article.slug_en}`
  const images = article.cover_image_url
    ? [{ url: article.cover_image_url, width: 1200, height: 630, alt: rawTitle }]
    : [{ url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630, alt: 'NewsTide Finance' }]

  return {
    title,
    description,
    alternates: {
      canonical: url,
      languages: { 'en': url, 'x-default': url },
    },
    openGraph: {
      title: rawTitle,
      description,
      url,
      siteName: 'NewsTide',
      locale: 'en_US',
      type: 'article',
      publishedTime: article.published_at,
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

export default async function FinanceArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params

  const { data: article } = await supabase
    .from('finance_articles')
    .select('*')
    .eq('slug_en', slug)
    .maybeSingle()

  if (!article) notFound()

  const title   = article.title_en   || article.title
  const content = article.content_en || article.content
  const excerpt = article.excerpt_en || article.excerpt
  const url     = `https://www.newstide.news/en/fin/${article.slug_en}`

  const { data: related } = await supabase
    .from('finance_articles')
    .select('title_en, title, slug_en, category, published_at')
    .eq('category', article.category)
    .neq('slug_en', article.slug_en)
    .order('published_at', { ascending: false })
    .limit(6)

  const { data: latest } = await supabase
    .from('finance_articles')
    .select('title_en, title, slug_en')
    .neq('slug_en', article.slug_en)
    .order('published_at', { ascending: false })
    .limit(5)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: title,
    description: excerpt || '',
    url,
    datePublished: article.published_at,
    dateModified: article.updated_at || article.published_at,
    inLanguage: 'en',
    isAccessibleForFree: true,
    articleSection: article.category,
    author: {
      '@type': 'Person',
      name: 'Javier Valencia',
      url: AUTHOR_PAGE_EN,
      jobTitle: 'Founder & Editor in Chief',
    },
    publisher: {
      '@type': 'NewsMediaOrganization',
      '@id': 'https://www.newstide.news/#organization',
      name: 'NewsTide',
      url: 'https://www.newstide.news',
      logo: { '@type': 'ImageObject', url: 'https://www.newstide.news/favicon-192x192.png', width: 192, height: 192 },
    },
    image: article.cover_image_url
      ? { '@type': 'ImageObject', url: article.cover_image_url, width: 1200, height: 630 }
      : { '@type': 'ImageObject', url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630 },
    mainEntityOfPage: { '@type': 'WebPage', '@id': url },
  }

  return (
    <div className="article-page" lang="en">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      <div className="article-hero" style={{ background: article.image_gradient || 'linear-gradient(135deg,#0d2a1a,#0a1a0a)' }}>
        <div className="article-hero-overlay" />
        <div className="container">
          <div className="article-header">
            <nav aria-label="Breadcrumb" style={{ marginBottom: 16 }}>
              <ol style={{ display: 'flex', alignItems: 'center', gap: 6, listStyle: 'none', padding: 0, margin: 0, flexWrap: 'wrap' }}>
                <li><Link href="/en" style={{ fontSize: 13, color: 'var(--muted)' }}>Home</Link></li>
                <li style={{ color: 'var(--faint)', fontSize: 13 }}>/</li>
                <li><Link href="/en/fin" style={{ fontSize: 13, color: 'var(--muted)' }}>Personal Finance</Link></li>
                <li style={{ color: 'var(--faint)', fontSize: 13 }}>/</li>
                <li style={{ fontSize: 13, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200 }} aria-current="page">{title}</li>
              </ol>
            </nav>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
              <Badge cat={article.category} />
              <span className="meta-sep">·</span>
              <Link href={AUTHOR_PAGE_EN} style={{ fontSize: 13, color: 'var(--muted)', textDecoration: 'none', fontWeight: 500 }}>Javier Valencia</Link>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 12, color: 'var(--faint)' }}>Reviewed by NewsTide Finance</span>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{formatDate(article.published_at)}</span>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{article.reading_time} min read</span>
            </div>
            <h1 className="article-main-title">{title}</h1>
            <p className="article-byline">{excerpt}</p>
          </div>
        </div>
      </div>

      <div className="container">
        <div className="article-body-grid">
          <article>
            {article.cover_image_url && (
              <div style={{ margin: '0 0 32px' }}>
                <img
                  src={article.cover_image_url}
                  alt={title}
                  style={{ width: '100%', height: 'auto', borderRadius: 12, objectFit: 'cover', maxHeight: 480, display: 'block', border: '1px solid var(--border)' }}
                />
              </div>
            )}
            <ReactMarkdown
              components={{
                h2: ({ children }) => (<h2 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.03em', margin: '40px 0 16px', color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: 10 }}>{children}</h2>),
                h3: ({ children }) => (<h3 style={{ fontSize: '1.15rem', fontWeight: 600, margin: '28px 0 12px', color: 'var(--text)' }}>{children}</h3>),
                p: ({ children }) => (<p style={{ fontSize: 17, lineHeight: 1.8, color: 'rgba(240,240,238,0.85)', marginBottom: 20 }}>{children}</p>),
                img: ({ src, alt }) => {
                  const cleanAlt = (alt && alt.length > 10 && !alt.startsWith('a ') && !alt.startsWith('an '))
                    ? alt : `${title} — NewsTide Finance`
                  return src ? (
                    <span style={{ display: 'block', margin: '32px 0' }}>
                      <img src={src} alt={cleanAlt} loading="lazy" style={{ width: '100%', height: 'auto', borderRadius: 12, objectFit: 'cover', maxHeight: 480, display: 'block', border: '1px solid var(--border)' }} />
                    </span>
                  ) : null
                },
                ul: ({ children }) => <ul style={{ margin: '16px 0 20px 24px' }}>{children}</ul>,
                ol: ({ children }) => <ol style={{ margin: '16px 0 20px 24px' }}>{children}</ol>,
                li: ({ children }) => <li style={{ fontSize: 16, lineHeight: 1.7, color: 'rgba(240,240,238,0.8)', marginBottom: 8 }}>{children}</li>,
                strong: ({ children }) => <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{children}</strong>,
                blockquote: ({ children }) => (<blockquote style={{ borderLeft: '3px solid var(--cyan)', paddingLeft: 20, margin: '24px 0', color: 'var(--muted)', fontStyle: 'italic' }}>{children}</blockquote>),
                code: ({ children }) => (<code style={{ fontFamily: 'var(--mono)', fontSize: 13, background: 'var(--surface)', border: '1px solid var(--border)', padding: '2px 7px', borderRadius: 5, color: 'var(--cyan)' }}>{children}</code>),
                hr: () => <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '40px 0' }} />,
              }}
            >
              {content}
            </ReactMarkdown>

            <div style={{ marginTop: 48, padding: '16px 20px', background: 'rgba(110,207,202,0.05)', border: '1px solid rgba(110,207,202,0.15)', borderRadius: 10, fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
              <strong style={{ color: 'var(--cyan)' }}>Editorial note:</strong> This article was produced with AI assistance and reviewed by Javier Valencia for accuracy. Content is for informational purposes only — not financial advice. <Link href="/en/editorial-policy" style={{ color: 'var(--cyan)' }}>Read our editorial policy.</Link>
            </div>

            {related && related.length > 0 && (
              <div style={{ marginTop: 48 }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 20, color: 'var(--text)' }}>More on {article.category}</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {related.map((r) => (
                    <Link key={r.slug_en} href={`/en/fin/${r.slug_en}`}
                      style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '12px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, textDecoration: 'none', transition: 'border-color 0.2s' }}>
                      <span style={{ fontSize: 18, flexShrink: 0 }}>→</span>
                      <span style={{ fontSize: 14, color: 'var(--text)', fontWeight: 500, lineHeight: 1.4 }}>{r.title_en || r.title}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div style={{ marginTop: 40, paddingTop: 32, borderTop: '1px solid var(--border)', display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
              <Link href="/en/fin" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--cyan)', fontSize: 14, fontWeight: 600 }}>← Back to Finance</Link>
            </div>
          </article>

          <aside>
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Author</div>
              <Link href={AUTHOR_PAGE_EN} style={{ textDecoration: 'none' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, var(--cyan), #9b8cef)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 800, color: 'var(--bg)', flexShrink: 0 }}>JV</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)' }}>Javier Valencia</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>Reviewed by NewsTide Finance</div>
                  </div>
                </div>
              </Link>
              <Link href="/en/editorial-policy" style={{ fontSize: 12, color: 'var(--cyan)' }}>Editorial policy →</Link>
            </div>

            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Details</div>
              <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 2.2 }}>
                <div>📅 {formatDate(article.published_at)}</div>
                <div>⏱ {article.reading_time} min read</div>
                <div>🏷 <Badge cat={article.category} /></div>
              </div>
            </div>

            {latest && latest.length > 0 && (
              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
                <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 14 }}>Latest Finance</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {latest.map((a) => (
                    <Link key={a.slug_en} href={`/en/fin/${a.slug_en}`}
                      style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.4, textDecoration: 'none', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                      {a.title_en || a.title}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div style={{ background: 'linear-gradient(135deg, rgba(110,207,202,0.08), rgba(155,140,239,0.08))', border: '1px solid rgba(110,207,202,0.2)', borderRadius: 14, padding: 24 }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 8 }}>✉️ Newsletter</div>
              <p style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6, marginBottom: 16 }}>Weekly finance tips in your inbox.</p>
              <NewsletterForm compact />
            </div>

            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginTop: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Share</div>
              <ShareButtons url={url} title={title} />
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
