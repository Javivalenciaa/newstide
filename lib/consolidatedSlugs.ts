/**
 * Cannibalised article pairs consolidated on 2026-09-02.
 *
 * Why
 * ---
 * Deduplication ran on whole-title trigram similarity (pg_trgm at 0.45), which
 * measures wording rather than subject, so the same comparison shipped twice
 * under different phrasings. "Airtable vs. Asana: A Complete Tool Comparison"
 * scores 0.33 against "Airtable vs. Asana: Which Tool Is Better for Founders?"
 * — two pages competing for one query, eleven days apart. Replaying an
 * entity-pair rule over all 281 rows found 13 such articles.
 *
 * pipeline/seo_guard.py now blocks new ones before generation. This map cleans
 * up the ones already live.
 *
 * How the survivor was chosen
 * ---------------------------
 * 1. The URL with real Search Console impressions wins (only one pair had any:
 *    airtable-vs-google-sheets-which-saves-time, 54 impressions).
 * 2. Otherwise the page serving the broader query wins — which is why the
 *    three-way "n8n vs Zapier vs Make" absorbs the two-way "Zapier vs Make"
 *    rather than the other way round.
 * 3. Otherwise the older URL wins, since age is the only remaining signal.
 *
 * Every redirected URL had 0 impressions and 0 clicks, so nothing measurable
 * is being given up.
 *
 * Deliberately NOT consolidated: "Zapier vs. Integromat" (comparison) against
 * "Automate Your Workflow: Zapier and Integromat Setup" (how-to). Same brands,
 * genuinely different search intent — these two should both exist.
 *
 * Consumed by next.config.ts (301 redirects) and app/sitemap.ts (exclusion),
 * so the redirect and the sitemap can never disagree.
 */

export type Consolidation = {
  /** slug_en of the page being retired (undefined when it never had one) */
  fromEn?: string
  /** slug (Spanish) of the page being retired */
  fromEs?: string
  /** slug_en of the surviving page */
  toEn: string
  /** slug (Spanish) of the surviving page */
  toEs: string
  /** shared entities that made the pair cannibalise */
  cluster: string
}

export const CONSOLIDATIONS: Consolidation[] = [
  {
    cluster: 'airtable+asana',
    fromEn: 'airtable-vs-asana-a-complete-tool-comparison',
    fromEs: 'airtable-vs-asana-comparativa-completa-de-herramientas',
    toEn: 'airtable-vs-asana-which-tool-is-better-for-founders',
    toEs: 'airtable-vs-asana-cual-herramienta-es-mejor-para-fundadores',
  },
  {
    cluster: 'airtable+googlesheets',
    fromEn: 'airtable-vs-google-sheets-which-tool-is-more-versatile',
    fromEs: 'airtable-vs-google-sheets-cual-herramienta-es-mas-versatil',
    toEn: 'airtable-vs-google-sheets-which-saves-time',
    toEs: 'airtable-vs-google-sheets-cual-ahorra-mas-tiempo',
  },
  {
    cluster: 'airtable+notion',
    fromEn: 'airtable-vs-notion-which-tool-is-best-for-solo-projects',
    fromEs: 'airtable-vs-notion-cual-es-la-mejor-herramienta-para-proyectos-en',
    toEn: 'airtable-vs-notion-which-tool-saves-time-for-founders',
    toEs: 'airtable-vs-notion-which-tool-saves-time-for-founders',
  },
  {
    cluster: 'zapier+make',
    fromEn: 'zapier-vs-make-which-automation-tool-wins-for-founders',
    fromEs: 'zapier-vs-make-que-herramienta-de-automatizacion-ganan-los',
    toEn: 'n8n-vs-zapier-vs-make-solo-automation-compared',
    toEs: 'n8n-vs-zapier-vs-make-comparacion-de-automatizacion-en-solitario',
  },
  {
    cluster: 'vercel+netlify',
    fromEn: 'vercel-outpaces-netlify-in-3-key-performance-metrics',
    fromEs: 'vercel-aplasta-a-netlify-en-3-metricas-que-importan',
    toEn: 'vercel-vs-netlify-which-is-best-for-solo-founders',
    toEs: 'vercel-vs-netlify-which-is-best-for-solo-founders',
  },
  {
    cluster: 'flutter+firebase',
    fromEn: 'ship-your-first-ai-product-in-7-days-flutter-firebase',
    fromEs: 'ship-your-first-ai-product-in-7-days-flutter-firebase',
    toEn: 'build-rapid-prototypes-in-7-days-with-flutter-firebase',
    toEs: 'build-rapid-prototypes-in-7-days-with-flutter-firebase',
  },
  {
    cluster: 'mistral+openai',
    fromEn: 'mistral-secures-500m-open-architecture-outpaces-openai',
    fromEs: 'mistral-capta-500m-y-su-arquitectura-abierta-aleja-a-openai',
    toEn: 'mistral-raises-300m-challenges-openais-lead',
    toEs: 'mistral-capta-300m-y-entierra-la-ventaja-de-openai',
  },
]

/** slug_en values that must no longer be served or listed. */
export const RETIRED_EN_SLUGS: ReadonlySet<string> = new Set(
  CONSOLIDATIONS.map((c) => c.fromEn).filter((s): s is string => !!s)
)

/** Spanish slug values that must no longer be served or listed. */
export const RETIRED_ES_SLUGS: ReadonlySet<string> = new Set(
  CONSOLIDATIONS.map((c) => c.fromEs).filter((s): s is string => !!s)
)
