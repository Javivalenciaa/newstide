import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { notFound, permanentRedirect } from 'next/navigation'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import NewsletterForm from '@/components/NewsletterForm'
import ShareButtons from '@/components/ShareButtons'

export const revalidate = 300

const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef',
  'Herramientas': '#e8d5a3', 'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c'
}

const CAT_SLUG_ES: Record<string, string> = {
  'IA': 'ia', 'Tutoriales': 'tutoriales',
  'Herramientas': 'herramientas', 'Startups': 'startups', 'Noticias': 'noticias',
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

export async function generateStaticParams() {
  const { data } = await supabase.from('articles').select('slug')
  return (data || []).map((a) => ({ slug: a.slug }))
}

export async function generateMetadata(
  { params }: { params: Promise<{ slug: string }> }
): Promise<Metadata> {
  const { slug } = await params

  const { data: article } = await supabase
    .from('articles')
    .select('title, excerpt, slug, slug_en, category, published_at, cover_image_url, author')
    .eq('slug', slug)
    .maybeSingle()

  if (!article) return { title: 'Artículo no encontrado', description: 'Este contenido no está disponible en NewsTide.' }

  const title = article.title
  const description = article.excerpt || 'Tecnología, IA y tendencias para founders, developers y profesionales.'
  const url = `https://www.newstide.news/articulo/${article.slug}`
  const enSlug = article.slug_en
  const urlEN = enSlug ? `https://www.newstide.news/en/article/${enSlug}` : undefined
  const images = article.cover_image_url
    ? [{ url: article.cover_image_url, width: 1200, height: 630, alt: title }]
    : []

  return {
    title,
    description,
    alternates: {
      canonical: url,
      languages: {
        'es': url,
        ...(urlEN ? { 'en': urlEN, 'x-default': urlEN } : { 'x-default': url }),
      },
    },
    openGraph: {
      title, description, url,
      siteName: 'NewsTide', locale: 'es_ES', type: 'article',
      publishedTime: article.published_at,
      authors: ['NewsTide Editorial'],
      images,
    },
    twitter: {
      card: 'summary_large_image', title, description,
      ...(article.cover_image_url ? { images: [article.cover_image_url] } : {}),
    },
  }
}

const CAT_SECTION: Record<string, string> = {
  'IA': 'Inteligencia Artificial', 'Startups': 'Startups',
  'Herramientas': 'Herramientas y Tecnología', 'Tutoriales': 'Tutoriales', 'Noticias': 'Noticias',
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

  if (!article) {
    const { data: bySlugEn } = await supabase
      .from('articles')
      .select('slug')
      .eq('slug_en', slug)
      .maybeSingle()

    if (bySlugEn?.slug) {
      permanentRedirect(`/articulo/${bySlugEn.slug}`)
    }

    notFound()
  }

  const catSlug = CAT_SLUG_ES[article.category] || article.category.toLowerCase()
  const enSlug = article.slug_en
  const url = `https://www.newstide.news/articulo/${article.slug}`
  const urlEN = enSlug ? `https://www.newstide.news/en/article/${enSlug}` : null

  const { data: related } = await supabase
    .from('articles')
    .select('title, slug, category, published_at')
    .eq('category', article.category)
    .neq('slug', article.slug)
    .order('published_at', { ascending: false })
    .limit(8)

  const { data: latest } = await supabase
    .from('articles')
    .select('title, slug')
    .neq('slug', article.slug)
    .order('published_at', { ascending: false })
    .limit(5)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'NewsArticle',
    headline: article.title,
    description: article.excerpt || '',
    url,
    datePublished: article.published_at,
    dateModified: article.updated_at || article.published_at,
    inLanguage: 'es',
    isAccessibleForFree: true,
    articleSection: CAT_SECTION[article.category] || article.category,
    speakable: { '@type': 'SpeakableSpecification', cssSelector: ['.article-main-title', '.article-byline'] },
    author: {
      '@type': 'Organization',
      name: 'NewsTide Editorial',
      url: 'https://www.newstide.news/equipo-editorial',
    },
    publisher: {
      '@type': 'NewsMediaOrganization',
      '@id': 'https://www.newstide.news/#organization',
      name: 'NewsTide',
      url: 'https://www.newstide.news',
      logo: { '@type': 'ImageObject', url: 'https://www.newstide.news/favicon-192x192.png', width: 192, height: 192 },
    },
    ...(article.cover_image_url ? { image: { '@type': 'ImageObject', url: article.cover_image_url, width: 1200, height: 630 } } : {}),
    mainEntityOfPage: { '@type': 'WebPage', '@id': url },
  }

  return (
    <div className="article-page">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      {/* HERO */}
      <div className="article-hero" style={{ background: article.image_gradient }}>
        <div className="article-hero-overlay" />
        <div className="container">
          <div className="article-header">
            <nav aria-label="Miga de pan" style={{ marginBottom: 16 }}>
              <ol style={{ display: 'flex', alignItems: 'center', gap: 6, listStyle: 'none', padding: 0, margin: 0, flexWrap: 'wrap' }}>
                <li><Link href="/" style={{ fontSize: 13, color: 'var(--muted)' }}>Inicio</Link></li>
                <li style={{ color: 'var(--faint)', fontSize: 13 }}>/</li>
                <li><Link href={`/articulos/${catSlug}`} style={{ fontSize: 13, color: 'var(--muted)' }}>{article.category}</Link></li>
                <li style={{ color: 'var(--faint)', fontSize: 13 }}>/</li>
                <li style={{ fontSize: 13, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200 }} aria-current="page">{article.title}</li>
              </ol>
            </nav>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
              <Badge cat={article.category} />
              <span className="meta-sep">·</span>
              <Link href="/equipo-editorial" style={{ fontSize: 13, color: 'var(--muted)', textDecoration: 'none' }}>NewsTide Editorial</Link>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{formatDate(article.published_at)}</span>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{article.reading_time} min de lectura</span>
              {urlEN && (
                <><span className="meta-sep">·</span>
                <Link href={urlEN} style={{ fontSize: 12, color: 'var(--muted)', border: '1px solid var(--border)', borderRadius: 6, padding: '2px 8px' }}>🇬🇧 EN</Link></>
              )}
            </div>
            <h1 className="article-main-title">{article.title}</h1>
            <p className="article-byline">{article.excerpt}</p>
          </div>
        </div>
      </div>

      {/* CUERPO + SIDEBAR */}
      <div className="container">
        <div className="article-body-grid">
          <article lang="es">
            <ReactMarkdown
              components={{
                h2: ({ children }) => (<h2 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.03em', margin: '40px 0 16px', color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: 10 }}>{children}</h2>),
                h3: ({ children }) => (<h3 style={{ fontSize: '1.15rem', fontWeight: 600, margin: '28px 0 12px', color: 'var(--text)' }}>{children}</h3>),
                p: ({ children }) => (<p style={{ fontSize: 17, lineHeight: 1.8, color: 'rgba(240,240,238,0.85)', marginBottom: 20 }}>{children}</p>),
                img: ({ src, alt }) => (src ? (<span style={{ display: 'block', margin: '32px 0' }}><img src={src} alt={alt || ''} loading="lazy" style={{ width: '100%', height: 'auto', borderRadius: 12, objectFit: 'cover', maxHeight: 480, display: 'block', border: '1px solid var(--border)' }} /></span>) : null),
                ul: ({ children }) => <ul style={{ margin: '16px 0 20px 24px' }}>{children}</ul>,
                ol: ({ children }) => <ol style={{ margin: '16px 0 20px 24px' }}>{children}</ol>,
                li: ({ children }) => <li style={{ fontSize: 16, lineHeight: 1.7, color: 'rgba(240,240,238,0.8)', marginBottom: 8 }}>{children}</li>,
                strong: ({ children }) => <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{children}</strong>,
                blockquote: ({ children }) => (<blockquote style={{ borderLeft: '3px solid var(--cyan)', paddingLeft: 20, margin: '24px 0', color: 'var(--muted)', fontStyle: 'italic' }}>{children}</blockquote>),
                code: ({ children }) => (<code style={{ fontFamily: 'var(--mono)', fontSize: 13, background: 'var(--surface)', border: '1px solid var(--border)', padding: '2px 7px', borderRadius: 5, color: 'var(--cyan)' }}>{children}</code>),
                hr: () => <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '40px 0' }} />,
              }}
            >
              {article.content}
            </ReactMarkdown>

            <div style={{ marginTop: 48, padding: '16px 20px', background: 'rgba(110,207,202,0.05)', border: '1px solid rgba(110,207,202,0.15)', borderRadius: 10, fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
              <strong style={{ color: 'var(--cyan)' }}>Nota editorial:</strong> Este artículo ha sido generado con asistencia de inteligencia artificial y revisado por el equipo editorial de NewsTide para garantizar su precisión y relevancia. <Link href="/politica-editorial" style={{ color: 'var(--cyan)' }}>Conoce nuestra política editorial.</Link>
            </div>

            {related && related.length > 0 && (
              <div style={{ marginTop: 48 }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 20, color: 'var(--text)' }}>Más sobre {article.category}</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {related.map((r) => (
                    <Link key={r.slug} href={`/articulo/${r.slug}`}
                      style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '12px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, textDecoration: 'none', transition: 'border-color 0.2s' }}>
                      <span style={{ fontSize: 18, flexShrink: 0 }}>→</span>
                      <span style={{ fontSize: 14, color: 'var(--text)', fontWeight: 500, lineHeight: 1.4 }}>{r.title}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div style={{ marginTop: 40, paddingTop: 32, borderTop: '1px solid var(--border)', display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
              <Link href="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--cyan)', fontSize: 14, fontWeight: 600 }}>← Volver al inicio</Link>
              <Link href={`/articulos/${catSlug}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--muted)', fontSize: 14 }}>Ver todos de {article.category} →</Link>
            </div>
          </article>

          <aside>
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Publicado por</div>
              <Link href="/equipo-editorial" style={{ textDecoration: 'none' }}>
                <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6, color: 'var(--text)' }}>NewsTide Editorial</div>
              </Link>
              <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.5, marginBottom: 10 }}>Contenido elaborado con asistencia de IA y revisado por nuestro equipo.</div>
              <Link href="/politica-editorial" style={{ fontSize: 12, color: 'var(--cyan)' }}>Política editorial →</Link>
            </div>

            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Detalles</div>
              <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 2.2 }}>
                <div>📅 {formatDate(article.published_at)}</div>
                <div>⏱ {article.reading_time} min de lectura</div>
                <div>🏷 <Link href={`/articulos/${catSlug}`} style={{ color: 'var(--cyan)' }}>{article.category}</Link></div>
              </div>
            </div>

            {latest && latest.length > 0 && (
              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
                <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 14 }}>Últimas noticias</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {latest.map((a) => (
                    <Link key={a.slug} href={`/articulo/${a.slug}`}
                      style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.4, textDecoration: 'none', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                      {a.title}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* NEWSLETTER — real */}
            <div style={{ background: 'linear-gradient(135deg, rgba(110,207,202,0.08), rgba(155,140,239,0.08))', border: '1px solid rgba(110,207,202,0.2)', borderRadius: 14, padding: 24 }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 8 }}>✉️ Newsletter</div>
              <p style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6, marginBottom: 16 }}>Las mejores historias de la semana en tu inbox.</p>
              <NewsletterForm />
            </div>

            {/* COMPARTIR — real */}
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginTop: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Compartir</div>
              <ShareButtons url={url} title={article.title} />
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
