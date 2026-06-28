import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
    ],
  },
  async redirects() {
    return [
      {
        source: '/noticias/:categoria/:slug',
        destination: '/',
        permanent: true,
      },
      {
        source: '/noticias/:categoria',
        destination: '/',
        permanent: true,
      },
      {
        source: '/noticias',
        destination: '/',
        permanent: true,
      },
    ]
  },
}

export default nextConfig
