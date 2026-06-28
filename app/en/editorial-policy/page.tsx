import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Editorial Policy — NewsTide',
  description: "Learn about NewsTide's editorial standards: how we use AI, how we review content, our correction process and our transparency commitments.",
  alternates: {
    canonical: 'https://www.newstide.news/en/editorial-policy',
    languages: {
      'en': 'https://www.newstide.news/en/editorial-policy',
      'es': 'https://www.newstide.news/politica-editorial',
      'x-default': 'https://www.newstide.news/en/editorial-policy',
    },
  },
}

export default function EditorialPolicyEN() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Home</Link>
        </div>

        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Editorial Policy</h1>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 48 }}>Last updated: June 2026</p>

        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>1. Use of artificial intelligence</h2>
          <p>
            NewsTide uses AI models to assist in the writing, structuring and translation of articles.
            Every published article is reviewed by a human editor who verifies data accuracy, analytical
            coherence and editorial tone before publication.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>2. Sources and verification</h2>
          <p>
            All articles are based on verifiable primary sources: official press releases, corporate reports,
            technical documentation, market data from recognized sources and public statements from authoritative
            figures in the relevant field. We link to original sources whenever technically possible.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>3. Corrections and updates</h2>
          <p>
            If an article contains a factual error, NewsTide commits to correcting it within 48 hours of being
            notified. Corrections are made transparently, indicating the nature of the change and the correction
            date within the article. To report an error, contact us at{' '}
            <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a>.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>4. Editorial independence</h2>
          <p>
            NewsTide editorial content is completely independent of any commercial, advertising or affiliate
            relationships. Reviews, analyses and comparisons are conducted without intervention from the companies
            being covered. When an article contains affiliate links, this is explicitly stated.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>5. Conflicts of interest</h2>
          <p>
            No member of the NewsTide editorial team may publish articles about companies in which they hold
            direct financial interests without an explicit declaration of that conflict at the beginning of the article.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>6. Diversity and representation</h2>
          <p>
            NewsTide is committed to covering the technology and financial ecosystem from a global perspective,
            including diverse voices, companies and perspectives in its analysis.
          </p>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/en/about" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>About us →</Link>
            <Link href="/en/contact" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contact →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
