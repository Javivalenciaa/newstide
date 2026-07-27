import type { Metadata } from 'next'
import Script from 'next/script'
import Link from 'next/link'
import LangSwitcher from '@/components/LangSwitcher'
import MobileNav from '@/components/MobileNav'
import SubNav from '@/components/SubNav'

const GA_ID = 'G-C0Z8YQC18J'

export const metadata: Metadata = {
  title: {
    // FIX C3: template must NOT include '| NewsTide' because root layout already
    // defines title.template = '%s | NewsTide'. Using just '%s' here prevents the
    // double-suffix '… | NewsTide | NewsTide' that appeared on all ~328 EN pages.
    default: 'NewsTide — The intelligence shaping the future',
    template: '%s',
  },
  description: 'Technology, AI and trends for founders, developers and professionals. Daily news on artificial intelligence, startups and tech tools.',
  metadataBase: new URL('https://www.newstide.news'),
  alternates: {
    canonical: 'https://www.newstide.news/en',
    languages: {
      'es': 'https://www.newstide.news',
      'en': 'https://www.newstide.news/en',
      'x-default': 'https://www.newstide.news/en',
    },
  },
  openGraph: {
    siteName: 'NewsTide',
    locale: 'en_US',
    type: 'website',
    url: 'https://www.newstide.news/en',
    title: 'NewsTide — The intelligence shaping the future',
    description: 'Technology, AI and trends for founders, developers and professionals.',
    images: [{ url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630, alt: 'NewsTide' }],
  },
  twitter: {
    card: 'summary_large_image',
    site: '@newstide',
    creator: '@newstide',
    title: 'NewsTide — The intelligence shaping the future',
    description: 'Technology, AI and trends for founders, developers and professionals.',
    images: ['https://www.newstide.news/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
}

// FIX C5: Only ONE NewsMediaOrganization @graph per page.
// The root layout (app/layout.tsx) already emits the canonical ES-locale
// WebSite + NewsMediaOrganization graph with @id 'https://www.newstide.news/#organization'.
// This EN layout previously re-emitted a SECOND graph with the SAME @id but
// contradictory foundingDate ('2026' vs '2024') and missing sameAs/masthead —
// causing Google to see two conflicting entities.
//
// Solution: emit ONLY the EN WebSite node here (different @id: /en#website).
// The shared NewsMediaOrganization is referenced by @id from root layout and
// does NOT need to be re-declared. foundingDate is unified to '2025' in root layout.
const websiteSchemaEN = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'WebSite',
      '@id': 'https://www.newstide.news/en#website',
      url: 'https://www.newstide.news/en',
      name: 'NewsTide',
      description: 'Technology, AI and trends for founders, developers and professionals.',
      inLanguage: 'en',
      publisher: { '@id': 'https://www.newstide.news/#organization' },
      potentialAction: {
        '@type': 'SearchAction',
        target: {
          '@type': 'EntryPoint',
          urlTemplate: 'https://www.newstide.news/en/articles?q={search_term_string}',
        },
        'query-input': 'required name=search_term_string',
      },
    },
  ],
}

export default function EnLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {/*
        FIX C4: <html lang="es"> was being served on all /en/* pages because the
        root layout derives lang from the next-url header, which was not always
        available during the initial HTML flush.

        The root layout already does:
          const isEnglish = nextUrl.startsWith('/en')
          const lang = isEnglish ? 'en' : 'es'
        and passes it to <html lang={lang}>.

        The previous inline script that forcibly set lang='en' via JS was a
        client-side patch that crawlers/AT still saw as 'es' in raw HTML.
        We now rely solely on the server-side root layout logic (no JS patch needed).
        The root layout header-based detection handles this correctly.
      */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteSchemaEN) }}
      />
      <link rel="alternate" type="application/rss+xml" title="NewsTide EN RSS" href="https://www.newstide.news/en/rss.xml" />
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
        strategy="afterInteractive"
      />
      <Script id="google-analytics-en" strategy="afterInteractive">
        {`window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${GA_ID}',{page_path:window.location.pathname});`}
      </Script>

      {/* MAIN NAVBAR */}
      <nav id="navbar">
        <Link href="/en" className="nav-logo">
          <div className="nav-logo-mark">NT</div>
          NewsTide
        </Link>
        <div className="nav-links">
          <Link href="/en">Home</Link>
          <Link href="/en/articles">Articles</Link>
          <Link href="/en/compare">Guides</Link>
          <Link href="/en#newsletter">Newsletter</Link>
        </div>
        <div className="nav-right" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <LangSwitcher />
          <Link href="/en#newsletter" className="nav-cta">Subscribe</Link>
          <MobileNav lang="en" />
        </div>
      </nav>

      {/* SECONDARY TABS BAR */}
      <SubNav />

      {children}

      <footer>
        <div className="container">
          <div className="footer-top">
            <div className="footer-brand">
              <Link href="/en" className="nav-logo" style={{ marginBottom: '12px' }}>
                <div className="nav-logo-mark">NT</div>NewsTide
              </Link>
              <p className="footer-tagline">Technology, AI and trends<br />for those who stay ahead.</p>
            </div>
            <div className="footer-links">
              <div className="footer-col">
                <div className="footer-col-title">Categories</div>
                <Link href="/en/articles/ai">AI &amp; Models</Link>
                <Link href="/en/articles/startups">Startups</Link>
                <Link href="/en/articles/tools">Tools</Link>
                <Link href="/en/articles/tutorials">Tutorials</Link>
                <Link href="/en/articles/news">News</Link>
              </div>
              <div className="footer-col">
                <div className="footer-col-title">Guides</div>
                <Link href="/en/compare">All Guides</Link>
                <Link href="/en/compare?filter=comparisons">⚔️ Comparisons</Link>
                <Link href="/en/compare?filter=alternatives">🔄 Alternatives</Link>
                <Link href="/en/compare?filter=guides">📖 Guides</Link>
                <Link href="/en/compare?filter=for-profession">👤 For Pros</Link>
              </div>
              <div className="footer-col">
                <div className="footer-col-title">Company</div>
                <Link href="/en/about">About us</Link>
                <Link href="/en/editorial-policy">Editorial Policy</Link>
                <Link href="/en/contact">Contact</Link>
                <Link href="/en/privacy">Privacy</Link>
              </div>
              <div className="footer-col">
                <div className="footer-col-title">Feeds</div>
                <Link href="/en/rss.xml">RSS Feed</Link>
                <Link href="/rss.xml">RSS Español</Link>
                <Link href="/news-sitemap.xml">News Sitemap</Link>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <span>© 2026 NewsTide · All rights reserved</span>
            <span style={{ color: 'var(--faint)' }}>newstide.news</span>
          </div>
        </div>
      </footer>
      <script dangerouslySetInnerHTML={{ __html: `const nav=document.getElementById('navbar');if(nav)window.addEventListener('scroll',()=>nav.classList.toggle('scrolled',window.scrollY>20),{passive:true});` }} />
    </>
  )
}
