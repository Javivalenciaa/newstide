import { supabase } from '@/lib/supabase'
import Link from 'next/link'
import type { Metadata } from 'next'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Todos los artículos — NewsTide',
  description: 'Todos los artículos de NewsTide sobre IA, startups, herramientas y tecnología.',
  alternates: {
    canonical: 'https://www.newstide.news/articulos',
    languages: { 'es': 'https://www.newstide.news/articulos', 'en': 'https://www.newstide.news/en/articles' },
  },
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

export default async function ArticulosPage() {
  const { data: articles } = await supabase
    .from('articles')
    .select('id,title,slug,excerpt,category,author,published_at,reading_time,featured,image_gradient')
    .order('published_at', { ascending: false })
    .limit(100)

  const cats = ['Todos', ...Array.from(new Set(articles?.map(a => a.category) || []))]

  return (
    <main style={{ minHeight: '100vh', paddingTop: '90px' }}>
      {/* PAGE HEADER */}
      <section style={{
        borderBottom: '1px solid var(--border)',
        padding: '48px 0 40px',
        background: 'linear-gradient(180deg, rgba(110,207,202,0.04) 0%, transparent 100%)'
      }}>
        <div className="container">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Link href="/" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>Inicio</Link>
            <span style={{ color: 'var(--faint)' }}>›</span>
            <span style={{ color: 'var(--fg)', fontSize: 13 }}>Artículos</span>
          </div>
          <h1 style={{
            fontSize: 'clamp(28px, 5vw, 42px)', fontWeight: 800,
            letterSpacing: '-0.02em', marginBottom: 12
          }}>
            Todos los <span className="grad">artículos</span>
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: 16, maxWidth: 480 }}>
            {articles?.length || 0} artículos sobre IA, startups, herramientas y tecnología.
          </p>
          {/* CATEGORY PILLS */}
          <div style={{
            display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 28
          }}>
            {cats.map(c => (
              <span key={c} style={{
                padding: '6px 14px', borderRadius: '20px', fontSize: 13, fontWeight: 500,
                background: c === 'Todos' ? 'var(--accent)' : 'var(--surface)',
                color: c === 'Todos' ? 'var(--bg)' : 'var(--muted)',
                border: '1px solid var(--border)', cursor: 'pointer'
              }}>{c}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ARTICLES GRID */}
      <section style={{ padding: '48px 0 80px' }}>
        <div className="container">
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 320px), 1fr))',
            gap: '24px'
          }}>
            {articles?.map((a, i) => (
              <Link
                href={`/articulo/${a.slug}`}
                key={a.id}
                className="article-card"
                style={{ '--delay': `${i * 0.04}s` } as React.CSSProperties}
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
          {(!articles || articles.length === 0) && (
            <div style={{ textAlign: 'center', padding: '80px 20px', color: 'var(--muted)' }}>
              No hay artículos todavía.
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
