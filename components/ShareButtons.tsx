'use client'
import { useState } from 'react'

interface Props {
  url: string
  title: string
}

export default function ShareButtons({ url, title }: Props) {
  const [copied, setCopied] = useState(false)

  const encodedUrl = encodeURIComponent(url)
  const encodedTitle = encodeURIComponent(title)

  function copyLink() {
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const shareLinks = [
    {
      label: '𝕏',
      title: 'Compartir en X (Twitter)',
      href: `https://twitter.com/intent/tweet?text=${encodedTitle}&url=${encodedUrl}`,
    },
    {
      label: 'in',
      title: 'Compartir en LinkedIn',
      href: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`,
    },
  ]

  return (
    <div style={{ display: 'flex', gap: 10 }}>
      {shareLinks.map((s) => (
        <a
          key={s.label}
          href={s.href}
          target="_blank"
          rel="noopener noreferrer"
          title={s.title}
          style={{
            flex: 1, padding: '8px 0', borderRadius: 8,
            background: 'var(--bg)', border: '1px solid var(--border)',
            color: 'var(--muted)', fontSize: 13, fontWeight: 600,
            cursor: 'pointer', transition: 'border-color 0.2s, color 0.2s',
            textDecoration: 'none', textAlign: 'center', display: 'block',
          }}
        >
          {s.label}
        </a>
      ))}
      <button
        onClick={copyLink}
        title="Copiar enlace"
        style={{
          flex: 1, padding: '8px 0', borderRadius: 8,
          background: copied ? 'rgba(110,207,202,0.1)' : 'var(--bg)',
          border: `1px solid ${copied ? 'rgba(110,207,202,0.4)' : 'var(--border)'}`,
          color: copied ? '#6ecfca' : 'var(--muted)',
          fontSize: 13, fontWeight: 600, cursor: 'pointer',
          transition: 'all 0.2s',
        }}
      >
        {copied ? '✓' : '🔗'}
      </button>
    </div>
  )
}
