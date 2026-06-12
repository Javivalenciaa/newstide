import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import SpanishShell from '@/components/SpanishShell'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: 'NewsTide — La inteligencia que transforma el futuro',
  description: 'Tecnología, IA y tendencias para founders, developers y profesionales.',
  metadataBase: new URL('https://www.newstide.news'),
  openGraph: { siteName: 'NewsTide', locale: 'es_ES', type: 'website' },
  twitter: { card: 'summary_large_image', site: '@newstide' },
  icons: { icon: '/favicon.ico' },
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
