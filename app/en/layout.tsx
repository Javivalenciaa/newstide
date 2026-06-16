import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import Script from 'next/script'
import Link from 'next/link'
import LangSwitcher from '@/components/LangSwitcher'
import MobileNav from '@/components/MobileNav'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

const GA_ID = 'G-C0Z8YQC18J'

export const metadata: Metadata = {
  title: {
    default: 'NewsTide — The intelligence shaping the future',
    template: '%s | NewsTide',
  },
  description: 'Technology, AI and trends for founders, developers and professionals.',
  metadataBase: new URL('https://www.newstide.news'),
  alternates: {
    canonical: 'https://www.newstide.news/en',
    languages: {
      'es': 'https://www.newstide.news',
      'en': 'https://www.newstide.news/en',
    },
  },
  openGraph: {
    siteName: 'NewsTide',
    locale: 'en_US',
    type: 'website',
    url: 'https://www.newstide.news/en',
  },
  twitter: {
    card: 'summary_large_image',
    site: '@newstide',
    creator: '@newstide',
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

// ⚠️ Este layout ES el root para /en — sobreescribe el html lang="es" del root layout
// Next.js App Router: el layout más cercano gana en el árbol de segmentos
export default function EnLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`}>
      <head>
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GA_ID}', {
              page_path: window.location.pathname,
            });
          `}
        </Script>
      </head>
      <body>
        <nav id="navbar">
          <Link href="/en" className="nav-logo">
            <div className="nav-logo-mark">NT</div>
            NewsTide
          </Link>
          <div className="nav-links">
            <Link href="/en">Home</Link>
            <Link href="/en/articles">Articles</Link>
            <Link href="/en#newsletter">Newsletter</Link>
          </div>
          <div className="nav-right" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <LangSwitcher />
            <Link href="/en#newsletter" className="nav-cta">Subscribe</Link>
            <MobileNav lang="en" />
          </div>
        </nav>
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
                  <Link href="/en/articles">AI &amp; Models</Link>
                  <Link href="/en/articles">Startups</Link>
                  <Link href="/en/articles">Tools</Link>
                  <Link href="/en/articles">Tutorials</Link>
                </div>
                <div className="footer-col">
                  <div className="footer-col-title">Company</div>
                  <Link href="/en/about">About us</Link>
                  <Link href="/en/contact">Contact</Link>
                  <Link href="/en/privacy">Privacy</Link>
                </div>
              </div>
            </div>
            <div className="footer-bottom">
              <span>© 2026 NewsTide · All rights reserved</span>
              <span style={{ color: 'var(--faint)' }}>newstide.news</span>
            </div>
          </div>
        </footer>
        <script dangerouslySetInnerHTML={{ __html: `
          const nav = document.getElementById('navbar');
          if(nav) window.addEventListener('scroll', () => nav.classList.toggle('scrolled', window.scrollY > 20), {passive:true});
        ` }} />
      </body>
    </html>
  )
}
