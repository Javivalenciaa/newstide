import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function POST(req: NextRequest) {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  )

  try {
    const { email } = await req.json()

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.json({ error: 'Email inválido' }, { status: 400 })
    }

    const { error } = await supabase
      .from('newsletter_subscribers')
      .upsert({ email: email.toLowerCase().trim() }, { onConflict: 'email', ignoreDuplicates: true })

    if (error) throw error

    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error('[newsletter]', err)
    return NextResponse.json({ error: 'Error interno' }, { status: 500 })
  }
}
