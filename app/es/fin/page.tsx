import { supabase } from '@/lib/supabase'
import Image from 'next/image'
import Link from 'next/link'
import type { Metadata } from 'next'
import NewsletterForm from '@/components/NewsletterForm'

export const revalidate = 300

export const metadata: Metadata = {
  title: 'Finanzas Personales — NewsTide',
  description: 'Guías prácticas de finanzas personales para hispanos en EE.UU.: ahorro, presupuesto, inversión, deudas y crédito. Actualizado a diario.',
  alternates: {
    canonical: 'https://www.newstide.news/es/fin',
    languages: { 'es': 'https://www.newstide.news/es/fin', 'x-default': 'https://www.newstide.news/es/fin' },
  },
  openGraph: {
    title: 'Finanzas Personales — NewsTide',
    description: 'Guías prácticas de finanzas personales para hispanos en EE.UU.',
    siteName: 'NewsTide',
    locale: 'es_ES',
    type: 'website',
    url: 'https://www.newstide.news/es/fin',
  },
}

interface FinanceArticle {
  id: string
  title: string
  slug: string
  excerpt: string
  category: string
  author: string
  published_at: string
  reading_time: number
  featured: boolean
  cover_image_url: string | null
}

const FIN_CAT_COLORS: Record<string, string> = {
  'Saving Money':  '#6ecfca',
  'Budgeting':     '#9b8cef',
  'Investing':     '#7ecf9b',
  'Debt':          '#ef6c6c',
  'Credit':        '#e8d5a3',
  'Side Hustles':  '#f0a050',
}

const FALLBACK_GRADIENT = 'linear-gradient(135deg, #0d2a1a 0%, #0a1a0a 100%)'

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
}

function Badge({ cat }: { cat: string }) {
  const color = FIN_CAT_COLORS[cat] || '#6ecfca'
  return (
    <span style={{
      display: 'inline-block', padding: '3px 10px', borderRadius: '6px',
      fontSize: '10px', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase',
      background: `${color}18`, color, border: `1px solid ${color}30`,
    }}>{cat}</span>
  )
}

