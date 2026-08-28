import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Editorial Policy — NewsTide',
  description:
    "NewsTide's editorial standards: how we use AI, how we verify facts, our corrections process, source-linking policy and independence commitments.",
  alternates: {
    canonical: 'https://www.newstide.news/en/editorial-policy',
    languages: {
      'en': 'https://www.newstide.news/en/editorial-policy',
      'es': 'https://www.newstide.news/politica-editorial',
      'x-default': 'https://www.newstide.news/en/editorial-policy',
    },
  },
}

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'WebPage',
  '@id': 'https://www.newstide.news/en/editorial-policy#webpage',
  name: 'Editorial Policy — NewsTide',
  url: 'https://www.newstide.news/en/editorial-policy',
  description:
    "NewsTide's full editorial policy covering AI usage, source verification, corrections, independence and diversity standards.",
  isPartOf: { '@id': 'https://www.newstide.news/en#website' },
  about: { '@id': 'https://www.newstide.news/#organization' },
  speakable: {
    '@type': 'SpeakableSpecification',
    cssSelector: ['h1', '.editorial-lead'],
  },
  dateModified: '2026-06-01',
}

export default function EditorialPolicyEN() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Home</Link>
        </div>

        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Editorial Policy</h1>
        <p className="editorial-lead" style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 48 }}>Last updated: June 2026</p>

        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>

          {/* ── 1. AI usage ── */}
          <h2 id="ai-usage" style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>1. Use of artificial intelligence</h2>
          <p>
            NewsTide uses AI language models to assist in drafting, structuring and translating articles.
            Every published article is reviewed by a human editor who verifies factual accuracy,
            analytical coherence and editorial tone before publication. AI-assisted articles are
            labelled as such in the article metadata. We comply with the{' '}
            <a
              href="https://publishercenter.google.com/intl/en_us/about/publisher-policies"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: 'var(--cyan)' }}
            >
              Google News Publisher Policies
            </a>{' '}
            on AI-generated content disclosure.
          </p>

          {/* ── 2. Sources ── */}
          <h2 id="verification" style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>2. Sources and verification</h2>
          <p>
            All articles are based on verifiable primary sources: official press releases, corporate
            filings, technical documentation, market data from recognised providers, and public
            statements from authoritative figures in the relevant field. We link to original sources
            whenever technically possible, and inline citations are included in article bodies.
            Our verification standards are aligned with the{' '}
            <a
              href="https://www.spj.org/ethicscode.asp"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: 'var(--cyan)' }}
            >
              SPJ Code of Ethics
            </a>{' '}
            and the{' '}
            <a
              href="https://www.ipso.co.uk/editors-code-of-practice/"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: 'var(--cyan)' }}
            >
              IPSO Editors&apos; Code of Practice
            </a>.
          </p>

          {/* ── 3. Corrections ── */}
          <h2 id="corrections" style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>3. Corrections and updates</h2>
          <p>
            If an article contains a factual error, NewsTide commits to correcting it within
            48 hours of notification. Corrections are made transparently: the nature of the
            change and the correction date are noted at the bottom of the affected article.
            To report an error, contact us at{' '}
            <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a>.
          </p>

          {/* ── 4. Independence ── */}
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>4. Editorial independence</h2>
          <p>
            NewsTide editorial content is completely independent of any commercial, advertising
            or affiliate relationships. Reviews, analyses and comparisons are conducted without
            intervention from the companies covered. When an article contains affiliate links,
            this is explicitly disclosed at the top of the article.
          </p>

          {/* ── 5. Conflicts ── */}
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>5. Conflicts of interest</h2>
          <p>
            No member of the NewsTide editorial team may publish articles about companies in which
            they hold direct financial interests without an explicit declaration of that conflict
            at the beginning of the article.
          </p>

          {/* ── 6. Diversity ── */}
          <h2 id="diversity" style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>6. Diversity and representation</h2>
          <p>
            NewsTide is committed to covering the technology and financial ecosystem from a global
            perspective, including diverse voices, companies and regions in its analysis. We
            actively seek coverage of founders and professionals underrepresented in mainstream
            tech media.
          </p>

          {/* ── External standards ── */}
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>7. External standards we follow</h2>
          <p>Our editorial practice is informed by the following publicly available frameworks:</p>
          <ul style={{ margin: '12px 0 20px 24px' }}>
            <li style={{ marginBottom: 10 }}>
              <a href="https://www.spj.org/ethicscode.asp" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>
                SPJ Code of Ethics
              </a>{' '}— Society of Professional Journalists
            </li>
            <li style={{ marginBottom: 10 }}>
              <a href="https://publishercenter.google.com/intl/en_us/about/publisher-policies" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>
                Google News Publisher Policies
              </a>
            </li>
            <li style={{ marginBottom: 10 }}>
              <a href="https://www.ipso.co.uk/editors-code-of-practice/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>
                IPSO Editors&apos; Code of Practice
              </a>
            </li>
            <li style={{ marginBottom: 10 }}>
              <a href="https://www.reuters.com/news/editorial-standards" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>
                Reuters Editorial Standards
              </a>
            </li>
          </ul>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/en/about" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>About us →</Link>
            <Link href="/en/contact" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contact →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
