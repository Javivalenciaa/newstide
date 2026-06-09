import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'NewsTide — The intelligence shaping the future',
  description: 'Technology, AI and trends for founders, developers and professionals.',
  openGraph: { siteName: 'NewsTide', locale: 'en_US', type: 'website' },
}

export default function EnLayout({ children }: { children: React.ReactNode }) {
  // Override lang="en" for all /en/* routes.
  // The <html> tag rendered by the root layout is replaced by this one
  // because Next.js merges nested layouts — the closest layout wins for html attributes.
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
