import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import Link from 'next/link'

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
  params: { slug: string }
}) {
  const { data: article, error } = await supabase
    .from('articles')
    .select('*')
    .eq('slug', params.slug)
    .single()

  if (error || !article) {
    notFound()
  }

  return (
    <div className="article-page">

      {/* HERO */}
      <div
        className="article-hero"
        style={{ background: article!.image_gradient }}
      >
        <div className="article-hero-overlay" />
        <div className="container">
          <div className="article-header">

            {/* BREADCRUMB */}
            <div className="article-meta-top">
              <Link href="/" style={{ color: 'var(--muted)' }}>Inicio</Link>
              <span className="meta-sep">/</span>
              <span>{article!.category}</span>
            </div>

            {/* BADGE + META */}
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
              <Badge cat={article!.category} />
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{article!.author}</span>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{formatDate(article!.published_at)}</span>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{article!.reading_time} min</span>
            </div>

            <h1 className="article-main-title">{article!.title}</h1>
            <p className="article-byline">{article!.excerpt}</p>
          </div>
        </div>
      </div>

      {/* CUERPO */}
      <div className="container">
        <div className="article-body-wrap">
          <div
            className="article-content"
            style={{ whiteSpace: 'pre-wrap' }}
          >
            {article!.content}
          </div>

          {/* VOLVER */}
          <div style={{
            marginTop: 64, paddingTop: 32,
            borderTop: '1px solid var(--border)'
          }}>
            <Link href="/" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              color: 'var(--cyan)', fontSize: 14, fontWeight: 600
            }}>
              ← Volver al inicio
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
