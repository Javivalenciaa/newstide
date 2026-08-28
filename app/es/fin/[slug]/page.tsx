import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import NewsletterForm from '@/components/NewsletterForm'
import ShareButtons from '@/components/ShareButtons'

export const revalidate = 300
export const dynamicParams = true

const FIN_CAT_COLORS: Record<string, string> = {
  'Saving Money':  '#6ecfca',
  'Budgeting':     '#9b8cef',
  'Investing':     '#7ecf9b',
  'Debt':          '#ef6c6c',
  'Credit':        '#e8d5a3',
  'Side Hustles':  '#f0a050',
  // Categorías reales de finance_pipeline.py's detect_category() (FIN_CATEGORIES)
  'Crédito':        '#e8d5a3',
  'Impuestos':      '#f0a050',
  'Ahorro':         '#6ecfca',
  'Presupuesto':    '#9b8cef',
  'Inversión':      '#7ecf9b',
  'Remesas':        '#8ecae6',
  'Deudas':         '#ef6c6c',
  'Vivienda':       '#c9a0f5',
  'Ingresos Extra': '#ffd166',
}

const AUTHOR_SLUG   = 'javier-valencia'
const AUTHOR_PAGE_ES = `https://www.newstide.news/autores/${AUTHOR_SLUG}`

function Badge({ cat }: { cat: string }) {
  const color = FIN_CAT_COLORS[cat] || '#6ecfca'
  return (
    <span style={{
      display: 'inline-block', padding: '4px 10px', borderRadius: '6px',
      fontSize: '10px', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase',
      background: `${color}18`, color, border: `1px solid ${color}30`,
    }}>{cat}</span>
  )
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
}

function seoTitle(title: string, siteName = 'NewsTide'): string {
  const max = 60 - siteName.length - 3
  if (title.length <= max) return `${title} | ${siteName}`
  const cut = title.substring(0, max)
  const lastSpace = cut.lastIndexOf(' ')
  return `${cut.substring(0, lastSpace > 20 ? lastSpace : max)} | ${siteName}`
}

function seoDescription(excerpt: string, fallback: string): string {
  const text = excerpt || fallback
  if (text.length <= 155) return text
  const cut = text.substring(0, 152)
  const lastSpace = cut.lastIndexOf(' ')
  return `${cut.substring(0, lastSpace > 50 ? lastSpace : 152)}...`
}

function extractFAQs(content: string): Array<{ question: string; answer: string }> {
  const faqs: Array<{ question: string; answer: string }> = []
  const h3Regex = /^###\s+(.+\?)\s*\n+([^#]+)/gm
  let match
  while ((match = h3Regex.exec(content)) !== null && faqs.length < 5) {
    const question = match[1].trim()
    const answer = match[2].replace(/\*\*/g, '').trim().substring(0, 300)
    if (question && answer) faqs.push({ question, answer })
  }
  return faqs
}

// Only for genuine "Cómo X" titles — steps are the article's real H2 sections,
// nothing invented. Skips FAQ/conclusion sections, which aren't steps.
function extractHowToSteps(content: string, title: string): Array<{ name: string; text: string }> {
  if (!/^(cómo|como)\b/i.test(title.trim())) return []
  const steps: Array<{ name: string; text: string }> = []
  const sections = content.split(/^##\s+/m).slice(1)
  for (const section of sections) {
    const lines = section.split('\n')
    const heading = (lines[0] || '').trim()
    if (!heading || /^(faq|preguntas frecuentes|conclusión|conclusion|cuándo esto no funciona)/i.test(heading)) continue
    let text = ''
    for (const line of lines.slice(1)) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('!') || trimmed.startsWith('|')) continue
      text = trimmed.replace(/\*\*(.+?)\*\*/g, '$1').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      break
    }
    if (heading && text) steps.push({ name: heading, text: text.slice(0, 300) })
    if (steps.length >= 8) break
  }
  return steps.length >= 3 ? steps : []
}

// Conservative: only real brand names lifted verbatim from a "X vs Y" title, no invented data.
// Uses generic Organization (not SoftwareApplication) — finance comparisons are banks/fintech
// brands (Chime, Bank of America), not necessarily software products.
function extractBrandMentions(title: string): Array<{ name: string }> {
  const m = title.match(/^(.+?)\s+vs\.?\s+(.+?)(?:[:\-–—]|$)/i)
  if (!m) return []
  const a = m[1].trim()
  const b = m[2].trim()
  if (!a || !b || a.length > 40 || b.length > 40) return []
  return [{ name: a }, { name: b }]
}

