'use client'
import { useState } from 'react'
import Link from 'next/link'

interface Props {
  lang: 'es' | 'en'
}

const NAV = {
  es: [
    { label: '🏠 Inicio',        href: '/' },
    { label: '📰 Artículos',     href: '/articulos' },
    { label: '📬 Newsletter',    href: '/#newsletter' },
  ],
  en: [
    { label: '🏠 Home',          href: '/en' },
    { label: '📰 All Articles',  href: '/en/articles' },
    { label: '📬 Newsletter',    href: '/en#newsletter' },
  ],
}

// Guides section — only shown for EN (pSEO is English-only)
const GUIDE_LINKS = [
  { label: '⚔️ Comparisons',   href: '/en/compare?filter=comparisons' },
  { label: '🔄 Alternatives',  href: '/en/compare?filter=alternatives' },
  { label: '📖 Guides',        href: '/en/compare?filter=guides' },
  { label: '👤 For Pros',      href: '/en/compare?filter=for-profession' },
]

export default function MobileNav({ lang }: Props) {
  const [open, setOpen] = useState(false)
  const links = NAV[lang]

  return (
    <>
      {/* Hamburger button — only visible on mobile */}
      <button
        onClick={() => setOpen(o => !o)}
        aria-label="Menu"
        style={{
          display: 'none',
          background: 'none',
          border: '1px solid var(--border)',
          borderRadius: 6,
          padding: '6px 10px',
          cursor: 'pointer',
          color: 'var(--fg)',
          lineHeight: 1,
          fontSize: 18,
        }}
        className="mobile-menu-btn"
      >
        {open ? '✕' : '☰'}
      </button>

      {/* Drawer */}
      {open && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 999,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Backdrop */}
          <div
            onClick={() => setOpen(false)}
            style={{
              position: 'absolute',
              inset: 0,
              background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(4px)',
            }}
          />
          {/* Panel */}
          <nav style={{
            position: 'relative',
            marginTop: '64px',
            marginLeft: 'auto',
            marginRight: 'auto',
            width: 'min(320px, 90vw)',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 16,
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
            boxShadow: '0 24px 64px rgba(0,0,0,0.4)',
          }}>

            {/* Main links */}
            {links.map(l => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                style={{
                  padding: '13px 16px',
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 500,
                  color: 'var(--fg)',
                  textDecoration: 'none',
                  display: 'block',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--hover)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                {l.label}
              </Link>
            ))}

            {/* Guides section — EN only */}
            {lang === 'en' && (
              <>
                <div style={{ height: 1, background: 'var(--border)', margin: '8px 0' }} />
                <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--faint)', padding: '0 16px', margin: '4px 0 2px' }}>Guides &amp; Tools</p>
                {GUIDE_LINKS.map(l => (
                  <Link
                    key={l.href}
                    href={l.href}
                    onClick={() => setOpen(false)}
                    style={{
                      padding: '11px 16px',
                      borderRadius: 10,
                      fontSize: 14,
                      fontWeight: 400,
                      color: 'var(--muted)',
                      textDecoration: 'none',
                      display: 'block',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--hover)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  >
                    {l.label}
                  </Link>
                ))}
              </>
            )}

            <div style={{ height: 1, background: 'var(--border)', margin: '8px 0' }} />
            <Link
              href={lang === 'es' ? '/#newsletter' : '/en#newsletter'}
              onClick={() => setOpen(false)}
              className="nav-cta"
              style={{ textAlign: 'center', marginTop: 4, padding: '12px' }}
            >
              {lang === 'es' ? 'Suscribirse gratis' : 'Subscribe for free'}
            </Link>
          </nav>
        </div>
      )}
    </>
  )
}
