import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import Link from 'next/link'

const AUTHOR_MAP: Record<string, { name: string; bio: string; title: string; sameAs?: string[] }> = {
  'javier-valencia': {
    name: 'Javier Valencia',
    title: 'Fundador y Editor en Jefe de NewsTide',
    bio: 'Javier Valencia es el fundador de NewsTide, medio especializado en inteligencia artificial, startups y tecnología para profesionales de habla hispana. Revisa y edita cada artículo publicado en la plataforma, combinando análisis propio con asistencia de IA para ofrecer contenido riguroso y actualizado.',
    sameAs: ['https://twitter.com/newstide'],
  },
}

export async function generateStaticParams() {
  return Object.keys(AUTHOR_MAP).map((slug) => ({ slug }))
}

export async function generateMetadata(
  { params }: { params: Promise<{ slug: string }> }
): Promise<Metadata> {
  const { slug } = await params
  const author = AUTHOR_MAP[slug]
  if (!author) return { title: 'Autor no encontrado' }
  const url = `https://www.newstide.news/autores/${slug}`
  const enUrl = `https://www.newstide.news/en/authors/${slug}`
  return {
    title: `${author.name} — ${author.title} | NewsTide`,
    description: author.bio,
    alternates: {
      canonical: url,
      languages: { 'es': url, 'en': enUrl, 'x-default': url },
    },
    openGraph: {
      title: `${author.name} — NewsTide`,
      description: author.bio,
      url,
      siteName: 'NewsTide',
      locale: 'es_ES',
      type: 'profile',
    },
  }
}

export default async function AutorPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const author = AUTHOR_MAP[slug]
  if (!author) notFound()

  const url = `https://www.newstide.news/autores/${slug}`

  const { data: articles } = await supabase
    .from('articles')
    .select('title, slug, published_at, category, excerpt')
    .order('published_at', { ascending: false })
    .limit(50)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'ProfilePage',
    url,
    mainEntity: {
      '@type': 'Person',
      '@id': url,
      name: author.name,
      jobTitle: author.title,
      description: author.bio,
      url,
      ...(author.sameAs ? { sameAs: author.sameAs } : {}),
      worksFor: {
        '@type': 'NewsMediaOrganization',
        '@id': 'https://www.newstide.news/#organization',
        name: 'NewsTide',
        url: 'https://www.newstide.news',
      },
    },
  }

  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <div className="container" style={{ maxWidth: 820, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Inicio</Link>
        </div>
        <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', marginBottom: 48, flexWrap: 'wrap' }}>
          <div style={{
            width: 80, height: 80, borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--cyan), #9b8cef)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 28, fontWeight: 800, color: 'var(--bg)', flexShrink: 0,
          }}>
            JV
          </div>
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 4 }}>{author.name}</h1>
            <p style={{ fontSize: 14, color: 'var(--cyan)', fontWeight: 600, marginBottom: 12 }}>{author.title}</p>
            <p style={{ fontSize: 15, color: 'var(--muted)', lineHeight: 1.7, maxWidth: 600 }}>{author.bio}</p>
            <div style={{ marginTop: 14, display: 'flex', gap: 10 }}>
              <a href="https://twitter.com/newstide" target="_blank" rel="noopener noreferrer"
                style={{ fontSize: 12, color: 'var(--cyan)', border: '1px solid rgba(110,207,202,0.3)', borderRadius: 6, padding: '4px 10px', textDecoration: 'none' }}>
                Twitter / X
              </a>
            </div>
          </div>
        </div>

        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: 24 }}>Artículos recientes</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {(articles || []).map((a) => (
            <Link
              key={a.slug}
              href={`/articulo/${a.slug}`}
              style={{
                display: 'block', padding: '20px 24px',
                background: 'var(--surface)', border: '1px solid var(--border)',
                borderRadius: 12, textDecoration: 'none',
                transition: 'border-color 0.2s',
              }}
            >
              <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6 }}>
                {a.category} · {new Date(a.published_at).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })}
              </div>
              <div style={{ fontWeight: 600, fontSize: 16, color: 'var(--text)', marginBottom: 6 }}>{a.title}</div>
              {a.excerpt && <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.5 }}>{a.excerpt}</div>}
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