export async function generateStaticParams() {
  const { data } = await supabase.from('finance_articles').select('slug').not('slug', 'is', null)
  return (data || []).map((a) => ({ slug: a.slug }))
}

export async function generateMetadata(
  { params }: { params: Promise<{ slug: string }> }
): Promise<Metadata> {
  const { slug } = await params
  const { data: article } = await supabase
    .from('finance_articles')
    .select('title, excerpt, slug, category, published_at, cover_image_url')
    .eq('slug', slug)
    .maybeSingle()

  if (!article) return {
    title: 'Artículo no encontrado | NewsTide',
    description: 'Este contenido no está disponible en NewsTide.'
  }

  const rawTitle    = article.title
  const title       = seoTitle(rawTitle)
  const description = seoDescription(
    article.excerpt,
    'Guía práctica de finanzas personales en NewsTide.'
  )
  const url    = `https://www.newstide.news/es/fin/${article.slug}`
  const images = article.cover_image_url
    ? [{ url: article.cover_image_url, width: 1200, height: 630, alt: rawTitle }]
    : [{
        url: `https://www.newstide.news/api/og?title=${encodeURIComponent(title)}&category=${encodeURIComponent(article.category || '')}`,
        width: 1200, height: 630, alt: rawTitle,
      }]

  return {
    title,
    description,
    alternates: {
      canonical: url,
      languages: { 'es': url, 'x-default': url },
    },
    openGraph: {
      title: rawTitle,
      description,
      url,
      siteName: 'NewsTide',
      locale: 'es_ES',
      type: 'article',
      publishedTime: article.published_at,
      authors: ['Javier Valencia'],
      images,
    },
    twitter: {
      card: 'summary_large_image',
      title: rawTitle,
      description,
      images: article.cover_image_url
        ? [article.cover_image_url]
        : ['https://www.newstide.news/og-image.png'],
    },
  }
}

