import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Sobre NewsTide — Tecnología e IA para los que van por delante',
  description: 'Conoce a NewsTide: quiénes somos, cómo creamos nuestro contenido y por qué cubrimos tecnología, inteligencia artificial y finanzas con asistencia de IA y revisión editorial humana.',
  alternates: {
    canonical: 'https://www.newstide.news/sobre-nosotros',
    languages: {
      'es': 'https://www.newstide.news/sobre-nosotros',
      'en': 'https://www.newstide.news/en/about',
      'x-default': 'https://www.newstide.news/en/about',
    },
  },
  openGraph: {
    title: 'Sobre NewsTide',
    description: 'Quiénes somos y cómo creamos contenido de tecnología e IA.',
    url: 'https://www.newstide.news/sobre-nosotros',
    siteName: 'NewsTide',
    locale: 'es_ES',
    type: 'website',
  },
}

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'AboutPage',
  name: 'Sobre NewsTide',
  url: 'https://www.newstide.news/sobre-nosotros',
  description: 'NewsTide es una publicación digital especializada en tecnología, inteligencia artificial y finanzas.',
  publisher: {
    '@type': 'NewsMediaOrganization',
    name: 'NewsTide',
    url: 'https://www.newstide.news',
    logo: {
      '@type': 'ImageObject',
      url: 'https://www.newstide.news/favicon-192x192.png',
    },
    sameAs: [
      'https://twitter.com/newstide',
      'https://www.linkedin.com/company/newstide',
    ],
  },
}

export default function SobreNosotros() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Inicio</Link>
        </div>

        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>Sobre NewsTide</h1>
        <p style={{ fontSize: 18, color: 'var(--muted)', lineHeight: 1.7, marginBottom: 48 }}>
          Tecnología, IA y finanzas para los que van por delante.
        </p>

        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>¿Qué es NewsTide?</h2>
          <p>
            NewsTide es una publicación digital especializada en cubrir las últimas noticias, análisis y tendencias sobre
            inteligencia artificial, herramientas tecnológicas, startups y finanzas. Nuestro objetivo es ofrecer
            información precisa, actual y relevante para founders, desarrolladores, inversores y profesionales digitales.
          </p>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>Cómo creamos nuestro contenido</h2>
          <p>
            NewsTide combina tecnología de inteligencia artificial de última generación con supervisión editorial humana.
            Todos los artículos son generados con asistencia de IA a partir de fuentes primarias verificadas y
            posteriormente revisados por nuestro equipo editorial para garantizar su precisión, contexto y valor
            informativo. Esta metodología nos permite publicar contenido de calidad con una frecuencia que ninguna
            redacción tradicional podría mantener.
          </p>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>Nuestros pilares temáticos</h2>
          <ul style={{ margin: '0 0 20px 24px' }}>
            <li style={{ marginBottom: 10 }}><strong>Inteligencia Artificial y modelos:</strong> seguimiento de los últimos modelos, herramientas y tendencias en IA.</li>
            <li style={{ marginBottom: 10 }}><strong>Herramientas para developers:</strong> análisis y comparativas de las mejores herramientas de desarrollo, productividad y automatización.</li>
            <li style={{ marginBottom: 10 }}><strong>Finanzas y mercados:</strong> noticias de mercados financieros, criptomonedas, estrategias de inversión y economía digital.</li>
            <li style={{ marginBottom: 10 }}><strong>Startups y empresa:</strong> ecosistema emprendedor, rondas de financiación y casos de éxito.</li>
          </ul>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>Transparencia editorial</h2>
          <p>
            Creemos firmemente en la transparencia. Siempre indicamos cuando un artículo ha sido generado con asistencia
            de IA y enlazamos a las fuentes primarias utilizadas. Si detectas un error o tienes alguna duda sobre un
            artículo, puedes contactarnos y nos comprometemos a revisar y corregir cualquier inexactitud.
          </p>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/politica-editorial" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Política editorial →</Link>
            <Link href="/contacto" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contacto →</Link>
            <Link href="/en/about" style={{ color: 'var(--muted)', fontWeight: 600, fontSize: 14 }}>Read in English →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
