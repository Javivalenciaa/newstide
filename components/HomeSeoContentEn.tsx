import Link from 'next/link'

// Editorial block for the English homepage.
// Fixes: too few useful words, H1/title words not reused in body copy,
// too few varied internal links, zero external links.
// Import in app/en/page.tsx: <HomeSeoContentEn /> before the footer.
export default function HomeSeoContentEn() {
  return (
    <section
      aria-labelledby="about-newstide"
      style={{ padding: '64px 24px', maxWidth: 860, margin: '0 auto' }}
    >
      <h2 id="about-newstide" style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 20, letterSpacing: '-0.02em' }}>
        NewsTide: the intelligence shaping the future of how you stay informed
      </h2>

      <p style={{ fontSize: 17, lineHeight: 1.8, marginBottom: 20, color: 'rgba(240,240,238,0.85)' }}>
        NewsTide started from a simple premise: artificial intelligence is shaping the future of how
        founders, developers, and professionals get their information, and someone needed to cover
        that shift with rigor. Every week we publish in-depth articles on AI, tech startups, and the
        tools redefining how digital products get built in 2026. We do not chase empty headlines —
        every piece you find in{' '}
        <Link href="/en/articles" style={{ color: 'var(--cyan)' }}>our article archive</Link>{' '}
        goes through an editorial process that blends AI assistance with human review, following the
        standards outlined in our{' '}
        <Link href="/en/editorial-policy" style={{ color: 'var(--cyan)' }}>editorial policy</Link>.
      </p>

      <p style={{ fontSize: 17, lineHeight: 1.8, marginBottom: 20, color: 'rgba(240,240,238,0.85)' }}>
        Beyond technology, we cover an angle most general-interest outlets skip: practical{' '}
        <Link href="/en/fin" style={{ color: 'var(--cyan)' }}>personal finance for everyday Americans</Link>,
        from saving and budgeting to investing and building credit. This finance section grows daily
        and complements our AI coverage with content people actually need to make better decisions
        with their money.
      </p>

      <p style={{ fontSize: 17, lineHeight: 1.8, marginBottom: 20, color: 'rgba(240,240,238,0.85)' }}>
        Our team tracks the industry closely — from official announcements at{' '}
        <a href="https://openai.com/blog" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>OpenAI</a>{' '}
        and{' '}
        <a href="https://www.anthropic.com/news" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)' }}>Anthropic</a>{' '}
        to the market moves shaping startups and big tech — and turn it into clear analysis, without
        the filler. You can meet the team behind these stories on our{' '}
        <Link href="/en/authors" style={{ color: 'var(--cyan)' }}>authors page</Link>, or subscribe to
        our newsletter to get the most relevant stories of the week straight to your inbox.
      </p>

      <p style={{ fontSize: 17, lineHeight: 1.8, color: 'rgba(240,240,238,0.85)' }}>
        If you want to understand how artificial intelligence is shaping the future of work,
        investing, or product development, NewsTide is your starting point. Browse our categories,
        tool comparisons, and finance guides, and check back often — we publish new content
        constantly so you do not have to hunt for it across dozens of scattered sources.
      </p>
    </section>
  )
}
