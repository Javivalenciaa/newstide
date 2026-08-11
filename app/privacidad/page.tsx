import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Política de Privacidad — NewsTide',
  description: 'Política de privacidad de NewsTide. Información sobre cómo recopilamos, usamos y protegemos tus datos personales, incluyendo el uso de cookies y publicidad.',
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
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 48 }}>Última actualización: agosto 2026</p>
        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>1. Responsable del tratamiento</h2>
          <p>
            El responsable del tratamiento de los datos personales recogidos a través de este sitio web
            (newstide.news) es <strong>Javier Valencia</strong>, fundador de NewsTide.
            Correo de contacto: <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a>.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>2. Datos que recopilamos</h2>
          <p>Recopilamos los siguientes tipos de datos:</p>
          <ul style={{ margin: '12px 0 12px 24px' }}>
            <li style={{ marginBottom: 8 }}><strong>Datos de navegación anónimos</strong> a través de Google Analytics 4 (dirección IP anonimizada, páginas visitadas, tiempo de sesión, tipo de dispositivo y navegador).</li>
            <li style={{ marginBottom: 8 }}><strong>Datos de email</strong> si te suscribes voluntariamente a nuestra newsletter, almacenados con tu consentimiento explícito.</li>
            <li style={{ marginBottom: 8 }}><strong>Datos técnicos de cookies</strong> necesarios para el correcto funcionamiento del sitio.</li>
          </ul>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>3. Finalidad del tratamiento</h2>
          <p>
            Los datos de analítica se usan exclusivamente para mejorar los contenidos y la experiencia del sitio.
            El email de newsletter se usa únicamente para enviar el boletín al que te has suscrito y no se cede a terceros.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>4. Cookies y publicidad</h2>
          <p>Este sitio utiliza los siguientes tipos de cookies:</p>
          <ul style={{ margin: '12px 0 12px 24px' }}>
            <li style={{ marginBottom: 8 }}><strong>Cookies técnicas:</strong> necesarias para el funcionamiento básico del sitio. No requieren consentimiento.</li>
            <li style={{ marginBottom: 8 }}><strong>Cookies analíticas:</strong> Google Analytics 4 para medir el uso del sitio de forma anonimizada. Puedes desactivarlas desde la configuración de tu navegador o instalando el <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>complemento de inhabilitación de Google Analytics</a>.</li>
            <li style={{ marginBottom: 8 }}><strong>Cookies publicitarias:</strong> este sitio utiliza <strong>Google AdSense</strong> para mostrar anuncios. Google y sus socios pueden usar cookies para mostrar anuncios personalizados basados en tus visitas a este y otros sitios. Puedes desactivar la publicidad personalizada visitando <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>Configuración de anuncios de Google</a> o mediante <a href="https://optout.aboutads.info/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>aboutads.info</a>.</li>
          </ul>
          <p style={{ marginTop: 12 }}>
            Más información sobre cómo Google utiliza los datos en sitios que usan sus servicios:{' '}
            <a href="https://policies.google.com/technologies/partner-sites" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>policies.google.com/technologies/partner-sites</a>.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>5. Base legal del tratamiento</h2>
          <p>
            El tratamiento de datos analíticos se basa en nuestro interés legítimo en mejorar el servicio (Art. 6.1.f RGPD).
            El tratamiento de datos de newsletter se basa en el consentimiento explícito del usuario (Art. 6.1.a RGPD).
            El tratamiento asociado a la publicidad personalizada de AdSense se basa en el consentimiento del usuario.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>6. Conservación de datos</h2>
          <p>
            Los datos de analítica se conservan durante 14 meses (configuración estándar de GA4).
            Los datos de email de newsletter se conservan hasta que el usuario solicite la baja.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>7. Tus derechos</h2>
          <p>
            De acuerdo con el RGPD, tienes derecho a acceder, rectificar, suprimir, limitar, oponerte y
            portabilizar tus datos. También tienes derecho a retirar el consentimiento en cualquier momento sin
            que ello afecte a la licitud del tratamiento previo. Para ejercer cualquier derecho, contacta con
            nosotros en <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a>.
            Si consideras que el tratamiento no es conforme, puedes presentar una reclamación ante la
            <a href="https://www.aepd.es" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}> Agencia Española de Protección de Datos (AEPD)</a>.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>8. Cambios en esta política</h2>
          <p>
            Nos reservamos el derecho a actualizar esta política de privacidad. Cualquier cambio relevante
            será comunicado mediante un aviso visible en el sitio. Te recomendamos revisar esta página periódicamente.
          </p>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>← Volver al inicio</Link>
            <Link href="/contacto" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contacto →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
