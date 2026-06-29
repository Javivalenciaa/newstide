'use client'
import { useState, useRef } from 'react'

interface Props {
  compact?: boolean
}

export default function NewsletterForm({ compact }: Props) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [msg, setMsg] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const email = inputRef.current?.value?.trim()
    if (!email) return
    setStatus('loading')
    try {
      const res = await fetch('/api/newsletter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      if (res.ok) {
        setStatus('ok')
        setMsg('¡Suscrito! Te esperamos en el próximo número.')
      } else {
        const d = await res.json()
        setStatus('error')
        setMsg(d.error || 'Algo salió mal, inténtalo de nuevo.')
      }
    } catch {
      setStatus('error')
      setMsg('Error de conexión. Inténtalo de nuevo.')
    }
  }

  if (status === 'ok') {
    return (
      <div style={{ fontSize: 13, color: '#6ecfca', fontWeight: 600, textAlign: 'center', padding: compact ? '8px 0' : '12px 0' }}>
        ✓ {msg}
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <input
        ref={inputRef}
        type="email"
        required
        placeholder="tu@email.com"
        disabled={status === 'loading'}
        className="sidebar-email"
      />
      <button
        type="submit"
        disabled={status === 'loading'}
        className="sidebar-sub-btn"
        style={{ opacity: status === 'loading' ? 0.6 : 1, cursor: status === 'loading' ? 'wait' : 'pointer' }}
      >
        {status === 'loading' ? 'Enviando…' : 'Suscribirse gratis'}
      </button>
      {status === 'error' && (
        <p style={{ fontSize: 12, color: '#ef6c6c', margin: 0 }}>{msg}</p>
      )}
    </form>
  )
}
