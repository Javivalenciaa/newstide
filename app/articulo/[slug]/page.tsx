import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'

const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef',
  'Herramientas': '#e8d5a3', 'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c'
}

function Badge({ cat }: { cat: string }) {
  const color = CAT_COLORS[cat] || '#6ecfca'
  return (
    <span style={{
      display: 'inline-block', padding: '4px 10px', borderRadius: '6px',
      fontSize: '10px', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase',
      background: `${color}18`, color, border: `1px solid ${color}30`
    }}>{cat}</span>
  )
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default async function ArticuloPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params

  const { data: article } = await supabase
    .from('articles')
    .select('*')
    .eq('slug', slug)
    .maybeSingle()

  if (!article) notFound()

  return (
    <div className="article-page">

      {/* HERO */}
      <div className="article-hero" style={{ background: article!.image_gradient }}>
        <div className="article-hero-overlay" />
        <div className="container">
          <div className="article-header">
            <div className="article-meta-top">
              <Link href="/" style={{ color: 'var(--muted)' }}>Inicio</Link>
              <span className="meta-sep">/</span>
              <span>{article!.category}</span>
            </div>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
              <Badge cat={article!.category} />
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{article!.author}</span>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{formatDate(article!.published_at)}</span>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{article!.reading_time} min de lectura</span>
            </div>
            <h1 className="article-main-title">{article!.title}</h1>
            <p className="article-byline">{article!.excerpt}</p>
          </div>
        </div>
      </div>

      {/* CUERPO + SIDEBAR */}
      <div className="container">
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 280px',
          gap: '64px',
          alignItems: 'start',
          padding: '60px 0 100px',
          maxWidth: 1100,
          margin: '0 auto'
        }}>

          {/* CONTENIDO MARKDOWN */}
          <div className="article-content">
            <ReactMarkdown
              components={{
                h2: ({ children }) => (
                  <h2 style={{
                    fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.03em',
                    margin: '40px 0 16px', color: 'var(--text)',
                    borderBottom: '1px solid var(--border)', paddingBottom: 10
                  }}>{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 style={{
                    fontSize: '1.15rem', fontWeight: 600,
                    margin: '28px 0 12px', color: 'var(--text)'
                  }}>{children}</h3>
                ),
                p: ({ children }) => (
                  <p style={{
                    fontSize: 17, lineHeight: 1.8,
                    color: 'rgba(240,240,238,0.85)', marginBottom: 20
                  }}>{children}</p>
                ),
                ul: ({ children }) => (
                  <ul style={{ margin: '16px 0 20px 24px' }}>{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol style={{ margin: '16px 0 20px 24px' }}>{children}</ol>
                ),
                li: ({ children }) => (
                  <li style={{
                    fontSize: 16, lineHeight: 1.7,
                    color: 'rgba(240,240,238,0.8)', marginBottom: 8
                  }}>{children}</li>
                ),
                strong: ({ children }) => (
                  <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{children}</strong>
                ),
                blockquote: ({ children }) => (
                  <blockquote style={{
                    borderLeft: '3px solid var(--cyan)', paddingLeft: 20,
                    margin: '24px 0', color: 'var(--muted)', fontStyle: 'italic'
                  }}>{children}</blockquote>
                ),
                code: ({ children }) => (
                  <code style={{
                    fontFamily: 'var(--mono)', fontSize: 13,
                    background: 'var(--surface)', border: '1px solid var(--border)',
                    padding: '2px 7px', borderRadius: 5, color: 'var(--cyan)'
                  }}>{children}</code>
                ),
                hr: () => (
                  <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '40px 0' }} />
                ),
              }}
            >
              {article!.content}
            </ReactMarkdown>

            {/* VOLVER */}
            <div style={{ marginTop: 64, paddingTop: 32, borderTop: '1px solid var(--border)' }}>
              <Link href="/" style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                color: 'var(--cyan)', fontSize: 14, fontWeight: 600
              }}>
                ← Volver al inicio
              </Link>
            </div>
          </div>

          {/* SIDEBAR */}
          <aside style={{ position: 'sticky', top: 88 }}>

            {/* AUTOR */}
            <div style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 14, padding: 24, marginBottom: 16
            }}>
              <div style={{
                fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase',
                color: 'var(--muted)', marginBottom: 12
              }}>Autor</div>
              <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>{article!.author}</div>
              <Badge cat={article!.category} />
            </div>

            {/* DETALLES */}
            <div style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 14, padding: 24, marginBottom: 16
            }}>
              <div style={{
                fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase',
                color: 'var(--muted)', marginBottom: 12
              }}>Detalles</div>
              <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 2.2 }}>
                <div>📅 {formatDate(article!.published_at)}</div>
                <div>⏱ {article!.reading_time} min de lectura</div>
                <div>🏷 {article!.category}</div>
              </div>
            </div>

            {/* NEWSLETTER */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(110,207,202,0.08), rgba(155,140,239,0.08))',
              border: '1px solid rgba(110,207,202,0.2)',
              borderRadius: 14, padding: 24
            }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 8 }}>✉️ Newsletter</div>
              <p style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6, marginBottom: 16 }}>
                Las mejores historias de la semana en tu inbox.
              </p>
              <input
                type="email"
                placeholder="tu@email.com"
                className="sidebar-email"
              />
              <button className="sidebar-sub-btn">Suscribirse gratis</button>
            </div>

            {/* COMPARTIR */}
            <div style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 14, padding: 24, marginTop: 16
            }}>
              <div style={{
                fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase',
                color: 'var(--muted)', marginBottom: 12
              }}>Compartir</div>
              <div style={{ display: 'flex', gap: 10 }}>
                {['𝕏', 'in', '🔗'].map((icon, i) => (
                  <button key={i} style={{
                    flex: 1, padding: '8px 0', borderRadius: 8,
                    background: 'var(--bg)', border: '1px solid var(--border)',
                    color: 'var(--muted)', fontSize: i === 2 ? 14 : 13,
                    fontWeight: 600, cursor: 'pointer',
                    transition: 'border-color 0.2s, color 0.2s'
                  }}>{icon}</button>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
