import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Terms of Use — NewsTide',
  description: 'Terms and conditions governing the use of NewsTide. Covers permitted use, prohibited conduct, availability, advertising and applicable law.',
  alternates: {
    canonical: 'https://www.newstide.news/en/terms-of-use',
    languages: {
      'en': 'https://www.newstide.news/en/terms-of-use',
      'es': 'https://www.newstide.news/terminos-de-uso',
      'x-default': 'https://www.newstide.news/en/terms-of-use',
    },
  },
  robots: { index: true, follow: true },
}

export default function TermsOfUse() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Home</Link>
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Terms of Use</h1>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 48 }}>Last updated: August 2026</p>

        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>1. Acceptance</h2>
          <p>
            Accessing and using <strong>newstide.news</strong>, operated by <strong>Javier Valencia</strong>, constitutes full and unconditional acceptance of these Terms of Use, the <Link href="/en/legal-notice" style={{ color: 'var(--cyan)' }}>Legal Notice</Link> and the <Link href="/en/privacy" style={{ color: 'var(--cyan)' }}>Privacy Policy</Link>. If you do not agree with any of these terms, you must stop using the site.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>2. Description of the service</h2>
          <p>
            NewsTide provides free access to informational articles, analysis and news covering technology, artificial intelligence, startups and finance. The service is provided as-is, without guarantees of continuous availability or absence of errors.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>3. Permitted use</h2>
          <p>Users may:</p>
          <ul style={{ margin: '12px 0 12px 24px' }}>
            <li style={{ marginBottom: 8 }}>Access and read published content freely and at no cost.</li>
            <li style={{ marginBottom: 8 }}>Share links to articles on social media or other platforms, provided the source is credited.</li>
            <li style={{ marginBottom: 8 }}>Reproduce short excerpts (up to 150 words) for informational or academic purposes, provided authorship is credited and a link to the original article is included.</li>
          </ul>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>4. Prohibited conduct</h2>
          <p>The following are expressly prohibited:</p>
          <ul style={{ margin: '12px 0 12px 24px' }}>
            <li style={{ marginBottom: 8 }}>Reproducing, distributing or commercially exploiting site content without prior written authorisation from Javier Valencia.</li>
            <li style={{ marginBottom: 8 }}>Using site content to train AI models or for automated scraping without express authorisation.</li>
            <li style={{ marginBottom: 8 }}>Any action that may damage, overload or disrupt the proper functioning of the site.</li>
            <li style={{ marginBottom: 8 }}>Using the site for fraudulent, illegal or rights-infringing purposes.</li>
            <li style={{ marginBottom: 8 }}>Impersonating NewsTide, Javier Valencia or any other person or entity.</li>
          </ul>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>5. AI-assisted content</h2>
          <p>
            Some NewsTide content is drafted with AI assistance and is reviewed by the editorial team before publication. Articles are transparently labelled when AI-assisted. NewsTide does not assume liability for errors inherent to AI tools where editorial review has been carried out.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>6. Informational content — not professional advice</h2>
          <p>
            All articles and analysis published on NewsTide are for informational purposes only. Nothing on this site constitutes financial, legal, tax, medical or any other professional advice. Users are solely responsible for decisions made based on information published here.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>7. Service availability</h2>
          <p>
            Javier Valencia endeavours to keep the site continuously available but does not guarantee the absence of technical interruptions or downtime. The owner shall not be liable for any damages resulting from temporary unavailability of the service.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>8. Third-party advertising</h2>
          <p>
            NewsTide may display third-party advertisements, including via Google AdSense. Javier Valencia is not responsible for the content of those ads or the practices of advertisers. The display of ads does not imply endorsement of the products or services advertised.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>9. Modifications and suspension</h2>
          <p>
            Javier Valencia reserves the right to modify, suspend or discontinue the service at any time without prior notice, and to update these Terms of Use. Changes take effect upon publication on the site.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>10. Contact</h2>
          <p>
            For any queries regarding these Terms of Use, contact us at{' '}
            <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a>.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>11. Applicable law</h2>
          <p>
            These Terms of Use are governed by Spanish law. Any disputes shall be submitted to the jurisdiction of Spanish courts.
          </p>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/en/legal-notice" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Legal Notice →</Link>
            <Link href="/en/privacy" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Privacy Policy →</Link>
            <Link href="/en/contact" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contact →</Link>
            <Link href="/terminos-de-uso" style={{ color: 'var(--muted)', fontWeight: 600, fontSize: 14 }}>Leer en español →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
