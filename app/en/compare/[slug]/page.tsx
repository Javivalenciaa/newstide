import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import NewsletterForm from '@/components/NewsletterForm'
import ShareButtons from '@/components/ShareButtons'

export const revalidate = 86400  // 24h — pSEO pages are evergreen, no need to revalidate often

const TEMPLATE_LABELS: Record<string, string> = {
  comparisons:      'Comparison',
  alternatives:     'Alternatives',
  guides:           'Guide',
  'for-profession': 'For Professionals',
}

const TEMPLATE_CATEGORY_COLOR: Record<string, string> = {
  comparisons:      '#6ecfca',
  alternatives:     '#9b8cef',
  guides:           '#7ecf9b',
  'for-profession': '#e8d5a3',
}

const AUTHOR_PAGE = 'https://www.newstide.news/en/authors/javier-valencia'

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
}

function seoTitle(title: string): string {
  const siteName = 'NewsTide'
  const max = 60 - siteName.length - 3
  if (title.length <= max) return `${title} | ${siteName}`
  const cut = title.substring(0, max)
  const lastSpace = cut.lastIndexOf(' ')
  return `${cut.substring(0, lastSpace > 20 ? lastSpace : max)} | ${siteName}`
}

function seoDesc(excerpt: string): string {
  if (!excerpt) return 'In-depth tech guide on NewsTide — trusted AI, startup and developer content.'
  if (excerpt.length <= 155) return excerpt
  const cut = excerpt.substring(0, 152)
  const ls  = cut.lastIndexOf(' ')
  return `${cut.substring(0, ls > 50 ? ls : 152)}...`
}

export async function generateStaticParams() {
  const { data } = await supabase.from('pseo_pages').select('slug')
  return (data || []).map((p) => ({ slug: p.slug }))
}

export async function generateMetadata(
  { params }: { params: Promise<{ slug: string }> }
): Promise<Metadata> {
  const { slug } = await params
  const { data: page } = await supabase
    .from('pseo_pages')
    .select('title, excerpt, slug, template, entity_a, entity_b, published_at')
    .eq('slug', slug)
    .maybeSingle()

  if (!page) return { title: 'Not Found | NewsTide' }

  const url = `https://www.newstide.news/en/compare/${slug}`

  return {
    title:       seoTitle(page.title),
    description: seoDesc(page.excerpt),
    alternates: {
      canonical: url,
      languages: { 'en': url, 'x-default': url },
    },
    openGraph: {
      title:       page.title,
      description: seoDesc(page.excerpt),
      url,
      siteName:    'NewsTide',
      locale:      'en_US',
      type:        'article',
      publishedTime: page.published_at,
      authors:     ['Javier Valencia'],
      images:      [{ url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630, alt: page.title }],
    },
    twitter: {
      card:        'summary_large_image',
      title:       page.title,
      description: seoDesc(page.excerpt),
      images:      ['https://www.newstide.news/og-image.png'],
    },
  }
}

