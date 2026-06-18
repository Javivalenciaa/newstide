import type { Metadata } from 'next'
import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import Link from 'next/link'

const CAT_EN: Record<string, string> = {
  'IA': 'AI', 'Tutoriales': 'Tutorials',
  'Herramientas': 'Tools', 'Startups': 'Startups', 'Noticias': 'News',
}

const AUTHOR_MAP: Record<string, { name: string; bio: string; title: string }> = {
  'maria-lopez': {
    name: 'María López',
    title: 'AI & Technology Editor',
    bio: 'María López covers artificial intelligence, language models and developer tools. With over 8 years of experience in tech journalism, she has followed the evolution of AI from early transformers to today\'s multimodal models.',
  },
  'carlos-ruiz': {
    name: 'Carlos Ruiz',
    title: 'Finance & Markets Editor',
    bio: 'Carlos Ruiz specializes in financial markets, cryptocurrencies and the digital economy. Before joining NewsTide, he worked as a financial analyst and as an economics correspondent for specialized digital media.',
  },
  'ana-martinez': {
    name: 'Ana Martínez',
    title: 'Startups & Business Editor',
    bio: 'Ana Martínez covers the entrepreneurial ecosystem, funding rounds and the impact of technology on business models. She has interviewed over 200 founders and written about some of the most relevant startups in Europe and Latin America.',
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
  if (!author) return { title: 'Author not found' }
  const url = `https://www.newstide.news/en/authors/${slug}`
  return {
    title: `${author.name} — ${author.title} | NewsTide`,
    description: author.bio,
    alternates: { canonical: url },
    openGraph: {
      title: `${author.name} — NewsTide`,
      description: author.bio,
      url,
      siteName: 'NewsTide',
      locale: 'en_US',
      type: 'profile',
    },
  }
}

export default async function AuthorPageEN({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const author = AUTHOR_MAP[slug]
  if (!author) notFound()

  const url = `https://www.newstide.news/en/authors/${slug}`

  const { data: articles } = await supabase
    .from('articles')
    .select('title_en, title, slug_en, slug, published_at, category, excerpt_en, excerpt')
    .eq('author', author.name)
    .not('slug_en', 'is', null)
    .order('published_at', { ascending: false })
    .limit(20)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'ProfilePage',
    mainEntity: {
      '@type': 'Person',
      name: author.name,
      jobTitle: author.title,
      description: author.bio,
      url,
      worksFor: {
        '@type': 'NewsMediaOrganization',
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
          <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Home</Link>
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

        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: 24 }}>Recent articles</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {(articles || []).map((a) => (
            <Link
              key={a.slug_en || a.slug}
              href={`/en/article/${a.slug_en || a.slug}`}
              style={{
                display: 'block', padding: '20px 24px',
                background: 'var(--surface)', border: '1px solid var(--border)',
                borderRadius: 12, textDecoration: 'none',
                transition: 'border-color 0.2s'
              }}
            >
              <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6 }}>
                {CAT_EN[a.category] || a.category} · {new Date(a.published_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })}
              </div>
              <div style={{ fontWeight: 600, fontSize: 16, color: 'var(--text)', marginBottom: 6 }}>{a.title_en || a.title}</div>
              {(a.excerpt_en || a.excerpt) && <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.5 }}>{a.excerpt_en || a.excerpt}</div>}
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
