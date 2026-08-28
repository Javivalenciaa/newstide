'use client'
import Link from 'next/link'

const GUIDE_TABS = [
  { label: 'All Articles',  href: '/en/articles',                     emoji: '📰' },
  { label: 'Comparisons',  href: '/en/compare?filter=comparisons',    emoji: '⚔️' },
  { label: 'Alternatives', href: '/en/compare?filter=alternatives',   emoji: '🔄' },
  { label: 'Guides',       href: '/en/compare?filter=guides',         emoji: '📖' },
  { label: 'For Pros',     href: '/en/compare?filter=for-profession', emoji: '👤' },
]

const linkStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
  padding: '10px 14px',
  fontSize: 13,
  fontWeight: 500,
  color: 'var(--muted)',
  textDecoration: 'none',
  borderBottom: '2px solid transparent',
  transition: 'color .15s, border-color .15s',
  flexShrink: 0,
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      style={linkStyle}
      onMouseEnter={e => {
        e.currentTarget.style.color = 'var(--text)'
        e.currentTarget.style.borderBottomColor = 'var(--cyan)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.color = 'var(--muted)'
        e.currentTarget.style.borderBottomColor = 'transparent'
      }}
    >
      {children}
    </Link>
  )
}

export default function SubNav() {
  return (
    <div
      id="subnav"
      style={{
        position: 'sticky',
        top: 60,
        zIndex: 90,
        background: 'var(--bg)',
        borderBottom: '1px solid var(--border)',
        overflowX: 'auto',
        WebkitOverflowScrolling: 'touch',
        scrollbarWidth: 'none',
      }}
    >
      <style>{`#subnav::-webkit-scrollbar{display:none}`}</style>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          padding: '0 16px',
          maxWidth: 1200,
          margin: '0 auto',
          whiteSpace: 'nowrap',
        }}
      >
        <NavLink href="/en">🏠 Home</NavLink>
        <span style={{ width: 1, height: 16, background: 'var(--border)', flexShrink: 0, margin: '0 4px' }} />
        {GUIDE_TABS.map(tab => (
          <NavLink key={tab.href} href={tab.href}>
            {tab.emoji} {tab.label}
          </NavLink>
        ))}
      </div>
    </div>
  )
}
