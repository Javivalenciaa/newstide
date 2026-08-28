'use client'
import { useState, useRef } from 'react'

interface Props {
  compact?: boolean
  lang?: 'es' | 'en'
}

export default function NewsletterForm({ compact, lang = 'es' }: Props) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [msg, setMsg] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const copy = {
    es: {
      placeholder: 'tu@email.com',
      btn: 'Suscribirse gratis',
      sending: 'Enviando…',
      ok: '¡Suscrito! Te esperamos en el próximo número.',
      err: 'Algo salió mal, inténtalo de nuevo.',
      connErr: 'Error de conexión. Inténtalo de nuevo.',
    },
    en: {
      placeholder: 'you@email.com',
      btn: 'Subscribe for free',
      sending: 'Sending…',
      ok: 'Subscribed! See you in the next issue.',
      err: 'Something went wrong, please try again.',
      connErr: 'Connection error. Please try again.',
    },
  }[lang]

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
        setMsg(copy.ok)
      } else {
        const d = await res.json()
        setStatus('error')
        setMsg(d.error || copy.err)
      }
    } catch {
      setStatus('error')
      setMsg(copy.connErr)
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
        placeholder={copy.placeholder}
        disabled={status === 'loading'}
        className="sidebar-email"
      />
      <button
        type="submit"
        disabled={status === 'loading'}
        className="sidebar-sub-btn"
        style={{ opacity: status === 'loading' ? 0.6 : 1, cursor: status === 'loading' ? 'wait' : 'pointer' }}
      >
        {status === 'loading' ? copy.sending : copy.btn}
      </button>
      {status === 'error' && (
        <p style={{ fontSize: 12, color: '#ef6c6c', margin: 0 }}>{msg}</p>
      )}
    </form>
  )
}
