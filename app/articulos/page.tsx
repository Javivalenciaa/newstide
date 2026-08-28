import { supabase } from '@/lib/supabase'
import Image from 'next/image'
import Link from 'next/link'
import type { Metadata } from 'next'

// A3: listado de artículos → revalida cada hora (suficiente para un listado)
export const revalidate = 3600
// A2: necesario para leer searchParams en un Server Component de página
export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Todos los artículos — NewsTide',
  description: 'Todos los artículos de NewsTide sobre IA, startups, herramientas y tecnología.',
  alternates: {
    canonical: 'https://www.newstide.news/articulos',
    languages: {
      'es': 'https://www.newstide.news/articulos',
      'en': 'https://www.newstide.news/en/articles',
      // A5: x-default apunta a la homepage ES (mercado principal)
      'x-default': 'https://www.newstide.news',
    },
  },
}

const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef',
  'Herramientas': '#e8d5a3', 'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c',
  'AI Tools': '#6ecfca', 'Automation': '#9b8cef', 'Build & Launch': '#e8d5a3',
  'Indie Hacking': '#7ecf9b', 'Growth': '#ef6c6c', 'Monetization': '#f0a050',
  'Freelancing': '#8ecae6', 'Dev Stack': '#c9a0f5',
}

const CAT_SLUG_ES: Record<string, string> = {
  'IA': 'ia', 'Tutoriales': 'tutoriales',
  'Herramientas': 'herramientas', 'Startups': 'startups', 'Noticias': 'noticias',
  'AI Tools': 'ai-tools', 'Automation': 'automation', 'Build & Launch': 'build-launch',
  'Indie Hacking': 'indie-hacking', 'Growth': 'growth', 'Monetization': 'monetization',
  'Freelancing': 'freelancing', 'Dev Stack': 'dev-stack',
}

const FALLBACK_GRADIENT = 'linear-gradient(135deg, #1a1f2e 0%, #0f1623 100%)'

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

// A2: recibe searchParams para implementar el buscador que promete el SearchAction
export default async function ArticulosPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>
}) {
  const { q } = await searchParams
  const query = q?.trim() ?? ''

  // A2: si hay query, filtra por title.ilike; si no, devuelve todos
  let builder = supabase
    .from('articles')
    .select('id,title,slug,excerpt,category,author,published_at,reading_time,featured,cover_image_url')
    .order('published_at', { ascending: false })
    .limit(100)

  if (query) {
    builder = builder.ilike('title', `%${query}%`)
  }

  const { data: articles } = await builder

  const cats = Array.from(new Set(articles?.map(a => a.category) || []))

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
            {query
              ? `${articles?.length || 0} resultado${articles?.length !== 1 ? 's' : ''} para "${query}"`
              : `${articles?.length || 0} artículos sobre IA, startups, herramientas y tecnología.`
            }
          </p>

          {/* A2: formulario de búsqueda — form GET, Server Component puro, sin JS cliente */}
          <form
            method="GET"
            action="/articulos"
            style={{ marginTop: 24, display: 'flex', gap: 8, maxWidth: 480 }}
          >
            <input
              type="search"
              name="q"
              defaultValue={query}
              placeholder="Buscar artículos…"
              aria-label="Buscar artículos"
              style={{
                flex: 1,
                padding: '9px 14px',
                borderRadius: 10,
                border: '1px solid var(--border)',
                background: 'var(--surface)',
                color: 'var(--text)',
                fontSize: 14,
                outline: 'none',
              }}
            />
            <button
              type="submit"
              style={{
                padding: '9px 18px',
                borderRadius: 10,
                border: '1px solid var(--border)',
                background: 'var(--accent)',
                color: 'var(--bg)',
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Buscar
            </button>
            {query && (
              <Link
                href="/articulos"
                style={{
                  padding: '9px 14px',
                  borderRadius: 10,
                  border: '1px solid var(--border)',
                  background: 'var(--surface)',
                  color: 'var(--muted)',
                  fontSize: 13,
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                ✕
              </Link>
            )}
          </form>

          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 20 }}>
            <Link
              href="/articulos"
              style={{
                padding: '6px 14px', borderRadius: '20px', fontSize: 13, fontWeight: 500,
                background: 'var(--accent)', color: 'var(--bg)',
                border: '1px solid var(--border)', textDecoration: 'none',
              }}
            >Todos</Link>
            {cats.map(c => (
              <Link
                key={c}
                href={`/articulos/${CAT_SLUG_ES[c] || c.toLowerCase()}`}
                style={{
                  padding: '6px 14px', borderRadius: '20px', fontSize: 13, fontWeight: 500,
                  background: 'var(--surface)', color: 'var(--muted)',
                  border: '1px solid var(--border)', textDecoration: 'none',
                }}
              >{c}</Link>
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
                  {a.cover_image_url ? (
                    <Image
                      src={a.cover_image_url}
                      alt={a.title}
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
              {query ? `No se encontraron artículos para "${query}".` : 'No hay artículos todavía.'}
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
