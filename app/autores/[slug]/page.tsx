import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'

const AUTHOR_MAP: Record<string, {
  name: string; bio: string; title: string; sameAs?: string[]; image?: string; credentials?: string[]
}> = {
  'javier-valencia': {
    name: 'Javier Valencia',
    title: 'Fundador y Editor en Jefe de NewsTide',
    bio: 'Javier Valencia es ingeniero de software y estudiante de Ingeniería Informática. Fundó NewsTide para explorar la intersección entre pipelines de automatización de contenido con IA y el periodismo de calidad. Ha trabajado como freelance para empresas tech, desarrollado proyectos de gemelos digitales y participado en concursos de innovación y startups. Combina su experiencia en desarrollo full-stack (Next.js, Python, Supabase) con supervisión editorial en cada artículo publicado.',
    image: '/authors/7e13d624-55ae-4d72-b4aa-27aac63b4c14.jpeg',
    sameAs: [
      'https://www.linkedin.com/in/javier-valencia-mu%C3%B1oz-b193ab2ba',
      'https://github.com/Javivalenciaa',
      'https://twitter.com/newstide',
    ],
    credentials: [
      'Ingeniería Informática (en curso)',
      'Fundador de NewsTide',
      'Desarrollo full-stack: Next.js, Python, Supabase',
      'Proyectos de gemelos digitales e IA',
      'Freelance tech para empresas',
    ],
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
      languages: { 'es': url, 'en': enUrl, 'x-default': enUrl },
    },
    openGraph: {
      title: `${author.name} — NewsTide`,
      description: author.bio,
      url,
      siteName: 'NewsTide',
      locale: 'es_ES',
      type: 'profile',
      images: author.image
        ? [{ url: `https://www.newstide.news${author.image}`, width: 400, height: 400, alt: author.name }]
        : [],
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
      image: author.image
        ? { '@type': 'ImageObject', url: `https://www.newstide.news${author.image}`, width: 400, height: 400 }
        : undefined,
      sameAs: author.sameAs || [],
      hasCredential: (author.credentials || []).map((c) => ({
        '@type': 'EducationalOccupationalCredential',
        credentialCategory: c,
      })),
      worksFor: {
        '@type': 'NewsMediaOrganization',
        '@id': 'https://www.newstide.news/#organization',
        name: 'NewsTide',
        url: 'https://www.newstide.news',
      },
      knowsAbout: [
        'Inteligencia Artificial',
        'Startups',
        'Ingeniería de Software',
        'Next.js',
        'Python',
        'Gemelos Digitales',
        'SEO',
      ],
    },
  }

  const linkedin = (author.sameAs || []).find((s) => s.includes('linkedin'))
  const github   = (author.sameAs || []).find((s) => s.includes('github'))

  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <div className="container" style={{ maxWidth: 820, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Inicio</Link>
        </div>
        <div style={{ display: 'flex', gap: 28, alignItems: 'flex-start', marginBottom: 48, flexWrap: 'wrap' }}>
          {author.image ? (
            <Image
              src={author.image}
              alt={`Foto de ${author.name}`}
              width={88}
              height={88}
              style={{ borderRadius: '50%', objectFit: 'cover', flexShrink: 0, border: '2px solid var(--border)' }}
              priority
            />
          ) : (
            <div style={{
              width: 88, height: 88, borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--cyan), #9b8cef)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 28, fontWeight: 800, color: 'var(--bg)', flexShrink: 0,
            }}>JV</div>
          )}
          <div style={{ flex: 1 }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 4 }}>{author.name}</h1>
            <p style={{ fontSize: 14, color: 'var(--cyan)', fontWeight: 600, marginBottom: 12 }}>{author.title}</p>
            <p style={{ fontSize: 15, color: 'var(--muted)', lineHeight: 1.7, maxWidth: 620 }}>{author.bio}</p>
            {author.credentials && (
              <div style={{ marginTop: 16, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {author.credentials.map((c) => (
                  <span key={c} style={{
                    fontSize: 11, padding: '3px 10px', borderRadius: 20,
                    border: '1px solid var(--border)', color: 'var(--muted)',
                  }}>{c}</span>
                ))}
              </div>
            )}
            <div style={{ marginTop: 16, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {linkedin && (
                <a href={linkedin} target="_blank" rel="noopener noreferrer"
                  style={{ fontSize: 12, color: 'var(--cyan)', border: '1px solid rgba(110,207,202,0.3)', borderRadius: 6, padding: '4px 12px', textDecoration: 'none' }}>
                  LinkedIn
                </a>
              )}
              {github && (
                <a href={github} target="_blank" rel="noopener noreferrer"
                  style={{ fontSize: 12, color: 'var(--cyan)', border: '1px solid rgba(110,207,202,0.3)', borderRadius: 6, padding: '4px 12px', textDecoration: 'none' }}>
                  GitHub
                </a>
              )}
            </div>
          </div>
        </div>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: 24 }}>Artículos recientes</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {(articles || []).map((a) => (
            <Link key={a.slug} href={`/articulo/${a.slug}`}
              style={{ display: 'block', padding: '20px 24px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, textDecoration: 'none', transition: 'border-color 0.2s' }}
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
