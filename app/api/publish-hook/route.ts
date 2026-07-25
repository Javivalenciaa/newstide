import { NextRequest, NextResponse } from 'next/server'
import { pingIndexNow } from '@/lib/indexnow'

// Optional: protect the webhook with a secret token
// Set PUBLISH_HOOK_SECRET in Vercel env vars (any random string)
// Your script must send: Authorization: Bearer <secret>
const SECRET = process.env.PUBLISH_HOOK_SECRET

export async function POST(req: NextRequest) {
  // Auth check (skip if no secret configured)
  if (SECRET) {
    const auth = req.headers.get('authorization') ?? ''
    if (auth !== `Bearer ${SECRET}`) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
  }

  try {
    const body = await req.json()

    // Accepts two formats:
    // 1. Direct: { slug: 'mi-articulo', slug_en: 'my-article' }
    // 2. Supabase webhook: { record: { slug, slug_en } }
    const record = body.record ?? body
    const { slug, slug_en } = record

    if (!slug) {
      return NextResponse.json({ error: 'slug required' }, { status: 400 })
    }

    const urls: string[] = []
    urls.push(`https://www.newstide.news/articulo/${slug}`)
    if (slug_en) urls.push(`https://www.newstide.news/en/article/${slug_en}`)

    await pingIndexNow(urls)

    console.log('[publish-hook] IndexNow pinged for:', urls)
    return NextResponse.json({ success: true, pinged: urls })
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500 })
  }
}
