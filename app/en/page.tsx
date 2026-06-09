import { supabase } from '@/lib/supabase'
import Link from 'next/link'
import type { Metadata } from 'next'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'NewsTide — The intelligence shaping the future',
  description: 'Technology, AI and trends for founders, developers and professionals.',
  alternates: {
    canonical: 'https://www.newstide.news/en',
    languages: { 'es': 'https://www.newstide.news', 'en': 'https://www.newstide.news/en' },
  },
  openGraph: { siteName: 'NewsTide', locale: 'en_US', type: 'website' },
}

interface Article {
  id: string
  title: string
  title_en: string
  slug: string
  excerpt: string
  excerpt_en: string
  category: string
  author: string
  published_at: string
  reading_time: number
  featured: boolean
  image_gradient: string
}

const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef',
  'Herramientas': '#e8d5a3', 'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c'
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
}

function Badge({ cat }: { cat: string }) {
  const color = CAT_COLORS[cat] || '#6ecfca'
  return (
    <span style={{
      display: 'inline-block', padding: '3px 10px', borderRadius: '6px',
      fontSize: '10px', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase',
      background: `${color}18`, color, border: `1px solid ${color}30`
    }}>{cat}</span>
  )
}

export default async function HomeEN() {
  const { data: articles } = await supabase
    .from('articles')
    .select('id,title,title_en,slug,excerpt,excerpt_en,category,author,published_at,reading_time,featured,image_gradient')
    .order('published_at', { ascending: false })
    .limit(20)

  const featured = articles?.find(a => a.featured) || articles?.[0]
  const rest = articles?.filter(a => a.id !== featured?.id) || []

  const t = (a: Article) => ({
    title: a.title_en || a.title,
    excerpt: a.excerpt_en || a.excerpt,
  })

  return (
    <main>
      {/* HERO */}
      <section id="hero">
        <div className="hero-bg" />
        <div className="hero-grid" />
        <div className="hero-content">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            Tech · AI · Startups
          </div>
          <h1 className="hero-title">
            The <span className="grad">intelligence</span><br />
            shaping<br />
            the future
          </h1>
          <p className="hero-sub">
            In-depth articles, tools and trends for founders, developers and professionals.
          </p>
          <div className="hero-tags">
            <span>Trending:</span>
            {['Claude vs GPT-4o', 'Automation', 'AI Startups 2026', 'Advanced RAG'].map(tag => (
              <span key={tag} className="hero-tag">{tag}</span>
            ))}
          </div>
        </div>
        <div className="hero-scroll">Scroll<div className="hero-scroll-line" /></div>
      </section>

      {/* FEATURED */}
      {featured && (
        <section id="featured">
          <div className="container">
            <Link href={`/en/article/${featured.slug}`} className="featured-card">
              <div className="featured-img" style={{ background: featured.image_gradient }}>
                <div className="featured-dots" />
              </div>
              <div className="featured-content">
                <div className="featured-meta">
                  <Badge cat={featured.category} />
                  <span style={{ fontSize: 12, color: 'var(--muted)' }}>Featured article</span>
                </div>
                <h2 className="featured-title">{t(featured).title}</h2>
                <p className="featured-desc">{t(featured).excerpt}</p>
                <div className="featured-footer">
                  <strong>{featured.author}</strong>
                  <span>·</span>
                  <span>{formatDate(featured.published_at)}</span>
                  <span>·</span>
                  <span>{featured.reading_time} min</span>
                  <span className="featured-tag">Read article →</span>
                </div>
              </div>
            </Link>
          </div>
        </section>
      )}

      {/* ARTICLES GRID */}
      <section className="section-articles" id="articles">
        <div className="container">
          <div className="section-header">
            <div className="section-label">Latest</div>
            <h2 className="section-title">Articles & Analysis</h2>
          </div>
          <div className="articles-layout">
            <div className="articles-grid">
              {rest.slice(0, 6).map((a, i) => (
                <Link
                  href={`/en/article/${a.slug}`}
                  key={a.id}
                  className="article-card"
                  style={{ '--delay': `${i * 0.1}s` } as React.CSSProperties}
                >
                  <div className="article-img">
                    <div className="article-img-inner" style={{ background: a.image_gradient }} />
                  </div>
                  <div className="article-body">
                    <div className="article-meta">
                      <Badge cat={a.category} />
                      <span className="article-time">{a.reading_time} min</span>
                    </div>
                    <h3 className="article-title">{t(a).title}</h3>
                    <p className="article-excerpt">{t(a).excerpt}</p>
                    <div className="article-footer">
                      <span className="article-author">{a.author}</span>
                      <span className="article-dot">·</span>
                      <span>{formatDate(a.published_at)}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            <aside className="sidebar">
              <div className="sidebar-widget">
                <div className="widget-title">🔥 Trending</div>
                <ol className="trending-list">
                  {rest.slice(0, 5).map((a, i) => (
                    <li key={a.id} className="trending-item">
                      <span className="trending-num">0{i + 1}</span>
                      <div>
                        <Link href={`/en/article/${a.slug}`} className="trending-text">{t(a).title}</Link>
                        <div style={{ marginTop: 4 }}><Badge cat={a.category} /></div>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
              <div className="sidebar-widget" style={{ marginTop: 16 }}>
                <div className="widget-title">✉️ Newsletter</div>
                <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 14, lineHeight: 1.6 }}>
                  The best stories of the week in your inbox.
                </p>
                <input type="email" placeholder="you@email.com" className="sidebar-email" />
                <button className="sidebar-sub-btn">Subscribe for free</button>
              </div>
            </aside>
          </div>
        </div>
      </section>

      {/* NEWSLETTER */}
      <section className="section-newsletter" id="newsletter">
        <div className="container">
          <div className="newsletter-card">
            <div className="nl-bg" />
            <div className="nl-content">
              <div className="nl-badge">✉️ Newsletter</div>
              <h2 className="nl-title">The best of the week,<br />in your inbox.</h2>
              <p className="nl-sub">Over 8,400 founders and developers already receive our weekly digest.</p>
              <div className="nl-form">
                <input type="email" placeholder="you@email.com" className="nl-input" />
                <button className="nl-btn">Subscribe for free</button>
              </div>
            </div>
            <div className="nl-stats">
              {[['8.4k', 'Subscribers'], ['97%', 'Open rate'], ['0', 'Spam']].map(([n, l]) => (
                <div key={l}>
                  <div className="nstat-num">{n}</div>
                  <div className="nstat-label">{l}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
