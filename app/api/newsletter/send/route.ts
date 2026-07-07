import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Called every Friday at 09:00 UTC by Vercel Cron (see vercel.json)
// Also callable manually: GET /api/newsletter/send?secret=CRON_SECRET
export const runtime = 'nodejs'
export const maxDuration = 60

function buildEmailHtml(articles: Article[]): string {
  const articleRows = articles
    .map(
      (a) => `
      <tr>
        <td style="padding:0 0 28px 0;">
          <a href="https://www.newstide.news/en/article/${a.slug_en || a.slug}"
             style="font-size:17px;font-weight:700;color:#6ecfca;text-decoration:none;line-height:1.35;"
          >${a.title_en || a.title}</a>
          <p style="margin:6px 0 10px;font-size:14px;color:#a0a0a0;line-height:1.6;">
            ${a.excerpt_en || a.excerpt || ''}
          </p>
          <a href="https://www.newstide.news/en/article/${a.slug_en || a.slug}"
             style="font-size:13px;color:#6ecfca;text-decoration:none;font-weight:600;"
          >Read article →</a>
        </td>
      </tr>`
    )
    .join('')

  return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

        <!-- HEADER -->
        <tr>
          <td style="background:linear-gradient(135deg,#0d1a2e,#0d2a2e);border-radius:14px 14px 0 0;padding:32px 40px 28px;border-bottom:1px solid #1e3a3a;">
            <a href="https://www.newstide.news/en" style="font-size:22px;font-weight:800;color:#6ecfca;text-decoration:none;letter-spacing:-0.03em;">NewsTide</a>
            <p style="margin:6px 0 0;font-size:13px;color:#6ecfca;opacity:0.7;">Your weekly AI &amp; Tech digest</p>
          </td>
        </tr>

        <!-- INTRO -->
        <tr>
          <td style="background:#0f1923;padding:28px 40px 8px;">
            <p style="margin:0;font-size:15px;color:#c0c0c0;line-height:1.7;">
              Happy Friday! Here are the stories worth your attention this week.
            </p>
          </td>
        </tr>

        <!-- ARTICLES -->
        <tr>
          <td style="background:#0f1923;padding:16px 40px 8px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              ${articleRows}
            </table>
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="background:#0a0a0f;border-radius:0 0 14px 14px;padding:24px 40px;border-top:1px solid #1a2a2a;">
            <p style="margin:0 0 8px;font-size:12px;color:#555;line-height:1.6;">
              You’re receiving this because you subscribed at
              <a href="https://www.newstide.news" style="color:#6ecfca;text-decoration:none;">newstide.news</a>.
            </p>
            <p style="margin:0;font-size:12px;color:#555;">
              <a href="https://www.newstide.news/unsubscribe?email={{email}}" style="color:#555;">Unsubscribe</a>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`
}

interface Article {
  slug: string
  slug_en: string | null
  title: string
  title_en: string | null
  excerpt: string | null
  excerpt_en: string | null
}

export async function GET(req: NextRequest) {
  // Protect manual calls with a secret
  const secret = req.nextUrl.searchParams.get('secret')
  const cronSecret = process.env.CRON_SECRET
  if (cronSecret && secret !== cronSecret) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  )
  const resendKey = process.env.RESEND_API_KEY
  if (!resendKey) {
    return NextResponse.json({ error: 'RESEND_API_KEY not set' }, { status: 500 })
  }

  // 1. Get active subscribers
  const { data: subscribers, error: subErr } = await supabase
    .from('newsletter_subscribers')
    .select('email')
    .eq('active', true)

  if (subErr) {
    console.error('[newsletter/send] subscribers error:', subErr.message)
    return NextResponse.json({ error: subErr.message }, { status: 500 })
  }
  if (!subscribers || subscribers.length === 0) {
    return NextResponse.json({ ok: true, sent: 0, reason: 'no subscribers' })
  }

  // 2. Get the 5 most recent EN articles from the past 7 days
  const since = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
  const { data: articles, error: artErr } = await supabase
    .from('articles')
    .select('slug, slug_en, title, title_en, excerpt, excerpt_en')
    .gte('published_at', since)
    .not('slug_en', 'is', null)
    .order('published_at', { ascending: false })
    .limit(5)

  if (artErr) {
    console.error('[newsletter/send] articles error:', artErr.message)
    return NextResponse.json({ error: artErr.message }, { status: 500 })
  }
  if (!articles || articles.length === 0) {
    return NextResponse.json({ ok: true, sent: 0, reason: 'no articles this week' })
  }

  const html = buildEmailHtml(articles as Article[])
  const subject = `NewsTide Weekly — ${new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`

  // 3. Send to all subscribers via Resend batch
  let sent = 0
  let failed = 0

  // Send in batches of 50 to avoid rate limits
  const BATCH = 50
  for (let i = 0; i < subscribers.length; i += BATCH) {
    const batch = subscribers.slice(i, i + BATCH)
    await Promise.all(
      batch.map(async ({ email }) => {
        try {
          const res = await fetch('https://api.resend.com/emails', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${resendKey}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              from: 'NewsTide <newsletter@newstide.news>',
              to: [email],
              subject,
              html: html.replace('{{email}}', encodeURIComponent(email)),
            }),
          })
          if (res.ok) {
            sent++
          } else {
            const err = await res.json()
            console.error(`[newsletter/send] Failed for ${email}:`, err)
            failed++
          }
        } catch (e) {
          console.error(`[newsletter/send] Exception for ${email}:`, e)
          failed++
        }
      })
    )
  }

  // 4. Log the send in Supabase
  await supabase.from('newsletter_sends').insert({
    sent_at: new Date().toISOString(),
    recipients: sent,
    failed,
    article_slugs: articles.map((a) => a.slug),
    subject,
  })

  console.log(`[newsletter/send] Done. Sent: ${sent}, Failed: ${failed}`)
  return NextResponse.json({ ok: true, sent, failed })
}
