import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function POST(req: NextRequest) {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  )

  try {
    const body = await req.json().catch(() => null)
    if (!body?.email) {
      return NextResponse.json({ error: 'Email requerido' }, { status: 400 })
    }

    const email = body.email.toLowerCase().trim()
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.json({ error: 'Email inválido' }, { status: 400 })
    }

    const { error } = await supabase
      .from('newsletter_subscribers')
      .upsert(
        { email, subscribed_at: new Date().toISOString(), active: true },
        { onConflict: 'email', ignoreDuplicates: true }
      )

    if (error) {
      console.error('[newsletter/subscribe] Supabase error:', error.message, error.code)
      // Table missing — give a clear hint in server logs
      if (error.code === '42P01') {
        console.error('[newsletter/subscribe] Table newsletter_subscribers does not exist. Run the SQL setup script.')
      }
      return NextResponse.json({ error: 'Error interno' }, { status: 500 })
    }

    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error('[newsletter/subscribe] Unexpected error:', err)
    return NextResponse.json({ error: 'Error interno' }, { status: 500 })
  }
}
