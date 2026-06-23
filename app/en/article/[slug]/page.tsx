import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { notFound, redirect } from 'next/navigation'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'

export const revalidate = 3600

const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef',
  'Herramientas': '#e8d5a3', 'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c'
}

const CAT_EN: Record<string, string> = {
  'IA': 'AI',
  'Tutoriales': 'Tutorials',
  'Herramientas': 'Tools',
  'Startups': 'Startups',
  'Noticias': 'News',
}

const CAT_SECTION_EN: Record<string, string> = {
  'IA': 'Artificial Intelligence',
  'Tutoriales': 'Tutorials',
  'Herramientas': 'Tools & Technology',
  'Startups': 'Startups',
  'Noticias': 'News',
}

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
    .select('title, title_en, excerpt, excerpt_en, slug, slug_en, category, published_at, cover_image_url, author')
    .eq('slug_en', slug)
    .maybeSingle()

  if (!article) return { title: 'Article not found' }

  const title = article.title_en || article.title
  const description = article.excerpt_en || article.excerpt || 'Technology, AI and trends for founders, developers and professionals.'
  const enSlug = article.slug_en
  const url = `https://www.newstide.news/en/article/${enSlug}`
  const urlES = `https://www.newstide.news/articulo/${article.slug}`
  const images = article.cover_image_url
    ? [{ url: article.cover_image_url, width: 1200, height: 630, alt: title }]
    : []

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
      title, description, url,
      siteName: 'NewsTide', locale: 'en_US', type: 'article',
      publishedTime: article.published_at,
      authors: [article.author],
      images,
    },
    twitter: {
      card: 'summary_large_image', title, description,
      ...(article.cover_image_url ? { images: [article.cover_image_url] } : {}),
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
    .select('*')
    .eq('slug_en', slug)
    .maybeSingle()

  if (!article) {
    const { data: bySlugEs } = await supabase
      .from('articles')
      .select('slug_en')
      .eq('slug', slug)
      .maybeSingle()

    if (bySlugEs?.slug_en) {
      redirect(`/en/article/${bySlugEs.slug_en}`)
    }

    notFound()
  }

  const title   = article.title_en   || article.title
  const content = article.content_en || article.content
  const excerpt = article.excerpt_en || article.excerpt
  const enSlug  = article.slug_en
  const url     = `https://www.newstide.news/en/article/${enSlug}`
  const urlES   = `https://www.newstide.news/articulo/${article.slug}`

  const authorSlug = article.author?.toLowerCase().replace(/ /g, '-').normalize('NFD').replace(/[\u0300-\u036f]/g, '')

  const { data: related } = await supabase
    .from('articles')
    .select('title_en, title, slug_en, slug, category, published_at')
    .eq('category', article.category)
    .neq('slug', article.slug)
    .not('slug_en', 'is', null)
    .order('published_at', { ascending: false })
    .limit(4)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'NewsArticle',
    headline: title,
    description: excerpt || '',
    url,
    datePublished: article.published_at,
    dateModified: article.published_at,
    inLanguage: 'en',
    isAccessibleForFree: true,
    articleSection: CAT_SECTION_EN[article.category] || article.category,
    speakable: {
      '@type': 'SpeakableSpecification',
      cssSelector: ['.article-main-title', '.article-byline'],
    },
    author: {
      '@type': 'Person',
      name: article.author,
      url: `https://www.newstide.news/en/authors/${authorSlug}`,
    },
    publisher: {
      '@type': 'NewsMediaOrganization',
      '@id': 'https://www.newstide.news/#organization',
      name: 'NewsTide',
      url: 'https://www.newstide.news',
      logo: {
        '@type': 'ImageObject',
        url: 'https://www.newstide.news/favicon-192x192.png',
        width: 192,
        height: 192,
      },
    },
    ...(article.cover_image_url ? {
      image: {
        '@type': 'ImageObject',
        url: article.cover_image_url,
        width: 1200,
        height: 630,
      },
    } : {}),
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': url,
    },
  }

  return (
    <div className="article-page" lang="en">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      {/* hreflang links managed via generateMetadata alternates — no duplicates here */}

      {/* HERO */}
      <div className="article-hero" style={{ background: article.image_gradient }}>
        <div className="article-hero-overlay" />
        <div className="container">
          <div className="article-header">
            <div className="article-meta-top">
              <Link href="/en" style={{ color: 'var(--muted)' }}>Home</Link>
              <span className="meta-sep">/</span>
              <span>{CAT_EN[article.category] || article.category}</span>
            </div>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
              <Badge cat={article.category} />
              <span className="meta-sep">·</span>
              <Link href={`/en/authors/${authorSlug}`} style={{ fontSize: 13, color: 'var(--muted)', textDecoration: 'none' }}>{article.author}</Link>
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

      {/* BODY + SIDEBAR */}
      <div className="container">
        <div className="article-body-grid">
          <article>
            <ReactMarkdown
              components={{
                h2: ({ children }) => (
                  <h2 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.03em', margin: '40px 0 16px', color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: 10 }}>{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 600, margin: '28px 0 12px', color: 'var(--text)' }}>{children}</h3>
                ),
                p: ({ children }) => (
                  <p style={{ fontSize: 17, lineHeight: 1.8, color: 'rgba(240,240,238,0.85)', marginBottom: 20 }}>{children}</p>
                ),
                img: ({ src, alt }) => (
                  src ? (
                    <span style={{ display: 'block', margin: '32px 0' }}>
                      <img src={src} alt={alt || ''} style={{ width: '100%', borderRadius: 12, objectFit: 'cover', maxHeight: 480, display: 'block', border: '1px solid var(--border)' }} loading="lazy" />
                    </span>
                  ) : null
                ),
                ul: ({ children }) => <ul style={{ margin: '16px 0 20px 24px' }}>{children}</ul>,
                ol: ({ children }) => <ol style={{ margin: '16px 0 20px 24px' }}>{children}</ol>,
                li: ({ children }) => <li style={{ fontSize: 16, lineHeight: 1.7, color: 'rgba(240,240,238,0.8)', marginBottom: 8 }}>{children}</li>,
                strong: ({ children }) => <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{children}</strong>,
                blockquote: ({ children }) => (
                  <blockquote style={{ borderLeft: '3px solid var(--cyan)', paddingLeft: 20, margin: '24px 0', color: 'var(--muted)', fontStyle: 'italic' }}>{children}</blockquote>
                ),
                code: ({ children }) => (
                  <code style={{ fontFamily: 'var(--mono)', fontSize: 13, background: 'var(--surface)', border: '1px solid var(--border)', padding: '2px 7px', borderRadius: 5, color: 'var(--cyan)' }}>{children}</code>
                ),
                hr: () => <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '40px 0' }} />,
              }}
            >
              {content}
            </ReactMarkdown>

            <div style={{
              marginTop: 48, padding: '16px 20px',
              background: 'rgba(110,207,202,0.05)',
              border: '1px solid rgba(110,207,202,0.15)',
              borderRadius: 10, fontSize: 12, color: 'var(--muted)', lineHeight: 1.6
            }}>
              <strong style={{ color: 'var(--cyan)' }}>Editorial note:</strong> This article was generated with AI assistance and reviewed by the NewsTide editorial team to ensure accuracy and relevance. <Link href="/en/editorial-policy" style={{ color: 'var(--cyan)' }}>Read our editorial policy.</Link>
            </div>

            {related && related.length > 0 && (
              <div style={{ marginTop: 48 }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 20, color: 'var(--text)' }}>More on {CAT_EN[article.category] || article.category}</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {related.map((r) => (
                    <Link
                      key={r.slug_en || r.slug}
                      href={`/en/article/${r.slug_en || r.slug}`}
                      style={{
                        display: 'flex', gap: 12, alignItems: 'center',
                        padding: '12px 16px',
                        background: 'var(--surface)', border: '1px solid var(--border)',
                        borderRadius: 10, textDecoration: 'none',
                        transition: 'border-color 0.2s'
                      }}
                    >
                      <span style={{ fontSize: 18, flexShrink: 0 }}>→</span>
                      <span style={{ fontSize: 14, color: 'var(--text)', fontWeight: 500, lineHeight: 1.4 }}>{r.title_en || r.title}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div style={{ marginTop: 40, paddingTop: 32, borderTop: '1px solid var(--border)' }}>
              <Link href="/en" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--cyan)', fontSize: 14, fontWeight: 600 }}>
                ← Back to home
              </Link>
            </div>
          </article>

          <aside>
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Author</div>
              <Link href={`/en/authors/${authorSlug}`} style={{ textDecoration: 'none' }}>
                <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8, color: 'var(--text)' }}>{article.author}</div>
              </Link>
              <Badge cat={article.category} />
            </div>
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Details</div>
              <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 2.2 }}>
                <div>📅 {formatDate(article.published_at)}</div>
                <div>⏱ {article.reading_time} min read</div>
                <div>🏷 {CAT_EN[article.category] || article.category}</div>
              </div>
            </div>
            <div style={{ background: 'linear-gradient(135deg, rgba(110,207,202,0.08), rgba(155,140,239,0.08))', border: '1px solid rgba(110,207,202,0.2)', borderRadius: 14, padding: 24 }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 8 }}>✉️ Newsletter</div>
              <p style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6, marginBottom: 16 }}>The best stories of the week in your inbox.</p>
              <input type="email" placeholder="you@email.com" className="sidebar-email" />
              <button className="sidebar-sub-btn">Subscribe for free</button>
            </div>
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginTop: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Share</div>
              <div style={{ display: 'flex', gap: 10 }}>
                {['𝕏', 'in', '🔗'].map((icon, i) => (
                  <button key={i} style={{ flex: 1, padding: '8px 0', borderRadius: 8, background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--muted)', fontSize: i === 2 ? 14 : 13, fontWeight: 600, cursor: 'pointer', transition: 'border-color 0.2s, color 0.2s' }}>{icon}</button>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
