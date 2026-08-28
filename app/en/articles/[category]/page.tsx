import { supabase } from '@/lib/supabase'
import Image from 'next/image'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'

export const revalidate = 300

const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef',
  'Herramientas': '#e8d5a3', 'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c',
  'AI Tools': '#6ecfca', 'Automation': '#9b8cef', 'Build & Launch': '#e8d5a3',
  'Indie Hacking': '#7ecf9b', 'Growth': '#ef6c6c', 'Monetization': '#f0a050',
  'Freelancing': '#8ecae6', 'Dev Stack': '#c9a0f5',
}

const SLUG_TO_CAT_ES: Record<string, string> = {
  'ai': 'IA', 'startups': 'Startups', 'tools': 'Herramientas',
  'tutorials': 'Tutoriales', 'news': 'Noticias',
  // Real categories from pipeline.py's detect_category() (solopreneur/indie hacker niche)
  'ai-tools': 'AI Tools', 'automation': 'Automation', 'build-launch': 'Build & Launch',
  'indie-hacking': 'Indie Hacking', 'growth': 'Growth', 'monetization': 'Monetization',
  'freelancing': 'Freelancing', 'dev-stack': 'Dev Stack',
}

const CAT_EN_LABEL: Record<string, string> = {
  'IA': 'AI', 'Startups': 'Startups', 'Herramientas': 'Tools',
  'Tutoriales': 'Tutorials', 'Noticias': 'News',
  'AI Tools': 'AI Tools', 'Automation': 'Automation', 'Build & Launch': 'Build & Launch',
  'Indie Hacking': 'Indie Hacking', 'Growth': 'Growth', 'Monetization': 'Monetization',
  'Freelancing': 'Freelancing', 'Dev Stack': 'Dev Stack',
}

const SLUG_TO_EN_LABEL: Record<string, string> = {
  'ai': 'AI', 'startups': 'Startups', 'tools': 'Tools',
  'tutorials': 'Tutorials', 'news': 'News',
  'ai-tools': 'AI Tools', 'automation': 'Automation', 'build-launch': 'Build & Launch',
  'indie-hacking': 'Indie Hacking', 'growth': 'Growth', 'monetization': 'Monetization',
  'freelancing': 'Freelancing', 'dev-stack': 'Dev Stack',
}

const CAT_DESC_EN: Record<string, string> = {
  'IA': 'Articles on artificial intelligence, language models, AI tools and industry trends.',
  'Startups': 'News and analysis on tech startups, investments, founders and the entrepreneurial ecosystem.',
  'Herramientas': 'Reviews and guides of the best tech tools for developers, founders and professionals.',
  'Tutoriales': 'Practical tutorials on technology, programming, AI and digital tools.',
  'Noticias': 'The latest news on technology, AI, startups and the digital world.',
  'AI Tools': 'AI tools, agents and LLM workflows for solopreneurs and indie hackers.',
  'Automation': 'Automation platforms and workflows — n8n, Zapier, Make — for solo teams.',
  'Build & Launch': 'Guides on shipping MVPs and launching SaaS products solo.',
  'Indie Hacking': 'Indie hacking and bootstrapping stories, tactics and lessons.',
  'Growth': 'SEO, content and growth tactics for solo-run products.',
  'Monetization': 'Pricing, revenue and monetization strategies for indie products.',
  'Freelancing': 'Freelancing rates, clients and business advice for solo developers.',
  'Dev Stack': 'Stack, infra and tooling choices for solo developers.',
}

const FALLBACK_GRADIENT = 'linear-gradient(135deg, #1a1f2e 0%, #0f1623 100%)'

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
}

function Badge({ cat }: { cat: string }) {
  const color = CAT_COLORS[cat] || '#6ecfca'
  const label = CAT_EN_LABEL[cat] || cat
  return (
    <span style={{
      display: 'inline-block', padding: '3px 10px', borderRadius: '6px',
      fontSize: '10px', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase',
      background: `${color}18`, color, border: `1px solid ${color}30`
    }}>{label}</span>
  )
}

