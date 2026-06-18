import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Política de Privacidad — NewsTide',
  description: 'Política de privacidad de NewsTide. Información sobre cómo recopilamos, usamos y protegemos tus datos personales.',
  alternates: {
    canonical: 'https://www.newstide.news/privacidad',
    languages: {
      'es': 'https://www.newstide.news/privacidad',
      'en': 'https://www.newstide.news/en/privacy',
      'x-default': 'https://www.newstide.news/en/privacy',
    },
  },
  robots: { index: true, follow: true },
}

export default function Privacidad() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Inicio</Link>
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Política de Privacidad</h1>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 48 }}>Última actualización: junio 2026</p>
        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>1. Responsable del tratamiento</h2>
          <p>NewsTide es responsable del tratamiento de los datos personales recogidos a través de este sitio web (newstide.news).</p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>2. Datos que recopilamos</h2>
          <p>Recopilamos datos de navegación anónimos a través de Google Analytics (dirección IP anonimizada, páginas visitadas, tiempo de sesión). Si te suscribes a nuestra newsletter, almacenamos tu dirección de email con tu consentimiento explícito.</p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>3. Finalidad del tratamiento</h2>
          <p>Los datos de analítica se usan exclusivamente para mejorar los contenidos y la experiencia del sitio. El email de newsletter se usa únicamente para enviar el boletín al que te has suscrito.</p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>4. Cookies</h2>
          <p>Este sitio utiliza cookies técnicas necesarias para su funcionamiento y cookies analíticas de Google Analytics. Puedes desactivar las cookies analíticas desde la configuración de tu navegador.</p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>5. Tus derechos</h2>
          <p>Tienes derecho a acceder, rectificar, suprimir, limitar y portabilizar tus datos. Para ejercer cualquier derecho, contacta con nosotros en <a href="mailto:privacidad@newstide.news" style={{ color: 'var(--cyan)' }}>privacidad@newstide.news</a>.</p>

          <div style={{ marginTop: 48 }}>
            <Link href="/" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>← Volver al inicio</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