export default async function FinanceHomePageEs() {
  const { data: articles } = await supabase
    .from('finance_articles')
    .select('id,title,slug,excerpt,category,author,published_at,reading_time,featured,cover_image_url')
    .not('slug', 'is', null)
    .order('published_at', { ascending: false })
    .limit(7)

  const featured = articles?.find((a: FinanceArticle) => a.featured) || articles?.[0]
  const rest = articles?.filter((a: FinanceArticle) => a.id !== featured?.id) || []

  const t = (a: FinanceArticle) => ({
    title:  a.title,
    excerpt: a.excerpt,
    href:   `/es/fin/${a.slug}`,
  })

  return (
    <main>
      <section id="hero">
        <div className="hero-bg" />
        <div className="hero-grid" />
        <div className="hero-content">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            Finanzas Personales · USA
          </div>
          <h1 className="hero-title">
            Tu dinero,<br />
            <span className="grad">trabajando más</span>
          </h1>
          <p className="hero-sub">
            Guías prácticas sobre ahorro, presupuesto, inversión y crédito — sin relleno, sin humo.
          </p>
          <div className="hero-tags">
            <span>Temas:</span>
            {['Ahorro', 'Presupuesto', 'Inversión', 'Ingresos Extra', 'Deudas'].map(tag => (
              <span key={tag} className="hero-tag">{tag}</span>
            ))}
          </div>
        </div>
        <div className="hero-scroll">Scroll<div className="hero-scroll-line" /></div>
      </section>

      {featured && (
        <section id="featured">
          <div className="container">
            <Link href={t(featured).href} className="featured-card">
              <div className="featured-img" style={!featured.cover_image_url ? { background: FALLBACK_GRADIENT } : undefined}>
                {featured.cover_image_url && (
                  <Image
                    src={featured.cover_image_url}
                    alt={t(featured).title}
                    fill
                    style={{ objectFit: 'cover' }}
                    sizes="(max-width: 768px) 100vw, 1200px"
                    priority
                  />
                )}
              </div>
              <div className="featured-content">
                <div className="featured-meta">
                  <Badge cat={featured.category} />
                  <span style={{ fontSize: 12, color: 'var(--muted)' }}>Artículo destacado</span>
                </div>
                <h2 className="featured-title">{t(featured).title}</h2>
                <p className="featured-desc">{t(featured).excerpt}</p>
                <div className="featured-footer">
                  <strong>NewsTide Finanzas</strong>
                  <span>·</span>
                  <span>{formatDate(featured.published_at)}</span>
                  <span>·</span>
                  <span>{featured.reading_time} min</span>
                  <span className="featured-tag">Leer artículo →</span>
                </div>
              </div>
            </Link>
          </div>
        </section>
      )}

      <section className="section-articles" id="articles">
        <div className="container">
          <div className="section-header">
            <div className="section-label">Últimos</div>
            <h2 className="section-title">Guías de Finanzas Personales</h2>
          </div>
          <div className="articles-layout">
            <div className="articles-grid">
              {rest.slice(0, 6).map((a: FinanceArticle, i: number) => (
                <Link
                  href={t(a).href}
                  key={a.id}
                  className="article-card"
                  style={{ '--delay': `${i * 0.1}s` } as React.CSSProperties}
                >
                  <div className="article-img">
                    {a.cover_image_url ? (
                      <Image
                        src={a.cover_image_url}
                        alt={t(a).title}
                        fill
                        style={{ objectFit: 'cover' }}
                        sizes="(max-width: 768px) 100vw, 33vw"
                      />
                    ) : (
                      <div className="article-img-inner" style={{ background: FALLBACK_GRADIENT }} />
                    )}
                  </div>
                  <div className="article-body">
                    <div className="article-meta">
                      <Badge cat={a.category} />
                      <span className="article-time">{a.reading_time} min</span>
                    </div>
                    <h3 className="article-title">{t(a).title}</h3>
                    <p className="article-excerpt">{t(a).excerpt}</p>
                    <div className="article-footer">
                      <span className="article-author">NewsTide Finanzas</span>
                      <span className="article-dot">·</span>
                      <span>{formatDate(a.published_at)}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            <aside className="sidebar">
              <div className="sidebar-widget">
                <div className="widget-title">💰 Guías Top</div>
                <ol className="trending-list">
                  {rest.slice(0, 5).map((a: FinanceArticle, i: number) => (
                    <li key={a.id} className="trending-item">
                      <span className="trending-num">0{i + 1}</span>
                      <div>
                        <Link href={t(a).href} className="trending-text">{t(a).title}</Link>
                        <div style={{ marginTop: 4 }}><Badge cat={a.category} /></div>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
              <div className="sidebar-widget" style={{ marginTop: 16 }}>
                <div className="widget-title">✉️ Newsletter</div>
                <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 14, lineHeight: 1.6 }}>
                  Consejos financieros semanales en tu correo.
                </p>
                <NewsletterForm compact lang="es" />
              </div>
            </aside>
          </div>
        </div>
      </section>

      <section className="section-newsletter" id="newsletter">
        <div className="container">
          <div className="newsletter-card">
            <div className="nl-bg" />
            <div className="nl-content">
              <div className="nl-badge">✉️ Newsletter</div>
              <h2 className="nl-title">Mejores finanzas,<br />un consejo a la vez.</h2>
              <p className="nl-sub">Consejos financieros prácticos cada semana — sin spam, sin anuncios.</p>
              <NewsletterForm lang="es" />
            </div>
            <div className="nl-stats">
              {[['8.4k', 'Suscriptores'], ['97%', 'Tasa de apertura'], ['0', 'Spam']].map(([n, l]) => (
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
