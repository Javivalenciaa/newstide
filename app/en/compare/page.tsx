import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import Link from 'next/link'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'AI Tool Guides, Comparisons & Alternatives | NewsTide',
  description: 'In-depth comparisons, alternatives and guides for AI tools, startup software and developer tech. Updated regularly by the NewsTide team.',
  alternates: {
    canonical: 'https://www.newstide.news/en/compare',
    languages: { 'en': 'https://www.newstide.news/en/compare', 'x-default': 'https://www.newstide.news/en/compare' },
  },
  openGraph: {
    title: 'AI Tool Guides, Comparisons & Alternatives | NewsTide',
    description: 'In-depth comparisons, alternatives and guides for AI tools and startup software.',
    url: 'https://www.newstide.news/en/compare',
    siteName: 'NewsTide',
    locale: 'en_US',
    type: 'website',
    images: [{ url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630, alt: 'NewsTide Guides' }],
  },
}

const TEMPLATE_LABELS: Record<string, string> = {
  comparisons:      'Comparison',
  alternatives:     'Alternatives',
  guides:           'Guide',
  'for-profession': 'For Professionals',
}

const TEMPLATE_COLORS: Record<string, string> = {
  comparisons:      '#6ecfca',
  alternatives:     '#9b8cef',
  guides:           '#7ecf9b',
  'for-profession': '#e8d5a3',
}

const TEMPLATE_FILTERS = [
  { key: '',               label: 'All' },
  { key: 'comparisons',    label: '⚔️ Comparisons' },
  { key: 'alternatives',   label: '🔄 Alternatives' },
  { key: 'guides',         label: '📖 Guides' },
  { key: 'for-profession', label: '👤 For Professionals' },
]

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

export default async function CompareIndexPage() {
  const { data: pages } = await supabase
    .from('pseo_pages')
    .select('id, slug, title, excerpt, template, entity_a, entity_b, published_at, reading_time')
    .lte('published_at', new Date().toISOString())
    .order('published_at', { ascending: false })
    .limit(200)

  const allPages = pages || []

  // Structured data: CollectionPage
  const collectionSchema = {
    '@context': 'https://schema.org',
    '@type':    'CollectionPage',
    '@id':      'https://www.newstide.news/en/compare',
    name:       'AI Tool Guides, Comparisons & Alternatives',
    description: 'In-depth comparisons, alternatives and guides for AI tools and startup software.',
    url:        'https://www.newstide.news/en/compare',
    inLanguage: 'en',
    isPartOf:   { '@id': 'https://www.newstide.news/#website' },
    publisher:  { '@id': 'https://www.newstide.news/#organization' },
  }

  // BreadcrumbList
  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type':    'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home',   item: 'https://www.newstide.news/en' },
      { '@type': 'ListItem', position: 2, name: 'Guides', item: 'https://www.newstide.news/en/compare' },
    ],
  }

  return (
    <main style={{ minHeight: '100vh', paddingTop: '90px' }} lang="en">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(collectionSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }} />

      {/* HEADER */}
      <section style={{ borderBottom: '1px solid var(--border)', padding: '48px 0 40px', background: 'linear-gradient(180deg, rgba(110,207,202,0.05) 0%, transparent 100%)' }}>
        <div className="container">
          <nav aria-label="Breadcrumb" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>Home</Link>
            <span style={{ color: 'var(--faint)' }}>›</span>
            <span style={{ color: 'var(--fg)', fontSize: 13 }}>Guides</span>
          </nav>
          <h1 style={{ fontSize: 'clamp(26px, 5vw, 40px)', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 12 }}>
            AI Tool <span style={{ color: 'var(--cyan)' }}>Guides</span> & Comparisons
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: 16, maxWidth: 540, lineHeight: 1.6 }}>
            Honest comparisons, real alternatives, and practical guides for AI tools — built for founders and developers.
          </p>
          <p style={{ color: 'var(--faint)', fontSize: 13, marginTop: 8 }}>{allPages.length} guides published</p>

          {/* Template filter tabs */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 28 }}>
            {TEMPLATE_FILTERS.map(({ key, label }) => (
              <span key={key} style={{ padding: '6px 14px', borderRadius: '20px', fontSize: 13, fontWeight: 500, background: 'var(--surface)', color: 'var(--muted)', border: '1px solid var(--border)', cursor: 'default' }}>{label}</span>
            ))}
          </div>
        </div>
      </section>

      {/* GRID */}
      <section style={{ padding: '48px 0 80px' }}>
        <div className="container">
          {allPages.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '80px 20px', color: 'var(--muted)' }}>
              No guides published yet. Check back soon!
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 320px), 1fr))', gap: '24px' }}>
              {allPages.map((p) => {
                const color = TEMPLATE_COLORS[p.template] || '#6ecfca'
                const label = TEMPLATE_LABELS[p.template] || 'Guide'
                return (
                  <Link
                    key={p.id}
                    href={`/en/compare/${p.slug}`}
                    className="article-card"
                    style={{ textDecoration: 'none' }}
                  >
                    <div className="article-img">
                      <div className="article-img-inner" style={{ background: 'linear-gradient(135deg, #1a1f2e 0%, #0f1623 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <span style={{ fontSize: 32 }}>
                          {p.template === 'comparisons' ? '⚔️' : p.template === 'alternatives' ? '🔄' : p.template === 'guides' ? '📖' : '👤'}
                        </span>
                      </div>
                    </div>
                    <div className="article-body">
                      <div className="article-meta">
                        <span style={{ display: 'inline-block', padding: '3px 10px', borderRadius: '6px', fontSize: '10px', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', background: `${color}18`, color, border: `1px solid ${color}30` }}>{label}</span>
                        <span className="article-time">{p.reading_time} min</span>
                      </div>
                      <h3 className="article-title">{p.title}</h3>
                      {p.excerpt && <p className="article-excerpt">{p.excerpt}</p>}
                      <div className="article-footer">
                        <span className="article-author">Javier Valencia</span>
                        <span className="article-dot">·</span>
                        <span>{formatDate(p.published_at)}</span>
                      </div>
                    </div>
                  </Link>
                )
              })}
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
