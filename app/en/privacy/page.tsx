import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Privacy Policy — NewsTide',
  description: "NewsTide's privacy policy. Information about how we collect, use and protect your personal data.",
  alternates: {
    canonical: 'https://www.newstide.news/en/privacy',
    languages: {
      'en': 'https://www.newstide.news/en/privacy',
      'es': 'https://www.newstide.news/privacidad',
      'x-default': 'https://www.newstide.news/en/privacy',
    },
  },
  robots: { index: true, follow: true },
}

export default function PrivacyEN() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Home</Link>
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Privacy Policy</h1>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 48 }}>Last updated: June 2026</p>
        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>1. Data controller</h2>
          <p>NewsTide is the data controller for personal data collected through this website (newstide.news).</p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>2. Data we collect</h2>
          <p>We collect anonymous browsing data through Google Analytics (anonymized IP address, pages visited, session time). If you subscribe to our newsletter, we store your email address with your explicit consent.</p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>3. Purpose of processing</h2>
          <p>Analytics data is used exclusively to improve content and site experience. Newsletter email is used only to send the newsletter you subscribed to.</p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>4. Cookies</h2>
          <p>This site uses technical cookies necessary for its operation and analytical cookies from Google Analytics. You can disable analytical cookies from your browser settings.</p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>5. Your rights</h2>
          <p>You have the right to access, rectify, erase, restrict and port your data. To exercise any right, contact us at <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a>.</p>

          <div style={{ marginTop: 48 }}>
            <Link href="/en" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>← Back to home</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
