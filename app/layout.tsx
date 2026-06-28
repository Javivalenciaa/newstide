import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import Script from 'next/script'
import { headers } from 'next/headers'
import './globals.css'
import SpanishShell from '@/components/SpanishShell'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

const GA_ID = 'G-C0Z8YQC18J'

export const metadata: Metadata = {
  title: {
    default: 'NewsTide — Noticias de IA, Startups y Tech en Español',
    template: '%s | NewsTide',
  },
  description: 'Noticias diarias de inteligencia artificial, startups y herramientas tech para founders, developers y profesionales. Actualizado cada día.',
  metadataBase: new URL('https://www.newstide.news'),
  alternates: {
    canonical: 'https://www.newstide.news',
    languages: {
      'es': 'https://www.newstide.news',
      'en': 'https://www.newstide.news/en',
      'x-default': 'https://www.newstide.news/en',
    },
  },
  openGraph: {
    siteName: 'NewsTide',
    locale: 'es_ES',
    type: 'website',
    url: 'https://www.newstide.news',
    title: 'NewsTide — Noticias de IA, Startups y Tech en Español',
    description: 'Noticias diarias de inteligencia artificial, startups y herramientas tech para founders, developers y profesionales.',
    images: [{ url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630, alt: 'NewsTide' }],
  },
  twitter: {
    card: 'summary_large_image',
    site: '@newstide',
    creator: '@newstide',
    title: 'NewsTide — Noticias de IA, Startups y Tech en Español',
    description: 'Noticias diarias de inteligencia artificial, startups y herramientas tech para founders, developers y profesionales.',
    images: ['https://www.newstide.news/og-image.png'],
  },
  icons: {
    icon: [
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/favicon-192x192.png', sizes: '192x192', type: 'image/png' },
    ],
    apple: '/apple-touch-icon.png',
    shortcut: '/favicon.ico',
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
  verification: {
    google: '3vsTOEg0poOd6Waol-lATdTKyfxLUkWoqxHZuL0q774',
  },
  category: 'technology',
}

const websiteSchema = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'WebSite',
      '@id': 'https://www.newstide.news/#website',
      url: 'https://www.newstide.news',
      name: 'NewsTide',
      description: 'Noticias diarias de inteligencia artificial, startups y herramientas tech.',
      inLanguage: 'es',
      publisher: { '@id': 'https://www.newstide.news/#organization' },
      potentialAction: {
        '@type': 'SearchAction',
        target: { '@type': 'EntryPoint', urlTemplate: 'https://www.newstide.news/?q={search_term_string}' },
        'query-input': 'required name=search_term_string',
      },
    },
    {
      '@type': 'NewsMediaOrganization',
      '@id': 'https://www.newstide.news/#organization',
      name: 'NewsTide',
      url: 'https://www.newstide.news',
      logo: { '@type': 'ImageObject', url: 'https://www.newstide.news/favicon-192x192.png', width: 192, height: 192 },
      sameAs: ['https://twitter.com/newstide'],
      publishingPrinciples: 'https://www.newstide.news/politica-editorial',
      correctionsPolicy: 'https://www.newstide.news/politica-editorial#correcciones',
      actionableFeedbackPolicy: 'https://www.newstide.news/politica-editorial#feedback',
      verificationFactCheckingPolicy: 'https://www.newstide.news/politica-editorial#verificacion',
      masthead: 'https://www.newstide.news/equipo-editorial',
    },
  ],
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Detect language from the incoming request path at SSR time.
  // next/headers gives us access to request headers in Server Components.
  // The 'next-url' header contains the matched pathname (e.g. /en/article/...).
  const headersList = await headers()
  const nextUrl = headersList.get('next-url') ?? ''
  const isEnglish = nextUrl.startsWith('/en')
  const lang = isEnglish ? 'en' : 'es'

  return (
    <html lang={lang}>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteSchema) }}
        />
      </head>
      <body className={`${inter.variable} ${mono.variable}`}>
        <SpanishShell>{children}</SpanishShell>
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
          strategy="afterInteractive"
        />
        <Script id="ga4" strategy="afterInteractive">{`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', '${GA_ID}', { page_path: window.location.pathname });
        `}</Script>
      </body>
    </html>
  )
}