export async function generateStaticParams() {
  return Object.keys(SLUG_TO_CAT_ES).map(c => ({ category: c }))
}

export async function generateMetadata(
  { params }: { params: Promise<{ category: string }> }
): Promise<Metadata> {
  const { category } = await params
  const cat = SLUG_TO_CAT_ES[category]
  if (!cat) return { title: 'Not found | NewsTide' }
  const label = SLUG_TO_EN_LABEL[category] || category
  const desc = CAT_DESC_EN[cat] || `All NewsTide articles on ${label}.`
  return {
    title: `${label} — NewsTide Articles`,
    description: desc,
    alternates: {
      canonical: `https://www.newstide.news/en/articles/${category}`,
      languages: {
        'en': `https://www.newstide.news/en/articles/${category}`,
        'x-default': `https://www.newstide.news/en/articles/${category}`,
      },
    },
    openGraph: {
      title: `${label} — NewsTide`,
      description: desc,
      url: `https://www.newstide.news/en/articles/${category}`,
      siteName: 'NewsTide',
      locale: 'en_US',
      type: 'website',
    },
  }
}

export default async function CategoryPageEN({
  params,
}: {
  params: Promise<{ category: string }>
}) {
  const { category } = await params
  const cat = SLUG_TO_CAT_ES[category]
  if (!cat) notFound()

  const { data: articles } = await supabase
    .from('articles')
    .select('id,title,title_en,slug,slug_en,excerpt,excerpt_en,category,author,published_at,reading_time,cover_image_url')
    .eq('category', cat)
    .order('published_at', { ascending: false })
    .limit(100)

  const label = SLUG_TO_EN_LABEL[category] || category
  const color = CAT_COLORS[cat] || '#6ecfca'
  const allSlugs = Object.keys(SLUG_TO_CAT_ES)

  return (
    <main style={{ minHeight: '100vh', paddingTop: '90px' }}>
      {/* PAGE HEADER */}
      <section style={{
        borderBottom: '1px solid var(--border)',
        padding: '48px 0 40px',
        background: `linear-gradient(180deg, ${color}08 0%, transparent 100%)`
      }}>
        <div className="container">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>Home</Link>
            <span style={{ color: 'var(--faint)' }}>›</span>
            <Link href="/en/articles" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>Articles</Link>
            <span style={{ color: 'var(--faint)' }}>›</span>
            <span style={{ color: 'var(--fg)', fontSize: 13 }}>{label}</span>
          </div>
          <h1 style={{
            fontSize: 'clamp(28px, 5vw, 42px)', fontWeight: 800,
            letterSpacing: '-0.02em', marginBottom: 12
          }}>
            <span style={{ color }}>{label}</span>
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: 16, maxWidth: 520 }}>
            {CAT_DESC_EN[cat]}
          </p>
          <p style={{ color: 'var(--faint)', fontSize: 13, marginTop: 8 }}>
            {articles?.length || 0} articles
          </p>
          {/* Category nav */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 28 }}>
            <Link
              href="/en/articles"
              style={{
                padding: '6px 14px', borderRadius: '20px', fontSize: 13, fontWeight: 500,
                background: 'var(--surface)', color: 'var(--muted)',
                border: '1px solid var(--border)', textDecoration: 'none',
              }}
            >All</Link>
            {allSlugs.map(s => {
              const catEs = SLUG_TO_CAT_ES[s]
              const lbl = SLUG_TO_EN_LABEL[s]
              const active = s === category
              const col = CAT_COLORS[catEs] || '#6ecfca'
              return (
                <Link
                  key={s}
                  href={`/en/articles/${s}`}
                  style={{
                    padding: '6px 14px', borderRadius: '20px', fontSize: 13, fontWeight: 500,
                    background: active ? col : 'var(--surface)',
                    color: active ? '#0a0f1a' : 'var(--muted)',
                    border: `1px solid ${active ? col : 'var(--border)'}`,
                    textDecoration: 'none',
                  }}
                >{lbl}</Link>
              )
            })}
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
              No articles in this category yet.
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
