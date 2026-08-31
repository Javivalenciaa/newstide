import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { notFound, permanentRedirect } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import ReactMarkdown from 'react-markdown'
import NewsletterForm from '@/components/NewsletterForm'
import ShareButtons from '@/components/ShareButtons'

// 1 hora: artículos se regeneran frecuentemente (relacionados frescos, fuentes).
// El publish-hook llama revalidatePath('/articulo/[slug]') en cada nueva publicación
// así que los artículos populares siempre tienen los relacionados actualizados.
export const revalidate = 3600

type RelatedArticle = { title: string; slug: string; category: string; published_at: string }

const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef',
  'Herramientas': '#e8d5a3', 'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c',
  // Categorías reales de pipeline.py's detect_category() (nicho solopreneur/indie hacker)
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

const CAT_SECTION: Record<string, string> = {
  'IA': 'Inteligencia Artificial', 'Startups': 'Startups',
  'Herramientas': 'Herramientas y Tecnología', 'Tutoriales': 'Tutoriales', 'Noticias': 'Noticias',
}

const CAT_KEYWORDS: Record<string, string[]> = {
  'IA': ['inteligencia artificial', 'machine learning', 'LLM', 'modelos de lenguaje', 'IA generativa'],
  'Startups': ['startups', 'financiación', 'venture capital', 'emprendimiento', 'tecnología'],
  'Herramientas': ['herramientas tech', 'software para developers', 'productividad', 'automatización'],
  'Tutoriales': ['tutorial', 'guía técnica', 'cómo hacer', 'desarrollo web', 'programación'],
  'Noticias': ['noticias tecnología', 'tech news', 'actualidad digital', 'innovación'],
  'AI Tools': ['herramientas IA', 'inteligencia artificial', 'agentes IA'],
  'Automation': ['automatización', 'n8n', 'zapier'],
  'Build & Launch': ['lanzar SaaS', 'MVP', 'shipping'],
  'Indie Hacking': ['indie hacking', 'bootstrapping', 'solopreneur'],
  'Growth': ['SEO', 'crecimiento', 'marketing de contenidos'],
  'Monetization': ['monetización', 'pricing', 'ingresos recurrentes'],
  'Freelancing': ['freelance', 'clientes', 'tarifas'],
  'Dev Stack': ['stack tecnológico', 'infraestructura', 'herramientas dev'],
}

