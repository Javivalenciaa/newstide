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
    // FIX C3: this template is the SINGLE source of truth for the title suffix.
    // All child layouts/pages must use template: '%s' (no suffix) to avoid
    // producing '… | NewsTide | NewsTide' on every page.
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
    images: [{ url: 'https://www.newstide.news/og-image.png', width: 1200, height: 630, alt: 'NewsTide — Noticias de IA y Tech' }],
  },
  twitter: {
    card: 'summary_large_image',
    site: '@newstide',
    creator: '@newstide',
    title: 'NewsTide — Noticias de IA, Startups y Tech en Español',
    description: 'Noticias