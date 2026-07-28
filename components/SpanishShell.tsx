'use client'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import LangSwitcher from '@/components/LangSwitcher'
import MobileNav from '@/components/MobileNav'

export default function SpanishShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isEnglish = pathname.startsWith('/en')

  if (isEnglish) return <>{children}</>

  return (
    <>
      <nav id="navbar">
        <Link href="/" className="nav-logo">
          <div className="nav-logo-mark">NT</div>
          NewsTide
        </Link>
        <div className="nav-links">
          <Link href="/">Inicio</Link>
          <Link href="/articulos">Artículos</Link>
          <Link href="/#newsletter">Newsletter</Link>
        </div>
        <div className="nav-right" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <LangSwitcher />
          <Link href="/#newsletter" className="nav-cta">Suscribirse</Link>
          <MobileNav lang="es" />
        </div>
      </nav>
      {children}
      <footer>
        <div className="container">
          <div className="footer-top">
            <div className="footer-brand">
              <Link href="/" className="nav-logo" style={{ marginBottom: '12px' }}>
                <div className="nav-logo-mark">NT</div>NewsTide
              </Link>
              <p className="footer-tagline">Tecnología, IA y tendencias<br />para los que van por delante.</p>
            </div>
            <div className="footer-links">
              <div className="footer-col">
                <div className="footer-col-title">Categorías</div>
                <Link href="/articulos/ia">IA &amp; Modelos</Link>
                <Link href="/articulos/startups">Startups</Link>
                <Link href="/articulos/herramientas">Herramientas</Link>
                <Link href="/articulos/tutoriales">Tutoriales</Link>
                <Link href="/articulos/noticias">Noticias</Link>
              </div>
              <div className="footer-col">
                <div className="footer-col-title">Empresa</div>
                <Link href="/sobre-nosotros">Sobre nosotros</Link>
                <Link href="/politica-editorial">Política editorial</Link>
                <Link href="/autores/javier-valencia">Javier Valencia</Link>
                <Link href="/contacto">Contacto</Link>
                <Link href="/privacidad">Privacidad</Link>
              </div>
              <div className="footer-col">
                <div className="footer-col-title">Feeds</div>
                <Link href="/rss.xml">RSS Feed</Link>
                <Link href="/en/rss.xml">RSS English</Link>
                <Link href="/news-sitemap.xml">News Sitemap</Link>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <span>© 2026 NewsTide · Todos los derechos reservados</span>
            <span style={{ color: 'var(--faint)' }}>newstide.news</span>
          </div>
          <div style={{ textAlign: 'center', marginTop: '12px', fontSize: '12px', opacity: 0.5 }}>
            <a href="http://www.blogarama.com/fashion-blogs/1351624-blog/" title="Blogarama.com - Follow me on Blogarama">Blogarama - Blog Directory</a>
          </div>
        </div>
      </footer>
      <script dangerouslySetInnerHTML={{ __html: `
        const nav = document.getElementById('navbar');
        if(nav) window.addEventListener('scroll', () => nav.classList.toggle('scrolled', window.scrollY > 20), {passive:true});
      ` }} />
    </>
  )
}