export default async function FinanceArticlePageEs({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params

  const { data: article } = await supabase
    .from('finance_articles')
    .select('*')
    .eq('slug', slug)
    .maybeSingle()

  if (!article) notFound()

  const title   = article.title
  const content = article.content
  const excerpt = article.excerpt
  const url     = `https://www.newstide.news/es/fin/${article.slug}`
  const faqs         = extractFAQs(content || '')
  const howToSteps   = extractHowToSteps(content || '', title)
  const brandMentions = extractBrandMentions(title)

  // Prefer the persisted related_articles column (computed once at publish time
  // by compute_related_articles() in finance_pipeline.py); falls back to a live
  // query for articles published before that column existed.
  type RelatedFin = { title: string; slug: string; category?: string }
  const persistedRelatedEs: RelatedFin[] = Array.isArray(article.related_articles)
    ? article.related_articles.filter((r: { slug?: string }) => r?.slug)
    : []

  let related: RelatedFin[] | null = persistedRelatedEs.length > 0 ? persistedRelatedEs : null
  if (!related) {
    const { data } = await supabase
      .from('finance_articles')
      .select('title, slug, category, published_at')
      .eq('category', article.category)
      .neq('slug', article.slug)
      .order('published_at', { ascending: false })
      .limit(6)
    related = data
  }

  const { data: latest } = await supabase
    .from('finance_articles')
    .select('title, slug')
    .neq('slug', article.slug)
    .order('published_at', { ascending: false })
    .limit(5)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: title,
    description: excerpt || '',
    url,
    datePublished: article.published_at,
    dateModified: article.updated_at || article.published_at,
    inLanguage: 'es',
    isAccessibleForFree: true,
    articleSection: article.category,
    author: {
      '@type': 'Person',
      '@id': AUTHOR_PAGE_ES,
      name: 'Javier Valencia',
      url: AUTHOR_PAGE_ES,
      jobTitle: 'Fundador y Editor en Jefe',
      worksFor: { '@id': 'https://www.newstide.news/#organization' },
    },
    publisher: {
      '@type': 'NewsMediaOrganization',
      '@id': 'https://www.newstide.news/#organization',
      name: 'NewsTide',
      url: 'https://www.newstide.news',
      logo: { '@type': 'ImageObject', url: 'https://www.newstide.news/favicon-192x192.png', width: 192, height: 192 },
    },
    image: article.cover_image_url
      ? { '@type': 'ImageObject', url: article.cover_image_url, width: 1200, height: 630 }
      : { '@type': 'ImageObject', url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630 },
    mainEntityOfPage: { '@type': 'WebPage', '@id': url },
    ...(brandMentions.length > 0 && {
      mentions: brandMentions.map((m) => ({ '@type': 'Organization', name: m.name })),
    }),
  }

  const faqSchema = faqs.length > 0 ? {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map(({ question, answer }) => ({
      '@type': 'Question',
      name: question,
      acceptedAnswer: { '@type': 'Answer', text: answer },
    })),
  } : null

  const howToSchema = howToSteps.length > 0 ? {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: title,
    step: howToSteps.map(({ name, text }) => ({ '@type': 'HowToStep', name, text })),
  } : null

  return (
    <div className="article-page" lang="es">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      {faqSchema && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }} />
      )}
      {howToSchema && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }} />
      )}

      <div className="article-hero" style={{ background: article.image_gradient || 'linear-gradient(135deg,#0d2a1a,#0a1a0a)' }}>
        <div className="article-hero-overlay" />
        <div className="container">
          <div className="article-header">
            <nav aria-label="Breadcrumb" style={{ marginBottom: 16 }}>
              <ol style={{ display: 'flex', alignItems: 'center', gap: 6, listStyle: 'none', padding: 0, margin: 0, flexWrap: 'wrap' }}>
                <li><Link href="/es" style={{ fontSize: 13, color: 'var(--muted)' }}>Inicio</Link></li>
                <li style={{ color: 'var(--faint)', fontSize: 13 }}>/</li>
                <li><Link href="/es/fin" style={{ fontSize: 13, color: 'var(--muted)' }}>Finanzas Personales</Link></li>
                <li style={{ color: 'var(--faint)', fontSize: 13 }}>/</li>
                <li style={{ fontSize: 13, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200 }} aria-current="page">{title}</li>
              </ol>
            </nav>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
              <Badge cat={article.category} />
              <span className="meta-sep">·</span>
              <Link href={AUTHOR_PAGE_ES} style={{ fontSize: 13, color: 'var(--muted)', textDecoration: 'none', fontWeight: 500 }}>Javier Valencia</Link>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 12, color: 'var(--faint)' }}>Revisado por NewsTide Finanzas</span>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{formatDate(article.published_at)}</span>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{article.reading_time} min de lectura</span>
            </div>
            <h1 className="article-main-title">{title}</h1>
            <p className="article-byline">{excerpt}</p>
          </div>
        </div>
      </div>

      <div className="container">
        <div className="article-body-grid">
          <article>
            {article.cover_image_url && (
              <div style={{ margin: '0 0 32px' }}>
                <img
                  src={article.cover_image_url}
                  alt={title}
                  style={{ width: '100%', height: 'auto', borderRadius: 12, objectFit: 'cover', maxHeight: 480, display: 'block', border: '1px solid var(--border)' }}
                />
              </div>
            )}
            <ReactMarkdown
              components={{
                h2: ({ children }) => (<h2 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.03em', margin: '40px 0 16px', color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: 10 }}>{children}</h2>),
                h3: ({ children }) => (<h3 style={{ fontSize: '1.15rem', fontWeight: 600, margin: '28px 0 12px', color: 'var(--text)' }}>{children}</h3>),
                p: ({ children }) => (<p style={{ fontSize: 17, lineHeight: 1.8, color: 'rgba(240,240,238,0.85)', marginBottom: 20 }}>{children}</p>),
                img: ({ src, alt }) => {
                  const cleanAlt = (alt && alt.length > 10 && !alt.startsWith('a ') && !alt.startsWith('an '))
                    ? alt : `${title} — NewsTide Finanzas`
                  return src ? (
                    <span style={{ display: 'block', margin: '32px 0' }}>
                      <img src={src} alt={cleanAlt} loading="lazy" style={{ width: '100%', height: 'auto', borderRadius: 12, objectFit: 'cover', maxHeight: 480, display: 'block', border: '1px solid var(--border)' }} />
                    </span>
                  ) : null
                },
                ul: ({ children }) => <ul style={{ margin: '16px 0 20px 24px' }}>{children}</ul>,
                ol: ({ children }) => <ol style={{ margin: '16px 0 20px 24px' }}>{children}</ol>,
                li: ({ children }) => <li style={{ fontSize: 16, lineHeight: 1.7, color: 'rgba(240,240,238,0.8)', marginBottom: 8 }}>{children}</li>,
                strong: ({ children }) => <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{children}</strong>,
                blockquote: ({ children }) => (<blockquote style={{ borderLeft: '3px solid var(--cyan)', paddingLeft: 20, margin: '24px 0', color: 'var(--muted)', fontStyle: 'italic' }}>{children}</blockquote>),
                code: ({ children }) => (<code style={{ fontFamily: 'var(--mono)', fontSize: 13, background: 'var(--surface)', border: '1px solid var(--border)', padding: '2px 7px', borderRadius: 5, color: 'var(--cyan)' }}>{children}</code>),
                hr: () => <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '40px 0' }} />,
              }}
            >
              {content}
            </ReactMarkdown>

            <div style={{ marginTop: 48, padding: '16px 20px', background: 'rgba(110,207,202,0.05)', border: '1px solid rgba(110,207,202,0.15)', borderRadius: 10, fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
              <strong style={{ color: 'var(--cyan)' }}>Nota editorial:</strong> Este artículo fue producido con asistencia de IA y revisado por Javier Valencia para garantizar su precisión. El contenido es solo para fines informativos, no constituye asesoría financiera. <Link href="/es/politica-editorial" style={{ color: 'var(--cyan)' }}>Lee nuestra política editorial.</Link>
            </div>

            {related && related.length > 0 && (
              <div style={{ marginTop: 48 }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 20, color: 'var(--text)' }}>Más sobre {article.category}</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {related.map((r) => (
                    <Link key={r.slug} href={`/es/fin/${r.slug}`}
                      style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '12px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, textDecoration: 'none', transition: 'border-color 0.2s' }}>
                      <span style={{ fontSize: 18, flexShrink: 0 }}>→</span>
                      <span style={{ fontSize: 14, color: 'var(--text)', fontWeight: 500, lineHeight: 1.4 }}>{r.title}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div style={{ marginTop: 40, paddingTop: 32, borderTop: '1px solid var(--border)', display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
              <Link href="/es/fin" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--cyan)', fontSize: 14, fontWeight: 600 }}>← Volver a Finanzas</Link>
            </div>
          </article>

          <aside>
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Autor</div>
              <Link href={AUTHOR_PAGE_ES} style={{ textDecoration: 'none' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, var(--cyan), #9b8cef)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 800, color: 'var(--bg)', flexShrink: 0 }}>JV</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)' }}>Javier Valencia</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>Revisado por NewsTide Finanzas</div>
                  </div>
                </div>
              </Link>
              <Link href="/es/politica-editorial" style={{ fontSize: 12, color: 'var(--cyan)' }}>Política editorial →</Link>
            </div>

            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Detalles</div>
              <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 2.2 }}>
                <div>📅 {formatDate(article.published_at)}</div>
                <div>⏱ {article.reading_time} min de lectura</div>
                <div>🏷 <Badge cat={article.category} /></div>
              </div>
            </div>

            {latest && latest.length > 0 && (
              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginBottom: 16 }}>
                <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 14 }}>Últimas de Finanzas</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {latest.map((a) => (
                    <Link key={a.slug} href={`/es/fin/${a.slug}`}
                      style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.4, textDecoration: 'none', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                      {a.title}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div style={{ background: 'linear-gradient(135deg, rgba(110,207,202,0.08), rgba(155,140,239,0.08))', border: '1px solid rgba(110,207,202,0.2)', borderRadius: 14, padding: 24 }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 8 }}>✉️ Newsletter</div>
              <p style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6, marginBottom: 16 }}>Consejos financieros semanales en tu correo.</p>
              <NewsletterForm compact />
            </div>

            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, marginTop: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Compartir</div>
              <ShareButtons url={url} title={title} />
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
