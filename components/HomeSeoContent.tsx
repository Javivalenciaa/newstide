import Link from 'next/link'

// Bloque editorial para la home en español.
// Resuelve: pocas palabras útiles, palabras del H1/title no reutilizadas,
// pocos enlaces internos variados, cero enlaces externos.
// Importar en app/page.tsx: <HomeSeoContent /> antes del footer.
export default function HomeSeoContent() {
  return (
    <section
      aria-labelledby="sobre-newstide"
      style={{ padding: '64px 24px', maxWidth: 860, margin: '0 auto' }}
    >
      <h2 id="sobre-newstide" style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 20, letterSpacing: '-0.02em' }}>
        NewsTide: la inteligencia que transforma el futuro de la información
      </h2>

      <p style={{ fontSize: 17, lineHeight: 1.8, marginBottom: 20, color: 'rgba(240,240,238,0.85)' }}>
        NewsTide nació con una idea simple: la inteligencia artificial está transformando el futuro
        de cómo founders, developers y profesionales se informan, y alguien tenía que cubrir ese
        cambio con rigor en español. Cada semana publicamos artículos de fondo sobre IA, startups
        tecnológicas y las herramientas que están redefiniendo cómo se construyen productos digitales
        en 2026. No hacemos titulares vacíos: cada pieza que ves en{' '}
        <Link href="/articulos" style={{ color: 'var(--cyan)' }}>nuestro archivo de artículos</Link>{' '}
        pasa por un proceso editorial que combina asistencia de inteligencia artificial con revisión
        humana, siguiendo los criterios que detallamos en nuestra{' '}
        <Link href="/politica-editorial" style={{ color: 'var(--cyan)' }}>política editorial</Link>.
      </p>

      <p style={{ fontSize: 17, lineHeight: 1.8, marginBottom: 20, color: 'rgba(240,240,238,0.85)' }}>
        Además de tecnología, cubrimos un ángulo que muchos medios generalistas ignoran: las{' '}
        <Link href="/fin" style={{ color: 'var(--cyan)' }}>finanzas personales para hispanos en Estados Unidos</Link>,
        desde cómo abrir una cuenta bancaria sin historial de crédito hasta cómo declarar impuestos
        siendo inmigrante. Esta sección financiera crece a diario y complementa nuestra cobertura
        de inteligencia artificial con contenido práctico que la gente necesita para tomar mejores
        decisiones con su dinero.
      </p>

      <p style={{ fontSize: 17, lineHeight: 1.8, marginBottom: 20, color: 'rgba(240,240,238,0.85)' }}>
        Nuestro equipo sigue de cerca a las principales fuentes del sector — desde los anuncios
        oficiales de{' '}
        <a href="https://openai.com/blog" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>OpenAI</a>{' '}
        y{' '}
        <a href="https://www.anthropic.com/news" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>Anthropic</a>{' '}
        hasta los movimientos de mercado que afectan a startups y grandes tecnológicas — para
        traduÍrtelo en análisis claros, sin relleno. Puedes conocer al equipo detrás de estas
        publicaciones en la sección de{' '}
        <Link href="/autores" style={{ color: 'var(--cyan)' }}>autores</Link>, o suscribirte a nuestra
        newsletter para recibir lo más relevante de la semana directamente en tu correo.
      </p>

      <p style={{ fontSize: 17, lineHeight: 1.8, color: 'rgba(240,240,238,0.85)' }}>
        Si buscas entender cómo la inteligencia artificial está transformando el futuro del trabajo,
        la inversión o la creación de productos, NewsTide es tu punto de partida en español. Explora
        nuestras categorías, comparativas de herramientas y guías financieras, y vuelve cada día:
        publicamos contenido nuevo constantemente para mantenerte al día sin que tengas que
        buscarlo tu mismo entre decenas de fuentes distintas.
      </p>
    </section>
  )
}
