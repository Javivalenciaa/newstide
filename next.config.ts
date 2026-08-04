import type { NextConfig } from 'next'

// A4: dominios de scripts confirmados leyendo app/layout.tsx:
//   - www.googletagmanager.com  → GA4 script src
//   - pagead2.googlesyndication.com → AdSense script src
//   - www.google-analytics.com  → GA4 beacon endpoint
//   - googleads.g.doubleclick.net, tpc.googlesyndication.com → AdSense frames/requests
//   - adservice.google.com → AdSense ad serving
// Imágenes CDN confirmadas en next.config images.remotePatterns:
//   - images.unsplash.com
// Supabase storage confirmado en lib/supabase.ts (NEXT_PUBLIC_SUPABASE_URL = *.supabase.co)
const CSP = [
  `default-src 'self'`,
  // Scripts: propio + GTM/GA4 + AdSense (necesitan eval para sus workers internos)
  `script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://pagead2.googlesyndication.com https://www.google-analytics.com https://googleads.g.doubleclick.net https://tpc.googlesyndication.com https://adservice.google.com`,
  // Estilos: unsafe-inline requerido por Next.js (inline styles en componentes)
  `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com`,
  // Fuentes Google Fonts
  `font-src 'self' https://fonts.gstatic.com`,
  // Imágenes: self, data URIs, Supabase storage, Unsplash, dominios de tracking de anuncios
  `img-src 'self' data: blob: https://*.supabase.co https://images.unsplash.com https://www.google-analytics.com https://www.googletagmanager.com https://googleads.g.doubleclick.net https://pagead2.googlesyndication.com https://tpc.googlesyndication.com`,
  // Conexiones: Supabase API, GA4, GTM
  `connect-src 'self' https://*.supabase.co https://www.google-analytics.com https://analytics.google.com https://www.googletagmanager.com https://googleads.g.doubleclick.net https://pagead2.googlesyndication.com`,
  // Frames: AdSense iframes in-article
  `frame-src https://googleads.g.doubleclick.net https://tpc.googlesyndication.com https://www.google.com`,
  // Workers: AdSense usa service workers
  `worker-src 'self' blob:`,
  `object-src 'none'`,
  `base-uri 'self'`,
  `form-action 'self'`,
  `upgrade-insecure-requests`,
].join('; ')

const nextConfig: NextConfig = {
  compress: true,

  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'images.unsplash.com' },
      { protocol: 'https', hostname: '*.supabase.co' },
    ],
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 31536000,
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256],
  },

  async headers() {
    return [
      {
        // Cache JS/CSS bundles — immutable porque los nombres están hasheados
        source: '/_next/static/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
      {
        source: '/_next/image',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
      { source: '/:file*.ico',  headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }] },
      { source: '/:file*.png',  headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }] },
      { source: '/:file*.jpg',  headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }] },
      { source: '/:file*.jpeg', headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }] },
      { source: '/:file*.svg',  headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }] },
      { source: '/:file*.webp', headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }] },
      { source: '/:file*.woff2',headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }] },
      { source: '/:file*.woff', headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }] },
      {
        // A3: páginas HTML — s-maxage alineado con revalidate=86400 de artículos individuales.
        // Los listados usan revalidate=3600 pero no perjudica servirlos desde CDN hasta 24h
        // (stale-while-revalidate los mantiene frescos en background).
        source: '/(.*)',
        headers: [
          // A3: 300→86400 para alinear CDN cache con el nuevo revalidate de artículos
          { key: 'Cache-Control', value: 'public, s-maxage=86400, stale-while-revalidate=59' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
          // A4: Content-Security-Policy añadida
          { key: 'Content-Security-Policy', value: CSP },
        ],
      },
    ]
  },

  async redirects() {
    return [
      { source: '/noticias/:categoria/:slug', destination: '/', permanent: true },
      { source: '/noticias/:categoria', destination: '/', permanent: true },
      { source: '/noticias', destination: '/', permanent: true },
    ]
  },
}

export default nextConfig
