import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'About NewsTide — Technology and AI for Those Who Stay Ahead',
  description: 'Learn about NewsTide: who we are, how we create our content, and why we cover technology, artificial intelligence and finance with AI assistance and human editorial review.',
  alternates: {
    canonical: 'https://www.newstide.news/en/about',
    languages: {
      'en': 'https://www.newstide.news/en/about',
      'es': 'https://www.newstide.news/sobre-nosotros',
      'x-default': 'https://www.newstide.news/en/about',
    },
  },
  openGraph: {
    title: 'About NewsTide',
    description: 'Who we are and how we create technology and AI content.',
    url: 'https://www.newstide.news/en/about',
    siteName: 'NewsTide',
    locale: 'en_US',
    type: 'website',
  },
}

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'AboutPage',
  name: 'About NewsTide',
  url: 'https://www.newstide.news/en/about',
  description: 'NewsTide is a digital publication specializing in technology, artificial intelligence and finance.',
  publisher: {
    '@type': 'NewsMediaOrganization',
    name: 'NewsTide',
    url: 'https://www.newstide.news',
    logo: {
      '@type': 'ImageObject',
      url: 'https://www.newstide.news/favicon-192x192.png',
    },
    sameAs: [
      'https://twitter.com/newstide',
      'https://www.linkedin.com/company/newstide',
    ],
  },
}

export default function AboutEN() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Home</Link>
        </div>

        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>About NewsTide</h1>
        <p style={{ fontSize: 18, color: 'var(--muted)', lineHeight: 1.7, marginBottom: 48 }}>
          Technology, AI and finance for those who stay ahead.
        </p>

        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>What is NewsTide?</h2>
          <p>
            NewsTide is a digital publication specializing in covering the latest news, analysis and trends in
            artificial intelligence, tech tools, startups and finance. Our goal is to deliver accurate, timely
            and relevant information for founders, developers, investors and digital professionals.
          </p>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>How we create our content</h2>
          <p>
            NewsTide combines state-of-the-art artificial intelligence with human editorial oversight.
            All articles are generated with AI assistance from verified primary sources and subsequently
            reviewed by our editorial team to ensure accuracy, context and informational value. This methodology
            allows us to publish quality content at a frequency no traditional newsroom could maintain.
          </p>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>Our editorial pillars</h2>
          <ul style={{ margin: '0 0 20px 24px' }}>
            <li style={{ marginBottom: 10 }}><strong>Artificial Intelligence &amp; Models:</strong> tracking the latest AI models, tools and trends.</li>
            <li style={{ marginBottom: 10 }}><strong>Developer Tools:</strong> analysis and comparisons of the best development, productivity and automation tools.</li>
            <li style={{ marginBottom: 10 }}><strong>Finance &amp; Markets:</strong> financial markets news, crypto, investment strategies and digital economy.</li>
            <li style={{ marginBottom: 10 }}><strong>Startups &amp; Business:</strong> entrepreneurial ecosystem, funding rounds and success stories.</li>
          </ul>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>Editorial transparency</h2>
          <p>
            We believe strongly in transparency. We always indicate when an article has been generated with AI assistance
            and link to the primary sources used. If you spot an error or have questions about an article, contact us
            and we commit to reviewing and correcting any inaccuracies.
          </p>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/en/editorial-policy" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Editorial policy →</Link>
            <Link href="/en/contact" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contact →</Link>
            <Link href="/sobre-nosotros" style={{ color: 'var(--muted)', fontWeight: 600, fontSize: 14 }}>Leer en español →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
