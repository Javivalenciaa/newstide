import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'About NewsTide — Technology and AI for Those Who Stay Ahead',
  description: 'NewsTide is an AI-assisted technology news publication covering artificial intelligence, startups and finance. Learn about our editorial methodology, team and transparency commitments.',
  alternates: {
    canonical: 'https://www.newstide.news/en/about',
    languages: {
      'en': 'https://www.newstide.news/en/about',
      'es': 'https://www.newstide.news/sobre-nosotros',
      'x-default': 'https://www.newstide.news/en/about',
    },
  },
  openGraph: {
    title: 'About NewsTide — Technology and AI News',
    description: 'AI-assisted journalism covering AI, startups and finance. Human-reviewed, source-cited, transparent.',
    url: 'https://www.newstide.news/en/about',
    siteName: 'NewsTide',
    locale: 'en_US',
    type: 'website',
  },
}

const orgSchema = {
  '@context': 'https://schema.org',
  '@type': ['NewsMediaOrganization', 'Organization'],
  '@id': 'https://www.newstide.news/#organization',
  name: 'NewsTide',
  url: 'https://www.newstide.news',
  foundingDate: '2024',
  description:
    'NewsTide is an AI-assisted digital publication specialising in artificial intelligence, startups and financial technology, serving founders, developers and digital professionals.',
  inLanguage: ['en', 'es'],
  logo: {
    '@type': 'ImageObject',
    url: 'https://www.newstide.news/favicon-192x192.png',
    width: 192,
    height: 192,
  },
  masthead: 'https://www.newstide.news/en/about',
  ethicsPolicy: 'https://www.newstide.news/en/editorial-policy',
  correctionsPolicy: 'https://www.newstide.news/en/editorial-policy#corrections',
  verificationFactCheckingPolicy: 'https://www.newstide.news/en/editorial-policy#verification',
  sameAs: [
    'https://twitter.com/newstide',
    'https://www.linkedin.com/company/newstide',
    'https://github.com/Javivalenciaa',
  ],
  contactPoint: {
    '@type': 'ContactPoint',
    contactType: 'editorial',
    email: 'newstideco@gmail.com',
    availableLanguage: ['English', 'Spanish'],
  },
  knowsAbout: [
    'Artificial Intelligence',
    'Machine Learning',
    'Large Language Models',
    'Startups',
    'Venture Capital',
    'Financial Technology',
    'Software Engineering',
    'Developer Tools',
  ],
  founder: {
    '@type': 'Person',
    '@id': 'https://www.newstide.news/en/authors/javier-valencia',
    name: 'Javier Valencia',
    url: 'https://www.newstide.news/en/authors/javier-valencia',
    jobTitle: 'Founder & Editor',
    description:
      'Computer Science and Business Administration student with hands-on experience in software development, digital twins, AI-powered systems, and innovation programs at IBM and Techstars.',
    alumniOf: [
      { '@type': 'Organization', name: 'IBM' },
      { '@type': 'Organization', name: 'Techstars' },
    ],
    knowsAbout: [
      'Artificial Intelligence',
      'Software Development',
      'Next.js',
      'Python',
      'Supabase',
      'Digital Twins',
      'Startups',
    ],
  },
}

const aboutPageSchema = {
  '@context': 'https://schema.org',
  '@type': 'AboutPage',
  '@id': 'https://www.newstide.news/en/about#webpage',
  name: 'About NewsTide',
  url: 'https://www.newstide.news/en/about',
  description:
    'Learn about NewsTide: who we are, how we create our content, and why we cover technology, artificial intelligence and finance with AI assistance and human editorial review.',
  isPartOf: { '@id': 'https://www.newstide.news/en#website' },
  about: { '@id': 'https://www.newstide.news/#organization' },
  speakable: {
    '@type': 'SpeakableSpecification',
    cssSelector: ['h1', '.about-lead'],
  },
}

