import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Política Editorial — NewsTide',
  description: 'Conoce los estándares editoriales de NewsTide: cómo usamos la IA, cómo revisamos el contenido, nuestro proceso de corrección y nuestros compromisos de transparencia.',
  alternates: {
    canonical: 'https://www.newstide.news/politica-editorial',
    languages: {
      'es': 'https://www.newstide.news/politica-editorial',
      'en': 'https://www.newstide.news/en/editorial-policy',
      'x-default': 'https://www.newstide.news/en/editorial-policy',
    },
  },
}

export default function PoliticaEditorial() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Inicio</Link>
        </div>

        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Política Editorial</h1>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 48 }}>Última actualización: junio 2026</p>

        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>1. Uso de inteligencia artificial</h2>
          <p>
            NewsTide utiliza modelos de inteligencia artificial para asistir en la redacción, estructuración y traducción
            de artículos. Cada artículo publicado es revisado por un editor humano que verifica la precisión de los
            datos, la coherencia del análisis y la adecuación del tono editorial antes de su publicación.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>2. Fuentes y verificación</h2>
          <p>
            Todos los artículos se basan en fuentes primarias verificables: comunicados de prensa oficiales,
            informes corporativos, documentación técnica, datos de mercado de fuentes reconocidas y declaraciones
            públicas de personas con autoridad en el tema tratado. Enlazamos a las fuentes originales siempre
            que es técnicamente posible.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>3. Correcciones y actualizaciones</h2>
          <p>
            Si un artículo contiene un error factual, NewsTide se compromete a corregirlo en un plazo máximo de
            48 horas tras ser notificado. Las correcciones se realizarán de forma transparente, indicando en el
            artículo la naturaleza del cambio y la fecha de la corrección. Para reportar un error, contacta con
            nosotros en <a href="mailto:editorial@newstide.news" style={{ color: 'var(--cyan)' }}>editorial@newstide.news</a>.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>4. Independencia editorial</h2>
          <p>
            El contenido editorial de NewsTide es completamente independiente de cualquier relación comercial,
            publicitaria o de afiliados. Las reseñas, análisis y comparativas se realizan sin intervención de
            las empresas analizadas. Cuando un artículo contiene enlaces de afiliado, se indica expresamente.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>5. Conflictos de interés</h2>
          <p>
            Ningún miembro del equipo editorial de NewsTide puede publicar artículos sobre empresas en las que
            tenga intereses financieros directos sin una declaración explícita de dicho conflicto al inicio del artículo.
          </p>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 12, marginTop: 40 }}>6. Diversidad y representación</h2>
          <p>
            NewsTide se compromete a cubrir el ecosistema tecnológico y financiero desde una perspectiva global,
            incluyendo voces, empresas y perspectivas diversas en sus análisis.
          </p>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/sobre-nosotros" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Sobre nosotros →</Link>
            <Link href="/contacto" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contacto →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
