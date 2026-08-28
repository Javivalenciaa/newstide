import { supabase } from '@/lib/supabase'
import Image from 'next/image'
import Link from 'next/link'
import type { Metadata } from 'next'

// A3: listado EN → revalida cada hora
export const revalidate = 3600

export const metadata: Metadata = {
  title: 'All Articles — NewsTide',
  description: 'All NewsTide articles on AI, startups, tools and technology.',
  alternates: {
    canonical: 'https://www.newstide.news/en/articles',
    languages: {
      'es': 'https://www.newstide.news/articulos',
      'en': 'https://www.newstide.news/en/articles',
      // A5: x-default → homepage ES (mercado principal del sitio)
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

const CAT_EN: Record<string, string> = {
  'IA': 'AI', 'Tutoriales': 'Tutorials',
  'Herramientas': 'Tools', 'Startups': 'Startups', 'Noticias': 'News',
  'AI Tools': 'AI Tools', 'Automation': 'Automation', 'Build & Launch': 'Build & Launch',
  'Indie Hacking': 'Indie Hacking', 'Growth': 'Growth', 'Monetization': 'Monetization',
  'Freelancing': 'Freelancing', 'Dev Stack': 'Dev Stack',
}

const CAT_SLUG_EN: Record<string, string> = {
  'IA': 'ai', 'Tutoriales': 'tutorials',
  'Herramientas': 'tools', 'Startups': 'startups', 'Noticias': 'news',
  'AI Tools': 'ai-tools', 'Automation': 'automation', 'Build & Launch': 'build-launch',
  'Indie Hacking': 'indie-hacking', 'Growth': 'growth', 'Monetization': 'monetization',
  'Freelancing': 'freelancing', 'Dev Stack': 'dev-stack',
}

const FALLBACK_GRADIENT = 'linear-gradient(135deg, #1a1f2e 0%, #0f1623 100%)'

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
}

function Badge({ cat }: { cat: string }) {
  const color = CAT_COLORS[cat] || '#6ecfca'
  const label = CAT_EN[cat] || cat
  return (
    <span style={{
      display: 'inline-block', padding: '3px 10px', borderRadius: '6px',
      fontSize: '10px', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase',
      background: `${color}18`, color, border: `1px solid ${color}30`
    }}>{label}</span>
  )
}

export default async function ArticlesPageEN() {
  const { data: articles } = await supabase
    .from('articles')
    .select('id,title,title_en,slug,slug_en,excerpt,excerpt_en,category,author,published_at,reading_time,featured,cover_image_url')
    .order('published_at', { ascending: false })
    .limit(100)

  const rawCats = Array.from(new Set(articles?.map(a => a.category) || []))

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
            <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>Home</Link>
            <span style={{ color: 'var(--faint)' }}>›</span>
            <span style={{ color: 'var(--fg)', fontSize: 13 }}>Articles</span>
          </div>
          <h1 style={{
            fontSize: 'clamp(28px, 5vw, 42px)', fontWeight: 800,
            letterSpacing: '-0.02em', marginBottom: 12
          }}>
            All <span className="grad">articles</span>
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: 16, maxWidth: 480 }}>
            {articles?.length || 0} articles on AI, startups, tools and technology.
          </p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 28 }}>
            <Link
              href="/en/articles"
              style={{
                padding: '6px 14px', borderRadius: '20px', fontSize: 13, fontWeight: 500,
                background: 'var(--accent)', color: 'var(--bg)',
                border: '1px solid var(--border)', textDecoration: 'none',
              }}
            >All</Link>
            {rawCats.map(c => (
              <Link
                key={c}
                href={`/en/articles/${CAT_SLUG_EN[c] || c.toLowerCase()}`}
                style={{
                  padding: '6px 14px', borderRadius: '20px', fontSize: 13, fontWeight: 500,
                  background: 'var(--surface)', color: 'var(--muted)',
                  border: '1px solid var(--border)', textDecoration: 'none',
                }}
              >{CAT_EN[c] || c}</Link>
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
            {articles?.map((a, i) => {
              const title = a.title_en || a.title
              const excerpt = a.excerpt_en || a.excerpt
              const href = a.slug_en ? `/en/article/${a.slug_en}` : `/articulo/${a.slug}`
              return (
                <Link
                  href={href}
                  key={a.id}
                  className="article-card"
                  style={{ '--delay': `${i * 0.04}s` } as React.CSSProperties}
                >
                  <div className="article-img">
                    {a.cover_image_url ? (
                      <Image
                        src={a.cover_image_url}
                        alt={title}
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
                    <h3 className="article-title">{title}</h3>
                    <p className="article-excerpt">{excerpt}</p>
                    <div className="article-footer">
                      <span className="article-author">NewsTide Editorial</span>
                      <span className="article-dot">·</span>
                      <span>{formatDate(a.published_at)}</span>
                    </div>
                  </div>
                </Link>
              )
            })}
          </div>
          {(!articles || articles.length === 0) && (
            <div style={{ textAlign: 'center', padding: '80px 20px', color: 'var(--muted)' }}>
              No articles yet.
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
