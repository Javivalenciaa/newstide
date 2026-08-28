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

    // Check if already subscribed to avoid sending duplicate welcome emails
    const { data: existing } = await supabase
      .from('newsletter_subscribers')
      .select('email')
      .eq('email', email)
      .maybeSingle()

    // Table columns: id (uuid), email (text unique), created_at (timestamptz), confirmed (boolean)
    const { error: dbError } = await supabase
      .from('newsletter_subscribers')
      .upsert(
        { email, confirmed: false },
        { onConflict: 'email', ignoreDuplicates: true }
      )

    if (dbError) {
      console.error('[newsletter] Supabase error:', dbError.message, '| code:', dbError.code)
      if (dbError.code === '42P01') {
        return NextResponse.json({ error: 'Service unavailable' }, { status: 503 })
      }
      return NextResponse.json({ error: 'Internal error' }, { status: 500 })
    }

    // Send welcome email only for new subscribers
    if (!existing) {
      const resendKey = process.env.RESEND_API_KEY
      if (resendKey) {
        const welcomeHtml = `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
        <tr>
          <td style="background:linear-gradient(135deg,#0d1a2e,#0d2a2e);border-radius:14px 14px 0 0;padding:32px 40px 28px;border-bottom:1px solid #1e3a3a;">
            <a href="https://www.newstide.news/en" style="font-size:22px;font-weight:800;color:#6ecfca;text-decoration:none;letter-spacing:-0.03em;">NewsTide</a>
            <p style="margin:6px 0 0;font-size:13px;color:#6ecfca;opacity:0.7;">AI, Startups &amp; Tech News</p>
          </td>
        </tr>
        <tr>
          <td style="background:#0f1923;padding:36px 40px 28px;">
            <h1 style="margin:0 0 16px;font-size:22px;font-weight:700;color:#f0f0f0;line-height:1.3;">Welcome to NewsTide! 🚀</h1>
            <p style="margin:0 0 16px;font-size:15px;color:#c0c0c0;line-height:1.7;">
              You're in. Every Friday morning you'll get the most important stories in AI, startups and tech — curated and ready to read in 5 minutes.
            </p>
            <p style="margin:0 0 28px;font-size:15px;color:#c0c0c0;line-height:1.7;">
              While you wait for the first issue, catch up on the latest articles:
            </p>
            <a href="https://www.newstide.news/en/articles"
               style="display:inline-block;background:#6ecfca;color:#0a0a0f;font-size:14px;font-weight:700;padding:12px 28px;border-radius:8px;text-decoration:none;letter-spacing:0.01em;">
              Browse articles &rarr;
            </a>
          </td>
        </tr>
        <tr>
          <td style="background:#0a0a0f;border-radius:0 0 14px 14px;padding:24px 40px;border-top:1px solid #1a2a2a;">
            <p style="margin:0 0 8px;font-size:12px;color:#555;line-height:1.6;">
              You subscribed at <a href="https://www.newstide.news" style="color:#6ecfca;text-decoration:none;">newstide.news</a>.
            </p>
            <p style="margin:0;font-size:12px;color:#555;">
              <a href="https://www.newstide.news/unsubscribe?email=${encodeURIComponent(email)}" style="color:#555;">Unsubscribe</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`

        const resendRes = await fetch('https://api.resend.com/emails', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${resendKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            from: 'NewsTide <newsletter@newstide.news>',
            to: [email],
            subject: 'Welcome to NewsTide 👋',
            html: welcomeHtml,
          }),
        })

        if (!resendRes.ok) {
          const resendErr = await resendRes.json()
          console.error('[newsletter] Resend welcome email failed:', resendErr)
          // Don't return error — subscription was saved, email failure is non-critical
        }
      } else {
        console.warn('[newsletter] RESEND_API_KEY not set, skipping welcome email')
      }
    }

    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error('[newsletter] Unexpected error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}
