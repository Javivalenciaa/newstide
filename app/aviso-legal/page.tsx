import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Aviso Legal — NewsTide',
  description: 'Aviso legal del sitio web NewsTide. Información sobre el titular, propiedad intelectual, responsabilidad y legislación aplicable.',
  alternates: {
    canonical: 'https://www.newstide.news/aviso-legal',
    languages: {
      'es': 'https://www.newstide.news/aviso-legal',
      'en': 'https://www.newstide.news/en/legal-notice',
      'x-default': 'https://www.newstide.news/en/legal-notice',
    },
  },
  robots: { index: true, follow: true },
}

export default function AvisoLegal() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Inicio</Link>
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Aviso Legal</h1>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 48 }}>Última actualización: agosto 2026</p>

        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>1. Titular del sitio web</h2>
          <p>
            En cumplimiento de la Ley 34/2002, de 11 de julio, de Servicios de la Sociedad de la Información y del Comercio Electrónico (LSSICE), se informa que el titular del sitio web <strong>newstide.news</strong> es:
          </p>
          <ul style={{ margin: '16px 0 16px 24px' }}>
            <li style={{ marginBottom: 8 }}><strong>Titular:</strong> Javier Valencia</li>
            <li style={{ marginBottom: 8 }}><strong>Actividad:</strong> Publicación digital de contenidos tecnológicos y periodismo digital</li>
            <li style={{ marginBottom: 8 }}><strong>Correo electrónico:</strong> <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a></li>
            <li style={{ marginBottom: 8 }}><strong>Sitio web:</strong> <a href="https://www.newstide.news" style={{ color: 'var(--cyan)' }}>https://www.newstide.news</a></li>
          </ul>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>2. Objeto del sitio web</h2>
          <p>
            NewsTide es una publicación digital especializada en noticias, análisis y tendencias sobre inteligencia artificial, startups, herramientas tecnológicas y finanzas. El acceso y uso de este sitio web está sujeto a las condiciones recogidas en el presente Aviso Legal y en los <Link href="/terminos-de-uso" style={{ color: 'var(--cyan)' }}>Términos de Uso</Link>.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>3. Propiedad intelectual e industrial</h2>
          <p>
            Todos los contenidos del sitio web — incluyendo, pero no limitado a, textos, artículos, análisis, imágenes, logotipos, diseño gráfico, código fuente y estructura — son propiedad de Javier Valencia o de terceros que han autorizado su uso, y están protegidos por la legislación española e internacional sobre propiedad intelectual e industrial.
          </p>
          <p style={{ marginTop: 12 }}>
            Queda expresamente prohibida la reproducción, distribución, transformación o comunicación pública de cualquier contenido de este sitio sin autorización escrita previa del titular. Se permite la reproducción parcial con fines informativos siempre que se cite la fuente y se incluya un enlace al artículo original.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>4. Uso de inteligencia artificial</h2>
          <p>
            Parte de los contenidos publicados en NewsTide se elaboran con asistencia de herramientas de inteligencia artificial. Todo el contenido es supervisado y revisado por el equipo editorial antes de su publicación. NewsTide se compromete a mantener la precisión, actualidad y veracidad de sus contenidos, y a corregir cualquier error detectado en un plazo máximo de 48 horas tras su comunicación.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>5. Exclusión de responsabilidad</h2>
          <p>
            Javier Valencia no garantiza la ausencia de errores en los contenidos del sitio ni su actualización permanente. El titular no será responsable de los daños o perjuicios que pudieran derivarse del uso de la información publicada, de interrupciones en el servicio o del acceso a sitios externos enlazados.
          </p>
          <p style={{ marginTop: 12 }}>
            Los artículos publicados en NewsTide tienen una finalidad exclusivamente informativa y no constituyen asesoramiento financiero, legal, médico ni de ninguna otra índole profesional.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>6. Enlaces a sitios de terceros</h2>
          <p>
            Este sitio puede contener enlaces a sitios web de terceros. Dichos enlaces se facilitan únicamente con finalidad informativa. Javier Valencia no se responsabiliza del contenido, políticas de privacidad ni prácticas de los sitios enlazados, y no implica recomendación ni respaldo de los mismos.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>7. Publicidad</h2>
          <p>
            Este sitio web puede mostrar anuncios a través de servicios publicitarios de terceros, incluido <strong>Google AdSense</strong>. Dichos anuncios pueden utilizar cookies para personalizar la publicidad mostrada. Consulta nuestra <Link href="/privacidad" style={{ color: 'var(--cyan)' }}>Política de Privacidad</Link> para más información.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>8. Legislación aplicable y jurisdicción</h2>
          <p>
            El presente Aviso Legal se rige por la legislación española vigente. Para la resolución de cualquier controversia derivada del acceso o uso de este sitio web, las partes se someten a la jurisdicción de los Juzgados y Tribunales españoles, con renuncia expresa a cualquier otro fuero que pudiera corresponderles.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>9. Modificaciones</h2>
          <p>
            Javier Valencia se reserva el derecho a modificar este Aviso Legal en cualquier momento. Las modificaciones serán efectivas desde su publicación en el sitio. Se recomienda revisar esta página periódicamente.
          </p>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/terminos-de-uso" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Términos de Uso →</Link>
            <Link href="/privacidad" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Política de Privacidad →</Link>
            <Link href="/contacto" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contacto →</Link>
            <Link href="/en/legal-notice" style={{ color: 'var(--muted)', fontWeight: 600, fontSize: 14 }}>Read in English →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
