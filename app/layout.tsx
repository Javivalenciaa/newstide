import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import Link from 'next/link'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: 'NewsTide — La inteligencia que transforma el futuro',
  description: 'Tecnología, IA y tendencias para founders, developers y profesionales.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${inter.variable} ${mono.variable}`}>
      <body>
        <nav id="navbar">
          <Link href="/" className="nav-logo">
            <div className="nav-logo-mark">NT</div>
            NewsTide
          </Link>
          <div className="nav-links">
            <Link href="/">Inicio</Link>
            <Link href="/#articles">Artículos</Link>
            <Link href="/#newsletter">Newsletter</Link>
          </div>
          <div className="nav-right">
            <Link href="/#newsletter" className="nav-cta">Suscribirse</Link>
          </div>
        </nav>
        {children}
        <footer>
          <div className="container">
            <div className="footer-top">
              <div className="footer-brand">
                <Link href="/" className="nav-logo" style={{marginBottom:'12px'}}>
                  <div className="nav-logo-mark">NT</div>NewsTide
                </Link>
                <p className="footer-tagline">Tecnología, IA y tendencias<br/>para los que van por delante.</p>
              </div>
              <div className="footer-links">
                <div className="footer-col">
                  <div className="footer-col-title">Categorías</div>
                  <Link href="/">IA & Modelos</Link>
                  <Link href="/">Startups</Link>
                  <Link href="/">Herramientas</Link>
                  <Link href="/">Tutoriales</Link>
                </div>
                <div className="footer-col">
                  <div className="footer-col-title">Empresa</div>
                  <Link href="/sobre-nosotros">Sobre nosotros</Link>
                  <Link href="/contacto">Contacto</Link>
                  <Link href="/privacidad">Privacidad</Link>
                </div>
              </div>
            </div>
            <div className="footer-bottom">
              <span>© 2026 NewsTide · Todos los derechos reservados</span>
              <span style={{color:'var(--faint)'}}>newstide.news</span>
            </div>
          </div>
        </footer>
        <script dangerouslySetInnerHTML={{__html: `
          const nav = document.getElementById('navbar');
          window.addEventListener('scroll', () => nav.classList.toggle('scrolled', window.scrollY > 20), {passive:true});
        `}}/>
      </body>
    </html>
  )
}
