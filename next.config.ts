import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Compress all responses
  compress: true,

  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'images.unsplash.com' },
    ],
    // Modern formats — WebP/AVIF reduce image size 30-50%
    formats: ['image/avif', 'image/webp'],
    // Aggressive browser cache for images
    minimumCacheTTL: 31536000,
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256],
  },

  async headers() {
    return [
      {
        // Cache static assets aggressively (fonts, icons, images)
        source: '/_next/static/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
      {
        // Cache public assets (favicon, og-image, etc.)
        source: '/:path((?!api|_next).*\\.(ico|png|jpg|jpeg|svg|webp|avif|woff|woff2|ttf|otf))',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
      {
        // HTML pages — stale-while-revalidate so they're always fast
        source: '/(.*)',
        headers: [
          { key: 'Cache-Control', value: 'public, s-maxage=300, stale-while-revalidate=600' },
          // Security headers (bonus SEO trust signals)
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
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
