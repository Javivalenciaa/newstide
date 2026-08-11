import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function POST(req: NextRequest) {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const serviceKey =
    process.env.SUPABASE_SERVICE_ROLE_KEY ||
    process.env.SUPABASE_SERVICE_KEY ||
    ''

  if (!supabaseUrl || !serviceKey) {
    console.error(
      '[newsletter] Missing env vars. NEXT_PUBLIC_SUPABASE_URL:',
      !!supabaseUrl,
      '| service key present:',
      !!serviceKey
    )
    return NextResponse.json({ error: 'Server misconfiguration' }, { status: 500 })
  }

  const supabase = createClient(supabaseUrl, serviceKey)

  try {
    const body = await req.json().catch(() => null)
    if (!body?.email) {
      return NextResponse.json({ error: 'Email required' }, { status: 400 })
    }

    const email = body.email.toLowerCase().trim()
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.json({ error: 'Invalid email' }, { status: 400 })
    }

    // Table columns: id (uuid), email (text unique), created_at (timestamptz), confirmed (boolean)
    // ignoreDuplicates: true — silently succeeds if email already subscribed
    const { error } = await supabase
      .from('newsletter_subscribers')
      .upsert(
        { email, confirmed: false },
        { onConflict: 'email', ignoreDuplicates: true }
      )

    if (error) {
      console.error('[newsletter] Supabase error:', error.message, '| code:', error.code)
      if (error.code === '42P01') {
        return NextResponse.json({ error: 'Service unavailable' }, { status: 503 })
      }
      return NextResponse.json({ error: 'Internal error' }, { status: 500 })
    }

    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error('[newsletter] Unexpected error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}
