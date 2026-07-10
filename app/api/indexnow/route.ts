import { NextRequest, NextResponse } from 'next/server'

// Call this endpoint after publishing a new article to notify Bing instantly
// POST /api/indexnow  body: { urls: string[] }
// Also callable with a single url: { url: string }
export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => null)
    if (!body) return NextResponse.json({ error: 'Invalid body' }, { status: 400 })

    const key = '8be78df6f0af4417832b40b1192ffc0d'
    const host = 'www.newstide.news'
    const keyLocation = `https://${host}/${key}.txt`

    const urlList: string[] = body.urls ?? (body.url ? [body.url] : [])
    if (urlList.length === 0) {
      return NextResponse.json({ error: 'No URLs provided' }, { status: 400 })
    }

    const payload = {
      host,
      key,
      keyLocation,
      urlList,
    }

    const res = await fetch('https://api.indexnow.org/indexnow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify(payload),
    })

    console.log('[indexnow] Bing response:', res.status)
    return NextResponse.json({ ok: true, status: res.status, urls: urlList })
  } catch (err) {
    console.error('[indexnow] Error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}
