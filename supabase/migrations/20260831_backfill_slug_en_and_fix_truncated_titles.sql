-- =============================================================================
-- NewsTide — 2026-08-31
-- Puntos 5 y 6 de la lista de alto impacto.
--
-- Ejecutar en: Supabase → SQL Editor → pegar y Run.
-- Seguro y reversible: solo rellena columnas vacías y acorta dos títulos.
-- No borra filas, no renombra columnas, no toca slugs ya publicados.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- PUNTO 6 — Dar URL a 16 artículos que tienen contenido en inglés pero
-- ningún slug_en, así que /en/article/… nunca ha existido para ellos y el
-- contenido lleva meses invisible (y ya estaba pagado).
--
-- Los slugs se generaron con la función slugify() real de pipeline/pipeline.py,
-- así que siguen exactamente el mismo formato que el resto del sitio.
--
-- De los 19 candidatos se descartan 3 a propósito: uno con content_en vacío
-- y dos por debajo de las ~450 palabras (thin content — publicarlos haría
-- más daño que bien).
-- -----------------------------------------------------------------------------

UPDATE articles SET slug_en = CASE id
  WHEN 'a79bacd3-d692-4bc9-a476-9fed2d5f6c8e'::uuid THEN 'beijings-double-game-how-chinas-new-capital-controls-are'
  WHEN 'c7b01847-4f07-4b7f-a1ca-ae1530472211'::uuid THEN 'orbio-ai-raises-18m-why-hr-is-the-next-battleground-for'
  WHEN '259e4897-f737-43d7-ab6c-d4a0019469eb'::uuid THEN 'your-startup-needs-a-robot-lawyer-how-to-build-an-automated'
  WHEN 'c8e27f8a-7f7f-4fc4-bdda-edfadc398bbc'::uuid THEN 'bezos-invests-10b-in-project-prometheus-the-most-expensive'
  WHEN '0c4b922f-40c3-4353-9765-931e5656c45f'::uuid THEN 'brazil-puts-5m-on-the-table-why-google-chose-monashees-for'
  WHEN 'fc7699cf-2e2a-4fb3-8f3e-6e75ff5d2e5b'::uuid THEN 'from-canvas-contract-to-yours-implement-automated-legal'
  WHEN 'd065ffe7-78e5-4b8a-86d8-7188afc7e725'::uuid THEN 'when-the-british-government-bets-pensions-on-tech-50b-that'
  WHEN '798228df-6ef9-4291-b995-2554da4ff981'::uuid THEN 'when-your-startup-needs-a-lawyer-but-only-has-a-budget-for'
  WHEN '8bdde31b-c4ab-4ac6-b108-ddba9d2899df'::uuid THEN 'when-ai-leaves-the-lab-and-enters-the-hall-of-mirrors-the'
  WHEN '7aabeb28-392d-4879-8097-ad7749c0daa8'::uuid THEN 'when-strangers-unite-to-fund-a-10000-prompt-welcome-to'
  WHEN '4deba615-bdbe-4ab9-84cb-0abb3dbd77f9'::uuid THEN 'while-openai-and-anthropic-battle-google-conquers-the'
  WHEN '46c62cad-0674-42e6-a28d-1b8cdac1059b'::uuid THEN 'when-your-employees-defend-the-competition-the-dod-lawsuit'
  WHEN '08ac8dd8-ab1f-417e-a9cd-c1c52a490363'::uuid THEN 'the-tools-redefining-tech-development-in-june-2026'
  WHEN '4397c102-c196-40f1-b71f-099673fb8128'::uuid THEN 'business-ai-enters-its-consolidation-phase-whats-really'
  WHEN 'a87d2d5c-2ad7-400f-84b0-338773c51e33'::uuid THEN '14-ai-tools-redefining-productivity-in-your-startup'
  WHEN 'e050add0-c3a0-4b56-8148-db79606911a9'::uuid THEN 'conversational-ai-the-tools-redefining-business'
