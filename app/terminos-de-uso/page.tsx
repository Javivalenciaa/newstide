import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Términos de Uso — NewsTide',
  description: 'Términos y condiciones de uso del sitio web NewsTide. Reglas de acceso, uso permitido, prohibiciones, disponibilidad y limitación de responsabilidad.',
  alternates: {
    canonical: 'https://www.newstide.news/terminos-de-uso',
    languages: {
      'es': 'https://www.newstide.news/terminos-de-uso',
      'en': 'https://www.newstide.news/en/terms-of-use',
      'x-default': 'https://www.newstide.news/en/terms-of-use',
    },
  },
  robots: { index: true, follow: true },
}

export default function TerminosDeUso() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Inicio</Link>
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Términos de Uso</h1>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 48 }}>Última actualización: agosto 2026</p>

        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>1. Aceptación de las condiciones</h2>
          <p>
            El acceso y uso del sitio web <strong>newstide.news</strong>, operado por <strong>Javier Valencia</strong>, implica la aceptación plena y sin reservas de los presentes Términos de Uso, así como del <Link href="/aviso-legal" style={{ color: 'var(--cyan)' }}>Aviso Legal</Link> y la <Link href="/privacidad" style={{ color: 'var(--cyan)' }}>Política de Privacidad</Link>. Si no estás de acuerdo con alguna de estas condiciones, debes abstenerte de usar el sitio.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>2. Descripción del servicio</h2>
          <p>
            NewsTide proporciona acceso gratuito a artículos informativos, análisis y noticias sobre tecnología, inteligencia artificial, startups y finanzas. El servicio se presta tal cual, sin garantía de disponibilidad continua ni de ausencia de errores.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>3. Uso permitido</h2>
          <p>El usuario puede:</p>
          <ul style={{ margin: '12px 0 12px 24px' }}>
            <li style={{ marginBottom: 8 }}>Acceder y leer los contenidos publicados de forma libre y gratuita.</li>
            <li style={{ marginBottom: 8 }}>Compartir enlaces a los artículos en redes sociales u otras plataformas, siempre citando la fuente.</li>
            <li style={{ marginBottom: 8 }}>Reproducir fragmentos breves (hasta 150 palabras) con fines informativos o académicos, siempre que se indique la autoría y se enlace al artículo original.</li>
          </ul>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>4. Conductas prohibidas</h2>
          <p>Queda expresamente prohibido:</p>
          <ul style={{ margin: '12px 0 12px 24px' }}>
            <li style={{ marginBottom: 8 }}>Reproducir, distribuir o comercializar los contenidos del sitio sin autorización escrita previa de Javier Valencia.</li>
            <li style={{ marginBottom: 8 }}>Utilizar el contenido del sitio para entrenar modelos de inteligencia artificial o sistemas de scraping automatizado sin autorización expresa.</li>
            <li style={{ marginBottom: 8 }}>Realizar cualquier acción que pueda dañar, sobrecargar o interrumpir el correcto funcionamiento del sitio.</li>
            <li style={{ marginBottom: 8 }}>Usar el sitio con fines fraudulentos, ilegales o que vulneren derechos de terceros.</li>
            <li style={{ marginBottom: 8 }}>Suplantar la identidad de NewsTide, de Javier Valencia o de cualquier otra persona o entidad.</li>
          </ul>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>5. Contenido generado con IA</h2>
          <p>
            Parte del contenido de NewsTide se elabora con asistencia de herramientas de inteligencia artificial y es revisado por el equipo editorial antes de su publicación. Los artículos se etiquetan de forma transparente cuando han sido asistidos por IA. NewsTide no asume responsabilidad por errores derivados de limitaciones inherentes a las herramientas de IA utilizadas, siempre que se haya realizado la revisión editorial correspondiente.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>6. Contenido informativo — no asesoramiento profesional</h2>
          <p>
            Los artículos y análisis publicados en NewsTide tienen una finalidad exclusivamente informativa. Ningún contenido del sitio constituye asesoramiento financiero, legal, fiscal, médico ni de ninguna otra índole profesional. El usuario es responsable de las decisiones que tome en base a la información publicada.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>7. Disponibilidad del servicio</h2>
          <p>
            Javier Valencia se esfuerza por mantener el sitio disponible de forma continua, pero no garantiza la ausencia de interrupciones técnicas, mantenimientos o caídas del servicio. El titular no será responsable de los perjuicios que puedan derivarse de la falta de disponibilidad temporal del sitio.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>8. Publicidad de terceros</h2>
          <p>
            NewsTide puede mostrar anuncios de terceros, incluido Google AdSense. Javier Valencia no es responsable del contenido de dichos anuncios ni de las prácticas de los anunciantes. La visualización de anuncios no supone recomendación ni respaldo de los productos o servicios anunciados.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>9. Modificación y suspensión</h2>
          <p>
            Javier Valencia se reserva el derecho a modificar, suspender o cancelar el servicio en cualquier momento y sin previo aviso, así como a actualizar los presentes Términos de Uso. Los cambios serán efectivos desde su publicación en el sitio.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>10. Contacto</h2>
          <p>
            Para cualquier consulta relacionada con estos Términos de Uso, puedes contactar con nosotros en{' '}
            <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a>.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>11. Legislación aplicable</h2>
          <p>
            Los presentes Términos de Uso se rigen por la legislación española. Para la resolución de cualquier controversia las partes se someten a la jurisdicción de los Juzgados y Tribunales españoles.
          </p>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/aviso-legal" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Aviso Legal →</Link>
            <Link href="/privacidad" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Política de Privacidad →</Link>
            <Link href="/contacto" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contacto →</Link>
            <Link href="/en/terms-of-use" style={{ color: 'var(--muted)', fontWeight: 600, fontSize: 14 }}>Read in English →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
