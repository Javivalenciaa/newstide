import { NextRequest, NextResponse } from 'next/server'

const KEY = process.env.INDEXNOW_KEY ?? '449864d8a7154e33b47bcd42fc5b899a'
const HOST = 'www.newstide.news'
const KEY_LOCATION = `https://${HOST}/${KEY}.txt`

export async function POST(req: NextRequest) {
  try {
    const { urls } = await req.json()

    if (!urls || !Array.isArray(urls) || urls.length === 0) {
      return NextResponse.json({ error: 'urls array required' }, { status: 400 })
    }

    const body = {
      host: HOST,
      key: KEY,
      keyLocation: KEY_LOCATION,
      urlList: urls,
    }

    const res = await fetch('https://api.indexnow.org/IndexNow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify(body),
    })

    if (res.ok) {
      return NextResponse.json({ success: true, submitted: urls.length })
    } else {
      const text = await res.text()
      return NextResponse.json({ error: text, status: res.status }, { status: 502 })
    }
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500 })
  }
}

// GET: serve the key file inline (fallback, el .txt en /public es suficiente)
export async function GET() {
  return new Response(KEY, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  })
}