END
WHERE id IN (
  'a79bacd3-d692-4bc9-a476-9fed2d5f6c8e'::uuid, 'c7b01847-4f07-4b7f-a1ca-ae1530472211'::uuid,
  '259e4897-f737-43d7-ab6c-d4a0019469eb'::uuid, 'c8e27f8a-7f7f-4fc4-bdda-edfadc398bbc'::uuid,
  '0c4b922f-40c3-4353-9765-931e5656c45f'::uuid, 'fc7699cf-2e2a-4fb3-8f3e-6e75ff5d2e5b'::uuid,
  'd065ffe7-78e5-4b8a-86d8-7188afc7e725'::uuid, '798228df-6ef9-4291-b995-2554da4ff981'::uuid,
  '8bdde31b-c4ab-4ac6-b108-ddba9d2899df'::uuid, '7aabeb28-392d-4879-8097-ad7749c0daa8'::uuid,
  '4deba615-bdbe-4ab9-84cb-0abb3dbd77f9'::uuid, '46c62cad-0674-42e6-a28d-1b8cdac1059b'::uuid,
  '08ac8dd8-ab1f-417e-a9cd-c1c52a490363'::uuid, '4397c102-c196-40f1-b71f-099673fb8128'::uuid,
  'a87d2d5c-2ad7-400f-84b0-338773c51e33'::uuid, 'e050add0-c3a0-4b56-8148-db79606911a9'::uuid
)
AND slug_en IS NULL;   -- idempotente: relanzarlo no pisa nada


-- -----------------------------------------------------------------------------
-- PUNTO 5 — Los dos únicos títulos/metas objetivamente rotos de las páginas
-- que ya rankean en posición 3-10.
--
-- Los otros 6 NO se tocan a propósito: miden 47-59 caracteres con metas de
-- 114-155, están sanos, y reescribirlos resetearía señales de ranking a
-- cambio de nada. Con 11 impresiones en posición 4,7 lo esperable es ~1 clic,
-- así que 0 clics ahí es ruido estadístico, no un problema de título.
-- -----------------------------------------------------------------------------

-- Título de 103 caracteres (EN) y 114 (ES). Google trunca en ~60, así que la
-- promesa del titular nunca llegaba a verse en el resultado de búsqueda.
-- 44 impresiones en posición 6,0 y cero clics.
-- El slug NO se cambia: cambiarlo perdería el ranking y exigiría un 301.
UPDATE articles SET
  title_en = 'Greylock vs Slack: Persistent Context for Remote Teams',
  title    = 'Greylock vs Slack: contexto persistente para equipos remotos'
WHERE slug_en = 'greylock-is-not-slack-how-persistent-context-architecture-changes-the-rules-of-d';

-- Meta description cortada a media frase en los dos idiomas
-- (EN: "…here's how to pick and."  ES: "…para fundadores solitarios en.").
-- Una meta truncada se lee como descuido y hunde el CTR.
UPDATE articles SET
  excerpt_en = 'Vertical tools, API products, and workflow connectors are the three micro-SaaS models shipping revenue for solo founders in 2026. Here''s how to pick one.',
  excerpt    = 'Herramientas verticales, productos API y conectores de flujos: los tres modelos de micro-SaaS que generan ingresos para fundadores solitarios en 2026.'
WHERE slug_en = 'best-micro-saas-ideas-for-indie-hackers-in-2026';


-- -----------------------------------------------------------------------------
-- VERIFICACIÓN — ejecutar después; debe devolver 16, 0 y 0.
-- -----------------------------------------------------------------------------
-- SELECT
--   (SELECT COUNT(*) FROM articles WHERE slug_en IS NOT NULL
--      AND id IN ('a79bacd3-d692-4bc9-a476-9fed2d5f6c8e'::uuid)) AS ejemplo_ok,
--   (SELECT COUNT(*) FROM articles
--      WHERE slug_en IS NULL AND content_en IS NOT NULL
--        AND length(content_en) >= 6000)                          AS quedan_invisibles,
--   (SELECT COUNT(*) FROM articles WHERE length(title_en) > 70)   AS titulos_demasiado_largos;