export default async function PseoPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params

  const { data: page } = await supabase
    .from('pseo_pages')
    .select('*')
    .eq('slug', slug)
    .maybeSingle()

  if (!page) notFound()

  const url      = `https://www.newstide.news/en/compare/${slug}`
  const color    = TEMPLATE_CATEGORY_COLOR[page.template] || '#6ecfca'
  const catLabel = TEMPLATE_LABELS[page.template] || 'Guide'

  // Extract FAQs for FAQPage schema (H3 questions)
  const faqMatches = [...(page.content || '').matchAll(/^###\s+(.+\?)\s*\n+([^#]+)/gm)].slice(0, 5)
  const faqs = faqMatches.map((m) => ({
    question: m[1].trim(),
    answer:   m[2].replace(/\*\*/g, '').trim().substring(0, 300),
  }))

  // JSON-LD: Article
  const articleSchema = {
    '@context':          'https://schema.org',
    '@type':             'Article',
    headline:            page.title,
    description:         page.excerpt || '',
    url,
    datePublished:       page.published_at,
    dateModified:        page.updated_at || page.published_at,
    inLanguage:          'en',
    isAccessibleForFree: true,
    author: {
      '@type':    'Person',
      name:       'Javier Valencia',
      url:         AUTHOR_PAGE,
      jobTitle:   'Founder & Editor in Chief',
      worksFor:   { '@id': 'https://www.newstide.news/#organization' },
    },
    publisher:          { '@id': 'https://www.newstide.news/#organization' },
    image:              { '@type': 'ImageObject', url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630 },
    mainEntityOfPage:   { '@type': 'WebPage', '@id': url },
    isPartOf:           { '@id': 'https://www.newstide.news/#website' },
  }

  // JSON-LD: BreadcrumbList
  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type':    'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home',    item: 'https://www.newstide.news/en' },
      { '@type': 'ListItem', position: 2, name: 'Guides',  item: 'https://www.newstide.news/en/compare' },
      { '@type': 'ListItem', position: 3, name: page.title },
    ],
  }

  // JSON-LD: FAQPage (only if FAQs found)
  const faqSchema = faqs.length > 0 ? {
    '@context':  'https://schema.org',
    '@type':     'FAQPage',
    mainEntity:  faqs.map(({ question, answer }) => ({
      '@type':        'Question',
      name:            question,
      acceptedAnswer: { '@type': 'Answer', text: answer },
    })),
  } : null

  return (
    <div className="article-page" lang="en">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }} />
      {faqSchema && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }} />
      )}

      {/* HERO */}
      <div className="article-hero" style={{ background: page.image_gradient }}>
        <div className="article-hero-overlay" />
        <div className="container">
          <div className="article-header">
            {/* Breadcrumb nav */}
            <nav aria-label="Breadcrumb" style={{ marginBottom: 16 }}>
              <ol style={{ display: 'flex', alignItems: 'center', gap: 6, listStyle: 'none', padding: 0, margin: 0, flexWrap: 'wrap' }}>
                <li><Link href="/en" style={{ fontSize: 13, color: 'var(--muted)' }}>Home</Link></li>
                <li style={{ color: 'var(--faint)', fontSize: 13 }}>/</li>
                <li><Link href="/en/compare" style={{ fontSize: 13, color: 'var(--muted)' }}>Guides</Link></li>
                <li style={{ color: 'var(--faint)', fontSize: 13 }}>/</li>
                <li style={{ fontSize: 13, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 220 }} aria-current="page">{page.title}</li>
              </ol>
            </nav>

            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
              <span style={{
                display: 'inline-block', padding: '4px 10px', borderRadius: '6px',
                fontSize: '10px', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase',
                background: `${color}18`, color, border: `1px solid ${color}30`,
              }}>{catLabel}</span>
              <span className="meta-sep">·</span>
              <Link href={AUTHOR_PAGE} style={{ fontSize: 13, color: 'var(--muted)', textDecoration: 'none', fontWeight: 500 }}>Javier Valencia</Link>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{formatDate(page.published_at)}</span>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{page.reading_time} min read</span>
            </div>

            <h1 className="article-main-title">{page.title}</h1>
            {page.excerpt && <p className="article-byline">{page.excerpt}</p>}
          </div>
        </div>
      </div>

      {/* BODY */}
      <div className="container">
        <div className="article-body-grid">
          <article lang="en">
            <ReactMarkdown
              components={{
                h2: ({ children }) => <h2 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.03em', margin: '40px 0 16px', color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: 10 }}>{children}</h2>,
                h3: ({ children }) => <h3 style={{ fontSize: '1.15rem', fontWeight: 600, margin: '28px 0 12px', color: 'var(--text)' }}>{children}</h3>,
                p:  ({ children }) => <p style={{ fontSize: 17, lineHeight: 1.8, color: 'rgba(240,240,238,0.85)', marginBottom: 20 }}>{children}</p>,
                ul: ({ children }) => <ul style={{ margin: '16px 0 20px 24px' }}>{children}</ul>,
                ol: ({ children }) => <ol style={{ margin: '16px 0 20px 24px' }}>{children}</ol>,
                li: ({ children }) => <li style={{ fontSize: 16, lineHeight: 1.7, color: 'rgba(240,240,238,0.8)', marginBottom: 8 }}>{children}</li>,
                strong: ({ children }) => <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{children}</strong>,
                blockquote: ({ children }) => <blockquote style={{ borderLeft: '3px solid var(--cyan)', paddingLeft: 20, margin: '24px 0', color: 'var(--muted)', fontStyle: 'italic' }}>{children}</blockquote>,
                code: ({ children }) => <code style={{ fontFamily: 'var(--mono)', fontSize: 13, background: 'var(--surface)', border: '1px solid var(--border)', padding: '2px 7px', borderRadius: 5, color: 'var(--cyan)' }}>{children}</code>,
                table: ({ children }) => <div style={{ overflowX: 'auto', margin: '24px 0' }}><table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>{children}</table></div>,
                th: ({ children }) => <th style={{ padding: '10px 14px', background: 'var(--surface)', borderBottom: '1px solid var(--border)', textAlign: 'left', fontWeight: 600, color: 'var(--text)' }}>{children}</th>,
                td: ({ children }) => <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', color: 'rgba(240,240,238,0.8)' }}>{children}</td>,
                hr: () => <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '40px 0' }} />,
              }}
            >
              {page.content}
            </ReactMarkdown>

            <div style={{ marginTop: 48, padding: '16px 20px', background: 'rgba(110,207,202,0.05)', border: '1px solid rgba(110,207,202,0.15)', borderRadius: 10, fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
              <strong style={{ color: 'var(--cyan)' }}>Editorial note:</strong> This guide was produced with AI assistance and reviewed by Javier Valencia.{' '}
              <Link href="/en/editorial-policy" style={{ color: 'var(--cyan)' }}>Read our editorial policy.</Link>
            </div>

            <div style={{ marginTop: 40, paddingTop: 32, borderTop: '1px solid var(--border)', display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
              <Link href="/en" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--cyan)', fontSize: 14, fontWeight: 600 }}>← Back to home</Link>
              <Link href="/en/compare" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--muted)', fontSize: 14 }}>More guides →</Link>
            </div>
          </article>

          {/* SIDEBAR */}
          <aside>
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Author</div>
              <Link href={AUTHOR_PAGE} style={{ textDecoration: 'none' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, var(--cyan), #9b8cef)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 800, color: 'var(--bg)', flexShrink: 0 }}>JV</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)' }}>Javier Valencia</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>Reviewed by NewsTide Editorial</div>
                  </div>
                </div>
              </Link>
              <Link href="/en/editorial-policy" style={{ fontSize: 12, color: 'var(--cyan)' }}>Editorial policy →</Link>
            </div>

            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Details</div>
              <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 2.2 }}>
                <div>📅 {formatDate(page.published_at)}</div>
                <div>⏱ {page.reading_time} min read</div>
                <div>🏷 {catLabel}</div>
                {page.entity_a && <div>🔍 {page.entity_a}{page.entity_b ? ` vs ${page.entity_b}` : ''}</div>}
              </div>
            </div>

            <div style={{ background: 'linear-gradient(135deg, rgba(110,207,202,0.08), rgba(155,140,239,0.08))', border: '1px solid rgba(110,207,202,0.2)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 8 }}>✉️ Newsletter</div>
              <p style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6, marginBottom: 16 }}>The best AI & startup stories — weekly.</p>
              <NewsletterForm compact />
            </div>

            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Share</div>
              <ShareButtons url={url} title={page.title} />
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
