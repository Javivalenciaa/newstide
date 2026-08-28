import { NextRequest, NextResponse } from 'next/server'
import { revalidatePath, revalidateTag } from 'next/cache'
import { pingIndexNow } from '@/lib/indexnow'

// Optional: protect the webhook with a secret token.
// Set PUBLISH_HOOK_SECRET in Vercel env vars (any random string).
// Your pipeline must send: Authorization: Bearer <secret>
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
    // 1. Direct:           { slug, slug_en, category }
    // 2. Supabase webhook: { record: { slug, slug_en, category } }
    const record = body.record ?? body
    const { slug, slug_en, category } = record

    if (!slug) {
      return NextResponse.json({ error: 'slug required' }, { status: 400 })
    }

    // ── 1. IndexNow ping (Bing + others) ──────────────────────────────────
    const urls: string[] = [`https://www.newstide.news/articulo/${slug}`]
    if (slug_en) urls.push(`https://www.newstide.news/en/article/${slug_en}`)
    await pingIndexNow(urls)

    // ── 2. On-demand ISR revalidation ─────────────────────────────────────
    // Revalidate the new article pages immediately so they are live
    revalidatePath(`/articulo/${slug}`)
    if (slug_en) revalidatePath(`/en/article/${slug_en}`)

    // Revalidate listing pages so the new article appears in index/category
    revalidatePath('/')
    revalidatePath('/en')

    // Revalidate category pages for both languages (normalise to lowercase slug)
    if (category) {
      const CAT_SLUG_ES: Record<string, string> = {
        'IA': 'ia', 'Tutoriales': 'tutoriales',
        'Herramientas': 'herramientas', 'Startups': 'startups', 'Noticias': 'noticias',
      }
      const CAT_SLUG_EN: Record<string, string> = {
        'IA': 'ai', 'Tutoriales': 'tutorials',
        'Herramientas': 'tools', 'Startups': 'startups', 'Noticias': 'news',
      }
      const catSlugES = CAT_SLUG_ES[category] || category.toLowerCase()
      const catSlugEN = CAT_SLUG_EN[category] || category.toLowerCase()
      revalidatePath(`/articulos/${catSlugES}`)
      revalidatePath(`/en/articles/${catSlugEN}`)
    }

    // Revalidate sitemap and feeds so Google finds the article in < 5 min
    // (news-sitemap is force-dynamic so this is a belt-and-suspenders measure)
    // Next.js 16 requires a second argument for revalidateTag.
    // expire:0 = immediate eviction; this is a webhook (not a Server Action),
    // so updateTag() would be semantically wrong here.
    revalidateTag('sitemap', { expire: 0 })

    console.log('[publish-hook] IndexNow pinged + ISR revalidated for:', urls)
    return NextResponse.json({ success: true, pinged: urls })
  } catch (err) {
    console.error('[publish-hook] error:', err)
    return NextResponse.json({ error: String(err) }, { status: 500 })
  }
}
