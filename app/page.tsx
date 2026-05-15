import { createClient } from "@supabase/supabase-js";
import { notFound } from "next/navigation";
import Link from "next/link";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef',
  'Herramientas': '#e8d5a3', 'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c'
};

function Badge({ cat }: { cat: string }) {
  const color = CAT_COLORS[cat] || '#6ecfca';
  return (
    <span style={{
      display: 'inline-block', padding: '3px 10px', borderRadius: '6px',
      fontSize: '10px', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase',
      background: `${color}18`, color, border: `1px solid ${color}30`
    }}>{cat}</span>
  );
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' });
}

export default async function ArticuloPage({
  params,
}: {
  params: { slug: string };
}) {
  const { data: article, error } = await supabase
    .from('articles')
    .select('*')
    .eq('slug', params.slug)
    .single();

  if (error || !article) {
    notFound();
  }

  return (
    <main style={{ background: '#0a0a0a', minHeight: '100vh', color: '#fff' }}>

      {/* HERO DEL ARTÍCULO */}
      <section style={{
        position: 'relative', padding: '80px 0 60px', overflow: 'hidden',
        borderBottom: '1px solid rgba(255,255,255,0.07)'
      }}>
        {/* Fondo con gradiente del artículo */}
        <div style={{
          position: 'absolute', inset: 0,
          background: article.image_gradient,
          opacity: 0.08, pointerEvents: 'none'
        }} />
        <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 24px', position: 'relative' }}>

          {/* BREADCRUMB */}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 28, fontSize: 13, color: 'rgba(255,255,255,0.4)' }}>
            <Link href="/" style={{ color: 'rgba(255,255,255,0.4)', textDecoration: 'none' }}>Inicio</Link>
            <span>/</span>
            <Link href="/#articles" style={{ color: 'rgba(255,255,255,0.4)', textDecoration: 'none' }}>Artículos</Link>
            <span>/</span>
            <span style={{ color: 'rgba(255,255,255,0.7)' }}>{article.category}</span>
          </div>

          {/* BADGE + META */}
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
            <Badge cat={article.category} />
            <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
              {article.author}
            </span>
            <span style={{ color: 'rgba(255,255,255,0.2)', fontSize: 13 }}>·</span>
            <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
              {formatDate(article.published_at)}
            </span>
            <span style={{ color: 'rgba(255,255,255,0.2)', fontSize: 13 }}>·</span>
            <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
              {article.reading_time} min de lectura
            </span>
          </div>

          {/* TÍTULO */}
          <h1 style={{
            fontSize: 'clamp(2rem, 5vw, 3.2rem)', fontWeight: 800,
            lineHeight: 1.15, marginBottom: 24, letterSpacing: '-0.02em'
          }}>
            {article.title}
          </h1>

          {/* EXCERPT */}
          <p style={{
            fontSize: 19, color: 'rgba(255,255,255,0.6)',
            lineHeight: 1.7, maxWidth: 700, marginBottom: 0
          }}>
            {article.excerpt}
          </p>
        </div>
      </section>

      {/* IMAGEN / GRADIENTE DECORATIVA */}
      <div style={{ maxWidth: 860, margin: '0 auto', padding: '40px 24px 0' }}>
        <div style={{
          width: '100%', height: 320, borderRadius: 16,
          background: article.image_gradient,
          position: 'relative', overflow: 'hidden'
        }}>
          <div style={{
            position: 'absolute', inset: 0,
            backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(255,255,255,0.03) 1px, transparent 1px), radial-gradient(circle at 80% 20%, rgba(255,255,255,0.03) 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }} />
        </div>
      </div>

      {/* CONTENIDO */}
      <section style={{ maxWidth: 860, margin: '0 auto', padding: '48px 24px 80px' }}>
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 220px', gap: 48, alignItems: 'start'
        }}>

          {/* TEXTO PRINCIPAL */}
          <div style={{
            fontSize: 17, lineHeight: 1.9,
            color: 'rgba(255,255,255,0.82)',
            whiteSpace: 'pre-wrap',
          }}>
            {article.content}
          </div>

          {/* SIDEBAR */}
          <aside style={{ position: 'sticky', top: 24 }}>

            {/* AUTOR */}
            <div style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 12, padding: 20, marginBottom: 16
            }}>
              <div style={{ fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.35)', marginBottom: 10 }}>
                Autor
              </div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>{article.author}</div>
              <div style={{ marginTop: 6 }}><Badge cat={article.category} /></div>
            </div>

            {/* DATOS DEL ARTÍCULO */}
            <div style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 12, padding: 20, marginBottom: 16
            }}>
              <div style={{ fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.35)', marginBottom: 10 }}>
                Detalles
              </div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.55)', lineHeight: 2 }}>
                <div>📅 {formatDate(article.published_at)}</div>
                <div>⏱ {article.reading_time} min</div>
                <div>🏷 {article.category}</div>
              </div>
            </div>

            {/* NEWSLETTER */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(110,207,202,0.1), rgba(155,140,239,0.1))',
              border: '1px solid rgba(110,207,202,0.2)',
              borderRadius: 12, padding: 20
            }}>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>✉️ Newsletter</div>
              <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', lineHeight: 1.6, marginBottom: 14 }}>
                Recibe los mejores artículos en tu inbox cada semana.
              </p>
              <input
                type="email"
                placeholder="tu@email.com"
                style={{
                  width: '100%', padding: '8px 12px', borderRadius: 8,
                  background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                  color: '#fff', fontSize: 12, marginBottom: 8, boxSizing: 'border-box'
                }}
              />
              <button style={{
                width: '100%', padding: '9px 0', borderRadius: 8,
                background: 'linear-gradient(90deg, #6ecfca, #9b8cef)',
                border: 'none', color: '#0a0a0a', fontWeight: 700, fontSize: 12, cursor: 'pointer'
              }}>
                Suscribirme gratis
              </button>
            </div>
          </aside>
        </div>

        {/* VOLVER */}
        <div style={{ marginTop: 60, paddingTop: 32, borderTop: '1px solid rgba(255,255,255,0.07)' }}>
          <Link href="/" style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            color: '#6ecfca', textDecoration: 'none', fontSize: 14, fontWeight: 600
          }}>
            ← Volver al inicio
          </Link>
        </div>
      </section>

    </main>
  );
}
