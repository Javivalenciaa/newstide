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
  '@graph': [
    {
      '@type': 'AboutPage',
      '@id': 'https://www.newstide.news/sobre-nosotros#webpage',
      name: 'Sobre NewsTide',
      url: 'https://www.newstide.news/sobre-nosotros',
      description: 'NewsTide es una publicación digital especializada en tecnología, inteligencia artificial y finanzas.',
      isPartOf: { '@id': 'https://www.newstide.news/#website' },
    },
    {
      '@type': 'Person',
      '@id': 'https://www.newstide.news/en/authors/javier-valencia',
      name: 'Javier Valencia',
      url: 'https://www.newstide.news/en/authors/javier-valencia',
      jobTitle: 'Fundador y Editor',
      description:
        'Estudiante de Ingeniería Informática y Administración de Empresas con experiencia en desarrollo de software, startups, gemelos digitales, y programas de innovación de IBM y Techstars.',
      knowsAbout: [
        'Inteligencia Artificial',
        'Desarrollo de Software',
        'Startups',
        'Next.js',
        'Python',
        'Supabase',
        'Gemelos Digitales',
      ],
      alumniOf: [
        { '@type': 'Organization', name: 'IBM' },
        { '@type': 'Organization', name: 'Techstars' },
      ],
    },
    {
      '@type': 'NewsMediaOrganization',
      '@id': 'https://www.newstide.news/#organization',
      name: 'NewsTide',
      url: 'https://www.newstide.news',
      foundingDate: '2024',
      founder: { '@id': 'https://www.newstide.news/en/authors/javier-valencia' },
      logo: {
        '@type': 'ImageObject',
        url: 'https://www.newstide.news/favicon-192x192.png',
        width: 192,
        height: 192,
      },
      masthead: 'https://www.newstide.news/sobre-nosotros',
      publishingPrinciples: 'https://www.newstide.news/en/editorial-policy',
      correctionsPolicy: 'https://www.newstide.news/en/editorial-policy#corrections',
      sameAs: [
        'https://twitter.com/newstide',
        'https://www.linkedin.com/company/newstide',
      ],
    },
  ],
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
            NewsTide es una publicación digital especializada en cubrir noticias, análisis y tendencias sobre
            inteligencia artificial, herramientas para desarrolladores, startups y finanzas. Fundada en 2024,
            nuestro objetivo es ofrecer información precisa, actualizada y bien documentada para founders,
            desarrolladores, inversores y profesionales digitales.
          </p>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>El equipo</h2>
          <p>
            NewsTide fue fundado por{' '}
            <Link href="/en/authors/javier-valencia" style={{ color: 'var(--cyan)' }}>Javier Valencia</Link>,
            estudiante de Ingeniería Informática y Administración de Empresas. Javier acumula experiencia práctica
            como freelancer en desarrollo de webs y software a medida, ha participado en programas de innovación
            y startups de organizaciones como{' '}<strong>IBM</strong> y{' '}<strong>Techstars</strong>, y ha
            competido en concursos de programación e innovación empresarial. Entre sus proyectos técnicos destacan
            el desarrollo de gemelos digitales, sistemas de automatización con IA y plataformas de contenido
            propias como NewsTide.
          </p>
          <p style={{ marginTop: 16 }}>
            Javier supervisa la dirección editorial, la infraestructura técnica y el control de calidad de
            cada artículo publicado en la plataforma.
          </p>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>Cómo creamos el contenido</h2>
          <p>
            NewsTide combina modelos de lenguaje de última generación con supervisión editorial humana.
            Todos los artículos se generan con asistencia de IA a partir de fuentes primarias verificadas —
            comunicados oficiales, documentos corporativos, investigación académica y declaraciones directas
            de las personas y organizaciones cubiertas — y son revisados posteriormente para garantizar
            precisión, contexto y valor informativo.
          </p>
          <p style={{ marginTop: 16 }}>
            Cada artículo muestra la fecha de publicación y la última modificación, y enlaza a las fuentes
            primarias utilizadas. Si detectas un error, escríbenos a{' '}
            <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a>{' '}
            y nos comprometemos a revisar y corregir cualquier inexactitud en un plazo de 48 horas.
          </p>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>Nuestros pilares temáticos</h2>
          <ul style={{ margin: '0 0 20px 24px' }}>
            <li style={{ marginBottom: 10 }}><strong>Inteligencia Artificial y modelos:</strong> seguimiento de los últimos modelos, herramientas y tendencias en IA y sus implicaciones reales.</li>
            <li style={{ marginBottom: 10 }}><strong>Herramientas para developers:</strong> análisis y comparativas de las mejores herramientas de desarrollo, productividad y automatización, escritas por alguien que las usa.</li>
            <li style={{ marginBottom: 10 }}><strong>Finanzas y mercados:</strong> mercados financieros, criptomonedas, venture capital y economía digital, explicados sin jerga innecesaria.</li>
            <li style={{ marginBottom: 10 }}><strong>Startups y empresa:</strong> ecosistema emprendedor, rondas de financiación, lanzamientos de producto y casos de éxito.</li>
          </ul>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>Transparencia editorial</h2>
          <p>
            Creemos en la transparencia total sobre cómo opera esta publicación. NewsTide etiqueta
            claramente el contenido asistido por IA, enlaza directamente a las fuentes primarias y mantiene
            una política de correcciones pública. Nuestros estándares completos están detallados en nuestra{' '}
            <Link href="/politica-editorial" style={{ color: 'var(--cyan)' }}>Política Editorial</Link>.
          </p>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/politica-editorial" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Política editorial →</Link>
            <Link href="/contacto" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contacto →</Link>
            <Link href="/en/authors/javier-valencia" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Conoce al editor →</Link>
            <Link href="/en/about" style={{ color: 'var(--muted)', fontWeight: 600, fontSize: 14 }}>Read in English →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
