import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Contact — NewsTide',
  description: 'Get in touch with the NewsTide team for editorial inquiries, corrections, collaborations or advertising.',
  alternates: {
    canonical: 'https://www.newstide.news/en/contact',
    languages: {
      'en': 'https://www.newstide.news/en/contact',
      'es': 'https://www.newstide.news/contacto',
      'x-default': 'https://www.newstide.news/en/contact',
    },
  },
}

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'ContactPage',
  name: 'Contact — NewsTide',
  url: 'https://www.newstide.news/en/contact',
  publisher: {
    '@type': 'NewsMediaOrganization',
    name: 'NewsTide',
    url: 'https://www.newstide.news',
    email: 'hello@newstide.news',
  },
}

export default function ContactEN() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <div className="container" style={{ maxWidth: 640, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Home</Link>
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Contact</h1>
        <p style={{ fontSize: 18, color: 'var(--muted)', lineHeight: 1.7, marginBottom: 48 }}>Have a question, correction or proposal? Write to us.</p>
        <div style={{ fontSize: 16, lineHeight: 2, color: 'rgba(240,240,238,0.85)' }}>
          <p><strong>General:</strong> <a href="mailto:hello@newstide.news" style={{ color: 'var(--cyan)' }}>hello@newstide.news</a></p>
          <p><strong>Editorial (errors, corrections):</strong> <a href="mailto:editorial@newstide.news" style={{ color: 'var(--cyan)' }}>editorial@newstide.news</a></p>
          <p><strong>Privacy:</strong> <a href="mailto:privacy@newstide.news" style={{ color: 'var(--cyan)' }}>privacy@newstide.news</a></p>
          <p><strong>Advertising &amp; partnerships:</strong> <a href="mailto:ads@newstide.news" style={{ color: 'var(--cyan)' }}>ads@newstide.news</a></p>
        </div>
        <div style={{ marginTop: 48 }}>
          <Link href="/en/about" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>About us →</Link>
        </div>
      </div>
    </div>
  )
}
