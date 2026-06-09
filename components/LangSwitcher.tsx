'use client'
import { usePathname } from 'next/navigation'
import Link from 'next/link'

export default function LangSwitcher() {
  const pathname = usePathname()
  const isEN = pathname.startsWith('/en')

  // Build the alternate URL
  let altHref: string
  if (isEN) {
    // EN → ES
    if (pathname === '/en') {
      altHref = '/'
    } else if (pathname.startsWith('/en/article/')) {
      const slug = pathname.replace('/en/article/', '')
      altHref = `/articulo/${slug}`
    } else {
      altHref = '/'
    }
  } else {
    // ES → EN
    if (pathname === '/') {
      altHref = '/en'
    } else if (pathname.startsWith('/articulo/')) {
      const slug = pathname.replace('/articulo/', '')
      altHref = `/en/article/${slug}`
    } else {
      altHref = '/en'
    }
  }

  return (
    <Link
      href={altHref}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '5px 12px',
        borderRadius: 8,
        border: '1px solid var(--border)',
        fontSize: 12,
        fontWeight: 600,
        letterSpacing: '0.05em',
        color: 'var(--muted)',
        background: 'var(--surface)',
        textDecoration: 'none',
        transition: 'border-color 0.2s, color 0.2s',
      }}
    >
      {isEN ? '🇪🇸 ES' : '🇬🇧 EN'}
    </Link>
  )
}
