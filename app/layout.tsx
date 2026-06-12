import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: 'NewsTide',
  description: 'Tecnología, IA y tendencias para founders, developers y profesionales.',
  metadataBase: new URL('https://www.newstide.news'),
  openGraph: { siteName: 'NewsTide', type: 'website' },
  twitter: { card: 'summary_large_image', site: '@newstide' },
  icons: { icon: '/favicon.ico' },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html className={`${inter.variable} ${mono.variable}`}>
      <body>
        {children}
      </body>
    </html>
  )
}
