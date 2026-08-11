import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Legal Notice — NewsTide',
  description: 'Legal notice for NewsTide. Information about the site owner, intellectual property, liability and applicable law.',
  alternates: {
    canonical: 'https://www.newstide.news/en/legal-notice',
    languages: {
      'en': 'https://www.newstide.news/en/legal-notice',
      'es': 'https://www.newstide.news/aviso-legal',
      'x-default': 'https://www.newstide.news/en/legal-notice',
    },
  },
  robots: { index: true, follow: true },
}

export default function LegalNotice() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Home</Link>
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Legal Notice</h1>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 48 }}>Last updated: August 2026</p>

        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>1. Site owner</h2>
          <p>
            In compliance with Spanish Law 34/2002 on Information Society Services (LSSICE), the owner of the website <strong>newstide.news</strong> is:
          </p>
          <ul style={{ margin: '16px 0 16px 24px' }}>
            <li style={{ marginBottom: 8 }}><strong>Owner:</strong> Javier Valencia</li>
            <li style={{ marginBottom: 8 }}><strong>Activity:</strong> Digital publication — technology and AI journalism</li>
            <li style={{ marginBottom: 8 }}><strong>Email:</strong> <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a></li>
            <li style={{ marginBottom: 8 }}><strong>Website:</strong> <a href="https://www.newstide.news" style={{ color: 'var(--cyan)' }}>https://www.newstide.news</a></li>
          </ul>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>2. Purpose of the website</h2>
          <p>
            NewsTide is a digital publication specialising in news, analysis and trends in artificial intelligence, startups, developer tools and finance. Access to and use of this website is subject to this Legal Notice and the <Link href="/en/terms-of-use" style={{ color: 'var(--cyan)' }}>Terms of Use</Link>.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>3. Intellectual and industrial property</h2>
          <p>
            All website content — including but not limited to articles, analysis, images, logos, graphic design, source code and site structure — is the property of Javier Valencia or third parties who have authorised its use, and is protected by Spanish and international intellectual property law.
          </p>
          <p style={{ marginTop: 12 }}>
            Reproduction, distribution, transformation or public communication of any content without prior written authorisation from the owner is strictly prohibited. Partial reproduction for informational purposes is permitted provided the source is cited and a link to the original article is included.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>4. AI-assisted content</h2>
          <p>
            Some content published on NewsTide is drafted with the assistance of AI language models. All content is reviewed by the editorial team before publication. NewsTide is committed to the accuracy and timeliness of its content and will correct any reported error within 48 hours.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>5. Disclaimer of liability</h2>
          <p>
            Javier Valencia does not guarantee that the content of this website is free from errors or permanently up to date. The owner shall not be liable for damages arising from the use of published information, service interruptions or access to external linked sites.
          </p>
          <p style={{ marginTop: 12 }}>
            Articles published on NewsTide are for informational purposes only and do not constitute financial, legal, medical or any other professional advice.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>6. Third-party links</h2>
          <p>
            This website may contain links to third-party websites for informational purposes only. Javier Valencia is not responsible for the content, privacy policies or practices of linked sites, and inclusion of a link does not imply endorsement.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>7. Advertising</h2>
          <p>
            This website may display advertisements through third-party advertising services, including <strong>Google AdSense</strong>. These ads may use cookies to personalise the ads shown. Please refer to our <Link href="/en/privacy" style={{ color: 'var(--cyan)' }}>Privacy Policy</Link> for more information.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>8. Applicable law and jurisdiction</h2>
          <p>
            This Legal Notice is governed by Spanish law. Any disputes arising from access to or use of this website shall be submitted to the jurisdiction of Spanish courts, with each party waiving any other jurisdiction that may apply.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>9. Modifications</h2>
          <p>
            Javier Valencia reserves the right to modify this Legal Notice at any time. Changes take effect upon publication on the site. Users are advised to review this page periodically.
          </p>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/en/terms-of-use" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Terms of Use →</Link>
            <Link href="/en/privacy" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Privacy Policy →</Link>
            <Link href="/en/contact" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contact →</Link>
            <Link href="/aviso-legal" style={{ color: 'var(--muted)', fontWeight: 600, fontSize: 14 }}>Leer en español →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
