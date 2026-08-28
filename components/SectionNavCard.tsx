'use client'

import Link from 'next/link'
import { useState } from 'react'

interface SectionNavCardProps {
  href: string
  icon: string
  label: string
  desc: string
}

export default function SectionNavCard({ href, icon, label, desc }: SectionNavCardProps) {
  const [hovered, setHovered] = useState(false)

  return (
    <Link
      href={href}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        padding: '20px 18px',
        borderRadius: 10,
        border: `1px solid ${hovered ? 'var(--accent)' : 'var(--border)'}`,
        background: hovered ? 'rgba(110,207,202,0.07)' : 'rgba(110,207,202,0.03)',
        textDecoration: 'none',
        transition: 'border-color 0.2s, background 0.2s',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <span style={{ fontSize: 26 }}>{icon}</span>
      <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--fg)' }}>{label}</span>
      <span style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.4 }}>{desc}</span>
    </Link>
  )
}
