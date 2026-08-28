import { supabase } from '@/lib/supabase'
import Image from 'next/image'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { topicClusterKey, clusterLabel, groupByCluster, MIN_CLUSTER_SIZE } from '@/lib/topicClusters'

export const revalidate = 3600

const FALLBACK_GRADIENT = 'linear-gradient(135deg, #1a1f2e 0%, #0f1623 100%)'

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
}

// Cluster keys are computed from the English title (title_en) so ES and EN
// pillar pages group the exact same articles under the exact same key —
// category/keyword text itself stays whatever language the row has.
async function getClusteredArticles() {
  const { data } = await supabase
    .from('articles')
    .select('id,title,title_en,slug,slug_en,excerpt,category,published_at,reading_time,cover_image_url')
    .not('slug', 'is', null)
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
  const url = `https://www.newstide.news/temas/${cluster}`
  const urlEN = `https://www.newstide.news/en/topics/${cluster}`
  return {
    title: `${label} — Temas de NewsTide`,
    description: `Todos los artículos de NewsTide sobre ${label}, en un solo lugar.`,
    alternates: { canonical: url, languages: { 'es': url, 'en': urlEN, 'x-default': urlEN } },
    openGraph: {
      title: `${label} — NewsTide`,
      description: `Todos los artículos de NewsTide sobre ${label}, en un solo lugar.`,
      url,
      siteName: 'NewsTide',
      locale: 'es_ES',
      type: 'website',
    },
  }
}

export default async function TopicPageES({
  params,
}: {
  params: Promise<{ cluster: string }>
}) {
  const { cluster } = await params
  const articles = await getClusteredArticles()
  const matching = articles.filter((a) => topicClusterKey(a.title_en || a.title) === cluster)

  if (matching.length < MIN_CLUSTER_SIZE) notFound()

  const label = clusterLabel(cluster)
  const url = `https://www.newstide.news/temas/${cluster}`

  const collectionSchema = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    '@id': url,
    name: `${label} — NewsTide`,
    url,
    inLanguage: 'es',
    isPartOf: { '@id': 'https://www.newstide.news/#website' },
    publisher: { '@id': 'https://www.newstide.news/#organization' },
    hasPart: matching.map((a) => ({
      '@type': 'Article',
      headline: a.title,
      url: `https://www.newstide.news/articulo/${a.slug}`,
    })),
  }

  return (
    <main style={{ minHeight: '100vh', paddingTop: '90px' }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(collectionSchema) }} />

      <section style={{ borderBottom: '1px solid var(--border)', padding: '48px 0 40px' }}>
        <div className="container">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Link href="/" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>Inicio</Link>
            <span style={{ color: 'var(--faint)' }}>›</span>
            <Link href="/articulos" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>Artículos</Link>
            <span style={{ color: 'var(--faint)' }}>›</span>
            <span style={{ color: 'var(--fg)', fontSize: 13 }}>{label}</span>
          </div>
          <p style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--cyan)', marginBottom: 10 }}>Tema</p>
          <h1 style={{ fontSize: 'clamp(28px, 5vw, 42px)', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 12 }}>{label}</h1>
          <p style={{ color: 'var(--muted)', fontSize: 16, maxWidth: 560 }}>
            Todos los artículos de NewsTide sobre {label}, reunidos en un solo lugar.
          </p>
          <p style={{ color: 'var(--faint)', fontSize: 13, marginTop: 8 }}>{matching.length} artículos</p>
        </div>
      </section>

      <section style={{ padding: '48px 0 80px' }}>
        <div className="container">
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 320px), 1fr))',
            gap: '24px',
          }}>
            {matching.map((a, i) => (
              <Link
                href={`/articulo/${a.slug}`}
                key={a.id}
                className="article-card"
                style={{ '--delay': `${i * 0.04}s` } as React.CSSProperties}
              >
                <div className="article-img">
                  {a.cover_image_url ? (
                    <Image
                      src={a.cover_image_url}
                      alt={a.title}
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
                  <h3 className="article-title">{a.title}</h3>
                  <p className="article-excerpt">{a.excerpt}</p>
                  <div className="article-footer">
                    <span className="article-author">Javier Valencia</span>
                    <span className="article-dot">·</span>
                    <span>{formatDate(a.published_at)}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </main>
  )
}