export default function AboutEN() {
  return (
    <div style={{ minHeight: '100vh', padding: '120px 0 100px' }}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify([orgSchema, aboutPageSchema]) }}
      />
      <div className="container" style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <Link href="/en" style={{ color: 'var(--muted)', fontSize: 13, textDecoration: 'none' }}>← Home</Link>
        </div>

        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 16 }}>About NewsTide</h1>
        <p className="about-lead" style={{ fontSize: 18, color: 'var(--muted)', lineHeight: 1.7, marginBottom: 48 }}>
          Technology, AI and finance coverage for founders, developers and investors — AI-assisted, human-reviewed, source-cited.
        </p>

        <div style={{ fontSize: 16, lineHeight: 1.85, color: 'rgba(240,240,238,0.85)' }}>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>What is NewsTide?</h2>
          <p>
            NewsTide is a digital publication specialising in artificial intelligence, developer tools,
            startups and financial technology. Founded in 2024, our mission is to deliver accurate,
            timely and well-sourced information for the professionals who build and invest in the
            next generation of technology. Every article targets a reading level that respects the
            intelligence of our audience — no fluff, no filler.
          </p>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>The team</h2>
          <p>
            NewsTide was founded by{' '}
            <Link href="/en/authors/javier-valencia" style={{ color: 'var(--cyan)' }}>Javier Valencia</Link>,
            a student of Computer Science and Business Administration. Javier has hands-on experience as a
            freelance web and software developer, has participated in startup and innovation programs run by
            <strong> IBM</strong> and <strong>Techstars</strong>, and has competed in programming and
            business innovation contests. His technical work spans digital twin development, AI-powered
            automation systems, and self-built web platforms — including NewsTide itself.
          </p>
          <p style={{ marginTop: 16 }}>
            Javier oversees editorial direction, technical infrastructure and quality control on every
            article published on the platform.
          </p>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>How we create our content</h2>
          <p>
            NewsTide uses AI language models to assist in the drafting, structuring and translation
            of articles. Every published piece is then reviewed by our editorial team, which verifies
            factual claims against primary sources — official press releases, corporate filings,
            peer-reviewed research, and direct statements from the individuals and organisations covered.
            We follow the{' '}
            <a
              href="https://www.spj.org/ethicscode.asp"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: 'var(--cyan)' }}
            >
              SPJ Code of Ethics
            </a>{' '}
            and the{' '}
            <a
              href="https://publishercenter.google.com/intl/en_us/about/publisher-policies"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: 'var(--cyan)' }}
            >
              Google News Publisher Policies
            </a>{' '}
            as our baseline editorial standards.
          </p>
          <p style={{ marginTop: 16 }}>
            Our AI-assisted workflow is transparent by design: every article displays the date
            it was published and last modified, and links to the primary sources used. If you
            find an error, email us at{' '}
            <a href="mailto:newstideco@gmail.com" style={{ color: 'var(--cyan)' }}>newstideco@gmail.com</a>{' '}
            — we commit to reviewing and correcting inaccuracies within 48 hours.
          </p>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>Our editorial pillars</h2>
          <ul style={{ margin: '0 0 20px 24px' }}>
            <li style={{ marginBottom: 10 }}>
              <strong>Artificial Intelligence &amp; Models:</strong> tracking the latest foundation
              models, AI tools, research breakthroughs and their real-world implications.
            </li>
            <li style={{ marginBottom: 10 }}>
              <strong>Developer Tools:</strong> hands-on analysis and comparisons of development,
              productivity and automation tools — written by people who actually use them.
            </li>
            <li style={{ marginBottom: 10 }}>
              <strong>Finance &amp; Markets:</strong> financial markets, crypto, venture capital
              and the digital economy, explained without unnecessary jargon.
            </li>
            <li style={{ marginBottom: 10 }}>
              <strong>Startups &amp; Business:</strong> funding rounds, product launches,
              founder interviews and the broader entrepreneurial ecosystem.
            </li>
          </ul>

          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 16, marginTop: 40 }}>Editorial transparency</h2>
          <p>
            We believe in radical transparency about how this publication operates. NewsTide
            clearly labels AI-assisted content, links directly to primary sources, and maintains
            a public corrections policy. Our full standards are detailed in our{' '}
            <Link href="/en/editorial-policy" style={{ color: 'var(--cyan)' }}>Editorial Policy</Link>.
          </p>

          <div style={{ marginTop: 48, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/en/editorial-policy" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Editorial policy →</Link>
            <Link href="/en/contact" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Contact →</Link>
            <Link href="/en/authors/javier-valencia" style={{ color: 'var(--cyan)', fontWeight: 600, fontSize: 14 }}>Meet the editor →</Link>
            <Link href="/sobre-nosotros" style={{ color: 'var(--muted)', fontWeight: 600, fontSize: 14 }}>Leer en español →</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
