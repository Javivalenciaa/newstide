import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import SpanishShell from '@/components/SpanishShell'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: {
    default: 'NewsTide — La inteligencia que transforma el futuro',
    template: '%s | NewsTide',
  },
  description: 'Tecnología, IA y tendencias para founders, developers y profesionales.',
  metadataBase: new URL('https://www.newstide.news'),
  alternates: {
    canonical: 'https://www.newstide.news',
    languages: {
      'es': 'https://www.newstide.news',
      'en': 'https://www.newstide.news/en',
    },
  },
  openGraph: {
    siteName: 'NewsTide',
    locale: 'es_ES',
    type: 'website',
    url: 'https://www.newstide.news',
  },
  twitter: {
    card: 'summary_large_image',
    site: '@newstide',
    creator: '@newstide',
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
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${inter.variable} ${mono.variable}`}>
      <body>
        <SpanishShell>
          {children}
        </SpanishShell>
      </body>
    </html>
  )
}