// Fallback slug for any category not yet mapped above (was `.toLowerCase()`, unsafe for "Build & Launch").
function slugifyCategory(cat: string): string {
  return cat.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

const AUTHOR_SLUG = 'javier-valencia'

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

function seoTitle(title: string): string {
  const max = 57
  if (title.length <= max) return title
  const cut = title.substring(0, max)
  const lastSpace = cut.lastIndexOf(' ')
  return cut.substring(0, lastSpace > 20 ? lastSpace : max)
}

function seoDescription(excerpt: string, fallback: string): string {
  const text = excerpt || fallback
  if (text.length <= 155) return text
  const cut = text.substring(0, 152)
  const lastSpace = cut.lastIndexOf(' ')
  return `${cut.substring(0, lastSpace > 50 ? lastSpace : 152)}...`
}

function pickRelatedArticles(
  article: { title: string; keyword?: string; category: string },
  candidates: RelatedArticle[]
): RelatedArticle[] {
  const titleTokens = (article.title + ' ' + (article.keyword || ''))
    .toLowerCase().split(/\s+/).filter((t) => t.length > 3)
  return candidates
    .map((r) => {
      let score = 0
      if (r.category === article.category) score += 3
      const rTokens = r.title.toLowerCase().split(/\s+/)
      for (const token of titleTokens) { if (rTokens.includes(token)) score += 1 }
      return { ...r, score }
    })
    .sort((a, b) => (b as RelatedArticle & { score: number }).score - (a as RelatedArticle & { score: number }).score)
    .map(({ score: _score, ...r }) => r as RelatedArticle)
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

// Extract first plain-text paragraph for SpeakableSpecification and articleBody preview
function extractFirstParagraph(content: string): string {
  const lines = content.split('\n')
  for (const line of lines) {
    const trimmed = line.trim()
    // Skip headings, images, blank lines, horizontal rules
    if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('!') || trimmed.startsWith('---') || trimmed.startsWith('|')) continue
    // Remove markdown bold/italic/links for clean plain text
    const plain = trimmed
      .replace(/\*\*(.+?)\*\*/g, '$1')
      .replace(/\*(.+?)\*/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
    if (plain.length > 40) return plain.substring(0, 500)
  }
  return ''
}

// Count words for wordCount schema property
function countWords(content: string): number {
  return content.trim().split(/\s+/).filter(Boolean).length
}

// Only for genuine "Cómo X" titles — steps are the article's real H2 sections,
// nothing invented. Skips FAQ/conclusion/mistakes sections, which aren't steps.
function extractHowToSteps(content: string, title: string): Array<{ name: string; text: string }> {
  if (!/^(cómo|como)\b/i.test(title.trim())) return []
  const steps: Array<{ name: string; text: string }> = []
  const sections = content.split(/^##\s+/m).slice(1)
  for (const section of sections) {
    const lines = section.split('\n')
    const heading = (lines[0] || '').trim()
    if (!heading || /^(faq|preguntas frecuentes|conclusión|conclusion|errores comunes|lo que nadie te cuenta|para quién es esto)/i.test(heading)) continue
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

// Conservative: only real tool names lifted verbatim from a "X vs Y" title, no invented data.
function extractSoftwareMentions(title: string): Array<{ name: string }> {
  const m = title.match(/^(.+?)\s+vs\.?\s+(.+?)(?:[:\-–—]|$)/i)
  if (!m) return []
  const a = m[1].trim()
  const b = m[2].trim()
  if (!a || !b || a.length > 40 || b.length > 40) return []
  return [{ name: a }, { name: b }]
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
    .select('title, title_en, excerpt, slug, slug_en, category, published_at, cover_image_url, keyword')
    .eq('slug', slug)
    .maybeSingle()

  if (!article) return {
    title: 'Artículo no encontrado',
    description: 'Este contenido no está disponible en NewsTide — noticias de IA, startups y tecnología.'
  }

  const title       = seoTitle(article.title)
  const description = seoDescription(
    article.excerpt,
    'Tecnología, IA y tendencias para founders, developers y profesionales. Actualizado cada día en NewsTide.'
  )
  const url   = `https://www.newstide.news/articulo/${article.slug}`
  const urlEN = article.slug_en ? `https://www.newstide.news/en/article/${article.slug_en}` : undefined
  const images = article.cover_image_url
    ? [{ url: article.cover_image_url, width: 1200, height: 630, alt: article.title }]
    : [{
        url: `https://www.newstide.news/api/og?title=${encodeURIComponent(title)}&category=${encodeURIComponent(article.category || '')}`,
        width: 1200, height: 630, alt: article.title,
      }]

  // Build keyword list: category defaults + article keyword
  const catKws = CAT_KEYWORDS[article.category] || []
  const articleKw = article.keyword ? [article.keyword] : []
  const keywordsStr = [...new Set([...articleKw, ...catKws])].join(', ')

  // Legacy duplicate pair (published before 2026-08-13): the translation step
  // failed and stored the English text in the Spanish columns, so this URL and
  // its /en/article/ twin serve byte-identical content while hreflang claims
  // they are different languages. title === title_en identifies every one of
  // those rows exactly (26/26 verified in Supabase). This niche is
  // English-primary, so the /en/article/ URL is the canonical survivor and
  // this one drops out of the index instead of competing with it.
  const isDuplicateOfEnglish = !!article.title_en && article.title === article.title_en
  const canonicalUrl = isDuplicateOfEnglish && urlEN ? urlEN : url

  return {
    title,
    description,
    keywords: keywordsStr,
    ...(isDuplicateOfEnglish ? { robots: { index: false, follow: true } } : {}),
    alternates: {
      canonical: canonicalUrl,
      // A duplicate declares no language alternates: claiming a Spanish
      // version that is really English is the contradiction that made Google
      // distrust the pair in the first place.
      ...(isDuplicateOfEnglish ? {} : {
        languages: {
          'es': url,
          ...(urlEN ? { 'en': urlEN } : {}),
          'x-default': urlEN ?? url,
        },
      }),
    },
    openGraph: {
      title: article.title,
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
      title: article.title,
      description,
      images: article.cover_image_url
        ? [article.cover_image_url]
        : ['https://www.newstide.news/og-image.png'],
    },
  }
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
      .from('articles').select('slug').eq('slug_en', slug).maybeSingle()
    if (bySlugEn?.slug) permanentRedirect(`/articulo/${bySlugEn.slug}`)
    notFound()
  }

  const catSlug       = CAT_SLUG_ES[article.category] || slugifyCategory(article.category)
  const enSlug        = article.slug_en
  const url           = `https://www.newstide.news/articulo/${article.slug}`
  const urlEN         = enSlug ? `https://www.newstide.news/en/article/${enSlug}` : null
  const authorPageUrl = `https://www.newstide.news/autores/${AUTHOR_SLUG}`

  // Prefer the persisted related_articles column (computed once at publish time
  // by compute_related_articles() in pipeline.py); fall back to a live query for
  // older articles published before that column existed.
  const persistedRelated: RelatedArticle[] = Array.isArray(article.related_articles)
    ? article.related_articles
        .filter((r: { slug?: string; title?: string }) => r?.slug && r?.title)
        .map((r: { title: string; slug: string; category?: string }) => ({
          title: r.title, slug: r.slug, category: r.category || article.category, published_at: article.published_at,
        }))
    : []

  let relatedSmart: RelatedArticle[] = persistedRelated.slice(0, 4)
  if (relatedSmart.length === 0) {
    const { data: related } = await supabase
      .from('articles')
      .select('title, slug, category, published_at')
      .eq('category', article.category)
      .neq('slug', article.slug)
      .order('published_at', { ascending: false })
      .limit(12)

    relatedSmart = pickRelatedArticles(article, related || []).slice(0, 4)
  }

  const { data: latest } = await supabase
    .from('articles')
    .select('title, slug')
    .neq('slug', article.slug)
    .order('published_at', { ascending: false })
    .limit(5)

  const faqs        = extractFAQs(article.content || '')
  const howToSteps  = extractHowToSteps(article.content || '', article.title)
  const softwareMentions = extractSoftwareMentions(article.title)
  const firstPara   = extractFirstParagraph(article.content || '')
  const wordCount   = countWords(article.content || '')
  const catKws      = CAT_KEYWORDS[article.category] || []
  const articleKw   = article.keyword ? [article.keyword] : []
  const keywords    = [...new Set([...articleKw, ...catKws])]

  const articleSchema = {
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
    wordCount,
    keywords: keywords.join(', '),
    // SpeakableSpecification: 4 selectors so LLMs/voice assistants can extract
    // the most citable parts — title, byline, first paragraph, and the full article body
    speakable: {
      '@type': 'SpeakableSpecification',
      cssSelector: [
        '.article-main-title',
        '.article-byline',
        '.article-first-paragraph',
        '.article-body',
      ],
    },
    // articleBody preview: first paragraph as plain text for direct LLM extraction
    ...(firstPara ? { articleBody: firstPara } : {}),
    // about: semantic topic linking for LLM context graphs
    about: keywords.map((kw) => ({ '@type': 'Thing', name: kw })),
    author: {
      '@type': 'Person',
      '@id': `https://www.newstide.news/autores/${AUTHOR_SLUG}`,
      name: 'Javier Valencia',
      url: authorPageUrl,
      jobTitle: 'Fundador y Editor en Jefe',
      worksFor: { '@id': 'https://www.newstide.news/#organization' },
    },
    publisher: { '@id': 'https://www.newstide.news/#organization' },
    image: article.cover_image_url
      ? { '@type': 'ImageObject', url: article.cover_image_url, width: 1200, height: 630 }
      : { '@type': 'ImageObject', url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630 },
    mainEntityOfPage: { '@type': 'WebPage', '@id': url },
    isPartOf: { '@id': 'https://www.newstide.news/#website' },
    // Mention linked articles as cited entities — helps LLMs build topic graphs
    ...(relatedSmart.length > 0 ? {
      citation: relatedSmart.map((r) => ({
        '@type': 'Article',
        headline: r.title,
        url: `https://www.newstide.news/articulo/${r.slug}`,
      }))
    } : {}),
    ...(softwareMentions.length > 0 && {
      mentions: softwareMentions.map((m) => ({ '@type': 'SoftwareApplication', name: m.name })),
    }),
  }

  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Inicio', item: 'https://www.newstide.news' },
      { '@type': 'ListItem', position: 2, name: article.category, item: `https://www.newstide.news/articulos/${catSlug}` },
      { '@type': 'ListItem', position: 3, name: article.title, item: url },
    ],
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
    name: article.title,
    step: howToSteps.map(({ name, text }) => ({ '@type': 'HowToStep', name, text })),
  } : null

  // Track paragraph index to mark only the first real <p> with the speakable class
  let firstParaRendered = false

  return (
    <div className="article-page">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }} />
      {faqSchema && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }} />
      )}
      {howToSchema && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }} />
      )}

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
              <Link href={authorPageUrl} style={{ fontSize: 13, color: 'var(--muted)', textDecoration: 'none', fontWeight: 500 }}>Javier Valencia</Link>
              <span className="meta-sep">·</span>
              <span style={{ fontSize: 12, color: 'var(--faint)' }}>Revisado por NewsTide Editorial</span>
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

      <div className="container">
        <div className="article-body-grid">
          {/* article-body class enables the SpeakableSpecification cssSelector for LLMs */}
          <article lang="es" className="article-body">
            {/* Cover image: next/image with priority prevents LCP delay and reserves
                exact dimensions to eliminate CLS (no layout shift on load). */}
            {article.cover_image_url && (
              <div style={{ position: 'relative', width: '100%', aspectRatio: '1200 / 630', borderRadius: 12, overflow: 'hidden', marginBottom: 32, border: '1px solid var(--border)' }}>
                <Image
                  src={article.cover_image_url}
                  alt={article.title}
                  fill
                  priority
                  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 70vw, 800px"
                  style={{ objectFit: 'cover' }}
                />
              </div>
            )}

            <ReactMarkdown
              components={{
                h2: ({ children }) => (<h2 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.03em', margin: '40px 0 16px', color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: 10 }}>{children}</h2>),
                h3: ({ children }) => (<h3 style={{ fontSize: '1.15rem', fontWeight: 600, margin: '28px 0 12px', color: 'var(--text)' }}>{children}</h3>),
                p: ({ children }) => {
                  // Mark the very first rendered paragraph as article-first-paragraph
                  // so SpeakableSpecification and LLM crawlers can extract the lede directly
                  if (!firstParaRendered) {
                    firstParaRendered = true
                    return (
                      <p
                        className="article-first-paragraph"
                        style={{ fontSize: 17, lineHeight: 1.8, color: 'rgba(240,240,238,0.85)', marginBottom: 20 }}
                      >
                        {children}
                      </p>
                    )
                  }
                  return (<p style={{ fontSize: 17, lineHeight: 1.8, color: 'rgba(240,240,238,0.85)', marginBottom: 20 }}>{children}</p>)
                },
                img: ({ src, alt }) => {
                  if (!src) return null
                  const srcString = String(src)
                  const cleanAlt = (alt && alt.length > 10 && !alt.startsWith('a ') && !alt.startsWith('an '))
                    ? alt : `${article.title} — NewsTide`
                  return (
                    <span style={{ display: 'block', margin: '32px 0', position: 'relative', width: '100%', aspectRatio: '16/9', borderRadius: 12, overflow: 'hidden', border: '1px solid var(--border)' }}>
                      <Image
                        src={srcString}
                        alt={cleanAlt}
                        fill
                        loading="lazy"
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 70vw, 800px"
                        style={{ objectFit: 'cover' }}
                      />
                    </span>
                  )
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
              {article.content}
            </ReactMarkdown>

            <div style={{ marginTop: 48, padding: '16px 20px', background: 'rgba(110,207,202,0.05)', border: '1px solid rgba(110,207,202,0.15)', borderRadius: 10, fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
              <strong style={{ color: 'var(--cyan)' }}>Nota editorial:</strong> Este artículo ha sido elaborado con asistencia de inteligencia artificial y revisado por Javier Valencia para garantizar su precisión y relevancia. <Link href="/politica-editorial" style={{ color: 'var(--cyan)' }}>Conoce nuestra política editorial.</Link>
            </div>

            {(article.source_url || article.source_name) && (
              <div style={{ marginTop: 32, padding: '16px 20px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, fontSize: 13, color: 'var(--muted)', lineHeight: 1.6 }}>
                <div style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 10 }}>Fuentes</div>
                {article.source_url && (
                  <div style={{ marginBottom: 4 }}>
                    <a href={article.source_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)', wordBreak: 'break-all' }}>{article.source_url}</a>
                  </div>
                )}
                {article.source_name && <div style={{ marginBottom: 4 }}><strong style={{ color: 'var(--text)' }}>{article.source_name}</strong></div>}
                {article.source_date && <div style={{ marginBottom: 4 }}>{formatDate(article.source_date)}</div>}
                {article.source_excerpt && <div style={{ fontStyle: 'italic' }}>{article.source_excerpt}</div>}
              </div>
            )}

            {relatedSmart.length > 0 && (
              <div style={{ marginTop: 48 }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 20, color: 'var(--text)' }}>Más sobre {article.category}</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {relatedSmart.map((r: RelatedArticle) => (
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
              <div style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>Autor</div>
              <Link href={authorPageUrl} style={{ textDecoration: 'none' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: '50%',
                    background: 'linear-gradient(135deg, var(--cyan), #9b8cef)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 12, fontWeight: 800, color: 'var(--bg)', flexShrink: 0,
                  }}>JV</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)' }}>Javier Valencia</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>Revisado por NewsTide Editorial</div>
                  </div>
                </div>
              </Link>
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

            <div style={{ background: 'linear-gradient(135deg, rgba(110,207,202,0.08), rgba(155,140,239,0.08))', border: '1px solid rgba(110,207,202,0.2)', borderRadius: 14, padding: 24 }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 8 }}>✉️ Newsletter</div>
              <p style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6, marginBottom: 16 }}>Las mejores historias de la semana en tu inbox.</p>
              <NewsletterForm />
            </div>

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
