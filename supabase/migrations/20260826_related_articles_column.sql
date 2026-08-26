-- ═══════════════════════════════════════════════════════════════════
-- NewsTide — GAP-01 / GAP-06: Internal Linking — Related Articles column
-- Apply manually in Supabase SQL Editor (project: newstide)
-- Order: run this BEFORE deploying pipeline changes
-- ═══════════════════════════════════════════════════════════════════

-- 1. Solopreneur / indie hacker niche (table: articles)
ALTER TABLE public.articles
  ADD COLUMN IF NOT EXISTS related_articles jsonb DEFAULT '[]'::jsonb;

-- 2. Personal Finance for US Hispanics (table: finance_articles)
ALTER TABLE public.finance_articles
  ADD COLUMN IF NOT EXISTS related_articles jsonb DEFAULT '[]'::jsonb;

-- Optional: index for non-null / non-empty checks (low overhead, helps frontend fallback queries)
CREATE INDEX IF NOT EXISTS articles_related_articles_not_empty_idx
  ON public.articles ((related_articles IS NOT NULL AND jsonb_array_length(related_articles) > 0));

CREATE INDEX IF NOT EXISTS finance_articles_related_articles_not_empty_idx
  ON public.finance_articles ((related_articles IS NOT NULL AND jsonb_array_length(related_articles) > 0));
