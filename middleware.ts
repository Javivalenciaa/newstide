import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * FIX C1: Propagate the request pathname as a custom header so that
 * the root Server Component (app/layout.tsx) can read it via
 * next/headers and set the correct <html lang> attribute:
 *   /en/* → lang="en"
 *   everything else → lang="es"
 */
export function middleware(request: NextRequest) {
  const response = NextResponse.next()
  response.headers.set('x-pathname', request.nextUrl.pathname)
  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT:
     * - _next/static  (static files)
     * - _next/image   (image optimisation)
     * - favicon.ico, robots.txt, sitemap.xml, etc.
     */
    '/((?!_next/static|_next/image|favicon|robots|sitemap|news-sitemap|rss|.*\.(?:png|jpg|jpeg|gif|webp|svg|ico|css|js|woff2?|ttf|otf)).*)',
  ],
}
