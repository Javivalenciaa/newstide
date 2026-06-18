import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import Link from 'next/link'

// Normalized author slugs → display name
const AUTHOR_MAP: Record<string, { name: string; bio: string; title: string; sameAs?: string[] }> = {
  'maria-lopez': {
    name: 'María López',
    title: 'Editora de IA y Tecnología',
    bio: 'María López cubre inteligencia artificial, modelos de lenguaje y herramientas para desarrolladores. Con más de 8 años de experiencia en periodismo tecnológico, ha seguido la evolución de la IA desde los primeros transformers hasta los modelos multimodales actuales.',
    sameAs: ['https://twitter.com/newstide', 'https://linkedin.com/company/newstide'],
  },
  'carlos-ruiz': {
    name: 'Carlos Ruiz',
    title: 'Editor de Finanzas y Mercados',
    bio: 'Carlos Ruiz es especialista en mercados financieros, criptomonedas y economía digital. Antes de unirse a NewsTide, trabajó como analista financiero y como corresponsal de economía en medios digitales especializados.',
    sameAs: ['https://twitter.com/newstide', 'https://linkedin.com/company/newstide'],
  },
  'ana-martinez': {
    name: 'Ana Martínez',
    title: 'Editora de Startups y Empresa',
    bio: 'Ana Martínez cubre el ecosistema emprendedor, rondas de financiación y el impacto de la tecnología en los modelos de negocio. Ha entrevistado a más de 200 founders y escrito sobre algunas de las startups más relevantes de Europa y Latinoamérica.',
    sameAs: ['https://twitter.com/newstide', 'https://linkedin.com/company/newstide'],
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
      languages: { 'es': url, 'en': enUrl },
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
    .eq('author', author.name)
    .order('published_at', { ascending: false })
    .limit(20)

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
            fontSize: 28, fontWeight: 800, color: 'var(--bg)', flexShrink: 0
          }}>
            {author.name.charAt(0)}
          </div>
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 4 }}>{author.name}</h1>
            <p style={{ fontSize: 14, color: 'var(--cyan)', fontWeight: 600, marginBottom: 12 }}>{author.title}</p>
            <p style={{ fontSize: 15, color: 'var(--muted)', lineHeight: 1.7, maxWidth: 600 }}>{author.bio}</p>
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
                transition: 'border-color 0.2s'
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
