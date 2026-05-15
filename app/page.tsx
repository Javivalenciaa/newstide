
import { supabase } from '@/lib/supabase'
import Link from 'next/link'

interface Article {
  id: string
  title: string
  slug: string
  excerpt: string
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
  return new Date(d).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
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

export default async function Home() {
  const { data: articles } = await supabase
    .from('articles')
    .select('id,title,slug,excerpt,category,author,published_at,reading_time,featured,image_gradient')
    .order('published_at', { ascending: false })
    .limit(20)

  const featured = articles?.find(a => a.featured) || articles?.[0]
  const rest = articles?.filter(a => a.id !== featured?.id) || []

  return (
    <main>
      {/* HERO */}
      <section id="hero">
        <div className="hero-bg" />
        <div className="hero-grid" />
        <div className="hero-content">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            Tech · IA · Startups
          </div>
          <h1 className="hero-title">
            La <span className="grad">inteligencia</span><br />
            que transforma<br />
            el futuro
          </h1>
          <p className="hero-sub">
            Artículos de fondo, herramientas y tendencias para founders, developers y profesionales.
          </p>
          <div className="hero-tags">
            <span>Tendencias:</span>
            {['Claude vs GPT-4o', 'Automatización', 'Startups IA 2026', 'RAG avanzado'].map(t => (
              <span key={t} className="hero-tag">{t}</span>
            ))}
          </div>
        </div>
        <div className="hero-scroll">
          Scroll
          <div className="hero-scroll-line" />
        </div>
      </section>

      {/* FEATURED */}
      {featured && (
        <section id="featured">
          <div className="container">
            <Link href={`/articulo/${featured.slug}`} className="featured-card">
              <div className="featured-img" style={{ background: featured.image_gradient }}>
                <div className="featured-dots" />
              </div>
              <div className="featured-content">
                <div className="featured-meta">
                  <Badge cat={featured.category} />
                  <span style={{ fontSize: 12, color: 'var(--muted)' }}>Artículo destacado</span>
                </div>
                <h2 className="featured-title">{featured.title}</h2>
                <p className="featured-desc">{featured.excerpt}</p>
                <div className="featured-footer">
                  <strong>{featured.author}</strong>
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

      {/* ARTICLES GRID */}
      <section className="section-articles" id="articles">
        <div className="container">
          <div className="section-header">
            <div className="section-label">Lo más reciente</div>
            <h2 className="section-title">Artículos y análisis</h2>
          </div>
          <div className="articles-layout">
            <div className="articles-grid">
              {rest.slice(0, 6).map((a, i) => (
                <Link
                  href={`/articulo/${a.slug}`}
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
                    <h3 className="article-title">{a.title}</h3>
                    <p className="article-excerpt">{a.excerpt}</p>
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
                        <Link href={`/articulo/${a.slug}`} className="trending-text">{a.title}</Link>
                        <div style={{ marginTop: 4 }}><Badge cat={a.category} /></div>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
              <div className="sidebar-widget" style={{ marginTop: 16 }}>
                <div className="widget-title">✉️ Newsletter</div>
                <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 14, lineHeight: 1.6 }}>
                  Las mejores historias de la semana en tu inbox.
                </p>
                <input type="email" placeholder="tu@email.com" className="sidebar-email" />
                <button className="sidebar-sub-btn">Suscribirse gratis</button>
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
              <h2 className="nl-title">Lo mejor de la semana,<br />en tu inbox.</h2>
              <p className="nl-sub">Más de 8.400 founders y developers ya reciben nuestro resumen semanal.</p>
              <div className="nl-form">
                <input type="email" placeholder="tu@email.com" className="nl-input" />
                <button className="nl-btn">Suscribirme gratis</button>
              </div>
            </div>
            <div className="nl-stats">
              {[['8.4k', 'Suscriptores'], ['97%', 'Tasa apertura'], ['0', 'Spam']].map(([n, l]) => (
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
