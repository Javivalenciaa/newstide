import { ImageResponse } from 'next/og'

export const runtime = 'edge'

// Same brand palette as app/globals.css --cyan/--violet/--gold/--red/--green,
// plus every real category from pipeline.py/finance_pipeline.py's detect_category().
const CAT_COLORS: Record<string, string> = {
  'IA': '#6ecfca', 'Startups': '#9b8cef', 'Herramientas': '#e8d5a3',
  'Tutoriales': '#7ecf9b', 'Noticias': '#ef6c6c',
  'AI Tools': '#6ecfca', 'Automation': '#9b8cef', 'Build & Launch': '#e8d5a3',
  'Indie Hacking': '#7ecf9b', 'Growth': '#ef6c6c', 'Monetization': '#f0a050',
  'Freelancing': '#8ecae6', 'Dev Stack': '#c9a0f5',
  'Crédito': '#e8d5a3', 'Impuestos': '#f0a050', 'Ahorro': '#6ecfca',
  'Presupuesto': '#9b8cef', 'Inversión': '#7ecf9b', 'Remesas': '#8ecae6',
  'Deudas': '#ef6c6c', 'Vivienda': '#c9a0f5', 'Ingresos Extra': '#ffd166',
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const title = (searchParams.get('title') || 'NewsTide').slice(0, 140)
  const category = (searchParams.get('category') || '').slice(0, 40)
  const color = CAT_COLORS[category] || '#6ecfca'

  return new ImageResponse(
    (
      <div
        style={{
          height: '100%',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '64px 72px',
          background: 'linear-gradient(135deg, #08090f 0%, #111118 100%)',
          fontFamily: 'sans-serif',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 16, height: 16, borderRadius: 4, background: color, display: 'flex' }} />
          <div style={{ fontSize: 30, fontWeight: 800, color: '#f0f0ee', letterSpacing: '-0.02em', display: 'flex' }}>
            NewsTide
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
          {category && (
            <div
              style={{
                display: 'flex',
                alignSelf: 'flex-start',
                fontSize: 22,
                fontWeight: 600,
                color,
                padding: '8px 18px',
                borderRadius: 8,
                background: `${color}22`,
                border: `2px solid ${color}55`,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              {category}
            </div>
          )}
          <div
            style={{
              display: 'flex',
              fontSize: title.length > 80 ? 46 : 58,
              fontWeight: 800,
              color: '#f0f0ee',
              lineHeight: 1.15,
              letterSpacing: '-0.02em',
              maxWidth: 1040,
            }}
          >
            {title}
          </div>
        </div>

        <div style={{ display: 'flex', fontSize: 22, color: '#888899' }}>newstide.news</div>
      </div>
    ),
    { width: 1200, height: 630 }
  )
}
