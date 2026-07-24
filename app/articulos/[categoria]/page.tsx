import { supabase } from '@/lib/supabase'
import Image from 'next/image'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'

export const revalidate = 300

const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef',
  'Herramientas': '#e8d5a3', 'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c'
}

const SLUG_TO_CAT: Record<string, string> = {
  'ia': 'IA', 'startups': 'Startups', 'herramientas': 'Herramientas',
  'tutoriales': 'Tutoriales', 'noticias': 'Noticias',
}

const CAT_SLUG_ES: Record<string, string> = {
  'IA': 'ia', 'Tutoriales': 'tutoriales',
  'Herramientas': 'herramientas', 'Startups': 'startups', 'Noticias': 'noticias',
}

const CAT_DESC: Record<string, string> = {
  'IA': 'Artículos sobre inteligencia artificial, modelos de lenguaje, herramientas de IA y tendencias del sector.',
  'Startups': 'Noticias y análisis sobre startups tecnológicas, inversiones, fundadores y ecosistema emprendedor.',
  'Herramientas': 'Reviews y guías de las mejores herramientas tech para developers, founders y profesionales.',
  'Tutoriales': 'Tutoriales prácticos de tecnología, programación, IA y herramientas digitales.',
  'Noticias': 'Las últimas noticias de tecnología, IA, startups y el mundo digital.',
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

export async function generateStaticParams() {
  return Object.keys(SLUG_TO_CAT).map(c => ({ categoria: c }))
}

export async function generateMetadata(
  { params }: { params: Promise<{ categoria: string }> }
): Promise<Metadata> {
  const { categoria } = await params
  const cat = SLUG_TO_CAT[categoria]
  if (!cat) return { title: 'Not found | NewsTide' }
  const url = `https://www.newstide.news/articulos/${categoria}`
  return {
    title: `${cat} — Artículos de NewsTide`,
    description: CAT_DESC[cat] || `Todos los artículos de NewsTide sobre ${cat}.`,
    alternates: {
      canonical: url,
      languages: { 'es': url },
    },
    openGraph: {
      title: `${cat} — NewsTide`,
      description: CAT_DESC[cat] || `Artículos sobre ${cat} en NewsTide.`,
      url,
      siteName: 'NewsTide',
      locale: 'es_ES',
      type: 'website',
      images: [{ url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630, alt: `${cat} — NewsTide` }],
    },
  }
}

export default async function CategoriaPage({
  params,
}: {
  params: Promise<{ categoria: string }>
}) {
  const { categoria } = await params
  const cat = SLUG_TO_CAT[categoria]
  if (!cat) notFound()

  const url = `https://www.newstide.news/articulos/${categoria}`

  const { data: articles } = await supabase
    .from('articles')
    .select('id,title,slug,excerpt,category,author,published_at,reading_time,cover_image_url')
    .eq('category', cat)
    .order('published_at', { ascending: false })
    .limit(100)

  const color   = CAT_COLORS[cat] || '#6ecfca'
  const allCats = Object.keys(SLUG_TO_CAT)

  // BreadcrumbList JSON-LD for category page
  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Inicio', item: 'https://www.newstide.news' },
      { '@type': 'ListItem', position: 2, name: 'Artículos', item: 'https://www.newstide.news/articulos' },
      { '@type': 'ListItem', position: 3, name: cat, item: url },
    ],
  }

  // CollectionPage JSON-LD
  const collectionSchema = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    '@id': url,
    name: `${cat} — NewsTide`,
    description: CAT_DESC[cat],
    url,
    inLanguage: 'es',
    isPartOf: { '@id': 'https://www.newstide.news/#website' },
    publisher: { '@id': 'https://www.newstide.news/#organization' },
  }

  return (
    <main style={{ minHeight: '100vh', paddingTop: '90px' }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(collectionSchema) }} />

      {/* PAGE HEADER */}
      <section style={{
        borderBottom: '1px solid var(--border)',
        padding: '48px 0 40px',
        background: `linear-gradient(180deg, ${color}08 0%, transparent 100%)`
      }}>
        <div className="container">
          <nav aria-label="Miga de pan" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Link href="/" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>Inicio</Link>
            <span style={{ color: 'var(--faint)' }}>›</span>
            <Link href="/articulos" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>Artículos</Link>
            <span style={{ color: 'var(--faint)' }}>›</span>
            <span style={{ color: 'var(--fg)', fontSize: 13 }}>{cat}</span>
          </nav>
          <h1 style={{
            fontSize: 'clamp(28px, 5vw, 42px)', fontWeight: 800,
            letterSpacing: '-0.02em', marginBottom: 12
          }}>
            <span style={{ color }}>{cat}</span>
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: 16, maxWidth: 520 }}>
            {CAT_DESC[cat]}
          </p>
          <p style={{ color: 'var(--faint)', fontSize: 13, marginTop: 8 }}>
            {articles?.length || 0} artículos
          </p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 28 }}>
            <Link href="/articulos" style={{ padding: '6px 14px', borderRadius: '20px', fontSize: 13, fontWeight: 500, background: 'var(--surface)', color: 'var(--muted)', border: '1px solid var(--border)', textDecoration: 'none' }}>Todos</Link>
            {allCats.map(c => {
              const label  = SLUG_TO_CAT[c]
              const active = c === categoria
              const col    = CAT_COLORS[label] || '#6ecfca'
              return (
                <Link key={c} href={`/articulos/${c}`} style={{ padding: '6px 14px', borderRadius: '20px', fontSize: 13, fontWeight: 500, background: active ? col : 'var(--surface)', color: active ? '#0a0f1a' : 'var(--muted)', border: `1px solid ${active ? col : 'var(--border)'}`, textDecoration: 'none' }}>{label}</Link>
              )
            })}
          </div>
        </div>
      </section>

      {/* ARTICLES GRID */}
      <section style={{ padding: '48px 0 80px' }}>
        <div className="container">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 320px), 1fr))', gap: '24px' }}>
            {articles?.map((a, i) => (
              <Link href={`/articulo/${a.slug}`} key={a.id} className="article-card" style={{ '--delay': `${i * 0.04}s` } as React.CSSProperties}>
                <div className="article-img">
                  {a.cover_image_url ? (
                    <Image src={a.cover_image_url} alt={a.title} fill style={{ objectFit: 'cover' }} sizes="(max-width: 768px) 100vw, 33vw" />
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
                    <span className="article-author">{a.author || 'Javier Valencia'}</span>
                    <span className="article-dot">·</span>
                    <span>{formatDate(a.published_at)}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
          {(!articles || articles.length === 0) && (
            <div style={{ textAlign: 'center', padding: '80px 20px', color: 'var(--muted)' }}>No hay artículos en esta categoría todavía.</div>
          )}
        </div>
      </section>
    </main>
  )
}
