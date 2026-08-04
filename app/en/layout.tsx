import type { Metadata } from 'next'
import Link from 'next/link'
import LangSwitcher from '@/components/LangSwitcher'
import MobileNav from '@/components/MobileNav'
import SubNav from '@/components/SubNav'

export const metadata: Metadata = {
  title: {
    default: 'NewsTide — AI, Startups & Tech News',
    template: '%s | NewsTide',
  },
  description: 'Daily AI, startup and tech news for founders, developers and professionals. Stay ahead with NewsTide.',
  metadataBase: new URL('https://www.newstide.news'),
  alternates: {
    canonical: 'https://www.newstide.news/en',
    languages: {
      'en': 'https://www.newstide.news/en',
      'en-US': 'https://www.newstide.news/en',
      'en-GB': 'https://www.newstide.news/en',
      'en-AU': 'https://www.newstide.news/en',
      'es': 'https://www.newstide.news',
      // A5: x-default → homepage ES, coherente con root layout y el resto del sitio.
      // Aunque esta es la home EN, el sitio tiene ES como idioma principal.
      'x-default': 'https://www.newstide.news',
    },
  },
  openGraph: {
    siteName: 'NewsTide',
    locale: 'en_US',
    type: 'website',
    url: 'https://www.newstide.news/en',
    title: 'NewsTide — AI, Startups & Tech News',
    description: 'Daily AI, startup and tech news for founders, developers and professionals. Stay ahead with NewsTide.',
    images: [{ url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630, alt: 'NewsTide — AI & Tech News' }],
  },
  twitter: {
    card: 'summary_large_image',
    site: '@newstide',
    creator: '@newstide',
    title: 'NewsTide — AI, Startups & Tech News',
    description: 'Daily AI, startup and tech news for founders, developers and professionals.',
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
  category: 'technology',
}

const websiteSchemaEN = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'WebSite',
      '@id': 'https://www.newstide.news/en#website',
      url: 'https://www.newstide.news/en',
      name: 'NewsTide',
      description: 'Daily AI, startup and tech news for founders, developers and professionals.',
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
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteSchemaEN) }}
      />
      <link rel="alternate" type="application/rss+xml" title="NewsTide EN RSS" href="https://www.newstide.news/en/rss.xml" />
      <link rel="alternate" type="application/rss+xml" title="NewsTide ES RSS" href="https://www.newstide.news/rss.xml" />

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

      <SubNav />

      {children}

      <footer>
        <div className="container">
          <div className="footer-top">
            <div className="footer-brand">
              <Link href="/en" className="nav-logo" style={{ marginBottom: '12px' }}>
                <div className="nav-logo-mark">NT</div>NewsTide
              </Link>
              <p className="footer-tagline">AI, startups & tech news<br />for those who stay ahead.</p>
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
                <Link href="/en/authors/javier-valencia">Javier Valencia</Link>
                <Link href="/en/contact">Contact</Link>
                <Link href="/en/privacy">Privacy</Link>
              </div>
              <div className="footer-col">
                <div className="footer-col-title">Feeds</div>
                <Link href="/en/rss.xml">RSS Feed (EN)</Link>
                <Link href="/rss.xml">RSS Feed (ES)</Link>
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
