import { supabase } from '@/lib/supabase'
import Image from 'next/image'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { topicClusterKey, clusterLabel, groupByCluster, MIN_CLUSTER_SIZE } from '@/lib/topicClusters'

export const revalidate = 3600

const FALLBACK_GRADIENT = 'linear-gradient(135deg, #1a1f2e 0%, #0f1623 100%)'

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function getClusteredArticles() {
  const { data } = await supabase
    .from('articles')
    .select('id,title,title_en,slug,slug_en,excerpt,excerpt_en,category,published_at,reading_time,cover_image_url')
    .not('slug_en', 'is', null)
    .order('published_at', { ascending: false })
    .limit(500)
  return data || []
}

export async function generateStaticParams() {
  const articles = await getClusteredArticles()
  const groups = groupByCluster(articles, (a) => a.title_en || a.title)
  return Array.from(groups.entries())
    .filter(([, items]) => items.length >= MIN_CLUSTER_SIZE)
    .map(([cluster]) => ({ cluster }))
}

export async function generateMetadata(
  { params }: { params: Promise<{ cluster: string }> }
): Promise<Metadata> {
  const { cluster } = await params
  const label = clusterLabel(cluster)
  const url = `https://www.newstide.news/en/topics/${cluster}`
  return {
    title: `${label} — NewsTide Topics`,
    description: `Every NewsTide article about ${label}, in one place.`,
    alternates: { canonical: url, languages: { 'en': url, 'x-default': url } },
    openGraph: {
      title: `${label} — NewsTide`,
      description: `Every NewsTide article about ${label}, in one place.`,
      url,
      siteName: 'NewsTide',
      locale: 'en_US',
      type: 'website',
    },
  }
}

export default async function TopicPageEN({
  params,
}: {
  params: Promise<{ cluster: string }>
}) {
  const { cluster } = await params
  const articles = await getClusteredArticles()
  const matching = articles.filter((a) => topicClusterKey(a.title_en || a.title) === cluster)

  if (matching.length < MIN_CLUSTER_SIZE) notFound()

  const label = clusterLabel(cluster)
  const url = `https://www.newstide.news/en/topics/${cluster}`

  const collectionSchema = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    '@id': url,
    name: `${label} — NewsTide`,
    url,
    inLanguage: 'en',
    isPartOf: { '@id': 'https://www.newstide.news/en#website' },
    publisher: { '@id': 'https://www.newstide.news/#organization' },
    hasPart: matching.map((a) => ({
      '@type': 'Article',
      headline: a.title_en || a.title,
      url: `https://www.newstide.news/en/article/${a.slug_en}`,
    })),
  }

  return (
    <main style={{ minHeight: '100vh', paddingTop: '90px' }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(collectionSchema) }} />

      <section style={{ borderBottom: '1px solid var(--border)', padding: '48px 0 40px' }}>
        <div className="container">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>Home</Link>
            <span style={{ color: 'var(--faint)' }}>›</span>
            <Link href="/en/articles" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>Articles</Link>
            <span style={{ color: 'var(--faint)' }}>›</span>
            <span style={{ color: 'var(--fg)', fontSize: 13 }}>{label}</span>
          </div>
          <p style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--cyan)', marginBottom: 10 }}>Topic</p>
          <h1 style={{ fontSize: 'clamp(28px, 5vw, 42px)', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 12 }}>{label}</h1>
          <p style={{ color: 'var(--muted)', fontSize: 16, maxWidth: 560 }}>
            Every NewsTide article about {label}, gathered in one place.
          </p>
          <p style={{ color: 'var(--faint)', fontSize: 13, marginTop: 8 }}>{matching.length} articles</p>
        </div>
      </section>

      <section style={{ padding: '48px 0 80px' }}>
        <div className="container">
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 320px), 1fr))',
            gap: '24px',
          }}>
            {matching.map((a, i) => {
              const title = a.title_en || a.title
              const excerpt = a.excerpt_en || a.excerpt
              return (
                <Link
                  href={`/en/article/${a.slug_en}`}
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
        </div>
      </section>
    </main>
  )
}
