# NewsTide — Contexto del proyecto (Claude Code)

## Qué es
Plataforma de contenido automatizado en producción real, con tráfico activo. Next.js 14 (App Router) + Vercel + Supabase (Postgres). Dos verticales de contenido generadas por pipelines Python vía GitHub Actions (cron diario):

- `pipeline/pipeline.py` → tabla `articles`. Nicho: solopreneurs/indie hackers. Bilingüe: columnas `_en` para inglés (`title_en`, `slug_en`, `content_en`, `excerpt_en`), sin sufijo para español (`title`, `slug`, `content`, `excerpt`).
- `pipeline/finance_pipeline.py` → tabla `finance_articles`. Nicho: finanzas personales para hispanos en USA.
- `pipeline/pseo_pipeline.py` → páginas de comparación programática (pSEO).
- `pipeline/dataforseo.py` → módulo compartido de keyword research (volumen/dificultad).
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
2. **No tocar**: `pipeline/dataforseo.py`, `fetch_gsc_queries()` (en ambos pipelines), `FIRST_PARTY_VERIFIED`, `ARTICLES_PER_RUN`, `MAX_CLAUDE_CALLS_PER_RUN`, `MAX_CLAUDE_TOKENS_PER_RUN`. Todo esto ya funciona en producción.
3. **No eliminar** `fetch_related_articles()` ni `inject_internal_links()` (ya insertan 2-3 enlaces dentro del cuerpo del artículo vía prompt). Cualquier tarea de internal linking es ADICIONAL a esto, no lo sustituye.
4. Toda llamada nueva a Supabase va en `try/except` con `print()` de warning y fallback seguro — nunca debe romper el pipeline.
5. Solo `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` en Supabase. Nunca renombrar/eliminar columnas.
6. No crear ramas salvo que se pida explícitamente. Commit directo a `main` tras validar sintaxis/tipos/lint.
7. Antes de tocar cualquier archivo, léelo completo primero. Si algo en el código real no coincide con este documento, usa lo que encuentres en el código, no lo que dice aquí.

## Estado actual (actualiza esta sección cuando cierres un gap)
- ✅ Keyword research con DataForSEO — hecho y funcionando en ambos pipelines.
- ✅ GSC quick-wins con `GSC_SERVICE_ACCOUNT_JSON` — hecho en ambos pipelines.
- ✅ Enlaces internos en el cuerpo del artículo (`inject_internal_links`) — ya existía, funciona.
- ✅ Internal linking persistente (`related_articles jsonb` + sidebar en los 4 `page.tsx`) — falta ejecutar el SQL de migración en Supabase (ya entregado, no aplicado en automático).
- ✅ Categorías EN/ES sincronizadas con la taxonomía real de `detect_category()` en los 17 archivos que la hardcodeaban.
- ✅ `content-guardrails.ts` (código muerto) archivado; guardrails reales viven en `run_content_guardrails()` (Python).
- ✅ Testing automatizado: `pipeline/tests/` (pytest) + CI en `.github/workflows/pipeline-tests.yml`.
- 🔴 Pendiente: topic clusters + pillar pages, content refresh pipeline, FAQ/HowTo schema, OG images dinámicas, GSC tracking a Supabase, alertas de fallo del pipeline.

Ver lista completa de gaps priorizados por impacto en `gaps.md`.
