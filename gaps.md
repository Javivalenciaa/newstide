# NewsTide — Gap List (ordenado por impacto en tráfico)

Este documento NO se carga automáticamente en cada sesión (a diferencia de CLAUDE.md). Referéncialo solo cuando trabajes en priorización o retomes el roadmap. Motivo: mantener CLAUDE.md corto y barato en tokens.

## Ya resuelto (no re-abrir sin motivo)
1. Keyword research con volumen real (DataForSEO) — `pipeline/dataforseo.py`, integrado en ambos pipelines.
2. GSC quick-wins con credenciales JSON — `fetch_gsc_queries()` en ambos pipelines, firma JWT manual con `cryptography` (no usa `google-auth`, que no está instalado).
3. Internal linking dentro del cuerpo del artículo — `fetch_related_articles()` + `inject_internal_links()`, ya funcionando vía prompt de Claude/GPT.

## EN CURSO — Internal linking persistente (prioridad actual)
**Objetivo:** guardar los 5 artículos relacionados de cada artículo nuevo en una columna `related_articles jsonb`, y mostrarlos en el sidebar de las 4 páginas de artículo (no solo en el cuerpo, que ya funciona).

Pasos:
1. Migración SQL: `ALTER TABLE articles/finance_articles ADD COLUMN IF NOT EXISTS related_articles jsonb DEFAULT '[]'::jsonb;`
2. En `pipeline/pipeline.py` y `pipeline/finance_pipeline.py`: nueva función `compute_related_articles()` (no confundir con `fetch_related_articles()`, que sigue existiendo para el cuerpo del texto) que puntúa por categoría + solapamiento de tokens + recencia, y se llama en `save_article()` antes del insert.
3. En los 4 `page.tsx` de artículo: añadir `related_articles` al select, renderizar sidebar de "Related Articles" con fallback a query en vivo si la columna está vacía (artículos antiguos).

## Pendiente — por impacto

| # | Gap | Impacto | Complejidad |
|---|---|---|---|
| 1 | Topic clusters + pillar pages | Muy alto | Media |
| 2 | Pillar pages frontend (`/en/topics/[cluster]`) | Muy alto | Media |
| 3 | Content refresh pipeline (re-generar artículos >90 días) | Muy alto | Media |
| 4 | `updated_at` real al refrescar contenido | Alto | Baja |
| 5 | Guardrails: integrar o retirar `content-guardrails.ts` (código muerto, el pipeline usa su propia versión Python) | Alto | Baja |
| 6 | FAQPage + HowTo + SoftwareApplication schema en artículos | Alto | Media |
| 7 | E-E-A-T: author schema completo + `sameAs` (LinkedIn/GitHub) | Alto | Baja |
| 8 | OG Images dinámicas con `@vercel/og` | Alto | Baja |
| 9 | GSC tracking a Supabase (tabla `serp_tracking`, workflow diario) | Alto | Media |
| 10 | Fix categorías incoherentes EN/ES en frontend | Alto | Baja |
| 11 | Canibalización: similarity check con `pg_trgm` en vez de solo GPT+hash | Alto | Baja |
| 12 | pSEO: verificar que `pseo_pipeline.py` usa pricing real y actualizado | Alto | Media |
| 13 | `ARTICLES_PER_RUN` con lógica de cluster (no solo número fijo) | Alto | Baja |
| 14 | Búsqueda interna full-text | Medio | Baja |
| 15 | Newsletter: envío real vía Resend (captura ya existe, envío no) | Medio | Baja |
| 16 | Testing automatizado (pytest + CI) | Preventivo | Baja |
| 17 | Alertas de fallo del pipeline (Telegram/email) | Preventivo | Baja |

## Top 5 recomendado tras internal linking
1. Content refresh pipeline (mantiene rankings de artículos "best tools 2026").
2. Topic clusters + pillar pages (topical authority real).
3. FAQPage/HowTo schema (CTR con el mismo ranking).
4. Fix categorías EN/ES (bug activo, barato de arreglar).
5. GSC tracking a Supabase (visibilidad de qué está cayendo).
