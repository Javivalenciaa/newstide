import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Contacto — NewsTide',
  description: 'Ponte en contacto con el equipo de NewsTide para consultas editoriales, correcciones, colaboraciones o publicidad.',
  alternates: {
    canonical: 'https://www.newstide.news/contacto',
    languages: {
      'es': 'https://www.newstide.news/contacto',
      'en': 'https://www.newstide.news/en/contact',
      'x-default': 'https://www.newstide.news/en/contact',
    },
  },
}

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'ContactPage',
  name: 'Contacto — NewsTide',
  url: 'https://www.newstide.news/contacto',
  publisher: {
    '@type': 'NewsMediaOrganization',
    name: 'NewsTide',
    url: 'https://www.newstide.news',
    email: 'newstideco@gmail.com',
  },
}

export default function Contacto() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <div className="container" style={{ maxWidth: 640, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Inicio</Link>
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Contacto</h1>
        <p style={{ fontSize: 18, color: 'var(--muted)', lineHeight: 1.7, marginBottom: 48 }}>¿Tienes alguna pregunta, corrección o propuesta? Escríbenos.</p>
        <div style={{ fontSize: 16, lineHeight: 2, color: 'rgba(240,240,238,0.85)' }}>
          <p><strong>General:</strong> <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a></p>
          <p><strong>Editorial (errores, correcciones):</strong> <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a></p>
          <p><strong>Privacidad:</strong> <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a></p>
          <p><strong>Publicidad y colaboraciones:</strong> <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a></p>
        </div>
        <div style={{ marginTop: 48 }}>
          <Link href="/sobre-nosotros" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Sobre nosotros →</Link>
        </div>
      </div>
    </div>
  )
}
