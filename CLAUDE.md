# NewsTide — Contexto del proyecto (Claude Code)

## Qué es
Plataforma de contenido automatizado en producción real, con tráfico activo. Next.js 14 (App Router) + Vercel + Supabase (Postgres). Dos verticales de contenido generadas por pipelines Python vía GitHub Actions (cron diario):

- `pipeline/pipeline.py` → tabla `articles`. Nicho: solopreneurs/indie hackers. Bilingüe: columnas `_en` para inglés (`title_en`, `slug_en`, `content_en`, `excerpt_en`), sin sufijo para español (`title`, `slug`, `content`, `excerpt`).
- `pipeline/finance_pipeline.py` → tabla `finance_articles`. Nicho: finanzas personales para hispanos en USA.
- `pipeline/pseo_pipeline.py` → páginas de comparación programática (pSEO).
- `pipeline/dataforseo.py` → módulo compartido de keyword research (volumen/dificultad). Nombre de archivo heredado: desde 2026-08-31 llama a **YepAPI** (`YEPAPI_API_KEY`), no a DataForSEO — se migró porque se agotó el trial y su depósito mínimo de $50 no compensaba.
- `pipeline/geo_citation_pipeline.py` → optimización para citabilidad en LLMs (AEO/GEO).

## Rutas de artículo individual (confirmadas, no inventar otras)
| Ruta | Tabla | Idioma |
|---|---|---|
| `app/en/article/[slug]/page.tsx` | `articles` | Inglés |
| `app/articulo/[slug]/page.tsx` | `articles` | Español |
| `app/en/fin/[slug]/page.tsx` | `finance_articles` | Inglés |
| `app/es/fin/[slug]/page.tsx` | `finance_articles` | Español |

## Comandos
- Type-check: `npx tsc --noEmit`
- Lint: `npm run lint` (ver `eslint.config.mjs`)
- Sintaxis Python: `python -m py_compile <archivo>`
- Nunca ejecutar migraciones SQL directamente sin mostrarme el SQL antes.

## Reglas no negociables
1. **Solo añadir, nunca eliminar o reescribir funcionalidad existente.** Edita solo las secciones necesarias; nunca sustituyas un archivo completo por una versión de memoria.
2. **No tocar**: `pipeline/dataforseo.py`, `fetch_gsc_queries()` (en ambos pipelines), `FIRST_PARTY_VERIFIED`, `MAX_CLAUDE_CALLS_PER_RUN`, `MAX_CLAUDE_TOKENS_PER_RUN`. Todo esto ya funciona en producción. `ARTICLES_PER_RUN` sale de esta lista el 2026-09-02 por petición explícita del usuario: ahora es una decisión de estrategia SEO documentada abajo, no un límite de coste (los límites de coste siguen siendo los dos `MAX_CLAUDE_*`). No cambiarlo sin los datos de `serp_tracking` delante.
3. **No eliminar** `fetch_related_articles()` ni `inject_internal_links()` (ya insertan 2-3 enlaces dentro del cuerpo del artículo vía prompt). Cualquier tarea de internal linking es ADICIONAL a esto, no lo sustituye.
4. Toda llamada nueva a Supabase va en `try/except` con `print()` de warning y fallback seguro — nunca debe romper el pipeline.
5. Solo `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` en Supabase. Nunca renombrar/eliminar columnas.
6. No crear ramas salvo que se pida explícitamente. Commit directo a `main` tras validar sintaxis/tipos/lint.
7. Antes de tocar cualquier archivo, léelo completo primero. Si algo en el código real no coincide con este documento, usa lo que encuentres en el código, no lo que dice aquí.

## Volumen de publicación (decidido con datos el 2026-09-02 — no subir sin medir)
`ARTICLES_PER_RUN = 2` en ambos pipelines y `REFRESH_PER_RUN = 3`. Estado medido ese día: ~784 URLs indexables, **solo 32 con alguna impresión en GSC**, 0 clics, posición media 69. Antes de volver a subir el volumen, comprobar que crece el nº de URLs distintas en `serp_tracking` — esa métrica, no las impresiones, dice si Google ha vuelto a rastrear.

## Estado actual (actualiza esta sección cuando cierres un gap)
- ✅ Keyword research con YepAPI (antes DataForSEO, migrado 2026-08-31) — hecho y funcionando en ambos pipelines.
- ✅ GSC quick-wins con `GSC_SERVICE_ACCOUNT_JSON` — hecho en ambos pipelines.
- ✅ Enlaces internos en el cuerpo del artículo (`inject_internal_links`) — ya existía, funciona.
- ✅ Internal linking persistente (`related_articles jsonb` + sidebar en los 4 `page.tsx`) — falta ejecutar el SQL de migración en Supabase (ya entregado, no aplicado en automático).
- ✅ Categorías EN/ES sincronizadas con la taxonomía real de `detect_category()` en los 17 archivos que la hardcodeaban.
- ✅ `content-guardrails.ts` (código muerto) archivado; guardrails reales viven en `run_content_guardrails()` (Python).
- ✅ Testing automatizado: `pipeline/tests/` (pytest) + CI en `.github/workflows/pipeline-tests.yml`.
- ✅ Deduplicación por par de entidades (`pipeline/seo_guard.py`) — pg_trgm compara *redacción*; la canibalización la causa el *par de productos*. Usado por ambos pipelines antes de la llamada a Claude.
- ✅ Guardrails en `finance_pipeline.py` (antes solo existían en `pipeline.py`), con checks BLOQUEANTES de fuente `.gov` y disclaimer para YMYL.
- ✅ `needs_review` + `guardrail_flags` persistidos en Supabase — falta aplicar `supabase/migrations/20260902_guardrail_review_columns.sql` (los pipelines ya reintentan sin esas columnas si no existen).
- ✅ Consolidación de 7 pares canibalizados (`lib/consolidatedSlugs.ts` → 301 en `next.config.ts` + exclusión del sitemap).
- ✅ hreflang recíproco en `/es/fin/[slug]`; `BreadcrumbList` + `Speakable` en las dos rutas de finanzas.
- ✅ `related_articles`: la columna es `text[]`, no `jsonb`, así que cada entrada llega como string JSON. Normalizado en `lib/relatedArticles.ts` — **no asumir que son objetos**. Backfill: `pipeline/backfill_related_articles.py`.
- 🔴 Pendiente: ejecutar el backfill de `related_articles` (269 filas), alertas de fallo del pipeline, newsletter vía Resend, búsqueda interna.

Ver lista completa de gaps priorizados por impacto en `gaps.md`.
