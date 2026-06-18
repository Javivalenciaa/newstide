import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import SpanishShell from '@/components/SpanishShell'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

const GA_ID = 'G-C0Z8YQC18J'

export const metadata: Metadata = {
  title: {
    default: 'NewsTide — La inteligencia que transforma el futuro',
    template: '%s | NewsTide',
  },
  description: 'Tecnología, IA y tendencias para founders, developers y profesionales. Noticias diarias sobre inteligencia artificial, startups y herramientas tech.',
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
    title: 'NewsTide — La inteligencia que transforma el futuro',
    description: 'Tecnología, IA y tendencias para founders, developers y profesionales.',
    images: [{ url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630, alt: 'NewsTide' }],
  },
  twitter: {
    card: 'summary_large_image',
    site: '@newstide',
    creator: '@newstide',
    title: 'NewsTide — La inteligencia que transforma el futuro',
    description: 'Tecnología, IA y tendencias para founders, developers y profesionales.',
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
    google: 'pending-add-your-gsc-token-here',
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
      description: 'Tecnología, IA y tendencias para founders, developers y profesionales.',
      inLanguage: 'es',
      potentialAction: {
        '@type': 'SearchAction',
        target: {
          '@type': 'EntryPoint',
          urlTemplate: 'https://www.newstide.news/articulos?q={search_term_string}',
        },
        'query-input': 'required name=search_term_string',
      },
    },
    {
      '@type': 'NewsMediaOrganization',
      '@id': 'https://www.newstide.news/#organization',
      name: 'NewsTide',
      alternateName: 'NewsTide News',
      url: 'https://www.newstide.news',
      logo: {
        '@type': 'ImageObject',
        url: 'https://www.newstide.news/favicon-192x192.png',
        width: 192,
        height: 192,
      },
      sameAs: [
        'https://twitter.com/newstide',
        'https://linkedin.com/company/newstide',
      ],
      foundingDate: '2026',
      description: 'NewsTide es un medio de noticias especializado en tecnología, inteligencia artificial, startups y finanzas tech. Publicamos artículos elaborados por periodistas y expertos con asistencia de inteligencia artificial.',
      publishingPrinciples: 'https://www.newstide.news/politica-editorial',
      ownershipFundingInfo: 'https://www.newstide.news/sobre-nosotros',
      actionableFeedbackPolicy: 'https://www.newstide.news/politica-editorial#correcciones',
      correctionsPolicy: 'https://www.newstide.news/politica-editorial#correcciones',
      ethicsPolicy: 'https://www.newstide.news/politica-editorial#etica',
      masthead: 'https://www.newstide.news/sobre-nosotros#equipo',
      diversityPolicy: 'https://www.newstide.news/sobre-nosotros',
      verificationFactCheckingPolicy: 'https://www.newstide.news/politica-editorial#verificacion',
      contactPoint: {
        '@type': 'ContactPoint',
        email: 'hola@newstide.news',
        contactType: 'editorial',
        availableLanguage: ['Spanish', 'English'],
      },
    },
  ],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${inter.variable} ${mono.variable}`}>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteSchema) }}
        />
        <link rel="alternate" type="application/rss+xml" title="NewsTide RSS" href="https://www.newstide.news/rss.xml" />
        {/* Google Analytics */}
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
        <SpanishShell>
          {children}
        </SpanishShell>
      </body>
    </html>
  )
}
